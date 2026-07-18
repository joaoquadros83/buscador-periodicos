"""
Discovery-First Prompt
Prompt otimizado para descoberta de revistas via IA generativa
"""


def get_discovery_prompt(titulo: str, resumo: str, idioma: str = "Português") -> str:
    """
    Retorna prompt Discovery-First otimizado
    
    Args:
        titulo: Título do artigo
        resumo: Resumo do artigo
        idioma: Idioma do prompt (Português, English, Español)
        
    Returns:
        String com o prompt
    """
    
    if idioma == "Português":
        return f"""Analise este artigo científico e liste as 30 revistas mais adequadas para submissão:

TÍTULO: {titulo}
RESUMO: {resumo}

CRITÉRIOS:
1. Aderência temática é a PRIORIDADE #1 (não use fator de impacto como critério principal)
2. Inclua revistas em PORTUGUÊS, INGLÊS e ESPANHOL
3. Inclua revistas brasileiras (CAPES/SciELO) E internacionais (WoS, Scopus)
4. Diversifique níveis de prestígio (não só Q1, nem só nacionais)
5. Use seu conhecimento real sobre o escopo editorial de cada revista

Para cada revista, avalie:
- Aderência ao tema (0-100): quão alinhado o artigo está com o escopo?
- Justificativa: 2-3 frases explicando a adequação

RESPONDA apenas com JSON válido (sem markdown), exatamente neste formato:
[
  {{
    "revista_nome": "Nome exato e completo da revista",
    "aderencia": 85,
    "idioma": "PT",
    "justificativa": "Breve explicação da adequação temática"
  }}
]"""
    
    elif idioma == "English":
        return f"""Analyze this scientific article and list the 30 most suitable journals for submission:

TITLE: {titulo}
ABSTRACT: {resumo}

CRITERIA:
1. Thematic adherence is PRIORITY #1 (do not use impact factor as main criterion)
2. Include journals in PORTUGUESE, ENGLISH, and SPANISH
3. Include Brazilian journals (CAPES/SciELO) AND international journals (WoS, Scopus)
4. Diversify prestige levels (not only Q1, not only national)
5. Use your real knowledge about each journal's editorial scope

For each journal, evaluate:
- Thematic adherence (0-100): how aligned is the article with the scope?
- Justification: 2-3 sentences explaining the thematic fit

RESPOND only with valid JSON (no markdown), exactly in this format:
[
  {{
    "journal_name": "Exact and complete journal name",
    "adherence": 85,
    "language": "EN",
    "justification": "Brief explanation of thematic fit"
  }}
]"""
    
    else:  # Español
        return f"""Analice este artículo científico y liste las 30 revistas más adecuadas para envío:

TÍTULO: {titulo}
RESUMEN: {resumo}

CRITERIOS:
1. La adhesión temática es PRIORIDAD #1 (no use factor de impacto como criterio principal)
2. Incluya revistas en PORTUGUÉS, INGLÉS y ESPAÑOL
3. Incluya revistas brasileñas (CAPES/SciELO) E internacionales (WoS, Scopus)
4. Diversifique niveles de prestigio (no solo Q1, no solo nacionales)
5. Use su conocimiento real sobre el alcance editorial de cada revista

Para cada revista, evalúe:
- Adhesión temática (0-100): qué tan alineado está el artículo con el alcance?
- Justificación: 2-3 frases explicando la adecuación temática

RESPONDA solo con JSON válido (sin markdown), exactamente en este formato:
[
  {{
    "revista_nombre": "Nombre exacto y completo de la revista",
    "adherencia": 85,
    "idioma": "ES",
    "justificacion": "Breve explicación de la adecuación temática"
  }}
]"""


def get_classification_prompt(titulo: str, resumo: str, idioma: str = "Português") -> str:
    """
    Retorna prompt para classificação CAPES do artigo
    
    Args:
        titulo: Título do artigo
        resumo: Resumo do artigo
        idioma: Idioma do prompt
        
    Returns:
        String com o prompt
    """
    
    if idioma == "Português":
        return f"""Classifique este artigo nas áreas do CNPq/CAPES:

TÍTULO: {titulo}
RESUMO: {resumo}

RESPONDA apenas com JSON válido:
{{
    "grande_area": "Ex: Ciências Exatas e da Terra",
    "area": "Ex: Ciência da Computação",
    "subarea": "Ex: Sistemas de Computação",
    "confianca": 0.92
}}"""
    
    elif idioma == "English":
        return f"""Classify this article in CNPq/CAPES areas:

TITLE: {titulo}
ABSTRACT: {resumo}

RESPOND only with valid JSON:
{{
    "grande_area": "Ex: Exact and Earth Sciences",
    "area": "Ex: Computer Science",
    "subarea": "Ex: Computer Systems",
    "confianca": 0.92
}}"""
    
    else:  # Español
        return f"""Clasifique este artículo en las áreas del CNPq/CAPES:

TÍTULO: {titulo}
RESUMEN: {resumo}

RESPONDA solo con JSON válido:
{{
    "grande_area": "Ex: Ciencias Exactas y de la Tierra",
    "area": "Ex: Ciencia de la Computación",
    "subarea": "Ex: Sistemas de Computación",
    "confianca": 0.92
}}"""
