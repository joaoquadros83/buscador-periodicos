# Match Journal V2 - Semantic Kernel Style (Python + LLM Orchestration)

"""
Camada 1: Ingestão e Semantic Fingerprinting com LLM Orchestration
- Similar ao Semantic Kernel mas usando Ollama/Gemini local (100% gratuito)
- Orquestração via funções Python para classificação e embeddings
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
    Usa Ollama/Gemini via funções Python (gratuito)
    """
    
    def __init__(self, model: str = "llama3"):
        self.model = model
        self.vectorizer = TfidfVectorizer(max_features=512, stop_words=None)
    
    def _classify_broad_area(self, titulo: str, resumo: str) -> str:
        """Classifica Broad Area usando LLM via prompt"""
        prompt = f"""
Classifique o artigo abaixo em uma única "Broad Area":
- Computer Science
- Medicine
- Social Sciences  
- Engineering
- Biological Sciences
- Arts & Humanities
- Agricultural Sciences
- Health Sciences
- Exact Sciences

Título: {titulo}
Resumo: {resumo[:500]}

Retorne APENAS o nome da Broad Area.
"""
        try:
            import ollama
            response = ollama.generate(model=self.model, prompt=prompt, stream=False)
            return response.get("response", "").strip()
        except Exception:
            # Fallback: classificação por palavras-chave
            text = f"{titulo} {resumo}".lower()
            mapping = {
                "computer": "Computer Science", "software": "Computer Science",
                "medicine": "Medicine", "medical": "Medicine", "health": "Health Sciences",
                "social": "Social Sciences", "educação": "Social Sciences",
                "engineering": "Engineering", "engenharia": "Engineering",
                "biology": "Biological Sciences", "biológica": "Biological Sciences",
            }
            for kw, area in mapping.items():
                if kw in text:
                    return area
            return "Social Sciences"  # Default
    
    def _calculate_adherence_score(self, 
        titulo_embedding: np.ndarray, resumo_embedding: np.ndarray,
        aims_scope: str) -> float:
        """Calcula Adherence Score via similaridade de cosseno"""
        try:
            combined_text = f"{titulo_embedding} {resumo_embedding} {aims_scope}"
            vecs = self.vectorizer.fit_transform([combined_text, aims_scope]).toarray()
            sim = cosine_similarity([vecs[0]], [vecs[1]])[0][0]
            return round(sim * 100, 2)
        except Exception:
            return 50.0


class MatchJournalV2:
    """
    Match Journal V2 com pipeline atualizado:
    1. Classificação por Broad Area (LLM)
    2. Filtro primário por Broad Area
    3. Adherence Score (vetorial + LLM)
    4. Estimated Acceptance Probability
    5. Ordenamento dinâmico (A-Z, Adherence, Probability)
    """
    
    def __init__(self, df_local: pd.DataFrame, llm_model: str = "llama3"):
        self.df = df_local.copy()
        self.kernel = SemanticKernelStyle(model=llm_model)
        self._normalize_columns()
    
    def _normalize_columns(self):
        col_map = {
            'Grande Area': 'Grande Área',
            'Area do Conhecimento': 'Área do Conhecimento',
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
        Pipeline V2:
        1. Classifica Broad Area via LLM
        2. Filtra revistas pela Broad Area
        3. Calcula Adherence Score para todas
        4. Calcula Estimated Acceptance Probability
        5. Ordena por critério escolhido
        """
        # Camada 1: Classificação Broad Area
        broad_area = self.kernel._classify_broad_area(titulo, resumo)
        
        # Camada 2: Filtro primário
        df_filtered = self.df[
            self.df["Grande Área"].str.lower().str.contains(broad_area.lower(), na=False)
        ].copy()
        
        if df_filtered.empty:
            df_filtered = self.df.head(200).copy()  # Fallback
        
        # Camada 3: Adherence Score
        query_vec = f"{titulo} {resumo}"
        adherence_scores = []
        for idx, row in df_filtered.iterrows():
            aims_scope = self._get_col(row, "Aims e Escopo", "aims_scope", "")
            score = self.kernel._calculate_adherence_score(query_vec, resumo, aims_scope)
            adherence_scores.append(score)
        
        df_filtered["adherence_score"] = adherence_scores
        
        # Camada 4: Estimated Acceptance Probability
        probabilities = []
        for idx, row in df_filtered.iterrows():
            adh = row["adherence_score"]
            quartil = str(self._get_col(row, "Quartil JCR", "")).upper()
            
            # Fórmula ponderada
            # Q1 reduz probabilidade (mais competitivo)
            # Q4 aumenta probabilidade (menos competitivo)
            quartile_factor = {"Q1": 0.7, "Q2": 0.8, "Q3": 0.9, "Q4": 1.0}.get(quartil, 0.85)
            
            prob = min(95, max(30, adh * quartile_factor - 10))
            probabilities.append(round(prob, 1))
        
        df_filtered["probability"] = probabilities
        
        # Camada 5: Ordenamento dinâmico
        order_map = {
            "az": ("Título da Revista", True),
            "adherence": ("adherence_score", False),
            "probability": ("probability", False),
        }
        col_order, asc = order_map.get(order_by, ("probability", False))
        
        if col_order in df_filtered.columns:
            df_filtered = df_filtered.sort_values(by=col_order, ascending=asc)
        
        # Retorna apenas revistas com probability > 60%
        top_results = df_filtered[df_filtered["probability"] > 60].head(top_n)
        
        results = []
        for idx, row in top_results.iterrows():
            results.append({
                "nome": self._get_col(row, "Título da Revista", "title", ""),
                "issn": self._get_col(row, "ISSN", ""),
                "grande_area": self._get_col(row, "Grande Área", ""),
                "area": self._get_col(row, "Área do Conhecimento", ""),
                "quartil": self._get_col(row, "Quartil JCR", ""),
                "sjr": self._get_col(row, "SJR", ""),
                "indexador": self._get_col(row, "Indexador", ""),
                "h5_link": self._get_col(row, "Índice h5", ""),
                "adherence_score": row.get("adherence_score", 50),
                "probability": row.get("probability", 50),
                "justificativa": f"Adherence: {row.get('adherence_score', 50)}%. Quartil: {self._get_col(row, 'Quartil JCR', 'N/A')}."
            })
        
        return results


# UI Component Mock (para integração no Streamlit)
def create_sort_selector():
    """Componente de ordenamento para UI"""
    return """
    st.radio(
        "Ordenar por:",
        options=["probability", "adherence", "az"],
        format_func=lambda x: {
            "probability": "📊 Estimated Acceptance Probability",
            "adherence": "🎯 Adherence Score", 
            "az": "🔤 A-Z"
        }[x],
        horizontal=True
    )
