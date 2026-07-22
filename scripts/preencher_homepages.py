"""
Script de Preenchimento Automático de Homepages de Periódicos
Este script pesquisa no Google / DuckDuckGo o site oficial de cada revista com Homepage ausente
e salva a URL direta correspondente no arquivo dados.csv.
"""

import os
import sys
import time
import re
import urllib.request
import urllib.parse
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "dados.csv")

# Domínios a ignorar (motores de busca, redes sociais, agregadores genéricos)
DOMINIOS_IGNORAR = [
    "duckduckgo.com", "google.com", "bing.com", "wikipedia.org", "facebook.com",
    "twitter.com", "x.com", "linkedin.com", "youtube.com", "amazon.com",
    "researchgate.net", "academia.edu", "reddit.com"
]

def buscar_homepage_ddg(titulo_revista, issn):
    query_str = f'"{titulo_revista}" website official journal'
    url_search = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query_str)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        req = urllib.request.Request(url_search, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as response:
            html = response.read().decode("utf-8", errors="ignore")
            
        raw_links = re.findall(r'uddg=([^&"\']+)', html)
        for raw in raw_links:
            decoded = urllib.parse.unquote(raw)
            # Ignora domínios da lista de exclusão
            if not any(ign in decoded.lower() for ign in DOMINIOS_IGNORAR):
                if decoded.startswith("http://") or decoded.startswith("https://"):
                    return decoded
    except Exception as e:
        pass
    return None

def preencher_homepages(max_busca=300):
    print(f"Lendo base de dados: {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH, low_memory=False)
    
    col_title = "Título da Revista" if "Título da Revista" in df.columns else df.columns[1]
    col_issn = "ISSN" if "ISSN" in df.columns else "ISSN"
    col_home = "Homepage"
    
    mask_missing = df[col_home].isna() | (df[col_home].astype(str).str.strip() == "-") | (df[col_home].astype(str).str.strip() == "")
    indices_faltantes = df[mask_missing].index.tolist()
    
    total_faltantes = len(indices_faltantes)
    print(f"Total de periódicos sem Homepage: {total_faltantes}")
    
    processados = 0
    encontrados = 0
    
    for idx in indices_faltantes:
        if processados >= max_busca:
            print(f"Limite máximo de busca para esta execução atingido ({max_busca}).")
            break
            
        row = df.loc[idx]
        titulo = str(row[col_title]).strip()
        issn = str(row.get(col_issn, "")).strip()
        
        if not titulo or titulo in ["-", "nan", "None"]:
            continue
            
        processados += 1
        print(f"[{processados}/{min(total_faltantes, max_busca)}] Pesquisando site para: '{titulo}'...")
        
        hp_encontrada = buscar_homepage_ddg(titulo, issn)
        
        if hp_encontrada:
            print(f"   --> Link encontrado: {hp_encontrada}")
            df.loc[idx, col_home] = hp_encontrada
            encontrados += 1
        else:
            print("   --> Nenhum link oficial encontrado.")
            
        # Salva o progresso a cada 10 registros
        if processados % 10 == 0:
            df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
            print("   [Progresso salvo no CSV]")
            
        time.sleep(0.5) # Evita bloqueio de taxa
        
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"\nFinalizado! Total de homepages atualizadas nesta sessão: {encontrados}/{processados}")

if __name__ == "__main__":
    import sys
    limite = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    preencher_homepages(max_busca=limite)
