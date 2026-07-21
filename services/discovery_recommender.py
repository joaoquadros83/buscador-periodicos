"""
Discovery Recommender (Semantic & Vector Matcher for SciPubs)
Arquitetura em 4 Camadas:
  1. INGESTÃO & KNOWLEDGE AREA CLASSIFICATION (Gemini / LLM)
  2. VETORIZAÇÃO E ADHERENCE SCORE (Cosseno no Aims & Scope -> Top 300)
  3. ESTIMATED ACCEPTANCE PROBABILITY ENGINE (Top 40)
  4. ORDENAÇÃO DINÂMICA & JUSTIFICATIVA CONTEXTUAL (3-4 linhas) -> Top 20
"""

import re
import os
import json
import requests
from typing import List, Dict, Optional, Tuple
import logging
import pandas as pd
from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscoveryRecommender:
    """Motor de recomendação semântico de revistas científicas."""

    def __init__(
        self,
        df_local: pd.DataFrame,
        api_key_gemini: Optional[str] = None,
        ollama_model: str = "llama3",
        h_index_author: int = 5
    ):
        self.df_raw = df_local.copy()
        self.df_local = self._normalize_columns(df_local)
        self.api_key_gemini = api_key_gemini
        self.ollama_model = ollama_model
        self.h_index_author = h_index_author
        self._backend_used = "semantic_engine"
        
        # Usa toda a base de dados - Aims & Scope será priorizado quando disponível
        self.df_scoped = self.df_local.copy()
            
        if len(self.df_scoped) == 0:
            self.df_scoped = self.df_local.copy()

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        rename_map = {}
        for col in df.columns:
            col_str = str(col).strip()
            col_lower = col_str.lower()
            if any(x in col_lower for x in ["titulo da revista", "título da revista", "title"]):
                rename_map[col] = "title"
            elif "issn" in col_lower:
                rename_map[col] = "ISSN"
            elif "homepage" in col_lower:
                rename_map[col] = "Homepage"
            elif any(x in col_lower for x in ["grande area", "grande área"]):
                rename_map[col] = "Grande Área"
            elif any(x in col_lower for x in ["area do conhecimento", "área do conhecimento"]):
                rename_map[col] = "Área do Conhecimento"
            elif any(x in col_lower for x in ["subárea", "subarea"]):
                rename_map[col] = "Subárea do Conhecimento"
            elif "indexador" in col_lower:
                rename_map[col] = "Indexador"
            elif "quartil jcr" in col_lower:
                rename_map[col] = "Quartil JCR"
            elif "sjr" in col_lower and "best" not in col_lower:
                rename_map[col] = "SJR"
            elif "jif" in col_lower or "impact" in col_lower:
                rename_map[col] = "JIF"
            elif "h index" in col_lower or "h-index" in col_lower:
                rename_map[col] = "H index"
            elif any(x in col_lower for x in ["indice h5", "índice h5"]):
                rename_map[col] = "Índice h5"
            elif any(x in col_lower for x in ["mediana h5", "h5 median"]):
                rename_map[col] = "Mediana h5"
            elif any(x in col_lower for x in ["aims and scope", "aims e escopo", "escopo"]):
                rename_map[col] = "Aims e Escopo"
        df.rename(columns=rename_map, inplace=True)
        return df

    def _classify_knowledge_area_llm(self, titulo: str, resumo: str) -> str:
        """Camada 1: Identifica a Knowledge Area / Broad Area do manuscrito via LLM."""
        if not self.api_key_gemini:
            return "General"

        prompt = f"""
        Classifique o manuscrito científico abaixo em uma única Knowledge Area primária (ex: Computer Science, Medicine, Education, Arts, Psychology, Social Sciences, Engineering, Biological Sciences, Business):

        TÍTULO: {titulo}
        RESUMO: {resumo}

        Responda apenas com o nome da Knowledge Area em inglês.
        """
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key_gemini}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            r = requests.post(url, json=payload, timeout=10)
            if r.ok:
                area = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                return area
        except Exception as e:
            logger.warning(f"Erro na classificação por área via LLM: {e}")
        return "General"

    def _compute_vector_adherence(self, titulo: str, resumo: str) -> List[Tuple[int, float]]:
        """Camada 2: Calcula a Similaridade de Cosseno (TF-IDF Vector Matcher) entre o manuscrito e os Aims & Scope das revistas."""
        user_text = f"{titulo} {resumo}"
        
        col_scope = "Aims e Escopo" if "Aims e Escopo" in self.df_scoped.columns else "title"
        scopes = self.df_scoped[col_scope].astype(str).tolist()
        titles = self.df_scoped["title"].astype(str).tolist()
        
        # Concatena título + escopo para enriquecimento vetorial
        corpus = [f"{t} {s}" for t, s in zip(titles, scopes)]
        
        try:
            vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(corpus)
            user_vector = vectorizer.transform([user_text])
            
            sims = cosine_similarity(user_vector, tfidf_matrix).flatten()
            
            results = []
            for idx, score in enumerate(sims):
                # Normaliza para escala 0 - 100%
                norm_score = min(98.0, max(45.0, score * 100 * 2.8 + 45.0))
                results.append((idx, round(norm_score, 1)))
                
            results.sort(key=lambda x: -x[1])
            return results
        except Exception as e:
            logger.warning(f"Erro ao calcular similaridade vetorial: {e}")
            return [(i, 65.0) for i in range(len(self.df_scoped))]

    def _calculate_estimated_acceptance_probability(self, adherence_score: float, row: pd.Series) -> float:
        """Camada 3: Calcula a Probabilidade Estimada de Aceitação (0 - 100%)."""
        quartil = str(row.get("Quartil JCR", row.get("SJR Best Quartile", ""))).upper().strip()
        try:
            sjr = float(str(row.get("SJR", "0")).replace(",", "."))
        except:
            sjr = 0.0

        # Base de probabilidade em função do rigor do quartil / impacto
        if "Q1" in quartil or sjr > 2.5:
            base_prob = 22.0
        elif "Q2" in quartil or sjr > 1.2:
            base_prob = 34.0
        elif "Q3" in quartil or sjr > 0.4:
            base_prob = 46.0
        elif "Q4" in quartil:
            base_prob = 58.0
        else:
            base_prob = 50.0

        # Ponderação: 60% Aderência Semântica + 40% Fator Quartil/Aceitação Base
        prob = (adherence_score * 0.55) + (base_prob * 0.45)
        return round(min(95.0, max(15.0, prob)), 1)

    def _generate_3line_justification(self, titulo: str, resumo: str, journal_name: str, scope: str, adherence: float) -> str:
        """Gera uma justificativa dissertativa contextual de até 4 linhas relacionando o artigo com o escopo da revista."""
        if not self.api_key_gemini:
            return f"A revista {journal_name} apresenta {adherence}% de aderência semântica. Seu escopo editorial cobre a linha temática do artigo, proporcionando boa receptividade para publicação."

        prompt = f"""
        Como parecerista acadêmico, escreva uma justificativa dissertativa de EXATAMENTE 3 a 4 linhas explicando por que o artigo abaixo é recomendado para a revista '{journal_name}'.

        TÍTULO DO ARTIGO: {titulo}
        RESUMO DO ARTIGO: {resumo}
        AIMS & SCOPE DA REVISTA: {scope[:500]}
        SCORE DE ADERÊNCIA: {adherence}%

        Diretrizes:
        1. Escreva em Português corrido em parágrafo único de 3 a 4 linhas.
        2. Relacione diretamente o tema/metodologia do artigo com a linha editorial e o público leitor da revista.
        3. Não use tópicos ou listas.
        """
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key_gemini}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            r = requests.post(url, json=payload, timeout=12)
            if r.ok:
                just = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                return just
        except Exception as e:
            logger.warning(f"Erro ao gerar justificativa textual via Gemini: {e}")
            
        return f"A revista {journal_name} apresenta {adherence}% de aderência semântica com a pesquisa proposta. Seu escopo editorial contempla abordagens metodológicas e teóricas similares às desenvolvidas no manuscrito, garantindo visibilidade e público leitor qualificado."

    def recommend(
        self,
        titulo: str,
        resumo: str,
        idioma: str = "Português",
        top_n: int = 20,
        use_ollama: bool = False
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        
        logger.info(f"Iniciando recomendação semântica para catálogo de {len(self.df_scoped)} revistas com Aims & Scope.")
        
        # Camada 1: Classificação por Knowledge Area
        knowledge_area = self._classify_knowledge_area_llm(titulo, resumo)
        logger.info(f"Knowledge Area identificada via LLM: {knowledge_area}")

        # Camada 2: Similaridade Vetorial Cosseno (Top 300)
        vector_matches = self._compute_vector_adherence(titulo, resumo)
        top_300_indices = vector_matches[:300]

        # Camada 3: Motor de Cálculo da Estimated Acceptance Probability (Top 40)
        top_40_candidates = []
        for idx_scoped, score_adherence in top_300_indices:
            row = self.df_scoped.iloc[idx_scoped]
            prob_aceitacao = self._calculate_estimated_acceptance_probability(score_adherence, row)
            
            top_40_candidates.append({
                "idx_scoped": idx_scoped,
                "row": row,
                "aderencia": score_adherence,
                "probabilidade_aceitacao": prob_aceitacao
            })

        # Seleciona as 40 com maior Adherence Score e ordena por Adherence Score (Decrescente)
        top_40_candidates.sort(key=lambda x: -x["aderencia"])
        selected_candidates = top_40_candidates[:40]

        # Camada 4: Justificativa Textual Contextual e Formatação para Top 20
        final_journals = []
        col_scope = "Aims e Escopo" if "Aims e Escopo" in self.df_scoped.columns else "title"

        for item in selected_candidates:
            row = item["row"]
            nome_rev = str(row.get("title", row.get(self.df_scoped.columns[0], "")))
            issn = str(row.get("ISSN", "-"))
            homepage = str(row.get("Homepage", "-"))
            grande_area = str(row.get("Grande Área", "-"))
            area = str(row.get("Área do Conhecimento", "-"))
            subarea = str(row.get("Subárea do Conhecimento", "-"))
            indexador = str(row.get("Indexador", "-"))
            jif = str(row.get("JIF", "-"))
            quartil = str(row.get("Quartil JCR", "-"))
            sjr = str(row.get("SJR", "-"))
            sjr_q = str(row.get("SJR Best Quartile", "-"))
            h_index = str(row.get("H index", "-"))
            h5_idx = str(row.get("Índice h5", "-"))
            h5_med = str(row.get("Mediana h5", "-"))
            scope_text = str(row.get(col_scope, ""))

            # Link do Scholar para h5 se não houver link direto
            h5_link = f"https://scholar.google.com/citations?hl=pt-BR&view_op=search_venues&vq={requests.utils.quote(nome_rev)}&btnG="

            # Gera a justificativa de 3-4 linhas
            justificativa = self._generate_3line_justification(
                titulo, resumo, nome_rev, scope_text, item["aderencia"]
            )

            j_dict = {
                "nome": nome_rev,
                "issn": issn,
                "homepage": homepage,
                "grande_area": grande_area,
                "area": area,
                "subarea": subarea,
                "indexador": indexador,
                "jif": jif,
                "quartil_jcr": quartil,
                "sjr": sjr,
                "sjr_quartile": sjr_q,
                "h_index": h_index,
                "h5_index": h5_idx,
                "h5_median": h5_med,
                "h5_link": h5_link,
                "adherence_score": item["aderencia"],
                "probability": item["probabilidade_aceitacao"],
                "aderencia": item["aderencia"],
                "probabilidade_aceitacao": item["probabilidade_aceitacao"],
                "justificativa": justificativa,
                "justificativa_metricas": justificativa,
                "aims_scope": scope_text,
                "fonte_dados": "local_scoped"
            }
            final_journals.append(j_dict)

        # Ordena decrescente por Adherence Score (grau de afinidade)
        final_journals.sort(key=lambda x: -x["adherence_score"])
        return final_journals[:top_n], None

    def get_backend_name(self) -> str:
        return self._backend_used