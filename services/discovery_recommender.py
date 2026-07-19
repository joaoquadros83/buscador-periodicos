"""
Discovery Recommender (Otimizado)
Motor de recomendação baseado em:
  1. Classificação da área do artigo
  2. Busca vetorial por similaridade de cosseno (com vetores pré-computados)
  3. Probabilidade proxy de publicação
  4. Justificativa estruturada baseada em métricas (até 3 linhas)
"""

import re
import requests
import os
import pickle
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
import logging

from prompts.discovery_prompt import get_justification_prompt
from services.embeddings_client import EmbeddingsClient, cosine_similarity
from services.area_classifier import classify_article_area
from services.cache_manager import get_cache_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscoveryRecommender:
    """Motor de recomendação rápido por classificação de área + busca vetorial + proxy"""

    def __init__(
        self,
        df_local: pd.DataFrame,
        api_key_gemini: Optional[str] = None,
        ollama_model: str = "llama3",
        embeddings_model: str = "nomic-embed-text",
        h_index_author: int = 5
    ):
        self.df_local = df_local
        self.api_key_gemini = api_key_gemini
        self.ollama_model = ollama_model
        self.h_index_author = h_index_author
        self.embeddings_client = EmbeddingsClient(model=embeddings_model, gemini_api_key=api_key_gemini)
        self.cache_manager = get_cache_manager()
        self._backend_used = "unknown"
        self.catalog_texts = []
        self.catalog_vectors = []
        self._load_vectors()

    def _load_vectors(self):
        """Carrega vetores pré-computados do catálogo, se disponíveis"""
        cache_path = "data/journal_vectors.pkl"
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "rb") as f:
                    data = pickle.load(f)
                self.catalog_texts = data.get("texts", [])
                self.catalog_vectors = data.get("vectors", [])
                vocab = data.get("vocab")
                idf = data.get("idf")
                if vocab is not None and idf is not None:
                    self.embeddings_client.load_pretrained_tfidf(vocab, idf)
                logger.info(f"Vetores pré-computados carregados: {len(self.catalog_vectors)} revistas")
                return
            except Exception as e:
                logger.warning(f"Erro ao carregar vetores pré-computados: {e}")

        logger.info("Computando vetores do catálogo em memória...")
        self._build_catalog_texts()
        self.embeddings_client.fit_tfidf(self.catalog_texts)
        self.catalog_vectors = self.embeddings_client.embed_batch(self.catalog_texts)

    def _build_catalog_texts(self):
        texts = []
        for idx, row in self.df_local.iterrows():
            nome = str(row.get("title", idx))
            partes = [nome]
            for col in ["Grande Área", "Área do Conhecimento", "Subárea do Conhecimento", "Indexador", "ISSN", "Homepage"]:
                if col in row.index:
                    val = str(row[col])
                    if val and val not in ["-", "nan", "None", ""]:
                        partes.append(val)
            texts.append(" ".join(partes))
        self.catalog_texts = texts

    def get_backend_name(self) -> str:
        return self._backend_used

    def _call_llm_fast(self, prompt: str) -> Optional[str]:
        if self.api_key_gemini:
            try:
                return self._call_gemini(prompt, timeout=10)
            except Exception:
                pass
        try:
            import ollama
            response = ollama.generate(
                model=self.ollama_model,
                prompt=prompt,
                stream=False,
                options={"num_predict": 250, "temperature": 0.7}
            )
            return response.get("response", "")
        except Exception:
            return None

    def _call_gemini(self, prompt: str, timeout: int = 15) -> Optional[str]:
        modelos = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
        for modelo in modelos:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={self.api_key_gemini}"
                response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]},
                                         headers={"Content-Type": "application/json"}, timeout=timeout)
                if response.status_code == 200:
                    return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                else:
                    logger.warning(f"Gemini {modelo} retornou {response.status_code}: {response.text[:200]}")
            except Exception as e:
                logger.warning(f"Erro ao chamar Gemini {modelo}: {e}")
                continue
        return None

    def _classificar_artigo(self, titulo: str, resumo: str) -> Dict:
        return classify_article_area(titulo, resumo)

    def _busca_vetorial(self, query_text: str, df_candidatos: pd.DataFrame, top_k: int = 40) -> List[Dict]:
        indices = []
        for idx in df_candidatos.index:
            try:
                pos = self.df_local.index.get_loc(idx)
                if isinstance(pos, slice):
                    pos = pos.start
                indices.append((idx, int(pos)))
            except Exception:
                continue

        query_vector = self.embeddings_client.embed(query_text)

        similarities = []
        for df_idx, vec_idx in indices:
            if vec_idx < len(self.catalog_vectors):
                sim = cosine_similarity(query_vector, self.catalog_vectors[vec_idx])
                similarities.append((df_idx, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)

        results = []
        for df_idx, sim in similarities[:top_k]:
            try:
                row = self.df_local.loc[df_idx]
                nome = str(row.get("title", df_idx))
                results.append({
                    "nome": nome,
                    "issn": str(row.get("ISSN", "-")) if len(row) > 0 else "-",
                    "homepage": str(row.get("Homepage", "-")) if len(row) > 0 else "-",
                    "grande_area": str(row.get("Grande Área", "-")) if len(row) > 0 else "-",
                    "area": str(row.get("Área do Conhecimento", row.get("Area do Conhecimento", "-"))) if len(row) > 0 else "-",
                    "subarea": str(row.get("Subárea do Conhecimento", "-")) if len(row) > 0 else "-",
                    "indexador": str(row.get("Indexador", "-")) if len(row) > 0 else "-",
                    "jif": row.get("JIF", "-") if len(row) > 0 else "-",
                    "quartil_jcr": str(row.get("Quartil JCR", "-")) if len(row) > 0 else "-",
                    "sjr": str(row.get("SJR", "-")) if len(row) > 0 else "-",
                    "sjr_quartile": str(row.get("SJR Best Quartile", "-")) if len(row) > 0 else "-",
                    "h_index": row.get("H index", row.get("h-index", "-")) if len(row) > 0 else "-",
                    "h5_link": str(row.get("Índice h5", "-")) if len(row) > 0 else "-",
                    "similaridade": sim,
                    "aderencia": round(sim * 100, 1),
                    "fonte_dados": "local",
                })
            except Exception as e:
                logger.warning(f"Erro ao processar revista {df_idx}: {e}")
                continue

        if not results and similarities:
            results.append({
                "nome": str(similarities[0][0]),
                "issn": "-",
                "homepage": "-",
                "grande_area": "-",
                "area": "-",
                "subarea": "-",
                "indexador": "-",
                "jif": "-",
                "quartil_jcr": "-",
                "sjr": "-",
                "sjr_quartile": "-",
                "h_index": "-",
                "h5_link": "-",
                "similaridade": similarities[0][1],
                "aderencia": round(similarities[0][1] * 100, 1),
                "fonte_dados": "local",
            })

        return results

    def _taxa_aceitacao_historica(self, journal: Dict) -> float:
        quartil = str(journal.get("quartil_jcr", "")).upper()
        sjr_q = str(journal.get("sjr_quartile", "")).upper()
        taxa = 35.0
        if quartil == "Q1" or sjr_q == "Q1":
            taxa = 18.0
        elif quartil == "Q2" or sjr_q == "Q2":
            taxa = 28.0
        elif quartil == "Q3" or sjr_q == "Q3":
            taxa = 38.0
        elif quartil == "Q4" or sjr_q == "Q4":
            taxa = 48.0
        elif quartil in ["-", "", "N/A"] and sjr_q in ["-", "", "N/A"]:
            taxa = 42.0

        indexador = str(journal.get("indexador", "")).lower()
        indexadores_list = [i.strip() for i in indexador.split(",") if i.strip()]
        reconhecidos = ["wos", "scopus", "scielo", "educ@", "doaj"]
        count = sum(1 for idx in indexadores_list if any(r in idx for r in reconhecidos))
        if count >= 3:
            taxa -= 5
        elif count == 0:
            taxa += 5

        return max(5.0, min(taxa, 80.0))

    def _penalidade_incompatibilidade(self, journal: Dict, classificacao: Dict) -> float:
        area_artigo = classificacao.get("grande_area", "").lower()
        area_revista = str(journal.get("grande_area", "")).lower()

        if not area_artigo or not area_revista or area_artigo == area_revista:
            return 1.0

        proximas = {
            "ciências humanas": ["linguística, letras e artes", "ciências sociais aplicadas"],
            "linguística, letras e artes": ["ciências humanas"],
            "ciências sociais aplicadas": ["ciências humanas", "linguística, letras e artes"],
            "ciências da saúde": ["ciências biológicas"],
            "ciências biológicas": ["ciências da saúde", "ciências agrárias"],
            "engenharias": ["ciências exatas e da terra"],
            "ciências exatas e da terra": ["engenharias"]
        }

        for prox in proximas.get(area_artigo, []):
            if prox in area_revista:
                return 0.75

        return 0.45

    def _h_index_revista(self, journal: Dict) -> float:
        h = journal.get("h_index", "-")
        try:
            return float(h) if h not in [None, "-", "N/A", "", "nan"] else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _calcular_probabilidade_proxy(self, journal: Dict, classificacao: Dict) -> float:
        taxa = self._taxa_aceitacao_historica(journal)
        penalidade = self._penalidade_incompatibilidade(journal, classificacao)

        h_revista = self._h_index_revista(journal)
        if h_revista > 0:
            ratio = self.h_index_author / max(h_revista * 0.1, 1.0)
            fator_h = min(1.05, max(0.85, ratio))
        else:
            fator_h = 1.0

        probabilidade = taxa * penalidade * fator_h
        return round(min(probabilidade, 70.0), 1)

    def recommend(
        self,
        titulo: str,
        resumo: str,
        idioma: str = "Português",
        top_n: int = 20,
        use_ollama: bool = False
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        cache_key = f"rec_v3_{hash(titulo + resumo + str(top_n) + idioma)}"
        cached = self.cache_manager.get(cache_key)
        if cached:
            cached.sort(key=lambda x: (x.get("aderencia", 0), x.get("probabilidade_aceitacao", 0)), reverse=True)
            return cached, None

        query_text = f"{titulo} {resumo}"

        classificacao = self._classificar_artigo(titulo, resumo)
        area_artigo = classificacao.get("grande_area", "")

        df_candidatos = self.df_local.copy()
        if area_artigo and area_artigo != "Outras / Não Classificado":
            col_area = "Grande Área"
            if col_area in df_candidatos.columns:
                mask = df_candidatos[col_area].astype(str).str.contains(area_artigo, case=False, na=False)
                df_filtrado = df_candidatos[mask]
                if len(df_filtrado) >= 20:
                    df_candidatos = df_filtrado

        candidates = self._busca_vetorial(query_text, df_candidatos, top_k=40)
        if not candidates:
            return None, "Nenhuma revista encontrada no catálogo."

        seen = set()
        diversified = []
        for j in candidates:
            key = (
                str(j.get("nome", "")).strip().lower(),
                str(j.get("area", "")).strip().lower(),
                str(j.get("indexador", "")).strip().lower(),
            )
            if key in seen:
                continue
            seen.add(key)
            diversified.append(j)
        candidates = diversified

        for j in candidates:
            j["probabilidade_aceitacao"] = self._calcular_probabilidade_proxy(j, classificacao)
            j["classificacao_area"] = classificacao

        def _parse_num(val):
            try:
                v = float(val)
                if pd.notna(v):
                    return v
            except (ValueError, TypeError):
                pass
            return 0.0

        def _quartil_score(q):
            q = str(q).upper().replace("Q", "").strip()
            try:
                n = int(q)
                return 5 - n
            except (ValueError, TypeError):
                return 0

        def _score(j):
            return (
                j.get("aderencia", 0),
                j.get("probabilidade_aceitacao", 0),
                _parse_num(j.get("sjr", 0)),
                _parse_num(j.get("jif", 0)),
                _parse_num(j.get("h_index", 0)),
                _quartil_score(j.get("quartil_jcr", "")),
            )

        candidates.sort(key=_score, reverse=True)
        top_journals = candidates[:top_n]

        min_ad = 60
        max_ad = 95
        ad_range = max(1.0, max_ad - min_ad)
        max_sim = max((j.get("similaridade", 0) for j in top_journals), default=1.0)
        if max_sim > 0:
            for j in top_journals:
                sim = j.get("similaridade", 0)
                ad_base = min_ad + (sim / max_sim) * ad_range
                j["aderencia"] = round(min(ad_base, max_ad), 1)

        max_prob = max((j.get("probabilidade_aceitacao", 0) for j in top_journals), default=1.0)
        min_prob = 15.0
        max_prob_cap = 70.0
        prob_range = max(1.0, max_prob_cap - min_prob)
        if max_prob > 0:
            for j in top_journals:
                prob = j.get("probabilidade_aceitacao", 0)
                prob_norm = min_prob + (prob / max_prob) * prob_range
                j["probabilidade_aceitacao"] = round(min(prob_norm, max_prob_cap), 1)

        self._backend_used = "vetorial"
        for j in top_journals:
            j["justificativa"] = self._justificativa_estruturada(j, classificacao, idioma)

        self.cache_manager.set(cache_key, top_journals, ttl=86400)
        return top_journals, None

    def _justificativa_estruturada(self, journal: Dict, classificacao: Dict, idioma: str) -> str:
        nome = journal.get("nome", "")
        aderencia = journal.get("aderencia", 0)
        probabilidade = journal.get("probabilidade_aceitacao", 0)
        area_journal = journal.get("grande_area", "-")
        area_artigo = classificacao.get("grande_area", "-")
        quartil = journal.get("quartil_jcr", "-")
        sjr = journal.get("sjr", "-")
        indexador = journal.get("indexador", "-")

        def fmt_num(v):
            try:
                f = float(v)
                return str(round(f, 1)) if pd.notna(f) else "-"
            except (ValueError, TypeError):
                return "-"

        if str(quartil).strip() != "-":
            impact_line = f"Quartil: {quartil}."
        elif str(sjr).strip() != "-":
            impact_line = f"SJR: {fmt_num(sjr)}."
        else:
            impact_line = "Prestígio: não classificado."

        index_line = f"Indexação: {indexador}."

        if idioma == "English":
            return (
                f"{nome} aligns with the article scope in {area_journal}, with {aderencia}% thematic fit "
                f"and estimated {probabilidade}% publication probability. "
                f"{impact_line} {index_line}"
            )
        elif idioma == "Español":
            return (
                f"{nome} se alinea con el alcance del artículo en {area_journal}, con {aderencia}% de ajuste temático "
                f"y probabilidad estimada de publicación del {probabilidade}%. "
                f"{impact_line} {index_line}"
            )
        return (
            f"{nome} alinha-se ao escopo do artigo em {area_journal}, com {aderencia}% de aderência temática "
            f"e probabilidade estimada de {probabilidade}%. "
            f"{impact_line} {index_line}"
        )