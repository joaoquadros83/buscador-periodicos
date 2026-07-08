import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO PREMIUM DA PÁGINA
st.set_page_config(
    page_title="Portal do Pesquisador v3.0",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. INJEÇÃO DE CSS AVANÇADO (Design de Alto Padrão e Ajuste de Botões)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif !important;
    }
    
  /* --- CUSTOMIZAÇÃO EXCLUSIVA DOS BOTÕES DA BARRA LATERAL ESQUERDA --- */
    
    /* 1. Item Ativo (Indexador Dinâmico) - Fundo Vermelho e Fonte Branca */
    div[data-testid="stSidebar"] [data-testid="stCheckbox"] {
        background-color: #A91D22 !important;  /* Tom avermelhado Dialnet */
        padding: 10px 14px !important;
        border: 1px solid #A91D22 !important;
        border-radius: 6px !important;
        margin-bottom: 8px !important;
    }

/* --- BARRA LATERAL ESQUERDA (CORREÇÃO DE CONTRASTE DOS BOTÕES) --- */
    [data-testid="stSidebar"] {
        background-color: #FAF9F6 !important;
        border-right: 1px solid #EAE8E4 !important;
        box-shadow: none !important;
    }
    
    /* 1. TEXTOS INFORMATIVOS (Fora dos botões: Títulos, Labels e Rodapé) */
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] b,
    [data-testid="stSidebar"] i {
        color: #0F172A !important; /* Mesma cor do Painel de Navegação */
    }
    
    /* 2. ITEM ATIVO (Indexador Dinâmico) - Fundo Vermelho e Texto Branco */
    div[data-testid="stSidebar"] [data-testid="stCheckbox"] {
        background-color: #A91D22 !important;
        padding: 10px 14px !important;
        border: 1px solid #A91D22 !important;
        border-radius: 6px !important;
        margin-bottom: 8px !important;
    }
    /* Força fonte branca em qualquer elemento de texto dentro do Indexador */
    div[data-testid="stSidebar"] [data-testid="stCheckbox"] p,
    div[data-testid="stSidebar"] [data-testid="stCheckbox"] span,
    div[data-testid="stSidebar"] [data-testid="stCheckbox"] label {
        color: #FFFFFF !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }

    /* 3. LINKS DE INTERESSE (Botões Escuros) - Fundo Azul e TEXTO BRANCO OBRIGATÓRIO */
    div[data-testid="stSidebar"] [data-testid="stLinkButton"] a {
        background-color: #004B87 !important;  /* Fundo Escuro */
        border: 1px solid #004B87 !important;
        border-radius: 6px !important;
        padding: 10px 14px !important;
        margin-bottom: 8px !important;
        text-align: left !important;
	color: #FFFFFF !important;
        display: flex !important;
        align-items: center !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        text-decoration: none !important;
    }
    
    /* Seletor ultra-específico para anular a cor escura e forçar BRANCO nas letras internas dos links */
    div[data-testid="stSidebar"] [data-testid="stLinkButton"] a,
    div[data-testid="stSidebar"] [data-testid="stLinkButton"] a p,
    div[data-testid="stSidebar"] [data-testid="stLinkButton"] a span {
        color: #FFFFFF !important;              /* TEXTO BRANCO GARANTIDO */
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }
    
    /* 4. COMPORTAMENTO HOVER (Passar o Mouse) - Muda para Vermelho e MANTÉM TEXTO BRANCO */
    div[data-testid="stSidebar"] [data-testid="stLinkButton"] a:hover {
        background-color: #A91D22 !important;  /* Vermelho Dialnet */
        border-color: #A91D22 !important;
        box-shadow: 0 4px 8px rgba(169, 29, 34, 0.2) !important;
	onmouseover="this.style.backgroundColor='#FF2B2B'; this.style.borderColor='#FF2B2B';" 
	onmouseout="this.style.backgroundColor='#004B87'; this.style.borderColor='#004B87';"
    }
    /* Mantém as letras brancas durante o hover */
    div[data-testid="stSidebar"] [data-testid="stLinkButton"] a:hover p,
    div[data-testid="stSidebar"] [data-testid="stLinkButton"] a:hover span {
        color: #FFFFFF !important;              /* CONTINUA BRANCO */
    }

# 3. DESIGN DO HERO DA PÁGINA (CSS CUSTOMIZADO)
st.markdown("""
<style>
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
    
    /* Inputs, Selectboxes e Tabs */
    .stTextInput input { border-radius: 10px !important; padding: 12px 16px !important; border: 1px solid #CBD5E1 !important; }
    .stSelectbox div[data-baseweb="select"] { border-radius: 10px !important; }
    button[data-baseweb="tab"] { font-size: 1rem !important; font-weight: 500 !important; color: #64748B; padding: 12px 20px !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #0F172A !important; border-bottom-color: #0F172A !important; }
    
    /* Botão de download customizado */
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

# 4. BASE DE DADOS COM CACHE
@st.cache_data
def carregar_dados():
    df = pd.read_csv("dados_revistas.csv", sep=",", encoding="utf-8-sig", low_memory=False, on_bad_lines='skip')
    df = df.drop_duplicates(subset=[df.columns[0]])
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.columns = [c.strip() for c in df.columns]
    
    # Tratamento inicial de dados numéricos limpando vírgulas por pontos
    for col in ['SJR', 'JIF', 'h-index', 'H index']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # Substituição global de nulos e 'None' por '-'
    df = df.fillna("-")
    df = df.replace(["None", "none", "NONE", "nan", "NaN", "null", ""], "-")
        
    return df

try:
    df_original = carregar_dados()
except Exception as e:
    st.error(f"⚠️ Erro ao carregar a base de dados. Detalhes: {e}")
    st.stop()

# 5. MENU LATERAL
st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.sidebar.markdown("""
    <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 20px;'>
        <h2 style='margin: 0; font-size: 1.75rem; font-weight: 700; color: #0F172A;'>Painel de Navegação</h2>
    </div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<style>
    .btn-custom-menu {
        background-color: #E2E8F0 !important;
        border: 1px solid #004B87 !important;
        border-radius: 6px !important;
        padding: 10px 14px !important;
        margin-bottom: 8px !important;
        text-align: left !important;
        display: flex !important;
        align-items: center !important;
        text-decoration: none !important;
    }
    .btn-custom-menu span { color: #0F172A !important; font-weight: 500 !important; font-size: 0.9rem !important; }
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px;'>INDEXADORES</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://www.webofknowledge.com" target="_blank"><span>🌐 Web of Science</span></a>
    <a class="btn-custom-menu" href="https://www.scopus.com" target="_blank"><span>🧬 Scopus</span></a>
    <a class="btn-custom-menu" href="https://pubmed.ncbi.nlm.nih.gov/" target="_blank"><span>🏥 PubMed</span></a>
    <a class="btn-custom-menu" href="https://www.scielo.br/" target="_blank"><span>📚 Scielo BR</span></a>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px;'>IA PARA USO ACADÊMICO</p>
<div style="display: flex; flex-direction: column;">
    <a class="btn-custom-menu" href="https://www.perplexity.ai/" target="_blank"><span>🤖 Perplexity AI</span></a>
    <a class="btn-custom-menu" href="https://scispace.com/" target="_blank"><span>🚀 SciSpace</span></a>
    <a class="btn-custom-menu" href="https://elicit.com/" target="_blank"><span>🔍 Elicit</span></a>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>", unsafe_allow_html=True)
st.sidebar.markdown("""
    <div style='color: #0F172A; font-size: 0.8rem; padding-left: 5px; line-height: 1.6;'>
        © 2026 <b>João F. Soares-Quadros Jr.</b><br>UFOP | Todos os direitos reservados.
    </div>
""", unsafe_allow_html=True)

# 6. PAINEL PRINCIPAL
st.markdown("""
    <div class="premium-hero">
        <h1 class="premium-title">Portal do Pesquisador</h1>
        <p class="premium-subtitle">Cruze indexadores internacionais com as grandes áreas de fomento do CNPq para descobrir o periódico estratégico ideal.</p>
    </div>
""", unsafe_allow_html=True)

st.markdown("#### 🛠️ Filtros Inteligentes de Pesquisa")
busca = st.text_input("Buscar registro específico:", placeholder="Digite o título da revista, ISSN...")

aba_escopo, aba_impacto = st.tabs(["📂 Escopo Acadêmico & CNPq", "📈 Métricas de Performance & Quartis"])

with aba_escopo:
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        col_grande_area = "Grande Area"
        lista_grande_area = sorted([str(x).strip() for x in df_original[col_grande_area].unique() if str(x).strip() not in ["", "-"]])
        grande_area_sel = st.selectbox("Grande Área CNPq (Brasil):", ["Todas"] + lista_grande_area)
    with col_f2:
        col_area = "Area do Conhecimento"
        lista_areas = sorted([str(x).strip() for x in df_original[col_area].unique() if str(x).strip() not in ["", "-"]])
        area_sel = st.selectbox("Área do Conhecimento (1º Nível):", ["Todas"] + lista_areas)
    with col_f3:
        col_indexador = "Indexador" if "Indexador" in df_original.columns else None
        if col_indexador:
            set_indexadores = set()
            for x in df_original[col_indexador].unique():
                if x != "-":
                    for idx in str(x).split(","): set_indexadores.add(idx.strip())
            indexador_sel = st.multiselect("Bases Detentoras:", sorted(list(set_indexadores)), default=sorted(list(set_indexadores)))
        else: indexador_sel = []

with aba_impacto:
    col_f4, col_f5, col_f6 = st.columns(3)
    with col_f4:
        col_q_jcr = "Quartil JCR" if "Quartil JCR" in df_original.columns else None
        opcoes_jcr = sorted([str(x).strip() for x in df_original[col_q_jcr].unique() if str(x).strip() != "-"]) if col_q_jcr else []
        q_jcr_sel = st.multiselect("Quartil JCR (Clarivate):", opcoes_jcr, default=opcoes_jcr)
    with col_f5:
        col_q_sjr = "SJR Best Quartile" if "SJR Best Quartile" in df_original.columns else None
        opcoes_sjr = sorted([str(x).strip() for x in df_original[col_q_sjr].unique() if str(x).strip() != "-"]) if col_q_sjr else []
        q_sjr_sel = st.multiselect("Quartil SJR (Scopus):", opcoes_sjr, default=opcoes_sjr)
    with col_f6:
        opcoes_ordenacao = ["Título"]
        if "SJR" in df_original.columns: opcoes_ordenacao.append("SJR (Prestígio)")
        if "JIF" in df_original.columns: opcoes_ordenacao.append("JIF (Fator de Impacto)")
        criterio_ordem = st.selectbox("Ordenar Resultados por:", options=opcoes_ordenacao)

# 7. FILTRAGEM SEQUENCIAL DE DADOS
df_filtrado = df_original.copy()

if busca:
    df_filtrado = df_filtrado[
        df_filtrado[df_filtrado.columns[0]].astype(str).str.contains(busca, case=False, na=False) | 
        df_filtrado["ISSN"].astype(str).str.contains(busca, case=False, na=False)
    ]
if grande_area_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado[col_grande_area] == grande_area_sel]
if area_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado[col_area] == area_sel]
if col_indexador and indexador_sel:
    df_filtrado = df_filtrado[df_filtrado[col_indexador].astype(str).str.contains("|".join(indexador_sel), na=False)]
if col_q_jcr and q_jcr_sel:
    df_filtrado = df_filtrado[df_filtrado[col_q_jcr].astype(str).str.strip().isin(q_jcr_sel)]
if col_q_sjr and q_sjr_sel:
    df_filtrado = df_filtrado[df_filtrado[col_q_sjr].astype(str).str.strip().isin(q_sjr_sel)]

mapa_ordem = {"SJR (Prestígio)": ("SJR", False), "JIF (Fator de Impacto)": ("JIF", False), "Título": (df_filtrado.columns[0], True)}
col_ordenar, ascendente = mapa_ordem[criterio_ordem]
if col_ordenar in df_filtrado.columns: 
    df_filtrado = df_filtrado.sort_values(by=col_ordenar, ascending=ascendente)

# 8. METRICAS DINÂMICAS COM SEGURANÇA DE TIPO
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1: 
    st.metric("Revistas Selecionadas", f"{len(df_filtrado):,}".replace(",", "."))
with col_m2: 
    h_index_numerico = pd.to_numeric(df_filtrado["H index"], errors='coerce')
    max_h = int(h_index_numerico.max()) if pd.notna(h_index_numerico.max()) else 0
    st.metric("H-Index Topo", max_h)
with col_m3: 
    jif_numerico = pd.to_numeric(df_filtrado['JIF'], errors='coerce')
    max_jif = f"{jif_numerico.max():.2f}" if pd.notna(jif_numerico.max()) else "0.00"
    st.metric("Fator JIF Máximo", max_jif)
with col_m4: 
    sjr_numerico = pd.to_numeric(df_filtrado['SJR'], errors='coerce')
    max_sjr = f"{sjr_numerico.max():.3f}" if pd.notna(sjr_numerico.max()) else "0.000"
    st.metric("SJR Score Ápice", max_sjr)

st.markdown("<br>", unsafe_allow_html=True)

# 9. EXIBIÇÃO E PAGINAÇÃO
st.markdown("#### 📋 Catálogo de Periódicos")
total_itens = len(df_filtrado)
if total_itens > 0:
    col_pag1, col_pag2, _ = st.columns([1.5, 2, 5])
    with col_pag1:
        itens_por_pagina = st.selectbox("Exibir por página:", options=[20, 50, 100], index=1)
    total_paginas = (total_itens // itens_por_pagina) + (1 if total_itens % itens_por_pagina > 0 else 0)
    with col_pag2:
        pagina_atual = st.number_input(f"Página (1 de {total_paginas}):", min_value=1, max_value=max(1, total_paginas), value=1)
    
    inicio = (pagina_atual - 1) * itens_por_pagina
    fim = inicio + itens_por_pagina
    df_da_pagina = df_filtrado.iloc[inicio:fim]
    
    st.dataframe(df_da_pagina, use_container_width=True, hide_index=True)
    
    csv_pagina = df_da_pagina.to_csv(index=False, sep=';', encoding='utf-8-sig')
    st.download_button(label=f"📥 Exportar apenas esta página ({len(df_da_pagina)} itens)", data=csv_pagina, file_name="sciindex_pagina_atual.csv", mime="text/csv")
else:
    st.warning("Nenhum periódico atende aos critérios aplicados.")