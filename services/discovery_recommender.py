"""
Discovery Recommender
Motor de recomendação Discovery-First com suporte a Gemini API + Ollama + fallback local
Arquitetura: Gemini (primário, nuvem) → Ollama (local, dev) → Algoritmo local (fallback)
"""

import json
import re
import requests
import pandas as pd
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from prompts.discovery_prompt import get_discovery_prompt
from utils.fuzzy_matcher import find_journal_in_dataframe, find_journal_by_issn
from services.openalex_client import get_openalex_client
from services.scielo_client import get_scielo_client
from services.cache_manager import get_cache_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscoveryRecommender:
    """Motor de recomendação Discovery-First com fallback automático"""
    
    def __init__(
        self,
        df_local: pd.DataFrame,
        api_key_gemini: Optional[str] = None,
        ollama_model: str = "llama3",
        email_openalex: Optional[str] = None
    ):
        """
        Inicializa o motor de recomendação
        
        Args:
            df_local: DataFrame com base local de revistas
            api_key_gemini: Chave API Gemini (opcional, para modo nuvem)
            ollama_model: Modelo Ollama a usar (default: llama3)
            email_openalex: Email para politeness OpenAlex
        """
        self.df_local = df_local
        self.api_key_gemini = api_key_gemini
        self.ollama_model = ollama_model
        self.openalex_client = get_openalex_client(email_openalex)
        self.scielo_client = get_scielo_client()
        self.cache_manager = get_cache_manager()
        self._backend_used = "unknown"
    
    def get_backend_name(self) -> str:
        """Retorna qual backend foi usado na última recomendação"""
        return self._backend_used
    
    def _call_gemini(self, prompt: str, timeout: int = 30) -> Optional[str]:
        """
        Faz chamada à API Gemini (Google)
        
        Args:
            prompt: Prompt para enviar ao modelo
            timeout: Timeout em segundos
            
        Returns:
            Texto da resposta ou None em caso de erro
        """
        if not self.api_key_gemini:
            return None
            
        modelos_tentar = [
            "gemini-2.0-flash",
            "gemini-2.0-flash-001",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ]
        
        ultimo_erro = ""
        for modelo in modelos_tentar:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={self.api_key_gemini}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}]
                }
                headers = {"Content-Type": "application/json"}
                
                response = requests.post(url, json=payload, headers=headers, timeout=timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
                elif response.status_code == 429:
                    logger.warning(f"Gemini quota exceeded for model {modelo}")
                    return None  # Quota exceeded, try fallback
                else:
                    ultimo_erro = f"Modelo {modelo} falhou (Status {response.status_code})"
                    logger.warning(ultimo_erro)
            except requests.exceptions.Timeout:
                ultimo_erro = f"Timeout no modelo {modelo}"
                logger.warning(ultimo_erro)
            except Exception as ex:
                ultimo_erro = f"Exceção no modelo {modelo}: {ex}"
                logger.warning(ultimo_erro)
        
        logger.error(f"Todos os modelos Gemini falharam. Último erro: {ultimo_erro}")
        return None
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """
        Faz chamada ao Ollama local
        
        Args:
            prompt: Prompt para enviar ao modelo
            
        Returns:
            Texto da resposta ou None em caso de erro
        """
        try:
            import ollama
            response = ollama.generate(
                model=self.ollama_model,
                prompt=prompt,
                stream=False,
                options={"num_predict": 2000, "temperature": 0.7}
            )
            return response.get("response", "")
        except ImportError:
            logger.warning("Ollama não instalado")
            return None
        except Exception as e:
            logger.warning(f"Erro ao chamar Ollama: {e}")
            return None
    
    def _parse_ai_response(self, texto: str) -> Optional[List[Dict]]:
        """
        Parseia a resposta JSON da IA
        
        Args:
            texto: Texto bruto da resposta da IA
            
        Returns:
            Lista de dicionários ou None se falhar
        """
        if not texto:
            return None
        
        # Remove markdown code blocks se houver
        if texto.startswith("```"):
            texto = re.sub(r'^```(?:json)?\n?|```$', '', texto, flags=re.MULTILINE).strip()
        
        # Tenta encontrar array JSON
        match = re.search(r'\[\s*\{.*\}\s*\]', texto, re.DOTALL)
        if match:
            texto = match.group(0)
        
        try:
            raw_list = json.loads(texto)
            if not isinstance(raw_list, list):
                return None
            
            # Normaliza para formato interno
            results = []
            for item in raw_list:
                jname = item.get("revista_nome", item.get("journal_name", item.get("nome", "")))
                pct = item.get("porcentagem_aderencia", item.get("adherence_score", item.get("aderencia", 0)))
                if isinstance(pct, str):
                    pct = int(re.sub(r'\D', '', pct)) if re.sub(r'\D', '', pct) else 50
                just = item.get("justificativa", item.get("justification", item.get("motivo", "")))
                
                results.append({
                    "nome": jname,
                    "aderencia": min(max(pct, 0), 100),
                    "justificativa": just
                })
            
            return results
        
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao parsear JSON da IA: {e}")
            return None
    
    def _enriquecer_revistas(self, resultados: List[Dict]) -> List[Dict]:
        """
        Enriquece recomendações com dados da base local e OpenAlex
        
        Args:
            resultados: Lista de dicionários com recomendações básicas
            
        Returns:
            Lista enriquecida com dados completos
        """
        enriquecidas = []
        
        for item in resultados:
            nome = item.get("nome", "")
            if not nome:
                continue
            
            # Busca na base local
            match, _ = find_journal_in_dataframe(nome, self.df_local)
            
            enriched = {
                "nome": nome,
                "issn": item.get("issn", "-"),
                "homepage": item.get("homepage", ""),
                "grande_area": item.get("grande_area", "-"),
                "area": item.get("area", "-"),
                "subarea": item.get("subarea", "-"),
                "indexador": item.get("indexador", "-"),
                "jif": item.get("jif", "-"),
                "quartil_jcr": item.get("quartil_jcr", "-"),
                "sjr": item.get("sjr", "-"),
                "sjr_quartile": item.get("sjr_quartile", "-"),
                "h_index": item.get("h_index", "-"),
                "h5_link": item.get("h5_link", "-"),
                "aderencia": item.get("aderencia", 50),
                "justificativa": item.get("justificativa", ""),
                "fonte_dados": "ia",
            }
            
            if match is not None:
                row = match
                enriched["issn"] = str(row.get("ISSN", enriched["issn"]))
                enriched["homepage"] = str(row.get("Homepage", enriched["homepage"]))
                enriched["grande_area"] = str(row.get("Grande Área", enriched["grande_area"]))
                enriched["area"] = str(row.get("Área do Conhecimento", row.get("Area do Conhecimento", enriched["area"])))
                enriched["indexador"] = str(row.get("Indexador", enriched["indexador"]))
                enriched["jif"] = row.get("JIF", enriched["jif"])
                enriched["quartil_jcr"] = str(row.get("Quartil JCR", enriched["quartil_jcr"]))
                enriched["sjr"] = row.get("SJR", enriched["sjr"])
                enriched["sjr_quartile"] = str(row.get("SJR Best Quartile", enriched["sjr_quartile"]))
                enriched["h_index"] = row.get("H index", row.get("h-index", enriched["h_index"]))
                enriched["h5_link"] = str(row.get("Índice h5", enriched["h5_link"]))
                enriched["fonte_dados"] = "local"
            
            enriquecidas.append(enriched)
        
        return enriquecidas
    
    def recommend(
        self,
        titulo: str,
        resumo: str,
        idioma: str = "Português",
        top_n: int = 20,
        use_ollama: bool = False
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Gera recomendações com fallback automático
        
        Args:
            titulo: Título do artigo
            resumo: Resumo do artigo
            idioma: Idioma do artigo
            top_n: Número de recomendações
            use_ollama: Se True, tenta Ollama antes do Gemini
            
        Returns:
            (lista_de_recomendacoes, erro)
        """
        from services.openalex_client import OpenAlexClient
        
        # Cache key
        cache_key = f"rec_{hash(titulo + resumo + str(top_n))}"
        cached = self.cache_manager.get(cache_key)
        if cached:
            logger.info("Resultado retornado do cache")
            return cached, None
        
        # 1. Prepara candidatos da base local
        logger.info("Preparando candidatos da base local...")
        df_candidatos = self.df_local.copy()
        if len(df_candidatos) > 40:
            df_candidatos = df_candidatos.head(40)
        
        cols_envio = [self.df_local.columns[0]]
        for col in ["Grande Área", "Área do Conhecimento", "Indexador", "Quartil JCR", "SJR"]:
            if col in df_candidatos.columns:
                cols_envio.append(col)
        lista_periodicos = df_candidatos[cols_envio].to_dict(orient="records")
        
        # 2. Gera prompt Discovery-First
        prompt = get_discovery_prompt(titulo, resumo, lista_periodicos, top_n, idioma)
        
        # 3. Tenta IA (Gemini ou Ollama)
        resultados_ia = None
        erro_ia = None
        
        if use_ollama:
            logger.info("Tentando Ollama local...")
            resposta = self._call_ollama(prompt)
            if resposta:
                resultados_ia = self._parse_ai_response(resposta)
                if resultados_ia:
                    self._backend_used = "ollama"
                    logger.info("Recomendações geradas via Ollama")
        else:
            if self.api_key_gemini:
                logger.info("Tentando Gemini API...")
                resposta = self._call_gemini(prompt)
                if resposta:
                    resultados_ia = self._parse_ai_response(resposta)
                    if resultados_ia:
                        self._backend_used = "gemini"
                        logger.info("Recomendações geradas via Gemini")
                else:
                    erro_ia = "Gemini API não respondeu (cota esgotada ou chave inválida)"
            
            elif use_ollama:
                logger.info("Tentando Ollama como fallback...")
                resposta = self._call_ollama(prompt)
                if resposta:
                    resultados_ia = self._parse_ai_response(resposta)
                    if resultados_ia:
                        self._backend_used = "ollama"
                        logger.info("Recomendações geradas via Ollama (fallback)")
        
        # 4. Se IA falhou, usa algoritmo local
        if not resultados_ia:
            logger.info("Usando algoritmo local de relevância (fallback)")
            from services.discovery_recommender import _gerar_recomendacoes_locais
            resultados_ia = _gerar_recomendacoes_locais(
                self.df_local, titulo, resumo, top_n
            )
            self._backend_used = "local"
        
        if not resultados_ia:
            return None, "Nenhuma recomendação foi gerada"
        
        # 5. Enriquece com dados locais e OpenAlex
        logger.info("Enriquecendo recomendações...")
        enriquecidas = self._enriquecer_revistas(resultados_ia)
        
        # 6. Busca dados OpenAlex para revistas sem ISSN local
        openalex = OpenAlexClient()
        for rev in enriquecidas:
            if rev.get("issn", "-") in ["-", "N/A"] or rev.get("h_index", "-") == "-":
                try:
                    dados = openalex.get_journal_by_name(rev["nome"])
                    if dados:
                        if rev["issn"] in ["-", "N/A"]:
                            rev["issn"] = dados.get("issn", "-")
                        if rev["h_index"] == "-":
                            rev["h_index"] = dados.get("h_index", "-")
                        if not rev.get("homepage") or rev["homepage"] in ["-", "", "nan"]:
                            rev["homepage"] = dados.get("homepage", "")
                except Exception:
                    pass
        
        # 7. Ordena por aderência (decrescente)
        enriquecidas = sorted(enriquecidas, key=lambda x: x.get("aderencia", 0), reverse=True)
        
        # 8. Limita ao top_n
        enriquecidas = enriquecidas[:top_n]
        
        # 9. Salva em cache
        self.cache_manager.set(cache_key, enriquecidas, ttl=86400)  # 24h
        
        return enriquecidas, erro_ia


def _gerar_recomendacoes_locais(df_base, titulo, resumo, num_recomendacoes):
    """Algoritmo local de relevância temática (fallback universal)"""
    texto_busca = f"{titulo} {resumo}".lower()
    palavras = set(re.findall(r'\b[a-zA-Zà-ü]{4,}\b', texto_busca))
    stopwords = {
        "para", "como", "uma", "este", "esta", "com", "dos", "das", "pelo", "pela",
        "artigo", "pesquisa", "estudo", "sobre", "with", "this", "from", "that",
        "article", "research", "study", "about", "the", "and", "for", "are", "was"
    }
    palavras_filtradas = palavras - stopwords
    
    df = df_base.copy()
    col_titulo = df.columns[0]
    
    if palavras_filtradas:
        def calc_relevancia(row):
            score = 0
            nome = str(row.iloc[0]).lower()
            grande_area = str(row.get("Grande Área", "")).lower()
            area = str(row.get("Área do Conhecimento", row.get("Area do Conhecimento", ""))).lower()
            subarea = str(row.get("Subárea do Conhecimento", "")).lower()
            for pal in palavras_filtradas:
                if pal in nome: score += 5
                if pal in grande_area: score += 3
                if pal in area: score += 3
                if pal in subarea: score += 3
            return score
        
        df["relevancia"] = df.apply(calc_relevancia, axis=1)
        df = df.sort_values(by=["relevancia", "SJR"], ascending=[False, False])
    else:
        df["relevancia"] = 0
        df = df.sort_values(by="SJR", ascending=False)
    
    top_n = df.head(num_recomendacoes)
    max_rel = float(df["relevancia"].max()) if "relevancia" in df.columns else 0.0
    
    journals = []
    for idx, (_, row) in enumerate(top_n.iterrows()):
        if max_rel > 0:
            pct = min(96, max(82 + int((float(row.get("relevancia", 0)) / max_rel) * 14), 96 - (idx * 3)))
        else:
            pct = max(60, 78 - (idx * 4))
        
        journals.append({
            "nome": str(row[col_titulo]),
            "issn": str(row.get("ISSN", "-")),
            "homepage": str(row.get("Homepage", "")),
            "grande_area": str(row.get("Grande Área", "-")),
            "area": str(row.get("Área do Conhecimento", row.get("Area do Conhecimento", "-"))),
            "subarea": str(row.get("Subárea do Conhecimento", "-")),
            "indexador": str(row.get("Indexador", "-")),
            "jif": row.get("JIF", "-"),
            "quartil_jcr": str(row.get("Quartil JCR", "-")),
            "sjr": row.get("SJR", "-"),
            "sjr_quartile": str(row.get("SJR Best Quartile", "-")),
            "h_index": row.get("H index", row.get("h-index", "-")),
            "h5_link": str(row.get("Índice h5", "-")),
            "aderencia": pct,
            "justificativa": f"Recomendado por alinhamento temático com {palavras_filtradas}",
            "fonte_dados": "local",
        })
    
    return journals