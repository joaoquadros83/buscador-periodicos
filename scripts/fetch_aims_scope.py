#!/usr/bin/env python3
"""
Script para buscar "Aims and Scope" + "Mission" de cada revista.
Fontes: OpenAlex API (description + summary) + SciELO ArticleMeta API (mission).

Uso: python scripts/fetch_aims_scope.py
"""

import os
import time
import pandas as pd
import requests
from typing import Optional

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dados.csv")

# OpenAlex API
OPENALEX_URL = "https://api.openalex.org/sources/issn:{}"
# SciELO ArticleMeta API
SCIELO_URL = "https://articlemeta.scielo.org/api/v1/journal/issn/{}"
EMAIL = "support@scipubs.com"


def fetch_openalex(issn_clean: str) -> Optional[str]:
    """Busca description + summary na OpenAlex"""
    url = OPENALEX_URL.format(issn_clean)
    headers = {"User-Agent": f"SciPubs/1.0 (mailto:{EMAIL})", "Accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            desc = data.get("description", "") or ""
            summary = data.get("summary", "") or ""
            aims = ""
            if desc and desc not in ["None", "none"]:
                aims += desc.strip()
            if summary and summary not in ["None", "none"] and summary.strip() != desc.strip():
                if aims:
                    aims += " "
                aims += summary.strip()
            return aims if aims else None
    except Exception:
        pass
    return None


def fetch_scielo(issn_clean: str) -> Optional[str]:
    """Busca mission (missao/objetivos) na SciELO ArticleMeta API"""
    url = SCIELO_URL.format(issn_clean)
    try:
        resp = requests.get(url, timeout=15, params={"format": "json"})
        if resp.status_code == 200:
            data = resp.json()
            # SciELO retorna "mission" em diferentes formatos
            # Pode ser objeto com pt/en/es ou string direta
            journal = data.get("journal", data)  # SciELO pode retornar direto
            mission = None
            if isinstance(journal, dict):
                mission = journal.get("mission")
                if isinstance(mission, dict):
                    # Pega o texto em portugues, ingles ou espanhol
                    mission = mission.get("pt") or mission.get("en") or mission.get("es") or ""
                if mission and str(mission).strip() not in ["None", "none", ""]:
                    return str(mission).strip()
    except Exception:
        pass
    return None


def fetch_aims_scope(issn: str) -> Optional[str]:
    """
    Busca combinada: OpenAlex (description + summary) + SciELO (mission).
    Retorna o texto concatenado ou None.
    """
    if not issn or issn in ["-", "", "nan", "None"]:
        return None

    issn_clean = issn.replace(" ", "").replace("-", "").strip()
    if len(issn_clean) != 8:
        return None

    # Busca de ambas as fontes
    openalex_data = fetch_openalex(issn_clean)
    scielo_data = fetch_scielo(issn_clean)

    parts = []
    if openalex_data:
        parts.append(openalex_data)
    if scielo_data:
        # Adiciona mission se nao for duplicata
        if not openalex_data or scielo_data not in openalex_data:
            parts.append(f"[Mission] {scielo_data}")

    return " ".join(parts) if parts else None


def main():
    print("=" * 60)
    print("SciPubs - Busca de Aims & Scope + Mission")
    print("Fontes: OpenAlex (description+summary) + SciELO (mission)")
    print("=" * 60)

    print(f"\nLendo {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH, sep=";", encoding="utf-8-sig", low_memory=False)
    df.columns = [c.strip() for c in df.columns]

    # Identifica coluna ISSN
    issn_col = None
    for c in df.columns:
        if "issn" in c.lower():
            issn_col = c
            break
    if not issn_col:
        print("ERRO: Coluna ISSN nao encontrada!")
        return

    print(f"ISSN: '{issn_col}', Total: {len(df)} registros")

    # Adiciona coluna Aims e Escopo se nao existir
    if "Aims e Escopo" not in df.columns:
        df["Aims e Escopo"] = ""

    # Conta preenchidos
    ja_preenchidos = df["Aims e Escopo"].astype(str).apply(
        lambda x: len(x.strip()) > 10 and x.strip() not in ["-", "nan", "None"]
    ).sum()
    print(f"Ja preenchidos: {ja_preenchidos}")

    # Filtra vazios
    mask_vazio = df["Aims e Escopo"].astype(str).apply(
        lambda x: len(x.strip()) <= 10 or x.strip() in ["-", "nan", "None"]
    )
    indices = df[mask_vazio].index.tolist()
    total_buscar = len(indices)
    print(f"A buscar: {total_buscar}")

    if total_buscar == 0:
        print("Todos ja preenchidos!")
        return

    # Processa
    batch_size = 50
    success = 0
    skip = 0

    for i, idx in enumerate(indices):
        issn = str(df.at[idx, issn_col]).strip()
        aims = fetch_aims_scope(issn)

        if aims and len(aims) > 10:
            df.at[idx, "Aims e Escopo"] = aims
            success += 1
            fonte = "OpenAlex+SciELO" if "[Mission]" in aims else "OpenAlex"
            print(f"[{i+1}/{total_buscar}] OK {issn[:4]}... {fonte} -> {len(aims)} chars")
        else:
            skip += 1
            if (i + 1) % 100 == 0:
                print(f"[{i+1}/{total_buscar}] SKIP {issn[:4]}... sem dados ({skip} total)")

        # Checkpoint a cada 50
        if (i + 1) % batch_size == 0:
            df.to_csv(CSV_PATH, sep=";", index=False, encoding="utf-8-sig")
            print(f"  -> Checkpoint salvo ({i+1}/{total_buscar})")

        # Delay de 1s a cada 3 requisicoes
        if (i + 1) % 3 == 0:
            time.sleep(1)

    # Salva final
    df.to_csv(CSV_PATH, sep=";", index=False, encoding="utf-8-sig")

    print("\n" + "=" * 60)
    print(f"RESUMO FINAL:")
    print(f"  Processados: {total_buscar}")
    print(f"  Sucesso: {success}")
    print(f"  Sem dados: {skip}")
    print(f"  CSV salvo em: {CSV_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()