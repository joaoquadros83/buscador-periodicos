import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# -----------------------------------------------------------------------------
# Safe imports: avoid crashing the whole app if a service module is missing
# -----------------------------------------------------------------------------
try:
    from services.discovery_recommender import DiscoveryRecommender
    from services.similar_articles_finder import SimilarArticlesFinder
    from services.article_evaluator import ArticleEvaluator
    from services.cache_manager import CacheManager
    from utils.logger import AnonymousLogger, get_anonymous_logger
except Exception as e:
    try:
        st.warning(f"Service imports failed: {e}")
    except Exception:
        pass
    DiscoveryRecommender = None
    SimilarArticlesFinder = None
    ArticleEvaluator = None
    CacheManager = None
    AnonymousLogger = None
    get_anonymous_logger = None


def get_discovery_recommender(df_local, api_key_gemini=None, h_index_author=5):
    if DiscoveryRecommender is None:
        raise RuntimeError("DiscoveryRecommender is not available")
    return DiscoveryRecommender(df_local=df_local, api_key_gemini=api_key_gemini, h_index_author=h_index_author)


def call_hybrid_api(title: str, abstract: str, api_url: str, top_n: int = 10,
                    min_year: int = 2021, max_apc_usd: float = None,
                    max_decision_days: int = None, require_oa: bool = False) -> dict:
    import requests
    payload = {
        "title": title,
        "abstract": abstract,
        "top_n": top_n,
        "min_year": min_year,
        "max_apc_usd": max_apc_usd,
        "max_decision_days": max_decision_days,
        "require_oa": require_oa,
        "generate_justifications": True
    }
    response = requests.post(f"{api_url}/recommend", json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def call_discovery_api(title: str, abstract: str, api_url: str, top_n: int = 20,
                       idioma: str = "Português") -> dict:
    import requests
    payload = {
        "title": title,
        "abstract": abstract,
        "top_n": top_n,
        "idioma": idioma
    }
    response = requests.post(f"{api_url}/recommend/discovery", json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


def get_similar_articles_finder(email_openalex=None):
    if SimilarArticlesFinder is None:
        raise RuntimeError("SimilarArticlesFinder is not available")
    return SimilarArticlesFinder(email_openalex=email_openalex)


def get_article_evaluator(df_local, ollama_model="llama3"):
    if ArticleEvaluator is None:
        raise RuntimeError("ArticleEvaluator is not available")
    return ArticleEvaluator(df_local=df_local, ollama_model=ollama_model)


def get_cache_manager():
    if CacheManager is None:
        return None
    return CacheManager()


# -----------------------------------------------------------------------------
# Defer heavy UI content until after Streamlit core setup
# -----------------------------------------------------------------------------
def build_terms_text(lang):
    if lang == "English":
        return '''### SciPubs Terms of Use and Privacy Policy

**Last Updated:** July 13, 2026

**1. INTRODUCTION AND ACCEPTANCE**

1.1. Welcome to SciPubs: The Researcher's Portal ("Platform"). This document ("Terms") governs your relationship with our Platform, establishing the conditions of use and personal data processing practices.

1.2. ACEPTANCE: By clicking the "I have read and accept the Terms of Use" button and completing your registration, you ("Data Subject") declare to have read, understood, and fully agreed with all provisions contained herein, expressing your free, informed, and unambiguous consent for the processing of your personal data for the purposes described herein. If you do not agree with these Terms, you should not use the Platform.

**2. PURPOSE AND GRATUITY**

2.1. The Platform aims to assist researchers in the production and publication of scientific articles, offering a journal search tool, integrated with Artificial Intelligence (Google Gemini), and links to external academic resources.

2.2. The access and use of all functionalities of the Platform are, as of the present date, entirely free. The Data Subject will be notified at least 30 (thirty) days in advance in the event of any changes to the business model.

**3. VOLUNTARY DONATIONS**

3.1. The Data Subject who wishes to support the maintenance and continuous development of the Platform may do so through voluntary donations, made in a specific section within the application.

3.2. ABSENCE OF COUNTERPART: Donations are acts of mere liberality and do not grant the donating Data Subject any exclusive rights, benefits, features, products, or services in return. The access and resources of the Platform remain identical for all Data Subjects, whether donors or not.

3.3. PAYMENT INTERMEDIARY: Donation transactions will be processed through third-party payment platforms (e.g., Buy Me a Coffee). By choosing to donate, the Data Subject will be directed to the intermediary's secure environment and will be subject to the Terms of Use and Privacy Policies of the respective payment platform.

3.4. DISCLAIMER: SciPubs is not responsible for any failures, security breaches, or data collection carried out by the payment platform. The financial transaction and the data associated with it (such as credit card data) are the responsibility of the chosen intermediary.

3.5. NON-REFUNDABLE: Due to their nature as voluntary acts without a counterpart, donations made are, as a rule, final and non-refundable.

**4. DATA PROCESSING AGENTS AND DPO**

4.1. SciPubs acts as the Controller of personal data. For the technical viability of the service, we use the infrastructure of Google LLC (Firebase), which acts as the Operator.

4.2. DATA PROTECTION OFFICER (DPO): For any questions regarding these Terms or the exercise of your rights, the Data Subject may contact our Officer via email: support@scipubs.com.

**5. PROCESSING OF PERSONAL DATA**

5.1. LEGAL BASIS: The processing of all personal data collected by the Platform is based exclusivelyively on the Data Subject's Consent, provided at the time of registration.

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
    if lang == "Español":
        return '''### Términos de Uso y Política de Privacidad de SciPubs

**Última Actualización:** 13 de julio de 2026

**1. INTRODUCCIÓN Y ACEPTACIÓN**

1.1. Bienvenido a SciPubs: El Portal del Investigador ("Plataforma"). Este documento ("Términos") rige su relación con nuestra Plataforma, estableciendo las condiciones de uso y las prácticas de tratamiento de datos personales.

1.2. ACEPTACIÓN: Al hacer clic en el botón "He leído y acepto los Términos de Uso" y completar su registro, usted ("Titular") declara haber leído, comprendido y aceptado íntegramente todas las disposiciones aquí contenidas, manifestando su consentimiento libre e informado para el tratamiento de sus datos personales. Si no está de acuerdo con estos Términos, no debe utilizar la Plataforma.

**2. OBJETO Y GRATUIDAD**

2.1. La Plataforma tiene como objetivo ayudar a los investigadores en la producción y publicación de artículos científicos, ofreciendo una herramienta de búsqueda de revistas, integrada con Inteligencia Artificial (Google Gemini), y enlaces a recursos académicos externos.

2.2. El acceso y uso de todas las funcionalidades de la Plataforma son, a la fecha actual, totalmente gratuitos. El Titular será notificado con al menos 30 (treinta) días de antelación en caso de cualquier cambio en el modelo de negocio.

**3. DONACIONES VOLUNTARIAS**

3.1. El Titular que desee apoyar el mantenimiento y el desarrollo continuo de la Plataforma podrá hacerlo a través de donaciones voluntarias, realizadas en una sección específica dentro de la aplicación.

3.2. AUSENCIA DE CONTRAPARTIDA: Las donaciones son actos de mera liberalidad y no confieren al Titular donante ningún derecho, beneficio, característica, producto o servicio exclusivo a cambio. El acceso y los recursos de la Plataforma siguen siendo idénticos para todos los Titulares, sean donantes o no.

3.3. INTERMEDIARIO DE PAGO: Las transacciones de donación se procesarán a través de plataformas de pago de terceros (ej. Buy Me a Coffee). Al optar por donar, el Titular será dirigido al entorno seguro del intermediario y estará sujeto a los Términos de Uso y Políticas de Privacidad de la respectiva plataforma de pago.

3.4. EXENCIÓN DE RESPONSABILIDAD: SciPubs no se hace responsable de posibles fallos, brechas de seguridad o la recopilación de datos realizada por la plataforma de pago. La transacción financiera y los datos asociados a ella (como los datos de la tarjeta de crédito) son responsabilidad del intermediario elegido.

3.5. NO REEMBOLSABLE: Debido a su naturaleza de acto voluntario sin contrapartida, las donaciones realizadas son, por regla general, finales y no reembolsables.

**4. AGENTES DE TRATAMIENTO DE DATOS Y DPO**

4.1. SciPubs actúa como Controlador de los datos personales. Para la viabilidad técnica del servicio, utilizamos la infraestructura de Google LLC (Firebase), que actúa como Operador.

4.2. OFICIAL DE PROTECCIÓN DE DATOS (DPO): Para cualquier consulta sobre estos Términos, el Titular puede contactar a nuestro Oficial a través del correo electrónico: support@scipubs.com.

**5. TRATAMIENTO DE DATOS PERSONALES**

5.1. BASE LEGAL: El tratamiento de todos los datos personales recopilados por la Plataforma se basa exclusivamente en el Consentimiento del Titular, proporcionado en el momento del registro.

5.2. DATOS RECOPILADOS PARA EL FUNCIONAMIENTO DE LA PLATAFORMA (OBLIGATORIO): Recopilamos los datos mínimos necesarios para fines específicos: Nombre Completo y Dirección de Correo Electrónico.

5.3. DATOS PARA FINES DE INVESTIGACIÓN DE USO (PROPÓSITO SECUNDARIO): Con su consentimiento específico, los datos podrán ser utilizados para la elaboración de estudios e investigaciones científicas. * GARANTÍA DE ANONIMIZACIÓN: Para esta finalidad, todos los datos serán previamente sometidos a un proceso de anonimización.

5.4. DATOS PARA INVESTIGACIÓN DE PERFIL DEMOGRÁFICO (OPCIONAL Y SENSIBLE): La Plataforma ofrece al Titular la oportunidad opcional de contribuir con investigaciones sobre diversidad e inclusión. La participación es opcional y utiliza un proceso de anonimización mejorado.

**6. DERECHOS DEL TITULAR**

6.1. El Titular tiene el derecho de, en cualquier momento: acceder a sus datos, corregir datos incompletos, solicitar eliminación o revocar el consentimiento.

**7. SEGURIDAD Y TRANSFERENCIA INTERNACIONAL**

7.1. Empleamos medidas técnicas y administrativas para proteger los datos personales. Los datos se almacenan en infraestructura de nube segura (Google Firebase).

7.2. TRANSFERENCIA INTERNACIONAL: Al utilizar la infraestructura global de Google, los datos personales pueden ser transferidos y procesados en servidores ubicados fuera de su país.

**8. CAMBIOS Y JURISDICCIÓN**

8.1. Estos Términos pueden ser actualizados. El Titular será notificado de cambios sustanciales.

8.2. JURISDICCIÓN: Para resolver cualquier disputa que surja de estos Términos, se elegirá la jurisdicción del tribunal donde se encuentra la sede del SciPubs, renunciendo expresamente a cualquier otra, por muy privilegiada que sea.'''
    return '''### Termos de Uso e Política de Privacidade do SciPubs

**Data da Última Atualização:** 13 de julho de 2026

**1. INTRODUÇÃO E ACEITAÇÃO**

1.1. Bem-vindo ao SciPubs: O Portal do Pesquisador ("Plataforma"). Este documento ("Termos") rege a sua relação com a nossa Plataforma, estabelecendo as condições de uso e as práticas de tratamento de dados pessoais.

1.2. ACEITAÇÃO: Ao clicar no botão "Eu li e aceito os Termos de Uso e Política de Privacidade" e concluir o seu cadastro, você ("Titular") declara ter lido, compreendido e concordado integralmente com todas as disposições aqui contidas, manifestando seu consentimento livre, informado e inequívoco para o tratamento de seus dados pessoais. Caso não concorde com estes Termos, você não deverá utilizar a Plataforma.

**2. OBJETO E GRATUIDADE**

2.1. A Plataforma tem como objetivo auxiliar pesquisadores na produção e publicação de artigos científicos, oferecendo uma ferramenta de busca em periódicos, integrada com Inteligência Artificial (Google Gemini), e links para recursos acadêmicos externos.

2.2. O acesso e uso de todas as funcionalidades da Plataforma são, na presente data, inteiramente gratuitos. O Titular será notificado com antecedência mínima de 30 (trinta) dias caso haja qualquer alteração no modelo de negócio.

**3. DOAÇÕES VOLUNTÁRIAS**

3.1. O Titular que desejar apoiar a manutenção e o desenvolvimento contínuo da Plataforma poderá fazê-lo através de doações voluntárias, realizadas em seção específica dentro do aplicativo.

3.2. AUSÊNCIA DE CONTRAPARTIDA: As doações são atos de mera liberalidade e não conferem ao Titular doador quaisquer direitos, benefícios, funcionalidades exclusivas, produtos ou serviços em contrapartida. O acesso e os recursos da Plataforma permanecem idênticos para todos os Titulares, doadores ou não.

3.3. INTERMEDIADOR DE PAGAMENTO: As transações de doação serão processadas por meio de plataformas de pagamento de terceiros (ex: Buy Me a Coffee). Ao optar por doar, o Titular será direcionado ao ambiente seguro do intermediador e estará sujeito aos Termos de Uso e Políticas de Privacidade da respectiva plataforma de pagamento.

3.4. ISENÇÃO DE RESPONSABILIDADE: O SciPubs não se responsabiliza por eventuais falhas, violações de segurança ou pela coleta de dados realizada pela plataforma de pagamento. A transação financeira e os dados a ela associados (como dados de cartão de crédito) são de responsabilidade do intermediador escolhido.

3.5. NÃO REEMBOLSO: Por sua natureza de ato voluntário e sem contrapartida, as doações realizadas são, em regra, finais e não reembolsáveis.

**4. AGENTES DE TRATAMIENTO E ENCARREGADO (DPO)**

4.1. Para os fins da LGPD, o SciPubs atua como Controlador dos dados pessoais. Para a viabilização técnica do serviço, utilizamos a infraestrutura da Google LLC (Firebase), que atua como Operadora.

4.2. ENCARREGADO PELO TRATAMENTO DE DADOS (DPO): Para qualquer questão relativa a estes Termos, o Titular poderá contatar nosso Encarregado através do e-mail: support@scipubs.com.

**5. TRATAMENTO DE DADOS PESSOAIS**

5.1. BASE LEGAL: O tratamento de todos os dados pessoais coletados pela Plataforma fundamenta-se exclusivamente no Consentimento do Titular, fornecido no ato do cadastro.

5.2. DADOS COLETADOS PARA FUNCIONAMENTO DA PLATAFORMA (OBRIGATÓRIO): Coletamos o mínimo de dados necessários para as seguintes finalidades específicas: Nome Completo e Endereço de E-mail.

5.3. DADOS PARA FINS DE PESQUISA DE USO (FINALIDADE SECUNDÁRIA): Com o seu consentimento específico, os dados poderão ser utilizados para a elaboração de estudos, artigos e pesquisas científicas. * GARANTIA DE ANONIMIZAÇÃO: Para esta finalidade, todos os dados serão previamente submetidos a um processo de anonimização.

5.4. DADOS PARA PESQUISA DE PERFIL DEMOGRÁFICO (OPCIONAL E SENSÍVEL): A Plataforma oferece ao Titular a oportunidade opcional de contribuir com pesquisas sobre diversidade e inclusão. A participação é opcional e utiliza anonimização reforçada.

**6. DIREITOS DO TITULAR**

6.1. O Titular tem o direito de, a qualquer momento: acessar seus dados, corrigir dados incompletos, solicitar a eliminação ou revogar o consentimento.

**7. SEGURANÇA E TRANSFERENCIA INTERNACIONAL**

7.1. Empregamos medidas técnicas e administrativas aptas a proteger os dados pessoais. Os dados são armazenados em infraestrutura de nuvem segura (Google Firebase).

7.2. TRANSFERÊNCIA INTERNACIONAL: Ao utilizar a infraestrutura global da Google, os dados pessoais do Titular podem ser transferidos e processados em servidores localizados fora do Brasil.

**8. ALTERAÇÕES E FORO**

8.1. Estes Termos poderão ser atualizados. Ocorrendo alterações substanciais, o Titular será notificado.

8.2. FORO: Para dirimir quaisquer controvérsias oriundas destes Termos, fica eleito o foro da Comarca da sede do SciPubs, com renúncia expressa a qualquer outro, por mais privilegiado que seja.
'''


@st.dialog("📄 Termos de Uso e Política de Privacidade / Terms of Use / Términos de Uso", width="large")
def modal_termos():
    lang = st.session_state.get('idioma', 'Português')
    texto_termos = build_terms_text(lang)
    st.markdown(texto_termos)

    fechar_btn = "Fechar"
    if lang == "English":
        fechar_btn = "Close"
    elif lang == "Español":
        fechar_btn = "Cerrar"

    if st.button(fechar_btn, type="primary"):
        st.rerun()


@st.dialog("❤️ Apoie o SciPubs! / Support SciPubs!", width="large")
def modal_doacao():
    lang = st.session_state.get('idioma', 'Português')
    if lang == "English":
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
    elif lang == "Español":
        st.markdown('''
        ### ¡Gracias por apoyar la Ciencia!
        Su donación voluntaria es fundamental para mantener nuestros servidores activos y continuar desarrollando nuevas herramientas tecnológicas para la comunidad académica y científica.

        **Cómo donar:**
        Utilizamos **Buy Me a Coffee**, una plataforma internacional segura. Es muy sencillo:
        1. Haga clic en el enlace de abajo para ir a nuestra página oficial.
        2. Elija la cantidad de "cafés" que desea donar (cada café representa una pequeña cantidad simbólica).
        3. Complete el pago de forma segura utilizando una tarjeta de crédito u otros métodos locales disponibles.

        👉 **[Haga clic aquí para donar a través de Buy Me a Coffee](https://buymeacoffee.com/scipubs)**

        *Importante: Su donación es completamente voluntaria y no exige ninguna contrapartida de servicios de nuestra plataforma.*
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
    firebase_info = dict(st.secrets["firebase"])
    firebase_info["private_key"] = firebase_info["private_key"].replace("\\n", "\n")
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


# 2. Criar ou Atualizar dados do usuário (Salvar histórico de busca)
def salvar_historico_usuario(usuario_id, termo_busca):
    user_ref = db.collection("usuarios").document(usuario_id)
    user_ref.set({
        "historico_buscas": firestore.ArrayUnion([termo_busca]),
        "ultimo_acesso": firestore.SERVER_TIMESTAMP
    }, merge=True)
    st.success(f"Busca por '{termo_busca}' salva no histórico!")


# 3. Ler dados do usuário
def obter_dados_usuario(usuario_id):
    user_ref = db.collection("usuarios").document(usuario_id)
    doc = user_ref.get()
    if doc.exists:
        return doc.to_dict()
    return None


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


def obter_imagem_local_base64(caminho_arquivo):
    try:
        if os.path.exists(caminho_arquivo):
            with open(caminho_arquivo, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode()
    except Exception:
        return ""
    return ""
