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
import requests
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
            title = self._get_col(row, "title", "Título da Revista", "Título").lower()
            grande_area = self._get_col(row, "Grande Área", "Grande Area").lower()
            area_conhecimento = self._get_col(row, "Área do Conhecimento", "Area do Conhecimento").lower()
            indexador = self._get_col(row, "Indexador").lower()
            aims_scope = self._get_col(row, "aims_scope", "description", "Aims e Escopo", "Aims e Escopo").lower()
            text = f"{title} {grande_area} {area_conhecimento} {indexador} {aims_scope}"
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
        raw_recommendations = []
        
        # Etapa 1: Ingestão e Descoberta Semântica via IA (Gemini ou Ollama)
        prompt_ia = f"""
        Você é um especialista sênior em publicação científica com profundo conhecimento das linhas editoriais de revistas acadêmicas do mundo todo.
        Analise o artigo científico abaixo e identifique as {top_n} revistas científicas com maior afinidade e aderência temática para submissão:

        TÍTULO DO ARTIGO: {titulo}
        RESUMO DO ARTIGO: {resumo}

        DIRETRIZES OBRIGATÓRIAS DE SELEÇÃO:
        1. Analise profundamente o tema, a metodologia e a abordagem teórica do artigo.
        2. Recomende revistas brasileiras (em português) e também internacionais (em inglês ou espanhol) que cubram o tema.
        3. Priorize a aderência temática e o escopo da revista — o artigo deve se alinhar perfeitamente com o que a revista publica.
        4. Traga revistas reais, ativas e com os nomes escritos de forma correta e completa.

        RESPONDA estritamente com um array JSON válido, sem comentários e sem tags markdown de código (como ```json ou ```). Use exatamente o formato:
        [
          {{
            "revista_nome": "Nome exato e oficial da revista",
            "aderencia": 95,
            "justificativa": "Uma explicação concisa de 2-3 frases de por que este artigo se alinha com o escopo desta revista específica."
          }}
        ]
        """

        if use_ollama:
            try:
                import subprocess
                result = subprocess.run(
                    ["ollama", "run", self.ollama_model],
                    input=prompt_ia,
                    capture_output=True,
                    text=True,
                    timeout=45
                )
                if result.returncode == 0:
                    match = re.search(r'\[\s*\{.*\}\s*\]', result.stdout, re.DOTALL)
                    if match:
                        raw_recommendations = json.loads(match.group(0))
                        self._backend_used = "ollama"
            except Exception as e:
                logger.warning(f"Ollama falhou no modo discovery: {e}")

        if not raw_recommendations and self.api_key_gemini:
            try:
                import requests
                # Usa gemini-2.5-flash como modelo padrão robusto
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key_gemini}"
                payload = {"contents": [{"parts": [{"text": prompt_ia}]}]}
                response = requests.post(url, json=payload, timeout=40)
                if response.ok:
                    res_json = response.json()
                    texto_resposta = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if texto_resposta.startswith("```"):
                        texto_resposta = re.sub(r'^```(?:json)?\n|```$', '', texto_resposta, flags=re.MULTILINE).strip()
                    
                    match = re.search(r'\[\s*\{.*\}\s*\]', texto_resposta, re.DOTALL)
                    if match:
                        raw_recommendations = json.loads(match.group(0))
                        self._backend_used = "gemini"
            except Exception as e:
                logger.warning(f"Gemini falhou no modo discovery: {e}")

        # Fallback local se a IA falhar na sugestão de nomes
        if not raw_recommendations:
            logger.info("Usando busca textual local como fallback de descoberta")
            candidates = self._busca_textual_fallback(titulo, resumo, top_n)
            self._backend_used = "local_fallback"
            for j in candidates:
                raw_recommendations.append({
                    "revista_nome": j["nome"],
                    "aderencia": j["aderencia"],
                    "justificativa": j["justificativa"]
                })

        # Etapa 2: Validação no Catálogo e Enriquecimento Semântico (Fuzzy Matching + OpenAlex)
        def normalizar(nome):
            import unicodedata
            nome = str(nome).lower().strip()
            nome = ''.join(c for c in unicodedata.normalize('NFD', nome) if unicodedata.category(c) != 'Mn')
            nome = re.sub(r'[^a-z0-9\s]', '', nome)
            return ' '.join(nome.split())

        def encontrar_na_base(nome_ia, df_base, threshold=0.82):
            nome_norm = normalizar(nome_ia)
            melhor_score = 0
            melhor_row = None
            
            # Primeira coluna representa o nome da revista
            col_titulo = df_base.columns[0]
            for _, row in df_base.iterrows():
                nome_base = str(row[col_titulo])
                nome_base_norm = normalizar(nome_base)
                score = SequenceMatcher(None, nome_norm, nome_base_norm).ratio()
                if score > melhor_score:
                    melhor_score = score
                    melhor_row = row
            
            if melhor_score >= threshold:
                return melhor_row, melhor_score
            return None, 0

        final_journals = []
        for rec in raw_recommendations:
            nome_ia = rec.get("revista_nome", "")
            aderencia = rec.get("aderencia", 75)
            justificativa_ia = rec.get("justificativa", "")
            
            # Tenta encontrar no catálogo local
            row_local, score_match = encontrar_na_base(nome_ia, self.df_raw)
            
            if row_local is not None:
                # Revista encontrada no catálogo
                col_titulo = self.df_raw.columns[0]
                nome_final = str(row_local[col_titulo])
                issn = str(row_local.get("ISSN", "-"))
                homepage = str(row_local.get("Homepage", "-"))
                grande_area = str(row_local.get("Grande Área", "-"))
                area = str(row_local.get("Área do Conhecimento", row_local.get("Area do Conhecimento", "-")))
                subarea = str(row_local.get("Subárea do Conhecimento", "-"))
                indexador = str(row_local.get("Indexador", "-"))
                jif = str(row_local.get("JIF", "-"))
                quartil = str(row_local.get("Quartil JCR", "-"))
                sjr = str(row_local.get("SJR", "-"))
                sjr_q = str(row_local.get("SJR Best Quartile", "-"))
                h_index = str(row_local.get("H index", row_local.get("h-index", "-")))
                h5_link = str(row_local.get("Índice h5", "-"))
                fonte = "local"
            else:
                # Revista externa ao catálogo: tenta buscar na OpenAlex pelo nome
                nome_final = nome_ia
                issn = "-"
                homepage = "-"
                grande_area = "-"
                area = "-"
                subarea = "-"
                indexador = "Não Catalogado"
                jif = "-"
                quartil = "-"
                sjr = "-"
                sjr_q = "-"
                h_index = "-"
                h5_link = f"https://scholar.google.com/citations?hl=pt-BR&view_op=search_venues&vq={requests.utils.quote(nome_ia)}&btnG="
                fonte = "externo"
                
                # Tenta OpenAlex API para enriquecimento
                try:
                    from services.openalex_client import get_openalex_client
                    client = get_openalex_client()
                    oa_journal = client.get_journal_by_name(nome_ia)
                    if oa_journal:
                        nome_final = oa_journal.get("nome", nome_ia)
                        issn = oa_journal.get("issn", "-")
                        homepage = oa_journal.get("homepage_url", "-")
                        h_index = str(oa_journal.get("h_index", "-"))
                        
                        idx_list = []
                        if oa_journal.get("is_in_doaj"):
                            idx_list.append("DOAJ")
                        if "scopus" in str(oa_journal.get("concepts", [])).lower():
                            idx_list.append("Scopus")
                        indexador = ", ".join(idx_list) if idx_list else "Open Access"
                except Exception as e:
                    logger.warning(f"Falha ao enriquecer revista externa {nome_ia} via OpenAlex: {e}")
            
            # Formata Dicionário da Revista
            j_dict = {
                "nome": nome_final,
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
                "h5_link": h5_link,
                "aderencia": aderencia,
                "justificativa": justificativa_ia,
                "fonte_dados": fonte
            }
            
            # Etapa 3: Prova Social (Artigos similares específicos por periódico)
            if issn and issn != "-":
                artigos_similares = self._buscar_artigos_similares(resumo, issn)
                if artigos_similares:
                    j_dict["artigos_similares"] = artigos_similares
            
            # Calcula probabilidade proxy de publicação
            j_dict["probabilidade_aceitacao"] = self._taxa_aceitacao_proxy(j_dict)
            
            # Se a justificativa do Gemini estiver vazia, gera uma estruturada padrão
            if not j_dict["justificativa"]:
                j_dict["justificativa"] = self._justificativa_dissertativa(j_dict, idioma)
                
            final_journals.append(j_dict)

        # Ordenação final: Aderência (1º) > Probabilidade (2º)
        final_journals.sort(key=lambda x: (-x.get("aderencia", 0), -x.get("probabilidade_aceitacao", 0)))
        return final_journals[:top_n], None

    def get_backend_name(self) -> str:
        return self._backend_used