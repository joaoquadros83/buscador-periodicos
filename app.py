import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO PREMIUM DA PÁGINA
st.set_page_config(
    page_title="Portal do Pesquisador v3.0",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SISTEMA DE TRADUÇÃO MULTILÍNGUE ---
if 'idioma' not in st.session_state:
    st.session_state.idioma = "Português"

# Seletor de idioma fixado no topo da barra lateral
st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.session_state.idioma = st.sidebar.selectbox(
    "🌐 Language / Idioma:",
    ["Português", "English", "Español"]
)

# Dicionário central de tradução
dic = {
    "Português": {
        "titulo": "Portal do Pesquisador",
        "subtitulo": "Cruze indexadores internacionais com as subáreas de fomento do CNPq para descobrir o periódico estratégico ideal.",
        "filtros_tit": "#### 🛠️ Filtros Inteligentes de Pesquisa",
        "placeholder_busca": "Digite o título da revista, ISSN...",
        "buscar_reg": "Buscar registro específico:",
        "aba_escopo": "📂 Escopo Acadêmico & CNPq",
        "aba_impacto": "📈 Métricas de Performance & Quartis",
        "subarea_lbl": "Subárea do Conhecimento (CNPq):",
        "base_lbl": "Bases Detentoras:",
        "jcr_lbl": "Quartil JCR (Clarivate):",
        "sjr_lbl": "Quartil SJR (Scopus):",
        "ordem_lbl": "Ordenar Resultados por:",
        "m_selecionadas": "Revistas Selecionadas",
        "m_hindex": "H-Index Topo",
        "m_jif": "Fator JIF Máximo",
        "m_sjr": "SJR Score Ápice",
        "cat_tit": "#### 📋 Catálogo de Periódicos",
        "exibir_pag": "Exibir por página:",
        "pag_lbl": "Página",
        "exportar_btn": "📥 Exportar apenas esta página",
        "aviso_nada": "Nenhum periódico atende aos critérios aplicados.",
        "nav_tit": "Painel de Navegação",
        "todas": "Todas"
    },
    "English": {
        "titulo": "Researcher's Portal",
        "subtitulo": "Cross-reference international indexers with CNPq funding subareas to discover the ideal strategic journal.",
        "filtros_tit": "#### 🛠️ Smart Search Filters",
        "placeholder_busca": "Enter journal title, ISSN...",
        "buscar_reg": "Search specific record:",
        "aba_escopo": "📂 Academic Scope & CNPq",
        "aba_impacto": "📈 Performance Metrics & Quartiles",
        "subarea_lbl": "Subarea of Knowledge (CNPq):",
        "base_lbl": "Holding Databases:",
        "jcr_lbl": "JCR Quartile (Clarivate):",
        "sjr_lbl": "SJR Quartile (Scopus):",
        "ordem_lbl": "Sort Results by:",
        "m_selecionadas": "Selected Journals",
        "m_hindex": "Top H-Index",
        "m_jif": "Max JIF Factor",
        "m_sjr": "Peak SJR Score",
        "cat_tit": "#### 📋 Journal Catalog",
        "exibir_pag": "Display per page:",
        "pag_lbl": "Page",
        "exportar_btn": "📥 Export this page only",
        "aviso_nada": "No journals match the applied criteria.",
        "nav_tit": "Navigation Panel",
        "todas": "All"
    },
    "Español": {
        "titulo": "Portal del Investigador",
        "subtitulo": "Cruce indexadores internacionales con las subáreas de fomento del CNPq para descubrir la revista estratégica ideal.",
        "filtros_tit": "#### 🛠️ Filtros de Búsqueda Inteligentes",
        "placeholder_busca": "Ingrese el título de la revista, ISSN...",
        "buscar_reg": "Buscar registro específico:",
        "aba_escopo": "📂 Alcance Académico y CNPq",
        "aba_impacto": "📈 Métricas de Rendimiento y Cuartiles",
        "subarea_lbl": "Subárea del Conocimiento (CNPq):",
        "base_lbl": "Bases de Datos Detentoras:",
        "jcr_lbl": "Cuartil JCR (Clarivate):",
        "sjr_lbl": "Cuartil SJR (Scopus):",
        "ordem_lbl": "Ordenar Resultados por:",
        "m_selecionadas": "Revistas Seleccionadas",
        "m_hindex": "H-Index Máximo",
        "m_jif": "Factor JIF Máximo",
        "m_sjr": "SJR Score Ápice",
        "cat_tit": "#### 📋 Catálogo de Revistas",
        "exibir_pag": "Mostrar por página:",
        "pag_lbl": "Página",
        "exportar_btn": "📥 Exportar solo esta página",
        "aviso_nada": "Ninguna revista coincide con los criterios aplicados.",
        "nav_tit": "Panel de Navegación",
        "todas": "Todas"
    }
}
t = dic[st.session_state.idioma]

# 2. DESIGN DO HERO DA PÁGINA (CSS CUSTOMIZADO)
st.markdown("""
<style>
    /* Força o fundo do menu lateral com a cor definida */
    [data-testid="stSidebar"] {
        background-color: #F8F0E3 !important;
    }   
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #004B87 !important;
    }
    .premium-hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 35px;
        border-radius: 12px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        margin-bottom: 25px;
        border-left: 6px solid #FF2B2B;
    }
    .premium-title {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif;
        font-size: 2.6rem !important;
        font-weight: 800 !important;
        margin-bottom: 8px !important;
        letter-spacing: -0.5px;
    }
    .premium-subtitle {
        color: #94a3b8 !important;
        font-size: 1.15rem !important;
        max-width: 800px;
        line-height: 1.5;
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
    
    .stTextInput input { border-radius: 10px !important; padding: 12px 16px !important; border: 1px solid #CBD5E1 !important; }
    .stSelectbox div[data-baseweb="select"] { border-radius: 10px !important; }
    button[data-baseweb="tab"] { font-size: 1rem !important; font-weight: 500 !important; color: #64748B; padding: 12px 20px !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #0F172A !important; border-bottom-color: #0F172A !important; }
    
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

# 3. BASE DE DADOS COM CACHE
@st.cache_data
def carregar_dados():
    df = pd.read_csv("dados_revistas.csv", sep=",", encoding="utf-8-sig", low_memory=False, on_bad_lines='skip')
    df = df.drop_duplicates(subset=[df.columns[0]])
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.columns = [c.strip() for c in df.columns]
    
    for col in ['SJR', 'JIF', 'h-index', 'H index']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    df = df.fillna("-")
    df = df.replace(["None", "none", "NONE", "nan", "NaN", "null", ""], "-")
    return df

try:
    df_original = carregar_dados()
except Exception as e:
    st.error(f"⚠️ Erro ao carregar a base de dados. Detalhes: {e}")
    st.stop()

# 4. ESTRUTURA DO MENU LATERAL
st.sidebar.markdown(f"""
    <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 20px;'>
        <h2 style='margin: 0; font-size: 1.60rem; font-weight: 700; color: #0F172A;'>{t['nav_tit']}</h2>
    </div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<style>
    .btn-custom-menu {
        background-color: #FFFFFF !important;
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
        color: #004B87 !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        font-family: 'Roboto', sans-serif !important;
    }
    .btn-custom-menu:hover {
        background-color: #FF2B2B !important;
        border-color: #FF2B2B !important;
        box-shadow: 0 4px 8px rgba(255, 43, 43, 0.25) !important;
        transform: translateY(-1px) !important;
    }
    .btn-custom-menu:hover span { color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px; letter-spacing: 0.05em;'>INDEXADORES / INDEXERS</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://access.clarivate.com/login?app=wos&alternative=true&goto=https:%2F%2Fwww.webofknowledge.com" target="_blank"><span>🌐 Web of Science</span></a>
    <a class="btn-custom-menu" href="https://www.scopus.com/pages/home?display=basic#basic" target="_blank"><span>🧬 Scopus</span></a>
    <a class="btn-custom-menu" href="https://pubmed.ncbi.nlm.nih.gov/" target="_blank"><span>🏥 PubMed</span></a>
    <a class="btn-custom-menu" href="https://www.scielo.br/" target="_blank"><span>📚 Scielo BR</span></a>
    <a class="btn-custom-menu" href="http://educa.fcc.org.br/cgi-bin/wxis.exe/iah/?IsisScript=iah/iah.xis&base=title&fmt=iso.pft&lang=p" target="_blank"><span>📖 Educ@</span></a>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px; letter-spacing: 0.05em;'>IA / AI ACADEMIC</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://www.scopus.com/pages/home#scopus-ai" target="_blank"><span><img src="https://images.icon-icons.com/2389/PNG/512/elsevier_logo_icon_145310.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;"><span>ScopusAI</span></a>
    <a class="btn-custom-menu" href="https://researcher.elsevier.com/" target="_blank"><span><img src="https://content-media.pamedia.io/press-release/picture/2025/11/19/01KADJ2EW8YDYQABYJFZFVZ5YR.jpg?format=jpg&dl=pr-newswire-associated0.jpg" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;"><span>LeapSpace</span></a>
    <a class="btn-custom-menu" href="https://www.researchrabbit.ai/" target="_blank"><span><img src="https://pbs.twimg.com/profile_images/1983772825812189184/IXDTOqLX_400x400.jpg" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px;object-fit: cover;"><span>ResearchRabbit</span></a>
    <a class="btn-custom-menu" href="https://www.perplexity.ai/" target="_blank"><img src="https://framerusercontent.com/images/gcMkPKyj2RX8EOEja8A1GWvCb7E.jpg?width=2000&height=2000" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;"><span>Perplexity</span></a>
    <a class="btn-custom-menu" href="https://consensus.app/" target="_blank"><img src="https://logosandtypes.com/wp-content/uploads/2025/04/Consensus-scaled.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px;"><span>Consensus</span></a>
    <a class="btn-custom-menu" href="https://scispace.com/" target="_blank"><img src="https://typeset.io/favicon.ico" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px;"><span>SciSpace</span></a>
    <a class="btn-custom-menu" href="https://elicit.com/" target="_blank"><img src="https://zonalogo.com/assets/elicit-logo-png-svg.webp?asset=2444&w=320" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px;"><span>Elicit</span></a>   
    <a class="btn-custom-menu" href="https://logically.app/" target="_blank"><img src="https://www.logically.ai/favicon.ico" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px;"><span>Logically</span></a>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px; letter-spacing: 0.05em;'>SITES GOVERNAMENTAIS</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://cnpq.br/" target="_blank"><span><img src="https://images.seeklogo.com/logo-png/18/1/cnpq-logo-png_seeklogo-181432.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;"><span>CNPq</span></a>
    <a class="btn-custom-menu" href="https://www.gov.br/capes/pt-br" target="_blank"><span><img src="https://www.clipartmax.com/png/middle/289-2899434_previous-next-capes-logo.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;"><span>CAPES</span></a>
    <a class="btn-custom-menu" href="https://lattes.cnpq.br/" target="_blank"><span><img src="https://www.gov.br/observatorio/pt-br/assuntos/programas-academicos/imagens/Lattes.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;"><span>Currículo Lattes</span></a>
    <a class="btn-custom-menu" href="https://www.periodicos.capes.gov.br/" target="_blank"><span><img src="https://www.periodicos.capes.gov.br/templates/periodicos_gov/images/icon-periodicos.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;"><span>Portal de Periódicos CAPES</span></a>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px; letter-spacing: 0.05em;'>INFORMAÇÕES INSTITUCIONAIS</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://www.ufop.br" target="_blank"><span><img src="https://labiiex.ufop.br/sites/default/files/styles/media_gallery_thumbnail/public/labiiex/files/ufop_logo.png?m=1597327148&itok=EmS_8t7o" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;"><span>UFOP</span></a>
    <a class="btn-custom-menu" href="https://www.posedu.ufop.br" target="_blank"><span><img src="https://posedu.ufop.br/sites/default/files/styles/os_files_small/public/ppge/files/logo_reduzida.png?m=1593192999&itok=0JX9OWRl" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;"><span>PPGE-UFOP</span></a>
    <a class="btn-custom-menu" href="https://professor.ufop.br/joaoquadros" target="_blank"><span>👤 Site pessoal</span></a>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>", unsafe_allow_html=True)
st.sidebar.markdown("""
    <div style='color: #0F172A; font-size: 0.8rem; padding-left: 5px; line-height: 1.6;'>
        <p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin:0 0 8px 0; letter-spacing: 0.05em;'>METADADOS</p>
        <span style='color: #A91D22;'>●</span> <b>Sistema:</b> Operacional<br>
        <b>Versão Base:</b> 2026.1<br>
        <b>Padrão CNPq:</b> Ativo
        <br><br>
        <hr style='border: 0; border-top: 1px dashed #E2E8F0; margin: 10px 0;'>
        <b>Direitos Autorais & Propriedade:</b><br>
        © 2026 <b>João F. Soares-Quadros Jr.</b><br>
        Universidade Federal Ouro Preto<br>
        Minas Gerais, Brasil.<br>
        <i>Todos os direitos reservados.</i>
    </div>
""", unsafe_allow_html=True)

# 5. PAINEL PRINCIPAL
st.markdown(f"""
    <div class="premium-hero">
        <h1 class="premium-title">{t['titulo']}</h1>
        <p class="premium-subtitle">{t['subtitulo']}</p>
    </div>
""", unsafe_allow_html=True)

st.markdown(t['filtros_tit'])
busca = st.text_input(t['buscar_reg'], placeholder=t['placeholder_busca'])

aba_escopo, aba_impacto = st.tabs([t['aba_escopo'], t['aba_impacto']])

with aba_escopo:
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        col_subarea = "Subárea do Conhecimento"
        set_subareas = set()
        if col_subarea in df_original.columns:
            for x in df_original[col_subarea].unique():
                if str(x).strip() not in ["", "-", "nan", "None"]:
                    for sub in str(x).split(","):
                        set_subareas.add(sub.strip())
        lista_subareas = sorted(list(set_subareas))
        subarea_sel = st.selectbox(t['subarea_lbl'], [t['todas']] + lista_subareas)
    with col_f2:
        col_indexador = "Indexador" if "Indexador" in df_original.columns else None
        if col_indexador:
            set_indexadores = set()
            for x in df_original[col_indexador].unique():
                if x != "-":
                    for idx in str(x).split(","): set_indexadores.add(idx.strip())
            indexador_sel = st.multiselect(t['base_lbl'], sorted(list(set_indexadores)))
        else: indexador_sel = []

with aba_impacto:
    col_f4, col_f5, col_f6 = st.columns(3)
    with col_f4:
        col_q_jcr = "Quartil JCR"
        opcoes_jcr = sorted([str(x).strip() for x in df_original[col_q_jcr].unique() if str(x).strip() not in ["", "-", "nan", "None"]]) if col_q_jcr in df_original.columns else []
        if not opcoes_jcr: opcoes_jcr = ["Q1", "Q2", "Q3", "Q4"]
        q_jcr_sel = st.multiselect(t['jcr_lbl'], opcoes_jcr)
    with col_f5:
        col_q_sjr = "SJR Best Quartile"
        opcoes_sjr = sorted([str(x).strip() for x in df_original[col_q_sjr].unique() if str(x).strip() not in ["", "-", "nan", "None"]]) if col_q_sjr in df_original.columns else []
        if not opcoes_sjr: opcoes_sjr = ["Q1", "Q2", "Q3", "Q4"]
        q_sjr_sel = st.multiselect(t['sjr_lbl'], opcoes_sjr)
    with col_f6:
        opcoes_ordenacao = ["Título"]
        if "SJR" in df_original.columns: opcoes_ordenacao.append("SJR (Prestígio)")
        if "JIF" in df_original.columns: opcoes_ordenacao.append("JIF (Fator de Impacto)")
        criterio_ordem = st.selectbox(t['ordem_lbl'], options=opcoes_ordenacao)

# 6. FILTRAGEM SEQUENCIAL DE DADOS
df_filtrado = df_original.copy()

if busca:
    df_filtrado = df_filtrado[
        df_filtrado[df_filtrado.columns[0]].astype(str).str.contains(busca, case=False, na=False) | 
        df_filtrado["ISSN"].astype(str).str.contains(busca, case=False, na=False)
    ]

if col_subarea in df_filtrado.columns and subarea_sel != t['todas']:
    df_filtrado = df_filtrado[df_filtrado[col_subarea].astype(str).str.contains(subarea_sel, case=False, na=False)]

if col_indexador and len(indexador_sel) > 0:
    df_filtrado = df_filtrado[df_filtrado[col_indexador].astype(str).str.contains("|".join(indexador_sel), na=False)]

if col_q_jcr in df_filtrado.columns and len(q_jcr_sel) > 0:
    df_filtrado = df_filtrado[df_filtrado[col_q_jcr].astype(str).str.strip().isin(q_jcr_sel)]

if col_q_sjr in df_filtrado.columns and len(q_sjr_sel) > 0:
    df_filtrado = df_filtrado[df_filtrado[col_q_sjr].astype(str).str.strip().isin(q_sjr_sel)]

mapa_ordem = {"SJR (Prestígio)": ("SJR", False), "JIF (Fator de Impacto)": ("JIF", False), "Título": (df_filtrado.columns[0], True)}
col_ordenar, ascendente = mapa_ordem[criterio_ordem]
if col_ordenar in df_filtrado.columns: 
    df_filtrado = df_filtrado.sort_values(by=col_ordenar, ascending=ascendente)

# 7. METRICAS DINÂMICAS COM SEGURANÇA DE TIPO
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1: 
    st.metric(t['m_selecionadas'], f"{len(df_filtrado):,}".replace(",", "."))
with col_m2: 
    h_index_numerico = pd.to_numeric(df_filtrado["H index"], errors='coerce')
    max_h = int(h_index_numerico.max()) if pd.notna(h_index_numerico.max()) else 0
    st.metric(t['m_hindex'], max_h)
with col_m3: 
    jif_numerico = pd.to_numeric(df_filtrado['JIF'], errors='coerce')
    max_jif = f"{jif_numerico.max():.2f}" if pd.notna(jif_numerico.max()) else "0.00"
    st.metric(t['m_jif'], max_jif)
with col_m4: 
    sjr_numerico = pd.to_numeric(df_filtrado['SJR'], errors='coerce')
    max_sjr = f"{sjr_numerico.max():.3f}" if pd.notna(sjr_numerico.max()) else "0.000"
    st.metric(t['m_sjr'], max_sjr)

st.markdown("<br>", unsafe_allow_html=True)

# 8. EXIBIÇÃO E PAGINAÇÃO
st.markdown(t['cat_tit'])
total_itens = len(df_filtrado)
if total_itens > 0:
    col_pag1, col_pag2, _ = st.columns([1.5, 2, 5])
    with col_pag1:
        itens_por_pagina = st.selectbox(t['exibir_pag'], options=[20, 50, 100], index=1)
    total_paginas = (total_itens // itens_por_pagina) + (1 if total_itens % itens_por_pagina > 0 else 0)
    with col_pag2:
        pagina_atual = st.number_input(f"{t['pag_lbl']} (1 de {total_paginas}):", min_value=1, max_value=max(1, total_paginas), value=1)
    
    inicio = (pagina_atual - 1) * itens_por_pagina
    fim = inicio + itens_por_pagina
    df_da_pagina = df_filtrado.iloc[inicio:fim]
    
    # Exibição com colunas ocultas através do formato dicionário seguro
    st.dataframe(
        df_da_pagina, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Homepage": None,
            "Grande Area": None,
            "Area do Conhecimento": None,
            "Subárea do Conhecimento": None
        }
    )
    
    csv_pagina = df_da_pagina.to_csv(index=False, sep=';', encoding='utf-8-sig')
    st.download_button(label=f"{t['exportar_btn']} ({len(df_da_pagina)} itens)", data=csv_pagina, file_name="sciindex_pagina_atual.csv", mime="text/csv")
else:
    st.warning(t['aviso_nada'])