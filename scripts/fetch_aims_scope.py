#!/usr/bin/env python3
"""
Script para buscar "Aims and Scope" de cada revista via OpenAlex API (gratuita).
Le dados.csv, consulta cada ISSN, e salva em nova coluna "Aims e Escopo".

Uso: python scripts/fetch_aims_scope.py
"""

import os
import sys
import time
import json
import pandas as pd
import requests
from typing import Optional

# Caminho para o CSV
CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dados.csv")

# OpenAlex API - gratuita, sem autenticacao
# Rate limit: 10 req/s (recomendado: 1 req/s para evitar bloqueios)
BASE_URL = "https://api.openalex.org/sources/issn:{}"
EMAIL = "support@scipubs.com"  # Politely identify ourselves (boas praticas)


def fetch_aims_scope(issn: str) -> Optional[str]:
    """
    Busca o Aims & Scope de uma revista na OpenAlex.
    Retorna o texto ou None se nao encontrar.
    """
    if not issn or issn in ["-", "", "nan", "None"]:
        return None
    
    # Remove espacos e hifens
    issn_clean = issn.replace(" ", "").replace("-", "").strip()
    if len(issn_clean) != 8:
        return None
    
    url = BASE_URL.format(issn_clean)
    headers = {"User-Agent": f"SciPubs/1.0 (mailto:{EMAIL})", "Accept": "application/json"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            # OpenAlex retorna description (abstract) e summary (Aims & Scope)
            desc = data.get("description", "")
            summary = data.get("summary", "")
            
            # Combina description + summary
            aims = ""
            if desc and desc != "None":
                aims += desc
            if summary and summary != "None" and summary != desc:
                if aims:
                    aims += " "
                aims += summary
            return aims if aims else None
        elif resp.status_code == 404:
            return None
        else:
            print(f"  Erro HTTP {resp.status_code} para ISSN {issn}")
            return None
    except Exception as e:
        print(f"  Erro ao buscar ISSN {issn}: {e}")
        return None


def main():
    print("=" * 60)
    print("SciPubs - Busca de Aims & Scope via OpenAlex")
    print("=" * 60)
    
    # Le o CSV
    print(f"\nLendo {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH, sep=";", encoding="utf-8-sig", low_memory=False)
    
    # Normaliza nomes de colunas
    df.columns = [c.strip() for c in df.columns]
    
    # Identifica coluna ISSN
    issn_col = None
    for c in df.columns:
        if "issn" in c.lower():
            issn_col = c
            break
    
    if not issn_col:
        print("ERRO: Coluna ISSN nao encontrada no CSV!")
        return
    
    print(f"Coluna ISSN encontrada: '{issn_col}'")
    print(f"Total de registros: {len(df)}")
    
    # Adiciona coluna Aims e Escopo se nao existir
    if "Aims e Escopo" not in df.columns:
        df["Aims e Escopo"] = ""
    
    # Conta quantos ja tem dados
    ja_preenchidos = df["Aims e Escopo"].astype(str).apply(lambda x: len(x.strip()) > 5 and x.strip() not in ["-", "nan", "None"]).sum()
    print(f"Registros com Aims preenchido: {ja_preenchidos}")
    
    # Filtra apenas os que precisam ser buscados
    mask_vazio = df["Aims e Escopo"].astype(str).apply(
        lambda x: len(x.strip()) <= 5 or x.strip() in ["-", "nan", "None"]
    )
    indices = df[mask_vazio].index.tolist()
    total_buscar = len(indices)
    print(f"Registros a buscar: {total_buscar}")
    
    if total_buscar == 0:
        print("Todos os registros ja tem Aims & Scope!")
        return
    
    # Processa em lotes com delay para respeitar rate limit
    batch_size = 50
    success = 0
    skip = 0
    
    for i, idx in enumerate(indices):
        issn = str(df.at[idx, issn_col]).strip()
        
        aims = fetch_aims_scope(issn)
        
        if aims:
            df.at[idx, "Aims e Escopo"] = aims
            success += 1
            print(f"[{i+1}/{total_buscar}] OK: {issn[:4]}... -> {len(aims)} chars")
        else:
            skip += 1
            print(f"[{i+1}/{total_buscar}] SKIP: {issn[:4]}... -> sem dados")
        
        # Salva a cada batch
        if (i + 1) % batch_size == 0:
            df.to_csv(CSV_PATH, sep=";", index=False, encoding="utf-8-sig")
            print(f"\n  -> Salvo checkpoint ({i+1}/{total_buscar})")
        
        # Delay entre requisicoes (1 req/s)
        if (i + 1) % 3 == 0:
            time.sleep(1)
    
    # Salva final
    df.to_csv(CSV_PATH, sep=";", index=False, encoding="utf-8-sig")
    
    print("\n" + "=" * 60)
    print(f"RESUMO:")
    print(f"  Total processado: {total_buscar}")
    print(f"  Sucesso: {success}")
    print(f"  Sem dados: {skip}")
    print(f"  CSV salvo em: {CSV_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()