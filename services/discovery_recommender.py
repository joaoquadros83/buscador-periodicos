"""
Discovery Recommender
Motor de recomendação baseado em busca vetorial (embeddings) + probabilidade proxy + LLM apenas para justificativa.
Arquitetura:
  1. Embeddings do título+resumo do usuário
  2. Busca vetorial por similaridade de cosseno no catálogo
  3. Cálculo matemático da probabilidade proxy de aceitação
  4. LLM (Gemini/Ollama) APENAS para redigir justificativa qualitativa
"""

import json
import re
import requests
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
import logging

from prompts.discovery_prompt import get_justification_prompt
from services.embeddings_client import get_embeddings_client, cosine_similarity
from services.vector_search import get_vector_search
from services.article_evaluator import ArticleEvaluator
from services.cache_manager import get_cache_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscoveryRecommender:
    """Motor de recomendação por busca vetorial + probabilidade proxy + LLM justificativa"""

    def __init__(
        self,
        df_local: pd.DataFrame,
        api_key_gemini: Optional[str] = None,
        ollama_model: str = "llama3",
        embeddings_model: str = "nomic-embed-text"
    ):
        """
        Inicializa o motor de recomendação

        Args:
            df_local: DataFrame com base local de revistas
            api_key_gemini: Chave API Gemini (opcional, para justificativa via nuvem)
            ollama_model: Modelo Ollama para justificativa
            embeddings_model: Modelo Ollama para embeddings
        """
        self.df_local = df_local
        self.api_key_gemini = api_key_gemini
        self.ollama_model = ollama_model
        self.embeddings_client = get_embeddings_client(model=embeddings_model)
        self.vector_search = get_vector_search(df_local=df_local, embeddings_client=self.embeddings_client)
        self.cache_manager = get_cache_manager()
        self.article_evaluator = ArticleEvaluator(df_local=df_local, ollama_model=ollama_model)
        self._backend_used = "unknown"

    def get_backend_name(self) -> str:
        """Retorna qual backend foi usado na última recomendação"""
        return self._backend_used

    def _call_llm(self, prompt: str, timeout: int = 30) -> Optional[str]:
        """
        Faz chamada à LLM para justificativa (Gemini primário, Ollama fallback)

        Args:
            prompt: Prompt para a LLM
            timeout: Timeout em segundos

        Returns:
            Texto da resposta ou None
        """
        # Tenta Gemini primeiro se tiver chave
        if self.api_key_gemini:
            try:
                return self._call_gemini(prompt, timeout)
            except Exception as e:
                logger.warning(f"Gemini falhou para justificativa: {e}")

        # Fallback Ollama
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
            logger.warning(f"Ollama falhou para justificativa: {e}")
            return None

    def _call_gemini(self, prompt: str, timeout: int = 30) -> Optional[str]:
        """Chamada à API Gemini para justificativa"""
        modelos_tentar = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]

        for modelo in modelos_tentar:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={self.api_key_gemini}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                headers = {"Content-Type": "application/json"}
                response = requests.post(url, json=payload, headers=headers, timeout=timeout)

                if response.status_code == 200:
                    data = response.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception:
                continue

        return None

    def _calcular_probabilidade_proxy(self, journal: Dict, similar_articles_count: int = 0) -> float:
        """
        Calcula probabilidade proxy de aceitação usando metadados reais.
        Fórmula: aderência (35%) + artigos similares (25%) + métricas revista (25%) + idioma (15%)
        """
        aderencia = journal.get("aderencia", 0)

        # 1. Aderência ao escopo (35%)
        score = aderencia * 0.35

        # 2. Artigos similares publicados (25%)
        similar_score = min(similar_articles_count * 20, 100)
        score += similar_score * 0.25

        # 3. Métricas da revista (25%)
        quartil = str(journal.get("quartil_jcr", ""))
        prestige_score = 80.0
        if quartil == "Q1":
            prestige_score = 85.0
        elif quartil == "Q2":
            prestige_score = 88.0
        elif quartil == "Q3":
            prestige_score = 90.0
        elif quartil == "Q4":
            prestige_score = 92.0

        indexador = str(journal.get("indexador", "")).lower()
        indexadores_list = [i.strip() for i in indexador.split(",") if i.strip()]
        reconhecidos = ["wos", "scopus", "scielo", "educ@", "doaj"]
        count_reconhecidos = sum(1 for idx in indexadores_list if any(r in idx for r in reconhecidos))
        if count_reconhecidos >= 2:
            prestige_score = min(prestige_score + 5, 100)

        score += prestige_score * 0.25

        # 4. Idioma (15%) - assume compatível se não houver informação
        score += 90.0 * 0.15

        return round(min(score, 100.0), 1)

    def recommend(
        self,
        titulo: str,
        resumo: str,
        idioma: str = "Português",
        top_n: int = 20,
        use_ollama: bool = False
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Gera recomendações por busca vetorial + proxy + justificativa LLM

        Args:
            titulo: Título do artigo
            resumo: Resumo do artigo
            idioma: Idioma do prompt
            top_n: Número de recomendações
            use_ollama: Não utilizado diretamente (mantido para compatibilidade)

        Returns:
            (lista_de_recomendacoes, erro)
        """
        cache_key = f"vec_{hash(titulo + resumo + str(top_n) + idioma)}"
        cached = self.cache_manager.get(cache_key)
        if cached:
            logger.info("Resultado retornado do cache")
            return cached, None

        query_text = f"{titulo} {resumo}"

        # Etapa 1 e 2: embeddings + busca vetorial
        logger.info("Buscando revistas por similaridade vetorial...")
        candidates = self.vector_search.search(query_text, top_k=40)

        if not candidates:
            return None, "Nenhuma revista encontrada no catálogo."

        # Etapa 3: calcular probabilidade proxy para as 40 revistas
        logger.info("Calculando probabilidade proxy de aceitação...")
        for j in candidates:
            j["probabilidade_aceitacao"] = self._calcular_probabilidade_proxy(j)

        # Ordena por probabilidade proxy decrescente
        candidates.sort(key=lambda x: x["probabilidade_aceitacao"], reverse=True)

        # Seleciona top 20
        top_journals = candidates[:top_n]

        # Etapa 4: LLM apenas para justificativa das 20 selecionadas
        logger.info("Gerando justificativas qualitativas...")
        self._backend_used = "vetorial"

        if self.api_key_gemini or self._ollama_available():
            self._backend_used = "gemini" if self.api_key_gemini else "ollama"
            for j in top_journals:
                try:
                    prompt = get_justification_prompt(titulo, resumo, j, idioma)
                    justificativa = self._call_llm(prompt)
                    if justificativa:
                        j["justificativa"] = justificativa
                except Exception as e:
                    logger.warning(f"Erro ao gerar justificativa: {e}")

        # Se não gerou justificativa, usa texto padrão
        for j in top_journals:
            if not j.get("justificativa"):
                j["justificativa"] = self._justificativa_padrao(j, idioma)

        # Salva em cache
        self.cache_manager.set(cache_key, top_journals, ttl=86400)

        return top_journals, None

    def _ollama_available(self) -> bool:
        """Verifica se Ollama está disponível"""
        try:
            import ollama
            ollama.list()
            return True
        except Exception:
            return False

    def _justificativa_padrao(self, journal: Dict, idioma: str) -> str:
        """Justificativa padrão quando LLM não está disponível"""
        nome = journal.get("nome", "")
        aderencia = journal.get("aderencia", 0)
        probabilidade = journal.get("probabilidade_aceitacao", 0)

        if idioma == "English":
            return (
                f"{nome} was selected because its editorial scope has a thematic adherence of "
                f"{aderencia}% with your article, resulting in an estimated acceptance probability of {probabilidade}%."
            )
        elif idioma == "Español":
            return (
                f"{nome} fue seleccionada porque su alcance editorial tiene una adherencia temática de "
                f"{aderencia}% con su artículo, lo que resulta en una probabilidad estimada de aceptación del {probabilidade}%."
            )
        return (
            f"{nome} foi selecionada porque seu escopo editorial apresenta {aderencia}% de aderência temática "
            f"com o seu artigo, resultando em probabilidade estimada de aceitação de {probabilidade}%."
        )
