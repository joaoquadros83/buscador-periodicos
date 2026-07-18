"""
Discovery Recommender
Motor de recomendação baseado em:
  1. Classificação da área do artigo
  2. Embeddings + busca vetorial por similaridade de cosseno
  3. Probabilidade proxy de publicação (taxa histórica estimada, penalidade por incompatibilidade, h-index do autor)
  4. LLM apenas para redigir justificativa qualitativa
"""

import re
import requests
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
import logging

from prompts.discovery_prompt import get_justification_prompt
from services.embeddings_client import get_embeddings_client, cosine_similarity
from services.area_classifier import classify_article_area
from services.cache_manager import get_cache_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscoveryRecommender:
    """Motor de recomendação por classificação de área + busca vetorial + probabilidade proxy + LLM"""

    def __init__(
        self,
        df_local: pd.DataFrame,
        api_key_gemini: Optional[str] = None,
        ollama_model: str = "llama3",
        embeddings_model: str = "nomic-embed-text",
        h_index_author: int = 5
    ):
        """
        Inicializa o motor de recomendação

        Args:
            df_local: DataFrame com base local de revistas
            api_key_gemini: Chave API Gemini (opcional, para embeddings e justificativa)
            ollama_model: Modelo Ollama para justificativa
            embeddings_model: Modelo Ollama para embeddings
            h_index_author: H-index estimado do autor (default: 5)
        """
        self.df_local = df_local
        self.api_key_gemini = api_key_gemini
        self.ollama_model = ollama_model
        self.h_index_author = h_index_author
        self.embeddings_client = get_embeddings_client(model=embeddings_model, gemini_api_key=api_key_gemini)
        self.cache_manager = get_cache_manager()
        self._backend_used = "unknown"

    def get_backend_name(self) -> str:
        """Retorna qual backend foi usado na última recomendação"""
        return self._backend_used

    def _call_llm(self, prompt: str, timeout: int = 30) -> Optional[str]:
        """Chama LLM para justificativa (Gemini primário, Ollama fallback)"""
        if self.api_key_gemini:
            try:
                return self._call_gemini(prompt, timeout)
            except Exception as e:
                logger.warning(f"Gemini falhou: {e}")

        try:
            import ollama
            response = ollama.generate(
                model=self.ollama_model,
                prompt=prompt,
                stream=False,
                options={"num_predict": 400, "temperature": 0.7}
            )
            return response.get("response", "")
        except Exception as e:
            logger.warning(f"Ollama falhou: {e}")
            return None

    def _call_gemini(self, prompt: str, timeout: int = 30) -> Optional[str]:
        """Chamada à API Gemini"""
        modelos = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
        for modelo in modelos:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={self.api_key_gemini}"
                response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]},
                                         headers={"Content-Type": "application/json"}, timeout=timeout)
                if response.status_code == 200:
                    return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception:
                continue
        return None

    def _classificar_artigo(self, titulo: str, resumo: str) -> Dict:
        """Classifica o artigo na área do conhecimento"""
        return classify_article_area(titulo, resumo)

    def _filtrar_por_area(self, df: pd.DataFrame, area_artigo: str) -> pd.DataFrame:
        """Filtra revistas da mesma grande área do artigo"""
        if not area_artigo or area_artigo == "Outras / Não Classificado":
            return df

        col_area = "Grande Área"
        if col_area not in df.columns:
            return df

        df_filtrado = df[df[col_area].astype(str).str.contains(area_artigo, case=False, na=False)]

        # Se filtrar demais, volta ao catálogo completo
        if len(df_filtrado) < 20:
            return df

        return df_filtrado

    def _busca_vetorial(self, query_text: str, df_candidatos: pd.DataFrame, top_k: int = 40) -> List[Dict]:
        """Busca as revistas mais similares por embeddings + cosseno"""
        col_titulo = df_candidatos.columns[0]

        # Constrói textos das revistas
        catalog_texts = []
        for _, row in df_candidatos.iterrows():
            partes = [str(row[col_titulo])]
            for col in ["Grande Área", "Área do Conhecimento", "Subárea do Conhecimento", "Indexador"]:
                if col in row.index:
                    val = str(row[col])
                    if val and val not in ["-", "nan", "None", ""]:
                        partes.append(val)
            catalog_texts.append(" ".join(partes))

        # Gera embeddings
        query_vector = self.embeddings_client.embed(query_text)
        catalog_vectors = self.embeddings_client.embed_batch(catalog_texts)

        # Calcula similaridades
        similarities = []
        for idx, vec in enumerate(catalog_vectors):
            sim = cosine_similarity(query_vector, vec)
            similarities.append((idx, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, sim in similarities[:top_k]:
            row = df_candidatos.iloc[idx]
            results.append({
                "nome": str(row[col_titulo]),
                "issn": str(row.get("ISSN", "-")),
                "homepage": str(row.get("Homepage", "-")),
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
                "similaridade": sim,
                "aderencia": round(sim * 100, 1),
                "fonte_dados": "local",
            })

        return results

    def _taxa_aceitacao_historica(self, journal: Dict) -> float:
        """
        Proxy para Taxa de Aceitação Histórica.
        Revistas mais prestigiadas (Q1) tendem a ser mais seletivas.
        """
        quartil = str(journal.get("quartil_jcr", "")).upper()
        sjr_q = str(journal.get("sjr_quartile", "")).upper()

        # Base: 35% de aceitação média
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
            # Sem quartil: revista nacional ou emergente, taxa média-alta
            taxa = 42.0

        # Ajuste por número de indexadores (mais indexadores = mais competitiva)
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
        """
        Penalidade por incompatibilidade entre área do artigo e da revista.
        Retorna fator entre 0 e 1 (1 = totalmente compatível).
        """
        area_artigo = classificacao.get("grande_area", "").lower()
        area_revista = str(journal.get("grande_area", "")).lower()

        if not area_artigo or not area_revista:
            return 1.0

        if area_artigo == area_revista:
            return 1.0

        # Áreas próximas
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
        """Extrai h-index numérico da revista"""
        h = journal.get("h_index", "-")
        try:
            return float(h) if h not in [None, "-", "N/A", "", "nan"] else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _calcular_probabilidade_proxy(self, journal: Dict, classificacao: Dict) -> float:
        """
        Probabilidade Proxy de Publicação:
        Taxa de Aceitação Histórica x Penalidade por Incompatibilidade x Fator H-Index do Autor
        """
        taxa = self._taxa_aceitacao_historica(journal)
        penalidade = self._penalidade_incompatibilidade(journal, classificacao)

        # Fator H-Index do Autor: autor com h-index maior tem mais chance em revistas de maior prestígio
        h_revista = self._h_index_revista(journal)
        if h_revista > 0:
            # Se h-index do autor for menor que 10% do h-index da revista, reduz chance
            ratio = self.h_index_author / max(h_revista * 0.1, 1.0)
            fator_h = min(1.2, max(0.6, ratio))
        else:
            fator_h = 1.0

        probabilidade = taxa * penalidade * fator_h
        return round(min(probabilidade, 95.0), 1)

    def recommend(
        self,
        titulo: str,
        resumo: str,
        idioma: str = "Português",
        top_n: int = 20,
        use_ollama: bool = False
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Gera recomendações por área + busca vetorial + proxy + justificativa
        """
        cache_key = f"rec_v2_{hash(titulo + resumo + str(top_n) + idioma)}"
        cached = self.cache_manager.get(cache_key)
        if cached:
            return cached, None

        query_text = f"{titulo} {resumo}"

        # Etapa 1: Classificar área do artigo
        classificacao = self._classificar_artigo(titulo, resumo)

        # Etapa 2: Filtrar catálogo pela área
        df_candidatos = self._filtrar_por_area(self.df_local, classificacao.get("grande_area", ""))

        # Etapa 3: Busca vetorial -> Top 40 por aderência ao escopo
        candidates = self._busca_vetorial(query_text, df_candidatos, top_k=40)
        if not candidates:
            return None, "Nenhuma revista encontrada no catálogo."

        # Etapa 4: Probabilidade proxy de publicação
        for j in candidates:
            j["probabilidade_aceitacao"] = self._calcular_probabilidade_proxy(j, classificacao)
            j["classificacao_area"] = classificacao

        # Etapa 5: Ordenar por viabilidade (probabilidade proxy)
        candidates.sort(key=lambda x: x["probabilidade_aceitacao"], reverse=True)
        top_journals = candidates[:top_n]

        # Etapa 6: LLM apenas para justificativa das melhores opções
        self._backend_used = "vetorial"
        if self.api_key_gemini or self._ollama_available():
            self._backend_used = "gemini" if self.api_key_gemini else "ollama"
            for j in top_journals[:10]:  # justificativa só para as 10 primeiras
                try:
                    prompt = get_justification_prompt(titulo, resumo, j, idioma)
                    justificativa = self._call_llm(prompt)
                    if justificativa:
                        j["justificativa"] = justificativa
                except Exception as e:
                    logger.warning(f"Erro ao gerar justificativa: {e}")

        for j in top_journals:
            if not j.get("justificativa"):
                j["justificativa"] = self._justificativa_padrao(j, idioma)

        self.cache_manager.set(cache_key, top_journals, ttl=86400)
        return top_journals, None

    def _ollama_available(self) -> bool:
        try:
            import ollama
            ollama.list()
            return True
        except Exception:
            return False

    def _justificativa_padrao(self, journal: Dict, idioma: str) -> str:
        nome = journal.get("nome", "")
        aderencia = journal.get("aderencia", 0)
        probabilidade = journal.get("probabilidade_aceitacao", 0)
        area = journal.get("grande_area", "")

        if idioma == "English":
            return (
                f"{nome} is a strong match for your article. Its editorial scope in {area} "
                f"shows {aderencia}% thematic adherence, with an estimated publication probability of {probabilidade}% "
                f"based on historical acceptance patterns and journal metrics."
            )
        elif idioma == "Español":
            return (
                f"{nome} es una buena opción para su artículo. Su alcance editorial en {area} "
                f"muestra {aderencia}% de adherencia temática, con una probabilidad estimada de publicación del {probabilidade}% "
                f"basada en patrones históricos de aceptación y métricas de la revista."
            )
        return (
            f"{nome} é uma forte candidata para seu artigo. Seu escopo editorial em {area} "
            f"apresenta {aderencia}% de aderência temática, com probabilidade estimada de publicação de {probabilidade}% "
            f"com base em padrões históricos de aceitação e métricas da revista."
        )
