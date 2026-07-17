"""
Validadores para scores, recomendações e dados
"""

from typing import Tuple, List, Optional, Dict

def validar_score(valor, campo_nome: str, min_val=0, max_val=100) -> Tuple[int, Optional[str]]:
    """
    Valida que um score está entre 0-100
    Retorna: (valor_validado, erro)
    """
    try:
        # Tentar converter para int
        if isinstance(valor, str):
            valor = int(valor.replace("%", "").strip())
        else:
            valor = int(valor)
        
        # Validar range
        if valor < min_val or valor > max_val:
            valor_normalizado = max(min_val, min(max_val, valor))
            return valor_normalizado, \
                   f"⚠️ {campo_nome} {valor}% normalizado para {valor_normalizado}%"
        
        return valor, None
    
    except (ValueError, TypeError):
        return 50, f"❌ {campo_nome} inválido: {valor}. Usando padrão 50%."

def validar_resultado_recomendacao(recomendacao: dict) -> Tuple[dict, Optional[str]]:
    """
    Valida estrutura completa de recomendação
    """
    campos_obrigatorios = [
        "nome",
        "aderencia",
        "justificativa"
    ]
    
    erros = []
    
    # Verificar campos faltando
    for campo in campos_obrigatorios:
        if campo not in recomendacao:
            erros.append(f"Campo faltando: {campo}")
    
    # Validar nome
    if not recomendacao.get("nome", "").strip():
        erros.append("Nome da revista vazio")
    
    # Validar scores
    valor, erro = validar_score(
        recomendacao.get("aderencia", 50),
        "Aderência"
    )
    recomendacao["aderencia"] = valor
    if erro:
        erros.append(erro)
    
    # Validar justificativa
    justificativa = str(recomendacao.get("justificativa", "")).strip()
    if not justificativa or len(justificativa) < 10:
        erros.append("Justificativa muito curta (mín. 10 caracteres)")
    
    if erros:
        return recomendacao, " | ".join(erros)
    
    return recomendacao, None

def validar_batch_recomendacoes(recomendacoes: list) -> Tuple[list, list]:
    """
    Valida lista de recomendações
    Retorna: (recomendacoes_validas, lista_de_erros)
    """
    validas = []
    erros_lista = []
    
    for idx, rec in enumerate(recomendacoes):
        rec_valida, erro = validar_resultado_recomendacao(rec)
        validas.append(rec_valida)
        
        if erro:
            erros_lista.append({
                "index": idx,
                "revista": rec.get("nome", "DESCONHECIDA"),
                "erro": erro
            })
    
    return validas, erros_lista
