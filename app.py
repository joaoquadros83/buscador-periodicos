import streamlit as str
import pandas as pd
import plotly.express as px

# Configuração da página (Aparência profissional em modo amplo)
str.set_page_config(
    page_title="Portal de Periódicos Científicos",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Função com Cache para carregar os dados uma única vez e economizar memória
@str.cache_data
def carregar_dados():
    # Carrega o arquivo unificado
    df = pd.read_csv("dados_revistas.csv", sep=";", encoding="utf-8-sig", low_memory=False)
    
    # Remove duplicatas residuais pelo Título da Revista (Coluna 1) por segurança
    col_titulo = df.columns[0]
    df = df.drop_duplicates(subset=[col_titulo])
    
    # Garante que colunas numéricas sejam tratadas corretamente (substituindo vírgula por ponto se necessário)
    for col in ['SJR', 'JIF', 'Citations / Doc. (2years)']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').astype(float, errors='ignore')
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    return df

# Inicializa a base de dados
try:
    df_original = carregar_dados()
except Exception as e:
    str.error(f"Erro ao carregar o arquivo 'dados_revistas.csv'. Verifique o nome e o separador. Erro: {e}")
    str.stop()

# --- BARRA LATERAL: FILTROS AVANÇADOS ---
str.sidebar.header("🔍 Filtros de Busca")

# 1. Filtro por Palavra-Chave (Título ou ISSN)
busca = str.sidebar.text_input("Buscar por Nome da Revista ou ISSN:")

# 2. Filtro por Área do Conhecimento
col_area = "Áreas do Conhecimento" if "Áreas do Conhecimento" in df_original.columns else df_original.columns[5]
# Extrai as áreas únicas tratando células que têm múltiplas áreas separadas por vírgula
todas_areas = set()
for x in df_original[col_area].dropna():
    for area in str(x).split(","):
        todas_areas.add(area.strip())
lista_areas = sorted(list(todas_areas))

area_selecionada = str.sidebar.selectbox("Selecione a Área:", ["Todas"] + lista_areas)

# 3. Filtros por Quartil
col_q_sjr = "SJR Best Quartile" if "SJR Best Quartile" in df_original.columns else "Quartil"
quartis_disponiveis = sorted(df_original[col_q_sjr].dropna().unique())
quartil_sjr_sel = str.sidebar.multiselect("Quartil SJR (Scopus):", quartis_disponiveis, default=quartis_disponiveis)

# 4. Ordenação dos Resultados
criterio_ordem = str.sidebar.selectbox(
    "Ordenar resultados por:",
    options=["SJR (Prestígio)", "H index (Impacto Histórico)", "JIF (Fator de Impacto JCR)", "Título"]
)

# --- CORPO PRINCIPAL DO APLICATIVO ---
str.title("📚 Localizador de Periódicos para Publicação Científica")
str.markdown("---")

# Aplicação dos filtros no DataFrame
df_filtrado = df_original.copy()

if busca:
    col_titulo = df_filtrado.columns[0]
    col_issn = [c for c in df_filtrado.columns if 'issn' in c.lower()][0]
    df_filtrado = df_filtrado[
        df_filtrado[col_titulo].str.contains(busca, case=False, na=False) |
        df_filtrado[col_issn].str.contains(busca, case=False, na=False)
    ]

if area_selecionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado[col_area].str.contains(area_selecionada, case=False, na=False)]

if quartil_sjr_sel:
    df_filtrado = df_filtrado[df_filtrado[col_q_sjr].isin(quartil_sjr_sel)]

# Aplicação da Ordenação
mapa_ordem = {
    "SJR (Prestígio)": ("SJR", False),
    "H index (Impacto Histórico)": ("H index", False),
    "JIF (Fator de Impacto JCR)": ("JIF", False),
    "Título": (df_filtrado.columns[0], True)
}
col_ordenar, ascendente = mapa_ordem[criterio_ordem]
if col_ordenar in df_filtrado.columns:
    df_filtrado = df_filtrado.sort_values(by=col_ordenar, ascending=ascendente)

# --- MÉTRICAS DE DESTAQUE (CARDS) ---
col1, col2, col3 = str.columns(3)
with col1:
    str.metric("Revistas Encontradas", f"{len(df_filtrado):,}".replace(",", "."))
with col2:
    maior_h = int(df_filtrado['H index'].max()) if 'H index' in df_filtrado.columns and not df_filtrado['H index'].isna().all() else 0
    str.metric("Maior Índice H da Seleção", maior_h)
with col3:
    total_q1 = len(df_filtrado[df_filtrado[col_q_sjr] == "Q1"])
    str.metric("Revistas de Elite (Q1)", total_q1)

str.markdown("### 📋 Resultados da Pesquisa")

# PAGINAÇÃO: Exibir 53 mil linhas de uma vez trava a tela. Vamos exibir de 50 em 50.
itens_por_pagina = 50
total_itens = len(df_filtrado)
if total_itens > 0:
    total_paginas = (total_itens // itens_por_pagina) + (1 if total_itens % itens_por_pagina > 0 else 0)
    pagina_atual = str.number_input(f"Página (1 de {total_paginas}):", min_value=1, max_value=max(1, total_paginas), value=1)
    
    inicio = (pagina_atual - 1) * itens_por_pagina
    fim = inicio + itens_por_pagina
    
    # Exibe a tabela elegante contendo apenas o bloco de páginas atual
    str.dataframe(
        df_filtrado.iloc[inicio:fim], 
        use_container_width=True,
        hide_index=True
    )
    
    # Botão para o pesquisador baixar a lista customizada que ele filtrou
    csv_download = df_filtrado.to_csv(index=False, sep=';', encoding='utf-8-sig')
    str.download_button(
        label="📥 Baixar esta lista filtrada em CSV",
        data=csv_download,
        file_name="revistas_filtradas.csv",
        mime="text/csv"
    )
else:
    str.warning("Nenhuma revista encontrada com as combinações de filtros selecionadas.")