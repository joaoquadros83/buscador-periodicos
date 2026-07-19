"""
Discovery Recommender (Semantic Discovery - SciSpace Style)
Arquitetura em 3 fases:
  1. INGESTÃO & FINGERPRINTING (Gemini/Ollama) - Descoberta de revistas via conhecimento enciclopédico
  2. KNOWLEDGE GRAPH & ENRIQUECIMENTO - Fuzzy matching + dados OpenAlex
  3. PROVA SOCIAL - Artigos similares por ISSN via OpenAlex

FALLBACK: Busca textual local inteligente + métricas quando IA não disponível
"""

import re
import os
import json
from typing import List, Dict, Optional, Tuple
import logging
import pandas as pd
from difflib import SequenceMatcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscoveryRecommender:
    """Motor de recomendação baseado em descoberta semântica via IA + fallback local"""

    # Mapeamento semântico: palavras-chave -> áreas relevantes
    KEYWORD_AREA_MAP = {
        # Educação & Psicometria
        "educação": "Ciências Sociais",
        "ensino": "Ciências Sociais", 
        "aprendizagem": "Ciências Sociais",
        "psicometria": "Ciências Sociais",
        "instrumento": "Ciências Sociais",
        "avaliação": "Ciências Sociais",
        "reaproximação": "Ciências Sociais",
        "permanência": "Ciências Sociais",
        "evasão": "Ciências Sociais",
        "freire": "Ciências Sociais",
        "humanização": "Ciências Sociais",
        "music": "Artes",
        "música": "Artes",
        "artistic": "Artes",
        "arte": "Artes",
        # Interdisciplinar
        "interdisciplinar": "Interdisciplinar",
    }

    def __init__(
        self,
        df_local: pd.DataFrame,
        api_key_gemini: Optional[str] = None,
        ollama_model: str = "llama3",
        h_index_author: int = 5
    ):
        self.df_local = self._normalize_columns(df_local)
        self.df_raw = df_local
        self.api_key_gemini = api_key_gemini
        self.ollama_model = ollama_model
        self.h_index_author = h_index_author
        self._backend_used = "local_fallback"
        self._build_search_index()

    def _get_col(self, row: pd.Series, *candidates: str) -> str:
        for col in candidates:
            if col in row.index:
                val = row.get(col, "")
                if pd.notna(val):
                    return str(val)
        return ""

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
        df.rename(columns=rename_map, inplace=True)
        return df

    def _infer_area_from_text(self, titulo: str, resumo: str) -> List[str]:
        """Infere áreas relevantes baseado em palavras-chave do texto"""
        text = f"{titulo} {resumo}".lower()
        areas_found = set()
        for keyword, area in self.KEYWORD_AREA_MAP.items():
            if keyword in text:
                areas_found.add(area)
        return list(areas_found) if areas_found else ["Interdisciplinar"]

    def _build_search_index(self):
        self.search_texts = []
        for idx, row in self.df_local.iterrows():
            title = self._get_col(row, "title").lower()
            grande_area = self._get_col(row, "Grande Área").lower()
            area_conhecimento = self._get_col(row, "Área do Conhecimento").lower()
            indexador = self._get_col(row, "Indexador").lower()
            text = f"{title} {grande_area} {area_conhecimento} {indexador}"
            self.search_texts.append((idx, text, grande_area, area_conhecimento))

    def _busca_textual_fallback(self, titulo: str, resumo: str, top_n: int = 40) -> List[Dict]:
        """Busca textual inteligente com priorização semântica"""
        query = f"{titulo} {resumo}".lower()
        
        # Detecta áreas relevantes do artigo
        areas_relevantes = self._infer_area_from_text(titulo, resumo)
        
        # Palavras-chave do artigo
        keywords = [w for w in re.findall(r'\b\w{4,}\b', query)]
        
        results = []
        for idx, text, grande_area, area_conhecimento in self.search_texts:
            # Score baseado em matches de palavras-chave
            score_keywords = sum(1 for kw in keywords if kw in text)
            
            # Bonus por área alinhada
            score_area = 0
            for area in areas_relevantes:
                if area.lower() in grande_area or area.lower() in area_conhecimento:
                    score_area += 10
            
            # Bonus para revistas de educação
            if "educação" in text or "education" in text or "ensino" in text:
                score_area += 15
            if "psicometria" in text or "psychometric" in text or "instrumento" in text:
                score_area += 20
            if "música" in text or "music" in text:
                score_area += 5
            
            total_score = score_keywords + score_area
            
            if total_score > 0:
                row = self.df_local.iloc[idx]
                results.append({
                    "nome": self._get_col(row, "title"),
                    "issn": self._get_col(row, "ISSN"),
                    "aderencia": min(95, max(60, total_score * 5)),
                    "area": self._get_col(row, "Grande Área"),
                    "quartil": self._get_col(row, "Quartil JCR"),
                    "sjr": self._get_col(row, "SJR"),
                    "indexador": self._get_col(row, "Indexador"),
                    "h5_link": self._get_col(row, "Índice h5"),
                    "homepage": self._get_col(row, "Homepage"),
                    "fonte_dados": "local"
                })
        
        # Ordena por score
        results.sort(key=lambda x: -x["aderencia"])
        return results[:top_n]

    def _enriquecer_openalex(self, issn: str) -> Dict:
        try:
            from services.openalex_client import get_openalex_client
            client = get_openalex_client()
            journal_data = client.get_journal_by_issn(issn)
            if journal_data:
                return {
                    "h_index": str(journal_data.get("h_index", "-")),
                    "open_access": journal_data.get("open_access", {}).get("is_oa", False),
                }
        except Exception as e:
            logger.warning(f"Falha ao enriquecer via OpenAlex: {e}")
        return {}

    def _buscar_artigos_similares(self, resumo: str, issn: str) -> List[Dict]:
        try:
            from services.openalex_client import get_openalex_client
            client = get_openalex_client()
            return client.search_similar_articles_by_journal(resumo, issn, per_page=2)
        except Exception as e:
            logger.warning(f"Falha ao buscar artigos similares: {e}")
        return []

    def _taxa_aceitacao_proxy(self, journal: Dict) -> float:
        quartil = str(journal.get("quartil", "")).upper()
        try:
            sjr = float(str(journal.get("sjr", "0")).replace(",", "."))
        except:
            sjr = 0
        
        if quartil == "Q1" or sjr > 3.0:
            base = 18.0
        elif quartil == "Q2" or sjr > 1.5:
            base = 28.0
        elif quartil == "Q3" or sjr > 0.5:
            base = 38.0
        elif quartil == "Q4":
            base = 48.0
        else:
            base = 42.0
        
        return round(min(max(base, 15.0), 70.0), 1)

    def _justificativa_dissertativa(self, journal: Dict, idioma: str) -> str:
        nome = journal.get("nome", "")
        aderencia = journal.get("aderencia", 75)
        probabilidade = journal.get("probabilidade_aceitacao", 45)
        area = journal.get("area", journal.get("Grande Área", "-"))
        quartil = journal.get("quartil", "")
        sjr = journal.get("sjr", "")
        indexador = journal.get("indexador", "-")

        if idioma == "English":
            just = f"The journal {nome} is recommended because its editorial scope aligns with the research area '{area}'. "
            just += f"It shows {aderencia}% thematic alignment and an estimated {probabilidade}% probability of acceptance. "
            if quartil and quartil not in ["-", "", "nan"]:
                just += f"Ranked in {quartil} JCR quartile, reflecting significant reputation. "
            elif sjr and sjr not in ["-", "", "nan"]:
                just += f"SJR score of {sjr} indicates international visibility. "
            just += f"Indexed in: {indexador}."
            return just
        elif idioma == "Español":
            just = f"La revista {nome} es recomendada porque su alcance editorial se alinea con el área de investigación '{area}'. "
            just += f"Muestra {aderencia}% de alineación temática y probabilidad estimada de {probabilidade}%. "
            if quartil and quartil not in ["-", "", "nan"]:
                just += f"Clasificada en cuartil {quartil} JCR, reflejando prestigio relevante. "
            elif sjr and sjr not in ["-", "", "nan"]:
                just += f"Puntuación SJR de {sjr} indica visibilidad internacional. "
            just += f"Indexada en: {indexador}."
            return just
        else:
            just = f"A revista {nome} é recomendada porque seu escopo editorial se alinha com a área de pesquisa '{area}'. "
            just += f"Apresenta {aderencia}% de aderência temática e uma probabilidade estimada de {probabilidade}% de aceitação. "
            if quartil and quartil not in ["-", "", "nan"]:
                just += f"Classificada no {quartil}º quartil do JCR, refletindo seu prestígio na área. "
            elif sjr and sjr not in ["-", "", "nan"]:
                just += f"SJR de {sjr} indica boa visibilidade internacional. "
            just += f"Indexada em: {indexador}."
            return just

    def recommend(
        self,
        titulo: str,
        resumo: str,
        idioma: str = "Português",
        top_n: int = 20,
        use_ollama: bool = False
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        journals = []

        if use_ollama:
            try:
                import subprocess
                prompt = f"""Retorne JSON com {top_n} revistas:
TÍTULO: {titulo}
RESUMO: {resumo}
Formato: [{{"nome": "...", "issn": "...", "aderencia": 85, "area": "...", "quartil": "..."}}]"""
                result = subprocess.run(
                    ["ollama", "run", self.ollama_model],
                    input=prompt,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    match = re.search(r'\[.*\]', result.stdout, re.DOTALL)
                    if match:
                        journals = json.loads(match.group())
                        self._backend_used = "ollama"
            except Exception as e:
                logger.warning(f"Ollama falhou: {e}")

        if not journals and self.api_key_gemini:
            try:
                import requests
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={self.api_key_gemini}"
                prompt = f"""Retorne JSON com {top_n} revistas:
TÍTULO: {titulo}
RESUMO: {resumo}
Formato: [{{"nome": "...", "issn": "...", "aderencia": 85, "area": "...", "quartil": "..."}}]"""
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                response = requests.post(url, json=payload, timeout=30)
                if response.ok:
                    match = re.search(r'\[.*\]', response.text, re.DOTALL)
                    if match:
                        journals = json.loads(match.group())
                        self._backend_used = "gemini"
            except Exception as e:
                logger.warning(f"Gemini falhou: {e}")

        if not journals:
            logger.info("Usando fallback de busca textual local")
            journals = self._busca_textual_fallback(titulo, resumo, top_n)
            self._backend_used = "local_fallback"

        if not journals:
            return None, "Nenhuma revista encontrada no catálogo."

        for j in journals:
            issn = j.get("issn", "")
            if issn:
                oa_data = self._enriquecer_openalex(issn)
                j.update(oa_data)
                artigos_similares = self._buscar_artigos_similares(resumo, issn)
                if artigos_similares:
                    j["artigos_similares"] = artigos_similares
            j["probabilidade_aceitacao"] = self._taxa_aceitacao_proxy(j)

        for j in journals:
            j["justificativa"] = self._justificativa_dissertativa(j, idioma)

        journals.sort(key=lambda x: (-x.get("aderencia", 0), -x.get("probabilidade_aceitacao", 0)))

        return journals[:top_n], None

    def get_backend_name(self) -> str:
        return self._backend_used