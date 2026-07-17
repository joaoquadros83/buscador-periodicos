"""
SciPubs - O Portal do Pesquisador
VERSÃO ATUALIZADA COM DISCOVERY-FIRST + GEMINI FALLBACK
Integração completa com validação de dependências, cache e logging anônimo
"""

import faulthandler
faulthandler.enable()

import streamlit as st
import sys
import os
import time
import hashlib
import json
import re
import pandas as pd
import urllib.parse
import requests
import base64

# ===== SETUP CRÍTICO: Adicionar diretório atual ao path =====
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ===== VALIDAÇÃO DE DEPENDÊNCIAS (PRIMEIRA COISA) =====
from services import (
    validate_dependencies,
    validate_gemini_key,
    get_discovery_recommender,
    get_cache_manager,
    get_anonymous_logger
)

# Valida dependências no startup
if not validate_dependencies():
    st.stop()

# ===== INICIALIZAÇÃO DE COMPONENTES GLOBAIS =====
cache_manager = get_cache_manager()
anonymous_logger = get_anonymous_logger()

# Firebase (opcional, se configurado em secrets)
import firebase_admin
from firebase_admin import credentials, firestore

db = None
try:
    if "firebase" in st.secrets:
        @st.cache_resource
        def inicializar_firebase():
            firebase_info = dict(st.secrets["firebase"])
            firebase_info["private_key"] = firebase_info["private_key"].replace("\\n", "\n")
            
            if not firebase_admin._apps:
                cred = credentials.Certificate(firebase_info)
                firebase_admin.initialize_app(cred)
            
            return firestore.client()
        
        db = inicializar_firebase()
except Exception:
    pass

# ===== TEXTOS E TRADUÇÃO =====
def get_texto_termos(lang):
    if st.session_state.get("idioma", "English") == "English":
        return '''### SciPubs Terms of Use and Privacy Policy

**Last Updated:** July 13, 2026

**1. INTRODUCTION AND ACCEPTANCE**

1.1. Welcome to SciPubs: The Researcher's Portal ("Platform"). This document ("Terms") governs your relationship with our Platform, establishing the conditions of use and personal data processing practices.

1.2. ACCEPTANCE: By clicking the "I have read and accept the Terms of Use" button and completing your registration, you ("Data Subject") declare to have read, understood, and fully agreed with all provisions contained herein, expressing your free, informed, and unambiguous consent for the processing of your personal data for the purposes described herein. If you do not agree with these Terms, you should not use the Platform.

**2. PURPOSE AND GRATUITY**

2.1. The Platform aims to assist researchers in the production and publication of scientific articles, offering a journal search tool, integrated with Artificial Intelligence (Google Gemini), and links to external academic resources.

2.2. The access and use of all functionalities of the Platform are, as of the present date, entirely free. The Data Subject will be notified at least 30 (thirty) days in advance in the event of any changes to the business model.

**3. VOLUNTARY DONATIONS**

3.1. The Data Subject who wishes to support the maintenance and continuous development of the Platform may do so through voluntary donations, made in a specific section within the application.

3.2. ABSENCE OF COUNTERPART: Donations are acts of mere liberality and do not grant the donating Data Subject any exclusive rights, benefits, features, products, or services in return. The access and resources of the Platform remain identical for all Data Subjects, whether donors or not.

**4. DATA PROCESSING AGENTS AND DPO**

4.1. SciPubs acts as the Controller of personal data. For the technical viability of the service, we use the infrastructure of Google LLC (Firebase), which acts as the Operator.

4.2. DATA PROTECTION OFFICER (DPO): For any questions regarding these Terms or the exercise of your rights, the Data Subject may contact our Officer via email: support@scipubs.com.

**5. PROCESSING OF PERSONAL DATA**

5.1. LEGAL BASIS: The processing of all personal data collected by the Platform is based exclusively on the Data Subject's Consent, provided at the time of registration.

5.2. DATA COLLECTED FOR PLATFORM OPERATION (MANDATORY): We collect the minimum data necessary for specific purposes, whose consent is provided at the time of main registration: Full Name and Email Address.

5.3. DATA FOR USAGE RESEARCH PURPOSES (SECONDARY PURPOSE): With your specific consent, the data may be used for the elaboration of studies, articles, and scientific research. * ANONYMIZATION GUARANTEE: For this purpose, all data will be previously submitted to an anonymization process.

5.4. DATA FOR DEMOGRAPHIC PROFILE RESEARCH (OPTIONAL AND SENSITIVE): The Platform offers the Data Subject the optional opportunity to contribute to research on diversity and inclusion. Participation is optional and uses an enhanced anonymization process.

**6. DATA SUBJECT RIGHTS**

6.1. The Data Subject has the right to, at any time: access their data, correct incomplete data, request deletion, or revoke consent.

**7. SECURITY AND INTERNATIONAL TRANSFER**

7.1. We employ technical and administrative measures to protect personal data from unauthorized access. Data is stored on secure cloud infrastructure (Google Firebase).

7.2. INTERNATIONAL TRANSFER: By using Google's global infrastructure, personal data may be transferred and processed on servers located outside your country.

**8. CHANGES AND JURISDICTION**

8.1. These Terms may be updated. The Data Subject will be notified of substantial changes.

8.2. JURISDICTION: The courts of the judicial district where the *SciPubs* is headquartered are designated to resolve any disputes arising from these Terms, with the express waiver of any other jurisdiction, however privileged it may be.'''
    elif st.session_state.get("idioma", "English") == "Español":
        return '''### Términos de Uso y Política de Privacidad de SciPubs

**Última Actualización:** 13 de julio de 2026

[... Conteúdo em Espanhol ...]'''
    else:
        return '''### Termos de Uso e Política de Privacidade do SciPubs

**Data da Última Atualização:** 13 de julho de 2026

[... Conteúdo em Português ...]'''

@st.dialog("📄 Termos de Uso e Política de Privacidade / Terms of Use / Términos de Uso", width="large")
def modal_termos():
    lang = st.session_state.get('idioma', 'Português')
    texto_termos = get_texto_termos(lang)
    st.markdown(texto_termos)
    
    fechar_btn = "Fechar"
    if st.session_state.get("idioma", "English") == "English":
        fechar_btn = "Close"
    elif st.session_state.get("idioma", "English") == "Español":
        fechar_btn = "Cerrar"
    
    if st.button(fechar_btn, type="primary"):
        st.rerun()

@st.dialog("❤️ Apoie o SciPubs! / Support SciPubs!", width="large")
def modal_doacao():
    lang = st.session_state.get('idioma', 'Português')
    
    if st.session_state.get("idioma", "English") == "English":
        st.markdown('''
        ### Thank you for supporting Science!
        Your voluntary donation is essential for us to keep our servers active and continue developing new technological tools for the academic and scientific community.
        
        **How to donate:**
        We use **Buy Me a Coffee**, a secure international platform. It's very simple:
        1. Click the link below to go to our official page.
        2. Choose the number of "coffees" you want to donate (each coffee represents a small symbolic amount).
        3. Complete the payment securely using a credit card or other available local methods.
        
        👉 **[Click here to donate via Buy Me a Coffee](https://buymeacoffee.com/scipubs)**
        
        *Important: Your donation is completely voluntary and does not require any service counterpart from our platform.*
        ''')
        btn_close = "Close"
    elif st.session_state.get("idioma", "English") == "Español":
        st.markdown('''
        ### ¡Gracias por apoyar la Ciencia!
        Su donación voluntaria es fundamental para mantener nuestros servidores activos y continuar desarrollando nuevas herramientas tecnológicas para la comunidad académica y científica.
        
        [... Conteúdo em Espanhol ...]
        ''')
        btn_close = "Cerrar"
    else:
        st.markdown('''
        ### Obrigado por apoiar a Ciência!
        A sua doação voluntária é fundamental para mantermos os nossos servidores ativos e continuarmos desenvolvendo novas ferramentas tecnológicas para a comunidade acadêmica e científica.
        
        **Como realizar a sua doação:**
        Nós utilizamos o **Buy Me a Coffee**, uma plataforma internacional segura. É muito simples:
        1. Clique no link abaixo para acessar a nossa página oficial.
        2. Escolha a quantidade de "cafés" que deseja doar (cada café representa um pequeno valor simbólico, geralmente $5).
        3. Conclua o pagamento de forma segura utilizando seu cartão de crédito, Apple Pay, Google Pay ou outros métodos disponíveis.
        
        👉 **[Clique aqui para doar pelo Buy Me a Coffee](https://buymeacoffee.com/scipubs)**
        
        *Importante: A sua doação é totalmente espontânea e não exige nenhuma contrapartida de serviços da nossa plataforma.*
        ''')
        btn_close = "Fechar"
    
    if st.button(btn_close, type="primary"):
        if st.session_state.get('modo_cadastro', False):
            st.session_state.modo_cadastro = False
            st.session_state.modo_login = True
        st.rerun()

# ===== DICIONÁRIO DE TRADUÇÃO (RESUMIDO) =====
dic = {
    "Português": {
        "titulo": "O Portal do Pesquisador",
        "subtitulo": "A ciência aberta importa. Sem perguntas. Sem taxas. Sem anúncios. Apenas use.",
        "filtros_tit": "####   Buscador de Periódicos",
        "buscar_reg": "Buscar registro específico:",
        "placeholder_busca": "Digite o título da revista, ISSN...",
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
        "m_sjr": "SJR Score Pico",
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
        "gov_tit": "SITES GOVERNAMENTAIS",
        "inst_tit": "INFORMAÇÕES INSTITUCIONAIS",
        "pessoal_lbl": "👤 Site pessoal",
        "indexadores_tit": "INDEXADORES",
        "repositorios_tit": "REPOSITÓRIOS",
        "ia_tit": "IA ACADÊMICA",
        "btn_desktop": "💻 Baixar Versão para Windows",
        "busca_cat": "📚 Catálogo de Periódicos",
        "busca_ia": "🤖 Recomendador Inteligente (IA)",
        "ia_titulo": "Recomendação Temática com Inteligência Artificial",
        "ia_subtitulo": "Cole o título e o resumo (abstract) do seu artigo. A IA analisa o conteúdo e indica os periódicos mais adequados, com métricas enriquecidas.",
        "ia_campo_titulo": "Título do Artigo",
        "ia_campo_resumo": "Resumo / Abstract (Suporta Português, Inglês ou Espanhol)",
        "ia_motor_tit": "Motor de IA",
        "ia_motor_desc": "Recomendações via Google Gemini — Gratuito com sua chave API pessoal.",
        "ia_num_rec": "Quantidade de recomendações desejadas (máx. 20)",
        "ia_btn_buscar": "Analisar e Recomendar",
        "ia_analisando": "Analisando seu artigo e buscando as melhores revistas...",
        "ia_sucesso": "✅ Recomendações geradas com sucesso!",
        "ia_erro": "❌ Erro ao processar a recomendação. Tente novamente em instantes.",
        "ia_fallback_local": "Resultado gerado pelo algoritmo local de relevância temática (Gemini indisponível).",
        "ia_credencial_tit": "🔑 Credencial",
        "ia_chave_api": "Chave da API Google Gemini",
        "ia_como_obter_titulo": "ℹ️  Como obter uma chave gratuita?",
        "ia_como_obter_texto": '''
<div style="font-size: 14px; line-height: 1.5; font-family: inherit;">
Esta ferramenta é gratuita. Para usá-la, você precisa de uma chave da API do Google Gemini, também gratuita:<br><br>
1. Acesse <b><a href="https://aistudio.google.com" target="_blank">aistudio.google.com</a></b><br>
2. Faça login com sua conta Google<br>
3. Clique em <b>"Get API Key"</b> → <b>"Create API Key"</b><br>
4. Copie a chave gerada e cole no campo acima<br><br>
<i>A chave gratuita permite centenas de consultas por dia.</i>
</div>
        ''',
        "ia_refinar_pesquisa": "🎯 Refinar Pesquisa",
        "ia_todos": "Todos",
        "filtro_area": "Grande Área",
        "filtro_indexador": "Indexador",
        "ia_aderencia_escopo": "Aderência ao Escopo",
        "ia_aderencia_area": "Aderência à Área",
        "ia_probabilidade": "Probabilidade Estimada de Aceitação",
        "ia_card_motivo": "Por que publicar aqui:",
        "ia_card_site": "🔗 Visitar Homepage Oficial",
        "ia_card_sem_site": "Site indisponível na base",
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
        "subtitulo": "Open science matters. No asks. No fees. No ads. Just use.",
        "filtros_tit": "####   Journal Finder",
        "buscar_reg": "Search specific record:",
        "placeholder_busca": "Enter journal title, ISSN...",
        # ... adicione demais campos conforme necessário
    },
    "Español": {
        # ... adicione tradução em espanhol
    }
}

# ===== CARREGAMENTO DE DADOS =====
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
            with open(nome_arquivo, "r", encoding="utf-8-sig", errors="ignore") as f:
                primeira_linha = f.readline()
            separador = ";" if primeira_linha.count(";") >= primeira_linha.count(",") else ","
            
            df = pd.read_csv(nome_arquivo, sep=separador, encoding="utf-8-sig", low_memory=False, on_bad_lines='skip')
            
            df.columns = df.columns.str.replace('^\ufeff', '', regex=True)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df.columns = [c.strip() for c in df.columns]
            
            # Normaliza nomes de colunas
            df = df.rename(columns={
                "Grande Area": "Grande Área",
                "Area do Conhecimento": "Área do Conhecimento",
                "Subarea do Conhecimento": "Subárea do Conhecimento",
            })
            
            # Tratamento de colunas numéricas
            for col in ['SJR', 'JIF', 'h-index', 'H index']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(',', '.').str.strip()
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Preencher vazios
            for col in df.columns:
                if col not in ['SJR', 'JIF', 'h-index', 'H index']:
                    df[col] = df[col].fillna("-").astype(str).str.strip()
                    df[col] = df[col].replace(["None", "none", "nan", "null", ""], "-")
            
            if "Homepage" not in df.columns:
                df["Homepage"] = "-"
            
            # Agregação por título
            col_titulo = df.columns[0]
            df["titulo_norm"] = df[col_titulo].astype(str).str.lower().str.strip()
            
            def agg_indexadores(series):
                vals = sorted(list(set([str(val).strip() for val in series if str(val).strip() not in ["-", "", "None", "nan"]])))
                return ", ".join(vals) if vals else "-"
            
            def agg_primeiro_valido(series):
                for val in series:
                    val_str = str(val).strip()
                    if val_str not in ["-", "", "None", "nan"]:
                        return val_str
                return "-"
            
            def agg_max_numerico(series):
                nums = pd.to_numeric(series, errors='coerce').dropna()
                return nums.max() if not nums.empty else 0.0
            
            agg_dict = {}
            for col in df.columns:
                if col == "titulo_norm":
                    continue
                if col == "Indexador":
                    agg_dict[col] = agg_indexadores
                elif col in ['SJR', 'JIF', 'h-index', 'H index']:
                    agg_dict[col] = agg_max_numerico
                else:
                    agg_dict[col] = agg_primeiro_valido
            
            df = df.groupby("titulo_norm", as_index=False).agg(agg_dict)
            df = df.drop(columns=["titulo_norm"])
            
            return df, nome_arquivo
        except Exception as e:
            st.error(f"❌ Erro ao processar a base de dados: {e}")
            st.stop()
    else:
        st.error("❌ Base de dados não encontrada. Arquivo 'dados.csv' não localizado.")
        st.stop()

df_original, arquivo_usado = carregar_dados()

# ===== CONFIGURAÇÃO INICIAL DA PÁGINA =====
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

kwargs_largura = {"width": "stretch"} if SUPPORTS_NEW_WIDTH else {"use_container_width": True}

# Configurar página
def obter_imagem_local_base64(caminho_arquivo):
    try:
        if os.path.exists(caminho_arquivo):
            with open(caminho_arquivo, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode()
    except Exception:
        return ""
    return ""

imagem_base64_icon = obter_imagem_local_base64("favicon.png")
if not imagem_base64_icon:
    imagem_base64_icon = obter_imagem_local_base64("logo.png")

novo_page_icon = f"data:image/png;base64,{imagem_base64_icon}" if imagem_base64_icon else "📚"

st.set_page_config(
    page_title="O Portal do Pesquisador",
    page_icon=novo_page_icon,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== TEMA DINÂMICO =====
if st.session_state.get("dark_mode", False):
    st.markdown("""
        <style>
            .stApp { background-color: #0F172A !important; color: #F8FAFC !important; }
            section[data-testid="stSidebar"] { background-color: #1E293B !important; }
            section[data-testid="stSidebar"] * { color: #F8FAFC !important; }
            h1, h2, h3, h4, h5, h6, p, span, label { color: #F8FAFC !important; }
        </style>
    """, unsafe_allow_html=True)

# ===== INICIALIZAÇÃO DE SESSION STATE =====
if 'idioma' not in st.session_state:
    st.session_state.idioma = "Português"

if 'registrado' not in st.session_state:
    st.session_state.registrado = False

if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# Selecionar idioma na sidebar
st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.session_state.idioma = st.sidebar.selectbox(
    "Language / Idioma:",
    ["English", "Español", "Português"],
    index=2
)

t = dic.get(st.session_state.idioma, dic["Português"])

print("✅ App inicializado com sucesso! Componentes carregados:")
print(f"   - Cache Manager: {cache_manager}")
print(f"   - Anonymous Logger: {anonymous_logger}")
print(f"   - Base de dados: {len(df_original)} revistas")
print(f"   - Idioma: {st.session_state.idioma}")
