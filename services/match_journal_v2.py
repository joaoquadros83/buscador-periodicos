# Match Journal V2 - Pipeline Refinado (Semantic Kernel Style)

"""
Match Journal V2 - Recomendacao Inteligente de Periodicos

Pipeline:
1. Knowledge Area via LLM (Ollama)
2. Filtro por Knowledge Area + Adherence Score
3. Top 300 por score
4. Estimated Acceptance Probability (Top 40)
5. Ordenamento por probability (default)
6. Output Top 20 com probability > 60% + justificativa textual
"""

import logging
from typing import List, Dict
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SemanticKernelStyle:
    """Orquestrador LLM - usando TF-IDF e Ollama (100% gratuito)"""

    def __init__(self, model: str = "llama3"):
        self.model = model
        self.vectorizer = TfidfVectorizer(max_features=512, stop_words=None)

    def _classify_knowledge_area(self, titulo: str, resumo: str) -> str:
        """Camada 1: Classifica Knowledge Area"""
        prompt = f"""
Classifique o artigo abaixo em uma unica "Knowledge Area":
Lista: Education / Music / Computer Science / Medicine / Health Sciences / Social Sciences / Psychology / Engineering / Biological Sciences / Arts / Economics / Law / Physics / Chemistry / Mathematics / Agronomy / Veterinary / Philosophy / History / Geography / Linguistics / Multidisciplinary
Titulo: {titulo}
Resumo: {resumo[:600]}
Retorne APENAS o nome da Knowledge Area.
"""
        try:
            import ollama
            resp = ollama.generate(model=self.model, prompt=prompt, stream=False)
            return resp.get("response", "").strip()
        except:
            text = f"{titulo} {resumo}".lower()
            mapping = [
                ("education", "Education"), ("musica", "Music"), ("music", "Music"),
                ("computer", "Computer Science"), ("computacao", "Computer Science"),
                ("medicine", "Medicine"), ("medical", "Medicine"),
                ("saude", "Health Sciences"), ("health", "Health Sciences"),
                ("social", "Social Sciences"), ("psicologia", "Psychology"),
                ("engineering", "Engineering"), ("arte", "Arts"),
                ("economia", "Economics"), ("direito", "Law"),
                ("fisica", "Physics"), ("biologia", "Biological Sciences"),
            ]
            for kw, area in mapping:
                if kw in text:
                    return area
            return "Social Sciences"

    def _similarity(self, text_a: str, text_b: str) -> float:
        """Similaridade cosseno entre dois textos"""
        try:
            if not text_a.strip() or not text_b.strip():
                return 30.0
            vecs = self.vectorizer.fit_transform([text_a, text_b]).toarray()
            sim = cosine_similarity([vecs[0]], [vecs[1]])[0][0]
            return round(max(0, min(95, sim * 100)), 2)
        except:
            return 30.0


class MatchJournalV2:
    """
    Pipeline completo de 8 camadas.
    Dados disponiveis: Titulo, Grande Area, Area do Conhecimento,
    Subarea, Indexador, Quartil JCR, SJR, H index, Indice h5
    """

    def __init__(self, df_local: pd.DataFrame, llm_model: str = "llama3"):
        self.df = df_local.copy()
        self.kernel = SemanticKernelStyle(model=llm_model)
        # Mapeia colunas para nomes normalizados (sem acentos para matching)
        self.col_map = {}
        for c in self.df.columns:
            k = c.strip()
            # Corrige encoding corrompido
            k = k.replace('\ufffd', 'a').replace('\ufffd', 'a')
            self.col_map[c] = k

    def _col(self, row: pd.Series, *nomes: str) -> str:
        """Busca valor na coluna por nome alternativo"""
        for nome in nomes:
            for col_orig, col_norm in self.col_map.items():
                if col_norm.lower().strip() == nome.lower().strip():
                    val = row.get(col_orig, "")
                    if pd.notna(val) and str(val).strip() not in ["", "-", "nan", "None"]:
                        return str(val).strip()
        return ""

    def recommend(self, titulo: str, resumo: str,
                  order_by: str = "probability", top_n: int = 20) -> List[Dict]:
        """
        Pipeline completo:

        1. Knowledge Area via LLM
        2. Filtro por Knowledge Area nas colunas Grande Area / Area do Conhecimento / Subarea
        3. Adherence Score via similaridade cosseno com nome + area + subarea
        4. Top 300
        5. Estimated Acceptance Probability (adherence x fator quartil)
        6. Top 40
        7. Ordenar por probability (desc)
        8. Output Top 20 com justificativa textual
        """
        query_text = f"{titulo} {resumo}"

        # --- CAMADA 1: Knowledge Area ---
        knowledge_area = self.kernel._classify_knowledge_area(titulo, resumo)
        logger.info(f"Knowledge Area: {knowledge_area}")

        # --- CAMADA 2: Filtro por Knowledge Area ---
        ka_lower = knowledge_area.lower()
        mask = pd.Series(False, index=self.df.index)
        for col in self.df.columns:
            cn = self.col_map[col].lower()
            if "grande area" in cn or "conhecimento" in cn or "subarea" in cn or "area do" in cn:
                mask = mask | self.df[col].astype(str).str.lower().str.contains(ka_lower, na=False)
                mask = mask | self.df[col].astype(str).str.lower().str.contains(ka_lower.split()[-1], na=False)

        df_filtered = self.df[mask].copy()
        if df_filtered.empty:
            logger.warning(f"Knowledge Area '{knowledge_area}' nao encontrada. Fallback.")
            df_filtered = self.df.head(300).copy()

        # --- CAMADA 3: Adherence Score ---
        scores = []
        for idx, row in df_filtered.iterrows():
            nome = self._col(row, "Titulo da Revista", "title")
            grande_area = self._col(row, "Grande Area", "grande area")
            area = self._col(row, "Area do Conhecimento", "area do conhecimento")
            subarea = self._col(row, "Subarea do Conhecimento", "subarea do conhecimento")
            indexador = self._col(row, "Indexador", "indexador")

            # Texto combinado da revista para similaridade
            texto_revista = f"{nome} {grande_area} {area} {subarea} {indexador}"

            # Similaridade cosseno entre artigo e revista
            score = self.kernel._similarity(query_text, texto_revista)
            scores.append(score)

        df_filtered["adherence_score"] = scores

        # --- CAMADA 4: Top 300 ---
        df_filtered = df_filtered.sort_values("adherence_score", ascending=False)
        df_secondary = df_filtered.head(300).copy()

        # --- CAMADA 5: Estimated Acceptance Probability ---
        probs = []
        for idx, row in df_secondary.iterrows():
            adh = row["adherence_score"]
            q = self._col(row, "Quartil JCR", "quartil jcr").upper()
            fator = {"Q1": 0.65, "Q2": 0.78, "Q3": 0.88, "Q4": 0.95}.get(q, 0.82)
            p = min(95, max(10, round(adh * fator, 1)))
            probs.append(p)

        df_secondary["probability"] = probs

        # --- CAMADA 6: Top 40 ---
        df_tertiary = df_secondary.head(40).copy()

        # --- CAMADA 7: Ordenar por probability (default) ---
        df_tertiary = df_tertiary.sort_values("probability", ascending=False)

        # --- CAMADA 8: Output Top 20 ---
        top_results = df_tertiary[df_tertiary["probability"] > 60].head(top_n)

        results = []
        for idx, row in top_results.iterrows():
            nome = self._col(row, "Titulo da Revista", "title")
            grande_area = self._col(row, "Grande Area", "grande area")
            area = self._col(row, "Area do Conhecimento", "area do conhecimento")
            quartil = self._col(row, "Quartil JCR", "quartil jcr")
            indexador = self._col(row, "Indexador", "indexador")
            adh = row.get("adherence_score", 50)
            prob = row.get("probability", 50)

            # Justificativa textual (ate 4 linhas)
            just = f"A revista {nome} (Quartil {quartil}, {indexador}) apresenta forte alinhamento tematico com sua pesquisa em {area}."
            just += f" O escopo editorial cobre temas como {grande_area}, "
            just += f"compativel com o enfoque do seu artigo. "
            just += f"Score de aderencia: {adh}%. "
            just += f"Probabilidade estimada de aceitacao: {prob}%."

            results.append({
                "nome": nome,
                "issn": self._col(row, "ISSN", "issn"),
                "grande_area": grande_area,
                "area": area,
                "subarea": self._col(row, "Subarea do Conhecimento", "subarea do conhecimento"),
                "quartil": quartil,
                "sjr": self._col(row, "SJR", "sjr"),
                "indexador": indexador,
                "h5_link": self._col(row, "Indice h5"),
                "adherence_score": adh,
                "probability": prob,
                "justificativa": just,
                "knowledge_area": knowledge_area,
            })

        return results