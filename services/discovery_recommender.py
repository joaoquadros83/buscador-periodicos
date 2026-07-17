"""
Motor de Recomendação Discovery-First com suporte a Gemini
Usado quando Ollama não está disponível (Streamlit Cloud)
"""

import requests
import json
import re
import time
from typing import List, Dict, Tuple, Optional
import hashlib

class DiscoveryRecommender:
    """
    Implementação Discovery-First que funciona com Gemini API
    Com fallback automático para algoritmo local se API falhar
    """
    
    def __init__(self, df_local, api_key_gemini=None, prefer_ollama=True):
        self.df_local = df_local
        self.api_key_gemini = api_key_gemini
        self.prefer_ollama = prefer_ollama
        self.backend = "unknown"
        self.modelo_ativo = None
        
    def recommend(self, titulo: str, resumo: str, idioma: str, top_n: int = 20) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Gera recomendações de revistas para o artigo
        Retorna: (lista_recomendacoes, erro)
        """
        try:
            # Preparar candidatos locais
            df_candidatos = self._preparar_candidatos(titulo, resumo)
            
            if df_candidatos.empty:
                return None, "Nenhum periódico atende aos critérios."
            
            # Tentar Gemini API
            recomendacoes, erro = self._chamar_gemini(
                titulo, resumo, df_candidatos, idioma, top_n
            )
            
            if recomendacoes:
                self.backend = "gemini"
                return recomendacoes, None
            
            # Fallback para algoritmo local
            if erro:
                recomendacoes = self._gerar_localmente(
                    titulo, resumo, df_candidatos, idioma, top_n
                )
                self.backend = "local"
                return recomendacoes, None
            
            return None, erro or "Erro desconhecido ao processar recomendação"
            
        except Exception as e:
            return None, f"Erro crítico: {str(e)}"
    
    def _preparar_candidatos(self, titulo: str, resumo: str, max_candidatos: int = 40):
        """Filtra e ordena candidatos por relevância temática"""
        df = self.df_local.copy()
        
        # Extrai palavras-chave
        texto = f"{titulo} {resumo}".lower()
        palavras = set(re.findall(r'\b[a-zA-Zà-ü]{4,}\b', texto))
        stopwords = {
            "para", "como", "uma", "este", "esta", "com", "dos", "das",
            "with", "from", "that", "article", "research", "study"
        }
        palavras = palavras - stopwords
        
        # Calcula relevância
        def score_relevancia(row):
            score = 0
            col_titulo = df.columns[0]
            nome = str(row[col_titulo]).lower()
            area = str(row.get("Área do Conhecimento", "")).lower()
            
            for pal in palavras:
                if pal in nome:
                    score += 5
                if pal in area:
                    score += 3
            return score
        
        df["relevancia"] = df.apply(score_relevancia, axis=1)
        df = df.sort_values(by=["relevancia", "SJR"], ascending=[False, False])
        
        return df.head(max_candidatos)
    
    def _chamar_gemini(self, titulo: str, resumo: str, df_cand, idioma: str, top_n: int) -> Tuple[Optional[List], Optional[str]]:
        """Chama Gemini API para gerar recomendações"""
        
        if not self.api_key_gemini:
            return None, "Sem chave Gemini configurada"
        
        try:
            # Preparar lista de periódicos
            col_titulo = self.df_local.columns[0]
            periodicos = []
            for _, row in df_cand.iterrows():
                periodicos.append({
                    "nome": str(row[col_titulo]),
                    "area": str(row.get("Área do Conhecimento", "-")),
                    "indexador": str(row.get("Indexador", "-")),
                    "quartil": str(row.get("Quartil JCR", "-"))
                })
            
            # Prompt em português (língua principal do usuário)
            prompt = f"""
            Você é especialista em publicação acadêmica. Analize este artigo:
            
            TÍTULO: {titulo}
            RESUMO: {resumo}
            
            Selecione as {top_n} revistas mais adequadas desta lista:
            {json.dumps(periodicos[:40], ensure_ascii=False)}
            
            Retorne APENAS um JSON array válido (sem markdown) com objetos contendo:
            - "revista_nome": nome exato da revista
            - "porcentagem_aderencia": 0-100
            - "justificativa": breve explicação em {idioma}
            """
            
            modelos = [
                "gemini-2.0-flash",
                "gemini-2.5-flash",
                "gemini-2.0-flash-lite",
            ]
            
            for modelo in modelos:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={self.api_key_gemini}"
                    response = requests.post(
                        url,
                        json={"contents": [{"parts": [{"text": prompt}]}]},
                        timeout=45
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        texto = data["candidates"][0]["content"]["parts"][0]["text"]
                        
                        # Parse JSON
                        match = re.search(r'\[\s*\{.*\}\s*\]', texto, re.DOTALL)
                        if match:
                            raw = json.loads(match.group(0))
                            recomendacoes = []
                            for item in raw:
                                recomendacoes.append({
                                    "nome": item.get("revista_nome", ""),
                                    "aderencia": min(100, max(0, int(item.get("porcentagem_aderencia", 50)))),
                                    "justificativa": item.get("justificativa", "")
                                })
                            self.modelo_ativo = modelo
                            return recomendacoes, None
                    
                    elif response.status_code == 429:
                        return None, "⚠️ Cota de requisições Gemini excedida. Tente novamente mais tarde."
                    
                except Exception as ex:
                    continue
            
            return None, "Todos os modelos Gemini falharam"
        
        except Exception as e:
            return None, f"Erro ao chamar Gemini: {str(e)}"
    
    def _gerar_localmente(self, titulo: str, resumo: str, df_cand, idioma: str, top_n: int) -> List[Dict]:
        """Gera recomendações usando algoritmo local (fallback)"""
        
        col_titulo = self.df_local.columns[0]
        recomendacoes = []
        
        for idx, (_, row) in enumerate(df_cand.head(top_n).iterrows()):
            aderencia = max(60, 100 - (idx * 5))
            nome = str(row[col_titulo])
            area = str(row.get("Área do Conhecimento", "-"))
            
            if "português" in idioma.lower() or idioma == "Português":
                just = f"Periódico de excelência em {area}. Alinhado com o escopo editorial do seu trabalho."
            else:
                just = f"Excellent journal in {area}. Aligned with your work's scope."
            
            recomendacoes.append({
                "nome": nome,
                "aderencia": aderencia,
                "justificativa": just
            })
        
        return recomendacoes
    
    def get_backend_name(self) -> str:
        """Retorna o backend usado (gemini, ollama, ou local)"""
        return self.backend
