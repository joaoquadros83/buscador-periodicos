"""
Fuzzy Matching para correspondência de nomes de revistas
"""

from difflib import SequenceMatcher
from typing import Tuple

def calculate_similarity(s1: str, s2: str, threshold: float = 0.75) -> float:
    """
    Calcula similaridade entre duas strings usando SequenceMatcher
    Retorna valor entre 0 e 1
    """
    s1 = str(s1).lower().strip()
    s2 = str(s2).lower().strip()
    
    if not s1 or not s2:
        return 0.0
    
    ratio = SequenceMatcher(None, s1, s2).ratio()
    return ratio

def fuzzy_match_journal(journal_name: str, df_base, threshold: float = 0.82) -> Tuple[bool, dict]:
    """
    Tenta fazer fuzzy matching de um nome de revista com a base local
    Retorna: (encontrada, registro_revista)
    """
    col_titulo = df_base.columns[0]
    
    # Primeiro tenta match exato
    exact_match = df_base[df_base[col_titulo].astype(str).str.lower().str.strip() == journal_name.lower().strip()]
    if not exact_match.empty:
        return True, exact_match.iloc[0].to_dict()
    
    # Depois tenta fuzzy match
    best_match = None
    best_score = 0
    
    for idx, row in df_base.iterrows():
        nome_base = str(row[col_titulo])
        score = calculate_similarity(journal_name, nome_base, threshold)
        
        if score > best_score:
            best_score = score
            best_match = row
    
    if best_score >= threshold and best_match is not None:
        return True, best_match.to_dict()
    
    return False, {}
