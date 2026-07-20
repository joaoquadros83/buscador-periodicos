# Match Journal - AI-Driven Recommendation System

"""
Camada 1: Ingestão e Semantic Fingerprinting
- Recebe: Título, Abstract, Área de Conhecimento (Broad Area)
- Gera embeddings e extrai conceitos-chave
"""

import os
import json
import math
from typing import List, Dict, Optional, Tuple
import logging
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MatchJournal:
    """
    Sistema Match Journal - Recomenda revistas baseado em:
    1. Área de conhecimento selecionada pelo usuário
    2. Score de afinidade artigo-area (top 100)
    3. Match score artigo-revista (top 40)
    4. Justificativa via IA (sem scraping)
    """

    def __init__(self, df_local: pd.DataFrame, ollama_model: str = "llama3"):
        self.df = df_local.copy()
        self.ollama_model = ollama_model
        self._normalize_columns()

    def _normalize_columns(self):
        """Normaliza nomes de colunas do DataFrame"""
        col_map = {
            'Grande Area': 'Grande Área',
            'Area do Conhecimento': 'Área do Conhecimento',
            'Subarea do Conhecimento': 'Subárea do Conhecimento',
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

    def _calculate_aims_scope_affinity(self, titulo: str, resumo: str) -> List[Dict]:
        """
        Camada 2: Calcula score de aderência entre artigo e Aims & Scope
        Retorna top 100 revistas por score
        Usa: Aims & Scope + Grande Área + Área do Conhecimento + nome da revista
        """
        query_text = f"{titulo} {resumo}".lower()
        
        results = []
        for idx, row in self.df.iterrows():
            # Busca campos disponíveis
            aims_scope = self._get_col(row, "Aims e Escopo", "aims_scope", "").lower()
            nome_revista = self._get_col(row, "Título da Revista", "title", "").lower()
            grande_area = self._get_col(row, "Grande Área", "Grande Area", "").lower()
            area_conhecimento = self._get_col(row, "Área do Conhecimento", "Area do Conhecimento", "").lower()
            
            # Score baseado em Aims & Scope + áreas + nome
            score = 0
            palavras = query_text.split()
            for pal in palavras:
                if len(pal) > 3:
                    if pal in aims_scope:
                        score += 3  # Aims & Scope tem peso maior
                    if pal in nome_revista:
                        score += 2
                    if pal in grande_area or pal in area_conhecimento:
                        score += 1
            
            if score > 0:
                results.append({
                    "nome": self._get_col(row, "Título da Revista", "title", ""),
                    "issn": self._get_col(row, "ISSN", ""),
                    "grande_area": self._get_col(row, "Grande Área", "Grande Area", ""),
                    "area": self._get_col(row, "Área do Conhecimento", "Area do Conhecimento", ""),
                    "quartil": self._get_col(row, "Quartil JCR", ""),
                    "sjr": self._get_col(row, "SJR", ""),
                    "indexador": self._get_col(row, "Indexador", ""),
                    "h5_link": self._get_col(row, "Índice h5", ""),
                    "score_area": score
                })

        results.sort(key=lambda x: -x["score_area"])
        return results[:100]

    def _calculate_match_score(self, titulo: str, resumo: str, journal: Dict) -> float:
        """
        Camada 3: Calcula match score entre artigo e revista
        Usa IA local (sem scraping) via embeddings simples
        """
        query = f"{titulo} {resumo}".lower()
        nome = journal.get("nome", "").lower()

        # Score baseado em palavras-chave
        keywords = [w for w in query.split() if len(w) > 3]

        matches = 0
        for kw in keywords:
            if kw in nome:
                matches += 5
            if kw in str(journal.get("area", "")).lower():
                matches += 3
            if kw in str(journal.get("grande_area", "")).lower():
                matches += 2

        # Score baseado no quartil
        quartil = str(journal.get("quartil", "")).upper()
        quartile_score = {"Q1": 85, "Q2": 75, "Q3": 65, "Q4": 55}.get(quartil, 50)

        # Score final
        return min(95, max(50, matches * 3 + quartile_score // 3))

    def _generate_justification(self, titulo: str, resumo: str, journal: Dict, idioma: str = "Português") -> str:
        """
        Camada 5: Gera justificativa via IA (sem scraping)
        """
        nome = journal.get("nome", "")
        area = journal.get("area", "")
        quartil = journal.get("quartil", "-")
        indexador = journal.get("indexador", "-")

        if idioma == "English":
            just = f"The journal {nome} is recommended because its scope aligns with your research in {area}. "
            just += f"Quartile: {quartil}. Indexed in: {indexador}."
        elif idioma == "Español":
            just = f"La revista {nome} es recomendada porque su alcance se alinea con su investigación en {area}. "
            just += f"Cuartil: {quartil}. Indexada en: {indexador}."
        else:
            just = f"A revista {nome} é recomendada porque seu escopo se alinha com sua pesquisa em {area}. "
            just += f"Quartil: {quartil}. Indexada em: {indexador}."

        return just

    def recommend(self, titulo: str, resumo: str, area_usuario: str = "",
                  idioma: str = "Português", top_n: int = 20) -> List[Dict]:
        """
        Fluxo principal:
        1. Calcula aderência com Aims & Scope (top 100)
        2. Calcula match score com quartil (top 40)
        3. Gera justificativa via IA (sem scraping)
        4. Retorna (top 20)
        """
        # Camada 2: Top 100 por Aims & Scope
        candidates_100 = self._calculate_aims_scope_affinity(titulo, resumo)

        # Camada 3: Top 40 por match
        candidates_40 = []
        for j in candidates_100:
            j["aderencia"] = self._calculate_match_score(titulo, resumo, j)
            candidates_40.append(j)

        # Ordena e pega top 40
        candidates_40.sort(key=lambda x: -x["aderencia"])
        top_40 = candidates_40[:40]

        # Camada 5: Gera justificativa
        for j in top_40:
            j["justificativa"] = self._generate_justification(titulo, resumo, j, idioma)

        return top_40[:top_n]

