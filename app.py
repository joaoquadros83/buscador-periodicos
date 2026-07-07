import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página (Aparência profissional em modo amplo)
st.set_page_config(
    page_title="Portal de Periódicos Científicos",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Função com Cache para carregar os dados uma única vez e economizar memória
@st.cache_data
def carregar_dados():
    # Carrega o arquivo traduzido que você gerou
    df = pd.read_csv("dados_revistas.csv", sep=";", encoding="utf-8-sig", low_memory=False)
    
    # Remove duplicatas residuais pelo Título da Revista (Coluna 1) por segurança
    col_titulo = df.columns[0]
    df = df.drop_duplicates(subset=[col_titulo])
    
    # Remove colunas ocultas ou vazias geradas por delimitadores extras
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Garante que colunas numéricas sejam tratadas corretamente
    for col in ['SJR', 'JIF', 'h-index', 'H index']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').astype(float, errors='ignore')
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    return df

# Inicializa a base de dados
try:
    df_original = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar o arquivo 'dados_revistas.csv'. Verifique o nome e o separador. Erro: {e}")
    st.stop()

# --- BARRA LATERAL: FILTROS AVANÇADOS ---
st.sidebar.header("🔍 Filtros de Busca")

# 1. Filtro por Palavra-Chave (Título ou ISSN)
busca = st.sidebar.text_input("Buscar por Nome da Revista ou ISSN:")

# 2. Filtro por Área do Conhecimento
col_area = "Área do Conhecimento" if "Área do Conhecimento" in df_original.columns else df_original.columns[3]

# Extrai as áreas únicas tratando células que têm múltiplas áreas separadas por vírgula
todas_areas = set()
for x in df_original[col_area].dropna():
    for area in str(x).split(","):
        todas_areas.add(area.strip())
lista_areas = sorted(list(todas_areas))

area_selecionada = st.sidebar.selectbox("Selecione a Área:", ["Todas"] + lista_areas)

# 3. Filtros por Quartil (JCR ou SJR se disponíveis)
col_q = "Quartil JCR" if "Quartil JCR" in df_original.columns else ([c for c in df_original.columns if 'quartil' in c.lower()][0] if [c for c in df_original.columns if 'quartil' in c.lower()] else None)

if col_q:
    quartis_disponiveis = sorted([str(x).strip() for x in df_original[col_q].dropna().unique() if str(x).strip() != ""])
    quartil_sel = st.sidebar.multiselect(f"Filtrar por {col_q}:", quartis_disponiveis, default=quartis_disponiveis)
else:
    quartil_sel = []

# 4. Ordenação dos Resultados
opcoes_ordenacao = ["Título"]
if "SJR" in df_original.columns: opcoes_ordenacao.append("SJR (Prestígio)")
if "JIF" in df_original.columns: opcoes_ordenacao.append("JIF (Fator de Impacto JCR)")
if "h-index" in df_original.columns: opcoes_ordenacao.append("h-index (Impacto Histórico)")
if "H index" in df_original.columns: opcoes_ordenacao.append("H index (Impacto Histórico)")

criterio_ordem = st.sidebar.selectbox("Ordenar resultados por:", options=opcoes_ordenacao)

# --- CORPO PRINCIPAL DO APLICATIVO ---
st.title("📚 Localizador de Periódicos para Publicação Científica")
st.markdown("Plataforma profissional de busca e avaliação de indexadores acadêmicos.")
st.markdown("---")

# Aplicação dos filtros no DataFrame
df_filtrado = df_original.copy()

if busca:
    col_titulo = df_filtrado.columns[0]
    col_issn = "ISSN" if "ISSN" in df_filtrado.columns else [c for c in df_filtrado.columns if 'issn' in c.lower()][0]
    df_filtrado = df_filtrado[
        df_filtrado[col_titulo].str.contains(busca, case=False, na=False) |
        df_filtrado[col_issn].str.contains(busca, case=False, na=False)
    ]

if area_selecionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado[col_area].str.contains(area_selecionada, case=False, na=False)]

if col_q and quartil_sel:
    df_filtrado = df_filtrado[df_filtrado[col_q].astype(str).str.strip().isin(quartil_sel)]

# Aplicação da Ordenação
mapa_ordem = {
    "SJR (Prestígio)": ("SJR", False),
    "JIF (Fator de Impacto JCR)": ("JIF", False),
    "h-index (Impacto Histórico)": ("h-index", False),
    "H index (Impacto Histórico)": ("H index", False),
    "Título": (df_filtrado.columns[0], True)
}
col_ordenar, ascendente = mapa_ordem[criterio_ordem]
if col_ordenar in df_filtrado.columns:
    df_filtrado = df_filtrado.sort_values(by=col_ordenar, ascending=ascendente)

# --- MÉTRICAS DE DESTAQUE (CARDS) ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Revistas Encontradas", f"{len(df_filtrado):,}".replace(",", "."))
with col2:
    col_h = "h-index" if "h-index" in df_filtrado.columns else ("H index" if "H index" in df_filtrado.columns else None)
    maior_h = int(df_filtrado[col_h].max()) if col_h and not df_filtrado[col_h].isna().all() else 0
    st.metric("Maior Índice H da Seleção", maior_h)
with col3:
    maior_jif = df_filtrado['JIF'].max() if 'JIF' in df_filtrado.columns and not df_filtrado['JIF'].isna().all() else 0.0
    st.metric("Maior JIF (Impacto) da Seleção", f"{maior_jif:.2f}" if pd.notna(maior_jif) else "0.00")

st.markdown("### 📋 Resultados da Pesquisa")

# PAGINAÇÃO: Exibir 53 mil linhas de uma vez trava a tela. Vamos exibir de 50 em 50.
itens_por_pagina = 50
total_itens = len(df_filtrado)
if total_itens > 0:
    total_paginas = (total_itens // itens_por_pagina) + (1 if total_itens % itens_por_pagina > 0 else 0)
    pagina_atual = st.number_input(f"Página (1 de {total_paginas}):", min_value=1, max_value=max(1, total_paginas), value=1)
    
    inicio = (pagina_atual - 1) * itens_por_pagina
    fim = inicio + itens_por_pagina
    
    # Exibe a tabela elegante contendo apenas o bloco de páginas atual
    st.dataframe(
        df_filtrado.iloc[inicio:fim], 
        use_container_width=True,
        hide_index=True
    )
    
    # Botão para o pesquisador baixar a lista customizada que ele filtrou
    csv_download = df_filtrado.to_csv(index=False, sep=';', encoding='utf-8-sig')
    st.download_button(
        label="📥 Baixar esta lista filtrada em CSV",
        data=csv_download,
        file_name="revistas_filtradas.csv",
        mime="text/csv"
    )
else:
    st.warning("Nenhuma revista encontrada com as combinações de filtros selecionadas.")