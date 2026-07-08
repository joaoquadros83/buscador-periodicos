import streamlit as st
import pandas as pd

st.set_page_config(page_title="App Revista", layout="wide")
st.title("📚 Painel de Periódicos e Revistas Científicas")

# 1. Carrega os dados e garante que a coluna CNPq exista
@st.cache_data
def carregar_e_tratar_dados():
    try:
        # Tenta ler o CSV assumindo ponto e vírgula (padrão comum do Excel brasileiro)
        df = pd.read_csv("dados_revistas.csv", sep=';', encoding="utf-8-sig")
    except Exception:
        try:
            # Se falhar, tenta ler com vírgula tradicional, ignorando linhas defeituosas
            df = pd.read_csv("dados_revistas.csv", sep=',', encoding="utf-8-sig", on_bad_lines='skip')
        except Exception:
            # Terceira tentativa caso o arquivo use codificação antiga do Windows (latin1)
            df = pd.read_csv("dados_revistas.csv", encoding="latin1", on_bad_lines='skip')
    
    # Se a coluna do CNPq não existir no CSV, o app cria em tempo real
    if "Area_Conhecimento_CNPq" not in df.columns:
        coluna_e = df.columns[4] # Pega a quinta coluna
        
        mapeamento_seguranca = {
            "matematica": "Matemática", "mathematics": "Matemática", "algebra": "Matemática", "analise": "Matemática", "geometry": "Matemática",
            "education": "Educação", "educacao": "Educação", "teaching": "Educação",
            "medicine": "Medicina", "medica": "Medicina", "saude": "Saúde Coletiva",
            "history": "História", "sociology": "Sociologia", "law": "Direito"
        }
        
        def definir_area(valor):
            texto = str(valor).lower().strip()
            for chave, area_oficial in mapeamento_seguranca.items():
                if chave in texto:
                    return area_oficial
            return "Geral / Outros"
            
        df["Area_Conhecimento_CNPq"] = df[coluna_e].apply(definir_area)
        
    return df

df = carregar_e_tratar_dados()

# 2. Configuração da Barra Lateral (Sidebar)
st.sidebar.header("Filtros de Busca")

areas_disponiveis = ["Todas"] + sorted(df["Area_Conhecimento_CNPq"].unique().tolist())
area_selecionada = st.sidebar.selectbox("Selecione a Área do Conhecimento (CNPq):", areas_disponiveis)

busca_termo = st.sidebar.text_input("Buscar por nome da revista ou ISSN:")

# 3. Aplicando os filtros
df_filtrado = df.copy()

if area_selecionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Area_Conhecimento_CNPq"] == area_selecionada]

if busca_termo:
    coluna_nome = df.columns[0]
    coluna_issn = df.columns[1]
    df_filtrado = df_filtrado[
        df_filtrado[coluna_nome].str.contains(busca_termo, case=False, na=False) |
        df_filtrado[coluna_issn].str.contains(busca_termo, case=False, na=False)
    ]

# 4. Exibindo os resultados
st.subheader(f"Resultados Encontrados ({len(df_filtrado)} revistas)")
st.dataframe(df_filtrado, use_container_width=True)