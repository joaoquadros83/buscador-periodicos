-- =============================================================================
-- PRODUCTION-GRADE SCHEMA: Hybrid Scientific Journal Recommender
-- Stack: PostgreSQL 15+ + pgvector (Supabase or Neon free tier)
-- Architecture: Dense (cosine) + Sparse (BM25/FTS) + Recency + Business + LLM
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =============================================================================
-- CONFIGURATION TABLE: Weights and thresholds (deterministic, tunable)
-- =============================================================================
CREATE TABLE IF NOT EXISTS matcher_config (
    key VARCHAR(100) PRIMARY KEY,
    value NUMERIC(6,4) NOT NULL,
    description TEXT
);

INSERT INTO matcher_config (key, value, description) VALUES
('title_weight', 1.5, 'Weight applied to title embedding vs abstract embedding'),
('abstract_weight', 1.0, 'Base weight for abstract embedding'),
('dense_alpha', 0.65, 'Weight for dense cosine score in hybrid linear combination'),
('sparse_alpha', 0.35, 'Weight for sparse BM25/FTS score in hybrid linear combination'),
('rrf_k', 60.0, 'Reciprocal Rank Fusion constant'),
('recency_lambda', 0.3, 'Exponential decay constant for recency scoring'),
('semantic_score_weight', 0.55, 'Weight of semantic/hybrid score in final match score'),
('recency_score_weight', 0.25, 'Weight of recency score in final match score'),
('business_score_weight', 0.20, 'Weight of business metadata score in final match score')
ON CONFLICT (key) DO NOTHING;

-- =============================================================================
-- STAGE A: JOURNALS TABLE (relational metadata + business filters)
-- =============================================================================
CREATE TABLE IF NOT EXISTS journals (
    id              SERIAL PRIMARY KEY,

    -- Identifiers
    title           TEXT NOT NULL,
    normalized_title TEXT NOT NULL,
    issn            VARCHAR(20),
    e_issn          VARCHAR(20),
    doi_prefix      VARCHAR(50),

    -- Relational filters
    publisher       TEXT,
    country         VARCHAR(100),
    language        VARCHAR(50),
    subjects        TEXT[],
    disciplines     TEXT[],

    -- Business metadata (strict filters)
    is_open_access  BOOLEAN DEFAULT FALSE,
    oa_type         VARCHAR(50), -- 'gold', 'hybrid', 'bronze', 'green', 'subscription'
    apc_value_usd   NUMERIC(10,2),
    apc_currency    VARCHAR(10) DEFAULT 'USD',
    avg_days_to_first_decision INTEGER,
    acceptance_rate NUMERIC(5,2),

    -- Impact metrics
    jif             NUMERIC(8,4),
    sjr             NUMERIC(8,4),
    quartil_jcr     VARCHAR(10),
    sjr_quartile    VARCHAR(10),
    h_index         INTEGER,
    h5_index        INTEGER,

    -- Links
    homepage        TEXT,
    h5_link         TEXT,

    -- Full-text search document (for sparse search on journal scope)
    scope_text      TEXT,
    scope_tsv       TSVECTOR,

    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),

    CONSTRAINT uq_journals_issn UNIQUE (issn)
);

-- Indexes for relational filtering
CREATE INDEX IF NOT EXISTS idx_journals_oa ON journals(is_open_access);
CREATE INDEX IF NOT EXISTS idx_journals_apc ON journals(apc_value_usd);
CREATE INDEX IF NOT EXISTS idx_journals_decision ON journals(avg_days_to_first_decision);
CREATE INDEX IF NOT EXISTS idx_journals_subjects ON journals USING gin (subjects);
CREATE INDEX IF NOT EXISTS idx_journals_disciplines ON journals USING gin (disciplines);
CREATE INDEX IF NOT EXISTS idx_journals_title_trgm ON journals USING gin (normalized_title gin_trgm_ops);

-- Full-text search index on journal scope
CREATE INDEX IF NOT EXISTS idx_journals_scope_fts ON journals USING gin (scope_tsv);

-- Trigger to auto-update scope_tsv
CREATE OR REPLACE FUNCTION update_journal_scope_tsv()
RETURNS TRIGGER AS $$
BEGIN
    NEW.scope_tsv := to_tsvector('english', COALESCE(NEW.scope_text, '') || ' ' || COALESCE(NEW.title, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_journal_scope_tsv ON journals;
CREATE TRIGGER trg_update_journal_scope_tsv
BEFORE INSERT OR UPDATE ON journals
FOR EACH ROW
EXECUTE FUNCTION update_journal_scope_tsv();

-- =============================================================================
-- STAGE A: JOURNAL EMBEDDINGS TABLE (separate title and abstract embeddings)
-- =============================================================================
CREATE TABLE IF NOT EXISTS journal_embeddings (
    id              SERIAL PRIMARY KEY,
    journal_id      INTEGER NOT NULL REFERENCES journals(id) ON DELETE CASCADE,

    -- Separate dense embeddings for title and abstract/scope
    title_embedding     vector(768),
    abstract_embedding  vector(768),

    model_name          VARCHAR(100) DEFAULT 'BAAI/bge-m3',
    generated_at        TIMESTAMP DEFAULT NOW(),

    CONSTRAINT uq_journal_embeddings_journal UNIQUE (journal_id)
);

-- HNSW indexes for cosine similarity on separate embeddings
CREATE INDEX IF NOT EXISTS idx_journal_embeddings_title_hnsw
    ON journal_embeddings USING hnsw (title_embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_journal_embeddings_abstract_hnsw
    ON journal_embeddings USING hnsw (abstract_embedding vector_cosine_ops);

-- =============================================================================
-- STAGE A: ARTICLES TABLE (recent publications used for recency + semantic)
-- =============================================================================
CREATE TABLE IF NOT EXISTS journal_articles (
    id              BIGSERIAL PRIMARY KEY,
    journal_id      INTEGER NOT NULL REFERENCES journals(id) ON DELETE CASCADE,

    title           TEXT NOT NULL,
    abstract        TEXT,
    doi             VARCHAR(255),
    pub_year        INTEGER NOT NULL,
    pub_date        DATE,
    citation_count  INTEGER DEFAULT 0,

    -- Separate dense embeddings
    title_embedding     vector(768),
    abstract_embedding  vector(768),

    -- Full-text search document
    article_text    TEXT,
    article_tsv     TSVECTOR,

    created_at      TIMESTAMP DEFAULT NOW(),

    CONSTRAINT uq_journal_articles_doi UNIQUE (doi)
);

CREATE INDEX IF NOT EXISTS idx_articles_journal_id ON journal_articles(journal_id);
CREATE INDEX IF NOT EXISTS idx_articles_pub_year ON journal_articles(pub_year);
CREATE INDEX IF NOT EXISTS idx_articles_title_hnsw
    ON journal_articles USING hnsw (title_embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_articles_abstract_hnsw
    ON journal_articles USING hnsw (abstract_embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_articles_fts ON journal_articles USING gin (article_tsv);

-- Trigger to auto-update article_tsv
CREATE OR REPLACE FUNCTION update_article_tsv()
RETURNS TRIGGER AS $$
BEGIN
    NEW.article_tsv := to_tsvector('english', COALESCE(NEW.article_text, '') || ' ' || COALESCE(NEW.title, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_article_tsv ON journal_articles;
CREATE TRIGGER trg_update_article_tsv
BEFORE INSERT OR UPDATE ON journal_articles
FOR EACH ROW
EXECUTE FUNCTION update_article_tsv();

-- =============================================================================
-- STAGE B: HYBRID RETRIEVAL FUNCTIONS
-- =============================================================================

-- Compute weighted query embedding: 1.5 * title + 1.0 * abstract, normalized
CREATE OR REPLACE FUNCTION compute_weighted_query_embedding(
    p_title_embedding vector(768),
    p_abstract_embedding vector(768)
)
RETURNS vector(768) AS $$
DECLARE
    v_title_weight NUMERIC;
    v_abstract_weight NUMERIC;
    v_title_vec vector(768);
    v_abstract_vec vector(768);
    v_combined vector(768);
    v_norm DOUBLE PRECISION;
BEGIN
    SELECT value INTO v_title_weight FROM matcher_config WHERE key = 'title_weight';
    SELECT value INTO v_abstract_weight FROM matcher_config WHERE key = 'abstract_weight';

    -- Cast to array for scalar multiplication, then back to vector
    v_title_vec := (p_title_embedding::real[] * v_title_weight::real)::vector(768);
    v_abstract_vec := (p_abstract_embedding::real[] * v_abstract_weight::real)::vector(768);
    v_combined := (v_title_vec::real[] + v_abstract_vec::real[])::vector(768);

    -- Normalize
    v_norm := sqrt(sum((v_combined::real[])[i] * (v_combined::real[])[i])) FROM generate_series(1, 768) AS i;
    IF v_norm = 0 THEN
        RETURN v_combined;
    END IF;

    RETURN (v_combined::real[] / v_norm::real)::vector(768);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Dense retrieval: top-K articles by cosine similarity with weighted query
CREATE OR REPLACE FUNCTION dense_article_search(
    p_title_embedding vector(768),
    p_abstract_embedding vector(768),
    p_limit INTEGER DEFAULT 100,
    p_min_year INTEGER DEFAULT NULL
)
RETURNS TABLE (
    article_id      BIGINT,
    journal_id      INTEGER,
    title           TEXT,
    pub_year        INTEGER,
    cosine_score    DOUBLE PRECISION
) AS $$
DECLARE
    v_query_vec vector(768);
BEGIN
    v_query_vec := compute_weighted_query_embedding(p_title_embedding, p_abstract_embedding);

    RETURN QUERY
    SELECT
        ja.id AS article_id,
        ja.journal_id,
        ja.title,
        ja.pub_year,
        (1 - (ja.abstract_embedding <=> v_query_vec))::DOUBLE PRECISION AS cosine_score
    FROM journal_articles ja
    WHERE (p_min_year IS NULL OR ja.pub_year >= p_min_year)
    ORDER BY ja.abstract_embedding <=> v_query_vec
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Sparse retrieval: top-K articles by PostgreSQL full-text search (BM25-like ts_rank)
CREATE OR REPLACE FUNCTION sparse_article_search(
    p_query_text TEXT,
    p_limit INTEGER DEFAULT 100,
    p_min_year INTEGER DEFAULT NULL
)
RETURNS TABLE (
    article_id      BIGINT,
    journal_id      INTEGER,
    title           TEXT,
    pub_year        INTEGER,
    bm25_score      DOUBLE PRECISION
) AS $$
DECLARE
    v_query_tsquery TSQUERY;
BEGIN
    v_query_tsquery := plainto_tsquery('english', p_query_text);

    RETURN QUERY
    SELECT
        ja.id AS article_id,
        ja.journal_id,
        ja.title,
        ja.pub_year,
        ts_rank(ja.article_tsv, v_query_tsquery)::DOUBLE PRECISION AS bm25_score
    FROM journal_articles ja
    WHERE ja.article_tsv @@ v_query_tsquery
      AND (p_min_year IS NULL OR ja.pub_year >= p_min_year)
    ORDER BY bm25_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Reciprocal Rank Fusion (RRF) combining dense + sparse results
CREATE OR REPLACE FUNCTION hybrid_article_search_rrf(
    p_title_embedding vector(768),
    p_abstract_embedding vector(768),
    p_query_text TEXT,
    p_limit INTEGER DEFAULT 100,
    p_min_year INTEGER DEFAULT NULL
)
RETURNS TABLE (
    article_id      BIGINT,
    journal_id      INTEGER,
    title           TEXT,
    pub_year        INTEGER,
    rrf_score       DOUBLE PRECISION,
    dense_rank      INTEGER,
    sparse_rank     INTEGER
) AS $$
DECLARE
    v_rrf_k NUMERIC;
BEGIN
    SELECT value INTO v_rrf_k FROM matcher_config WHERE key = 'rrf_k';

    RETURN QUERY
    WITH dense_results AS (
        SELECT d.article_id, d.journal_id, d.title, d.pub_year, d.cosine_score,
               ROW_NUMBER() OVER (ORDER BY d.cosine_score DESC) AS rank_num
        FROM dense_article_search(p_title_embedding, p_abstract_embedding, p_limit * 3, p_min_year) d
    ),
    sparse_results AS (
        SELECT s.article_id, s.journal_id, s.title, s.pub_year, s.bm25_score,
               ROW_NUMBER() OVER (ORDER BY s.bm25_score DESC) AS rank_num
        FROM sparse_article_search(p_query_text, p_limit * 3, p_min_year) s
    ),
    fused AS (
        SELECT
            COALESCE(d.article_id, s.article_id) AS article_id,
            COALESCE(d.journal_id, s.journal_id) AS journal_id,
            COALESCE(d.title, s.title) AS title,
            COALESCE(d.pub_year, s.pub_year) AS pub_year,
            COALESCE(1.0 / (v_rrf_k + d.rank_num), 0.0) + COALESCE(1.0 / (v_rrf_k + s.rank_num), 0.0) AS rrf_score,
            d.rank_num AS dense_rank,
            s.rank_num AS sparse_rank
        FROM dense_results d
        FULL OUTER JOIN sparse_results s ON d.article_id = s.article_id
    )
    SELECT *
    FROM fused
    ORDER BY rrf_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- STAGE C: RECENCY DECAY FUNCTION
-- =============================================================================
CREATE OR REPLACE FUNCTION recency_decay_score(
    p_pub_year INTEGER,
    p_current_year INTEGER DEFAULT EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER
)
RETURNS DOUBLE PRECISION AS $$
DECLARE
    v_lambda NUMERIC;
    v_years_ago INTEGER;
BEGIN
    SELECT value INTO v_lambda FROM matcher_config WHERE key = 'recency_lambda';
    v_years_ago := GREATEST(0, p_current_year - p_pub_year);
    RETURN EXP(-v_lambda * v_years_ago)::DOUBLE PRECISION;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =============================================================================
-- STAGE C: AGGREGATED JOURNAL MATCH SCORE
-- =============================================================================
CREATE OR REPLACE FUNCTION score_journals(
    p_title_embedding vector(768),
    p_abstract_embedding vector(768),
    p_query_text TEXT,
    p_limit INTEGER DEFAULT 20,
    p_min_year INTEGER DEFAULT NULL,
    p_max_apc_usd NUMERIC DEFAULT NULL,
    p_max_decision_days INTEGER DEFAULT NULL,
    p_require_oa BOOLEAN DEFAULT FALSE
)
RETURNS TABLE (
    journal_id          INTEGER,
    title               TEXT,
    issn                VARCHAR(20),
    semantic_score      DOUBLE PRECISION,
    recency_score       DOUBLE PRECISION,
    business_score      DOUBLE PRECISION,
    match_score         DOUBLE PRECISION,
    top_article_titles  TEXT[],
    top_article_years   INTEGER[]
) AS $$
DECLARE
    v_sem_weight NUMERIC;
    v_rec_weight NUMERIC;
    v_biz_weight NUMERIC;
BEGIN
    SELECT value INTO v_sem_weight FROM matcher_config WHERE key = 'semantic_score_weight';
    SELECT value INTO v_rec_weight FROM matcher_config WHERE key = 'recency_score_weight';
    SELECT value INTO v_biz_weight FROM matcher_config WHERE key = 'business_score_weight';

    RETURN QUERY
    WITH hybrid_articles AS (
        SELECT *
        FROM hybrid_article_search_rrf(p_title_embedding, p_abstract_embedding, p_query_text, 200, p_min_year)
    ),
    journal_scores AS (
        SELECT
            ha.journal_id,
            AVG(ha.rrf_score * recency_decay_score(ha.pub_year)) AS semantic_score,
            AVG(recency_decay_score(ha.pub_year)) AS recency_score,
            ARRAY_AGG(ha.title ORDER BY ha.rrf_score DESC) FILTER (WHERE ha.title IS NOT NULL) AS top_article_titles,
            ARRAY_AGG(ha.pub_year ORDER BY ha.rrf_score DESC) FILTER (WHERE ha.pub_year IS NOT NULL) AS top_article_years
        FROM hybrid_articles ha
        GROUP BY ha.journal_id
    ),
    business_scores AS (
        SELECT
            j.id AS journal_id,
            CASE
                WHEN j.apc_value_usd IS NULL THEN 0.5
                WHEN j.apc_value_usd = 0 THEN 1.0
                ELSE GREATEST(0.0, 1.0 - (j.apc_value_usd / 3000.0))
            END * 0.4 +
            CASE j.oa_type
                WHEN 'gold' THEN 1.0
                WHEN 'hybrid' THEN 0.7
                WHEN 'bronze' THEN 0.6
                WHEN 'green' THEN 0.5
                ELSE 0.2
            END * 0.35 +
            CASE
                WHEN j.avg_days_to_first_decision IS NULL THEN 0.5
                ELSE GREATEST(0.0, 1.0 - (j.avg_days_to_first_decision::NUMERIC / 180.0))
            END * 0.25 AS business_score
        FROM journals j
    )
    SELECT
        j.id,
        j.title,
        j.issn,
        js.semantic_score::DOUBLE PRECISION,
        js.recency_score::DOUBLE PRECISION,
        bs.business_score::DOUBLE PRECISION,
        (
            v_sem_weight * js.semantic_score +
            v_rec_weight * js.recency_score +
            v_biz_weight * bs.business_score
        )::DOUBLE PRECISION AS match_score,
        js.top_article_titles[1:5],
        js.top_article_years[1:5]
    FROM journal_scores js
    JOIN journals j ON j.id = js.journal_id
    JOIN business_scores bs ON bs.journal_id = j.id
    WHERE
        (p_max_apc_usd IS NULL OR j.apc_value_usd IS NULL OR j.apc_value_usd <= p_max_apc_usd)
        AND (p_max_decision_days IS NULL OR j.avg_days_to_first_decision IS NULL OR j.avg_days_to_first_decision <= p_max_decision_days)
        AND (NOT p_require_oa OR j.is_open_access = TRUE)
    ORDER BY match_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
