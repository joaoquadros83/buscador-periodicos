import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO PREMIUM DA PÁGINA
st.set_page_config(
    page_title="SciIndex | Portal de Inteligência Científica",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. INJEÇÃO DE CSS AVANÇADO (Menu Claro em Contraste com Elementos Escuros)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* --- CUSTOMIZAÇÃO RADICAL DA BARRA LATERAL (MENU CLARO) --- */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
        box-shadow: 4px 0 10px -5px rgba(0, 0, 0, 0.03) !important;
    }
    
    /* Ajuste de cor dos textos e labels dentro do menu lateral */
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #334155 !important;
    }
    
    /* Estilização elegante dos Radio Buttons do menu para combinar com o fundo claro */
    div[data-testid="stSidebar"] div[role="radiogroup"] label {
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        padding: 12px 16px !important;
        border-radius: 10px !important;
        margin-bottom: 8px !important;
        transition: all 0.2s ease;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background-color: #F1F5F9 !important;
        border-color: #CBD5E1 !important;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
        background-color: #0F172A !important;  /* Destaque escuro no item selecionado */
        border-color: #0F172A !important;
    }
    div[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] span {
        color: #FFFFFF !important; /* Texto branco no item ativo */
    }

    /* --- ESTILIZAÇÃO DO CONTEÚDO PRINCIPAL (DASHBOARD) --- */
    .premium-hero {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        padding: 50px 40px;
        border-radius: 16px;
        color: #F8FAFC;
        margin-bottom: 35px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.1), 0 8px 10px -6px rgba(15, 23, 42, 0.1);
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
        max-width: 800px;
        line-height: 1.6;
    }
    
    /* Cards de Métricas */
    div[data-testid="stMetric"] {
        background: #FFFFFF !important;
        padding: 24px 28px !important;
        border-radius: 14px !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 20px -3px rgba(0, 0, 0, 0.04) !important;
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
    </style>
""", unsafe_allow_html=True)

# 3. BASE DE DADOS COM CACHE
@st.cache_data
def carregar_dados():
    df = pd.read_csv("dados_revistas.csv", sep=";", encoding="utf-8-sig", low_memory=False)
    df = df.drop_duplicates(subset=[df.columns[0]])
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

# --- 4. ESTRUTURA DO MENU LATERAL (AGORA CLARO) ---
st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.sidebar.markdown("""
    <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 25px;'>
        <span style='font-size: 1.8rem;'>💎</span>
        <h2 style='margin: 0; font-size: 1.35rem; font-weight: 700; color: #0F172A;'>SciIndex Hub</h2>
    </div>
""", unsafe_allow_html=True)

menu_selecionado = st.sidebar.radio(
    label="Menu de Navegação",
    options=[
        "🔍 Indexador Dinâmico",
        "📄 Inteligência de Escrita",
        "🌐 Ecossistema & Mídia",
        "📅 Simpósios e Eventos"
    ],
    label_visibility="collapsed"
)

st.sidebar.markdown("<br><br><hr style='border: 0; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
st.sidebar.markdown("""
    <div style='color: #64748B; font-size: 0.8rem; padding-left: 5px; line-height: 1.5;'>
        <span style='color: #10B981;'>●</span> <b>Sistema:</b> Operacional<br>
        <b>Versão Base:</b> 2026.1<br>
        <b>Padrão CNPq:</b> Ativo
    </div>
""", unsafe_allow_html=True)


# ==============================================================================
# SEÇÃO 1: INDEXADOR DINÂMICO DE REVISTAS
# ==============================================================================
if menu_selecionado == "🔍 Indexador Dinâmico":
    
    st.markdown("""
        <div class="premium-hero">
            <h1 class="premium-title">Portal de Inteligência Periódica</h1>
            <p class="premium-subtitle">Cruze indexadores internacionais com as grandes áreas de fomento do CNPq para descobrir o periódico estratégico ideal para o seu manuscrito.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("#### 🛠️ Filtros Inteligentes de Pesquisa")
    busca = st.text_input("Buscar registro específico:", placeholder="Digite uma palavra-chave do título da revista, ISSN ou assunto...")

    aba_escopo, aba_impacto = st.tabs(["📂 Escopo Acadêmico & CNPq", "📈 Métricas de Performance & Quartis"])

    with aba_escopo:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            col_cnpq1 = [c for c in df_original.columns if 'cnpq 1' in c.lower() or 'cnpq1' in c.lower()][0]
            col_cnpq2 = [c for c in df_original.columns if 'cnpq 2' in c.lower() or 'cnpq2' in c.lower()][0]
            todas_areas_cnpq = set(df_original[col_cnpq1].dropna().unique()).union(set(df_original[col_cnpq2].dropna().unique()))
            lista_cnpq = sorted([str(x).strip() for x in todas_areas_cnpq if str(x).strip() != ""])
            cnpq_selecionado = st.selectbox("Grande Área CNPq (Brasil):", ["Todas"] + lista_cnpq)
        
        with col_f2:
            col_area_especifica = "Área do Conhecimento" if "Área do Conhecimento" in df_original.columns else [c for c in df_original.columns if 'conhecimento' in c.lower()][0]
            todas_areas_especificas = set()
            for x in df_original[col_area_especifica].dropna():
                for area in str(x).split(","): todas_areas_especificas.add(area.strip())
            area_especifica_sel = st.selectbox("Área de Especialidade (Internacional):", ["Todas"] + sorted(list(todas_areas_especificas)))
        
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
            q_sjr_sel = st.multiselect("Quartil SJR (Scopus):", sorted([str(x).strip() for x in df_original[col_q_sjr].dropna().unique()]), default=sorted([str(x).strip() for x in df_original[col_q_sjr].dropna().unique()])) if col_q_sjr