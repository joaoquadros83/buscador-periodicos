import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA (Interface em modo amplo e profissional)
st.set_page_config(
    page_title="Portal de Periódicos Científicos",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. FUNÇÃO COM CACHE (Carrega as 53 mil linhas uma única vez na memória)
@st.cache_data
def carregar_dados():
    # Carrega o arquivo final consolidado e tratado
    df = pd.read_csv("dados_revistas.csv", sep=";", encoding="utf-8-sig", low_memory=False)
    
    # Remove duplicatas pelo Título da Revista (Coluna 1) por segurança
    col_titulo = df.columns[0]
    df = df.drop_duplicates(subset=[col_titulo])
    
    # Remove colunas fantasmas geradas por delimitadores extras no final do CSV
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Limpa os nomes das colunas de espaços em branco invisíveis
    df.columns = [c.strip() for c in df.columns]
    
    # Garante que as colunas de métricas sejam tratadas como números decimais do Python
    for col in ['SJR', 'JIF', 'h-index', 'H index']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').astype(float, errors='ignore')
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    return df

# Inicialização segura da base de dados
try:
    df_original = carregar_dados()
except Exception as e:
    st.error(f"⚠️ Erro ao carregar o arquivo 'dados_revistas.csv'. Verifique o nome e se o separador é ';'. Detalhes: {e}")
    st.stop()

# --- BARRA LATERAL: FILTROS AVANÇADOS REQUISITADOS ---
st.sidebar.header("🔍 Filtros de Busca")

# Filtro 1: Palavra-Chave (Título ou ISSN)
busca = st.sidebar.text_input("Buscar por Nome da Revista ou ISSN:")

st.sidebar.markdown("---")
st.sidebar.subheader("Filtragem por Escopo")

# Filtro 2: Grande Área CNPq (Varre Coluna 1 e Coluna 2 simultaneamente)
cnpq_1_cols = [c for c in df_original.columns if 'cnpq 1' in c.lower() or 'cnpq1' in c.lower()]
cnpq_2_cols = [c for c in df_original.columns if 'cnpq 2' in c.lower() or 'cnpq2' in c.lower()]

col_cnpq1 = cnpq_1_cols[0] if cnpq_1_cols else None
col_cnpq2 = cnpq_2_cols[0] if cnpq_2_cols else None

if col_cnpq1 and col_cnpq2:
    # Agrupa valores únicos de ambas as colunas do CNPq para montar a lista do filtro
    todas_areas_cnpq = set(df_original[col_cnpq1].dropna().unique()).union(
        set(df_original[col_cnpq2].dropna().unique())
    )
    lista_cnpq = sorted([str(x).strip() for x in todas_areas_cnpq if str(x).strip() != ""])
    cnpq_selecionado = st.sidebar.selectbox("Grande Área CNPq:", ["Todas"] + lista_cnpq)
else:
    st.sidebar.warning("Colunas de Grande Área CNPq não encontradas.")
    cnpq_selecionado = "Todas"

# Filtro 3: Área do Conhecimento (Traduzida)
col_area_especifica = "Área do Conhecimento" if "Área do Conhecimento" in df_original.columns else [c for c in df_original.columns if 'conhecimento' in c.lower()][0]
todas_areas_especificas = set()
for x in df_original[col_area_especifica].dropna():
    for area in str(x).split(","):
        todas_areas_especificas.add(area.strip())
lista_areas_especificas = sorted(list(todas_areas_especificas))
area_especifica_sel = st.sidebar.selectbox("Área do Conhecimento (Específica):", ["Todas"] + lista_areas_especificas)

# Filtro 4: Indexador (Scopus, JCR, etc.)
col_indexador = "Indexador" if "Indexador" in df_original.columns else ([c for c in df_original.columns if 'indexador' in c.lower()][0] if [c for c in df_original.columns if 'indexador' in c.lower()] else None)
if col_indexador:
    indexadores_disponiveis = sorted([str(x).strip() for x in df_original[col_indexador].dropna().unique() if str(x).strip() != ""])
    indexador_sel = st.sidebar.multiselect("Indexador:", indexadores_disponiveis, default=indexadores_disponiveis)
else:
    indexador_sel = []

st.sidebar.markdown("---")
st.sidebar.subheader("Filtragem por Qualidade/Impacto")

# Filtro 5: Quartil JCR (Web of Science)
col_q_jcr = "Quartil JCR" if "Quartil JCR" in df_original.columns else ([c for c in df_original.columns if 'jcr' in c.lower()][0] if [c for c in df_original.columns if 'jcr' in c.lower()] else None)
if col_q_jcr:
    q_jcr_disponiveis = sorted([str(x).strip() for x in df_original[col_q_jcr].dropna().unique() if str(x).strip() != ""])
    q_jcr_sel = st.sidebar.multiselect("Quartil JCR (WoS):", q_jcr_disponiveis, default=q_jcr_disponiveis)
else:
    q_jcr_sel = []

# Filtro 6: SJR Best Quartile (Scopus)
col_q_sjr = "SJR Best Quartile" if "SJR Best Quartile" in df_original.columns else ([c for c in df_original.columns if 'sjr' in c.lower() and 'quartile' in c.lower()][0] if [c for c in df_original.columns if 'sjr' in c.lower()] else None)
if col_q_sjr:
    q_sjr_disponiveis = sorted([str(x).strip() for x in df_original[col_q_sjr].dropna().unique() if str(x).strip() != ""])
    q_sjr_sel = st.sidebar.multiselect("SJR Best Quartile (Scopus):", q_sjr_disponiveis, default=q_sjr_disponiveis)
else:
    q_sjr_sel = []

# Opção de Ordenação Dinâmica
opcoes_ordenacao = ["Título"]
if "SJR" in df_original.columns: opcoes_ordenacao.append("SJR (Prestígio Scopus)")
if "JIF" in df_original.columns: opcoes_ordenacao.append("JIF (Fator de Impacto JCR)")
if "H index" in df_original.columns: opcoes_ordenacao.append("H index (Impacto Histórico)")
if "h-index" in df_original.columns: opcoes_ordenacao.append("h-index (Impacto Histórico)")

criterio_ordem = st.sidebar.selectbox("Ordenar resultados por:", options=opcoes_ordenacao)


# --- CORPO PRINCIPAL DO APLICATIVO ---
st.title("📚 Buscador Inteligente de Periódicos Científicos")
st.markdown("Ferramenta profissional para pesquisadores identificarem as melhores revistas nacionais e internacionais para submissão de manuscritos.")
st.markdown("---")

# Criando a cópia dos dados para iniciar a filtragem em cascata
df_filtrado = df_original.copy()

# APLICAÇÃO LOGÍCA DOS FILTROS

# 1. Filtro de Palavra-chave (Título ou ISSN)
if busca:
    col_titulo = df_filtrado.columns[0]
    col_issn = "ISSN" if "ISSN" in df_filtrado.columns else [c for c in df_filtrado.columns if 'issn' in c.lower()][0]
    df_filtrado = df_filtrado[
        df_filtrado[col_titulo].str.contains(busca, case=False, na=False) |
        df_filtrado[col_issn].str.contains(busca, case=False, na=False)
    ]

# 2. LÓGICA REQUISITADA: Busca simultânea em Grande Área CNPq 1 OU Grande Área CNPq 2
if cnpq_selecionado != "Todas" and col_cnpq1 and col_cnpq2:
    df_filtrado = df_filtrado[
        (df_filtrado[col_cnpq1] == cnpq_selecionado) | 
        (df_filtrado[col_cnpq2] == cnpq_selecionado)
    ]

# 3. Filtro de Área do Conhecimento (Especifica)
if area_especifica_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado[col_area_especifica].str.contains(area_especifica_sel, case=False, na=False)]

# 4. Filtro de Indexador
if col_indexador and indexador_sel:
    df_filtrado = df_filtrado[df_filtrado[col_indexador].astype(str).str.strip().isin(indexador_sel)]

# 5. Filtro de Quartil JCR
if col_q_jcr and q_jcr_sel:
    df_filtrado = df_filtrado[df_filtrado[col_q_jcr].astype(str).str.strip().isin(q_jcr_sel)]

# 6. Filtro de Quartil SJR
if col_q_sjr and q_sjr_sel:
    df_filtrado = df_filtrado[df_filtrado[col_q_sjr].astype(str).str.strip().isin(q_sjr_sel)]

# Aplicação da Ordenação escolhida pelo usuário
mapa_ordem = {
    "SJR (Prestígio Scopus)": ("SJR", False),
    "JIF (Fator de Impacto JCR)": ("JIF", False),
    "H index (Impacto Histórico)": ("H index", False),
    "h-index (Impacto Histórico)": ("h-index", False),
    "Título": (df_filtrado.columns[0], True)
}
col_ordenar, ascendente = mapa_ordem[criterio_ordem]
if col_ordenar in df_filtrado.columns:
    df_filtrado = df_filtrado.sort_values(by=col_ordenar, ascending=ascendente)


# --- EXIBIÇÃO DE METRICAS (DASHBOARD HIGHLIGHTS) ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Revistas Filtradas", f"{len(df_filtrado):,}".replace(",", "."))
with col2:
    col_h = "H index" if "H index" in df_filtrado.columns else ("h-index" if "h-index" in df_filtrado.columns else None)
    maior_h = int(df_filtrado[col_h].max()) if col_h and not df_filtrado[col_h].isna().all() else 0
    st.metric("Maior H-Index", maior_h)
with col3:
    maior_jif = df_filtrado['JIF'].max() if 'JIF' in df_filtrado.columns and not df_filtrado['JIF'].isna().all() else 0.0
    st.metric("Maior Fator JIF", f"{maior_jif:.2f}" if pd.notna(maior_jif) else "0.00")
with col4:
    maior_sjr = df_filtrado['SJR'].max() if 'SJR' in df_filtrado.columns and not df_filtrado['SJR'].isna().all() else 0.0
    st.metric("Maior Score SJR", f"{maior_sjr:.3f}" if pd.notna(maior_sjr) else "0.000")


st.markdown("### 📋 Periódicos Encontrados")

# SISTEMA DE PAGINAÇÃO (Exibe de 50 em 50 linhas para garantir performance instantânea)
itens_por_pagina = 50
total_itens = len(df_filtrado)

if total_itens > 0:
    total_paginas = (total_itens // itens_por_pagina) + (1 if total_itens % itens_por_pagina > 0 else 0)
    pagina_atual = st.number_input(f"Páginas disponíveis (1 a {total_paginas}):", min_value=1, max_value=max(1, total_paginas), value=1)
    
    inicio = (pagina_atual - 1) * itens_por_pagina
    fim = inicio + itens_por_pagina
    
    # Exibe a tabela interativa do Streamlit estilizada
    st.dataframe(
        df_filtrado.iloc[inicio:fim], 
        use_container_width=True,
        hide_index=True
    )
    
    # Recurso Extra: Download da seleção customizada do pesquisador
    csv_download = df_filtrado.to_csv(index=False, sep=';', encoding='utf-8-sig')
    st.download_button(
        label="📥 Baixar lista filtrada atual (CSV)",
        data=csv_download,
        file_name="revistas_selecionadas.csv",
        mime="text/csv"
    )
else:
    st.warning("⚠️ Nenhuma revista atende a todos os critérios de filtros selecionados simultaneamente. Tente flexibilizar os filtros na barra lateral.")