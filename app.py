import streamlit as st
import pandas as pd
import urllib.parse
import base64

# Forma simples e direta de ler
user = st.secrets["usuario"]
password = st.secrets["senha"]

# --- FUNÇÃO PARA CONVERTER IMAGEM LOCAL PARA BASE64 ---
def obter_imagem_local_base64(caminho_arquivo):
    try:
        with open(caminho_arquivo, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        return "" # Retorna vazio se não encontrar o arquivo

# --- PREPARAÇÃO DO NOVO ÍCONE DA PÁGINA ---
# Procura pelo arquivo 'logo.png' que você já enviou para o GitHub
imagem_base64_icon = obter_imagem_local_base64("logo.png")

# --- PREPARAÇÃO DO ÍCONE DA PÁGINA (Apontando para a versão simplificada) ---
imagem_base64_icon = obter_imagem_local_base64("favicon.png") # Nova imagem focada em tamanho pequeno

if imagem_base64_icon:
    novo_page_icon = f"data:image/png;base64,{imagem_base64_icon}"
else:
    novo_page_icon = "📚"

st.set_page_config(
    page_title="Portal do Pesquisador",
    page_icon=novo_page_icon, 
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
        "subtitulo": "Ciência de dados aplicada à produção científica de alto impacto",
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
        "todas": "Todas",
        "col_h5": "Índice h5 (Scholar)", # certifique-se que a última chave existente tenha uma vírgula no final
        # NOVAS CHAVES:
        "meta_tit": "METADADOS",
        "meta_sistema": "Sistema",
        "meta_versao": "Versão Base",
        "meta_padrao": "Padrão CNPq",
        "meta_status": "Operacional",
        "meta_ativo": "Ativo",
        "direitos_tit": "Direitos Autorais & Propriedade",
        "direitos_autor": "Universidade Federal Ouro Preto<br>Minas Gerais, Brasil.<br><i>Todos os direitos reservados.</i>",
        "visitas_lbl": "Visitas ao Portal",
        "gov_tit": "SITES GOVERNAMENTAIS",
        "inst_tit": "INFORMAÇÕES INSTITUCIONAIS",
        "pessoal_lbl": "👤 Site pessoal",
# TRADUÇÕES EXCLUSIVAS SOLICITADAS:
        "indexadores_tit": "INDEXADORES",
	"repositorios_tit": REPOSITÓRIOS,
        "ia_tit": "IA ACADÊMICA"
    },
    "English": {
        "titulo": "Researcher's Portal",
        "subtitulo": "Data science applied to high-impact scientific output.",
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
        "todas": "All",
        "col_h5": "h5-Index (Scholar)",
        # NOVAS CHAVES:
        "meta_tit": "METADATA",
        "meta_sistema": "System",
        "meta_versao": "Base Version",
        "meta_padrao": "CNPq Standard",
        "meta_status": "Operational",
        "meta_ativo": "Active",
        "direitos_tit": "Copyright & Ownership",
        "direitos_autor": "Federal University of Ouro Preto<br>Minas Gerais, Brazil.<br><i>All rights reserved.</i>",
        "visitas_lbl": "Portal Visits",
	"gov_tit": "GOVERNMENT WEBSITES",
        "inst_tit": "INSTITUTIONAL INFORMATION",
        "pessoal_lbl": "👤 Personal website",
# TRADUÇÕES EXCLUSIVAS SOLICITADAS:
        "indexadores_tit": "INDEXERS",
	"repositorios_tit": "DIRECTORY",
        "ia_tit": "ACADEMIC AI"
    },
    "Español": {
        "titulo": "Portal del Investigador",
        "subtitulo": "Ciencia de datos aplicada a la producción científica de más alto nivel.",
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
        "m_selecionadas": "Revistas Selecionadas",
        "m_hindex": "H-Index Máximo",
        "m_jif": "Factor JIF Máximo",
        "m_sjr": "SJR Score Ápice",
        "cat_tit": "#### 📋 Catálogo de Revistas",
        "exibir_pag": "Mostrar por página:",
        "pag_lbl": "Página",
        "exportar_btn": "📥 Exportar solo esta página",
        "aviso_nada": "Ninguna revista coincide con los criterios aplicados.",
        "nav_tit": "Panel de Navegación",
        "todas": "Todas",
        "col_h5": "Índice h5 (Scholar)",
        # NOVAS CHAVES:
        "meta_tit": "METADATOS",
        "meta_sistema": "Sistema",
        "meta_versao": "Versión Base",
        "meta_padrao": "Patrón CNPq",
        "meta_status": "Operacional",
        "meta_ativo": "Activo",
        "direitos_tit": "Derechos de Autor y Propiedad",
        "direitos_autor": "Universidad Federal de Ouro Preto<br>Minas Gerais, Brasil.<br><i>Todos los derechos reservados.</i>",
        "visitas_lbl": "Visitas al Portal",
	"gov_tit": "SITIOS DEL GOBIERNO",
        "inst_tit": "INFORMACIÓN INSTITUCIONAL",
        "pessoal_lbl": "👤 Sitio personal",
# TRADUÇÕES EXCLUSIVAS SOLICITADAS:
        "indexadores_tit": "INDEXADORES",
	"repositorios_tit": DIRECTORIO,
        "ia_tit": "IA ACADÉMICA"
    }
}
t = dic[st.session_state.idioma]

# 2. DESIGN DO HERO DA PÁGINA (CSS CUSTOMIZADO)
st.markdown("""
<style>
    /* Esconde a logo apenas em telas de celulares (menores que 768px) */
    @media (max-width: 768px) {
    .premium-hero img {
        display: none !important;
    }
    /* Opcional: Centraliza o texto no celular já que a logo sumiu */
    .premium-hero {
        text-align: center;
        justify-content: center;
    }
}
    /* Força o fundo do menu lateral com a cor definida */
    [data-testid="stSidebar"] {
        background-color: #F8F0E3 !important;
    }   
    
/* Aumenta o tamanho da fonte e destaca o título do expander */
.stExpander details summary p {
    font-size: 1.35rem !important; /* Ajuste este valor para o tamanho que desejar */
    font-weight: 600 !important;   /* Deixa o título em negrito */
    color: #FFFFF !important;     /* Mantém a cor no tom escuro padrão do seu site */
}

/* Altera a cor do texto "Language / Idioma" (e outros rótulos da barra lateral) */
    [data-testid="stSidebar"] label {
        color: #004B87 !important; 
        font-weight: 600 !important; 
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
        font-size: 3.0rem !important;
        font-weight: 800 !important;
        margin-bottom: 8px !important;
        letter-spacing: -0.5px;
    }
.premium-subtitle {
    color: #FFFFFF !important;
    font-size: 1.45rem !important; 
    max-width: 900px;              
    line-height: 1.5;
    margin-top: 10px; /* Adiciona um espaço elegante entre o título e o subtítulo */
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
    # CORREÇÃO CRÍTICA: Lendo com sep=";" conforme estrutura real do seu arquivo dados_revistas.csv
    df = pd.read_csv("dados_revistas.csv", sep=";", encoding="utf-8-sig", low_memory=False, on_bad_lines='skip')
    df = df.drop_duplicates(subset=[df.columns[0]])
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.columns = [c.strip() for c in df.columns]
    
    # Tratamento numérico padrão das métricas
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

st.sidebar.markdown(f"""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px; letter-spacing: 0.05em;'>{t['indexadores_tit']}</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://access.clarivate.com/login?app=wos&alternative=true&goto=https:%2F%2Fwww.webofknowledge.com" target="_blank"><span><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRR2EHX1gARlgEZ-baT5UZMBSLF7rw0mZtUAMuBSU46_Rm5RzBLW1oOaas&s=10" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px;"><span>Web of Science</span></a>
    <a class="btn-custom-menu" href="https://www.scopus.com/pages/home?display=basic#basic" target="_blank"><span><img src="https://camo.githubusercontent.com/799f6de501a057c2e1997a5f472ac272d4461dd65bdd1c25824d45a97ea9b8ec/68747470733a2f2f7777772e6665722e756e697a672e68722f5f7075622f7468656d65735f7374617469632f666572323031362f64656661756c742f696d672f73636f7075732d69636f6e2e706e67" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px;"><span>Scopus</span></a>
    <a class="btn-custom-menu" href="https://pubmed.ncbi.nlm.nih.gov/" target="_blank"><span><img src="https://its.weill.cornell.edu/sites/default/files/styles/news_item_full_article/public/news_images/720px-us-nlm-pubmed-logo.png?itok=trlhr3Lh" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px;"><span>PubMed</span></a>
    <a class="btn-custom-menu" href="https://www.scielo.br/" target="_blank"><span><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTHiaAjjMsCiMK-A-hur9z1KZcEuf5rEx8rjzketAWDRQNs963MW_DDHwQ&s=10" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px;"><span>Scielo BR</span></a>
    <a class="btn-custom-menu" href="http://educa.fcc.org.br/cgi-bin/wxis.exe/iah/?IsisScript=iah/iah.xis&base=title&fmt=iso.pft&lang=p" target="_blank"><span><img src="https://www.fcc.org.br/fcc/wp-content/uploads/2020/05/fcc.jpg" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px;"><span>Educ@</span></a>
    <a class="btn-custom-menu" href="https://www.jstor.org/" target="_blank"><span><img src="https://upload.wikimedia.org/wikipedia/en/5/56/JSTOR_vector_logo.svg" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px;"><span>JSTOR</span></a>
    <a class="btn-custom-menu" href="https://www.latindex.org/latindex/" target="_blank"><span><img src="https://www.insper.edu.br/content/insper-portal/en/campus/biblioteca-telles/recursos-de-busca/latindex/_jcr_content/root/responsivegrid/wrapper/container_grid/container/wrapper/featured_card_container/image.coreimg.png/1723749927456/latindex.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px;"><span>Latindex</span></a>
    <a class="btn-custom-menu" href="https://eric.ed.gov/" target="_blank"><span><img src="https://yt3.googleusercontent.com/ytc/AIdro_kFijnjScrZN1GZMpmVQDW_GRV5syVZsNuOqd2TiG5Y_A=s900-c-k-c0x00ffffff-no-rj" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px;"><span>ERIC</span></a>
    <a class="btn-custom-menu" href="https://api.base-search.net/" target="_blank"><span><img src="https://pbs.twimg.com/profile_images/1259600128/base_twitter_400x400.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px;"><span>BASE</span></a>
    <a class="btn-custom-menu" href="https://doaj.org/" target="_blank"><span><img src="https://upload.wikimedia.org/wikipedia/commons/d/d9/DOAJ_logo-colour.svg" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px;"><span>DOAJ</span></a>

</div>
""", unsafe_allow_html=True)

st.sidebar.markdown(f"""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px; letter-spacing: 0.05em;'>{t['repositorios_tit']}</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://eric.ed.gov/" target="_blank"><span><img src="https://yt3.googleusercontent.com/ytc/AIdro_kFijnjScrZN1GZMpmVQDW_GRV5syVZsNuOqd2TiG5Y_A=s900-c-k-c0x00ffffff-no-rj" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px;"><span>ERIC</span></a>
    <a class="btn-custom-menu" href="https://api.base-search.net/" target="_blank"><span><img src="https://pbs.twimg.com/profile_images/1259600128/base_twitter_400x400.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px;"><span>BASE</span></a>
    <a class="btn-custom-menu" href="https://doaj.org/" target="_blank"><span><img src="https://upload.wikimedia.org/wikipedia/commons/d/d9/DOAJ_logo-colour.svg" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px;"><span>DOAJ</span></a>

</div>
""", unsafe_allow_html=True)


st.sidebar.markdown(f"""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px; letter-spacing: 0.05em;'>{t['ia_tit']}</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://www.scopus.com/pages/home#scopus-ai" target="_blank"><span><img src="https://images.icon-icons.com/2389/PNG/512/elsevier_logo_icon_145310.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;"><span>ScopusAI</span></a>
    <a class="btn-custom-menu" href="https://researcher.elsevier.com/" target="_blank"><span><img src="https://content-media.pamedia.io/press-release/picture/2025/11/19/01KADJ2EW8YDYQABYJFZFVZ5YR.jpg?format=jpg&dl=pr-newswire-associated0.jpg" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;"><span>LeapSpace</span></a>
    <a class="btn-custom-menu" href="https://www.researchrabbit.ai/" target="_blank"><span><img src="https://pbs.twimg.com/profile_images/1983772825812189184/IXDTOqLX_400x400.jpg" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px;object-fit: cover;"><span>ResearchRabbit</span></a>
    <a class="btn-custom-menu" href="https://www.perplexity.ai/" target="_blank"><img src="https://framerusercontent.com/images/gcMkPKyj2RX8EOEja8A1GWvCb7E.jpg?width=2000&height=2000" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;"><span>Perplexity</span></a>
    <a class="btn-custom-menu" href="https://consensus.app/" target="_blank"><img src="https://logosandtypes.com/wp-content/uploads/2025/04/Consensus-scaled.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px;"><span>Consensus</span></a>
    <a class="btn-custom-menu" href="https://scispace.com/" target="_blank"><img src="https://typeset.io/favicon.ico" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px;"><span>SciSpace</span></a>
    <a class="btn-custom-menu" href="https://elicit.com/" target="_blank"><img src="https://zonalogo.com/assets/elicit-logo-png-svg.webp?asset=2444&w=320" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px;"><span>Elicit</span></a>   
    <a class="btn-custom-menu" href="https://logically.app/" target="_blank"><img src="https://www.logically.ai/favicon.ico" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px;"><span>Logically</span></a>
    <a class="btn-custom-menu" href="https://www.pubmed.ai/home" target="_blank"><img src="https://cdn-1.webcatalog.io/catalog/pubmed-ai/pubmed-ai-icon-filled-256.png?v=1747807986408" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px;"><span>PubMed.AI</span></a>
</div>

""", unsafe_allow_html=True)

st.sidebar.markdown(f"""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px; letter-spacing: 0.05em;'>{t['gov_tit']}</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://cnpq.br/" target="_blank"><span><img src="https://images.seeklogo.com/logo-png/18/1/cnpq-logo-png_seeklogo-181432.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;"><span>CNPq</span></a>
    <a class="btn-custom-menu" href="https://www.gov.br/capes/pt-br" target="_blank"><span><img src="https://www.clipartmax.com/png/middle/289-2899434_previous-next-capes-logo.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;"><span>CAPES</span></a>
    <a class="btn-custom-menu" href="https://lattes.cnpq.br/" target="_blank"><span><img src="https://www.gov.br/observatorio/pt-br/assuntos/programas-academicos/imagens/Lattes.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;"><span>Currículo Lattes</span></a>
    <a class="btn-custom-menu" href="https://www.periodicos.capes.gov.br/" target="_blank"><span><img src="https://www.periodicos.capes.gov.br/templates/periodicos_gov/images/icon-periodicos.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;"><span>Portal de Periódicos CAPES</span></a>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown(f"""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px; letter-spacing: 0.05em;'>{t['inst_tit']}</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://www.ufop.br" target="_blank"><span><img src="https://labiiex.ufop.br/sites/default/files/styles/media_gallery_thumbnail/public/labiiex/files/ufop_logo.png?m=1597327148&itok=EmS_8t7o" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;"><span>UFOP</span></a>
    <a class="btn-custom-menu" href="https://www.posedu.ufop.br" target="_blank"><span><img src="https://posedu.ufop.br/sites/default/files/styles/os_files_small/public/ppge/files/logo_reduzida.png?m=1593192999&itok=0JX9OWRl" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;"><span>PPGE-UFOP</span></a>
    <a class="btn-custom-menu" href="https://www.musica.ufop.br" target="_blank"><span><img src="https://musica.ufop.br/sites/default/files/styles/os_files_xxlarge/public/musica/files/logo22_1_03.png?m=1542714207&itok=i3jpi-oe" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;"><span>Música-UFOP</span></a>
    <a class="btn-custom-menu" href="https://professor.ufop.br/joaoquadros" target="_blank"><span>{t['pessoal_lbl']}</span></a>
</div>
""", unsafe_allow_html=True)

# --- BLOCO CONTADOR ---
st.sidebar.markdown("<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>", unsafe_allow_html=True)

try:
    import os
    arquivo_contador = "contador_visitas.txt"
    
    if not os.path.exists(arquivo_contador):
        with open(arquivo_contador, "w") as f:
            f.write("0")
            
    with open(arquivo_contador, "r") as f:
        conteudo = f.read().strip()
        visitas = int(conteudo) if conteudo.isdigit() else 0
        
    if 'visitou' not in st.session_state:
        st.session_state.visitou = True
        visitas += 1
        with open(arquivo_contador, "w") as f:
            f.write(str(visitas))
            
    st.sidebar.markdown(f"""
        <div style="
            background-color: #79C83D; 
            color: white; 
            padding: 10px 14px; 
            border-radius: 8px; 
            text-align: center; 
            font-weight: 600; 
            font-size: 0.88rem; 
            letter-spacing: 0.02em;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
            width: 100%;
            box-sizing: border-box;
        ">
            👤 {t['visitas_lbl']}: {visitas}
        </div>
    """, unsafe_allow_html=True)
except Exception:
    st.sidebar.markdown("""
        <div style="background-color: #475569; color: white; padding: 10px; border-radius: 8px; text-align: center; font-weight: 600; font-size: 0.88rem; width: 100%;">
            📊 Portal Online
        </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown("<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>", unsafe_allow_html=True)
st.sidebar.markdown(f"""
    <div style='color: #0F172A; font-size: 0.8rem; padding-left: 5px; line-height: 1.6;'>
        <p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin:0 0 8px 0; letter-spacing: 0.05em;'>{t['meta_tit']}</p>
        <span style='color: #A91D22;'>●</span> <b>{t['meta_sistema']}:</b> {t['meta_status']}<br>
        <b>{t['meta_versao']}:</b> 2026.1<br>
        <b>{t['meta_padrao']}:</b> {t['meta_ativo']}
        <br><br>
        <hr style='border: 0; border-top: 1px dashed #E2E8F0; margin: 10px 0;'>
        <b>{t['direitos_tit']}:</b><br>
        <b>© 2026 João F. Soares-Quadros Jr.</b><br>
        {t['direitos_autor']}
    </div>
""", unsafe_allow_html=True)

# 5. PAINEL PRINCIPAL
imagem_base64 = obter_imagem_local_base64("logo.png")

if imagem_base64:
    tag_imagem = f'<img src="data:image/png;base64,{imagem_base64}" style="height: 200px; width: auto; object-fit: contain;">'
else:
    # Se usar o emoji reserva, colocamos uma tag <span> para o CSS também conseguir escondê-lo no celular se quiser
    tag_imagem = '<span class="emoji-logo" style="font-size: 3.5rem; margin-right: 10px;">📚</span>'

st.markdown(f"""
    <div class="premium-hero" style="display: flex; align-items: center; gap: 25px;">
        {tag_imagem}
        <div>
            <h1 class="premium-title" style="margin:0 !important;">{t['titulo']}</h1>
            <p class="premium-subtitle" style="margin: 5px 0 0 0 !important;">{t['subtitulo']}</p>
        </div>
    </div>
""", unsafe_allow_html=True)

if st.session_state.idioma == "Português":
    expander_titulo = "📖 Sobre o Portal & Como Utilizar"
    sobre_texto = """
    ### Bem-vindo ao Portal do Pesquisador!
    Esta é um ferramenta gratuita e que foi desenvolvida com o objetivo de centralizar, otimizar e acelerar a busca por periódicos científicos de alto impacto e relevância acadêmica. Combinando ciência de dados e indexadores globais, o portal serve como um bússola para pesquisadores que buscam o melhor destino para suas produções científicas. 
    
    #### 🛠️ O que você pode fazer aqui?
    1. **Busca Avançada & Booleana:** Pesquise por termos exatos utilizando aspas (ex: `"educação musical"`) ou combine múltiplos critérios usando os operadores lógicos `AND`, `OR` e `NOT` (ex: `music AND education NOT medicine`).
    2. **Filtros por Subárea (CNPq):** Encontre periódicos perfeitamente alinhados à sua subárea específica de atuação e conhecimento.
    3. **Métricas de Impacto:** Analise o prestígio internacional através de quartis e indicadores consolidados das bases **JCR (Clarivate)**, **SJR (Scopus)**, **H-Index** e o link direto para o **Índice h5 (Google Scholar)**.
    4. **Exportação de Dados:** Filtre os resultados de acordo com sua necessidade e faça o download da tabela customizada imediatamente.
    """
elif st.session_state.idioma == "English":
    expander_titulo = "📖 About the Portal & How to Use"
    sobre_texto = """
    ### Welcome to the Researcher's Portal!
    This is a free tool that was developed to centralize, optimize, and accelerate the search for high-impact and academically relevant scientific journals. Combining data science and global indexers, the portal acts as a compass for researchers seeking the best venue for their scientific output.
    
    #### 🛠️ What can you do here?
    1. **Advanced & Boolean Search:** Search for exact phrases using quotation marks (e.g., `"music education"`) or combine multiple criteria using the logical operators `AND`, `OR`, and `NOT` (e.g., `music AND education NOT medicine`).
    2. **Filters by Subarea:** Find journals perfectly aligned with your specific subarea of expertise.
    3. **Impact Metrics:** Analyze international prestige through consolidated quartiles and indicators from **JCR (Clarivate)**, **SJR (Scopus)**, **H-Index**, and direct links to the **h5-Index (Google Scholar)**.
    4. **Data Export:** Filter results according to your needs and download the customized table immediately.
    """
else: # Español
    expander_titulo = "📖 Sobre o Portal y Cómo Utilizar"
    sobre_texto = """
    ### ¡Bienvenido al Portal del Investigador!
   Esta es una herramienta gratuita que fue desarrollada con el objetivo de centralizar, optimizar y acelerar la búsqueda de revistas científicas de alto impacto y relevancia académica. Combinando la ciencia de datos y los indexadores globales, el portal sirve como una brújula para los investigadores que buscan el mejor destino para sus producciones científicas.
    
    #### 🛠️ ¿Qué puedes hacer aquí?
    1. **Búsqueda Avanzada y Booleana:** Busque términos exactos usando comillas (por ejemplo: `"educación musical"`) o combine múltiples criterios usando los operadores lógicos `AND`, `OR` y `NOT` (por ejemplo: `music AND education NOT medicine`).
    2. **Filtros por Subárea:** Encuentre revistas perfectamente alineadas con su subárea específica de conocimiento.
    3. **Métricas de Impacto:** Analice el prestigio internacional a través de cuartiles e indicadores consolidados de las bases **JCR (Clarivate)**, **SJR (Scopus)**, **H-Index** y el enlace directo al **Índice h5 (Google Scholar)**.
    4. **Exportación de Datos:** Filtre los resultados según sus necesidades y descargue la tabla personalizada inmediatamente.
    """
# Renderiza o Expander na tela de forma limpa
with st.expander(expander_titulo, expanded=False):
    st.markdown(sobre_texto)

st.markdown("<br>", unsafe_allow_html=True)
# --- FIM DA NOVA SEÇÃO ---

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
    import re
    texto_busca = busca.strip()
    
    # 1. Tratamento Prévio: Identifica termos exatos entre aspas
    # Cria uma lista temporária para guardar os blocos exatos e não misturá-los com operadores
    termos_exatos = re.findall(r'"([^"]*)"', texto_busca)
    
    # Substitui os termos com aspas por um marcador temporário para não quebrar a lógica booleana seguinte
    texto_processado = texto_busca
    for i, termo in enumerate(termos_exatos):
        texto_processado = texto_processado.replace(f'"{termo}"', f'__EXACT_{i}__')
        
    # Se o usuário não digitou operadores lógicos explícitos, assume AND por padrão entre os blocos
    if not any(op in texto_processado.upper() for op in ["AND", "OR", "NOT"]):
        palavras = [p.strip() for p in texto_processado.split() if p.strip()]
        texto_processado = " AND ".join(palavras)

    # 2. Avaliação Lógica Avançada por Linha (Suporta Booleanos + Aspas)
    def avaliar_busca_avancada(linha_texto, expressao_logica, lista_exatos):
        linha_texto = str(linha_texto).lower()
        
        # Divide a expressão pelos operadores booleanos principais
        tokens = re.split(r'(\bAND\b|\bOR\b|\bNOT\b)', expressao_logica, flags=re.IGNORECASE)
        
        resultado_final = False
        operador_atual = "OR"  # Padrão de inicialização
        inverter_proximo = False
        
        for token in tokens:
            token_clean = token.strip()
            if not token_clean:
                continue
                
            token_upper = token_clean.upper()
            
            if token_upper == "AND":
                operador_atual = "AND"
            elif token_upper == "OR":
                operador_atual = "OR"
            elif token_upper == "NOT":
                inverter_proximo = True
            else:
                # Verifica se o token é um marcador de termo exato entre aspas
                match_exact = re.match(r'__EXACT_(\d+)__', token_clean)
                if match_exact:
                    idx = int(match_exact.group(1))
                    # Resgata o termo original de dentro das aspas e força correspondência exata
                    termo_real = lista_exatos[idx].lower()
                    possui_termo = termo_real in linha_texto
                else:
                    # Termo comum sem aspas
                    termo_real = token_clean.lower()
                    possui_termo = termo_real in linha_texto
                
                if inverter_proximo:
                    possui_termo = not possui_termo
                    inverter_proximo = False
                
                # Aplicação da tabela verdade booleana
                if operador_atual == "AND":
                    resultado_final = resultado_final and possui_termo
                elif operador_atual == "OR":
                    resultado_final = resultado_final or possui_termo
                    
        return resultado_final

    # Executa o filtro combinando o Título da Revista (coluna 0) e o ISSN
    df_filtrado = df_filtrado[
        df_filtrado.apply(
            lambda row: avaliar_busca_avancada(
                f"{row[df_filtrado.columns[0]]} {row['ISSN']}", 
                texto_processado, 
                termos_exatos
            ), 
            axis=1
        )
    ]

# (O restante do seu script com filtros de subárea, indexador, métricas e paginação continua igual abaixo...)
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
    df_da_pagina = df_filtrado.iloc[inicio:fim].copy()
    
    # Tratamento de segurança: Se o link for "-", limpamos para None para o LinkColumn não quebrar
    if "Índice h5" in df_da_pagina.columns:
        df_da_pagina["Índice h5"] = df_da_pagina["Índice h5"].replace("-", None)
    
    # Exibição com colunas ocultas e link limpo estilizado como "🔗 Abrir"
    st.dataframe(
        df_da_pagina, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Homepage": None,
            "Grande Area": None,
            "Area do Conhecimento": None,
            "Subárea do Conhecimento": None,
            "Índice h5": st.column_config.LinkColumn(
                t['col_h5'],
                help="Clique para abrir o índice h5 no Google Scholar",
                display_text="🔗 Abrir"
            )
        }
    )
    
    csv_pagina = df_da_pagina.to_csv(index=False, sep=';', encoding='utf-8-sig')
    st.download_button(label=f"{t['exportar_btn']} ({len(df_da_pagina)} itens)", data=csv_pagina, file_name="sciindex_pagina_atual.csv", mime="text/csv")
else:
    st.warning(t['aviso_nada'])