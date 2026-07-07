import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Portal de Periódicos Científicos",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed" # Começa recolhido para focar no design do portal
)

# Estilização CSS customizada para emular um site premium
st.markdown("""
    <style>
    /* Estilo do bloco do cabeçalho principal (Hero Section) */
    .hero-container {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        padding: 40px 30px;
        border-radius: 12px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .hero-title {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: white !important;
        margin-bottom: 8px;
    }
    .hero-subtitle {
        font-size: 1.1rem !important;
        color: #E2E8F0 !important;
    }
    
    /* Customização dos Cards de Métricas */
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 20px 25px !important;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.95rem !important;
        color: #64748B !important;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        color: #1E3A8A !important;
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO DOS DADOS (Com Cache)
@st.cache_data
def carregar_dados():
    df = pd.read_csv("dados_revistas.csv", sep=";", encoding="utf-8-sig", low_memory=False)
    col_titulo = df.columns[0]
    df = df.drop_duplicates(subset=[col_titulo])
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.columns = [c.strip() for c in df.columns]
    
    for col in ['SJR', 'JIF', 'h-index', 'H index']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').astype(float, errors='ignore')
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

try:
    df_original = carregar_dados()
except Exception as e:
    st.error(f"⚠️ Erro ao carregar a base de dados. Detalhes: {e}")
    st.stop()

# --- 3. CABEÇALHO HERO (Visual de Site) ---
st.markdown("""
    <div class="hero-container">
        <h1 class="hero-title">🔬 SciIndex · Portal de Inteligência Periódica</h1>
        <p class="hero-subtitle">Descubra, avalie e filtre as melhores opções de revistas científicas nacionais e internacionais para a submissão dos seus manuscritos.</p>
    </div>
""", unsafe_allow_html=True)


# --- 4. PAINEL CENTRAL DE FILTROS (Formato de Motor de Busca Avançado) ---
st.markdown("### 🔍 Motor de Busca Avançado")

# Input unificado proeminente (estilo caixa de pesquisa do Google Acadêmico)
busca = st.text_input("Digite o termo de busca (Ex: Nome da Revista, Palavra-chave ou ISSN):", placeholder="Ex: Revista de Direito Administrativo, 1516-3210, Nature...")

# Divisão de filtros avançados por abas elegantes no meio da página
aba_escopo, aba_impacto = st.tabs(["📌 Classificação e Áreas", "📈 Métricas de Impacto"])

with aba_escopo:
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        # Filtro Grande Área CNPq
        col_cnpq1 = [c for c in df_original.columns if 'cnpq 1' in c.lower() or 'cnpq1' in c.lower()][0]
        col_cnpq2 = [c for c in df_original.columns if 'cnpq 2' in c.lower() or 'cnpq2' in c.lower()][0]
        todas_areas_cnpq = set(df_original[col_cnpq1].dropna().unique()).union(set(df_original[col_cnpq2].dropna().unique()))
        lista_cnpq = sorted([str(x).strip() for x in todas_areas_cnpq if str(x).strip() != ""])
        cnpq_selecionado = st.selectbox("Grande Área CNPq (Fomento Nacional):", ["Todas"] + lista_cnpq)
        
    with col_f2:
        # Filtro Área do Conhecimento Específica
        col_area_especifica = "Área do Conhecimento" if "Área do Conhecimento" in df_original.columns else [c for c in df_original.columns if 'conhecimento' in c.lower()][0]
        todas_areas_especificas = set()
        for x in df_original[col_area_especifica].dropna():
            for area in str(x).split(","):
                todas_areas_especificas.add(area.strip())
        lista_areas_especificas = sorted(list(todas_areas_especificas))
        area_especifica_sel = st.selectbox("Área de Especialidade (Internacional):", ["Todas"] + lista_areas_especificas)
        
    with col_f3:
        # Filtro de Indexadores combinados
        col_indexador = "Indexador" if "Indexador" in df_original.columns else None
        if col_indexador:
            # Captura indexadores isolados mesmo que concatenados por vírgula
            set_indexadores = set()
            for x in df_original[col_indexador].dropna():
                for idx in str(x).split(","):
                    set_indexadores.add(idx.strip())
            indexadores_disponiveis = sorted(list(set_indexadores))
            indexador_sel = st.multiselect("Bases Indexadoras:", indexadores_disponiveis, default=indexadores_disponiveis)
        else:
            indexador_sel = []

with aba_impacto:
    col_f4, col_f5, col_f6 = st.columns(3)
    
    with col_f4:
        # Quartil JCR
        col_q_jcr = "Quartil JCR" if "Quartil JCR" in df_original.columns else None
        if col_q_jcr:
            q_jcr_disponiveis = sorted([str(x).strip() for x in df_original[col_q_jcr].dropna().unique() if str(x).strip() != ""])
            q_jcr_sel = st.multiselect("Quartil JCR (Clarivate/WoS):", q_jcr_disponiveis, default=q_jcr_disponiveis)
        else:
            q_jcr_sel = []
            
    with col_f5:
        # Quartil SJR
        col_q_sjr = "SJR Best Quartile" if "SJR Best Quartile" in df_original.columns else None
        if col_q_sjr:
            q_sjr_disponiveis = sorted([str(x).strip() for x in df_original[col_q_sjr].dropna().unique() if str(x).strip() != ""])
            q_sjr_sel = st.multiselect("Quartil SJR (Scopus):", q_sjr_disponiveis, default=q_sjr_disponiveis)
        else:
            q_sjr_sel = []
            
    with col_f6:
        # Critério de Ordenação
        opcoes_ordenacao = ["Título"]
        if "SJR" in df_original.columns: opcoes_ordenacao.append("SJR (Prestígio)")
        if "JIF" in df_original.columns: opcoes_ordenacao.append("JIF (Fator de Impacto)")
        if "H index" in df_original.columns: opcoes_ordenacao.append("H-Index (Histórico)")
        criterio_ordem = st.selectbox("Ordenar Catálogo por:", options=opcoes_ordenacao)

st.markdown("---")

# --- 5. EXECUÇÃO LOGÍCA DA FILTRAGEM ---
df_filtrado = df_original.copy()

if busca:
    col_titulo = df_filtrado.columns[0]
    col_issn = "ISSN" if "ISSN" in df_filtrado.columns else [c for c in df_filtrado.columns if 'issn' in c.lower()][0]
    df_filtrado = df_filtrado[
        df_filtrado[col_titulo].str.contains(busca, case=False, na=False) |
        df_filtrado[col_issn].str.contains(busca, case=False, na=False)
    ]

if cnpq_selecionado != "Todas" and col_cnpq1 and col_cnpq2:
    df_filtrado = df_filtrado[(df_filtrado[col_cnpq1] == cnpq_selecionado) | (df_filtrado[col_cnpq2] == cnpq_selecionado)]

if area_especifica_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado[col_area_especifica].str.contains(area_especifica_sel, case=False, na=False)]

if col_indexador and indexador_sel:
    # Filtra se houver intersecção (a célula contém qualquer um dos selecionados)
    padrao_regex = "|".join(indexador_sel)
    df_filtrado = df_filtrado[df_filtrado[col_indexador].astype(str).str.contains(padrao_regex, na=False)]

if col_q_jcr and q_jcr_sel:
    df_filtrado = df_filtrado[df_filtrado[col_q_jcr].astype(str).str.strip().isin(q_jcr_sel)]

if col_q_sjr and q_sjr_sel:
    df_filtrado = df_filtrado[df_filtrado[col_q_sjr].astype(str).str.strip().isin(q_sjr_sel)]

mapa_ordem = {
    "SJR (Prestígio)": ("SJR", False),
    "JIF (Fator de Impacto)": ("JIF", False),
    "H-Index (Histórico)": ("H index" if "H index" in df_filtrado.columns else "h-index", False),
    "Título": (df_filtrado.columns[0], True)
}
col_ordenar, ascendente = mapa_ordem[criterio_ordem]
if col_ordenar in df_filtrado.columns:
    df_filtrado = df_filtrado.sort_values(by=col_ordenar, ascending=ascendente)


# --- 6. METRICAS DO PORTAL (Cards com CSS aplicado) ---
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric("Periódicos Catalogados", f"{len(df_filtrado):,}".replace(",", "."))
with col_m2:
    col_h = "H index" if "H index" in df_filtrado.columns else "h-index"
    maior_h = int(df_filtrado[col_h].max()) if col_h in df_filtrado.columns and not df_filtrado[col_h].isna().all() else 0
    st.metric("H-Index Máximo", maior_h)
with col_m3:
    maior_jif = df_filtrado['JIF'].max() if 'JIF' in df_filtrado.columns and not df_filtrado['JIF'].isna().all() else 0.0
    st.metric("Fator JIF Ápice", f"{maior_jif:.2f}" if pd.notna(maior_jif) else "0.00")
with col_m4:
    maior_sjr = df_filtrado['SJR'].max() if 'SJR' in df_filtrado.columns and not df_filtrado['SJR'].isna().all() else 0.0
    st.metric("Score SJR de Elite", f"{maior_sjr:.3f}" if pd.notna(maior_sjr) else "0.000")

st.markdown("<br>", unsafe_allow_html=True)


# --- 7. EXIBIÇÃO DE RESULTADOS ---
st.markdown("### 📋 Catálogo Eletrônico de Resultados")

itens_por_pagina = 40
total_itens = len(df_filtrado)

if total_itens > 0:
    total_paginas = (total_itens // itens_por_pagina) + (1 if total_itens % itens_por_pagina > 0 else 0)
    
    col_pag1, col_pag2 = st.columns([1, 4])
    with col_pag1:
        pagina_atual = st.number_input(f"Página (1 a {total_paginas}):", min_value=1, max_value=max(1, total_paginas), value=1)
    
    inicio = (pagina_atual - 1) * itens_por_pagina
    fim = inicio + itens_por_pagina
    
    # Renderiza a tabela limpa
    st.dataframe(
        df_filtrado.iloc[inicio:fim], 
        use_container_width=True,
        hide_index=True
    )
    
    # Botão de exportação institucional
    csv_download = df_filtrado.to_csv(index=False, sep=';', encoding='utf-8-sig')
    st.download_button(
        label="📥 Exportar Relatório Customizado (CSV)",
        data=csv_download,
        file_name="relatorio_periodicos.csv",
        mime="text/csv"
    )
else:
    st.warning("⚠️ Nenhum registro localizado. Refine os parâmetros ou termos digitados no motor de busca.")