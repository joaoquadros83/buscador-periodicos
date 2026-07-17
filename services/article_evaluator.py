"""
Avaliador de Artigos com Índices de Aderência
Calcula scores de aderência ao escopo, área e probabilidade de aceitação
"""

import re
from typing import Dict, Optional

class ArticleEvaluator:
    """
    Avalia um artigo em relação a uma revista e retorna índices de qualidade
    """
    
    def __init__(self, df_local, use_ollama=False):
        self.df_local = df_local
        self.use_ollama = use_ollama
    
    def evaluate_article_for_journal(
        self,
        titulo: str,
        resumo: str,
        journal: Dict,
        similar_articles_count: int = 0,
        idioma: str = "Português"
    ) -> Dict:
        """
        Avalia o artigo em relação a uma revista específica
        Retorna dicionário com índices de aderência
        """
        
        # 1. Aderência ao Escopo (já vem do recomendador)
        aderencia_escopo = min(100, max(0, int(journal.get("aderencia", 50))))
        
        # 2. Aderência à Área de Conhecimento
        aderencia_area = self._calcular_aderencia_area(
            titulo, resumo, journal, idioma
        )
        
        # 3. Probabilidade de Aceitação (proxy multi-fator)
        probabilidade_aceitacao = self._calcular_probabilidade_aceitacao(
            aderencia_escopo, aderencia_area, similar_articles_count, journal
        )
        
        return {
            "aderencia_escopo": aderencia_escopo,
            "aderencia_area": aderencia_area,
            "probabilidade_aceitacao": probabilidade_aceitacao,
            "probabilidade_confianca": self._classificar_confianca(probabilidade_aceitacao),
            "metodo": "Estimativa baseada em aderência temática e análise de artigos similares"
        }
    
    def _calcular_aderencia_area(self, titulo: str, resumo: str, journal: Dict, idioma: str) -> int:
        """
        Calcula aderência do artigo à área de conhecimento da revista
        """
        texto_artigo = f"{titulo} {resumo}".lower()
        
        # Extrai área da revista
        area_revista = str(journal.get("area", "")).lower()
        subarea_revista = str(journal.get("subarea", "")).lower()
        
        # Calcula similaridade de termos
        palavras_artigo = set(re.findall(r'\b\w+\b', texto_artigo))
        palavras_area = set(re.findall(r'\b\w+\b', area_revista + " " + subarea_revista))
        
        if not palavras_area:
            return 50  # Default
        
        intersecao = palavras_artigo & palavras_area
        similaridade = len(intersecao) / len(palavras_area) if palavras_area else 0
        
        # Converte para percentual (0-100)
        score = int(50 + (similaridade * 50))  # Mínimo 50%, máximo 100%
        
        return min(100, max(0, score))
    
    def _calcular_probabilidade_aceitacao(
        self,
        aderencia_escopo: int,
        aderencia_area: int,
        similar_articles_count: int,
        journal: Dict
    ) -> int:
        """
        Calcula probabilidade de aceitação usando múltiplos fatores
        """
        scores = []
        
        # Fator 1: Aderência ao Escopo (40%)
        scores.append(aderencia_escopo * 0.4)
        
        # Fator 2: Aderência à Área (20%)
        scores.append(aderencia_area * 0.2)
        
        # Fator 3: Prestígio da Revista (30%)
        # Ajusta baseado em quartil
        quartil = str(journal.get("quartil_jcr", "-")).upper()
        if "Q1" in quartil:
            scores.append(60 * 0.3)  # Mais seletiva
        elif "Q2" in quartil:
            scores.append(75 * 0.3)
        elif "Q3" in quartil:
            scores.append(82 * 0.3)
        else:
            scores.append(85 * 0.3)  # Menos seletiva
        
        # Fator 4: Artigos Similares (10%)
        if similar_articles_count > 0:
            # Quanto mais artigos similares publicados, melhor
            prob_artigos = min(90, similar_articles_count * 8)
            scores.append(prob_artigos * 0.1)
        else:
            scores.append(50 * 0.1)  # Default neutro
        
        probabilidade = sum(scores)
        
        return int(min(100, max(10, probabilidade)))
    
    def _classificar_confianca(self, score: int) -> str:
        """
        Classifica o nível de confiança da estimativa
        """
        if score >= 75:
            return "Alta"
        elif score >= 50:
            return "Média"
        else:
            return "Baixa"
