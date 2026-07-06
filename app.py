import streamlit as st
import pandas as pd
import os

# 1. Configuração da Página
st.set_page_config(page_title="Buscador Multibases de Periódicos", layout="wide", page_icon="📚")

# 2. Carregamento com Cache Inteligente (Limpa a memória a cada 1 hora para não travar atualizações)
@st.cache_data(ttl=3600)
def carregar_base(nome_arquivo):
    if os.path.exists(nome_arquivo):
        if nome_arquivo.endswith('.xlsx'):
            return pd.read_excel(nome_arquivo)
        elif nome_arquivo.endswith('.csv'):
            return pd.read_csv(nome_arquivo)
    return None

base_scielo = carregar_base("scielo_original.csv")
base_educa = carregar_base("educa_original.csv")
base_scopus = carregar_base("scopus_original.xlsx")
base_wos = carregar_base("wos_original.xlsx")

# 3. Cabeçalho Principal
st.title("📚 Buscador Multibases de Periódicos Acadêmicos")
st.markdown("Consulte e exporte listas de periódicos de forma independente por indexador científico.")
st.markdown("---")

# 4. Criação das Abas
abas = st.tabs(["🟢 SciELO", "🟠 Educ@", "💚 Scopus", "🔷 Web of Science (WoS)"])

# --- ABA 1: SciELO ---
with abas[0]:
    st.header("Periódicos SciELO")
    if base_scielo is not None:
        busca = st.text_input("Buscar por título na SciELO:", key="b_scielo")
        df_f = base_scielo.copy()
        col_t = next((c for c in df_f.columns if 'tit' in c.lower() or 'nome' in c.lower()), df_f.columns[0])
        if busca:
            df_f = df_f[df_f[col_t].astype(str).str.contains(busca, case=False, na=False)]
        
        st.metric("Revistas Encontradas", len(df_f))
        st.dataframe(df_f, use_container_width=True)
        
        # Botão de Download Independente
        st.download_button("📥 Baixar Resultado SciELO", df_f.to_csv(index=False).encode('utf-8-sig'), "scielo_filtrado.csv", "text/csv", key='dl_scielo')
    else:
        st.warning("Arquivo da base SciELO não encontrado.")

# --- ABA 2: Educ@ ---
with abas[1]:
    st.header("Periódicos Educ@ (FCC)")
    if base_educa is not None:
        busca = st.text_input("Buscar por título no Educ@:", key="b_educa")
        df_f = base_educa.copy()
        col_t = next((c for c in df_f.columns if 'tit' in c.lower() or 'nome' in c.lower()), df_f.columns[0])
        if busca:
            df_f = df_f[df_f[col_t].astype(str).str.contains(busca, case=False, na=False)]
        
        st.metric("Revistas Encontradas", len(df_f))
        st.dataframe(df_f, use_container_width=True)
        
        st.download_button("📥 Baixar Resultado Educ@", df_f.to_csv(index=False).encode('utf-8-sig'), "educa_filtrado.csv", "text/csv", key='dl_educa')
    else:
        st.warning("Arquivo da base Educ@ não encontrado.")

# --- ABA 3: Scopus ---
with abas[2]:
    st.header("Periódicos Scopus (Base Oficial)")
    if base_scopus is not None:
        busca = st.text_input("Buscar por título na Scopus:", key="b_scopus")
        df_f = base_scopus.copy()
        col_t = next((c for c in df_f.columns if 'title' in c.lower() or 'tit' in c.lower()), df_f.columns[0])
        
        # Filtro de Colunas para a Scopus não ficar gigante na tela
        colunas_visiveis = [c for c in ['Source Title', 'Print-ISSN', 'E-ISSN', 'Publisher', 'Active or Inactive'] if c in df_f.columns]
        if not colunas_visiveis: colunas_visiveis = df_f.columns[:5]
        
        if busca:
            df_f = df_f[df_f[col_t].astype(str).str.contains(busca, case=False, na=False)]
        
        st.metric("Revistas Encontradas", len(df_f))
        st.dataframe(df_f[colunas_visiveis], use_container_width=True)
        
        st.download_button("📥 Baixar Resultado Scopus", df_f.to_csv(index=False).encode('utf-8-sig'), "scopus_filtrado.csv", "text/csv", key='dl_scopus')
    else:
        st.warning("Arquivo 'scopus_original.xlsx' não encontrado.")

# --- ABA 4: Web of Science ---
with abas[3]:
    st.header("Periódicos Web of Science (WoS)")
    if base_wos is not None:
        busca = st.text_input("Buscar por título na WoS:", key="b_wos")
        df_f = base_wos.copy()
        col_t = next((c for c in df_f.columns if 'title' in c.lower() or 'tit' in c.lower()), df_f.columns[0])
        
        if busca:
            df_f = df_f[df_f[col_t].astype(str).str.contains(busca, case=False, na=False)]
        
        st.metric("Revistas Encontradas", len(df_f))
        st.dataframe(df_f, use_container_width=True)
        
        st.download_button("📥 Baixar Resultado WoS", df_f.to_csv(index=False).encode('utf-8-sig'), "wos_filtrado.csv", "text/csv", key='dl_wos')
    else:
        st.warning("Arquivo 'wos_original.xlsx' não encontrado.")