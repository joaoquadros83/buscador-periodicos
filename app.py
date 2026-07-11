import streamlit as st
import pandas as pd
import urllib.parse
import base64
import json

# Tratamento de importação do google-generativeai com fallback seguro
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ModuleNotFoundError:
    HAS_GEMINI = False

# --- 1. CONFIGURAÇÃO ÚNICA DA PÁGINA (Mantém o Ícone e o Layout original) ---
def obter_imagem_local_base64(caminho_arquivo):
    try:
        with open(caminho_arquivo, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        return ""

imagem_base64_icon = obter_imagem_local_base64("st_static/favicon.png")
if not imagem_base64_icon:
    imagem_base64_icon = obter_imagem_local_base64("st_static/logo.png")

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

# --- 2. SISTEMA DE TRADUÇÃO MULTILÍNGUE COM RECURSOS DE IA ---
traducoes = {
    "pt": {
        "titulo": "Portal do Pesquisador",
        "subtitulo": "Buscador de Periódicos Científicos",
        "idioma": "Idioma / Language / Idioma",
        "busca_cat": "🔍 Catálogo de Periódicos",
        "busca_ia": "🧠 Recomendador Inteligente (IA)",
        "busca_placeholder": "Buscar por título, ISSN ou palavra-chave...",
        "filtro_area": "Filtrar por Grande Área",
        "filtro_conhecimento": "Filtrar por Área do Conhecimento",
        "filtro_indexador": "Filtrar por Indexador",
        "exibir_pag": "Exibir por página",
        "pag_lbl": "Página",
        "total_encontrado": "periódicos encontrados.",
        "sobre": "Sobre o Portal",
        "sobre_texto": "Este portal ajuda pesquisadores a identificar periódicos ideais para publicação de seus manuscritos científicos.",
        "ia_titulo": "Recomendação Temática com Inteligência Artificial",
        "ia_subtitulo": "Cole o título e o resumo (abstract) do seu artigo. A IA analisará nosso catálogo de periódicos e indicará as opções mais adequadas.",
        "ia_campo_titulo": "Título do Artigo",
        "ia_campo_resumo": "Resumo / Abstract (Suporta Português, Inglês ou Espanhol)",
        "ia_chave_api": "Chave API do Gemini (Google AI Studio)",
        "ia_chave_ajuda": "Você precisa de uma chave API gratuita obtida no Google AI Studio para rodar a recomendação online.",
        "ia_num_rec": "Quantidade de recomendações desejadas (máx. 10)",
        "ia_btn_buscar": "Analisar e Recomendar",
        "ia_analisando": "A IA está processando seu resumo e cruzando com o catálogo...",
        "ia_sucesso": "Recomendações geradas com sucesso!",
        "ia_erro": "Erro ao processar com a IA. Verifique se sua Chave API está correta.",
        "ia_card_motivo": "Por que publicar aqui:",
        "ia_card_aderencia": "Grau de Aderência:",
        "ia_card_site": "🌐 Visitar Homepage Oficial",
        "ia_card_sem_site": "Site indisponível na base"
    },
    "en": {
        "titulo": "Researcher Portal",
        "subtitulo": "Scientific Journal Finder",
        "idioma": "Language / Idioma / Idioma",
        "busca_cat": "🔍 Journal Catalog",
        "busca_ia": "🧠 Smart Recommender (AI)",
        "busca_placeholder": "Search by title, ISSN or keyword...",
        "filtro_area": "Filter by Broad Area",
        "filtro_conhecimento": "Filter by Knowledge Area",
        "filtro_indexador": "Filter by Indexer",
        "exibir_pag": "Display per page",
        "pag_lbl": "Page",
        "total_encontrado": "journals found.",
        "sobre": "About the Portal",
        "sobre_texto": "This portal helps researchers find ideal scientific journals for publishing their manuscripts.",
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
        "ia_card_sem_site": "Website not available in database"
    },
    "es": {
        "titulo": "Portal del Investigador",
        "subtitulo": "Buscador de Revistas Científicas",
        "idioma": "Idioma / Language / Idioma",
        "busca_cat": "🔍 Catálogo de Revistas",
        "busca_ia": "🧠 Recomendador Inteligente (IA)",
        "busca_placeholder": "Buscar por título, ISSN o palavra-clave...",
        "filtro_area": "Filtrar por Gran Área",
        "filtro_conhecimento": "Filtrar por Área de Conocimiento",
        "filtro_indexador": "Filtrar por Indexador",
        "exibir_pag": "Mostrar por página",
        "pag_lbl": "Página",
        "total_encontrado": "revistas encontradas.",
        "sobre": "Sobre el Portal",
        "sobre_texto": "Este portal ayuda a los investigadores a identificar las revistas ideales para publicar sus manuscritos científicos.",
        "ia_titulo": "Recomendación Temática con Inteligencia Artificial",
        "ia_subtitulo": "Pegue el título y el resumen (abstract) de su artículo. La IA analizará nuestro catálogo de revistas e indicará las mejores opciones.",
        "ia_campo_titulo": "Título del Artículo",
        "ia_campo_resumo": "Resumen / Abstract (Soporta Portugués, Inglés o Español)",
        "ia_chave_api": "Clave API de Gemini (Google AI Studio)",
        "ia_chave_ajuda": "Necesitas una clave API gratuita obtenida de Google AI Studio para ejecutar la recomendación en línea.",
        "ia_num_rec": "Cantidad de recomendaciones deseadas (máx. 10)",
        "ia_btn_buscar": "Analizar y Recomendar",
        "ia_analisando": "La IA está procesando su resumen y cruzándolo con el catálogo...",
        "ia_sucesso": "¡Recomendaciones generadas con éxito!",
        "ia_erro": "Error al procesar con la IA. Verifique que su Clave API sea correcta.",
        "ia_card_motivo": "Por qué publicar aquí:",
        "ia_card_aderencia": "Grado de Adherencia:",
        "ia_card_site": "🌐 Visitar Homepage Oficial",
        "ia_card_sem_site": "Sitio no disponible en la base"
    }
}

# --- 3. SELEÇÃO DE IDIOMA NA SIDEBAR ---
with st.sidebar:
    st.markdown("## ⚙️ Configurações / Settings")
    idioma_selecionado = st.selectbox(
        "Language / Idioma", 
        options=["Português (PT)", "English (EN)", "Español (ES)"],
        index=0
    )
    
    lang_map = {"Português (PT)": "pt", "English (EN)": "en", "Español (ES)": "es"}
    lang_code = lang_map[idioma_selecionado]
    t = traducoes[lang_code]

# --- 4. CARREGAMENTO DOS DADOS (Com suporte para o novo dados_2.csv) ---
@st.cache_data
def carregar_dados_portal():
    # Adicionado dados_2.csv no topo da prioridade de carregamento
    for nome_arquivo in ["dados_2.csv", "dados_quase.csv", "dados.csv"]:
        try:
            df = pd.read_csv(nome_arquivo, sep=";", encoding="utf-8")
            df.columns = df.columns.str.replace('^\ufeff', '', regex=True)
            return df, nome_arquivo
        except Exception:
            continue
    st.error("Erro: Não foi possível carregar os arquivos 'dados_2.csv', 'dados_quase.csv' ou 'dados.csv'.")
    st.stop()

df_original, arquivo_usado = carregar_dados_portal()

# Garantindo tratamento de colunas vazias
if "Homepage" not in df_original.columns:
    df_original["Homepage"] = ""
else:
    df_original["Homepage"] = df_original["Homepage"].fillna("")

# --- 5. LOGO E HEADER ---
imagem_base64_logo = obter_imagem_local_base64("st_static/logo.png")
if imagem_base64_logo:
    html_header = f"""
    <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 25px;">
        <img src="data:image/png;base64,{imagem_base64_logo}" style="height: 80px; max-width: 100%; object-fit: contain;">
        <div>
            <h1 style="margin: 0; font-size: 2.2rem; color: #1E3A8A;">{t['titulo']}</h1>
            <p style="margin: 5px 0 0 0; font-size: 1.1rem; color: #4B5563;">{t['subtitulo']}</p>
        </div>
    </div>
    """
    st.markdown(html_header, unsafe_allow_html=True)
else:
    st.title(f"📚 {t['titulo']}")
    st.subheader(t['subtitulo'])

# --- 6. CRIAÇÃO DAS ABAS DO PORTAL ---
tab_busca, tab_ia = st.tabs([t['busca_cat'], t['busca_ia']])

# ==================== ABA 1: CATÁLOGO TRADICIONAL ====================
with tab_busca:
    st.markdown("### " + t['busca_cat'])
    
    busca_query = st.text_input("🔍", placeholder=t['busca_placeholder'], label_visibility="collapsed")
    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
    
    with col_filtro1:
        lista_grandes_areas = ["Todas"] + list(df_original["Grande Area"].dropna().unique())
        filtro_g_area = st.selectbox(t['filtro_area'], options=lista_grandes_areas)
        
    with col_filtro2:
        if filtro_g_area != "Todas":
            df_temp = df_original[df_original["Grande Area"] == filtro_g_area]
        else:
            df_temp = df_original
        lista_conhecimento = ["Todas"] + list(df_temp["Area do Conhecimento"].dropna().unique())
        filtro_conhec = st.selectbox(t['filtro_conhecimento'], options=lista_conhecimento)
        
    with col_filtro3:
        lista_indexadores = ["Todos"] + list(df_original["Indexador"].dropna().unique())
        filtro_idx = st.selectbox(t['filtro_indexador'], options=lista_indexadores)

    df_filtrado = df_original.copy()
    
    if busca_query:
        busca_query_lower = busca_query.lower()
        df_filtrado = df_filtrado[
            df_filtrado["Título da Revista"].astype(str).str.lower().str.contains(busca_query_lower) |
            df_filtrado["ISSN"].astype(str).str.lower().str.contains(busca_query_lower)
        ]
        
    if filtro_g_area != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Grande Area"] == filtro_g_area]
        
    if filtro_conhec != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Area do Conhecimento"] == filtro_conhec]
        
    if filtro_idx != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Indexador"] == filtro_idx]

    total_itens = len(df_filtrado)
    st.markdown(f"**{total_itens}** {t['total_encontrado']}")
    
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

    st.dataframe(
        df_da_pagina, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Homepage": st.column_config.LinkColumn(
                "Homepage", 
                help="Clique para ir ao site oficial do periódico", 
                display_text="Ver site do periódico"
            ),
            "Grande Area": None,
            "Area do Conhecimento": None,
            "Subárea do Conhecimento": None,
            "Índice h5": st.column_config.NumberColumn("Índice h5"),
            "JIF": st.column_config.TextColumn("JIF"),
            "SJR": st.column_config.TextColumn("SJR")
        }
    )

# ==================== ABA 2: RECOMENDADOR INTELIGENTE POR IA ====================
with tab_ia:
    st.markdown(f"### {t['ia_titulo']}")
    st.markdown(f"*{t['ia_subtitulo']}*")
    
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"### 🔑 {t['ia_chave_api']}")
        user_gemini_key = st.text_input(
            "Gemini API Key", 
            type="password", 
            placeholder="AIzaSy...", 
            help=t['ia_chave_ajuda']
        )
    
    col_input, col_meta = st.columns([2, 1])
    
    with col_input:
        titulo_artigo = st.text_input(t['ia_campo_titulo'], placeholder="Ex: Análise Epidemiológica da Covid-19 no Brasil...")
        resumo_artigo = st.text_area(t['ia_campo_resumo'], placeholder="Paste abstract here...", height=250)
        
    with col_meta:
        st.markdown("#### 🎯 Refinar Alvos")
        area_ia = st.selectbox(f"{t['filtro_area']} (IA)", ["Todas"] + list(df_original["Grande Area"].dropna().unique()))
        indexador_ia = st.selectbox(f"{t['filtro_indexador']} (IA)", ["Todos"] + list(df_original["Indexador"].dropna().unique()))
        
        # Slider dinâmico integrado para selecionar entre 3 e 10 recomendações
        num_recomendacoes = st.slider(
            t['ia_num_rec'], 
            min_value=3, 
            max_value=10, 
            value=10, 
            step=1
        )
        
    if st.button(t['ia_btn_buscar'], type="primary"):
        if not HAS_GEMINI:
            st.error("❌ O pacote de IA do Google não pôde ser carregado. Certifique-se de implantar o arquivo `requirements.txt` no repositório.")
        elif not user_gemini_key:
            st.error("⚠️ Para utilizar esta ferramenta, insira sua chave da API do Gemini na barra lateral (Sidebar) à esquerda.")
        elif not titulo_artigo or not resumo_artigo:
            st.warning("⚠️ Preencha o Título e o Resumo do artigo para buscar.")
        else:
            with st.spinner(t['ia_analisando']):
                df_candidatos = df_original.copy()
                if area_ia != "Todas":
                    df_candidatos = df_candidatos[df_candidatos["Grande Area"] == area_ia]
                if indexador_ia != "Todos":
                    df_candidatos = df_candidatos[df_candidatos["Indexador"] == indexador_ia]
                
                # Se após filtragem houverem muitos registros, enviamos até 100 ao contexto da IA
                # para que ela selecione de forma qualificada até as 10 melhores
                if len(df_candidatos) > 100:
                    df_candidatos = df_candidatos.head(100)
                
                lista_periodicos_envio = df_candidatos[["Título da Revista", "Grande Area", "Area do Conhecimento", "Indexador", "Quartil JCR", "SJR"]].to_dict(orient="records")
                
                # Prompt parametrizado dinamicamente com o valor selecionado no slider
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
                    genai.configure(api_key=user_gemini_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    resposta = model.generate_content(prompt_ia)
                    
                    texto_resposta = resposta.text.strip()
                    if texto_resposta.startswith("```"):
                        texto_resposta = texto_resposta.replace("```json", "").replace("```", "").strip()
                    
                    recomendacoes = json.loads(texto_resposta)
                    
                    st.success(t['ia_sucesso'])
                    
                    for rec in recomendacoes:
                        registro_revista = df_original[df_original["Título da Revista"] == rec["revista_nome"]]
                        
                        homepage = ""
                        issn = "N/A"
                        indexador = "N/A"
                        quartil = "N/A"
                        sjr = "N/A"
                        
                        if not registro_revista.empty:
                            homepage = str(registro_revista.iloc[0]["Homepage"])
                            issn = registro_revista.iloc[0]["ISSN"]
                            indexador = registro_revista.iloc[0]["Indexador"]
                            quartil = str(registro_revista.iloc[0]["Quartil JCR"])
                            sjr = str(registro_revista.iloc[0]["SJR"])
                        
                        # Renderização de card para cada recomendação (agora dinamicamente de 3 a 10)
                        with st.container(border=True):
                            col_info, col_link = st.columns([3, 1])
                            
                            with col_info:
                                st.markdown(f"### {rec['revista_nome']}")
                                st.caption(f"**ISSN:** {issn} | **Indexador:** {indexador} | **Quartil:** {quartil} | **SJR:** {sjr}")
                                st.markdown(f"🎯 **{t['ia_card_aderencia']}** `{rec['porcentagem_aderencia']}%`")
                                st.markdown(f"💡 **{t['ia_card_motivo']}** {rec['justificativa']}")
                            
                            with col_link:
                                st.markdown("<br>", unsafe_allow_html=True)
                                if homepage and homepage != "nan" and homepage != "-" and homepage != "":
                                    st.link_button(t['ia_card_site'], homepage, type="primary", use_container_width=True)
                                else:
                                    st.info(t['ia_card_sem_site'])
                
                except Exception as ex:
                    st.error(t['ia_erro'])
                    st.caption(f"Detalhes técnicos do erro: {ex}")

# --- 7. FOOTER DO PORTAL ---
st.markdown("---")
with st.sidebar:
    st.markdown(f"### ℹ️ {t['sobre']}")
    st.markdown(t['sobre_texto'])
    st.caption(f"Banco de dados ativo: `{arquivo_usado}`")