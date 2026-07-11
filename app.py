import faulthandler
faulthandler.enable()

import streamlit as st
import pandas as pd
import urllib.parse
import requests
import base64
import json
import os
import re

# Detecção dinâmica de versão do Streamlit para evitar erros de TypeError
SUPPORTS_NEW_WIDTH = False
try:
    version_str = st.__version__.split("+")[0]
    parts = []
    for p in version_str.split("."):
        digits = "".join(c for c in p if c.isdigit())
        if digits:
            parts.append(int(digits))
    if len(parts) >= 2:
        if parts[0] > 1 or (parts[0] == 1 and parts[1] >= 58):
            SUPPORTS_NEW_WIDTH = True
except Exception:
    pass

# Dicionário desempacotado dinamicamente para largura de componentes
kwargs_largura = {"width": "stretch"} if SUPPORTS_NEW_WIDTH else {"use_container_width": True}

# --- 1. CONFIGURAÇÃO ÚNICA DA PÁGINA (Executada antes de qualquer comando Streamlit) ---
def obter_imagem_local_base64(caminho_arquivo):
    try:
        if os.path.exists(caminho_arquivo):
            with open(caminho_arquivo, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode()
    except Exception:
        return ""
    return ""

# Busca sequencial do favicon/logo para definir o page_icon
imagem_base64_icon = obter_imagem_local_base64("favicon.png")
if not imagem_base64_icon:
    imagem_base64_icon = obter_imagem_local_base64("logo.png")
if not imagem_base64_icon:
    imagem_base64_icon = obter_imagem_local_base64("st_static/favicon.png")
if not imagem_base64_icon:
    imagem_base64_icon = obter_imagem_local_base64("st_static/logo.png")

novo_page_icon = f"data:image/png;base64,{imagem_base64_icon}" if imagem_base64_icon else "📚"

st.set_page_config(
    page_title="Portal do Pesquisador",
    page_icon=novo_page_icon, 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. SISTEMA DE TRADUÇÃO MULTILÍNGUE ---
if 'idioma' not in st.session_state:
    st.session_state.idioma = "Português"

# Seletor de idioma fixado na barra lateral
st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.session_state.idioma = st.sidebar.selectbox(
    "🌐 Language / Idioma:",
    ["Português", "English", "Español"]
)

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
        "col_h5": "Índice h5 (Scholar)",
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
        "indexadores_tit": "INDEXADORES",
        "repositorios_tit": "REPOSITÓRIOS",
        "ia_tit": "IA ACADÊMICA",
        "btn_desktop": "💻 Baixar Versão para Windows",
        "busca_cat": "🔍 Catálogo de Periódicos",
        "busca_ia": "🧠 Recomendador Inteligente (IA)",
        "ia_titulo": "Recomendação Temática com Inteligência Artificial",
        "ia_subtitulo": "Cole o título e o resumo (abstract) do seu artigo. A IA analisará o nosso catálogo e indicará as opções mais adequadas.",
        "ia_campo_titulo": "Título do Artigo",
        "ia_campo_resumo": "Resumo / Abstract (Suporta Português, Inglês ou Espanhol)",
        "ia_chave_api": "Chave API do Gemini (Google AI Studio)",
        "ia_chave_ajuda": "Você precisa de uma chave API gratuita obtida no Google AI Studio para rodar a recomendação online.",
        "ia_num_rec": "Quantidade de recomendações desejadas (máx. 10)",
        "ia_btn_buscar": "Analisar e Recomendar",
        "ia_analisando": "A IA está processando o seu resumo e cruzando com o catálogo...",
        "ia_sucesso": "Recomendações geradas com sucesso!",
        "ia_erro": "Erro ao processar com a IA. Verifique se a sua Chave API está correta.",
        "ia_card_motivo": "Por que publicar aqui:",
        "ia_card_aderencia": "Grau de Aderência:",
        "ia_card_site": "🌐 Visitar Homepage Oficial",
        "ia_card_sem_site": "Site indisponível na base",
        "filtro_area": "Grande Área",
        "filtro_indexador": "Indexador"
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
        "jcr_lbl": "JCR%20Quartile%20(Clarivate):", # URL encoded helper
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
        "indexadores_tit": "INDEXERS",
        "repositorios_tit": "DIRECTORIES",
        "ia_tit": "ACADEMIC AI",
        "btn_desktop": "💻 Download Windows Version",
        "busca_cat": "🔍 Journal Catalog",
        "busca_ia": "🧠 Smart Recommender (AI)",
        "ia_titulo": "Thematic Recommendation with Artificial Intelligence",
        "ia_subtitulo": "Paste your article title and abstract. The AI will analyze our journal catalog and suggest the best matches.",
        "ia_campo_titulo": "Article Title",
        "ia_campo_resumo": "Abstract (Supports Portuguese, English, or Spanish)",
        "ia_chave_api": "Gemini API Key (Google AI Studio)",
        "ia_chave_ajuda": "You need a free API key from Google AI Studio to run the online recommendation.",
        "ia_num_rec": "Number of desired recommendations (max. 10)",
        "ia_btn_buscar": "Analyze and Recommend",
        "ia_analisando": "AI is processing your abstract and matching with the catalog...",
        "ia_sucesso": "Recommendations generated successfully!",
        "ia_erro": "Error processing with AI. Check if your API Key is correct.",
        "ia_card_motivo": "Why publish here:",
        "ia_card_aderencia": "Adherence Score:",
        "ia_card_site": "🌐 Visit Official Homepage",
        "ia_card_sem_site": "Website not available in database",
        "filtro_area": "Broad Area",
        "filtro_indexador": "Indexer"
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
        "meta_tit": "METADATOS",
        "meta_sistema": "Sistema",
        "meta_versao": "Versión Base",
        "meta_padrao": "Patrón CNPq",
        "meta_status": "Operacional",
        "meta_ativo": "Activo",
        "direitos_tit": "Derechos de Autor y Propiedad",
        "direitos_autor": "Universidad Federal de Ouro Preto<br>Minas Gerais, Brasil.<br><i>Todos os direitos reservados.</i>",
        "visitas_lbl": "Visitas al Portal",
        "gov_tit": "SITIOS DEL GOBIERNO",
        "inst_tit": "INFORMACIÓN INSTITUCIONAL",
        "pessoal_lbl": "👤 Sitio personal",
        "indexadores_tit": "INDEXADORES",
        "repositorios_tit": "DIRECTORIOS",
        "ia_tit": "IA ACADÉMICA",
        "btn_desktop": "💻 Descargar Versión para Windows",
        "busca_cat": "🔍 Catálogo de Revistas",
        "busca_ia": "🧠 Recomendador Inteligente (IA)",
        "ia_titulo": "Recomendación Temática con Inteligencia Artificial",
        "ia_subtitulo": "Pegue el título y el resumen (abstract) de su artículo. La IA analizará nuestro catálogo de revistas e indicará las mejores opciones.",
        "ia_campo_titulo": "Título del Artículo",
        "ia_campo_resumo": "Resumen / Abstract (Soporta Portugués, Inglés o Español)",
        "ia_chave_api": "Clave API de Gemini (Google AI Studio)",
        "ia_chave_ajuda": "Necesitas una clave API gratuita obtenida de Google AI Studio para ejecutar la recomendación en línea.",
        "ia_num_rec": "Cantidad de recomendaciones deseadas (máx. 10)",
        "ia_btn_buscar": "Analar y Recomendar",
        "ia_analisando": "La IA está procesando su resumo y cruzándolo con el catálogo...",
        "ia_sucesso": "¡Recomendaciones generadas con éxito!",
        "ia_erro": "Error al procesar con la IA. Verifique que su Clave API sea correcta.",
        "ia_card_motivo": "Por qué publicar aqui:",
        "ia_card_aderencia": "Grado de Adherencia:",
        "ia_card_site": "🌐 Visitar Homepage Oficial",
        "ia_card_sem_site": "Sitio no disponible en la base",
        "filtro_area": "Gran Área",
        "filtro_indexador": "Indexador"
    }
}
# Correção do seletor em inglês caso venha codificado
if st.session_state.idioma not in dic:
    st.session_state.idioma = "Português"
t = dic[st.session_state.idioma]

# --- 3. CSS CUSTOMIZADO CORRIGIDO (Design Responsivo e Premium) ---
st.markdown("""
<script>
    // Previne que ferramentas de tradução automática corrompam o DOM do React/Streamlit
    const meta = document.createElement('meta');
    meta.name = 'google';
    meta.content = 'notranslate';
    document.getElementsByTagName('head')[0].appendChild(meta);
    document.body.classList.add('notranslate');
    document.body.setAttribute('translate', 'no');
</script>
<style>
    /* Esconde a logo apenas em telas de celulares (menores que 768px) */
    @media (max-width: 768px) {
        .premium-hero img {
            display: none !important;
        }
        .premium-hero {
            text-align: center;
            justify-content: center;
        }
    }
    /* Força o fundo do menu lateral com a cor definida */
    [data-testid="stSidebar"] {
        background-color: #F8F0E3 !important;
    }   
    
    /* Destaque para o título do expander */
    .stExpander details summary p {
        font-size: 1.35rem !important;
        font-weight: 600 !important;
        color: #FFFFFF !important;
    }

    /* Rótulos da barra lateral */
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
        margin-top: 10px;
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

# --- 4. FUNÇÃO ÚNICA DE CARREGAMENTO DE DADOS (Focado apenas em dados.csv) ---
@st.cache_data
def carregar_dados():
    nome_arquivo = "dados.csv"
    if not os.path.exists(nome_arquivo):
        if os.path.exists("Dados.csv"):
            nome_arquivo = "Dados.csv"
        elif os.path.exists("DADOS.CSV"):
            nome_arquivo = "DADOS.CSV"
            
    if os.path.exists(nome_arquivo):
        try:
            # Detecta o separador (; ou ,) inspecionando a primeira linha
            with open(nome_arquivo, "r", encoding="utf-8-sig", errors="ignore") as f:
                primeira_linha = f.readline()
            separador = ";" if primeira_linha.count(";") >= primeira_linha.count(",") else ","
            
            df = pd.read_csv(nome_arquivo, sep=separador, encoding="utf-8-sig", low_memory=False, on_bad_lines='skip')
            
            df.columns = df.columns.str.replace('^\ufeff', '', regex=True)
            df = df.drop_duplicates(subset=[df.columns[0]])
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df.columns = [c.strip() for c in df.columns]
            
            # Tratamento numérico padrão das métricas
            for col in ['SJR', 'JIF', 'h-index', 'H index']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(',', '.').str.strip()
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
            # Identifica colunas não numéricas e substitui vazios por "-"
            for col in df.columns:
                if col not in ['SJR', 'JIF', 'h-index', 'H index']:
                    df[col] = df[col].fillna("-").astype(str)
                    df[col] = df[col].replace(["None", "none", "NONE", "nan", "NaN", "null", ""], "-")
            
            # Garante a existência da coluna Homepage
            if "Homepage" not in df.columns:
                df["Homepage"] = ""
            else:
                df["Homepage"] = df["Homepage"].fillna("")
                
            return df, nome_arquivo
        except Exception as e:
            st.error(f"⚠️ Erro ao processar a base de dados '{nome_arquivo}'. Detalhes: {e}")
            st.stop()
    else:
        st.error("⚠️ Base de dados não encontrada. O arquivo 'dados.csv' não foi localizado na raiz do projeto. Por favor, certifique-se de fazer o download do arquivo no repositório GitHub correspondente.")
        st.stop()

df_original, arquivo_usado = carregar_dados()

# --- 5. MONTAGEM DA SIDEBAR (LINKS E COMPONENTES) ---
st.sidebar.markdown(f"""
    <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 20px;'>
        <h2 style='margin: 0; font-size: 1.60rem; font-weight: 700; color: #0F172A;'>{t['nav_tit']}</h2>
    </div>
""", unsafe_allow_html=True)

# indexadores
st.sidebar.markdown(f"""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px; letter-spacing: 0.05em;'>{t['indexadores_tit']}</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://access.clarivate.com/login?app=wos&alternative=true&goto=https:%2F%2Fwww.webofknowledge.com" target="_blank">
        <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRR2EHX1gARlgEZ-baT5UZMBSLF7rw0mZtUAMuBSU46_Rm5RzBLW1oOaas&s=10" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>Web of Science</span>
    </a>
    <a class="btn-custom-menu" href="https://www.scopus.com/pages/home?display=basic#basic" target="_blank">
        <img src="https://camo.githubusercontent.com/799f6de501a057c2e1997a5f472ac272d4461dd65bdd1c25824d45a97ea9b8ec/68747470733a2f2f7777772e6665722e756e697a672e68722f5f7075622f7468656d65735f7374617469632f666572323031362f64656661756c742f696d672f73636f7075732d69636f6e2e706e67" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>Scopus</span>
    </a>
    <a class="btn-custom-menu" href="https://pubmed.ncbi.nlm.nih.gov/" target="_blank">
        <img src="https://its.weill.cornell.edu/sites/default/files/styles/news_item_full_article/public/news_images/720px-us-nlm-pubmed-logo.png?itok=trlhr3Lh" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>PubMed</span>
    </a>
    <a class="btn-custom-menu" href="https://www.scielo.br/" target="_blank">
        <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTHiaAjjMsCiMK-A-hur9z1KZcEuf5rEx8rjzketAWDRQNs963MW_DDHwQ&s=10" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>Scielo BR</span>
    </a>
    <a class="btn-custom-menu" href="http://educa.fcc.org.br/cgi-bin/wxis.exe/iah/?IsisScript=iah/iah.xis&base=title&fmt=iso.pft&lang=p" target="_blank">
        <img src="https://www.fcc.org.br/fcc/wp-content/uploads/2020/05/fcc.jpg" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>Educ@</span>
    </a>
    <a class="btn-custom-menu" href="https://www.jstor.org/" target="_blank">
        <img src="https://upload.wikimedia.org/wikipedia/en/5/56/JSTOR_vector_logo.svg" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>JSTOR</span>
    </a>
    <a class="btn-custom-menu" href="https://www.latindex.org/latindex/" target="_blank">
        <img src="https://www.insper.edu.br/content/insper-portal/en/campus/biblioteca-telles/recursos-de-busca/latindex/_jcr_content/root/responsivegrid/wrapper/container_grid/container/wrapper/featured_card_container/image.coreimg.png/1723749927456/latindex.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>Latindex</span>
    </a>
</div>
""", unsafe_allow_html=True)

# repositórios
st.sidebar.markdown(f"""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px; letter-spacing: 0.05em;'>{t['repositorios_tit']}</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://eric.ed.gov/" target="_blank">
        <img src="https://yt3.googleusercontent.com/ytc/AIdro_kFijnjScrZN1GZMpmVQDW_GRV5syVZsNuOqd2TiG5Y_A=s900-c-k-c0x00ffffff-no-rj" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>ERIC</span>
    </a>
    <a class="btn-custom-menu" href="https://api.base-search.net/" target="_blank">
        <img src="https://pbs.twimg.com/profile_images/1259600128/base_twitter_400x400.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>BASE</span>
    </a>
    <a class="btn-custom-menu" href="https://doaj.org/" target="_blank">
        <img src="https://upload.wikimedia.org/wikipedia/commons/d/d9/DOAJ_logo-colour.svg" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>DOAJ</span>
    </a>
    <a class="btn-custom-menu" href="https://catalogodeteses.capes.gov.br/catalogo-teses/#!/" target="_blank">
        <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ04fk8I3y7LecgydHxbQybU3R9TB7qb99ikUFKNUsZNQ&s" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>Catálogo da CAPES</span>
    </a>
</div>
""", unsafe_allow_html=True)

# ia acadêmica
st.sidebar.markdown(f"""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px; letter-spacing: 0.05em;'>{t['ia_tit']}</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://www.scopus.com/pages/home#scopus-ai" target="_blank">
        <img src="https://images.icon-icons.com/2389/PNG/512/elsevier_logo_icon_145310.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>ScopusAI</span>
    </a>
    <a class="btn-custom-menu" href="https://researcher.elsevier.com/" target="_blank">
        <img src="https://content-media.pamedia.io/press-release/picture/2025/11/19/01KADJ2EW8YDYQABYJFZFVZ5YR.jpg?format=jpg&dl=pr-newswire-associated0.jpg" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>LeapSpace</span>
    </a>
    <a class="btn-custom-menu" href="https://www.researchrabbit.ai/" target="_blank">
        <img src="https://pbs.twimg.com/profile_images/1983772825812189184/IXDTOqLX_400x400.jpg" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>ResearchRabbit</span>
    </a>
    <a class="btn-custom-menu" href="https://www.perplexity.ai/" target="_blank">
        <img src="https://framerusercontent.com/images/gcMkPKyj2RX8EOEja8A1GWvCb7E.jpg?width=2000&height=2000" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>Perplexity</span>
    </a>
    <a class="btn-custom-menu" href="https://consensus.app/" target="_blank">
        <img src="https://logosandtypes.com/wp-content/uploads/2025/04/Consensus-scaled.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>Consensus</span>
    </a>
    <a class="btn-custom-menu" href="https://scispace.com/" target="_blank">
        <img src="https://typeset.io/favicon.ico" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>SciSpace</span>
    </a>
    <a class="btn-custom-menu" href="https://elicit.com/" target="_blank">
        <img src="https://zonalogo.com/assets/elicit-logo-png-svg.webp?asset=2444&w=320" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>Elicit</span>
    </a>   
    <a class="btn-custom-menu" href="https://logically.app/" target="_blank">
        <img src="https://www.logically.ai/favicon.ico" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>Logically</span>
    </a>
    <a class="btn-custom-menu" href="https://www.pubmed.ai/home" target="_blank">
        <img src="https://cdn-1.webcatalog.io/catalog/pubmed-ai/pubmed-ai-icon-filled-256.png?v=1747807986408" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>PubMed.AI</span>
    </a>
</div>
""", unsafe_allow_html=True)

# governamentais
st.sidebar.markdown(f"""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px; letter-spacing: 0.05em;'>{t['gov_tit']}</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://cnpq.br/" target="_blank">
        <img src="https://images.seeklogo.com/logo-png/18/1/cnpq-logo-png_seeklogo-181432.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>CNPq</span>
    </a>
    <a class="btn-custom-menu" href="https://www.gov.br/capes/pt-br" target="_blank">
        <img src="https://www.clipartmax.com/png/middle/289-2899434_previous-next-capes-logo.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>CAPES</span>
    </a>
    <a class="btn-custom-menu" href="https://lattes.cnpq.br/" target="_blank">
        <img src="https://www.gov.br/observatorio/pt-br/assuntos/programas-academicos/imagens/Lattes.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>Currículo Lattes</span>
    </a>
    <a class="btn-custom-menu" href="https://www.periodicos.capes.gov.br/" target="_blank">
        <img src="https://www.periodicos.capes.gov.br/templates/periodicos_gov/images/icon-periodicos.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>Portal de Periódicos CAPES</span>
    </a>
</div>
""", unsafe_allow_html=True)

# institucionais
st.sidebar.markdown(f"""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px; letter-spacing: 0.05em;'>{t['inst_tit']}</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://www.ufop.br" target="_blank">
        <img src="https://labiiex.ufop.br/sites/default/files/styles/media_gallery_thumbnail/public/labiiex/files/ufop_logo.png?m=1597327148&itok=EmS_8t7o" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>UFOP</span>
    </a>
    <a class="btn-custom-menu" href="https://www.posedu.ufop.br" target="_blank">
        <img src="https://posedu.ufop.br/sites/default/files/styles/os_files_small/public/ppge/files/logo_reduzida.png?m=1593192999&itok=0JX9OWRl" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>PPGE-UFOP</span>
    </a>
    <a class="btn-custom-menu" href="https://www.musica.ufop.br" target="_blank">
        <img src="https://musica.ufop.br/sites/default/files/styles/os_files_xxlarge/public/musica/files/logo22_1_03.png?m=1542714207&itok=i3jpi-oe" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>Música-UFOP</span>
    </a>
    <a class="btn-custom-menu" href="https://professor.ufop.br/joaoquadros" target="_blank">
        <span style="font-weight: 500; font-size: 0.9rem; color: #004B87;">{t['pessoal_lbl']}</span>
    </a>
</div>
""", unsafe_allow_html=True)

# --- 6. BLOCO CONTADOR DE VISITAS ---
st.sidebar.markdown("<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>", unsafe_allow_html=True)
try:
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

# --- 7. METADADOS E DIREITOS AUTORAIS ---
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

# --- 8. BOTÃO DE DOWNLOAD DA VERSÃO DESKTOP ---
texto_botao = t.get("btn_desktop", "💻 Baixar Versão para Windows")

st.sidebar.markdown(
    f"""
    <a href="https://drive.google.com/..." target="_blank" style="text-decoration: none;">
        <button style="
            width: 100%;
            background-color: #FF2B2B;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 0.95rem;
            cursor: pointer;
            transition: background 0.3s ease;
            margin-bottom: 15px;
        " onmouseover="this.style.backgroundColor='#cc2222'" onmouseout="this.style.backgroundColor='#FF2B2B'">
            {texto_botao}
        </button>
    </a>
    """,
    unsafe_allow_html=True
)

# --- 9. PAINEL PRINCIPAL (HERO DESIGN) ---
imagem_base64 = obter_imagem_local_base64("logo.png")
if not imagem_base64:
    imagem_base64 = obter_imagem_local_base64("logo_azul.png")
if not imagem_base64:
    imagem_base64 = obter_imagem_local_base64("st_static/logo.png")

if imagem_base64:
    tag_imagem = f'<img src="data:image/png;base64,{imagem_base64}" style="height: 100px; width: auto; object-fit: contain;">'
else:
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

# Textos informativos traduzidos
if st.session_state.idioma == "Português":
    expander_titulo = "📖 Sobre o Portal & Como Utilizar"
    sobre_texto = """
### Bem-vindo ao Portal do Pesquisador!
Esta é uma ferramenta desenvolvida para otimizar a busca por periódicos científicos de alto impacto.
  
#### 🛠️ O que você pode fazer aqui?
1. **Busca Avançada & Booleana:** Pesquise por termos exatos utilizando aspas (ex: `"educação musical"`) ou combine múltiplos critérios usando os operadores lógicos `AND`, `OR` e `NOT` (ex: `music AND education NOT medicine`).
2. **Filtros por Subárea (CNPq):** Encontre periódicos perfeitamente alinhados à sua subárea específica de atuação e conhecimento.
3. **Métricas de Impacto:** Analise o prestígio internacional através de quartis e indicadores consolidados das bases **JCR (Clarivate)**, **SJR (Scopus)**, **H-Index** e o link direto para o **Índice h5 (Google Scholar)**.
4. **Recomendação Inteligente (IA):** Use a inteligência artificial do Google Gemini para colar o título e resumo do seu artigo e obter as recomendações de periódicos ideais com justificativa e link direto.
5. **Exportação de Dados:** Filtre os resultados de acordo com sua necessidade e faça o download da tabela customizada imediatamente.
"""
elif st.session_state.idioma == "English":
    expander_titulo = "📖 About the Portal & How to Use"
    sobre_texto = """
### Welcome to the Researcher's Portal!
This is a tool developed to optimize the search for high-impact scientific journals.
 
#### 🛠️ What can you do here?
1. **Advanced & Boolean Search:** Search for exact phrases using quotation marks (e.g., `"music education"`) or combine multiple criteria using the logical operators `AND`, `OR`, and `NOT` (e.g., `music AND education NOT medicine`).
2. **Filters by Subarea (CNPq):** Find journals perfectly aligned with your specific subarea of expertise.
3. **Impact Metrics:** Analyze international prestige through consolidated quartiles and indicators from **JCR (Clarivate)**, **SJR (Scopus)**, **H-Index**, and direct links to the **h5-Index (Google Scholar)**.
4. **Smart Recommender (AI):** Paste your title and abstract, and let the Google Gemini AI recommend the best matches with specific rationale and homepage links.
5. **Data Export:** Filter results according to your needs and download the customized table immediately.
"""
else: # Español
    expander_titulo = "📖 Sobre o Portal y Cómo Utilizar"
    sobre_texto = """
### ¡Bienvenido al Portal del Investigador!
Esta es una herramienta desarrollada con el objetivo de optimizar la búsqueda de revistas científicas de alto impacto.
 
#### 🛠️ ¿Qué puedes fazer aquí?
1. **Búsqueda Avanzada y Booleana:** Busque términos exactos usando comillas (por ejemplo: `"educación musical"`) o combine múltiples criterios usando los operadores lógicos `AND`, `OR` y `NOT` (por ejemplo: `music AND education NOT medicine`).
2. **Filtros por Subárea (CNPq):** Encuentre revistas perfectamente alineadas con su subárea específica de conocimiento.
3. **Métricas de Impacto:** Analise el prestigio internacional a través de cuartiles e indicadores consolidados de las bases **JCR (Clarivate)**, **SJR (Scopus)**, **H-Index** y el enlace directo al **Índice h5 (Google Scholar)**.
4. **Recomendador Inteligente (IA):** Use el motor de IA de Google Gemini para obtener sugerencias temáticas personalizadas basadas en el título y resumen de su artículo.
5. **Exportación de Dados:** Filtre los resultados según sus necesidades y descargue la tabla personalizada inmediatamente.
"""

with st.expander(expander_titulo, expanded=False):
    st.markdown(sobre_texto)

st.markdown("<br>", unsafe_allow_html=True)

# --- 10. INTERFACE PRINCIPAL MULTI-ABAS ---
tab_busca, tab_ia = st.tabs([t['busca_cat'], t['busca_ia']])

# ==================== ABA 1: CATÁLOGO TRADICIONAL ====================
with tab_busca:
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
                        for idx in str(x).split(","): 
                            set_indexadores.add(idx.strip())
                indexador_sel = st.multiselect(t['base_lbl'], sorted(list(set_indexadores)))
            else: 
                indexador_sel = []

    with aba_impacto:
        col_f4, col_f5, col_f6 = st.columns(3)
        with col_f4:
            col_q_jcr = "Quartil JCR"
            opcoes_jcr = sorted([str(x).strip() for x in df_original[col_q_jcr].unique() if str(x).strip() not in ["", "-", "nan", "None"]]) if col_q_jcr in df_original.columns else []
            if not opcoes_jcr: 
                opcoes_jcr = ["Q1", "Q2", "Q3", "Q4"]
            q_jcr_sel = st.multiselect(t['jcr_lbl'], opcoes_jcr)
        with col_f5:
            col_q_sjr = "SJR Best Quartile"
            opcoes_sjr = sorted([str(x).strip() for x in df_original[col_q_sjr].unique() if str(x).strip() not in ["", "-", "nan", "None"]]) if col_q_sjr in df_original.columns else []
            if not opcoes_sjr: 
                opcoes_sjr = ["Q1", "Q2", "Q3", "Q4"]
            q_sjr_sel = st.multiselect(t['sjr_lbl'], opcoes_sjr)
        with col_f6:
            opcoes_ordenacao = ["Título"]
            if "SJR" in df_original.columns: 
                opcoes_ordenacao.append("SJR (Prestígio)")
            if "JIF" in df_original.columns: 
                opcoes_ordenacao.append("JIF (Fator de Impacto)")
            criterio_ordem = st.selectbox(t['ordem_lbl'], options=opcoes_ordenacao)

    # FILTRAGEM SEQUENCIAL DE DADOS
    df_filtrado = df_original.copy()

    if busca:
        texto_busca = busca.strip()
        termos_exatos = re.findall(r'"([^"]*)"', texto_busca)
        
        texto_processado = texto_busca
        for i, termo in enumerate(termos_exatos):
            texto_processado = texto_processado.replace(f'"{termo}"', f'__EXACT_{i}__')
            
        if not any(op in texto_processado.upper() for op in ["AND", "OR", "NOT"]):
            palavras = [p.strip() for p in texto_processado.split() if p.strip()]
            texto_processado = " AND ".join(palavras)

        def avaliar_busca_avancada(linha_texto, expressao_logica, lista_exatos):
            linha_texto = str(linha_texto).lower()
            tokens = re.split(r'(\bAND\b|\bOR\b|\bNOT\b)', expressao_logica, flags=re.IGNORECASE)
            
            resultado_final = False
            operador_atual = "OR"
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
                    match_exact = re.match(r'__EXACT_(\d+)__', token_clean)
                    if match_exact:
                        idx = int(match_exact.group(1))
                        termo_real = lista_exatos[idx].lower()
                        possui_termo = termo_real in linha_texto
                    else:
                        termo_real = token_clean.lower()
                        possui_termo = termo_real in linha_texto
                    
                    if inverter_proximo:
                        possui_termo = not possui_termo
                        inverter_proximo = False
                    
                    if operador_atual == "AND":
                        resultado_final = resultado_final and possui_termo
                    elif operador_atual == "OR":
                        resultado_final = resultado_final or possui_termo
                        
            return resultado_final

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

    # METRICAS DINÂMICAS COM SEGURANÇA DE TIPO
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

    # EXIBIÇÃO E PAGINAÇÃO
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
        
        if "Índice h5" in df_da_pagina.columns:
            df_da_pagina["Índice h5"] = df_da_pagina["Índice h5"].replace("-", None)
        
        # EXIBIÇÃO DA HOMEPAGE NA TABELA COM LINK CLICÁVEL
        st.dataframe(
            df_da_pagina, 
            hide_index=True,
            column_config={
                "Homepage": st.column_config.LinkColumn(
                    "Homepage",
                    help="Clique para visitar o site oficial da revista",
                    display_text="🔗 Ver site"
                ),
                "Grande Area": None,
                "Area do Conhecimento": None,
                "Subárea do Conhecimento": None,
                "Índice h5": st.column_config.LinkColumn(
                    t['col_h5'],
                    help="Clique para abrir o índice h5 no Google Scholar",
                    display_text="🔗 Abrir"
                )
            },
            **kwargs_largura
        )
        
        csv_pagina = df_da_pagina.to_csv(index=False, sep=';', encoding='utf-8-sig')
        st.download_button(label=f"{t['exportar_btn']} ({len(df_da_pagina)} itens)", data=csv_pagina, file_name="sciindex_pagina_atual.csv", mime="text/csv")
    else:
        st.warning(t['aviso_nada'])

# ==================== ABA 2: RECOMENDADOR POR IA (GEMINI 1.5 FLASH) ====================
with tab_ia:
    st.markdown(f"### {t['ia_titulo']}")
    st.markdown(f"*{t['ia_subtitulo']}*")
    
    # Inicialização segura dos estados na Session State
    if "recomendacoes" not in st.session_state:
        st.session_state.recomendacoes = None
    if "erro_ia" not in st.session_state:
        st.session_state.erro_ia = None
    if "aviso_filtro" not in st.session_state:
        st.session_state.aviso_filtro = False
    
    col_input, col_meta = st.columns([2, 1])
    
    with col_input:
        titulo_artigo = st.text_input(t['ia_campo_titulo'], placeholder="Ex: Análise Epidemiológica de Saúde Coletiva...", key="ia_tit_input")
        resumo_artigo = st.text_area(t['ia_campo_resumo'], placeholder="Paste or type abstract here...", height=250, key="ia_res_input")
        
    with col_meta:
        # Credencial e Chave de API inseridas diretamente na aba de controle da IA
        st.markdown("#### 🔑 Credencial")
        
        # Lê chave do segredo do Streamlit Cloud se existir
        chave_secrets = ""
        try:
            if hasattr(st, "secrets") and st.secrets is not None:
                chave_secrets = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            pass
            
        if chave_secrets:
            placeholder_input = "🔑 Chave global ativa (opcional pessoal)"
            help_input = "Uma chave global já está configurada pelo proprietário do app. Se desejar usar sua própria chave pessoal, digite-a aqui."
        else:
            placeholder_input = "AIzaSy..."
            help_input = t['ia_chave_ajuda']
            
        user_gemini_key = st.text_input(
            t['ia_chave_api'], 
            type="password", 
            placeholder=placeholder_input, 
            help=help_input
        )
        
        # Define a chave ativa final (prioriza input do usuário)
        api_key_ativa = user_gemini_key.strip() if user_gemini_key else (chave_secrets.strip() if chave_secrets else "")
        
        st.markdown("#### 🎯 Refinar Alvos")
        area_ia = st.selectbox(f"{t['filtro_area']} (IA)", ["Todas"] + list(df_original["Grande Area"].dropna().unique()))
        indexador_ia = st.selectbox(f"{t['filtro_indexador']} (IA)", ["Todos"] + list(df_original["Indexador"].dropna().unique()))
        
        # Slider dinâmico integrado para selecionar entre 3 e 10 recomendações
        num_recomendacoes = st.slider(
            t['ia_num_rec'], 
            min_value=3, 
            max_value=10, 
            value=5, 
            step=1
        )
        
    if st.button(t['ia_btn_buscar'], type="primary", key="btn_ia_disparar"):
        if not api_key_ativa:
            st.error("⚠️ Para utilizar esta ferramenta, insira sua chave da API do Gemini no painel de Credenciais acima.")
        elif not titulo_artigo or not resumo_artigo:
            st.warning("⚠️ Preencha o Título e o Resumo do seu artigo científico para rodar a recomendação.")
        else:
            # Reseta os estados anteriores antes do novo processamento
            st.session_state.recomendacoes = None
            st.session_state.erro_ia = None
            st.session_state.aviso_filtro = False
            
            # Utiliza um placeholder simples do Streamlit (st.empty) para o indicador de progresso,
            # evitando qualquer conflito de animação de Spinner no DOM virtual do React.
            status_container = st.empty()
            status_container.info(f"⏳ {t['ia_analisando']}")
            
            df_candidatos = df_original.copy()
            if area_ia != "Todas":
                df_candidatos = df_candidatos[df_candidatos["Grande Area"] == area_ia]
            if indexador_ia != "Todos":
                df_candidatos = df_candidatos[df_candidatos["Indexador"].astype(str).str.contains(re.escape(indexador_ia), case=False, na=False)]
            
            # Validação caso a base filtrada esteja vazia
            if df_candidatos.empty:
                st.session_state.aviso_filtro = True
            else:
                # Seleciona até 100 candidatos para passar ao contexto do modelo de IA
                if len(df_candidatos) > 100:
                    df_candidatos = df_candidatos.head(100)
                
                lista_periodicos_envio = df_candidatos[[df_original.columns[0], "Grande Area", "Area do Conhecimento", "Indexador", "Quartil JCR", "SJR"]].to_dict(orient="records")
                
                # Prompt estruturado para forçar o retorno estrito de um array JSON
                prompt_ia = f"""
                Atue como especialista em publicação acadêmica. O pesquisador submeteu o seguinte artigo científico:
                TÍTULO DO ARTIGO: {titulo_artigo}
                RESUMO DO ARTIGO: {resumo_artigo}

                Com base estritamente na lista de periódicos abaixo estruturada em JSON, selecione até {num_recomendacoes} (dentre as disponíveis) revistas científicas que apresentem a maior aderência temática, metodológica e de escopo.

                Lista de Periódicos Candidatos:
                {json.dumps(lista_periodicos_envio, ensure_ascii=False)}

                Sua resposta deve ser obrigatoriamente um array JSON válido (sem tags markdown em volta como ```json, apenas a string crua do array), com chaves exatas:
                - "revista_nome": Nome exato da revista como aparece no catálogo enviado
                - "porcentagem_aderencia": Apenas um número inteiro de 0 a 100 estimando a aderência
                - "justificativa": Uma justificativa de até 3 linhas explicando o porquê da recomendação, escrita EXATAMENTE no mesmo idioma em que o resumo do usuário foi enviado.
                """
                
                try:
                    url_api = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key_ativa}"
                    payload = {
                        "contents": [{"parts": [{"text": prompt_ia}]}],
                        "generationConfig": {"responseMimeType": "application/json"}
                    }
                    headers = {"Content-Type": "application/json"}
                    
                    response = requests.post(url_api, json=payload, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        dados_resposta = response.json()
                        texto_resposta = dados_resposta["candidates"][0]["content"]["parts"][0]["text"].strip()
                        
                        # Tratamento seguro caso venha markdown de bloco JSON do Gemini
                        if texto_resposta.startswith("```"):
                            texto_resposta = re.sub(r'^```(?:json)?\n|```$', '', texto_resposta, flags=re.MULTILINE).strip()
                        
                        # Extrai o array JSON via regex se houver texto ao redor
                        match = re.search(r'\[\s*\{.*\}\s*\]', texto_resposta, re.DOTALL)
                        if match:
                            texto_resposta = match.group(0)
                        
                        st.session_state.recomendacoes = json.loads(texto_resposta)
                    else:
                        st.session_state.erro_ia = f"API retornou status {response.status_code}: {response.text}"
                except Exception as ex:
                    st.session_state.erro_ia = str(ex)
            
            # Limpa o indicador de progresso do DOM virtual
            status_container.empty()
            
            # Recarrega a página de forma limpa para exibir os resultados fora do fluxo do botão
            st.rerun()

    # RENDERIZAÇÃO ESTÁVEL DOS RESULTADOS (Lidos do st.session_state, fora do condicional do st.button)
    if st.session_state.get("aviso_filtro"):
        st.warning("⚠️ Nenhum periódico no catálogo atende aos filtros de Grande Área e Indexador selecionados. Por favor, ajuste os filtros.")
    elif st.session_state.get("erro_ia"):
        st.error(t['ia_erro'])
        st.caption(f"Detalhes técnicos do erro: {st.session_state.erro_ia}")
    elif st.session_state.get("recomendacoes") is not None:
        st.success(t['ia_sucesso'])
        
        for rec in st.session_state.recomendacoes:
            # Busca segura no df original usando a coluna index 0 para o nome
            registro_revista = df_original[df_original[df_original.columns[0]] == rec["revista_nome"]]
            
            homepage = ""
            issn = "N/A"
            indexador = "N/A"
            quartil = "N/A"
            sjr = "N/A"
            
            if not registro_revista.empty:
                # 1. Garante que os valores existam de forma segura antes de converter para string
                try:
                    issn = str(registro_revista.iloc[0].get("ISSN", "-"))
                    indexador = str(registro_revista.iloc[0].get("Indexador", "-"))
                    quartil = str(registro_revista.iloc[0].get("Quartil JCR", "-"))
                    sjr = str(registro_revista.iloc[0].get("SJR", "-"))
                    homepage = str(registro_revista.iloc[0].get("Homepage", ""))
                except Exception:
                    issn, indexador, quartil, sjr, homepage = "-", "-", "-", "-", ""
            
                # 2. Renderização de card para cada recomendação (até 10 dinâmicas)
                with st.container(border=True):
                    col_info, col_link = st.columns([3, 1])
                    
                    with col_info:
                        st.markdown(f"### {rec['revista_nome']}")
                        st.caption(f"**ISSN:** {issn} | **Indexador:** {indexador} | **Quartil:** {quartil} | **SJR:** {sjr}")
                        st.markdown(f"🎯 **{t['ia_card_aderencia']}** `{rec['porcentagem_aderencia']}%`")
                        st.markdown(f"💡 **{t['ia_card_motivo']}** {rec['justificativa']}")
                        
                        # SE HOUVER UM st.dataframe() ESCONDIDO AQUI PARA MOSTRAR OS DADOS COMPLETOS:
                        # Envolva-o SEMPRE em um validador de tamanho para não quebrar o Arrow
                        if len(registro_revista) > 0:
                            st.dataframe(registro_revista, hide_index=True, **kwargs_largura)
                    
                    with col_link:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if homepage and homepage not in ["nan", "-", "None", ""]:
                            st.link_button(t['ia_card_site'], homepage, type="primary", **kwargs_largura)
                        else:
                            st.info(t['ia_card_sem_site'])
            else:
                # Caso a IA recomende um nome de revista que sofreu uma variação de string e não casou no CSV
                with st.container(border=True):
                    st.markdown(f"### {rec['revista_nome']}")
                    st.caption("⚠️ *Periódico sugerido pela IA, mas metadados detalhados não localizados na base local.*")
                    st.markdown(f"🎯 **{t['ia_card_aderencia']}** `{rec['porcentagem_aderencia']}%`")
                    st.markdown(f"💡 **{t['ia_card_motivo']}** {rec['justificativa']}")