"""
Funções de normalização de texto e identificadores
"""

import re
import unicodedata

def normalize_text(text: str) -> str:
    """
    Normaliza texto: lowercase, remove acentos, espaços extras
    """
    text = str(text).lower().strip()
    
    # Remove acentos
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    
    # Remove caracteres especiais
    text = re.sub(r'[^a-z0-9\s]', '', text)
    
    # Remove espaços extras
    text = ' '.join(text.split())
    
    return text

def normalize_issn(issn: str) -> str:
    """
    Normaliza ISSN para formato padrão XXXX-XXXX
    """
    # Remove tudo que não é dígito ou X
    issn = re.sub(r'[^0-9X]', '', str(issn).upper())
    
    if len(issn) == 8:
        return f"{issn[:4]}-{issn[4:]}"
    
    return issn
