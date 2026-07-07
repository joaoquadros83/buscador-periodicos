import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Portal de Inteligência Científica",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded" # Menu esquerdo expandido por padrão
)

# Estilização CSS para o cabeçalho e cards
st.markdown("""
    <style>
    .hero-container {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        padding: 35px 25px;
        border-radius: 12px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .hero-title { font-size: 2.3rem !important; font-weight: 700 !important; color: white !important; margin-bottom: 5px; }
    .hero-subtitle { font-size: 1.05rem !important; color: #E2E8F0 !important; }
    
    div[data-testid="stMetric"] {
        background-color: white; padding: 15px 20px !important; border-radius: 10px;
        border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetricLabel"] { font-size: 0.9rem !important; color: #64748B !important; font-weight: 600; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem !important; color: #1E3A8A !important; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

# 2. FUNÇÃO DE CACHE PARA O BUSCADOR
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

# --- 3. CRIAÇÃO DO MENU LATERAL ESQUERDO ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1043/1043514.png", width=70) # Ícone decorativo pro menu
st.sidebar.title("🌐 SciIndex Portal")
st.sidebar.markdown("Navegue pelas seções:")

# O rádio botão funciona como o controlador das páginas do site
menu_selecionado = st.sidebar.radio(
    label="Menu Principal",
    options=[
        "🔍 Buscador de Periódicos",
        "✍️ Guias de Publicação",
        "📢 Divulgação Científica",
        "📅 Congressos e Eventos"
    ],
    label_visibility="collapsed" # Esconde o texto estrutural pra ficar mais limpo
)

st.sidebar.markdown("---")
st.sidebar.caption("Desenvolvido para apoio à comunidade acadêmica brasileira. © 2026")


# ==============================================================================
# PÁGINA 1: O MOTOR DE BUSCA (Seu código atual protegido dentro deste bloco)
# ==============================================================================
if menu_selecionado == "🔍 Buscador de Periódicos":
    
    st.markdown("""
        <div class="hero-container">
            <h1 class="hero-title">🔬 SciIndex · Buscador de Periódicos</h1>
            <p class="hero-subtitle">Identifique as melhores opções de revistas nacionais e internacionais para a submissão dos seus manuscritos.</p>
        </div>
    """, unsafe_allow_html=True)
    
    try:
        df_original = carregar_dados()
    except Exception as e:
        st.error(f"⚠️ Erro ao carregar a base de dados. Detalhes: {e}")
        st.stop()

    st.markdown("### 🔍 Motor de Busca Avançado")
    busca = st.text_input("Digite o termo de busca (Ex: Nome da Revista, Palavra-chave ou ISSN):", placeholder="Ex: Revista de Direito, 1516-3210...")

    aba_escopo, aba_impacto = st.tabs(["📌 Classificação e Áreas", "📈 Métricas de Impacto"])

    with aba_escopo:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            col_cnpq1 = [c for c in df_original.columns if 'cnpq 1' in c.lower() or 'cnpq1' in c.lower()][0]
            col_cnpq2 = [c for c in df_original.columns if 'cnpq 2' in c.lower() or 'cnpq2' in c.lower()][0]
            todas_areas_cnpq = set(df_original[col_cnpq1].dropna().unique()).union(set(df_original[col_cnpq2].dropna().unique()))
            lista_cnpq = sorted([str(x).strip() for x in todas_areas_cnpq if str(x).strip() != ""])
            cnpq_selecionado = st.selectbox("Grande Área CNPq:", ["Todas"] + lista_cnpq)
        with col_f2:
            col_area_especifica = "Área do Conhecimento" if "Área do Conhecimento" in df_original.columns else [c for c in df_original.columns if 'conhecimento' in c.lower()][0]
            todas_areas_especificas = set()
            for x in df_original[col_area_especifica].dropna():
                for area in str(x).split(","): todas_areas_especificas.add(area.strip())
            area_especifica_sel = st.selectbox("Área de Especialidade:", ["Todas"] + sorted(list(todas_areas_especificas)))
        with col_f3:
            col_indexador = "Indexador" if "Indexador" in df_original.columns else None
            if col_indexador:
                set_indexadores = set()
                for x in df_original[col_indexador].dropna():
                    for idx in str(x).split(","): set_indexadores.add(idx.strip())
                indexador_sel = st.multiselect("Bases Indexadoras:", sorted(list(set_indexadores)), default=sorted(list(set_indexadores)))
            else: indexador_sel = []

    with aba_impacto:
        col_f4, col_f5, col_f6 = st.columns(3)
        with col_f4:
            col_q_jcr = "Quartil JCR" if "Quartil JCR" in df_original.columns else None
            q_jcr_sel = st.multiselect("Quartil JCR (WoS):", sorted([str(x).strip() for x in df_original[col_q_jcr].dropna().unique()]), default=sorted([str(x).strip() for x in df_original[col_q_jcr].dropna().unique()])) if col_q_jcr else []
        with col_f5:
            col_q_sjr = "SJR Best Quartile" if "SJR Best Quartile" in df_original.columns else None
            q_sjr_sel = st.multiselect("Quartil SJR (Scopus):", sorted([str(x).strip() for x in df_original[col_q_sjr].dropna().unique()]), default=sorted([str(x).strip() for x in df_original[col_q_sjr].dropna().unique()])) if col_q_sjr else []
        with col_f6:
            opcoes_ordenacao = ["Título"]
            if "SJR" in df_original.columns: opcoes_ordenacao.append("SJR (Prestígio)")
            if "JIF" in df_original.columns: opcoes_ordenacao.append("JIF (Fator de Impacto)")
            criterio_ordem = st.selectbox("Ordenar Catálogo por:", options=opcoes_ordenacao)

    st.markdown("---")

    # Filtros lógicos
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

    col_ordenar, ascendente = mapa_ordem = {"SJR (Prestígio)": ("SJR", False), "JIF (Fator de Impacto)": ("JIF", False), "Título": (df_filtrado.columns[0], True)}[criterio_ordem]
    if col_ordenar in df_filtrado.columns: df_filtrado = df_filtrado.sort_values(by=col_ordenar, ascending=ascendente)

    # Exibição de métricas
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1: st.metric("Periódicos Filtrados", f"{len(df_filtrado):,}".replace(",", "."))
    with col_m2: st.metric("H-Index Máximo", int(df_filtrado["H index"].max()) if "H index" in df_filtrado.columns else 0)
    with col_m3: st.metric("Fator JIF Ápice", f"{df_filtrado['JIF'].max():.2f}" if 'JIF' in df_filtrado.columns and pd.notna(df_filtrado['JIF'].max()) else "0.00")
    with col_m4: st.metric("Score SJR de Elite", f"{df_filtrado['SJR'].max():.3f}" if 'SJR' in df_filtrado.columns and pd.notna(df_filtrado['SJR'].max()) else "0.000")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabela com paginação
    itens_por_pagina = 40
    total_itens = len(df_filtrado)
    if total_itens > 0:
        total_paginas = (total_itens // itens_por_pagina) + (1 if total_itens % itens_por_pagina > 0 else 0)
        col_pag1, _ = st.columns([1, 4])
        with col_pag1: pagina_atual = st.number_input(f"Página (1 a {total_paginas}):", min_value=1, max_value=max(1, total_paginas), value=1)
        st.dataframe(df_filtrado.iloc[(pagina_atual - 1) * itens_por_pagina : pagina_atual * itens_por_pagina], use_container_width=True, hide_index=True)
        st.download_button(label="📥 Exportar Relatório Customizado (CSV)", data=df_filtrado.to_csv(index=False, sep=';', encoding='utf-8-sig'), file_name="relatorio_periodicos.csv", mime="text/csv")
    else:
        st.warning("⚠️ Nenhum registro localizado.")

# ==============================================================================
# PÁGINA 2: GUIAS DE PUBLICAÇÃO (Futura inclusão)
# ==============================================================================
elif menu_selecionado == "✍️ Guias de Publicação":
    st.markdown("""
        <div class="hero-container">
            <h1 class="hero-title">✍️ Central de Escrita e Publicação</h1>
            <p class="hero-subtitle">Diretrizes, boas práticas e ferramentas para estruturar artigos científicos de alto impacto.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.info("💡 **Espaço Reservado:** Aqui você poderá incluir checklists de submissão, templates de cartas de apresentação (Cover Letters) e guias passo a passo para responder aos revisores (Peer Review).")
    
    # Exemplo de bloco estruturado futuro
    st.markdown("### 📋 Checklist Rápido para Autores")
    st.checkbox("O resumo (Abstract) respeita o limite de palavras da revista?")
    st.checkbox("A folha de rosto omitiu os autores para garantir a revisão Double-Blind?")

# ==============================================================================
# PÁGINA 3: DIVULGAÇÃO CIENTÍFICA (Futura inclusão)
# ==============================================================================
elif menu_selecionado == "📢 Divulgação Científica":
    st.markdown("""
        <div class="hero-container">
            <h1 class="hero-title">📢 Divulgação e Ciência Aberta</h1>
            <p class="hero-subtitle">Como expandir o alcance da sua pesquisa para além dos muros da universidade.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.info("💡 **Espaço Reservado:** Setor destinado a conteúdos sobre escrita de abstracts visuais, como criar Press Releases para jornais e o uso estratégico das redes sociais acadêmicas (ResearchGate, LinkedIn, Twitter) para aumentar citações.")

# ==============================================================================
# PÁGINA 4: CONGRESSOS E EVENTOS (Futura inclusão)
# ==============================================================================
elif menu_selecionado == "📅 Congressos e Eventos":
    st.markdown("""
        <div class="hero-container">
            <h1 class="hero-title">📅 Agenda Científica Nacional e Internacional</h1>
            <p class="hero-subtitle">Fique por dentro dos principais simpósios, congressos e chamadas abertas de artigos.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.info("💡 **Espaço Reservado:** Calendário acadêmico dinâmico. No futuro, você poderá criar uma tabela aqui listando datas importantes de congressos de cada Grande Área do CNPq.")