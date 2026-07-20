# Match Journal V2 - Pipeline Refinado (Semantic Kernel Style)

"""
Camada 1: Ingestao, Semantic Fingerprinting e Selecao por Knowledge Area
Camada 2: Similaridade Vetorial + Similaridade LLM (Top 300)
Camada 3: Estimated Acceptance Probability (Top 40)
Camada 4: Ordenamento Dinamico + Output (Top 20)
"""

import os
import json
import re
from typing import List, Dict, Optional, Tuple
import logging
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SemanticKernelStyle:
    """
    Orquestrador semelhante ao Semantic Kernel para LLMs
    Usa Ollama/Gemini local (100% gratuito)
    """

    def __init__(self, model: str = "llama3"):
        self.model = model
        self.vectorizer = TfidfVectorizer(max_features=512, stop_words=None)

    def _classify_knowledge_area(self, titulo: str, resumo: str) -> str:
        """Camada 1: Classifica Knowledge Area via LLM"""
        prompt = f"""
Classifique o artigo abaixo em uma unica "Knowledge Area" (Subarea do Conhecimento):

Lista de Knowledge Areas:
- Computer Science / Medicine / Education / Arts / Engineering
- Biological Sciences / Social Sciences / Health Sciences
- Agricultural Sciences / Exact Sciences / Linguistics
- Psychology / Law / Economics / Music / Philosophy
- History / Geography / Physics / Chemistry / Mathematics
- Materials Science / Environmental Science / Neuroscience
- Nursing / Dentistry / Veterinary / Pharmacy
- Physical Education / Nutrition / Public Health
- Biotechnology / Agronomy / Forestry / Fisheries
- Architecture / Urban Planning / Demography
- Political Science / Anthropology / Sociology
- Theology / Communications / Information Science
- Multidisciplinary

Titulo: {titulo}
Resumo: {resumo[:800]}

Retorne APENAS o nome da Knowledge Area em ingles.
"""
        try:
            import ollama
            response = ollama.generate(model=self.model, prompt=prompt, stream=False)
            return response.get("response", "").strip()
        except Exception:
            text = f"{titulo} {resumo}".lower()
            mapping = {
                "education": "Education", "music": "Music",
                "computer": "Computer Science", "medicine": "Medicine",
                "health": "Health Sciences", "social": "Social Sciences",
                "psychology": "Psychology", "engineering": "Engineering",
                "biology": "Biological Sciences", "arts": "Arts",
                "law": "Law", "economics": "Economics",
                "physics": "Physics",
            }
            for kw, area in mapping.items():
                if kw in text:
                    return area
            return "Multidisciplinary"

    def _calculate_adherence_score(self, query_text: str, aims_scope: str) -> float:
        """Camada 2: Similaridade Vetorial (Cosseno)"""
        try:
            if not aims_scope or aims_scope == "":
                return 30.0
            combined = [query_text, aims_scope]
            vecs = self.vectorizer.fit_transform(combined).toarray()
            sim = cosine_similarity([vecs[0]], [vecs[1]])[0][0]
            return round(max(30, min(95, sim * 100 + 30)), 2)
        except Exception:
            return 50.0


class MatchJournalV2:
    """
    Match Journal V2 - Pipeline Refinado:

    Camada 1: Knowledge Area via LLM
    Camada 2: Filtro por Knowledge Area
    Camada 3: Adherence Score (todas as revistas)
    Camada 4: Top 300 (conjunto secundario)
    Camada 5: Estimated Acceptance Probability
    Camada 6: Top 40 (conjunto terciario)
    Camada 7: Ordenamento Dinamico
    Camada 8: Output Top 20 (probability > 60%)
    """

    def __init__(self, df_local: pd.DataFrame, llm_model: str = "llama3"):
        self.df = df_local.copy()
        self.kernel = SemanticKernelStyle(model=llm_model)
        self._normalize_columns()

    def _normalize_columns(self):
        col_map = {
            'Grande Area': 'Grande Area',
            'Area do Conhecimento': 'Area do Conhecimento',
            'Subarea do Conhecimento': 'Subarea do Conhecimento',
        }
        for old, new in col_map.items():
            if old in self.df.columns:
                self.df = self.df.rename(columns={old: new})

    def _get_col(self, row: pd.Series, *candidates: str) -> str:
        for col in candidates:
            if col in row.index:
                val = row.get(col, "")
                if pd.notna(val):
                    return str(val).strip()
        return ""

    def recommend(self, titulo: str, resumo: str,
                  order_by: str = "probability", top_n: int = 20) -> List[Dict]:
        """
        Pipeline completo V2:

        Etapa 1: Classifica Knowledge Area via LLM
        Etapa 2: Filtra revistas pela Knowledge Area
        Etapa 3: Calcula Adherence Score para todas
        Etapa 4: Refina para Top 300
        Etapa 5: Calcula Estimated Acceptance Probability
        Etapa 6: Refina para Top 40
        Etapa 7: Ordena por criterio escolhido
        Etapa 8: Retorna Top 20 com probability > 60%
        """
        query_text = f"{titulo} {resumo}"

        # --- CAMADA 1: Knowledge Area ---
        knowledge_area = self.kernel._classify_knowledge_area(titulo, resumo)
        logger.info(f"Knowledge Area: {knowledge_area}")

        # --- CAMADA 2: Filtro por Knowledge Area ---
        df_filtered = self.df[
            self.df["Subarea do Conhecimento"].str.lower().str.contains(
                knowledge_area.lower(), na=False
            ) |
            self.df["Area do Conhecimento"].str.lower().str.contains(
                knowledge_area.lower(), na=False
            )
        ].copy()

        if df_filtered.empty:
            df_filtered = self.df[
                self.df["Grande Area"].str.lower().str.contains(
                    knowledge_area.lower(), na=False
                )
            ].copy()

        if df_filtered.empty:
            logger.warning(f"Knowledge Area '{knowledge_area}' nao encontrada. Fallback top 500.")
            df_filtered = self.df.head(500).copy()

        # --- CAMADA 3: Adherence Score (Similaridade Vetorial) ---
        adherence_scores = []
        for idx, row in df_filtered.iterrows():
            aims_scope = self._get_col(row, "Aims e Escopo", "aims_scope", "")
            nome_rev = self._get_col(row, "Titulo da Revista", "title", "")
            area = self._get_col(row, "Area do Conhecimento", "Area do Conhecimento", "")
            score_scope = self.kernel._calculate_adherence_score(query_text, aims_scope)
            texto_revista = f"{nome_rev} {area}"
            score_nome = self.kernel._calculate_adherence_score(query_text, texto_revista)
            score_combinado = round(score_scope * 0.7 + score_nome * 0.3, 2)
            adherence_scores.append(score_combinado)

        df_filtered["adherence_score"] = adherence_scores

        # --- CAMADA 4: Top 300 (conjunto secundario) ---
        df_filtered = df_filtered.sort_values(by="adherence_score", ascending=False)
        df_secondary = df_filtered.head(300).copy()

        # --- CAMADA 5: Estimated Acceptance Probability ---
        probabilities = []
        for idx, row in df_secondary.iterrows():
            adh = row["adherence_score"]
            quartil = str(self._get_col(row, "Quartil JCR", "")).upper()
            quartile_factor = {"Q1": 0.65, "Q2": 0.78, "Q3": 0.88, "Q4": 0.95}.get(quartil, 0.82)
            prob = min(95, max(30, round(adh * quartile_factor - 5, 1)))
            probabilities.append(prob)

        df_secondary["probability"] = probabilities

        # --- CAMADA 6: Top 40 (conjunto terciario) ---
        df_tertiary = df_secondary.head(40).copy()

        # --- CAMADA 7: Ordenamento Dinamico ---
        order_map = {
            "az": ("Titulo da Revista", True),
            "adherence": ("adherence_score", False),
            "probability": ("probability", False),
        }
        col_order, asc = order_map.get(order_by, ("probability", False))
        if col_order in df_tertiary.columns:
            df_tertiary = df_tertiary.sort_values(by=col_order, ascending=asc)

        # --- CAMADA 8: Output Top 20 com probability > 60% ---
        top_results = df_tertiary[df_tertiary["probability"] > 60].head(top_n)

        results = []
        for idx, row in top_results.iterrows():
            nome = self._get_col(row, "Titulo da Revista", "title", "")
            quartil = self._get_col(row, "Quartil JCR", "N/A")
            adh = row.get("adherence_score", 50)
            prob = row.get("probability", 50)

            justificativa = (
                f"Knowledge Area: {knowledge_area}. "
                f"Adherence: {adh}%. "
                f"Quartil: {quartil}. "
                f"Probability: {prob}%."
            )

            results.append({
                "nome": nome,
                "issn": self._get_col(row, "ISSN", ""),
                "grande_area": self._get_col(row, "Grande Area", ""),
                "area": self._get_col(row, "Area do Conhecimento", ""),
                "subarea": self._get_col(row, "Subarea do Conhecimento", ""),
                "quartil": quartil,
                "sjr": self._get_col(row, "SJR", ""),
                "indexador": self._get_col(row, "Indexador", ""),
                "h5_link": self._get_col(row, "Indice h5", ""),
                "adherence_score": adh,
                "probability": prob,
                "justificativa": justificativa,
            })

        return results