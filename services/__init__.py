"""
SciPubs Services Package
Módulos de integração para IA, cache, APIs externas e logging.
"""

import streamlit as st
import sys
import importlib
from typing import Optional, Tuple

# ===== VALIDAÇÃO DE DEPENDÊNCIAS =====
REQUIRED_MODULES = {
    "requests": "requests",
    "pandas": "pandas",
    "ollama": "ollama",
}

def validate_dependencies():
    """Valida se todas as dependências estão instaladas"""
    missing = []
    
    for name, package in REQUIRED_MODULES.items():
        try:
            importlib.import_module(name)
        except ImportError:
            missing.append(package)
    
    if missing:
        st.error(f"""
        ❌ **Dependências faltando:** {', '.join(missing)}
        
        Execute no terminal:
        ```bash
        pip install {' '.join(missing)}
        ```
        """)
        st.stop()
        return False
    
    return True

def validate_ollama_connection() -> Tuple[bool, str]:
    """Valida se Ollama está respondendo"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            return True, "✅ Ollama pronto"
        else:
            return False, f"Ollama respondeu com status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Ollama não está rodando (ConnectionError). Execute: ollama serve"
    except requests.exceptions.Timeout:
        return False, "Ollama respondeu muito lentamente (timeout 5s)"
    except Exception as e:
        return False, f"Erro ao conectar: {str(e)}"

def validate_gemini_key(api_key: str) -> Tuple[bool, str]:
    """Valida chave Gemini antes de usar"""
    if not api_key or len(api_key) < 20:
        return False, "Chave API muito curta"
    
    try:
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        response = requests.post(
            url,
            json={"contents": [{"parts": [{"text": "test"}]}]},
            timeout=10
        )
        if response.status_code == 401:
            return False, "Chave API inválida ou expirada"
        elif response.status_code == 429:
            return False, "Cota de requisições excedida"
        elif response.status_code == 200:
            return True, "✅ Chave válida"
        else:
            return False, f"Status inesperado: {response.status_code}"
    except Exception as e:
        return False, str(e)

# ===== FACTORY FUNCTIONS =====

def get_discovery_recommender(df_local, api_key_gemini=None, prefer_ollama=True):
    """
    Factory com fallback automático
    prefer_ollama=True:  Tenta Ollama primeiro, depois Gemini
    prefer_ollama=False: Usa apenas Gemini
    """
    from services.discovery_recommender import DiscoveryRecommender
    
    return DiscoveryRecommender(
        df_local=df_local,
        api_key_gemini=api_key_gemini,
        prefer_ollama=prefer_ollama
    )

def get_article_evaluator(df_local, use_ollama=False):
    """Factory para article_evaluator"""
    from services.article_evaluator import ArticleEvaluator
    return ArticleEvaluator(df_local=df_local, use_ollama=use_ollama)

def get_cache_manager():
    """Factory para cache"""
    from services.cache_manager import CacheManager
    return CacheManager()

def get_anonymous_logger():
    """Factory para logger"""
    from utils.logger import AnonymousLogger
    return AnonymousLogger()

__all__ = [
    'validate_dependencies',
    'validate_ollama_connection',
    'validate_gemini_key',
    'get_discovery_recommender',
    'get_article_evaluator',
    'get_cache_manager',
    'get_anonymous_logger',
]
