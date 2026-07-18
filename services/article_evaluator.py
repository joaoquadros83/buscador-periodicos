"""
Article Evaluator
Calcula índices de avaliação do artigo (aderência, probabilidade de aceitação)
"""

import pandas as pd
from typing import Dict, Optional, List
import logging

from prompts.discovery_prompt import get_classification_prompt
from utils.fuzzy_matcher import find_journal_in_dataframe

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArticleEvaluator:
    """Avaliador de artigo com múltiplos índices"""
    
    def __init__(self, df_local: pd.DataFrame, ollama_model: str = "llama3"):
        """
        Inicializa o avaliador
        
        Args:
            df_local: DataFrame com base local de revistas
            ollama_model: Modelo Ollama a usar
        """
        self.df_local = df_local
        self.ollama_model = ollama_model
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """
        Faz chamada ao Ollama
        
        Args:
            prompt: Prompt para enviar
            
        Returns:
            Resposta do modelo ou None
        """
        try:
            import ollama
            response = ollama.generate(
                model=self.ollama_model,
                prompt=prompt,
                stream=False
            )
            return response['response']
        except ImportError:
            logger.error("Ollama não está instalado")
            return None
        except Exception as e:
            logger.error(f"Erro ao chamar Ollama: {e}")
            return None
    
    def classify_article_area(
        self,
        titulo: str,
        resumo: str,
        idioma: str = "Português"
    ) -> Optional[Dict]:
        """
        Classifica o artigo nas áreas CAPES
        
        Args:
            titulo: Título do artigo
            resumo: Resumo do artigo
            idioma: Idioma do prompt
            
        Returns:
            Dicionário com classificação ou None
        """
        prompt = get_classification_prompt(titulo, resumo, idioma)
        
        try:
            import json
            response = self._call_ollama(prompt)
            
            if response:
                # Remove markdown se presente
                response = response.strip()
                if response.startswith("```"):
                    response = response.split("```")[1]
                    if response.startswith("json"):
                        response = response[4:]
                
                classification = json.loads(response.strip())
                return classification
        except Exception as e:
            logger.error(f"Erro ao classificar artigo: {e}")
        
        return None
    
    def calculate_area_adherence(
        self,
        article_area: str,
        journal_area: str
    ) -> float:
        """
        Calcula aderência da área do artigo com a área da revista
        
        Args:
            article_area: Área do artigo
            journal_area: Área da revista
            
        Returns:
            Score de aderência (0-100)
        """
        if not article_area or not journal_area:
            return 50.0
        
        article_area = str(article_area).lower().strip()
        journal_area = str(journal_area).lower().strip()
        
        # Match exato
        if article_area == journal_area:
            return 100.0
        
        # Match parcial (contém)
        if article_area in journal_area or journal_area in article_area:
            return 75.0
        
        # Áreas próximas (lista de sinônimos)
        similar_areas = {
            "ciência da computação": ["computação", "informática", "sistemas de informação"],
            "engenharia": ["engenharias", "engenharia de"],
            "saúde": ["ciências da saúde", "medicina", "enfermagem"],
            "educação": ["educação", "ensino", "pedagogia"]
        }
        
        for key, synonyms in similar_areas.items():
            if article_area in synonyms and journal_area in synonyms:
                return 60.0
        
        return 30.0
    
    def calculate_acceptance_probability(
        self,
        journal: Dict,
        article_adherence: float,
        similar_articles_count: int = 0
    ) -> Dict:
        """
        Calcula probabilidade estimada de aceitação
        
        Args:
            journal: Dados da revista enriquecidos
            article_adherence: Aderência temática do artigo
            similar_articles_count: Número de artigos similares encontrados
            
        Returns:
            Dicionário com probabilidade e metadados
        """
        score = 0.0
        
        # 1. Aderência temática (40%)
        score += article_adherence * 0.4
        
        # 2. Nível de prestígio vs qualidade (30%)
        quartil = journal.get("quartil_jcr", "")
        if quartil == "Q1":
            prestige_score = 60  # Mais difícil
        elif quartil == "Q2":
            prestige_score = 75
        elif quartil == "Q3":
            prestige_score = 85
        elif quartil == "Q4":
            prestige_score = 90  # Mais fácil
        else:
            # Se não tem quartil, usa h-index
            h_index = journal.get("h_index")
            if h_index:
                if h_index >= 100:
                    prestige_score = 65
                elif h_index >= 50:
                    prestige_score = 75
                elif h_index >= 20:
                    prestige_score = 80
                else:
                    prestige_score = 85
            else:
                prestige_score = 70  # Médio
        
        score += prestige_score * 0.3
        
        # 3. Open Access (10%) - OA tende a aceitar mais
        if journal.get("is_oa") or journal.get("is_doaj"):
            score += 10 * 0.1
        
        # 4. Artigos similares (20%)
        if similar_articles_count > 0:
            similar_score = min(similar_articles_count * 15, 100)
            score += similar_score * 0.2
        
        # Cap em 100
        probability = min(score, 100.0)
        
        # Determina nível de confiança
        if probability >= 75:
            confianca = "Alta"
        elif probability >= 50:
            confianca = "Média"
        else:
            confianca = "Baixa"
        
        return {
            "probabilidade": round(probability, 1),
            "confianca": confianca,
            "metodo": "Estimativa baseada em aderência temática, prestígio da revista e análise de artigos similares"
        }
    
    def evaluate_article_for_journal(
        self,
        titulo: str,
        resumo: str,
        journal: Dict,
        similar_articles_count: int = 0,
        idioma: str = "Português"
    ) -> Dict:
        """
        Avalia artigo para uma revista específica
        
        Args:
            titulo: Título do artigo
            resumo: Resumo do artigo
            journal: Dados da revista
            similar_articles_count: Número de artigos similares
            idioma: Idioma
            
        Returns:
            Dicionário com todos os índices
        """
        # 1. Aderência ao escopo (já vem da IA)
        aderencia_escopo = journal.get("aderencia", 0)
        
        # 2. Classifica área do artigo
        classification = self.classify_article_area(titulo, resumo, idioma)
        
        if classification:
            article_area = classification.get("area", "")
            article_grande_area = classification.get("grande_area", "")
            classification_confidence = classification.get("confianca", 0)
        else:
            article_area = "-"
            article_grande_area = "-"
            classification_confidence = 0
        
        # 3. Aderência à área
        journal_area = journal.get("area", "-")
        aderencia_area = self.calculate_area_adherence(article_area, journal_area)
        
        # 4. Probabilidade de aceitação
        acceptance = self.calculate_acceptance_probability(
            journal,
            aderencia_escopo,
            similar_articles_count
        )
        
        return {
            "aderencia_escopo": aderencia_escopo,
            "aderencia_area": round(aderencia_area, 1),
            "probabilidade_aceitacao": acceptance["probabilidade"],
            "probabilidade_confianca": acceptance["confianca"],
            "probabilidade_metodo": acceptance["metodo"],
            "artigo_area": article_area,
            "artigo_grande_area": article_grande_area,
            "classificacao_confianca": classification_confidence
        }

    def evaluate_journal_with_classification(
        self,
        journal: Dict,
        classification: Optional[Dict],
        similar_articles_count: int = 0
    ) -> Dict:
        """
        Avalia revista usando classificação CAPES já calculada (sem nova chamada IA).
        """
        aderencia_escopo = journal.get("aderencia", 0)

        if classification:
            article_area = classification.get("area", "")
            article_grande_area = classification.get("grande_area", "")
            classification_confidence = classification.get("confianca", 0)
        else:
            article_area = "-"
            article_grande_area = "-"
            classification_confidence = 0

        journal_area = journal.get("area", "-")
        aderencia_area = self.calculate_area_adherence(article_area, journal_area)

        acceptance = self.calculate_acceptance_probability(
            journal,
            aderencia_escopo,
            similar_articles_count
        )

        return {
            "aderencia_escopo": aderencia_escopo,
            "aderencia_area": round(aderencia_area, 1),
            "probabilidade_aceitacao": acceptance["probabilidade"],
            "probabilidade_confianca": acceptance["confianca"],
            "probabilidade_metodo": acceptance["metodo"],
            "artigo_area": article_area,
            "artigo_grande_area": article_grande_area,
            "classificacao_confianca": classification_confidence
        }


def get_article_evaluator(df_local: pd.DataFrame, ollama_model: str = "llama3") -> ArticleEvaluator:
    """
    Retorna instância do ArticleEvaluator
    
    Args:
        df_local: DataFrame local
        ollama_model: Modelo Ollama
        
    Returns:
        Instância de ArticleEvaluator
    """
    return ArticleEvaluator(df_local, ollama_model)
