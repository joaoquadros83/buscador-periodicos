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
import time
import hashlib
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
# 1. Função para inicializar o Firebase com segurança e cache
@st.cache_resource
def inicializar_firebase():
    # Converte os segredos do Streamlit para um dicionário Python normal
    firebase_info = dict(st.secrets["firebase"])
    
    # Corrige problemas comuns de escape com a chave privada no Streamlit Cloud
    firebase_info["private_key"] = firebase_info["private_key"].replace("\\n", "\n")
    
    # Inicializa o app se ele já não estiver ativo
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_info)
        firebase_admin.initialize_app(cred)
        
    return firestore.client()
# Inicializa o cliente do Firestore globalmente se os segredos estiverem presentes
db = None
try:
    if "firebase" in st.secrets:
        db = inicializar_firebase()
except Exception:
    pass
# --- EXEMPLOS DE USO DO FIRESTORE ---
# 2. Criar ou Atualizar dados do usuário (Salvar histórico de busca)
def salvar_historico_usuario(usuario_id, termo_busca):
    # Acessa o documento do usuário na coleção 'usuarios'
    user_ref = db.collection("usuarios").document(usuario_id)
    
    # Cria o documento ou atualiza adicionando a busca ao histórico
    user_ref.set({
        "historico_buscas": firestore.ArrayUnion([termo_busca]),
        "ultimo_acesso": firestore.SERVER_TIMESTAMP
    }, merge=True) # merge=True impede que outros campos sejam apagados ao atualizar
    
    st.success(f"Busca por '{termo_busca}' salva no histórico!")
# 3. Ler dados do usuário
def obter_dados_usuario(usuario_id):
    user_ref = db.collection("usuarios").document(usuario_id)
    doc = user_ref.get()
    
    if doc.exists:
        return doc.to_dict()
    else:
        return None
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
# --- INJEÇÃO DE TEMA DINÂMICO (DIURNO / NOTURNO) ---
if st.session_state.get("dark_mode", False):
    st.markdown("""
        <style>
            /* Altera cores de fundo globais */
            .stApp {
                background-color: #0F172A !important;
                color: #F8FAFC !important;
            }
            /* Sidebar escuro */
            section[data-testid="stSidebar"] {
                background-color: #1E293B !important;
            }
            section[data-testid="stSidebar"] * {
                color: #F8FAFC !important;
            }
            /* Textos e títulos */
            h1, h2, h3, h4, h5, h6, p, span, label, div {
                color: #F8FAFC !important;
            }
            /* Inputs e Selects */
            input, select, textarea {
                background-color: #334155 !important;
                color: #F8FAFC !important;
                border: 1px solid #475569 !important;
            }
            /* Expander e cards */
            div[data-testid="stExpander"] {
                background-color: #1E293B !important;
                border: 1px solid #334155 !important;
            }
            /* Botões secundários */
            button {
                color: #F8FAFC !important;
                background-color: #334155 !important;
                border: 1px solid #475569 !important;
            }
            /* Abas */
            button[data-baseweb="tab"] {
                color: #CBD5E1 !important;
            }
            button[data-baseweb="tab"][aria-selected="true"] {
                color: #38BDF8 !important;
                border-bottom-color: #38BDF8 !important;
            }
        </style>
    """, unsafe_allow_html=True)
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
        "filtros_tit": "#### 🔍 Buscador de Periódicos",
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
        "ia_num_rec": "Quantidade de recomendações desejadas (máx. 20)",
        "ia_btn_buscar": "Analisar e Recomendar",
        "ia_analisando": "A IA está processando o seu resumo e cruzando com o catálogo...",
        "ia_sucesso": "Recomendações geradas com sucesso!",
        "ia_erro": "Erro ao processar com a IA. Verifique se a sua Chave API está correta.",
        "ia_card_motivo": "Por que publicar aqui:",
        "ia_card_aderencia": "Grau de Aderência:",
        "ia_card_site": "🌐 Visitar Homepage Oficial",
        "ia_card_sem_site": "Site indisponível na base",
        "filtro_area": "Grande Área",
        "filtro_indexador": "Indexador",
        "ia_credencial_tit": "🔑 Credencial",
        "ia_como_obter_titulo": "ℹ️ Como obter uma chave gratuita?",
        "ia_como_obter_texto": """
<div style="font-size: 14px; line-height: 1.5; font-family: inherit;">
Esta ferramenta é gratuita. Para usá-la, você precisa de uma chave da API do Google Gemini, também gratuita:<br><br>
1. Acesse <b><a href="https://aistudio.google.com" target="_blank">aistudio.google.com</a></b><br>
2. Faça login com sua conta Google<br>
3. Clique em <b>"Get API Key"</b> → <b>"Create API Key"</b><br>
4. Copie a chave gerada e cole no campo acima<br><br>
<i>A chave gratuita permite centenas de consultas por dia.</i>
</div>
        """,
        "ia_refinar_alvos": "🎯 Refinar Alvos",
        "ia_todos": "Todos",
        "reg_boas_vindas": "### Bem-vindo ao Portal do Pesquisador!",
        "reg_apresentacao": "Esta é uma plataforma científica de alta tecnologia projetada para simplificar a busca e a seleção de periódicos de impacto para sua publicação. Una forças com ciência de dados e IA.",
        "reg_beneficios_tit": "✨ Por que usar o Portal?",
        "reg_beneficio_1_tit": "🔍 Busca Tradicional",
        "reg_beneficio_1_desc": "Filtros por CNPq, Indexadores (Scopus, Web of Science, SciELO, Educ@) e métricas consolidadas.",
        "reg_beneficio_2_tit": "📊 Métricas Unificadas",
        "reg_beneficio_2_desc": "Quartis JCR/SJR, H-Index e atalhos de impacto no Scholar ao seu alcance.",
        "reg_beneficio_3_tit": "🧠 Recomendador IA",
        "reg_beneficio_3_desc": "Recomendador generativo via Gemini 1.5 Flash cruzado com nossa base de periódicos.",
        "reg_formulario_tit": "📝 Registro de Acesso Acadêmico",
        "reg_formulario_desc": "O acesso ao portal é gratuito e aberto a toda a comunidade científica (de estudantes de graduação a pós-doutores). Preencha o cadastro abaixo para liberar o acesso.",
        "reg_nome": "Nome Completo:",
        "reg_email": "E-mail Acadêmico ou Pessoal:",
        "reg_escolaridade": "Titulação:",
        "reg_instituicao": "Instituição de Vínculo:",
        "reg_inst_outra": "Especifique sua Instituição:",
        "reg_area_interesse": "Grande Área de Interesse (Predominante):",
        "reg_btn_enviar": "Registrar e Acessar o Buscador ➔",
        "reg_sucesso": "🎉 Registro concluído com sucesso! Bem-vindo ao Portal do Pesquisador.",
        "reg_erro_campos": "⚠️ Por favor, preencha todos os campos obrigatórios.",
        "reg_lateral_status_bloqueado": "🔒 Cadastro pendente para liberar o buscador.",
        "reg_lateral_status_liberado": "🔓 Acesso Liberado",
        "reg_btn_sair": "Sair",
        "log_email": "E-mail ou Usuário:",
        "log_senha": "Senha:",
        "log_btn_entrar": "Entrar ➔",
        "log_esqueceu": "Esqueceu a senha ou o login? Recupere aqui",
        "rec_titulo": "🔒 Recuperar Acesso",
        "rec_email": "E-mail Cadastrado:",
        "rec_tel": "Telefone Cadastrado:",
        "rec_btn_verificar": "Verificar Informações ➔",
        "rec_btn_redefinir": "Redefinir Senha",
        "rec_nova_senha": "Nova Senha:",
        "rec_conf_senha": "Confirmar Nova Senha:",
        "rec_sucesso": "🎉 Senha redefinida com sucesso! Faça login.",
        "rec_erro_nao_encontrado": "⚠️ E-mail não encontrado em nossos registros.",
        "rec_btn_voltar": "Voltar para o Login",
        "log_btn_google": "Conectar com o Google",
        "log_cadastrar_link": "Não tem uma conta? Cadastre-se aqui!",
        "log_entrar_link": "Já tem uma conta? Faça login aqui!",
        "log_titulo": "🔒 Entrar no Portal",
        "reg_titulo_form": "📝 Criar Conta Acadêmica",
        "reg_nome_sobrenome": "Nome e Sobrenome:",
        "reg_pais": "País:",
        "reg_telefone": "Telefone:",
        "reg_senha": "Senha:",
        "reg_confirmar_senha": "Confirmar Senha:",
        "reg_btn_cadastrar": "Criar Conta e Acessar ➔",
        "reg_erro_senha_diferente": "⚠️ As senhas digitadas não coincidem.",
        "reg_erro_ja_existe": "⚠️ Este e-mail já está cadastrado. Faça login.",
        "log_erro_invalido": "⚠️ E-mail ou senha incorretos.",
        "log_google_sucesso": "🚀 Conectado com o Google! Redirecionando...",
        "areas_trad": {
            "Engenharias": "Engenharias",
            "Linguística, Letras e Artes": "Linguística, Letras e Artes",
            "Ciências Biológicas": "Ciências Biológicas",
            "Ciências Exatas e da Terra": "Ciências Exatas e da Terra",
            "Outras / Não Classificado": "Outras / Não Classificado",
            "Ciências da Saúde": "Ciências da Saúde",
            "Ciências Sociais Aplicadas": "Ciências Sociais Aplicadas",
            "Ciências Agrárias": "Ciências Agrárias",
            "Ciências Humanas": "Ciências Humanas"
        }
    },
    "English": {
        "titulo": "The Researcher's Portal",
        "subtitulo": "Data science applied to high-impact scientific output.",
        "filtros_tit": "#### 🔍 Journal Finder",
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
        "ia_num_rec": "Number of desired recommendations (max. 20)",
        "ia_btn_buscar": "Analyze and Recommend",
        "ia_analisando": "AI is processing your abstract and matching with the catalog...",
        "ia_sucesso": "Recommendations generated successfully!",
        "ia_erro": "Error processing with AI. Check if your API Key is correct.",
        "ia_card_motivo": "Why publish here:",
        "ia_card_aderencia": "Adherence Score:",
        "ia_card_site": "🌐 Visit Official Homepage",
        "ia_card_sem_site": "Website not available in database",
        "filtro_area": "Broad Area",
        "filtro_indexador": "Indexer",
        "ia_credencial_tit": "🔑 Credentials",
        "ia_como_obter_titulo": "ℹ️ How to get a free API key?",
        "ia_como_obter_texto": """
<div style="font-size: 14px; line-height: 1.5; font-family: inherit;">
This tool is free. To use it, you need a Google Gemini API key, which is also free:<br><br>
1. Go to <b><a href="https://aistudio.google.com" target="_blank">aistudio.google.com</a></b><br>
2. Sign in with your Google account<br>
3. Click <b>"Get API Key"</b> → <b>"Create API Key"</b><br>
4. Copy the generated key and paste it into the field above<br><br>
<i>The free key allows hundreds of queries per day.</i>
</div>
        """,
        "ia_refinar_alvos": "🎯 Refine Targets",
        "ia_todos": "All",
        "reg_boas_vindas": "### Welcome to the Researcher's Portal!",
        "reg_apresentacao": "This is a high-tech scientific platform designed to simplify the search and selection of high-impact journals for your publication. Join forces with data science and AI.",
        "reg_beneficios_tit": "✨ Why use the Portal?",
        "reg_beneficio_1_tit": "🔍 Traditional Search",
        "reg_beneficio_1_desc": "Filters by CNPq subareas, indexers (Scopus, Web of Science, SciELO, Educ@), and consolidated metrics.",
        "reg_beneficio_2_tit": "📊 Unified Metrics",
        "reg_beneficio_2_desc": "JCR/SJR quartiles, H-Index, and impact shortcuts on Google Scholar at your fingertips.",
        "reg_beneficio_3_tit": "🧠 AI Recommender",
        "reg_beneficio_3_desc": "Generative recommendations via Gemini 1.5 Flash crossed with our journal database.",
        "reg_formulario_tit": "📝 Academic Access Registration",
        "reg_formulario_desc": "Access to the portal is free and open to the entire scientific community (from undergraduate students to postdocs). Fill out the form below to unlock access.",
        "reg_nome": "Full Name:",
        "reg_email": "Academic or Personal Email:",
        "reg_escolaridade": "Degree:",
        "reg_instituicao": "Affiliated Institution:",
        "reg_inst_outra": "Specify your Institution:",
        "reg_area_interesse": "Major Research Area of Interest:",
        "reg_btn_enviar": "Register and Access the Finder ➔",
        "reg_sucesso": "🎉 Registration completed successfully! Welcome to the Researcher's Portal.",
        "reg_erro_campos": "⚠️ Please fill in all required fields.",
        "reg_lateral_status_bloqueado": "🔒 Registration pending to unlock search.",
        "reg_lateral_status_liberado": "🔓 Access Granted",
        "reg_btn_sair": "Logout",
        "log_email": "Email or Username:",
        "log_senha": "Password:",
        "log_btn_entrar": "Login ➔",
        "log_esqueceu": "Forgot password or login? Recover here",
        "rec_titulo": "🔒 Recover Access",
        "rec_email": "Registered Email:",
        "rec_tel": "Registered Phone:",
        "rec_btn_verificar": "Verify Information ➔",
        "rec_btn_redefinir": "Reset Password",
        "rec_nova_senha": "New Password:",
        "rec_conf_senha": "Confirm New Password:",
        "rec_sucesso": "🎉 Password reset successfully! Please log in.",
        "rec_erro_nao_encontrado": "⚠️ E-mail not found in our records.",
        "rec_btn_voltar": "Back to Login",
        "log_btn_google": "Sign in with Google",
        "log_cadastrar_link": "Don't have an account? Sign up here!",
        "log_entrar_link": "Already have an account? Log in here!",
        "log_titulo": "🔒 Log in to the Portal",
        "reg_titulo_form": "📝 Create Academic Account",
        "reg_nome_sobrenome": "First and Last Name:",
        "reg_pais": "Country:",
        "reg_telefone": "Phone:",
        "reg_senha": "Password:",
        "reg_confirmar_senha": "Confirm Password:",
        "reg_btn_cadastrar": "Create Account and Access ➔",
        "reg_erro_senha_diferente": "⚠️ Passwords do not match.",
        "reg_erro_ja_existe": "⚠️ This email is already registered. Please log in.",
        "log_erro_invalido": "⚠️ Incorrect email or password.",
        "log_google_sucesso": "🚀 Connected with Google! Redirecting...",
        "areas_trad": {
            "Engenharias": "Engineering",
            "Linguística, Letras e Artes": "Linguistics, Literature & Arts",
            "Ciências Biológicas": "Biological Sciences",
            "Ciências Exatas e da Terra": "Exact & Earth Sciences",
            "Outras / Não Classificado": "Others / Unclassified",
            "Ciências da Saúde": "Health Sciences",
            "Ciências Sociais Aplicadas": "Applied Social Sciences",
            "Ciências Agrárias": "Agricultural Sciences",
            "Ciências Humanas": "Human Sciences"
        }
    },
    "Español": {
        "titulo": "Portal del Investigador",
        "subtitulo": "Ciencia de datos aplicada a la producción científica de más alto nivel.",
        "filtros_tit": "#### 🔍 Buscador de Revistas",
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
        "ia_num_rec": "Cantidad de recomendaciones deseadas (máx. 20)",
        "ia_btn_buscar": "Analar y Recomendar",
        "ia_analisando": "La IA está procesando su resumo y cruzándolo con el catálogo...",
        "ia_sucesso": "¡Recomendaciones generadas con éxito!",
        "ia_erro": "Error al procesar con la IA. Verifique que su Clave API sea correcta.",
        "ia_card_motivo": "Por qué publicar aqui:",
        "ia_card_aderencia": "Grado de Adherencia:",
        "ia_card_site": "🌐 Visitar Homepage Oficial",
        "ia_card_sem_site": "Sitio no disponible en la base",
        "filtro_area": "Gran Área",
        "filtro_indexador": "Indexador",
        "ia_credencial_tit": "🔑 Credenciales",
        "ia_como_obter_titulo": "ℹ️ ¿Cómo obtener una clave gratuita?",
        "ia_como_obter_texto": """
<div style="font-size: 14px; line-height: 1.5; font-family: inherit;">
Esta herramienta es gratuita. Para usarla, necesita una clave de API de Google Gemini, también gratuita:<br><br>
1. Acceda a <b><a href="https://aistudio.google.com" target="_blank">aistudio.google.com</a></b><br>
2. Inicie sesión con su cuenta de Google<br>
3. Haga clic en <b>"Get API Key"</b> → <b>"Create API Key"</b><br>
4. Copie la clave generada y péguela en el campo de arriba<br><br>
<i>La clave gratuita permite cientos de consultas al día.</i>
</div>
        """,
        "ia_refinar_alvos": "🎯 Refinar Objetivos",
        "ia_todos": "Todos",
        "reg_boas_vindas": "### ¡Bienvenido al Portal del Investigador!",
        "reg_apresentacao": "Esta es una plataforma científica de alta tecnología diseñada para simplificar la búsqueda y selección de revistas de impacto para su publicación. Una fuerzas con ciencia de datos e IA.",
        "reg_beneficios_tit": "✨ ¿Por qué usar el Portal?",
        "reg_beneficio_1_tit": "🔍 Búsqueda Tradicional",
        "reg_beneficio_1_desc": "Filtros por subáreas del CNPq, indexadores (Scopus, Web of Science, SciELO, Educ@) y métricas consolidadas.",
        "reg_beneficio_2_tit": "📊 Métricas Unificadas",
        "reg_beneficio_2_desc": "Cuartiles JCR/SJR, H-Index y accesos directos de impacto en Scholar a su alcance.",
        "reg_beneficio_3_tit": "🧠 Recomendador IA",
        "reg_beneficio_3_desc": "Recomendaciones generativas a través de Gemini 1.5 Flash cruzadas con nuestra base de revistas.",
        "reg_formulario_tit": "📝 Registro de Acceso Académico",
        "reg_formulario_desc": "El acceso al portal es gratuito y abierto a toda la comunidad científica (desde estudiantes hasta posdoctores). Complete el formulario a continuación para liberar el acceso.",
        "reg_nome": "Nombre Completo:",
        "reg_email": "Correo Electrónico Académico o Personal:",
        "reg_escolaridade": "Titulación:",
        "reg_instituicao": "Institución de Vínculo:",
        "reg_inst_outra": "Especifique su Institución:",
        "reg_area_interesse": "Gran Área de Interés Predominante:",
        "reg_btn_enviar": "Registrarse y Acceder al Buscador ➔",
        "reg_sucesso": "🎉 ¡Registro completado con éxito! Bienvenido al Portal del Investigador.",
        "reg_erro_campos": "⚠️ Por favor, complete todos los campos obligatorios.",
        "reg_lateral_status_bloqueado": "🔒 Registro pendiente para habilitar el buscador.",
        "reg_lateral_status_liberado": "🔓 Acceso Concedido",
        "reg_btn_sair": "Salir",
        "log_email": "Correo o Usuario:",
        "log_senha": "Contraseña:",
        "log_btn_entrar": "Ingresar ➔",
        "log_esqueceu": "¿Olvidó su contraseña o usuario? Recupere aquí",
        "rec_titulo": "🔒 Recuperar Acceso",
        "rec_email": "Correo Registrado:",
        "rec_tel": "Teléfono Registrado:",
        "rec_btn_verificar": "Verificar Información ➔",
        "rec_btn_redefinir": "Restablecer Contraseña",
        "rec_nova_senha": "Nueva Contraseña:",
        "rec_conf_senha": "Confirmar Nueva Contraseña:",
        "rec_sucesso": "🎉 ¡Contraseña restablecida con éxito! Inicie sesión.",
        "rec_erro_nao_encontrado": "⚠️ Correo electrónico no encontrado en nuestros registros.",
        "rec_btn_voltar": "Volver al Inicio",
        "log_btn_google": "Conectar con Google",
        "log_cadastrar_link": "¿No tienes una cuenta? ¡Regístrate aquí!",
        "log_entrar_link": "¿Ya tienes una cuenta? ¡Inicia sesión aquí!",
        "log_titulo": "🔒 Iniciar Sesión en el Portal",
        "reg_titulo_form": "📝 Crear Cuenta Académica",
        "reg_nome_sobrenome": "Nombre y Apellido:",
        "reg_pais": "País:",
        "reg_telefone": "Teléfono:",
        "reg_senha": "Contraseña:",
        "reg_confirmar_senha": "Confirmar Contraseña:",
        "reg_btn_cadastrar": "Crear Cuenta y Acceder ➔",
        "reg_erro_senha_diferente": "⚠️ Las contraseñas no coinciden.",
        "reg_erro_ja_existe": "⚠️ Este correo ya está registrado. Inicie sesión.",
        "log_erro_invalido": "⚠️ Correo o contraseña incorrectos.",
        "log_google_sucesso": "🚀 ¡Conectado con Google! Redireccionando...",
        "areas_trad": {
            "Engenharias": "Ingenierías",
            "Linguística, Letras e Artes": "Lingüística, Letras y Artes",
            "Ciências Biológicas": "Ciencias Biológicas",
            "Ciências Exatas e da Terra": "Ciencias Exactas y de la Tierra",
            "Outras / Não Classificado": "Otras / No Clasificado",
            "Ciências da Saúde": "Ciencias de la Salud",
            "Ciências Sociais Aplicadas": "Ciencias Sociales Aplicadas",
            "Ciências Agrárias": "Ciencias Agrarias",
            "Ciências Humanas": "Ciencias Humanas"
        }
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
        font-size: 1.1rem !important;
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
        font-size: 3.4rem !important;
        font-weight: 800 !important;
        margin-bottom: 0px !important;
        letter-spacing: -0.5px;
        line-height: 1.15 !important;
    }
    .premium-subtitle {
        color: #FFFFFF !important;
        font-size: 1.55rem !important; 
        max-width: 950px;              
        line-height: 1.4;
        margin-top: 0px !important;
    }
    .premium-text-block {
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 10px;
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
                    df[col] = df[col].fillna("-").astype(str).str.strip()
                    df[col] = df[col].replace(["None", "none", "NONE", "nan", "NaN", "null", ""], "-")
            
            # Garante a existência da coluna Homepage
            if "Homepage" not in df.columns:
                df["Homepage"] = "-"
            else:
                df["Homepage"] = df["Homepage"].fillna("-").astype(str).str.strip()
                df["Homepage"] = df["Homepage"].replace(["None", "none", "NONE", "nan", "NaN", "null", ""], "-")
            col_titulo = df.columns[0]
            
            # Cria a chave de agrupamento normalizada (em minúsculas) para ignorar diferenças de caixa
            df["titulo_norm"] = df[col_titulo].astype(str).str.lower().str.strip()
            if "ISSN" in df.columns:
                df["ISSN"] = df["ISSN"].astype(str).str.strip()
            
            # Funções de agregação personalizadas
            def agg_indexadores(series):
                vals = sorted(list(set([str(val).strip() for val in series if str(val).strip() not in ["-", "", "None", "nan"]])))
                return ", ".join(vals) if vals else "-"
                
            def agg_primeiro_valido(series):
                for val in series:
                    val_str = str(val).strip()
                    if val_str not in ["-", "", "None", "nan"]:
                        return val_str
                return "-"
                
            def agg_titulo(series):
                candidatos = [str(x).strip() for x in series if str(x).strip() not in ["-", "", "None", "nan"]]
                if not candidatos:
                    return "-"
                # Prefere títulos com letras misturadas (Title Case) sobre ALL CAPS
                suaves = [c for c in candidatos if not c.isupper() and any(ch.isupper() for ch in c)]
                if suaves:
                    return suaves[0]
                sem_caps = [c for c in candidatos if not c.isupper()]
                if sem_caps:
                    return sem_caps[0]
                return candidatos[0]
            def agg_max_numerico(series):
                nums = pd.to_numeric(series, errors='coerce').dropna()
                return nums.max() if not nums.empty else 0.0
                
            agg_dict = {}
            for col in df.columns:
                if col == "titulo_norm":
                    continue
                if col == col_titulo:
                    agg_dict[col] = agg_titulo
                elif col == "Indexador":
                    agg_dict[col] = agg_indexadores
                elif col in ['SJR', 'JIF', 'h-index', 'H index']:
                    agg_dict[col] = agg_max_numerico
                else:
                    agg_dict[col] = agg_primeiro_valido
                    
            # Agrupa pelo título normalizado
            df = df.groupby("titulo_norm", as_index=False).agg(agg_dict)
            df = df.drop(columns=["titulo_norm"])
            
            return df, nome_arquivo
        except Exception as e:
            st.error(f"⚠️ Erro ao processar a base de dados '{nome_arquivo}'. Detalhes: {e}")
            st.stop()
    else:
        st.error("⚠️ Base de dados não encontrada. O arquivo 'dados.csv' não foi localizado na raiz do projeto. Por favor, certifique-se de fazer o download do arquivo no repositório GitHub correspondente.")
        st.stop()
df_original, arquivo_usado = carregar_dados()
# --- 5. MONTAGEM DA SIDEBAR (LINKS E COMPONENTES) ---
# Inicializa o estado de registro se não existir
if "registrado" not in st.session_state:
    st.session_state.registrado = False
if "modo_login" not in st.session_state:
    st.session_state.modo_login = True
if "modo_recuperacao" not in st.session_state:
    st.session_state.modo_recuperacao = False
if "usuario_recuperado_email" not in st.session_state:
    st.session_state.usuario_recuperado_email = ""
if "email_usuario" not in st.session_state:
    st.session_state.email_usuario = ""
if "nome_usuario" not in st.session_state:
    st.session_state.nome_usuario = ""
if "acessos_usuario" not in st.session_state:
    st.session_state.acessos_usuario = 0
if "login_via_google" not in st.session_state:
    st.session_state.login_via_google = False
if "solicitar_email_google" not in st.session_state:
    st.session_state.solicitar_email_google = False
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "abrir_configuracoes" not in st.session_state:
    st.session_state.abrir_configuracoes = False
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
# Exibe o status de acesso na barra lateral
if st.session_state.registrado:
    nome_usr_exibir = st.session_state.get("nome_usuario", "Usuário")
    email_usr_exibir = st.session_state.get("email_usuario", "")
    acessos_usr = st.session_state.get("acessos_usuario", 1)
    
    # Se for login via Google, exibe o e-mail do usuário na mensagem de boas-vindas
    usr_identificador = email_usr_exibir if st.session_state.get("login_via_google", False) else nome_usr_exibir
    
    # Determina o texto de boas-vindas com base no número de acessos
    if acessos_usr <= 1:
        status_texto = f"Seja bem-vindo(a), {usr_identificador}"
    else:
        status_texto = f"Bem-vindo(a) de volta, {usr_identificador}"
        
    if st.session_state.get("is_admin", False):
        status_texto = f"🔑 Admin: {status_texto}"
        bg_cor = "#0F172A"
    else:
        bg_cor = "#10B981"
        
    # Colunas para exibir a mensagem e o ícone de engrenagem lado a lado
    col_status_box, col_config_btn = st.sidebar.columns([3.8, 1.2])
    with col_status_box:
        st.markdown(f"""
            <div style="background-color: {bg_cor}; color: white; padding: 10px 8px; border-radius: 8px; text-align: center; font-weight: 600; font-size: 0.82rem; line-height: 1.3; min-height: 38px; display: flex; align-items: center; justify-content: center;">
                {status_texto}
            </div>
        """, unsafe_allow_html=True)
    with col_config_btn:
        if st.button("⚙️", key="btn_config_gear_sidebar", help="Configurações e Acesso", use_container_width=True):
    # Caixa de boas-vindas
    st.markdown(f"""
        <div style="background-color: {bg_cor}; color: white; padding: 10px 8px; border-radius: 8px; text-align: center; font-weight: 600; font-size: 0.82rem; line-height: 1.3; margin-bottom: 8px;">
            {status_texto}
        </div>
    """, unsafe_allow_html=True)
    
    # Colunas para exibir botões de Sair e Configurações lado a lado
    col_sair, col_config = st.sidebar.columns([1, 1])
    with col_sair:
        if st.button("🚪 Sair", key="btn_sair_sidebar", help="Encerrar sessão", use_container_width=True):
            st.session_state.registrado = False
            st.session_state.email_usuario = ""
            st.session_state.nome_usuario = ""
            st.session_state.acessos_usuario = 0
            st.session_state.login_via_google = False
            st.session_state.solicitar_email_google = False
            st.session_state.abrir_configuracoes = False
            st.session_state.is_admin = False
            st.rerun()
    with col_config:
        if st.button("⚙️ Configs", key="btn_config_gear_sidebar", help="Configurações", use_container_width=True):
            st.session_state.abrir_configuracoes = not st.session_state.get("abrir_configuracoes", False)
            st.rerun()
                st.info(f"Link: `{url_portal}`")
                st.success("Link copiado para exibição!")
    elif "🚪 Desconectar da Plataforma" in opc_config:
        st.subheader("🚪 Desconectar da Plataforma")
        st.write("Deseja realmente encerrar sua sessão e desconectar do buscador?")
        if st.button("Sim, Sair da Plataforma", type="primary"):
            st.session_state.registrado = False
            st.session_state.email_usuario = ""
            st.session_state.nome_usuario = ""
            st.session_state.acessos_usuario = 0
            st.session_state.login_via_google = False
            st.session_state.solicitar_email_google = False
            st.session_state.abrir_configuracoes = False
            st.session_state.is_admin = False
            st.rerun()
            
    st.stop()
            )
        else:
            st.info("Nenhum usuário cadastrado encontrado na base.")
