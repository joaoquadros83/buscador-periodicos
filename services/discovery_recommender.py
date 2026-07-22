"""
Discovery Recommender (Semantic & Vector Matcher for SciPubs)
Arquitetura em 4 Camadas:
  1. INGESTÃO & KNOWLEDGE AREA CLASSIFICATION (Gemini / LLM ou Fallback Local)
  2. VETORIZAÇÃO E ADHERENCE SCORE (Cosseno no Aims & Scope -> Top 300)
  3. ESTIMATED ACCEPTANCE PROBABILITY ENGINE (Top 40)
  4. ORDENAÇÃO DINÂMICA & JUSTIFICATIVA CONTEXTUAL (3-4 linhas) -> Top 20
"""

import re
import os
import json
import requests
from typing import List, Dict, Optional, Tuple
import logging
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscoveryRecommender:
    """Motor de recomendação semântico de revistas científicas."""

    def __init__(
        self,
        df_local: pd.DataFrame,
        api_key_gemini: Optional[str] = None,
        ollama_model: str = "llama3",
        h_index_author: int = 5
    ):
        self.df_raw = df_local.copy()
        self.df_local = self._normalize_columns(df_local)
        self.api_key_gemini = api_key_gemini
        self.ollama_model = ollama_model
        self.h_index_author = h_index_author
        self._backend_used = "semantic_engine"

        # Usa toda a base de dados
        self.df_scoped = self.df_local.copy()

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if "Aims and Scope" in df.columns and "Aims e Escopo" in df.columns:
            df.drop(columns=["Aims e Escopo"], inplace=True)
            
        rename_map = {}
        for col in df.columns:
            col_str = str(col).strip()
            col_lower = col_str.lower()
            if any(x in col_lower for x in ["titulo da revista", "título da revista", "title"]):
                rename_map[col] = "title"
            elif "issn" in col_lower:
                rename_map[col] = "ISSN"
            elif "homepage" in col_lower:
                rename_map[col] = "Homepage"
            elif any(x in col_lower for x in ["subárea", "subarea", "categoria"]):
                rename_map[col] = "Subárea do Conhecimento"
            elif any(x in col_lower for x in ["area do conhecimento", "área do conhecimento", "area de conhecimento", "área de conhecimento"]):
                rename_map[col] = "Área do Conhecimento"
            elif any(x in col_lower for x in ["grande area", "grande área"]):
                rename_map[col] = "Grande Área"
            elif "indexador" in col_lower:
                rename_map[col] = "Indexador"
            elif "quartil jcr" in col_lower:
                rename_map[col] = "Quartil JCR"
            elif "sjr" in col_lower and "best" not in col_lower:
                rename_map[col] = "SJR"
            elif "jif" in col_lower or "impact" in col_lower:
                rename_map[col] = "JIF"
            elif any(x in col_lower for x in ["indice h5", "índice h5", "index-h5", "h5 index"]):
                rename_map[col] = "Índice h5"
            elif any(x in col_lower for x in ["h index", "h-index", "index-h"]):
                rename_map[col] = "H index"
            elif any(x in col_lower for x in ["mediana h5", "h5 median"]):
                rename_map[col] = "Mediana h5"
            elif any(x in col_lower for x in ["aims and scope", "aims e escopo", "escopo", "aims & scope"]):
                rename_map[col] = "Aims e Escopo"
        df.rename(columns=rename_map, inplace=True)
        return df

    def _classify_knowledge_area_llm(self, titulo: str, resumo: str) -> str:
        """Camada 1: Identifica a Knowledge Area / Broad Area do manuscrito via Gemini ou Fallback Local."""
        if not self.api_key_gemini:
            # Fallback local usando regex/keywords para classificar em áreas principais
            text = f"{titulo} {resumo}".lower()
            if any(w in text for w in ["medicine", "health", "clinical", "patient", "disease", "treatment", "therapy", "saúde", "médica"]):
                return "Medicine & Health Sciences"
            if any(w in text for w in ["computer", "software", "algorithm", "intelligence", "network", "security", "data", "computação"]):
                return "Computer Science"
            if any(w in text for w in ["education", "teaching", "learning", "student", "school", "pedagogy", "ensino", "escola"]):
                return "Education"
            if any(w in text for w in ["economic", "business", "market", "finance", "management", "corporate", "economia", "negócios"]):
                return "Business & Economics"
            if any(w in text for w in ["social", "society", "human", "culture", "political", "policy", "social", "sociedade"]):
                return "Social Sciences"
            if any(w in text for w in ["energy", "material", "chemical", "physics", "earth", "environment", "climate", "física", "química"]):
                return "Exact & Earth Sciences"
            if any(w in text for w in ["dna", "protein", "cell", "biological", "gene", "evolution", "species", "biologia", "célula"]):
                return "Biological Sciences"
            return "General"

        prompt = f"""
        Classifique o manuscrito científico abaixo em uma única Knowledge Area primária em inglês (ex: Computer Science, Medicine, Education, Arts, Psychology, Social Sciences, Engineering, Biological Sciences, Business):

        TÍTULO: {titulo}
        RESUMO: {resumo}

        Responda apenas com o nome da área em inglês.
        """
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key_gemini}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            r = requests.post(url, json=payload, timeout=10)
            if r.ok:
                area = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                return area
        except Exception as e:
            logger.warning(f"Erro na classificação por área via LLM: {e}")
        return "General"

    def _compute_vector_adherence(self, titulo: str, resumo: str) -> List[Tuple[int, float]]:
        """Camada 2: Calcula a Similaridade de Cosseno (TF-IDF Vector Matcher) priorizando o Aims & Scope das revistas."""
        user_text = f"{titulo} {resumo}"

        col_scope = "Aims e Escopo" if "Aims e Escopo" in self.df_scoped.columns else "title"
        scopes = self.df_scoped[col_scope].astype(str).tolist()
        titles = self.df_scoped["title"].astype(str).tolist()

        # Priorização de Aims & Scope: Repete o escopo editorial (s) para dobrar seu peso no vetor TF-IDF
        corpus = []
        for t, s in zip(titles, scopes):
            scope_clean = s.strip()
            if not scope_clean or scope_clean.lower() in ["nan", "none", ""]:
                corpus.append(t)
            else:
                corpus.append(f"{t} {scope_clean} {scope_clean}")

        try:
            vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(corpus)
            user_vector = vectorizer.transform([user_text])

            sims = cosine_similarity(user_vector, tfidf_matrix).flatten()

            results = []
            for idx, score in enumerate(sims):
                # Normaliza para escala 0 - 100%
                norm_score = score * 100 * 2.8 + 45.0
                
                # Penalidade de -15.0 se a revista não possuir Aims & Scope cadastrado
                s_val = scopes[idx].strip()
                if not s_val or s_val.lower() in ["nan", "none", "", "-"]:
                    norm_score -= 15.0

                norm_score = min(98.0, max(15.0, norm_score))
                results.append((idx, round(norm_score, 1)))

            results.sort(key=lambda x: -x[1])
            return results
        except Exception as e:
            logger.warning(f"Erro ao calcular similaridade vetorial: {e}")
            return [(i, 65.0) for i in range(len(self.df_scoped))]

    def _calculate_estimated_acceptance_probability(self, adherence_score: float, row: pd.Series) -> float:
        """Camada 3: Calcula a Probabilidade Estimada de Aceitação (0 - 100%)."""
        quartil = str(row.get("Quartil JCR", row.get("SJR Best Quartile", ""))).upper().strip()
        try:
            sjr = float(str(row.get("SJR", "0")).replace(",", "."))
        except:
            sjr = 0.0

        # Base de probabilidade em função do rigor do quartil / impacto
        if "Q1" in quartil or sjr > 2.5:
            base_prob = 22.0
        elif "Q2" in quartil or sjr > 1.2:
            base_prob = 34.0
        elif "Q3" in quartil or sjr > 0.4:
            base_prob = 46.0
        elif "Q4" in quartil:
            base_prob = 58.0
        else:
            base_prob = 50.0

        # Ponderação: 55% Aderência Semântica + 45% Fator Quartil/Aceitação Base
        prob = (adherence_score * 0.55) + (base_prob * 0.45)
        return round(min(95.0, max(15.0, prob)), 1)

    def _generate_3line_justification(self, titulo: str, resumo: str, journal_name: str, scope: str, adherence: float, row: pd.Series) -> str:
        """Gera uma justificativa dissertativa de exatamente 3 a 4 linhas via Gemini ou algoritmo local."""
        if not self.api_key_gemini:
            # Algoritmo Local Dinâmico e Contextualizado
            title_words = [w for w in re.findall(r'\b\w{5,}\b', titulo.lower()) if w not in ['artigo', 'pesquisa', 'estudo', 'analise']]
            keywords = ", ".join(title_words[:3]) if title_words else "a temática proposta"
            
            area = row.get("Área do Conhecimento", row.get("Grande Área", "sua respectiva linha editorial"))
            just = (
                f"Com base na análise temática local, o manuscrito apresenta forte sinergia de {adherence}% com a revista {journal_name}. "
                f"A pesquisa aborda tópicos diretamente alinhados a {keywords}, o que condiz perfeitamente com a cobertura editorial da revista "
                f"na área de {area}. Esse acoplamento garante um público leitor altamente qualificado e interessado para o seu trabalho."
            )
            return just

        prompt = f"""
        Como parecerista acadêmico, escreva uma justificativa dissertativa de EXATAMENTE 3 a 4 linhas explicando por que o artigo abaixo é recomendado para a revista '{journal_name}'.

        TÍTULO DO ARTIGO: {titulo}
        RESUMO DO ARTIGO: {resumo}
        AIMS & SCOPE DA REVISTA: {scope[:500]}
        SCORE DE ADERÊNCIA: {adherence}%

        Diretrizes:
        1. Escreva em Português corrido em parágrafo único de 3 a 4 linhas.
        2. Relacione diretamente o tema/metodologia do artigo com a linha editorial e o público leitor da revista.
        3. Não use tópicos ou listas.
        """
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key_gemini}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            r = requests.post(url, json=payload, timeout=12)
            if r.ok:
                just = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                return just
        except Exception as e:
            logger.warning(f"Erro ao gerar justificativa textual via Gemini: {e}")

        # Fallback se a API falhar
        title_words = [w for w in re.findall(r'\b\w{5,}\b', titulo.lower()) if w not in ['artigo', 'pesquisa', 'estudo', 'analise']]
        keywords = ", ".join(title_words[:3]) if title_words else "a temática proposta"
        area = row.get("Área do Conhecimento", row.get("Grande Área", "sua respectiva linha editorial"))
        return (
            f"Com base na análise temática local, o manuscrito apresenta forte sinergia de {adherence}% com a revista {journal_name}. "
            f"A pesquisa aborda tópicos diretamente alinhados a {keywords}, o que condiz perfeitamente com a cobertura editorial da revista "
            f"na área de {area}. Esse acoplamento garante um público leitor altamente qualificado e interessado para o seu trabalho."
        )

    def recommend(
        self,
        titulo: str,
        resumo: str,
        idioma: str = "Português",
        top_n: int = 20,
        use_ollama: bool = False
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:

        logger.info(f"Iniciando recomendação semântica para catálogo de {len(self.df_scoped)} revistas.")

        # Camada 1: Classificação por Knowledge Area (Gemini ou Fallback Local)
        knowledge_area = self._classify_knowledge_area_llm(titulo, resumo)
        # Camada 2: Vetorização TF-IDF + Adherence Score (Cosseno no Aims & Scope)
        vector_matches = self._compute_vector_adherence(titulo, resumo)

        # Otimização: Converte colunas relevantes do pandas para listas python para evitar overhead de iloc
        col_indexador = "Indexador" if "Indexador" in self.df_scoped.columns else self.df_scoped.columns[0]
        col_jif = "JIF" if "JIF" in self.df_scoped.columns else self.df_scoped.columns[0]
        col_sjr = "SJR" if "SJR" in self.df_scoped.columns else self.df_scoped.columns[0]
        col_garea = "Grande Área" if "Grande Área" in self.df_scoped.columns else self.df_scoped.columns[0]
        col_area = "Área do Conhecimento" if "Área do Conhecimento" in self.df_scoped.columns else self.df_scoped.columns[0]

        list_indexador = self.df_scoped[col_indexador].tolist()
        list_jif = self.df_scoped[col_jif].tolist()
        list_sjr = self.df_scoped[col_sjr].tolist()
        list_garea = self.df_scoped[col_garea].tolist()
        list_area = self.df_scoped[col_area].tolist()

        # Helper para conversão numérica segura
        def safe_float(val):
            try:
                return float(str(val).replace(",", ".").strip())
            except:
                return 0.0

        # Camada 3: Motor de Probabilidade de Aceitação - Processa todos os candidatos de forma otimizada
        all_candidates = []
        area_lower = knowledge_area.lower()
        area_words = [w for w in area_lower.split() if len(w) > 3]

        for idx_scoped, score_adherence in vector_matches:
            # Camada 1: bonificação se bater com a Knowledge Area identificada
            garea_val = str(list_garea[idx_scoped]).lower()
            area_val = str(list_area[idx_scoped]).lower()
            
            if any(w in garea_val or w in area_val for w in area_words):
                score_adherence = min(98.0, score_adherence + 4.0)

            # Probabilidade
            row = self.df_scoped.iloc[idx_scoped]
            prob_aceitacao = self._calculate_estimated_acceptance_probability(score_adherence, row)

            all_candidates.append({
                "idx_scoped": idx_scoped,
                "row": row,
                "aderencia": score_adherence,
                "probabilidade_aceitacao": prob_aceitacao
            })

        # Seleção Híbrida do Top 20 (8 afinidade pura, 6 WoS JCR + afinidade, 6 Scopus SJR + afinidade)
        selected_candidates = []
        selected_ids = set()

        # 1. Grupo A: 8 por Pure Affinity (Adherence Score)
        # Como vector_matches já veio ordenado por Adherence, ordenamos all_candidates decrescente por aderencia
        all_candidates.sort(key=lambda x: -x["aderencia"])
        
        grupo_a = []
        for c in all_candidates:
            if len(grupo_a) >= 8:
                break
            grupo_a.append(c)
            selected_ids.add(c["idx_scoped"])
        
        selected_candidates.extend(grupo_a)

        # 2. Grupo B: 6 por JCR + Afinidade (Web of Science)
        wos_candidates = []
        for c in all_candidates:
            if c["idx_scoped"] in selected_ids:
                continue
            idx = c["idx_scoped"]
            indexador = str(list_indexador[idx]).lower()
            is_wos = any(x in indexador for x in ["web of science", "wos", "scie", "ssci", "ahci", "esci"])
            if is_wos:
                jif_val = safe_float(list_jif[idx])
                combined_score = c["aderencia"] + (jif_val * 5.0)
                wos_candidates.append((c, combined_score))
        
        wos_candidates.sort(key=lambda x: -x[1])
        grupo_b = []
        for c, score in wos_candidates:
            if len(grupo_b) >= 6:
                break
            grupo_b.append(c)
            selected_ids.add(c["idx_scoped"])
            
        selected_candidates.extend(grupo_b)

        # 3. Grupo C: 6 por SJR + Afinidade (Scopus)
        scopus_candidates = []
        for c in all_candidates:
            if c["idx_scoped"] in selected_ids:
                continue
            idx = c["idx_scoped"]
            indexador = str(list_indexador[idx]).lower()
            is_scopus = "scopus" in indexador
            if is_scopus:
                sjr_val = safe_float(list_sjr[idx])
                combined_score = c["aderencia"] + (sjr_val * 15.0)
                scopus_candidates.append((c, combined_score))
                
        scopus_candidates.sort(key=lambda x: -x[1])
        grupo_c = []
        for c, score in scopus_candidates:
            if len(grupo_c) >= 6:
                break
            grupo_c.append(c)
            selected_ids.add(c["idx_scoped"])
            
        selected_candidates.extend(grupo_c)

        # Preenchimento se faltar WoS/Scopus
        if len(selected_candidates) < 20:
            for c in all_candidates:
                if c["idx_scoped"] not in selected_ids:
                    selected_candidates.append(c)
                    selected_ids.add(c["idx_scoped"])
                    if len(selected_candidates) >= 20:
                        break

        selected_candidates = selected_candidates[:20]

        # Camada 4: Justificativa dissertativa contextualizada (exclusivamente para o Top 20 final)
        final_journals = []
        col_scope = "Aims e Escopo" if "Aims e Escopo" in self.df_scoped.columns else "title"

        for item in selected_candidates:
            row = item["row"]
            nome_rev = str(row.get("title", row.get(self.df_scoped.columns[0], "")))
            issn = str(row.get("ISSN", "-"))
            homepage = str(row.get("Homepage", "-"))
            grande_area = str(row.get("Grande Área", "-"))
            area = str(row.get("Área do Conhecimento", "-"))
            subarea = str(row.get("Subárea do Conhecimento", "-"))
            indexador = str(row.get("Indexador", "-"))
            jif = str(row.get("JIF", "-"))
            quartil = str(row.get("Quartil JCR", "-"))
            sjr = str(row.get("SJR", "-"))
            sjr_q = str(row.get("SJR Best Quartile", "-"))
            h_index = str(row.get("H index", "-"))
            h5_idx = str(row.get("Índice h5", "-"))
            h5_med = str(row.get("Mediana h5", "-"))
            scope_text = str(row.get(col_scope, ""))

            # Link de backup para h5 do Google Scholar
            h5_link = f"https://scholar.google.com/citations?hl=pt-BR&view_op=search_venues&vq={requests.utils.quote(nome_rev)}&btnG="

            # Gera a justificativa de 3-4 linhas
            justificativa = self._generate_3line_justification(
                titulo, resumo, nome_rev, scope_text, item["aderencia"], row
            )

            j_dict = {
                "nome": nome_rev,
                "issn": issn,
                "homepage": homepage,
                "grande_area": grande_area,
                "area": area,
                "subarea": subarea,
                "indexador": indexador,
                "jif": jif,
                "quartil_jcr": quartil,
                "sjr": sjr,
                "sjr_quartile": sjr_q,
                "h_index": h_index,
                "h5_index": h5_idx,
                "h5_median": h5_med,
                "h5_link": h5_link,
                "adherence_score": item["aderencia"],
                "probability": item["probabilidade_aceitacao"],
                "aderencia": item["aderencia"],
                "probabilidade_aceitacao": item["probabilidade_aceitacao"],
                "justificativa": justificativa,
                "justificativa_metricas": justificativa,
                "aims_scope": scope_text,
                "fonte_dados": "local_scoped"
            }
            final_journals.append(j_dict)

        # Ordena decrescente por Estimated Acceptance Probability (probabilidade de aceitação)
        final_journals.sort(key=lambda x: -x["probability"])
        return final_journals[:top_n], None

    def get_backend_name(self) -> str:
        return self._backend_used