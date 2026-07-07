import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO PREMIUM DA PÁGINA
st.set_page_config(
    page_title="SciIndex | Portal de Inteligência Científica",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. INJEÇÃO DE CSS DE ALTA QUALIDADE (Estilo Website Premium)
st.markdown("""
    <style>
    /* Importação de Fonte Moderna */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Hero Banner Minimalista e Sofisticado */
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
    
    /* Refatoração Completa dos Cards de Métricas */
    div[data-testid="stMetric"] {
        background: #FFFFFF !important;
        padding: 24px 28px !important;
        border-radius: 14px !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.02) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 20px -3px rgba(0, 0, 0, 0.04), 0 4px 6px -2px rgba(0, 0, 0, 0.02) !important;
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
        letter-spacing: -0.03em;
    }
    
    /* Customização Lateral Menu */
    .css-17o9839 {
        background-color: #FFFFFF !important;
    }
    
    /* Ajustes Finos de Inputs e Tabelas */
    .stTextInput input {
        border-radius: 10px !important;
        padding: 12px 16px !important;
        border: 1px solid #CBD5E1 !important;
    }
    .stSelectbox div[data-baseweb="select"] {
        border-radius: 10px !important;
    }
    
    /* Tabs Corporativos */
    button[data-baseweb="tab"] {
        font-size: 1rem !important;
        font-weight: 500 !important;
        color: #64748B;
        padding: 12px 20px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #0F172A !important;
        border-bottom-color: #0F172A !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. BASE DE DADOS COM CACHE SEGURO
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

# --- 4. ESTRUTURA DO MENU LATERAL PREMIUM ---
st.sidebar.markdown("<br>", unsafe_allow_html=True)
# Ícone elegante e minimalista para o topo do menu
st.sidebar.markdown("""
    <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 20px;'>
        <span style='font-size: 2rem;'>💎</span>
        <h2 style='margin: 0; font-size: 1.4rem; font-weight: 700; color: #0F172A;'>SciIndex Hub</h2>
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
    <div style='color: #94A3B8; font-size: 0.8rem; padding-left: 5px;'>
        <b>Status do Sistema:</b> Online<br>
        <b>Versão da Base:</b> 2026.1<br>
        <b>Padrão CNPq:</b> Atualizado
    </div>
""", unsafe_allow_html=True)


# ==============================================================================
# SEÇÃO 1: INDEXADOR DINÂMICO DE REVISTAS
# ==============================================================================
if menu_selecionado == "🔍 Indexador Dinâmico":
    
    # Hero Section Premium
    st.markdown("""
        <div class="premium-hero">
            <h1 class="premium-title">Portal de Inteligência Periódica</h1>
            <p class="premium-subtitle">Cruze indexadores internacionais com as grandes áreas de fomento do CNPq para descobrir o periódico estratégico ideal para o seu manuscrito.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Container centralizado de buscas
    st.markdown("#### 🛠️ Filtros Inteligentes de Pesquisa")
    busca = st.text_input("Buscar registro específico:", placeholder="Digite uma palavra-chave do título da revista, ISSN ou assunto...")

    # Organização das abas com visual corporativo
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
            q_sjr_sel = st.multiselect("Quartil SJR (Scopus):", sorted([str(x).strip() for x in df_original[col_q_sjr].dropna().unique()]), default=sorted([str(x).strip() for x in df_original[col_q_sjr].dropna().unique()])) if col_q_sjr else []
        with col_f6:
            opcoes_ordenacao = ["Título"]
            if "SJR" in df_original.columns: opcoes_ordenacao.append("SJR (Prestígio)")
            if "JIF" in df_original.columns: opcoes_ordenacao.append("JIF (Fator de Impacto)")
            criterio_ordem = st.selectbox("Ordenar Resultados por:", options=opcoes_ordenacao)

    st.markdown("<br>", unsafe_allow_html=True)

    # Lógica de processamento de filtros
    df_filtrado = df_original.copy()
    if busca:
        df_filtrado = df_filtrado[df_filtrado[df_filtrado.columns[0]].str.contains(busca, case=False, na=False) | df_filtrado["ISSN"].str.contains(busca, case=False, na=False)]
    if cnpq_selecionado != "Todas":
        df_filtrado = df_filtrado[(df_filtrado[col_cnpq1] == cnpq_selecionado) | (df_filtrado[col_cnpq2] == cnpq_selecionado)]
    if area_especifica_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado[col_area_especifica].str.contains(area_especifica_sel, case=False, na=False)]
    if col_indexador and indexador_sel:
        df_filtrado = df_filtrado[df_filtrado[col_indexador].astype(str).str.contains("|".join(indexador_sel), na=False)]
    if col_q_jcr and q_jcr_sel:
        df_filtrado = df_filtrado[df_filtrado[col_q_jcr].astype(str).str.strip().isin(q_jcr_sel)]
    if col_q_sjr and q_sjr_sel:
        df_filtrado = df_filtrado[df_filtrado[col_q_sjr].astype(str).str.strip().isin(q_sjr_sel)]

    # Ordenação
    mapa_ordem = {"SJR (Prestígio)": ("SJR", False), "JIF (Fator de Impacto)": ("JIF", False), "Título": (df_filtrado.columns[0], True)}
    col_ordenar, ascendente = mapa_ordem[criterio_ordem]
    if col_ordenar in df_filtrado.columns: df_filtrado = df_filtrado.sort_values(by=col_ordenar, ascending=ascendente)

    # --- INDICADORES EXECUTIVOS (Cards com efeitos CSS de Hover) ---
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1: st.metric("Revistas Selecionadas", f"{len(df_filtrado):,}".replace(",", "."))
    with col_m2: st.metric("H-Index Topo", int(df_filtrado["H index"].max()) if "H index" in df_filtrado.columns else 0)
    with col_m3: st.metric("Fator JIF Máximo", f"{df_filtrado['JIF'].max():.2f}" if 'JIF' in df_filtrado.columns and pd.notna(df_filtrado['JIF'].max()) else "0.00")
    with col_m4: st.metric("SJR Score Ápice", f"{df_filtrado['SJR'].max():.3f}" if 'SJR' in df_filtrado.columns and pd.notna(df_filtrado['SJR'].max()) else "0.000")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabela de dados integrada
    st.markdown("#### 📋 Catálogo de Periódicos")
    itens_por_pagina = 40
    total_itens = len(df_filtrado)
    if total_itens > 0:
        total_paginas = (total_itens // itens_por_pagina) + (1 if total_itens % itens_por_pagina > 0 else 0)
        col_pag1, _ = st.columns([1, 5])
        with col_pag1: pagina_atual = st.number_input(f"Página (1 de {total_paginas}):", min_value=1, max_value=max(1, total_paginas), value=1)
        
        # Dataframe limpo, sem indexador poluidora lateral
        st.dataframe(df_filtrado.iloc[(pagina_atual - 1) * itens_por_pagina : pagina_atual * itens_por_pagina], use_container_width=True, hide_index=True)
        
        # Botão de Exportação Premium
        st.download_button(label="📥 Exportar Dados Selecionados (CSV)", data=df_filtrado.to_csv(index=False, sep=';', encoding='utf-8-sig'), file_name="relatorio_sciindex.csv", mime="text/csv")
    else:
        st.warning("Nenhum periódico atende aos critérios aplicados.")

# ==============================================================================
# SEÇÃO 2: INTELIGÊNCIA DE ESCRITA (PÁGINA EXCLUSIVA COM DESIGN EDITORIAL)
# ==============================================================================
elif menu_selecionado == "📄 Inteligência de Escrita":
    st.markdown("""
        <div class="premium-hero">
            <h1 class="premium-title">Central de Escrita de Alto Impacto</h1>
            <p class="premium-subtitle">Recursos avançados para a redação, estruturação e submissão de manuscritos científicos para periódicos internacionais de elite.</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_conteudo1, col_conteudo2 = st.columns(2)
    with col_conteudo1:
        st.markdown("""
        ### 🎯 Estrutura de uma Cover Letter Vencedora
        A *Cover Letter* é o primeiro contato com o Editor-Chefe. Ela deve explicar por que seu artigo é relevante **especificamente** para aquela revista.
        
        * **Parágrafo 1:** Título do manuscrito e declaração clara de originalidade.
        * **Parágrafo 2:** O problema de pesquisa e a grande descoberta do seu grupo.
        * **Parágrafo 3:** Por que o escopo da revista se alinha perfeitamente com o tema.
        """)
    with col_conteudo2:
        st.markdown("""
        ### 🧠 Ferramentas Úteis Recomendadas
        Otimize seu fluxo de trabalho científico com ferramentas profissionais:
        * **Overleaf / LaTeX:** Essencial para formatação automatizada matemática e de engenharia.
        * **Zotero / Mendeley:** Gerenciadores de referências para evitar erros de citação.
        * **DeepL / Grammarly:** Apoio linguístico fino para redação em língua inglesa.
        """)

# ==============================================================================
# SEÇÃO 3: ECOSSISTEMA E MÍDIA
# ==============================================================================
elif menu_selecionado == "🌐 Ecossistema & Mídia":
    st.markdown("""
        <div class="premium-hero">
            <h1 class="premium-title">Divulgação e Ciência Aberta</h1>
            <p class="premium-subtitle">Aprenda a transformar o seu artigo científico publicado em impacto social e engajamento acadêmico digital.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    ### 📈 Como Aumentar as Citações do seu Artigo (Estratégia Altmétrica)
    Publicar a pesquisa é apenas metade do trabalho. Para gerar relevância real no h-index, utilize estratégias de divulgação científica:
    1.  **Visual Abstracts:** Crie um infográfico resumindo a metodologia e a conclusão principal do manuscrito.
    2.  **Repositórios Institucionais:** Disponibilize a versão pré-print em plataformas de acesso aberto (como SciELO ou o repositório da sua Universidade).
    3.  **Redes Sociais Acadêmicas:** Mantenha seus perfis atualizados no ORCID, ResearchGate e LinkedIn Acadêmico.
    """)

# ==============================================================================
# SEÇÃO 4: SIMPÓSIOS E EVENTOS
# ==============================================================================
elif menu_selecionado == "📅 Simpósios e Eventos":
    st.markdown("""
        <div class="premium-hero">
            <h1 class="premium-title">Agenda Acadêmica Integrada</h1>
            <p class="premium-subtitle">Acompanhe as janelas de submissão de resumos, chamadas abertas (Special Issues) e grandes congressos.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.info("📅 **Calendário de Eventos:** Esta seção apresentará o cronograma unificado de conferências nacionais e internacionais divididas por Grandes Áreas do CNPq.")