"""
Utilitários do SciPubs
Funções auxiliares para normalização, validação e logging
"""

from utils.logger import AnonymousLogger
from utils.validators import (
    validar_score,
    validar_resultado_recomendacao,
    validar_batch_recomendacoes
)
from utils.fuzzy_matcher import calculate_similarity, fuzzy_match_journal
from utils.normalizer import normalize_text, normalize_issn

def get_anonymous_logger():
    """Factory para logger anônimo"""
    return AnonymousLogger()

__all__ = [
    'AnonymousLogger',
    'get_anonymous_logger',
    'validar_score',
    'validar_resultado_recomendacao',
    'validar_batch_recomendacoes',
    'calculate_similarity',
    'fuzzy_match_journal',
    'normalize_text',
    'normalize_issn',
]
