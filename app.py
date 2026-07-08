import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO PREMIUM DA PÁGINA
st.set_page_config(
    page_title="SciIndex | Portal do Pesquisador",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. INJEÇÃO DE CSS AVANÇADO (Design de Alto Padrão e Ajuste de Botões)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif !important;
    }
    
  /* --- CUSTOMIZAÇÃO EXCLUSIVA DOS BOTÕES DA BARRA LATERAL ESQUERDA --- */
    
    /* 1. Item Ativo (Indexador Dinâmico) - Fundo Vermelho e Fonte Branca */
    div[data-testid="stSidebar"] [data-testid="stCheckbox"] {
        background-color: #A91D22 !important;  /* Tom avermelhado Dialnet */
        padding: 10px 14px !important;
        border: 1px solid #A91D22 !important;
        border-radius: 6px !important;
        margin-bottom: 8px !important;
    }

/* --- BARRA LATERAL ESQUERDA (CORREÇÃO DE CONTRASTE DOS BOTÕES) --- */
    [data-testid="stSidebar"] {
        background-color: #FAF9F6 !important;
        border-right: 1px solid #EAE8E4 !important;
        box-shadow: none !important;
    }
    
    /* 1. TEXTOS INFORMATIVOS (Fora dos botões: Títulos, Labels e Rodapé) */
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] b,
    [data-testid="stSidebar"] i {
        color: #0F172A !important; /* Mesma cor do Painel de Navegação */
    }
    
    /* 2. ITEM ATIVO (Indexador Dinâmico) - Fundo Vermelho e Texto Branco */
    div[data-testid="stSidebar"] [data-testid="stCheckbox"] {
        background-color: #A91D22 !important;
        padding: 10px 14px !important;
        border: 1px solid #A91D22 !important;
        border-radius: 6px !important;
        margin-bottom: 8px !important;
    }
    /* Força fonte branca em qualquer elemento de texto dentro do Indexador */
    div[data-testid="stSidebar"] [data-testid="stCheckbox"] p,
    div[data-testid="stSidebar"] [data-testid="stCheckbox"] span,
    div[data-testid="stSidebar"] [data-testid="stCheckbox"] label {
        color: #FFFFFF !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }

    /* 3. LINKS DE INTERESSE (Botões Escuros) - Fundo Azul e TEXTO BRANCO OBRIGATÓRIO */
    div[data-testid="stSidebar"] [data-testid="stLinkButton"] a {
        background-color: #004B87 !important;  /* Fundo Escuro */
        border: 1px solid #004B87 !important;
        border-radius: 6px !important;
        padding: 10px 14px !important;
        margin-bottom: 8px !important;
        text-align: left !important;
	color: #FFFFFF !important;
        display: flex !important;
        align-items: center !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        text-decoration: none !important;
    }
    
    /* Seletor ultra-específico para anular a cor escura e forçar BRANCO nas letras internas dos links */
    div[data-testid="stSidebar"] [data-testid="stLinkButton"] a,
    div[data-testid="stSidebar"] [data-testid="stLinkButton"] a p,
    div[data-testid="stSidebar"] [data-testid="stLinkButton"] a span {
        color: #FFFFFF !important;              /* TEXTO BRANCO GARANTIDO */
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }
    
    /* 4. COMPORTAMENTO HOVER (Passar o Mouse) - Muda para Vermelho e MANTÉM TEXTO BRANCO */
    div[data-testid="stSidebar"] [data-testid="stLinkButton"] a:hover {
        background-color: #A91D22 !important;  /* Vermelho Dialnet */
        border-color: #A91D22 !important;
        box-shadow: 0 4px 8px rgba(169, 29, 34, 0.2) !important;
	onmouseover="this.style.backgroundColor='#FF2B2B'; this.style.borderColor='#FF2B2B';" 
	onmouseout="this.style.backgroundColor='#004B87'; this.style.borderColor='#004B87';"
    }
    /* Mantém as letras brancas durante o hover */
    div[data-testid="stSidebar"] [data-testid="stLinkButton"] a:hover p,
    div[data-testid="stSidebar"] [data-testid="stLinkButton"] a:hover span {
        color: #FFFFFF !important;              /* CONTINUA BRANCO */
    }

    /* --- ESTILIZAÇÃO DO CONTEÚDO PRINCIPAL (DASHBOARD) --- */
    .premium-hero {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        padding: 50px 40px;
        border-radius: 16px;
        color: #F8FAFC;
        margin-bottom: 35px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .premium-title {
        font-size: 2.6rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.04em;
        color: #FFFFFF !important;
        margin-bottom: 10px;
    }
    .premium-subtitle {
        font-size: 1.15rem !important;
        color: #94A3B8 !important;
        font-weight: 400;
        line-height: 1.6;
    }
    
    /* Cards de Métricas */
    div[data-testid="stMetric"] {
        background: #FFFFFF !important;
        padding: 24px 28px !important;
        border-radius: 14px !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02) !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: #64748B !important;
        font-weight: 600 !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        color: #0F172A !important;
        font-weight: 700 !important;
    }
    
    /* Inputs, Selectboxes e Tabs */
    .stTextInput input { border-radius: 10px !important; padding: 12px 16px !important; border: 1px solid #CBD5E1 !important; }
    .stSelectbox div[data-baseweb="select"] { border-radius: 10px !important; }
    button[data-baseweb="tab"] { font-size: 1rem !important; font-weight: 500 !important; color: #64748B; padding: 12px 20px !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #0F172A !important; border-bottom-color: #0F172A !important; }
    
    /* Botão de download customizado */
    div[data-testid="stDownloadButton"] button {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. BASE DE DADOS COM CACHE (Ajustada com substituição de None por '-')
@st.cache_data
def carregar_dados():
    # Lendo com separador de vírgula padrão e ignorando falhas de quebra de linha
    df = pd.read_csv("dados_revistas.csv", sep=",", encoding="utf-8-sig", low_memory=False, on_bad_lines='skip')
    df = df.drop_duplicates(subset=[df.columns[0]])
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.columns = [c.strip() for c in df.columns]
    
    # Tratamento de dados numéricos para as métricas
    for col in ['SJR', 'JIF', 'h-index', 'H index']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').astype(float, errors='ignore')
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # --- SUBSTITUIÇÃO GLOBAL DE 'NONE' E VALORES VAZIOS POR '-' ---
    # 1. Substitui valores nulos (NaN/NaT) pelo traço
    df = df.fillna("-")
    
    # 2. Varre todas as colunas limpando textos como "None", "none" ou espaços vazios
    for col in df.columns:
        df[col] = df[col].apply(lambda x: "-" if str(x).strip().lower() in ["none", "nan", "", "null"] else x)
        
    return df

try:
    df_original = carregar_dados()
except Exception as e:
    st.error(f"⚠️ Erro ao carregar a base de dados. Detalhes: {e}")
    st.stop()

# --- 4. ESTRUTURA DO MENU LATERAL ORGANIZADA EM BLOCOS TEMÁTICOS ---
st.sidebar.markdown("<br>", unsafe_allow_html=True)

# CABEÇALHO DO MENU
st.sidebar.markdown("""
    <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 20px;'>
        <span style='font-size: 1.8rem;'></span>
        <h2 style='margin: 0; font-size: 1.60rem; font-weight: 700; color: #0F172A;'>Painel de Navegação</h2>
    </div>
""", unsafe_allow_html=True)

# --- ESTILO GLOBAL DOS BOTÕES ---
st.sidebar.markdown("""
<style>
    .btn-custom-menu {
        background-color: #E2E8F0 !important;
        border: 1px solid #004B87 !important;
        border-radius: 6px !important;
        padding: 10px 14px !important;
        margin-bottom: 8px !important;
        text-align: left !important;
        display: flex !important;
        align-items: center !important;
        text-decoration: none !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
    }
    .btn-custom-menu span {
        color: #FFFFFF !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }
    .btn-custom-menu:hover {
        background-color: #FF2B2B !important;
        border-color: #FF2B2B !important;
        box-shadow: 0 4px 8px rgba(255, 43, 43, 0.25) !important;
        transform: translateY(-1px) !important;
    }
</style>
""", unsafe_allow_html=True)

# BLOCO 1: INDEXADORES
st.sidebar.markdown("""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px; letter-spacing: 0.05em;'>INDEXADORES</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://www.webofknowledge.com" target="_blank"><span>🌐 Web of Science</span></a>
    <a class="btn-custom-menu" href="https://www.scopus.com" target="_blank"><span>🧬 Scopus</span></a>
    <a class="btn-custom-menu" href="https://pubmed.ncbi.nlm.nih.gov/" target="_blank"><span>🏥 PubMed</span></a>
    <a class="btn-custom-menu" href="https://www.scielo.br/" target="_blank"><span>📚 Scielo BR</span></a>
</div>
""", unsafe_allow_html=True)

# BLOCO 2: IA ACADÊMICA
st.sidebar.markdown("""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px; letter-spacing: 0.05em;'>IA PARA USO ACADÊMICO</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://www.perplexity.ai/" target="_blank"><span>🤖 Perplexity AI</span></a>
    <a class="btn-custom-menu" href="https://scispace.com/" target="_blank"><span>🚀 SciSpace</span></a>
    <a class="btn-custom-menu" href="https://elicit.com/" target="_blank"><span>🔍 Elicit</span></a>
</div>
""", unsafe_allow_html=True)

# RODAPÉ
st.sidebar.markdown("<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>", unsafe_allow_html=True)
st.sidebar.markdown("""
    <div style='color: #0F172A; font-size: 0.8rem; padding-left: 5px; line-height: 1.6;'>
        © 2026 <b>João F. Soares-Quadros Jr.</b><br>UFOP | Todos os direitos reservados.
    </div>
""", unsafe_allow_html=True)

# ==============================================================================
# PAINEL PRINCIPAL
# ==============================================================================
st.markdown("""
    <div class="premium-hero">
        <h1 class="premium-title">Portal do Pesquisador</h1>
        <p class="premium-subtitle">Cruze indexadores internacionais com as grandes áreas de fomento do CNPq para descobrir o periódico estratégico ideal.</p>
    </div>
""", unsafe_allow_html=True)

st.markdown("#### 🛠️ Filtros Inteligentes de Pesquisa")
busca = st.text_input("Buscar registro específico:", placeholder="Digite o título da revista, ISSN...")

aba_escopo, aba_impacto = st.tabs(["📂 Escopo Acadêmico & CNPq", "📈 Métricas de Performance & Quartis"])

with aba_escopo:
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        # Corrigido para mapear a coluna 'Grande Area' real do seu arquivo
        col_grande_area = "Grande Area" if "Grande Area" in df_original.columns else df_original.columns[3]
        lista_grande_area = sorted([str(x).strip() for x in df_original[col_grande_area].dropna().unique() if str(x).strip() != ""])
        grande_area_sel = st.selectbox("Grande Área CNPq (Brasil):", ["Todas"] + lista_grande_area)
    
    with col_f2:
        # Corrigido para mapear a coluna 'Area do Conhecimento' real do seu arquivo
        col_area = "Area do Conhecimento" if "Area do Conhecimento" in df_original.columns else df_original.columns[4]
        lista_areas = sorted([str(x).strip() for x in df_original[col_area].dropna().unique() if str(x).strip() != ""])
        area_sel = st.selectbox("Área do Conhecimento (1º Nível):", ["Todas"] + lista_areas)
    
    with col_f3:
        col_indexador = "Indexador" if "Indexador" in df_original.columns else None
        if col_indexador:
            set_indexadores = set()
            for x in df_original[col_indexador].dropna():
                for idx in str(x).split(","): set_indexadores.add(idx.strip())
            indexador_sel = st.multiselect("Bases Detentoras:", sorted(list(set_indexadores)), default=sorted(list(set_indexadores)))
        else: indexador_sel = []

with aba_impacto:
    col_f4, col_f5, col_f6 = st.columns(3)
    with col_f4:
        col_q_jcr = "Quartil JCR" if "Quartil JCR" in df_original.columns else None
        q_jcr_sel = st.multiselect("Quartil JCR (Clarivate):", sorted([str(x).strip() for x in df_original[col_q_jcr].dropna().unique()]), default=sorted([str(x).strip() for x in df_original[col_q_jcr].dropna().unique()])) if col_q_jcr else []
    with col_f5:
        col_q_sjr = "SJR Best Quartile" if "SJR Best Quartile" in df_original.columns else None
        q_sjr_sel = st.multiselect("Quartil SJR (Scopus):", sorted([str(x).strip() for x in df_original[col_q_sjr].dropna().unique()]), default=sorted([str(x).strip() for x in df_original[col_q_sjr].dropna().unique()])) if col_q_sjr else []
    with col_f6:
        opcoes_ordenacao = ["Título"]
        if "SJR" in df_original.columns: opcoes_ordenacao.append("SJR (Prestígio)")
        if "JIF" in df_original.columns: opcoes_ordenacao.append("JIF (Fator de Impacto)")
        criterio_ordem = st.selectbox("Ordenar Resultados por:", options=opcoes_ordenacao)

# Lógica de Filtros aplicados sequencialmente
df_filtrado = df_original.copy()

if busca:
    df_filtrado = df_filtrado[df_filtrado[df_filtrado.columns[0]].str.contains(busca, case=False, na=False) | df_filtrado["ISSN"].str.contains(busca, case=False, na=False)]
if grande_area_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado[col_grande_area] == grande_area_sel]
if area_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado[col_area] == area_sel]
if col_indexador and indexador_sel:
    df_filtrado = df_filtrado[df_filtrado[col_indexador].astype(str).str.contains("|".join(indexador_sel), na=False)]
if col_q_jcr and q_jcr_sel:
    df_filtrado = df_filtrado[df_filtrado[col_q_jcr].astype(str).str.strip().isin(q_jcr_sel)]
if col_q_sjr and q_sjr_sel:
    df_filtrado = df_filtrado[df_filtrado[col_q_sjr].astype(str).str.strip().isin(q_sjr_sel)]

mapa_ordem = {"SJR (Prestígio)": ("SJR", False), "JIF (Fator de Impacto)": ("JIF", False), "Título": (df_filtrado.columns[0], True)}
col_ordenar, ascendente = mapa_ordem[criterio_ordem]
if col_ordenar in df_filtrado.columns: 
    df_filtrado = df_filtrado.sort_values(by=col_ordenar, ascending=ascendente)

# Painel de Métricas Dinâmicas
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1: st.metric("Revistas Selecionadas", f"{len(df_filtrado):,}".replace(",", "."))
with col_m2: st.metric("H-Index Topo", int(df_filtrado["H index"].max()) if "H index" in df_filtrado.columns and pd.notna(df_filtrado["H index"].max()) else 0)
with col_m3: st.metric("Fator JIF Máximo", f"{df_filtrado['JIF'].max():.2f}" if 'JIF' in df_filtrado.columns and pd.notna(df_filtrado['JIF'].max()) else "0.00")
with col_m4: st.metric("SJR Score Ápice", f"{df_filtrado['SJR'].max():.3f}" if 'SJR' in df_filtrado.columns and pd.notna(df_filtrado['SJR'].max()) else "0.000")

st.markdown("<br>", unsafe_allow_html=True)

# Exibição do Catálogo Paginado
st.markdown("#### 📋 Catálogo de Periódicos")
total_itens = len(df_filtrado)
if total_itens > 0:
    col_pag1, col_pag2, _ = st.columns([1.5, 2, 5])
    with col_pag1:
        itens_por_pagina = st.selectbox("Exibir por página:", options=[20, 50, 100], index=1)
        
    total_paginas = (total_itens // itens_por_pagina) + (1 if total_itens % itens_por_pagina > 0 else 0)
    with col_pag2:
        pagina_atual = st.number_input(f"Página (1 de {total_paginas}):", min_value=1, max_value=max(1, total_paginas), value=1)
    
    inicio = (pagina_atual - 1) * itens_por_pagina
    fim = inicio + itens_por_pagina
    df_da_pagina = df_filtrado.iloc[inicio:fim]
    
    st.dataframe(df_da_pagina, use_container_width=True, hide_index=True)
    
    csv_pagina = df_da_pagina.to_csv(index=False, sep=';', encoding='utf-8-sig')
    st.download_button(label=f"📥 Exportar apenas esta página ({len(df_da_pagina)} itens)", data=csv_pagina, file_name="sciindex_pagina_atual.csv", mime="text/csv")
else:
    st.warning("Nenhum periódico atende aos critérios aplicados.")