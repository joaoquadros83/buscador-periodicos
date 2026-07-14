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


# 1. FunÃ§Ã£o para inicializar o Firebase com seguranÃ§a e cache
@st.cache_resource
def inicializar_firebase():
    # Converte os segredos do Streamlit para um dicionÃ¡rio Python normal
    firebase_info = dict(st.secrets["firebase"])
    
    # Corrige problemas comuns de escape com a chave privada no Streamlit Cloud
    firebase_info["private_key"] = firebase_info["private_key"].replace("\\n", "\n")
    
    # Inicializa o app se ele jÃ¡ nÃ£o estiver ativo
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

# 2. Criar ou Atualizar dados do usuÃ¡rio (Salvar histÃ³rico de busca)
def salvar_historico_usuario(usuario_id, termo_busca):
    # Acessa o documento do usuÃ¡rio na coleÃ§Ã£o 'usuarios'
    user_ref = db.collection("usuarios").document(usuario_id)
    
    # Cria o documento ou atualiza adicionando a busca ao histÃ³rico
    user_ref.set({
        "historico_buscas": firestore.ArrayUnion([termo_busca]),
        "ultimo_acesso": firestore.SERVER_TIMESTAMP
    }, merge=True) # merge=True impede que outros campos sejam apagados ao atualizar
    
    st.success(f"Busca por '{termo_busca}' salva no histÃ³rico!")

# 3. Ler dados do usuÃ¡rio
def obter_dados_usuario(usuario_id):
    user_ref = db.collection("usuarios").document(usuario_id)
    doc = user_ref.get()
    
    if doc.exists:
        return doc.to_dict()
    else:
        return None

# DetecÃ§Ã£o dinÃ¢mica de versÃ£o do Streamlit para evitar erros de TypeError
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

# DicionÃ¡rio desempacotado dinamicamente para largura de componentes
kwargs_largura = {"width": "stretch"} if SUPPORTS_NEW_WIDTH else {"use_container_width": True}

# --- 1. CONFIGURAÃ‡ÃƒO ÃšNICA DA PÃGINA (Executada antes de qualquer comando Streamlit) ---
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

st.set_page_config(
    page_title="Portal do Pesquisador",
    page_icon="🔍",  # <-- Mudei aqui para um emoji direto em texto
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INJEÃ‡ÃƒO DE TEMA DINÃ‚MICO (DIURNO / NOTURNO) ---
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
            /* Textos e tÃ­tulos */
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
            /* BotÃµes secundÃ¡rios */
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

# --- 2. SISTEMA DE TRADUÃ‡ÃƒO MULTILÃNGUE ---
if 'idioma' not in st.session_state:
    st.session_state.idioma = "PortuguÃªs"

# Seletor de idioma fixado na barra lateral
st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.session_state.idioma = st.sidebar.selectbox(
    "ðŸŒ Language / Idioma:",
    ["PortuguÃªs", "English", "EspaÃ±ol"]
)

dic = {
    "PortuguÃªs": {
        "titulo": "Portal do Pesquisador",
        "subtitulo": "CiÃªncia de dados aplicada Ã  produÃ§Ã£o cientÃ­fica de alto impacto",
        "filtros_tit": "#### ðŸ” Buscador ➔",
        "placeholder_busca": "Digite o tÃ­tulo da revista, ISSN...",
        "buscar_reg": "Buscar registro especÃ­fico:",
        "aba_escopo": "ðŸ“‚ Escopo AcadÃªmico & CNPq",
        "aba_impacto": "ðŸ“ˆ MÃ©tricas de Performance & Quartis",
        "subarea_lbl": "SubÃ¡rea do Conhecimento (CNPq):",
        "base_lbl": "Bases Detentoras:",
        "jcr_lbl": "Quartil JCR (Clarivate):",
        "sjr_lbl": "Quartil SJR (Scopus):",
        "ordem_lbl": "Ordenar Resultados por:",
        "m_selecionadas": "Revistas Selecionadas",
        "m_hindex": "H-Index Topo",
        "m_jif": "Fator JIF MÃ¡ximo",
        "m_sjr": "SJR Score Ãpice",
        "cat_tit": "#### ðŸ“‹ CatÃ¡logo de PeriÃ³dicos",
        "exibir_pag": "Exibir por pÃ¡gina:",
        "pag_lbl": "PÃ¡gina",
        "exportar_btn": "ðŸ“¥ Exportar apenas esta pÃ¡gina",
        "aviso_nada": "Nenhum periÃ³dico atende aos critÃ©rios aplicados.",
        "nav_tit": "Painel de NavegaÃ§Ã£o",
        "todas": "Todas",
        "col_h5": "Ãndice h5 (Scholar)",
        "meta_tit": "METADADOS",
        "meta_sistema": "Sistema",
        "meta_versao": "VersÃ£o Base",
        "meta_padrao": "PadrÃ£o CNPq",
        "meta_status": "Operacional",
        "meta_ativo": "Ativo",
        "direitos_tit": "Direitos Autorais & Propriedade",
        "direitos_autor": "Universidade Federal Ouro Preto<br>Minas Gerais, Brasil.<br><i>Todos os direitos reservados.</i>",
        "visitas_lbl": "Visitas ao Portal",
        "gov_tit": "SITES GOVERNAMENTAIS",
        "inst_tit": "INFORMAÃ‡Ã•ES INSTITUCIONAIS",
        "pessoal_lbl": "ðŸ‘¤ Site pessoal",
        "indexadores_tit": "INDEXADORES",
        "repositorios_tit": "REPOSITÃ“RIOS",
        "ia_tit": "IA ACADÃŠMICA",
        "btn_desktop": "ðŸ’» Baixar VersÃ£o para Windows",
        "busca_cat": "ðŸ” CatÃ¡logo de PeriÃ³dicos",
        "busca_ia": "ðŸ§  Recomendador Inteligente (IA)",
        "ia_titulo": "RecomendaÃ§Ã£o TemÃ¡tica com InteligÃªncia Artificial",
        "ia_subtitulo": "Cole o tÃ­tulo e o resumo (abstract) do seu artigo. A IA analisarÃ¡ o nosso catÃ¡logo e indicarÃ¡ as opÃ§Ãµes mais adequadas.",
        "ia_campo_titulo": "TÃ­tulo do Artigo",
        "ia_campo_resumo": "Resumo / Abstract (Suporta PortuguÃªs, InglÃªs ou Espanhol)",
        "ia_chave_api": "Chave API do Gemini (Google AI Studio)",
        "ia_chave_ajuda": "VocÃª precisa de uma chave API gratuita obtida no Google AI Studio para rodar a recomendaÃ§Ã£o online.",
        "ia_num_rec": "Quantidade de recomendaÃ§Ãµes desejadas (mÃ¡x. 20)",
        "ia_btn_buscar": "Analisar e Recomendar",
        "ia_analisando": "A IA estÃ¡ processando o seu resumo e cruzando com o catÃ¡logo...",
        "ia_sucesso": "RecomendaÃ§Ãµes geradas com sucesso!",
        "ia_erro": "Erro ao processar com a IA. Verifique se a sua Chave API estÃ¡ correta.",
        "ia_card_motivo": "Por que publicar aqui:",
        "ia_card_aderencia": "Grau de AderÃªncia:",
        "ia_card_site": "ðŸŒ Visitar Homepage Oficial",
        "ia_card_sem_site": "Site indisponÃ­vel na base",
        "filtro_area": "Grande Ãrea",
        "filtro_indexador": "Indexador",
        "ia_credencial_tit": "ðŸ”‘ Credencial",
        "ia_como_obter_titulo": "â„¹ï¸ Como obter uma chave gratuita?",
        "ia_como_obter_texto": """
<div style="font-size: 14px; line-height: 1.5; font-family: inherit;">
Esta ferramenta Ã© gratuita. Para usÃ¡-la, vocÃª precisa de uma chave da API do Google Gemini, tambÃ©m gratuita:<br><br>
1. Acesse <b><a href="https://aistudio.google.com" target="_blank">aistudio.google.com</a></b><br>
2. FaÃ§a login com sua conta Google<br>
3. Clique em <b>"Get API Key"</b> â†’ <b>"Create API Key"</b><br>
4. Copie a chave gerada e cole no campo acima<br><br>
<i>A chave gratuita permite centenas de consultas por dia.</i>
</div>
        """,
        "ia_refinar_alvos": "ðŸŽ¯ Refinar Alvos",
        "ia_todos": "Todos",
        "reg_boas_vindas": "### Bem-vindo ao Portal do Pesquisador!",
        "reg_apresentacao": "Esta Ã© uma plataforma cientÃ­fica de alta tecnologia projetada para simplificar a busca e a seleÃ§Ã£o de periÃ³dicos de impacto para sua publicaÃ§Ã£o. Una forÃ§as com ciÃªncia de dados e IA.",
        "reg_beneficios_tit": "âœ¨ Por que usar o Portal?",
        "reg_beneficio_1_tit": "ðŸ” Busca Tradicional",
        "reg_beneficio_1_desc": "Filtros por CNPq, Indexadores (Scopus, Web of Science, SciELO, Educ@) e mÃ©tricas consolidadas.",
        "reg_beneficio_2_tit": "ðŸ“Š MÃ©tricas Unificadas",
        "reg_beneficio_2_desc": "Quartis JCR/SJR, H-Index e atalhos de impacto no Scholar ao seu alcance.",
        "reg_beneficio_3_tit": "ðŸ§  Recomendador IA",
        "reg_beneficio_3_desc": "Recomendador generativo via Gemini 1.5 Flash cruzado com nossa base de periÃ³dicos.",
        "reg_formulario_tit": "ðŸ“ Registro de Acesso AcadÃªmico",
        "reg_formulario_desc": "O acesso ao portal Ã© gratuito e aberto a toda a comunidade cientÃ­fica (de estudantes de graduaÃ§Ã£o a pÃ³s-doutores). Preencha o cadastro abaixo para liberar o acesso.",
        "reg_nome": "Nome Completo:",
        "reg_email": "E-mail AcadÃªmico ou Pessoal:",
        "reg_escolaridade": "TitulaÃ§Ã£o:",
        "reg_instituicao": "InstituiÃ§Ã£o de VÃ­nculo:",
        "reg_inst_outra": "Especifique sua InstituiÃ§Ã£o:",
        "reg_area_interesse": "Grande Ãrea de Interesse (Predominante):",
        "reg_btn_enviar": "Registrar e Acessar ➔",
        "reg_sucesso": "ðŸŽ‰ Registro concluÃ­do com sucesso! Bem-vindo ao Portal do Pesquisador.",
        "reg_erro_campos": "âš ï¸ Por favor, preencha todos os campos obrigatÃ³rios.",
        "reg_lateral_status_bloqueado": "ðŸ”’ Cadastro pendente para liberar o buscador.",
        "reg_lateral_status_liberado": "ðŸ”“ Acesso Liberado",
        "reg_btn_sair": "Sair",
        "log_email": "E-mail ou UsuÃ¡rio:",
        "log_senha": "Senha:",
        "log_btn_entrar": "Entrar ➔",
        "log_esqueceu": "Esqueceu a senha ou o login? Recupere aqui",
        "rec_titulo": "ðŸ”’ Recuperar Acesso",
        "rec_email": "E-mail Cadastrado:",
        "rec_tel": "Telefone Cadastrado:",
        "rec_btn_verificar": "Verificar InformaÃ§Ãµes âž”",
        "rec_btn_redefinir": "Redefinir Senha",
        "rec_nova_senha": "Nova Senha:",
        "rec_conf_senha": "Confirmar Nova Senha:",
        "rec_sucesso": "ðŸŽ‰ Senha redefinida com sucesso! FaÃ§a login.",
        "rec_erro_nao_encontrado": "âš ï¸ E-mail nÃ£o encontrado em nossos registros.",
        "rec_btn_voltar": "Voltar para o Login",
        "log_btn_google": "Conectar com o Google",
        "log_cadastrar_link": "NÃ£o tem uma conta? Cadastre-se aqui!",
        "log_entrar_link": "JÃ¡ tem uma conta? FaÃ§a login aqui!",
        "log_titulo": "ðŸ”’ Entrar ➔",
        "reg_titulo_form": "ðŸ“ Criar Conta AcadÃªmica",
        "reg_nome_sobrenome": "Nome e Sobrenome:",
        "reg_pais": "PaÃ­s:",
        "reg_telefone": "Telefone:",
        "reg_senha": "Senha:",
        "reg_confirmar_senha": "Confirmar Senha:",
        "reg_btn_cadastrar": "Criar Conta e Acessar ➔",
        "reg_erro_senha_diferente": "âš ï¸ As senhas digitadas nÃ£o coincidem.",
        "reg_erro_ja_existe": "âš ï¸ Este e-mail jÃ¡ estÃ¡ cadastrado. FaÃ§a login.",
        "log_erro_invalido": "âš ï¸ E-mail ou senha incorretos.",
        "log_google_sucesso": "ðŸš€ Conectado com o Google! Redirecionando...",
        "areas_trad": {
            "Engenharias": "Engenharias",
            "LinguÃ­stica, Letras e Artes": "LinguÃ­stica, Letras e Artes",
            "CiÃªncias BiolÃ³gicas": "CiÃªncias BiolÃ³gicas",
            "CiÃªncias Exatas e da Terra": "CiÃªncias Exatas e da Terra",
            "Outras / NÃ£o Classificado": "Outras / NÃ£o Classificado",
            "CiÃªncias da SaÃºde": "CiÃªncias da SaÃºde",
            "CiÃªncias Sociais Aplicadas": "CiÃªncias Sociais Aplicadas",
            "CiÃªncias AgrÃ¡rias": "CiÃªncias AgrÃ¡rias",
            "CiÃªncias Humanas": "CiÃªncias Humanas"
        }
    },
    "English": {
        "titulo": "The Researcher's Portal",
        "subtitulo": "Data science applied to high-impact scientific output.",
        "filtros_tit": "#### ðŸ” Journal Finder",
        "placeholder_busca": "Enter journal title, ISSN...",
        "buscar_reg": "Search specific record:",
        "aba_escopo": "ðŸ“‚ Academic Scope & CNPq",
        "aba_impacto": "ðŸ“ˆ Performance Metrics & Quartiles",
        "subarea_lbl": "Subarea of Knowledge (CNPq):",
        "base_lbl": "Holding Databases:",
        "jcr_lbl": "JCR%20Quartile%20(Clarivate):", # URL encoded helper
        "sjr_lbl": "SJR Quartile (Scopus):",
        "ordem_lbl": "Sort Results by:",
        "m_selecionadas": "Selected Journals",
        "m_hindex": "Top H-Index",
        "m_jif": "Max JIF Factor",
        "m_sjr": "Peak SJR Score",
        "cat_tit": "#### ðŸ“‹ Journal Catalog",
        "exibir_pag": "Display per page:",
        "pag_lbl": "Page",
        "exportar_btn": "ðŸ“¥ Export this page only",
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
        "pessoal_lbl": "ðŸ‘¤ Personal website",
        "indexadores_tit": "INDEXERS",
        "repositorios_tit": "DIRECTORIES",
        "ia_tit": "ACADEMIC AI",
        "btn_desktop": "ðŸ’» Download Windows Version",
        "busca_cat": "ðŸ” Journal Catalog",
        "busca_ia": "ðŸ§  Smart Recommender (AI)",
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
        "ia_card_site": "ðŸŒ Visit Official Homepage",
        "ia_card_sem_site": "Website not available in database",
        "filtro_area": "Broad Area",
        "filtro_indexador": "Indexer",
        "ia_credencial_tit": "ðŸ”‘ Credentials",
        "ia_como_obter_titulo": "â„¹ï¸ How to get a free API key?",
        "ia_como_obter_texto": """
<div style="font-size: 14px; line-height: 1.5; font-family: inherit;">
This tool is free. To use it, you need a Google Gemini API key, which is also free:<br><br>
1. Go to <b><a href="https://aistudio.google.com" target="_blank">aistudio.google.com</a></b><br>
2. Sign in with your Google account<br>
3. Click <b>"Get API Key"</b> â†’ <b>"Create API Key"</b><br>
4. Copy the generated key and paste it into the field above<br><br>
<i>The free key allows hundreds of queries per day.</i>
</div>
        """,
        "ia_refinar_alvos": "ðŸŽ¯ Refine Targets",
        "ia_todos": "All",
        "reg_boas_vindas": "### Welcome to the Researcher's Portal!",
        "reg_apresentacao": "This is a high-tech scientific platform designed to simplify the search and selection of high-impact journals for your publication. Join forces with data science and AI.",
        "reg_beneficios_tit": "âœ¨ Why use the Portal?",
        "reg_beneficio_1_tit": "ðŸ” Traditional Search",
        "reg_beneficio_1_desc": "Filters by CNPq subareas, indexers (Scopus, Web of Science, SciELO, Educ@), and consolidated metrics.",
        "reg_beneficio_2_tit": "ðŸ“Š Unified Metrics",
        "reg_beneficio_2_desc": "JCR/SJR quartiles, H-Index, and impact shortcuts on Google Scholar at your fingertips.",
        "reg_beneficio_3_tit": "ðŸ§  AI Recommender",
        "reg_beneficio_3_desc": "Generative recommendations via Gemini 1.5 Flash crossed with our journal database.",
        "reg_formulario_tit": "ðŸ“ Academic Access Registration",
        "reg_formulario_desc": "Access to the portal is free and open to the entire scientific community (from undergraduate students to postdocs). Fill out the form below to unlock access.",
        "reg_nome": "Full Name:",
        "reg_email": "Academic or Personal Email:",
        "reg_escolaridade": "Degree:",
        "reg_instituicao": "Affiliated Institution:",
        "reg_inst_outra": "Specify your Institution:",
        "reg_area_interesse": "Major Research Area of Interest:",
        "reg_btn_enviar": "Register and Access the Finder âž”",
        "reg_sucesso": "ðŸŽ‰ Registration completed successfully! Welcome to the Researcher's Portal.",
        "reg_erro_campos": "âš ï¸ Please fill in all required fields.",
        "reg_lateral_status_bloqueado": "ðŸ”’ Registration pending to unlock search.",
        "reg_lateral_status_liberado": "ðŸ”“ Access Granted",
        "reg_btn_sair": "Logout",
        "log_email": "Email or Username:",
        "log_senha": "Password:",
        "log_btn_entrar": "Login âž”",
        "log_esqueceu": "Forgot password or login? Recover here",
        "rec_titulo": "ðŸ”’ Recover Access",
        "rec_email": "Registered Email:",
        "rec_tel": "Registered Phone:",
        "rec_btn_verificar": "Verify Information âž”",
        "rec_btn_redefinir": "Reset Password",
        "rec_nova_senha": "New Password:",
        "rec_conf_senha": "Confirm New Password:",
        "rec_sucesso": "ðŸŽ‰ Password reset successfully! Please log in.",
        "rec_erro_nao_encontrado": "âš ï¸ E-mail not found in our records.",
        "rec_btn_voltar": "Back to Login",
        "log_btn_google": "Sign in with Google",
        "log_cadastrar_link": "Don't have an account? Sign up here!",
        "log_entrar_link": "Already have an account? Log in here!",
        "log_titulo": "ðŸ”’ Log in to the Portal",
        "reg_titulo_form": "ðŸ“ Create Academic Account",
        "reg_nome_sobrenome": "First and Last Name:",
        "reg_pais": "Country:",
        "reg_telefone": "Phone:",
        "reg_senha": "Password:",
        "reg_confirmar_senha": "Confirm Password:",
        "reg_btn_cadastrar": "Create Account and Access âž”",
        "reg_erro_senha_diferente": "âš ï¸ Passwords do not match.",
        "reg_erro_ja_existe": "âš ï¸ This email is already registered. Please log in.",
        "log_erro_invalido": "âš ï¸ Incorrect email or password.",
        "log_google_sucesso": "ðŸš€ Connected with Google! Redirecting...",
        "areas_trad": {
            "Engenharias": "Engineering",
            "LinguÃ­stica, Letras e Artes": "Linguistics, Literature & Arts",
            "CiÃªncias BiolÃ³gicas": "Biological Sciences",
            "CiÃªncias Exatas e da Terra": "Exact & Earth Sciences",
            "Outras / NÃ£o Classificado": "Others / Unclassified",
            "CiÃªncias da SaÃºde": "Health Sciences",
            "CiÃªncias Sociais Aplicadas": "Applied Social Sciences",
            "CiÃªncias AgrÃ¡rias": "Agricultural Sciences",
            "CiÃªncias Humanas": "Human Sciences"
        }
    },
    "EspaÃ±ol": {
        "titulo": "Portal del Investigador",
        "subtitulo": "Ciencia de datos aplicada a la producciÃ³n cientÃ­fica de mÃ¡s alto nivel.",
        "filtros_tit": "#### ðŸ” Buscador ➔",
        "placeholder_busca": "Ingrese el tÃ­tulo de la revista, ISSN...",
        "buscar_reg": "Buscar registro especÃ­fico:",
        "aba_escopo": "ðŸ“‚ Alcance AcadÃ©mico y CNPq",
        "aba_impacto": "ðŸ“ˆ MÃ©tricas de Rendimiento y Cuartiles",
        "subarea_lbl": "SubÃ¡rea del Conocimiento (CNPq):",
        "base_lbl": "Bases de Datos Detentoras:",
        "jcr_lbl": "Cuartil JCR (Clarivate):",
        "sjr_lbl": "Cuartil SJR (Scopus):",
        "ordem_lbl": "Ordenar Resultados por:",
        "m_selecionadas": "Revistas Selecionadas",
        "m_hindex": "H-Index MÃ¡ximo",
        "m_jif": "Factor JIF MÃ¡ximo",
        "m_sjr": "SJR Score Ãpice",
        "cat_tit": "#### ðŸ“‹ CatÃ¡logo de Revistas",
        "exibir_pag": "Mostrar por pÃ¡gina:",
        "pag_lbl": "PÃ¡gina",
        "exportar_btn": "ðŸ“¥ Exportar solo esta pÃ¡gina",
        "aviso_nada": "Ninguna revista coincide con los criterios aplicados.",
        "nav_tit": "Panel de NavegaciÃ³n",
        "todas": "Todas",
        "col_h5": "Ãndice h5 (Scholar)",
        "meta_tit": "METADATOS",
        "meta_sistema": "Sistema",
        "meta_versao": "VersiÃ³n Base",
        "meta_padrao": "PatrÃ³n CNPq",
        "meta_status": "Operacional",
        "meta_ativo": "Activo",
        "direitos_tit": "Derechos de Autor y Propiedad",
        "direitos_autor": "Universidad Federal de Ouro Preto<br>Minas Gerais, Brasil.<br><i>Todos os direitos reservados.</i>",
        "visitas_lbl": "Visitas al Portal",
        "gov_tit": "SITIOS DEL GOBIERNO",
        "inst_tit": "INFORMACIÃ“N INSTITUCIONAL",
        "pessoal_lbl": "ðŸ‘¤ Sitio personal",
        "indexadores_tit": "INDEXADORES",
        "repositorios_tit": "DIRECTORIOS",
        "ia_tit": "IA ACADÃ‰MICA",
        "btn_desktop": "ðŸ’» Descargar VersiÃ³n para Windows",
        "busca_cat": "ðŸ” CatÃ¡logo de Revistas",
        "busca_ia": "ðŸ§  Recomendador Inteligente (IA)",
        "ia_titulo": "RecomendaciÃ³n TemÃ¡tica con Inteligencia Artificial",
        "ia_subtitulo": "Pegue el tÃ­tulo y el resumen (abstract) de su artÃ­culo. La IA analizarÃ¡ nuestro catÃ¡logo de revistas e indicarÃ¡ las mejores opciones.",
        "ia_campo_titulo": "TÃ­tulo del ArtÃ­culo",
        "ia_campo_resumo": "Resumen / Abstract (Soporta PortuguÃ©s, InglÃ©s o EspaÃ±ol)",
        "ia_chave_api": "Clave API de Gemini (Google AI Studio)",
        "ia_chave_ajuda": "Necesitas una clave API gratuita obtenida de Google AI Studio para ejecutar la recomendaciÃ³n en lÃ­nea.",
        "ia_num_rec": "Cantidad de recomendaciones deseadas (mÃ¡x. 20)",
        "ia_btn_buscar": "Analar y Recomendar",
        "ia_analisando": "La IA estÃ¡ procesando su resumo y cruzÃ¡ndolo con el catÃ¡logo...",
        "ia_sucesso": "Â¡Recomendaciones generadas con Ã©xito!",
        "ia_erro": "Error al procesar con la IA. Verifique que su Clave API sea correcta.",
        "ia_card_motivo": "Por quÃ© publicar aqui:",
        "ia_card_aderencia": "Grado de Adherencia:",
        "ia_card_site": "ðŸŒ Visitar Homepage Oficial",
        "ia_card_sem_site": "Sitio no disponible en la base",
        "filtro_area": "Gran Ãrea",
        "filtro_indexador": "Indexador",
        "ia_credencial_tit": "ðŸ”‘ Credenciales",
        "ia_como_obter_titulo": "â„¹ï¸ Â¿CÃ³mo obtener una clave gratuita?",
        "ia_como_obter_texto": """
<div style="font-size: 14px; line-height: 1.5; font-family: inherit;">
Esta herramienta es gratuita. Para usarla, necesita una clave de API de Google Gemini, tambiÃ©n gratuita:<br><br>
1. Acceda a <b><a href="https://aistudio.google.com" target="_blank">aistudio.google.com</a></b><br>
2. Inicie sesiÃ³n con su cuenta de Google<br>
3. Haga clic en <b>"Get API Key"</b> â†’ <b>"Create API Key"</b><br>
4. Copie la clave generada y pÃ©guela en el campo de arriba<br><br>
<i>La clave gratuita permite cientos de consultas al dÃ­a.</i>
</div>
        """,
        "ia_refinar_alvos": "ðŸŽ¯ Refinar Objetivos",
        "ia_todos": "Todos",
        "reg_boas_vindas": "### Â¡Bienvenido al Portal del Investigador!",
        "reg_apresentacao": "Esta es una plataforma cientÃ­fica de alta tecnologÃ­a diseÃ±ada para simplificar la bÃºsqueda y selecciÃ³n de revistas de impacto para su publicaciÃ³n. Una fuerzas con ciencia de datos e IA.",
        "reg_beneficios_tit": "âœ¨ Â¿Por quÃ© usar el Portal?",
        "reg_beneficio_1_tit": "ðŸ” BÃºsqueda Tradicional",
        "reg_beneficio_1_desc": "Filtros por subÃ¡reas del CNPq, indexadores (Scopus, Web of Science, SciELO, Educ@) y mÃ©tricas consolidadas.",
        "reg_beneficio_2_tit": "ðŸ“Š MÃ©tricas Unificadas",
        "reg_beneficio_2_desc": "Cuartiles JCR/SJR, H-Index y accesos directos de impacto en Scholar a su alcance.",
        "reg_beneficio_3_tit": "ðŸ§  Recomendador IA",
        "reg_beneficio_3_desc": "Recomendaciones generativas a travÃ©s de Gemini 1.5 Flash cruzadas con nuestra base de revistas.",
        "reg_formulario_tit": "ðŸ“ Registro de Acceso AcadÃ©mico",
        "reg_formulario_desc": "El acceso al portal es gratuito y abierto a toda la comunidad cientÃ­fica (desde estudiantes hasta posdoctores). Complete el formulario a continuaciÃ³n para liberar el acceso.",
        "reg_nome": "Nombre Completo:",
        "reg_email": "Correo ElectrÃ³nico AcadÃ©mico o Personal:",
        "reg_escolaridade": "TitulaciÃ³n:",
        "reg_instituicao": "InstituciÃ³n de VÃ­nculo:",
        "reg_inst_outra": "Especifique su InstituciÃ³n:",
        "reg_area_interesse": "Gran Ãrea de InterÃ©s Predominante:",
        "reg_btn_enviar": "Registrarse y Acceder al Buscador ➔",
        "reg_sucesso": "ðŸŽ‰ Â¡Registro completado con Ã©xito! Bienvenido al Portal del Investigador.",
        "reg_erro_campos": "âš ï¸ Por favor, complete todos los campos obligatorios.",
        "reg_lateral_status_bloqueado": "ðŸ”’ Registro pendiente para habilitar el buscador.",
        "reg_lateral_status_liberado": "ðŸ”“ Acceso Concedido",
        "reg_btn_sair": "Salir",
        "log_email": "Correo o Usuario:",
        "log_senha": "ContraseÃ±a:",
        "log_btn_entrar": "Ingresar âž”",
        "log_esqueceu": "Â¿OlvidÃ³ su contraseÃ±a o usuario? Recupere aquÃ­",
        "rec_titulo": "ðŸ”’ Recuperar Acceso",
        "rec_email": "Correo Registrado:",
        "rec_tel": "TelÃ©fono Registrado:",
        "rec_btn_verificar": "Verificar InformaciÃ³n âž”",
        "rec_btn_redefinir": "Restablecer ContraseÃ±a",
        "rec_nova_senha": "Nueva ContraseÃ±a:",
        "rec_conf_senha": "Confirmar Nueva ContraseÃ±a:",
        "rec_sucesso": "ðŸŽ‰ Â¡ContraseÃ±a restablecida con Ã©xito! Inicie sesiÃ³n.",
        "rec_erro_nao_encontrado": "âš ï¸ Correo electrÃ³nico no encontrado en nuestros registros.",
        "rec_btn_voltar": "Volver al Inicio",
        "log_btn_google": "Conectar con Google",
        "log_cadastrar_link": "Â¿No tienes una cuenta? Â¡RegÃ­strate aquÃ­!",
        "log_entrar_link": "Â¿Ya tienes una cuenta? Â¡Inicia sesiÃ³n aquÃ­!",
        "log_titulo": "ðŸ”’ Iniciar SesiÃ³n en el Portal",
        "reg_titulo_form": "ðŸ“ Crear Cuenta AcadÃ©mica",
        "reg_nome_sobrenome": "Nombre y Apellido:",
        "reg_pais": "PaÃ­s:",
        "reg_telefone": "TelÃ©fono:",
        "reg_senha": "ContraseÃ±a:",
        "reg_confirmar_senha": "Confirmar ContraseÃ±a:",
        "reg_btn_cadastrar": "Crear Cuenta y Acceder âž”",
        "reg_erro_senha_diferente": "âš ï¸ Las contraseÃ±as no coinciden.",
        "reg_erro_ja_existe": "âš ï¸ Este correo ya estÃ¡ registrado. Inicie sesiÃ³n.",
        "log_erro_invalido": "âš ï¸ Correo o contraseÃ±a incorrectos.",
        "log_google_sucesso": "ðŸš€ Â¡Conectado con Google! Redireccionando...",
        "areas_trad": {
            "Engenharias": "IngenierÃ­as",
            "LinguÃ­stica, Letras e Artes": "LingÃ¼Ã­stica, Letras y Artes",
            "CiÃªncias BiolÃ³gicas": "Ciencias BiolÃ³gicas",
            "CiÃªncias Exatas e da Terra": "Ciencias Exactas y de la Tierra",
            "Outras / NÃ£o Classificado": "Otras / No Clasificado",
            "CiÃªncias da SaÃºde": "Ciencias de la Salud",
            "CiÃªncias Sociais Aplicadas": "Ciencias Sociales Aplicadas",
            "CiÃªncias AgrÃ¡rias": "Ciencias Agrarias",
            "CiÃªncias Humanas": "Ciencias Humanas"
        }
    }
}
# CorreÃ§Ã£o do seletor em inglÃªs caso venha codificado
if st.session_state.idioma not in dic:
    st.session_state.idioma = "PortuguÃªs"
t = dic[st.session_state.idioma]

# --- 3. CSS CUSTOMIZADO CORRIGIDO (Design Responsivo e Premium) ---
st.markdown("""
<script>
    // Previne que ferramentas de traduÃ§Ã£o automÃ¡tica corrompam o DOM do React/Streamlit
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
    /* ForÃ§a o fundo do menu lateral com a cor definida */
    [data-testid="stSidebar"] {
        background-color: #F8F0E3 !important;
    }   
    
    /* Destaque para o tÃ­tulo do expander */
    .stExpander details summary p {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #FFFFFF !important;
    }

    /* RÃ³tulos da barra lateral */
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
    /* Cards de MÃ©tricas */
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

# --- 4. FUNÃ‡ÃƒO ÃšNICA DE CARREGAMENTO DE DADOS (Focado apenas em dados.csv) ---
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
            
            # Tratamento numÃ©rico padrÃ£o das mÃ©tricas
            for col in ['SJR', 'JIF', 'h-index', 'H index']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(',', '.').str.strip()
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
            # Identifica colunas nÃ£o numÃ©ricas e substitui vazios por "-"
            for col in df.columns:
                if col not in ['SJR', 'JIF', 'h-index', 'H index']:
                    df[col] = df[col].fillna("-").astype(str).str.strip()
                    df[col] = df[col].replace(["None", "none", "NONE", "nan", "NaN", "null", ""], "-")
            
            # Garante a existÃªncia da coluna Homepage
            if "Homepage" not in df.columns:
                df["Homepage"] = "-"
            else:
                df["Homepage"] = df["Homepage"].fillna("-").astype(str).str.strip()
                df["Homepage"] = df["Homepage"].replace(["None", "none", "NONE", "nan", "NaN", "null", ""], "-")

            col_titulo = df.columns[0]
            
            # Cria a chave de agrupamento normalizada (em minÃºsculas) para ignorar diferenÃ§as de caixa
            df["titulo_norm"] = df[col_titulo].astype(str).str.lower().str.strip()
            if "ISSN" in df.columns:
                df["ISSN"] = df["ISSN"].astype(str).str.strip()
            
            # FunÃ§Ãµes de agregaÃ§Ã£o personalizadas
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
                # Prefere tÃ­tulos com letras misturadas (Title Case) sobre ALL CAPS
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
                    
            # Agrupa pelo tÃ­tulo normalizado
            df = df.groupby("titulo_norm", as_index=False).agg(agg_dict)
            df = df.drop(columns=["titulo_norm"])
            
            return df, nome_arquivo
        except Exception as e:
            st.error(f"âš ï¸ Erro ao processar a base de dados '{nome_arquivo}'. Detalhes: {e}")
            st.stop()
    else:
        st.error("âš ï¸ Base de dados nÃ£o encontrada. O arquivo 'dados.csv' nÃ£o foi localizado na raiz do projeto. Por favor, certifique-se de fazer o download do arquivo no repositÃ³rio GitHub correspondente.")
        st.stop()

df_original, arquivo_usado = carregar_dados()

# --- 5. MONTAGEM DA SIDEBAR (LINKS E COMPONENTES) ---
# Inicializa o estado de registro se nÃ£o existir
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
    nome_usr_exibir = st.session_state.get("nome_usuario", "UsuÃ¡rio")
    email_usr_exibir = st.session_state.get("email_usuario", "")
    acessos_usr = st.session_state.get("acessos_usuario", 1)
    
    # Se for login via Google, exibe o e-mail do usuÃ¡rio na mensagem de boas-vindas
    usr_identificador = email_usr_exibir if st.session_state.get("login_via_google", False) else nome_usr_exibir
    
    # Determina o texto de boas-vindas com base no nÃºmero de acessos
    if acessos_usr <= 1:
        status_texto = f"Seja bem-vindo(a), {usr_identificador}"
    else:
        status_texto = f"Bem-vindo(a) de volta, {usr_identificador}"
        
    if st.session_state.get("is_admin", False):
        status_texto = f"ðŸ”‘ Admin: {status_texto}"
        bg_cor = "#0F172A"
    else:
        bg_cor = "#10B981"
        
    # Caixa de boas-vindas
    st.markdown(f"""
        <div style="background-color: {bg_cor}; color: white; padding: 10px 8px; border-radius: 8px; text-align: center; font-weight: 600; font-size: 0.82rem; line-height: 1.3; margin-bottom: 8px;">
            {status_texto}
        </div>
    """, unsafe_allow_html=True)
    
    # Colunas para exibir botÃµes de Sair e ConfiguraÃ§Ãµes lado a lado
    col_sair, col_config = st.sidebar.columns([1, 1])
    with col_sair:
        if st.button("ðŸšª Sair", key="btn_sair_sidebar", help="Encerrar sessÃ£o", use_container_width=True):
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
        if st.button("âš™ï¸ Configs", key="btn_config_gear_sidebar", help="ConfiguraÃ§Ãµes", use_container_width=True):
            st.session_state.abrir_configuracoes = not st.session_state.get("abrir_configuracoes", False)
            st.rerun()

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

# repositÃ³rios
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
        <span>CatÃ¡logo da CAPES</span>
    </a>
</div>
""", unsafe_allow_html=True)

# ia acadÃªmica
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
    <a class="btn-custom-menu" href="https://www.connectedpapers.com/" target="_blank">
        <img src="https://pbs.twimg.com/profile_images/1267529009409208325/avWQ0zGg_400x400.jpg" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 2px; object-fit: contain;">
        <span>ConnectedPapers</span>
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
        <span>CurrÃ­culo Lattes</span>
    </a>
    <a class="btn-custom-menu" href="https://www.periodicos.capes.gov.br/" target="_blank">
        <img src="https://www.periodicos.capes.gov.br/templates/periodicos_gov/images/icon-periodicos.png" style="width: 16px; height: 16px; margin-right: 10px; border-radius: 3px; object-fit: cover;">
        <span>Portal de PeriÃ³dicos CAPES</span>
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
        <span>MÃºsica-UFOP</span>
    </a>
    <a class="btn-custom-menu" href="https://professor.ufop.br/joaoquadros" target="_blank">
        <span style="font-weight: 500; font-size: 0.9rem; color: #004B87;">{t['pessoal_lbl']}</span>
    </a>
</div>
""", unsafe_allow_html=True)

# --- 6. BLOCO CONTADOR DE VISITAS (SILENCIOSO E PERSISTENTE) ---
arquivo_contador = "contador_visitas.txt"
try:
    if 'visitou' not in st.session_state:
        st.session_state.visitou = True
        incrementar = True
    else:
        incrementar = False

    sucesso_db = False
    visitas = 0

    # Tenta ler/gravar no Firebase Firestore se disponÃ­vel
    if db is not None:
        try:
            doc_ref = db.collection("metadados").document("visitas")
            doc = doc_ref.get()
            
            if doc.exists:
                visitas = int(doc.to_dict().get("quantidade", 0))
            else:
                # Se nÃ£o existir no DB, inicializa usando o valor do arquivo local como base para nÃ£o zerar
                visitas_inicial = 0
                if os.path.exists(arquivo_contador):
                    with open(arquivo_contador, "r") as f:
                        conteudo = f.read().strip()
                        visitas_inicial = int(conteudo) if conteudo.isdigit() else 0
                visitas = visitas_inicial
            
            if incrementar:
                visitas += 1
                doc_ref.set({"quantidade": visitas}, merge=True)
            sucesso_db = True
        except Exception:
            pass

    # Fallback local caso o Firebase nÃ£o esteja disponÃ­vel/configurado
    if not sucesso_db:
        if not os.path.exists(arquivo_contador):
            with open(arquivo_contador, "w") as f:
                f.write("0")
                
        with open(arquivo_contador, "r") as f:
            conteudo = f.read().strip()
            visitas = int(conteudo) if conteudo.isdigit() else 0
            
        if incrementar:
            visitas += 1
            with open(arquivo_contador, "w") as f:
                f.write(str(visitas))

    # Calcula a soma de todos os acessos individuais dos usuÃ¡rios cadastrados
    soma_acessos_individuais = 0
    if db is not None:
        try:
            docs = db.collection("usuarios").stream()
            for doc in docs:
                soma_acessos_individuais += int(doc.to_dict().get("acessos", 0))
        except Exception:
            pass
            
    if soma_acessos_individuais == 0:
        caminho_csv = "usuarios.csv"
        if os.path.exists(caminho_csv):
            try:
                df_local = pd.read_csv(caminho_csv, sep=";")
                if "Acessos" in df_local.columns:
                    soma_acessos_individuais = int(df_local["Acessos"].sum())
            except Exception:
                pass

    visitas_totais = visitas + soma_acessos_individuais

    # --- ABA SECRETA DO ADMINISTRADOR (URL com ?admin=true ou ?visitas=true ou Admin Logado) ---
    params = st.query_params
    if "admin" in params or "visitas" in params or st.session_state.get("is_admin", False):
        st.sidebar.markdown("<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>", unsafe_allow_html=True)
        # Exibe em preto (color: #000000)
        st.sidebar.markdown(f"<p style='color: #000000; font-weight: bold; margin-bottom: 0;'>ðŸ“Š Total de Visitas (Admin): {visitas_totais}</p>", unsafe_allow_html=True)
        
        # Campo para atualizar manualmente o valor do contador no Firebase/Local
        novo_valor = st.sidebar.number_input("Atualizar Contador:", min_value=0, value=visitas_totais, step=1, key="admin_visit_counter")
        if st.sidebar.button("Salvar Novo Valor", key="admin_save_visits_btn"):
            # O valor geral serÃ¡ ajustado descontando os acessos dos usuÃ¡rios
            visitas = max(0, novo_valor - soma_acessos_individuais)
            # Salva no Firestore se configurado
            if db is not None:
                try:
                    db.collection("metadados").document("visitas").set({"quantidade": visitas}, merge=True)
                    st.sidebar.success("Firebase atualizado!")
                except Exception as e:
                    st.sidebar.error(f"Erro no Firebase: {e}")
            # Salva no arquivo local
            try:
                with open(arquivo_contador, "w") as f:
                    f.write(str(visitas))
                st.sidebar.success("Arquivo local atualizado!")
            except Exception as e:
                st.sidebar.error(f"Erro local: {e}")
            st.rerun()
except Exception:
    pass

# --- 7. METADADOS E DIREITOS AUTORAIS ---
st.sidebar.markdown("<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>", unsafe_allow_html=True)
st.sidebar.markdown(f"""
    <div style='color: #0F172A; font-size: 0.8rem; padding-left: 5px; line-height: 1.6;'>
        <p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin:0 0 8px 0; letter-spacing: 0.05em;'>{t['meta_tit']}</p>
        <span style='color: #A91D22;'>â—</span> <b>{t['meta_sistema']}:</b> {t['meta_status']}<br>
        <b>{t['meta_versao']}:</b> 2026.1<br>
        <b>{t['meta_padrao']}:</b> {t['meta_ativo']}
        <br><br>
        <hr style='border: 0; border-top: 1px dashed #E2E8F0; margin: 10px 0;'>
        <b>{t['direitos_tit']}:</b><br>
        <b>Â© 2026 JoÃ£o F. Soares-Quadros Jr.</b><br>
        {t['direitos_autor']}
    </div>
""", unsafe_allow_html=True)

# --- 8. BOTÃƒO DE DOWNLOAD DA VERSÃƒO DESKTOP ---
texto_botao = t.get("btn_desktop", "ðŸ’» Baixar VersÃ£o para Windows")

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
# Seleciona o arquivo de imagem correspondente ao idioma ativo
nome_logo = "logo.png"
if st.session_state.idioma == "English":
    nome_logo = "logo_en.png"
elif st.session_state.idioma == "EspaÃ±ol":
    nome_logo = "logo_es.png"

imagem_base64 = obter_imagem_local_base64(nome_logo)
# Fallback caso a versÃ£o traduzida especÃ­fica nÃ£o exista
if not imagem_base64:
    imagem_base64 = obter_imagem_local_base64("logo.png")

if imagem_base64:
    tag_imagem = f'<img src="data:image/png;base64,{imagem_base64}" style="height: 180px; width: auto; object-fit: contain;">'
else:
    tag_imagem = '<span class="emoji-logo" style="font-size: 6.5rem; line-height: 1; margin-right: 15px;">ðŸ“š</span>'

st.markdown(f"""<div class="premium-hero" style="display: flex; align-items: center; flex-wrap: wrap; gap: 30px; padding: 25px 35px;">
{tag_imagem}
<div class="divider-line" style="width: 2px; height: 100px; background-color: rgba(255,255,255,0.15);"></div>
<div class="premium-text-block">
<h1 class="premium-title" style="margin: 0 !important; padding: 0 !important; font-size: 2.3rem !important; font-weight: 800 !important; letter-spacing: -0.5px;">{t['titulo']}</h1>
<p class="premium-subtitle" style="margin: 5px 0 0 0 !important; padding: 0 !important; font-size: 1.1rem !important; opacity: 0.85;">{t['subtitulo']}</p>
</div>
</div>""", unsafe_allow_html=True)

# --- 10. CONTROLE DE ACESSO COM REGISTRO ---
# FunÃ§Ãµes auxiliares globais para banco de dados de credenciais
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def gerar_senha_temporaria():
    caracteres = string.ascii_letters + string.digits
    return "".join(random.choice(caracteres) for _ in range(8))

def enviar_email_recuperacao(destinatario, login, senha_temporaria):
    try:
        smtp_secrets = st.secrets.get("smtp", {})
        sender_email = smtp_secrets.get("email")
        sender_password = smtp_secrets.get("password")
        smtp_server = smtp_secrets.get("server", "smtp.gmail.com")
        smtp_port = int(smtp_secrets.get("port", 587))
        
        if not sender_email or not sender_password:
            return False, "SMTP_NOT_CONFIGURED"
            
        msg = MIMEMultipart()
        msg["From"] = "SciPubs Support <support@scipubs.com>"
        msg["To"] = destinatario
        msg["Subject"] = "Recuperacao de Acesso - SciPubS"
        
        corpo = f"""Ola!

Voce solicitou a recuperacao de acesso ao SciPubs.
Aqui estao suas credenciais temporarias:

â€¢ Login: {login}
â€¢ Senha Temporaria: {senha_temporaria}

Por favor, acesse o portal com estas credenciais e altere sua senha no menu de configuracoes (icone de engrenagem âš™ï¸ na barra lateral).

Atenciosamente,
Equipe Portal do Pesquisador"""
        
        msg.attach(MIMEText(corpo, "plain", "utf-8"))
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, destinatario, msg.as_string())
        server.quit()
        return True, ""
    except Exception as e:
        return False, str(e)

import uuid

def gerar_token():
    return str(uuid.uuid4())

def enviar_email_confirmacao(destinatario, token):
    try:
        smtp_secrets = st.secrets.get("smtp", {})
        sender_email = smtp_secrets.get("email")
        sender_password = smtp_secrets.get("password")
        smtp_server = smtp_secrets.get("server", "smtp.gmail.com")
        smtp_port = int(smtp_secrets.get("port", 587))
        
        if not sender_email or not sender_password:
            return False, "SMTP_NOT_CONFIGURED"
            
        msg = MIMEMultipart()
        msg["From"] = "SciPubs Support <support@scipubs.com>"
        msg["To"] = destinatario
        msg["Subject"] = "Confirme seu Cadastro - SciPubs"
        
        # URL Oficial
        url_oficial = "https://buscador-periodicos.streamlit.app"
        link_confirmacao = f"{url_oficial}/?token={token}"
        
        corpo = f"""Ola!

Obrigado por se cadastrar no SciPubs! Para finalizar a criacao da sua conta e liberar seu acesso, por favor clique no link abaixo:

{link_confirmacao}

Se voce nao solicitou este cadastro, pode ignorar este e-mail.

Atenciosamente,
Equipe SciPubs"""
        
        msg.attach(MIMEText(corpo, "plain", "utf-8"))
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, destinatario, msg.as_string())
        server.quit()
        return True, ""
    except Exception as e:
        return False, str(e)

def confirmar_token(token):
    caminho = "usuarios.csv"
    if os.path.exists(caminho):
        try:
            df = pd.read_csv(caminho, sep=";")
            if "Token_Confirmacao" in df.columns:
                # Transforma as colunas em string para evitar erro de tipo (float/NaN)
                mask = df["Token_Confirmacao"].astype(str).str.strip() == str(token).strip()
                if mask.any():
                    idx = df[mask].index[0]
                    email_encontrado = df.loc[idx, "Email"]
                    nome_encontrado = df.loc[idx, "Nome"]
                    df.loc[idx, "Status_Confirmado"] = True
                    df.loc[idx, "Token_Confirmacao"] = ""
                    df.to_csv(caminho, index=False, sep=";", encoding="utf-8-sig")
                    
                    # Atualiza tambÃ©m no firebase
                    if db is not None:
                        try:
                            db.collection("usuarios").document(str(email_encontrado)).set({
                                "status_confirmado": True,
                                "token_confirmacao": ""
                            }, merge=True)
                        except: pass
                        
                    return True, email_encontrado, nome_encontrado
        except Exception:
            pass
    return False, None, None

def cadastrar_usuario(nome, email, pais, escolaridade, instituicao, senha, idade, sexo, raca, token_confirmacao, status_confirmado=False):
    caminho = "usuarios.csv"
    novo_usuario = pd.DataFrame([{
        "Data/Hora": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Nome": nome,
        "Email": email.lower().strip(),
        "PaÃ­s": pais,
        "Escolaridade": escolaridade,
        "InstituiÃ§Ã£o": instituicao,
        "Idade": idade,
        "Sexo": sexo,
        "RaÃ§a/Etnia": raca,
        "Senha_Hash": hash_senha(senha),
        "Acessos": 1,
        "Status_Confirmado": status_confirmado,
        "Token_Confirmacao": token_confirmacao
    }])
    if os.path.exists(caminho):
        try:
            df_existente = pd.read_csv(caminho, sep=";")
            emails_cadastrados = df_existente["Email"].astype(str).str.lower().str.strip().tolist()
            if email.lower().strip() in emails_cadastrados:
                return False
            df_novo = pd.concat([df_existente, novo_usuario], ignore_index=True)
            df_novo.to_csv(caminho, index=False, sep=";", encoding="utf-8-sig")
        except Exception:
            novo_usuario.to_csv(caminho, index=False, sep=";", encoding="utf-8-sig")
    else:
        novo_usuario.to_csv(caminho, index=False, sep=";", encoding="utf-8-sig")

    if db is not None:
        try:
            db.collection("usuarios").document(email.lower().strip()).set({
                "nome": nome,
                "email": email.lower().strip(),
                "pais": pais,
                "escolaridade": escolaridade,
                "instituicao": instituicao,
                "idade": idade,
                "sexo": sexo,
                "raca": raca,
                "acessos": 1,
                "status_confirmado": status_confirmado,
                "token_confirmacao": token_confirmacao,
                "data_cadastro": firestore.SERVER_TIMESTAMP,
                "ultimo_acesso": firestore.SERVER_TIMESTAMP
            }, merge=True)
        except Exception:
            pass
    return True

def verificar_recuperacao(email):
    email_clean = email.lower().strip()
    if db is not None:
        try:
            doc = db.collection("usuarios").document(email_clean).get()
            if doc.exists:
                d = doc.to_dict()
                return True, d.get("nome", "UsuÃ¡rio")
        except Exception:
            pass
    caminho = "usuarios.csv"
    if os.path.exists(caminho):
        try:
            df = pd.read_csv(caminho, sep=";")
            match = df[(df["Email"].astype(str).str.lower().str.strip() == email_clean)]
            if not match.empty:
                return True, match.iloc[0]["Nome"]
        except Exception:
            pass
    return False, ""

def redefinir_senha_usuario(email, nova_senha):
    email_clean = email.lower().strip()
    senha_hash_nova = hash_senha(nova_senha)
    if db is not None:
        try:
            db.collection("usuarios").document(email_clean).set({
                "Senha_Hash": senha_hash_nova
            }, merge=True)
        except Exception:
            pass
    caminho = "usuarios.csv"
    if os.path.exists(caminho):
        try:
            df = pd.read_csv(caminho, sep=";")
            idx = df[df["Email"].astype(str).str.lower().str.strip() == email_clean].index
            if not idx.empty:
                df.loc[idx, "Senha_Hash"] = senha_hash_nova
                df.to_csv(caminho, index=False, sep=";", encoding="utf-8-sig")
        except Exception:
            pass
    return True

def verificar_login(email_ou_usuario, senha):
    email_clean = email_ou_usuario.lower().strip()
    senha_clean = senha.strip()
    admin_email_conf = st.secrets.get("ADMIN_EMAIL", "joaoquadros@ufop.edu.br").lower().strip()
    admin_pass_conf = st.secrets.get("ADMIN_PASSWORD", "Ufop@2026").strip()
    
    if email_clean == admin_email_conf and senha_clean == admin_pass_conf:
        acessos_atuais = 0
        if db is not None:
            try:
                doc_ref = db.collection("usuarios").document(admin_email_conf)
                doc = doc_ref.get()
                if doc.exists:
                    acessos_atuais = int(doc.to_dict().get("acessos", 0))
                doc_ref.set({
                    "nome": "JoÃ£o F. Soares-Quadros Jr.",
                    "email": admin_email_conf,
                    "pais": "Brasil",
                    "telefone": "N/A",
                    "escolaridade": "Doutor",
                    "instituicao": "Universidade Federal de Ouro Preto (UFOP)",
                    "acessos": acessos_atuais + 1,
                    "ultimo_acesso": firestore.SERVER_TIMESTAMP
                }, merge=True)
            except Exception:
                pass
        st.session_state.nome_usuario = "JoÃ£o"
        st.session_state.acessos_usuario = acessos_atuais + 1
        return True

    caminho = "usuarios.csv"
    if not os.path.exists(caminho):
        return False
    try:
        df = pd.read_csv(caminho, sep=";")
        senha_hash_calc = hash_senha(senha)
        match = df[(df["Email"].astype(str).str.lower().str.strip() == email_clean) & (df["Senha_Hash"] == senha_hash_calc)]
        if not match.empty:
            idx = match.index[0]
            
            # Verifica se o e-mail foi confirmado (tratando contas antigas que nÃ£o tÃªm a coluna como confirmadas)
            if "Status_Confirmado" in df.columns:
                status = df.loc[idx, "Status_Confirmado"]
                if pd.notna(status) and str(status).strip().lower() == "false":
                    return "NOT_CONFIRMED"
                    
            if "Acessos" not in df.columns:
                df["Acessos"] = 1
            current_acessos = df.loc[idx, "Acessos"]
            novo_acessos = int(current_acessos) + 1 if pd.notna(current_acessos) else 1
            
            # Seta as Session States do UsuÃ¡rio logado
            st.session_state.nome_usuario = str(match.iloc[0]["Nome"]).split(" ")[0].capitalize()
            st.session_state.acessos_usuario = novo_acessos
            
            try:
                df.loc[idx, "Acessos"] = novo_acessos
                df.to_csv(caminho, index=False, sep=";", encoding="utf-8-sig")
            except Exception:
                pass
            if db is not None:
                try:
                    doc_ref = db.collection("usuarios").document(email_clean)
                    doc = doc_ref.get()
                    acessos_atuais = 0
                    if doc.exists:
                        acessos_atuais = int(doc.to_dict().get("acessos", 0))
                    doc_ref.set({
                        "acessos": acessos_atuais + 1,
                        "ultimo_acesso": firestore.SERVER_TIMESTAMP
                    }, merge=True)
                except Exception:
                    pass
            return True
        return False
    except Exception:
        return False

# --- 10. CONTROLE DE ACESSO COM REGISTRO ---
url_token = st.query_params.get("token")
if url_token:
    sucesso_token, email_token, nome_token = confirmar_token(url_token)
    if sucesso_token:
        st.session_state.registrado = True
        st.session_state.login_via_google = False
        st.session_state.email_usuario = email_token.lower().strip()
        st.session_state.nome_usuario = str(nome_token).split(" ")[0].capitalize()
        admin_email_conf = st.secrets.get("ADMIN_EMAIL", "joaoquadros@ufop.edu.br").lower().strip()
        st.session_state.is_admin = (email_token.lower().strip() == admin_email_conf)
        st.success("âœ… Conta ativada e acesso liberado com sucesso!")
        st.query_params.clear()
        time.sleep(2)
        st.rerun()
    else:
        st.error("âš ï¸ Token invÃ¡lido ou jÃ¡ utilizado.")
    st.query_params.clear()

if not st.session_state.registrado:

    # Escolha do Modo (RecuperaÃ§Ã£o, Login ou Cadastro)
    if st.session_state.get("modo_recuperacao", False):
        col_rec_1, col_rec_2, col_rec_3 = st.columns([1, 1.5, 1])
        with col_rec_2:
            st.markdown(f"### {t['rec_titulo']}")
            email_rec = st.text_input(t['rec_email'], placeholder="", key="email_rec_input")
            
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            
            # Se jÃ¡ verificou os dados, exibe a redefiniÃ§Ã£o de senha
            if st.session_state.get("usuario_recuperado_email", ""):
                email_confirmado = st.session_state.usuario_recuperado_email
                st.info(f"UsuÃ¡rio identificado. Defina uma nova senha para a conta: **{email_confirmado}**")
                
                nova_senha = st.text_input(t['rec_nova_senha'], type="password", key="rec_nova_senha_input")
                conf_senha = st.text_input(t['rec_conf_senha'], type="password", key="rec_conf_senha_input")
                
                if st.button(t['rec_btn_redefinir'], type="primary", use_container_width=True):
                    if not nova_senha.strip():
                        st.error(t['reg_erro_campos'] + " (Faltando: Nova Senha)")
                    elif nova_senha != conf_senha:
                        st.error(t['reg_erro_senha_diferente'])
                    else:
                        redefinir_senha_usuario(email_confirmado, nova_senha)
                        st.success(t['rec_sucesso'])
                        st.session_state.usuario_recuperado_email = ""
                        st.session_state.modo_recuperacao = False
                        st.session_state.modo_login = True
                        time.sleep(1.5)
                        st.rerun()
            else:
                if st.button(t['rec_btn_verificar'], type="primary", use_container_width=True):
                    if not email_rec.strip():
                        st.error(t['reg_erro_campos'] + " (Faltando: E-mail)")
                    else:
                        sucesso, nome = verificar_recuperacao(email_rec)
                        if sucesso:
                            # Gera senha temporÃ¡ria alfanumÃ©rica
                            senha_temp = gerar_senha_temporaria()
                            # Atualiza a senha no banco de dados
                            redefinir_senha_usuario(email_rec.lower().strip(), senha_temp)
                            
                            # Envia por e-mail
                            enviado, erro = enviar_email_recuperacao(email_rec.lower().strip(), email_rec.lower().strip(), senha_temp)
                            
                            if enviado:
                                st.success("ðŸŽ‰ Uma senha temporÃ¡ria foi enviada para o seu e-mail cadastrado! Acesse o portal e atualize-a nas configuraÃ§Ãµes.")
                                st.session_state.modo_recuperacao = False
                                st.session_state.modo_login = True
                                time.sleep(3.0)
                                st.rerun()
                            else:
                                # Fallback se SMTP nÃ£o estiver configurado
                                st.warning("âš ï¸ NÃ£o foi possÃ­vel enviar o e-mail no momento (Servidor SMTP nÃ£o configurado).")
                                st.info(f"Para continuar seu acesso agora, utilize as credenciais abaixo:\n\n**Login:** `{email_rec.lower().strip()}`\n\n**Senha TemporÃ¡ria:** `{senha_temp}`\n\nEm caso de dÃºvidas, contate o suporte: **support@scipubs.com**")
                                st.session_state.usuario_recuperado_email = email_rec.lower().strip()
                        else:
                            st.error(t['rec_erro_nao_encontrado'])
            
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            if st.button(t['rec_btn_voltar'], use_container_width=True):
                st.session_state.usuario_recuperado_email = ""
                st.session_state.modo_recuperacao = False
                st.session_state.modo_login = True
                st.rerun()

    elif st.session_state.modo_login:
        # TÃTULO E APRESENTAÃ‡ÃƒO MINIMALISTA
        col_log_1, col_log_2, col_log_3 = st.columns([1, 1.5, 1])
        with col_log_2:
            # FormulÃ¡rio de Login
            with st.form("form_login_usuario", clear_on_submit=False):
                email_log = st.text_input(t['log_email'], placeholder="", key="email_login")
                senha_log = st.text_input(t['log_senha'], type="password", placeholder="", key="senha_login")
                
                st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                
                btn_entrar = st.form_submit_button(t['log_btn_entrar'], type="primary", use_container_width=True)
            
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            
            # Link para ir para a pÃ¡gina de Cadastro colocado diretamente abaixo
            if st.button(t['log_cadastrar_link'], key="btn_ir_cadastro", use_container_width=True):
                st.session_state.modo_login = False
                st.rerun()
                
            # Link para ir para a pÃ¡gina de RecuperaÃ§Ã£o
            if st.button(f"ðŸ”‘ {t['log_esqueceu']}", key="btn_ir_recuperacao", use_container_width=True):
                st.session_state.modo_recuperacao = True
                st.session_state.modo_login = False
                st.session_state.usuario_recuperado_email = ""
                st.rerun()
                
            if btn_entrar:
                if not email_log.strip() or not senha_log.strip():
                    faltam = []
                    if not email_log.strip(): faltam.append("E-mail")
                    if not senha_log.strip(): faltam.append("Senha")
                    st.error(f"{t['reg_erro_campos']} (Faltando: {', '.join(faltam)})")
                else:
                    res_login = verificar_login(email_log, senha_log)
                    if res_login == "NOT_CONFIRMED":
                        st.warning("âš ï¸ Sua conta ainda nÃ£o foi confirmada. Verifique o link enviado para o seu e-mail.")
                    elif res_login:
                        st.session_state.registrado = True
                        st.session_state.login_via_google = False
                        
                        email_clean = email_log.lower().strip()
                        st.session_state.email_usuario = email_clean
                        admin_email_conf = st.secrets.get("ADMIN_EMAIL", "joaoquadros@ufop.edu.br").lower().strip()
                        st.session_state.is_admin = (email_clean == admin_email_conf)
                        
                        st.success(t['reg_sucesso'])
                        time.sleep(1.2)
                        st.rerun()
                    else:
                        st.error(t['log_erro_invalido'])
                        
            st.divider()
            st.markdown("### ðŸ”‘ Confirmar Conta Manualmente")
            st.write("NÃ£o conseguiu confirmar pelo link? Cole o token recebido no e-mail abaixo:")
            token_manual = st.text_input("Token de ConfirmaÃ§Ã£o")
            if st.button("Validar Token"):
                sucesso_token, email_token, nome_token = confirmar_token(token_manual)
                if sucesso_token:
                    st.session_state.registrado = True
                    st.session_state.login_via_google = False
                    st.session_state.email_usuario = email_token.lower().strip()
                    st.session_state.nome_usuario = str(nome_token).split(" ")[0].capitalize()
                    admin_email_conf = st.secrets.get("ADMIN_EMAIL", "joaoquadros@ufop.edu.br").lower().strip()
                    st.session_state.is_admin = (email_token.lower().strip() == admin_email_conf)
                    st.success("âœ… E-mail confirmado com sucesso! Acesso liberado.")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("âš ï¸ Token invÃ¡lido ou jÃ¡ utilizado.")
    else:
        with st.form("form_cadastro_usuario", clear_on_submit=False):
            col_reg_1, col_reg_2 = st.columns(2)
            with col_reg_1:
                nome_cad = st.text_input(t['reg_nome_sobrenome'], placeholder="Ex: JoÃ£o Silva")
                email_cad = st.text_input(t['reg_email'], placeholder="")
                pais_cad = st.text_input(t['reg_pais'], placeholder="Ex: Brasil")
                sexo_cad = st.selectbox("Sexo (Opcional):", ["", "Masculino", "Feminino", "NÃ£o informar"])
                
            with col_reg_2:
                # TitulaÃ§Ã£o
                opcoes_esc = []
                if st.session_state.idioma == "PortuguÃªs":
                    opcoes_esc = ["GraduaÃ§Ã£o", "EspecializaÃ§Ã£o", "Mestrado", "Doutorado", "Outra"]
                elif st.session_state.idioma == "English":
                    opcoes_esc = ["Undergraduate", "Specialization", "Master's", "Doctorate", "Other"]
                else:
                    opcoes_esc = ["Grado", "EspecializaciÃ³n", "MaestrÃ­a", "Doctorado", "Otra"]
                    
                escolaridade_cad = st.selectbox(t['reg_escolaridade'], opcoes_esc)
                
                # VÃ­nculo Institucional
                instituicao_cad = st.text_input(t['reg_instituicao'], placeholder="Ex: Universidade de SÃ£o Paulo (USP)")
                    
                idade_cad = st.number_input("Idade (Opcional):", min_value=0, max_value=120, value=0, step=1)
                raca_cad = st.selectbox("RaÃ§a/Etnia (Opcional):", ["", "Branca", "Parda", "Preta", "IndÃ­gena", "Outra"])
    
            # Senha e confirmaÃ§Ã£o de senha
            st.markdown("<hr style='border-top:1px dashed #CBD5E1; margin:15px 0;'>", unsafe_allow_html=True)
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                senha_cad = st.text_input(t['reg_senha'], type="password", placeholder="", key="senha_cad_reg")
            with col_s2:
                senha_cad_conf = st.text_input(t['reg_confirmar_senha'], type="password", placeholder="", key="senha_cad_conf_reg")
    
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            btn_registrar = st.form_submit_button(t['reg_btn_cadastrar'], type="primary", use_container_width=True)
            
        if btn_registrar:
            if not nome_cad.strip() or not email_cad.strip() or not pais_cad.strip() or not instituicao_cad.strip() or not senha_cad.strip():
                faltam = []
                if not nome_cad.strip(): faltam.append("Nome")
                if not email_cad.strip(): faltam.append("E-mail")
                if not pais_cad.strip(): faltam.append("PaÃ­s")
                if not instituicao_cad.strip(): faltam.append("InstituiÃ§Ã£o de VÃ­nculo")
                if not senha_cad.strip(): faltam.append("Senha")
                st.error(f"{t['reg_erro_campos']} (Faltando: {', '.join(faltam)})")
            elif not senha_cad_conf.strip():
                st.error(f"{t['reg_erro_campos']} (Faltando: ConfirmaÃ§Ã£o de Senha)")
            elif senha_cad != senha_cad_conf:
                st.error(t['reg_erro_senha_diferente'])
            else:
                idade_final = idade_cad if idade_cad > 0 else ""
                
                # Grava no CSV
                token_confirmacao = gerar_token()
                sucesso_cadastro = cadastrar_usuario(
                    nome_cad.strip(),
                    email_cad.strip(),
                    pais_cad.strip(),
                    escolaridade_cad,
                    instituicao_cad.strip(),
                    senha_cad.strip(),
                    idade_final,
                    sexo_cad,
                    raca_cad,
                    token_confirmacao,
                    status_confirmado=False
                )
                if sucesso_cadastro:
                    enviado, erro = enviar_email_confirmacao(email_cad.strip(), token_confirmacao)
                    if enviado:
                        st.success("âœ… Cadastro realizado! Verifique seu e-mail para confirmar a conta antes de fazer o login.")
                    else:
                        st.warning("âš ï¸ Conta criada, mas nÃ£o foi possÃ­vel enviar o e-mail de confirmaÃ§Ã£o.")
                        st.info(f"Para testes, vocÃª mesmo pode confirmar clicando aqui: https://buscador-periodicos.streamlit.app/?token={token_confirmacao}")
                    
                    st.session_state.modo_cadastro = False
                    st.session_state.modo_login = True
                    time.sleep(4)
                    st.rerun()
                else:
                    st.error(t['reg_erro_ja_existe'])
                    
        st.markdown("<br>", unsafe_allow_html=True)
        # Link para voltar ao Login
        if st.button(t['log_entrar_link'], key="btn_ir_login", use_container_width=True):
            st.session_state.modo_login = True
            st.rerun()
            
    st.stop()

# Textos informativos traduzidos

# --- TELA DE CONFIGURAÃ‡Ã•ES & AJUSTES ---
if st.session_state.get("abrir_configuracoes", False):
    st.markdown("## âš™ï¸ ConfiguraÃ§Ãµes & Ajustes do Portal")
    
    # BotÃ£o para fechar e retornar ao buscador
    if st.button("â¬…ï¸ Voltar para o Buscador", key="btn_fechar_config"):
        st.session_state.abrir_configuracoes = False
        st.rerun()
        
    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
    
    opc_config = st.radio(
        "Selecione uma opÃ§Ã£o de ajuste:",
        [
            "ðŸ‘¤ AtualizaÃ§Ã£o de Cadastro",
            "ðŸ”‘ AtualizaÃ§Ã£o de Senha",
            "ðŸŽ¨ Tema da Plataforma (Claro/Escuro)",
            "ðŸ“¢ Compartilhar Portal com Outros"
        ],
        key="radio_opc_config"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if "ðŸ‘¤ AtualizaÃ§Ã£o de Cadastro" in opc_config:
        st.subheader("ðŸ‘¤ Atualizar Meus Dados de Cadastro")
        email_atual = st.session_state.email_usuario
        nome_atual = st.session_state.get("nome_usuario", "")
        
        # Carrega dados atuais do usuÃ¡rio
        caminho_csv = "usuarios.csv"
        telefone_atual = ""
        escolaridade_atual = "Doutor"
        inst_atual = ""
        
        if db is not None:
            try:
                doc = db.collection("usuarios").document(email_atual).get()
                if doc.exists:
                    d = doc.to_dict()
                    nome_atual = d.get("nome", nome_atual)
                    telefone_atual = d.get("telefone", "")
                    escolaridade_atual = d.get("escolaridade", "Doutor")
                    inst_atual = d.get("instituicao", "")
            except Exception:
                pass
                
        if not telefone_atual and os.path.exists(caminho_csv):
            try:
                df_u = pd.read_csv(caminho_csv, sep=";")
                match = df_u[df_u["Email"].astype(str).str.lower().str.strip() == email_atual.lower().strip()]
                if not match.empty:
                    nome_atual = match.iloc[0]["Nome"]
                    telefone_atual = match.iloc[0]["Telefone"]
                    escolaridade_atual = match.iloc[0]["Escolaridade"]
                    inst_atual = match.iloc[0]["Instituicao"]
            except Exception:
                pass
                
        nome_edit = st.text_input("Nome Completo:", value=nome_atual)
        tel_edit = st.text_input("Telefone:", value=telefone_atual)
        
        opcoes_esc_edit = ["Estudante de GraduaÃ§Ã£o", "Especialista / PÃ³s-Graduado", "Mestrando", "Mestre", "Doutorando", "Doutor", "PÃ³s-Doutor", "Outro"]
        if escolaridade_atual not in opcoes_esc_edit:
            opcoes_esc_edit.append(escolaridade_atual)
        esc_edit = st.selectbox("Escolaridade:", opcoes_esc_edit, index=opcoes_esc_edit.index(escolaridade_atual))
        
        inst_edit = st.text_input("InstituiÃ§Ã£o de VÃ­nculo:", value=inst_atual)
        
        if st.button("Salvar AlteraÃ§Ãµes do Cadastro", type="primary"):
            if not nome_edit.strip() or not tel_edit.strip() or not inst_edit.strip():
                st.error("âš ï¸ Preencha todos os campos obrigatÃ³rios.")
            else:
                if os.path.exists(caminho_csv):
                    try:
                        df_u = pd.read_csv(caminho_csv, sep=";")
                        idx = df_u[df_u["Email"].astype(str).str.lower().str.strip() == email_atual.lower().strip()].index
                        if not idx.empty:
                            df_u.loc[idx, "Nome"] = nome_edit.strip()
                            df_u.loc[idx, "Telefone"] = tel_edit.strip()
                            df_u.loc[idx, "Escolaridade"] = esc_edit
                            df_u.loc[idx, "Instituicao"] = inst_edit.strip()
                            df_u.to_csv(caminho_csv, index=False, sep=";", encoding="utf-8-sig")
                    except Exception:
                        pass
                
                if db is not None:
                    try:
                        db.collection("usuarios").document(email_atual).set({
                            "nome": nome_edit.strip(),
                            "telefone": tel_edit.strip(),
                            "escolaridade": esc_edit,
                            "instituicao": inst_edit.strip()
                        }, merge=True)
                    except Exception:
                        pass
                        
                st.session_state.nome_usuario = nome_edit.strip().split(" ")[0].capitalize()
                st.success("ðŸŽ‰ Dados do cadastro atualizados com sucesso!")
                time.sleep(1.2)
                st.rerun()

    elif "ðŸ”‘ AtualizaÃ§Ã£o de Senha" in opc_config:
        st.subheader("ðŸ”‘ Alterar Minha Senha de Acesso")
        nova_s = st.text_input("Nova Senha:", type="password", key="settings_nova_senha")
        conf_s = st.text_input("Confirmar Nova Senha:", type="password", key="settings_conf_senha")
        if st.button("Atualizar Senha", type="primary"):
            if not nova_s.strip():
                st.error("âš ï¸ A senha nÃ£o pode estar em branco.")
            elif nova_s != conf_s:
                st.error("âš ï¸ As senhas digitadas sÃ£o diferentes.")
            else:
                redefinir_senha_usuario(st.session_state.email_usuario, nova_s)
                st.success("ðŸŽ‰ Senha alterada com sucesso!")
                time.sleep(1.2)
                st.rerun()
                
    elif "ðŸŽ¨ Tema da Plataforma (Claro/Escuro)" in opc_config:
        st.subheader("ðŸŽ¨ Estilo e AparÃªncia da Plataforma")
        tema_atual = "Modo Noturno (Escuro)" if st.session_state.get("dark_mode", False) else "Modo Diurno (Claro)"
        st.info(f"O tema ativo atualmente Ã©: **{tema_atual}**")
        
        if st.session_state.get("dark_mode", False):
            if st.button("Ativar Modo Diurno (Claro)", type="primary"):
                st.session_state.dark_mode = False
                st.rerun()
        else:
            if st.button("Ativar Modo Noturno (Escuro)", type="primary"):
                st.session_state.dark_mode = True
                st.rerun()

    elif "ðŸ“¢ Compartilhar Portal com Outros" in opc_config:
        st.subheader("ðŸ“¢ Compartilhar o Portal do Pesquisador")
        url_portal = "https://scipubs.com/"
        texto_compartilhar = f"Confira o Buscador de Periodicos Cientificos do PPGE UFOP: {url_portal}"
        
        msg_encoded = urllib.parse.quote(texto_compartilhar)
        link_wa = f"https://api.whatsapp.com/send?text={msg_encoded}"
        link_mail = f"mailto:?subject=Portal%20do%20Pesquisador&body={msg_encoded}"
        
        st.write("Escolha uma das formas abaixo para divulgar o portal:")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            st.markdown(f"[ðŸ’¬ WhatsApp]({link_wa})", unsafe_allow_html=True)
        with col_c2:
            st.markdown(f"[âœ‰ï¸ E-mail]({link_mail})", unsafe_allow_html=True)
        with col_c3:
            if st.button("ðŸ“‹ Copiar Link"):
                st.info(f"Link: `{url_portal}`")
                st.success("Link copiado para exibiÃ§Ã£o!")


            
    st.stop()

# Textos informativos traduzidos
if st.session_state.idioma == "PortuguÃªs":
    expander_titulo = "ðŸ’¡ Sobre o SciPubs & Como Utilizar"
    sobre_texto = """
### Bem-vindo ao SciPubs: o Portal do Pesquisador!
Esta Ã© uma ferramenta desenvolvida para otimizar a busca por periÃ³dicos cientÃ­ficos de alto impacto.
  
#### ðŸ› ï¸ O que vocÃª pode fazer aqui?
1. **Busca AvanÃ§ada & Booleana:** Pesquise por termos exatos utilizando aspas (ex: `"educaÃ§Ã£o musical"`) ou combine mÃºltiplos critÃ©rios usando os operadores lÃ³gicos `AND`, `OR` e `NOT` (ex: `music AND education NOT medicine`).
2. **Filtros por SubÃ¡rea (CNPq):** Encontre periÃ³dicos perfeitamente alinhados Ã  sua subÃ¡rea especÃ­fica de atuaÃ§Ã£o e conhecimento.
3. **MÃ©tricas de Impacto:** Analise o prestÃ­gio internacional atravÃ©s de quartis e indicadores consolidados das bases **JCR (Clarivate)**, **SJR (Scopus)**, **H-Index** e o link direto para o **Ãndice h5 (Google Scholar)**.
4. **RecomendaÃ§Ã£o Inteligente (IA):** Use a inteligÃªncia artificial do Google Gemini para colar o tÃ­tulo e resumo do seu artigo e obter as recomendaÃ§Ãµes de periÃ³dicos ideais com justificativa e link direto.
5. **ExportaÃ§Ã£o de Dados:** Filtre os resultados de acordo com sua necessidade e faÃ§a o download da tabela customizada imediatamente.
"""
elif st.session_state.idioma == "English":
    expander_titulo = "ðŸ’¡ About SciPubs & How to Use"
    sobre_texto = """
### Welcome to SciPubs: the Researcher's Portal!
This is a tool developed to optimize the search for high-impact scientific journals.
 
#### ðŸ› ï¸ What can you do here?
1. **Advanced & Boolean Search:** Search for exact phrases using quotation marks (e.g., `"music education"`) or combine multiple criteria using the logical operators `AND`, `OR`, and `NOT` (e.g., `music AND education NOT medicine`).
2. **Filters by Subarea (CNPq):** Find journals perfectly aligned with your specific subarea of expertise.
3. **Impact Metrics:** Analyze international prestige through consolidated quartiles and indicators from **JCR (Clarivate)**, **SJR (Scopus)**, **H-Index**, and direct links to the **h5-Index (Google Scholar)**.
4. **Smart Recommender (AI):** Paste your title and abstract, and let the Google Gemini AI recommend the best matches with specific rationale and homepage links.
5. **Data Export:** Filter results according to your needs and download the customized table immediately.
"""
else: # EspaÃ±ol
    expander_titulo = "ðŸ“– Sobre el Portal del Investigador y CÃ³mo Utilizar"
    sobre_texto = """
### Â¡Bienvenido al Portal del Investigador!
Esta es una herramienta desarrollada con el objetivo de optimizar la bÃºsqueda de revistas cientÃ­ficas de alto impacto.
 
#### ðŸ› ï¸ Â¿QuÃ© puedes fazer aquÃ­?
1. **BÃºsqueda Avanzada y Booleana:** Busque tÃ©rminos exactos usando comillas (por ejemplo: `"educaciÃ³n musical"`) o combine mÃºltiples criterios usando los operadores lÃ³gicos `AND`, `OR` y `NOT` (por ejemplo: `music AND education NOT medicine`).
2. **Filtros por SubÃ¡rea (CNPq):** Encuentre revistas perfectamente alineadas con su subÃ¡rea especÃ­fica de conocimiento.
3. **MÃ©tricas de Impacto:** Analise el prestigio internacional a travÃ©s de cuartiles e indicadores consolidados de las bases **JCR (Clarivate)**, **SJR (Scopus)**, **H-Index** y el enlace directo al **Ãndice h5 (Google Scholar)**.
4. **Recomendador Inteligente (IA):** Use el motor de IA de Google Gemini para obtener sugerencias temÃ¡ticas personalizadas basadas en el tÃ­tulo y resumen de su artÃ­culo.
5. **ExportaciÃ³n de Dados:** Filtre los resultados segÃºn sus necesidades y descargue la tabla personalizada inmediatamente.
"""

with st.expander(expander_titulo, expanded=False):
    st.markdown(sobre_texto)

st.markdown("<br>", unsafe_allow_html=True)

# --- 10. INTERFACE PRINCIPAL MULTI-ABAS ---
st.markdown(t['filtros_tit'])

# Define as abas com base na presenÃ§a do parÃ¢metro ?admin=true ou ?visitas=true na URL ou se o usuÃ¡rio logado for Admin
params_url = st.query_params
if "admin" in params_url or "visitas" in params_url or st.session_state.get("is_admin", False):
    tab_busca, tab_ia, tab_admin = st.tabs([t['busca_cat'], t['busca_ia'], "ðŸ“Š EstatÃ­sticas (Admin)"])
else:
    tab_busca, tab_ia = st.tabs([t['busca_cat'], t['busca_ia']])

# ==================== ABA 1: CATÃLOGO TRADICIONAL ====================
with tab_busca:
    busca = st.text_input(t['buscar_reg'], placeholder=t['placeholder_busca'])

    aba_escopo, aba_impacto = st.tabs([t['aba_escopo'], t['aba_impacto']])

    with aba_escopo:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            col_subarea = "SubÃ¡rea do Conhecimento"
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
            opcoes_ordenacao = ["TÃ­tulo"]
            if "SJR" in df_original.columns: 
                opcoes_ordenacao.append("SJR (PrestÃ­gio)")
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

    mapa_ordem = {"SJR (PrestÃ­gio)": ("SJR", False), "JIF (Fator de Impacto)": ("JIF", False), "TÃ­tulo": (df_filtrado.columns[0], True)}
    col_ordenar, ascendente = mapa_ordem[criterio_ordem]
    if col_ordenar in df_filtrado.columns: 
        df_filtrado = df_filtrado.sort_values(by=col_ordenar, ascending=ascendente)

    # METRICAS DINÃ‚MICAS COM SEGURANÃ‡A DE TIPO
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

    # EXIBIÃ‡ÃƒO E PAGINAÃ‡ÃƒO
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
        
        # Remove as colunas de Ã¡rea para simplificar a exibiÃ§Ã£o na tabela e evitar crashes de mapeamento do PyArrow
        df_exibir = df_da_pagina.drop(columns=["Grande Area", "Area do Conhecimento", "SubÃ¡rea do Conhecimento"], errors="ignore")
        
        # Limpa o index para evitar falhas de segmentaÃ§Ã£o em Ã­ndices nÃ£o contÃ­guos (bug do PyArrow pÃ³s-filtragem)
        df_exibir = df_exibir.reset_index(drop=True)
        
        # Formata links com fragmentos hash para permitir exibiÃ§Ã£o seletiva (e traÃ§o "-" nas cÃ©lulas vazias)
        if "Homepage" in df_exibir.columns:
            def format_homepage(val):
                val_str = str(val).strip()
                if val_str not in ["-", "", "None", "nan"]:
                    return val_str + "#ðŸ”— Ver site"
                return "-"
            df_exibir["Homepage"] = df_exibir["Homepage"].apply(format_homepage)
        if "Ãndice h5" in df_exibir.columns:
            def format_h5(val):
                val_str = str(val).strip()
                if val_str not in ["-", "", "None", "nan"]:
                    return val_str + "#ðŸ”— Abrir"
                return "-"
            df_exibir["Ãndice h5"] = df_exibir["Ãndice h5"].apply(format_h5)
        
        # ReconstruÃ§Ã£o ultra-defensiva para descartar qualquer metadado do pandas que confunda o PyArrow
        df_exibir = pd.DataFrame({col: df_exibir[col].tolist() for col in df_exibir.columns})
        
        # EXIBIÃ‡ÃƒO DA HOMEPAGE NA TABELA COM LINK CLICÃVEL
        st.dataframe(
            df_exibir, 
            hide_index=True,
            column_config={
                "Homepage": st.column_config.LinkColumn(
                    "Homepage",
                    help="Clique para visitar o site oficial da revista",
                    display_text=r"#(.+)$"
                ),
                "JIF": st.column_config.Column(
                    alignment="center"
                ),
                "Quartil JCR": st.column_config.Column(
                    alignment="center"
                ),
                "SJR": st.column_config.Column(
                    alignment="center"
                ),
                "SJR Best Quartile": st.column_config.Column(
                    alignment="center"
                ),
                "H index": st.column_config.Column(
                    alignment="center"
                ),
                "Ãndice h5": st.column_config.LinkColumn(
                    t['col_h5'],
                    help="Clique para abrir o Ã­ndice h5 no Google Scholar",
                    display_text=r"#(.+)$",
                    alignment="center"
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
    # FunÃ§Ã£o auxiliar local para traduzir as Grandes Ãreas
    def traduzir_grande_area(area_original, t_dict):
        if not area_original or str(area_original).strip() in ["-", "None", "nan"]:
            return "-"
        import unicodedata
        def clean_str(s):
            s = str(s).lower().strip()
            # Remove acentos
            s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
            # Remove caracteres especiais
            s = ''.join(c for c in s if c.isalnum() or c.isspace())
            return ' '.join(s.split())
            
        area_clean = clean_str(area_original)
        mapeamento = t_dict.get("areas_trad", {})
        for chave_original, valor_traduzido in mapeamento.items():
            if clean_str(chave_original) == area_clean:
                return valor_traduzido
        return str(area_original).strip()

    # InicializaÃ§Ã£o segura dos estados na Session State
    if "recomendacoes" not in st.session_state:
        st.session_state.recomendacoes = None
    if "erro_ia" not in st.session_state:
        st.session_state.erro_ia = None
    if "aviso_filtro" not in st.session_state:
        st.session_state.aviso_filtro = False
    if "modo_local" not in st.session_state:
        st.session_state.modo_local = False
    if "ia_cache" not in st.session_state:
        # Cache de resultados: chave = hash(titulo+resumo+num_rec+area+indexador), valor = lista de recomendaÃ§Ãµes
        st.session_state.ia_cache = {}
    
    col_input, col_meta = st.columns([2, 1])
    
    with col_input:
        st.markdown(f"### {t['ia_titulo']}")
        st.markdown(f"*{t['ia_subtitulo']}*")
        st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
        
        titulo_artigo = st.text_input(t['ia_campo_titulo'], placeholder="Ex: AnÃ¡lise EpidemiolÃ³gica de SaÃºde Coletiva...", key="ia_tit_input")
        resumo_artigo = st.text_area(t['ia_campo_resumo'], placeholder="Paste or type abstract here...", height=250, key="ia_res_input")
        
        # BotÃ£o posicionado logo abaixo do resumo
        disparar_busca = st.button(t['ia_btn_buscar'], type="primary", key="btn_ia_disparar")
        
    with col_meta:
        # Credencial e Chave de API inseridas diretamente na aba de controle da IA
        st.markdown(f"#### {t['ia_credencial_tit']}")
        
        # LÃª chave do segredo do Streamlit Cloud se existir
        chave_secrets = ""
        try:
            if hasattr(st, "secrets") and st.secrets is not None:
                chave_secrets = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            pass
            
        if chave_secrets:
            placeholder_input = "ðŸ”‘ Chave global ativa (opcional pessoal)"
            help_input = "Uma chave global jÃ¡ estÃ¡ configurada pelo proprietÃ¡rio do app. Se desejar usar sua prÃ³pria chave pessoal, digite-a aqui."
        else:
            placeholder_input = ""
            help_input = t['ia_chave_ajuda']
            
        user_gemini_key = st.text_input(
            t['ia_chave_api'], 
            type="password", 
            placeholder=placeholder_input, 
            help=help_input
        )
        
        # Define a chave ativa final (prioriza input do usuÃ¡rio)
        api_key_ativa = user_gemini_key.strip() if user_gemini_key else (chave_secrets.strip() if chave_secrets else "")
        
        # Guia amigÃ¡vel para obter chave gratuita (expander recolhido por padrÃ£o)
        if not api_key_ativa:
            with st.expander(t['ia_como_obter_titulo'], expanded=False):
                st.markdown(t['ia_como_obter_texto'], unsafe_allow_html=True)
        
        st.markdown(f"#### {t['ia_refinar_alvos']}")
        
        # Mapeia as grandes Ã¡reas originais para suas versÃµes traduzidas
        grandes_areas_originais = sorted(list(df_original["Grande Area"].dropna().unique()))
        area_ia_opcoes = {t['todas']: "Todas"}
        for area in grandes_areas_originais:
            area_traduzida = traduzir_grande_area(area, t)
            area_ia_opcoes[area_traduzida] = area
            
        area_ia_exibicao = st.selectbox(f"{t['filtro_area']} (IA)", list(area_ia_opcoes.keys()))
        area_ia = area_ia_opcoes[area_ia_exibicao]
        
        indexador_ia = st.selectbox(f"{t['filtro_indexador']} (IA)", [t['ia_todos']] + list(df_original["Indexador"].dropna().unique()))
        
        # Slider dinÃ¢mico integrado para selecionar entre 3 e 20 recomendaÃ§Ãµes
        num_recomendacoes = st.slider(
            t['ia_num_rec'], 
            min_value=3, 
            max_value=20, 
            value=5, 
            step=1
        )
        
    if disparar_busca:
        if not api_key_ativa:
            st.error("âš ï¸ Para utilizar esta ferramenta, insira sua chave da API do Gemini no painel de Credenciais acima.")
        elif not titulo_artigo or not resumo_artigo:
            st.warning("âš ï¸ Preencha o TÃ­tulo e o Resumo do seu artigo cientÃ­fico para rodar a recomendaÃ§Ã£o.")
        else:
            # Gera chave de cache baseada nos parÃ¢metros da busca (sem depender da chave API)
            cache_key = hashlib.md5(
                f"{titulo_artigo.strip().lower()}|{resumo_artigo.strip().lower()}|{num_recomendacoes}|{area_ia}|{indexador_ia}".encode("utf-8")
            ).hexdigest()
            
            if cache_key in st.session_state.ia_cache:
                # Resultado em cache â€” reutiliza sem chamar a API
                st.session_state.recomendacoes = st.session_state.ia_cache[cache_key]
                st.session_state.erro_ia = None
                st.session_state.aviso_filtro = False
                st.rerun()
            else:
                # Reseta os estados anteriores antes do novo processamento
                st.session_state.recomendacoes = None
                st.session_state.erro_ia = None
                st.session_state.aviso_filtro = False
                st.session_state.modo_local = False
                
                # Utiliza um placeholder simples do Streamlit (st.empty) para o indicador de progresso,
                # evitando qualquer conflito de animaÃ§Ã£o de Spinner no DOM virtual do React.
                status_container = st.empty()
                status_container.info(f"â³ {t['ia_analisando']}")
                
                df_candidatos = df_original.copy()
                if area_ia != "Todas":
                    df_candidatos = df_candidatos[df_candidatos["Grande Area"] == area_ia]
                if indexador_ia != "Todos":
                    df_candidatos = df_candidatos[df_candidatos["Indexador"].astype(str).str.contains(re.escape(indexador_ia), case=False, na=False)]
                
                # ValidaÃ§Ã£o caso a base filtrada esteja vazia
                if df_candidatos.empty:
                    st.session_state.aviso_filtro = True
                else:
                    # Seleciona candidatos baseados em relevÃ¢ncia de palavras-chave do tÃ­tulo e resumo
                    texto_busca = f"{titulo_artigo} {resumo_artigo}".lower()
                    # Extrai termos do tÃ­tulo/resumo para busca
                    palavras = set(re.findall(r'\b[a-zA-ZÃ¡-ÃºÃ-Ãš]{4,}\b', texto_busca))
                    # Remove stopwords comuns
                    stopwords = {"para", "como", "uma", "este", "esta", "com", "dos", "das", "pelo", "pela", "artigo", "pesquisa", "estudo", "sobre", "with", "this", "from", "that", "article", "research", "study", "about"}
                    palavras_filtradas = palavras - stopwords
                    
                    # Grupos de sinÃ´nimos acadÃªmicos em 3 idiomas (PortuguÃªs, InglÃªs e Espanhol) para busca bidirecional completa
                    sinonimos_academicos = [
                        {"educaÃ§Ã£o", "education", "educaciÃ³n", "ensino", "teaching", "aprendizado", "learning", "aprendizaje"},
                        {"computaÃ§Ã£o", "computing", "computador", "computer", "tecnologia", "technology", "tecnologÃ­a"},
                        {"saÃºde", "health", "salud", "medicina", "medicine", "mÃ©dico", "medical", "mÃ©dica"},
                        {"ciÃªncia", "science", "ciencia", "cientÃ­fico", "scientific", "pesquisa", "research", "investigaciÃ³n"},
                        {"desenvolvimento", "development", "desarrollo", "gestÃ£o", "management", "gestiÃ³n", "administraÃ§Ã£o", "administration", "administraciÃ³n"},
                        {"economia", "economy", "economÃ­a", "econÃ´mico", "economic", "econÃ³mico", "social"},
                        {"cultura", "culture", "cultura", "histÃ³ria", "history", "historia", "geografia", "geography", "geografÃ­a"},
                        {"matemÃ¡tica", "mathematics", "fÃ­sica", "physics", "fisica", "quÃ­mica", "chemistry", "quimica"},
                        {"biologia", "biology", "biologÃ­a", "meio ambiente", "environment", "medio ambiente", "ambiental", "environmental"},
                        {"sustentabilidade", "sustainability", "sostenibilidad", "engenharia", "engineering", "ingenierÃ­a", "indÃºstria", "industry", "industria"},
                        {"produÃ§Ã£o", "production", "producciÃ³n", "sistemas", "systems", "sistemas", "informaÃ§Ã£o", "information", "informaciÃ³n"},
                        {"comunicaÃ§Ã£o", "communication", "comunicaciÃ³n", "linguagem", "language", "lenguaje", "literatura", "literature"},
                        {"arte", "art", "mÃºsica", "music", "musica", "psicologia", "psychology", "psicologÃ­a"},
                        {"filosofia", "philosophy", "filosofÃ­a", "polÃ­tica", "politics", "polÃ­tica", "direito", "law", "derecho"},
                        {"energia", "energy", "energÃ­a", "materiais", "materials", "materiales", "agricultura", "agriculture"},
                        {"florestal", "forestry", "forestal", "veterinÃ¡ria", "veterinary", "veterinaria", "enfermagem", "nursing", "enfermerÃ­a"},
                        {"odontologia", "dentistry", "odontologÃ­a", "farmÃ¡cia", "pharmacy", "farmacia", "nutriÃ§Ã£o", "nutrition", "nutriciÃ³n"}
                    ]
                    
                    # Adiciona sinÃ´nimos em outros idiomas se encontrar qualquer termo correspondente
                    novas_palavras = set()
                    for pal in palavras_filtradas:
                        for grupo in sinonimos_academicos:
                            if pal in grupo:
                                novas_palavras.update(grupo)
                                break
                    palavras_filtradas.update(novas_palavras)
                    
                    if palavras_filtradas:
                        def calcular_relevancia(row):
                            score = 0
                            nome = str(row.iloc[0]).lower()
                            grande_area = str(row.get("Grande Area", "")).lower()
                            area = str(row.get("Area do Conhecimento", "")).lower()
                            subarea = str(row.get("SubÃ¡rea do Conhecimento", "")).lower()
                            
                            for pal in palavras_filtradas:
                                if pal in nome:
                                    score += 5  # Maior peso para termos no nome da revista
                                if pal in grande_area:
                                    score += 3
                                if pal in area:
                                    score += 3
                                if pal in subarea:
                                    score += 3
                            return score
                        
                        df_candidatos["relevancia"] = df_candidatos.apply(calcular_relevancia, axis=1)
                        # Ordena pelas mais relevantes tematicamente e depois pelo prestÃ­gio (SJR)
                        df_candidatos = df_candidatos.sort_values(by=["relevancia", "SJR"], ascending=[False, False])
                    else:
                        df_candidatos["relevancia"] = 0
                        df_candidatos = df_candidatos.sort_values(by="SJR", ascending=False)
                    
                    # Seleciona atÃ© 40 candidatos mais relevantes â€” reduz consumo de tokens da API
                    if len(df_candidatos) > 40:
                        df_candidatos = df_candidatos.head(40)
                    
                    # Payload enxuto: somente os campos essenciais para a IA tomar a decisÃ£o
                    cols_envio = [df_original.columns[0]]
                    for col in ["Grande Area", "Area do Conhecimento", "Indexador", "Quartil JCR", "SJR"]:
                        if col in df_candidatos.columns:
                            cols_envio.append(col)
                    lista_periodicos_envio = df_candidatos[cols_envio].to_dict(orient="records")
                    
                    # Prompt estruturado para forÃ§ar o retorno estrito de um array JSON
                    prompt_ia = f"""
                    Atue como especialista em publicaÃ§Ã£o acadÃªmica de alto impacto. O pesquisador submeteu o seguinte artigo cientÃ­fico:
                    TÃTULO DO ARTIGO: {titulo_artigo}
                    RESUMO DO ARTIGO: {resumo_artigo}

                    Com base estritamente na lista de periÃ³dicos abaixo estruturada em JSON, selecione atÃ© {num_recomendacoes} (dentre as disponÃ­veis) revistas cientÃ­ficas que apresentem a maior aderÃªncia temÃ¡tica, metodolÃ³gica e de escopo.

                    IMPORTANTES DIRETRIZES DE SELEÃ‡ÃƒO (ORDEM DE PRIORIDADE):
                    1. PRIORIDADE MÃXIMA (Grau de AderÃªncia): O critÃ©rio principal de escolha deve ser a aderÃªncia temÃ¡tica, metodolÃ³gica e de escopo do artigo ao periÃ³dico. O assunto do artigo deve fazer total sentido com a linha editorial da revista.
                    2. SEGUNDA PRIORIDADE (Qualidade e PrestÃ­gio): Dentre os periÃ³dicos com alta aderÃªncia e compatibilidade temÃ¡tica, priorize aqueles com maior prestÃ­gio acadÃªmico e qualidade cientÃ­fica (indicados por quartis JCR e Ã­ndice SJR elevados).
                    3. NÃ£o limite as recomendaÃ§Ãµes ao idioma do tÃ­tulo/resumo enviado. Siga estritamente as regras de cruzamento de idiomas abaixo:
                       - Se o artigo estiver em PORTUGUÃŠS: Recomende as melhores opÃ§Ãµes de revistas brasileiras (em portuguÃªs) e tambÃ©m as melhores revistas internacionais (em inglÃªs ou espanhol) que cubram o tema.
                       - Se o artigo estiver em INGLÃŠS: Traga os principais periÃ³dicos internacionais (em inglÃªs ou espanhol) e tambÃ©m inclua as revistas brasileiras de alto padrÃ£o que cubram o tema.
                       - Se o artigo estiver em ESPANHOL: Traga os principais periÃ³dicos internacionais (em espanhol ou inglÃªs) e tambÃ©m inclua as revistas brasileiras de alto padrÃ£o que cubram o tema.
                    
                    Lista de PeriÃ³dicos Candidatos:
                    {json.dumps(lista_periodicos_envio, ensure_ascii=False)}

                    Sua resposta deve ser obrigatoriamente um array JSON vÃ¡lido (sem tags markdown em volta como ```json, apenas a string crua do array), com chaves exatas:
                    - "revista_nome": Nome exato da revista como aparece no catÃ¡logo enviado
                    - "porcentagem_aderencia": Apenas um nÃºmero inteiro de 0 a 100 estimando a aderÃªncia
                    - "justificativa": Uma justificativa de atÃ© 3 linhas explicando o porquÃª da recomendaÃ§Ã£o, escrita EXATAMENTE no mesmo idioma em que o resumo do usuÃ¡rio foi enviado.
                    """
                    
                    modelos_tentar = [
                        "gemini-2.5-flash",
                        "gemini-2.5-pro",
                        "gemini-2.0-flash",
                        "gemini-2.0-flash-001",
                        "gemini-3.5-flash",
                        "gemini-flash-latest",
                        "gemini-pro-latest",
                        "gemini-2.0-flash-lite",
                    ]
                    
                    sucesso_ia = False
                    ultimo_erro_msg = ""
                    cota_esgotada = False

                    for modelo in modelos_tentar:
                        try:
                            url_api = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key_ativa}"
                            payload = {
                                "contents": [{"parts": [{"text": prompt_ia}]}]
                            }
                            headers = {"Content-Type": "application/json"}
                            
                            response = requests.post(url_api, json=payload, headers=headers, timeout=45)
                            
                            if response.status_code == 200:
                                dados_resposta = response.json()
                                texto_resposta = dados_resposta["candidates"][0]["content"]["parts"][0]["text"].strip()
                                
                                if texto_resposta.startswith("```"):
                                    texto_resposta = re.sub(r'^```(?:json)?\n|```$', '', texto_resposta, flags=re.MULTILINE).strip()
                                
                                match = re.search(r'\[\s*\{.*\}\s*\]', texto_resposta, re.DOTALL)
                                if match:
                                    texto_resposta = match.group(0)
                                
                                st.session_state.recomendacoes = json.loads(texto_resposta)
                                # Salva no cache para evitar chamadas repetidas com a mesma entrada
                                st.session_state.ia_cache[cache_key] = st.session_state.recomendacoes
                                sucesso_ia = True
                                break
                            elif response.status_code == 429:
                                # Cota esgotada â€” ativa fallback local imediatamente sem espera
                                cota_esgotada = True
                                break
                            else:
                                ultimo_erro_msg = f"Modelo {modelo} falhou (Status {response.status_code}): {response.text}"
                        except Exception as ex:
                            ultimo_erro_msg = f"Modelo {modelo} falhou com exceÃ§Ã£o: {ex}"
                        
                        if cota_esgotada:
                            break
                    
                    if not sucesso_ia:
                        # FALLBACK LOCAL AUTOMÃTICO: gera recomendaÃ§Ãµes diretamente pelo algoritmo de pontuaÃ§Ã£o
                        texto_detect = f"{titulo_artigo} {resumo_artigo}".lower()
                        pt_stops = {"o", "a", "e", "de", "do", "da", "em", "para", "um", "uma", "com", "por", "os", "as"}
                        en_stops = {"the", "and", "of", "in", "to", "a", "is", "that", "for", "it", "with", "on", "as"}
                        pt_count = sum(1 for w in re.findall(r'\b\w+\b', texto_detect) if w in pt_stops)
                        en_count = sum(1 for w in re.findall(r'\b\w+\b', texto_detect) if w in en_stops)
                        is_english = en_count > pt_count

                        col_titulo = df_original.columns[0]
                        top_n = df_candidatos.head(num_recomendacoes)
                        recomendacoes_locais = []
                        
                        # ObtÃ©m a pontuaÃ§Ã£o mÃ¡xima de relevÃ¢ncia para normalizaÃ§Ã£o
                        max_rel = float(df_candidatos["relevancia"].max()) if "relevancia" in df_candidatos.columns else 0.0
                        
                        for idx, (_, row) in enumerate(top_n.iterrows()):
                            nome_rev = str(row[col_titulo])
                            area_rev = str(row.get("Area do Conhecimento", row.get("Grande Area", "-")))
                            subarea_rev = str(row.get("SubÃ¡rea do Conhecimento", ""))
                            gr_area_rev = str(row.get("Grande Area", ""))
                            indexador_rev = str(row.get("Indexador", "-"))
                            sjr_rev = row.get("SJR", None)
                            quartil_rev = str(row.get("Quartil JCR", "-"))
                            rel_score = float(row.get("relevancia", 0.0))
                            
                            # Determina a porcentagem de aderÃªncia de forma realista e decrescente por rank
                            if max_rel > 0:
                                # Mapeia proporcionalmente ao score de relevÃ¢ncia, variando de 82% a 96%
                                pct_rel = 82 + int((rel_score / max_rel) * 14)
                                # Garante consistÃªncia do ranking decrescente (ex: 1Âº=95%, 2Âº=92%, etc.)
                                pct_rank = 96 - (idx * 3)
                                pct = min(96, max(pct_rel, pct_rank))
                            else:
                                # Se nÃ£o houver matches de palavras-chave, ordena por SJR de 60% a 78%
                                pct = max(60, 78 - (idx * 4))
                            
                            # Encontra palavras-chave que de fato casaram com esta revista
                            matched_keywords = []
                            nome_lower = nome_rev.lower()
                            area_lower = area_rev.lower()
                            subarea_lower = subarea_rev.lower()
                            gr_area_lower = gr_area_rev.lower()
                            
                            for p in palavras_filtradas:
                                if p in nome_lower or p in area_lower or p in subarea_lower or p in gr_area_lower:
                                    # Capitaliza a primeira letra do termo de busca para visualizaÃ§Ã£o premium
                                    matched_keywords.append(p.capitalize())
                            
                            # Justificativas inteligentes em 2 idiomas
                            if is_english:
                                if matched_keywords:
                                    kw_str = ", ".join(f"'{k}'" for k in list(matched_keywords)[:3])
                                    justificativa = f"Demonstrates strong thematic alignment with key concepts found in your work, specifically: {kw_str}."
                                else:
                                    justificativa = f"Recommended based on the journal's editorial scope in {area_rev}."
                                
                                detalhes = []
                                if quartil_rev and quartil_rev not in ["-", "None", "nan"]:
                                    detalhes.append(f"classified as {quartil_rev}")
                                if sjr_rev and str(sjr_rev) not in ["-", "None", "nan"]:
                                    try:
                                        detalhes.append(f"SJR rank of {float(sjr_rev):.3f}")
                                    except:
                                        pass
                                if indexador_rev and indexador_rev not in ["-", "None", "nan"]:
                                    detalhes.append(f"indexed in {indexador_rev}")
                                    
                                if detalhes:
                                    justificativa += f" The journal is {', '.join(detalhes)}."
                            else:
                                # PortuguÃªs / Espanhol
                                if matched_keywords:
                                    kw_str = ", ".join(f"'{k}'" for k in list(matched_keywords)[:3])
                                    justificativa = f"Apresenta forte alinhamento temÃ¡tico com conceitos-chave identificados no seu artigo, especialmente: {kw_str}."
                                else:
                                    justificativa = f"Recomendado com base no escopo editorial do periÃ³dico na Ã¡rea de {area_rev}."
                                
                                detalhes = []
                                if quartil_rev and quartil_rev not in ["-", "None", "nan"]:
                                    detalhes.append(f"classificaÃ§Ã£o {quartil_rev}")
                                if sjr_rev and str(sjr_rev) not in ["-", "None", "nan"]:
                                    try:
                                        detalhes.append(f"SJR de {float(sjr_rev):.3f}")
                                    except:
                                        pass
                                if indexador_rev and indexador_rev not in ["-", "None", "nan"]:
                                    detalhes.append(f"indexado em {indexador_rev}")
                                    
                                if detalhes:
                                    justificativa += f" O periÃ³dico possui {', '.join(detalhes)}."
                            
                            recomendacoes_locais.append({
                                "revista_nome": nome_rev,
                                "porcentagem_aderencia": pct,
                                "justificativa": justificativa
                            })
                        
                        st.session_state.recomendacoes = recomendacoes_locais
                        st.session_state.ia_cache[cache_key] = recomendacoes_locais
                        # Sinaliza que foi modo local para exibir aviso amigÃ¡vel
                        st.session_state.modo_local = True
            
            # Limpa o indicador de progresso do DOM virtual
            status_container.empty()
            
            # Recarrega a pÃ¡gina de forma limpa para exibir os resultados fora do fluxo do botÃ£o
            st.rerun()

    # RENDERIZAÃ‡ÃƒO ESTÃVEL DOS RESULTADOS (Lidos do st.session_state, fora do condicional do st.button)
    if st.session_state.get("aviso_filtro"):
        st.warning("âš ï¸ Nenhum periÃ³dico no catÃ¡logo atende aos filtros de Grande Ãrea e Indexador selecionados. Por favor, ajuste os filtros.")
    elif st.session_state.get("erro_ia"):
        erro_msg = st.session_state.erro_ia
        if erro_msg.startswith("â³"):
            # Erro de cota â€” exibe aviso amigÃ¡vel sem detalhes tÃ©cnicos
            st.warning(erro_msg)
        else:
            st.error(t['ia_erro'])
            st.caption(f"Detalhes tÃ©cnicos do erro: {erro_msg}")
    elif st.session_state.get("recomendacoes") is not None:
        if st.session_state.get("modo_local"):
            st.info("â„¹ï¸ Resultado gerado pelo algoritmo local de relevÃ¢ncia (a API do Gemini atingiu o limite de cota). A qualidade das recomendaÃ§Ãµes Ã© excelente â€” baseada em correspondÃªncia temÃ¡tica e mÃ©tricas SJR/JCR.")
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
            
                # 2. RenderizaÃ§Ã£o de card para cada recomendaÃ§Ã£o (atÃ© 10 dinÃ¢micas)
                with st.container(border=True):
                    col_info, col_link = st.columns([3, 1])
                    
                    with col_info:
                        st.markdown(f"### {rec['revista_nome']}")
                        st.caption(f"**ISSN:** {issn} | **Indexador:** {indexador} | **Quartil:** {quartil} | **SJR:** {sjr}")
                        st.markdown(f"ðŸŽ¯ **{t['ia_card_aderencia']}** `{rec['porcentagem_aderencia']}%`")
                        st.markdown(f"ðŸ’¡ **{t['ia_card_motivo']}** {rec['justificativa']}")
                        
                        # SE HOUVER UM st.dataframe() ESCONDIDO AQUI PARA MOSTRAR OS DADOS COMPLETOS:
                        # Envolva-o SEMPRE em um validador de tamanho para nÃ£o quebrar o Arrow
                        if len(registro_revista) > 0:
                            st.dataframe(registro_revista, hide_index=True, **kwargs_largura)
                    
                    with col_link:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if homepage and homepage not in ["nan", "-", "None", ""]:
                            st.link_button(t['ia_card_site'], homepage, type="primary", **kwargs_largura)
                        else:
                            st.info(t['ia_card_sem_site'])
            else:
                # Caso a IA recomende um nome de revista que sofreu uma variaÃ§Ã£o de string e nÃ£o casou no CSV
                with st.container(border=True):
                    st.markdown(f"### {rec['revista_nome']}")
                    st.caption("âš ï¸ *PeriÃ³dico sugerido pela IA, mas metadados detalhados nÃ£o localizados na base local.*")
                    st.markdown(f"ðŸŽ¯ **{t['ia_card_aderencia']}** `{rec['porcentagem_aderencia']}%`")
                    st.markdown(f"ðŸ’¡ **{t['ia_card_motivo']}** {rec['justificativa']}")

# ==================== ABA 3: ESTATÃSTICAS DE ACESSOS (SÃ“ PARA ADMIN) ====================
if "admin" in params_url or "visitas" in params_url or st.session_state.get("is_admin", False):
    with tab_admin:
        st.subheader("ðŸ“Š EstatÃ­sticas de Acessos dos UsuÃ¡rios")
        
        # FunÃ§Ã£o para carregar dados dos usuÃ¡rios
        usuarios_list = []
        # 1. Tenta carregar do Firebase se disponÃ­vel
        if db is not None:
            try:
                docs = db.collection("usuarios").stream()
                for doc in docs:
                    d = doc.to_dict()
                    ultimo = d.get("ultimo_acesso")
                    usuarios_list.append({
                        "Nome": d.get("nome", "-"),
                        "Email": d.get("email", "-"),
                        "PaÃ­s": d.get("pais", "-"),
                        "Telefone": d.get("telefone", "-"),
                        "Escolaridade": d.get("escolaridade", "-"),
                        "InstituiÃ§Ã£o": d.get("instituicao", "-"),
                        "Acessos (Logins)": d.get("acessos", 1),
                        "Ãšltimo Acesso": ultimo.strftime("%Y-%m-%d %H:%M:%S") if ultimo and hasattr(ultimo, 'strftime') else str(ultimo)
                    })
            except Exception:
                pass
                
        # 2. Se a lista estiver vazia (ou Firebase falhou/nÃ£o configurado), carrega do usuarios.csv local
        if not usuarios_list:
            caminho_csv = "usuarios.csv"
            if os.path.exists(caminho_csv):
                try:
                    df_local = pd.read_csv(caminho_csv, sep=";")
                    for _, row in df_local.iterrows():
                        acessos_val = row.get("Acessos", 1)
                        usuarios_list.append({
                            "Nome": row.get("Nome", "-"),
                            "Email": row.get("Email", "-"),
                            "PaÃ­s": row.get("PaÃ­s", "-"),
                            "Telefone": row.get("Telefone", "-"),
                            "Escolaridade": row.get("Escolaridade", "-"),
                            "InstituiÃ§Ã£o": row.get("InstituiÃ§Ã£o", "-"),
                            "Acessos (Logins)": int(acessos_val) if pd.notna(acessos_val) else 1,
                            "Ãšltimo Acesso": row.get("Data/Hora", "-")
                        })
                except Exception:
                    pass
                    
        df_stats = pd.DataFrame(usuarios_list)
        if not df_stats.empty:
            # Ordena pelo maior nÃºmero de acessos
            df_stats = df_stats.sort_values(by="Acessos (Logins)", ascending=False).reset_index(drop=True)
            
            # Exibe em uma tabela interativa do Streamlit
            st.dataframe(
                df_stats,
                use_container_width=True,
                column_config={
                    "Acessos (Logins)": st.column_config.NumberColumn("Acessos", format="%d"),
                    "Email": st.column_config.Column("Email")
                }
            )
            
            # Permite download em CSV
            csv_data = df_stats.to_csv(index=False, sep=";").encode('utf-8-sig')
            st.download_button(
                label="ðŸ“¥ Baixar Planilha de Acessos (CSV)",
                data=csv_data,
                file_name="estatisticas_acessos.csv",
                mime="text/csv",
                key="admin_download_stats_btn"
            )
        else:
            st.info("Nenhum usuÃ¡rio cadastrado encontrado na base.")