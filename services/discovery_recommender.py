"""
Discovery Recommender (Semantic Discovery - SciSpace Style)
Arquitetura em 3 fases:
  1. INGESTÃO & FINGERPRINTING (Gemini) - Descoberta de revistas via conhecimento enciclopédico
  2. KNOWLEDGE GRAPH & ENRIQUECIMENTO - Fuzzy matching + dados OpenAlex
  3. PROVA SOCIAL - Artigos similares por ISSN via OpenAlex
"""

import re
import requests
import os
import json
import time
from typing import List, Dict, Optional, Tuple
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscoveryRecommender:
    """Motor de recomendação baseado em descoberta semântica via IA"""

    def __init__(
        self,
        df_local: pd.DataFrame,
        api_key_gemini: Optional[str] = None,
        ollama_model: str = "llama3",
        h_index_author: int = 5
    ):
        self.df_local = df_local.reset_index(drop=True)
        self.api_key_gemini = api_key_gemini
        self.ollama_model = ollama_model
        self.h_index_author = h_index_author
        self._backend_used = "semantic_discovery"

    def _call_gemini_discovery(self, titulo: str, resumo: str, idioma: str) -> List[Dict]:
        """Fase 1: Gemini sugere 40 revistas via conhecimento enciclopédico de escopos"""
        prompt = self._build_discovery_prompt(titulo, resumo, idioma)
        
        try:
            # Tenta usar Ollama primeiro (gratuito)
            import subprocess
            result = subprocess.run(
                ["ollama", "run", self.ollama_model, "--json"],
                input=json.dumps({"prompt": prompt, "stream": False}),
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                response = json.loads(result.stdout)
                return self._parse_gemini_response(response.get("response", ""))
        except Exception as e:
            logger.warning(f"Ollama falhou, tentando Gemini API: {e}")
        
        # Fallback para Gemini API se disponível
        if self.api_key_gemini:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={self.api_key_gemini}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                response = requests.post(url, json=payload, timeout=30)
                if response.ok:
                    return self._parse_gemini_response(response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", ""))
            except Exception as e:
                logger.error(f"Gemini API falhou: {e}")
        
        return []

    def _build_discovery_prompt(self, titulo: str, resumo: str, idioma: str) -> str:
        lang_map = {"Português": "pt", "English": "en", "Español": "es"}
        lang = lang_map.get(idioma, "pt")
        
        return f"""
Analise este artigo científico e retorne JSON com 40 revistas periódicas que melhor se adequam ao seu escopo editorial.

TÍTULO: {titulo}
RESUMO: {resumo}

Critérios:
1. Aderência temática (prioridade máxima) - escopo editorial da revista vs tema do artigo
2. Diversifique: inclua revistas brasileiras e internacionais
3. Inclua dados: nome da revista, ISSN, área principal, quartil/SJR se souber, justificativa

Retorne APENAS JSON:
[
  {{
    "nome": "Nome da Revista",
    "issn": "1234-5678",
    "aderencia": 95,
    "area": "Nome da Área",
    "quartil": "Q1",
    "justificativa": "Texto explicativo"
  }}
]
""".strip()

    def _parse_gemini_response(self, text: str) -> List[Dict]:
        try:
            # Extrai JSON da resposta
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            logger.error(f"Erro ao parsear resposta Gemini: {e}")
        return []

    def _fuzzy_match_local(self, nome_revista: str) -> Optional[pd.Series]:
        """Fase 2: Fuzzy matching no catálogo local por nome/ISSN"""
        from difflib import SequenceMatcher
        
        melhor_match = None
        melhor_score = 0
        
        for idx, row in self.df_local.iterrows():
            for col in ["title", "ISSN", "Nome da Revista"]:
                if col in self.df_local.columns:
                    valor = str(row.get(col, ""))
                    score = SequenceMatcher(None, nome_revista.lower(), valor.lower()).ratio()
                    if score > melhor_score and score > 0.82:
                        melhor_score = score
                        melhor_match = row
        
        return melhor_match

    def _enriquecer_openalex(self, issn: str) -> Dict:
        """Enriquece dados via OpenAlex API"""
        try:
            from services.openalex_client import get_openalex_client
            client = get_openalex_client()
            journal_data = client.get_journal_by_issn(issn)
            if journal_data:
                return {
                    "h_index": journal_data.get("h_index", "-"),
                    "citacoes_anuais": journal_data.get("cited_by_count", 0),
                    "open_access": journal_data.get("open_access", {}).get("is_oa", False),
                }
        except Exception as e:
            logger.warning(f"Falha ao enriquecer via OpenAlex: {e}")
        return {}

    def _buscar_artigos_similares(self, resumo: str, issn: str) -> List[Dict]:
        """Fase 3: Prova social - artigos similares publicados na revista"""
        try:
            from services.openalex_client import get_openalex_client
            client = get_openalex_client()
            return client.search_similar_articles_by_journal(resumo, issn, per_page=3)
        except Exception as e:
            logger.warning(f"Falha ao buscar artigos similares: {e}")
        return []

    def _taxa_aceitacao_proxy(self, journal: Dict) -> float:
        """Calcula probabilidade proxy baseado em métricas da revista"""
        quartil = str(journal.get("quartil", "")).upper()
        sjr = float(str(journal.get("sjr", "0")).replace(",", ".")) if journal.get("sjr") else 0
        
        if quartil == "Q1" or sjr > 3.0:
            base = 18.0
        elif quartil == "Q2" or sjr > 1.5:
            base = 28.0
        elif quartil == "Q3" or sjr > 0.5:
            base = 38.0
        elif quartil == "Q4":
            base = 48.0
        else:
            base = 42.0  # Revistas não classificadas têm taxa maior
        
        return round(min(base, 70.0), 1)

    def _justificativa_dissertativa(self, journal: Dict, idioma: str) -> str:
        """Gera justificativa dissertativa completa"""
        nome = journal.get("nome", "")
        aderencia = journal.get("aderencia", 75)
        probabilidade = journal.get("probabilidade_aceitacao", 45)
        area = journal.get("area", "")
        quartil = journal.get("quartil", "")
        sjr = journal.get("sjr", "")
        indexador = journal.get("indexador", "")
        
        if idioma == "English":
            just = f"The journal {nome} is recommended because its editorial scope aligns with the research area '{area}'. "
            just += f"It shows {aderencia}% thematic alignment and an estimated {probabilidade}% probability of acceptance. "
            if quartil and quartil != "-":
                just += f"Ranked in {quartil} JCR quartile, reflecting significant reputation. "
            elif sjr:
                just += f"SJR score of {sjr} indicates international visibility. "
            just += f"Indexed in: {indexador}."
            return just
        elif idioma == "Español":
            just = f"La revista {nome} es recomendada porque su alcance editorial se alinea con el área de investigación '{area}'. "
            just += f"Muestra {aderencia}% de alineación temática y probabilidad estimada de {probabilidade}%. "
            if quartil and quartil != "-":
                just += f"Clasificada en cuartil {quartil} JCR, reflejando prestigio relevante. "
            elif sjr:
                just += f"Puntuación SJR de {sjr} indica visibilidad internacional. "
            just += f"Indexada en: {indexador}."
            return just
        else:
            just = f"A revista {nome} é recomendada porque seu escopo editorial se alinha com a área de pesquisa '{area}'. "
            just += f"Apresenta {aderencia}% de aderência temática e probabilidade estimada de {probabilidade}%. "
            if quartil and quartil != "-":
                just += f"Classificada no {quartil}º quartil do JCR, refletindo prestígio na área. "
            elif sjr:
                just += f"SJR de {sjr} indica boa visibilidade internacional. "
            just += f"Indexada em: {indexador}."
            return just

    def recommend(
        self,
        titulo: str,
        resumo: str,
        idioma: str = "Português",
        top_n: int = 20
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        # Fase 1: Descoberta via Gemini
        candidatos_gemini = self._call_gemini_discovery(titulo, resumo, idioma)
        
        if not candidatos_gemini:
            return None, "Erro ao consultar IA para descoberta de revistas."

        # Fase 2: Enriquecimento com dados locais e OpenAlex
        resultados_finais = []
        for candidato in candidatos_gemini[:top_n]:
            nome = candidato.get("nome", "")
            issn = candidato.get("issn", "")
            
            # Fuzzy match no catálogo local
            match_local = self._fuzzy_match_local(nome) if issn else None
            
            journal = {
                "nome": nome,
                "issn": issn,
                "aderencia": candidato.get("aderencia", 75),
                "area": candidato.get("area", ""),
                "quartil": candidato.get("quartil", "-"),
                "sjr": candidato.get("sjr", "-"),
                "indexador": candidato.get("indexador", "-"),
                "justificativa": candidato.get("justificativa", ""),
                "fonte_dados": "local" if match_local is not None else "descoberta"
            }
            
            # Enriquece com dados locais
            if match_local is not None:
                journal["quartil"] = str(match_local.get("Quartil JCR", journal["quartil"]))
                journal["sjr"] = str(match_local.get("SJR", journal["sjr"]))
                journal["indexador"] = str(match_local.get("Indexador", journal["indexador"]))
                journal["h5_link"] = str(match_local.get("Índice h5", "-"))
            
            # Enriquece com OpenAlex se ISSN disponível
            if issn:
                oa_data = self._enriquecer_openalex(issn)
                journal.update(oa_data)
            
            journal["probabilidade_aceitacao"] = self._taxa_aceitacao_proxy(journal)
            
            # Fase 3: Prova social - artigos similares
            if issn:
                artigos_similares = self._buscar_artigos_similares(resumo, issn)
                if artigos_similares:
                    journal["artigos_similares"] = artigos_similares[:2]
            
            # Gera justificativa dissertativa
            journal["justificativa"] = self._justificativa_dissertativa(journal, idioma)
            
            resultados_finais.append(journal)

        # Ordena por aderência + probabilidade
        resultados_finais.sort(key=lambda x: (-x.get("aderencia", 0), -x.get("probabilidade_aceitacao", 0)))
        
        return resultados_finais[:top_n], None

    def get_backend_name(self) -> str:
        return self._backend_used