# CONTINUAÇÃO DO app.py - PARTE 2 (ABA DE IA COM DISCOVERY-FIRST)
# Cole este código após a Parte 1 do app.py

# ===== SIDEBAR COM LINKS =====
st.sidebar.markdown(f"""
<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0 10px 0;'>
<p style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:12px; letter-spacing: 0.05em;'>{t.get('indexadores_tit', 'INDEXADORES')}</p>
<div style="display: flex; flex-direction: column;">
    <a href="https://access.clarivate.com/login?app=wos" target="_blank" style="text-decoration: none; margin-bottom: 8px;">
        <button style="width: 100%; background-color: #FFFFFF; color: #004B87; border: 1px solid #004B87; padding: 8px; border-radius: 6px; cursor: pointer; font-weight: 500;">
            🔗 Web of Science
        </button>
    </a>
    <a href="https://www.scopus.com" target="_blank" style="text-decoration: none; margin-bottom: 8px;">
        <button style="width: 100%; background-color: #FFFFFF; color: #004B87; border: 1px solid #004B87; padding: 8px; border-radius: 6px; cursor: pointer; font-weight: 500;">
            🔗 Scopus
        </button>
    </a>
    <a href="https://www.scielo.br/" target="_blank" style="text-decoration: none;">
        <button style="width: 100%; background-color: #FFFFFF; color: #004B87; border: 1px solid #004B87; padding: 8px; border-radius: 6px; cursor: pointer; font-weight: 500;">
            🔗 SciELO
        </button>
    </a>
</div>
""", unsafe_allow_html=True)

# ===== HERO SECTION =====
st.markdown(f'''<div style="background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); padding: 25px 35px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.15); margin-bottom: 25px; border-left: 6px solid #FF2B2B;">
<h1 style="color: #ffffff; font-size: 2.3rem; font-weight: 800; margin: 0; padding: 0; letter-spacing: -0.5px;">{t['titulo']}</h1>
<p style="color: #FFFFFF; font-size: 1.1rem; margin: 5px 0 0 0; opacity: 0.85;">{t['subtitulo']}</p>
</div>''', unsafe_allow_html=True)

# ===== EXPANDER COM INFORMAÇÕES =====
with st.expander("💡 Como usar o SciPubs?", expanded=False):
    st.markdown(f"""
    ### Bem-vindo ao SciPubs: O Portal do Pesquisador!
    
    #### O que você pode fazer:
    1. **Busca Avançada**: Pesquise revistas por título, ISSN ou usando filtros por área CNPq
    2. **Recomendador IA**: Cole título e resumo do seu artigo e obtenha recomendações personalizadas
    3. **Métricas Unificadas**: Veja Quartis JCR/SJR, H-Index e links diretos para Google Scholar
    4. **Exportação**: Baixe seus resultados em CSV
    """)

# ===== ABA 1: CATÁLOGO TRADICIONAL =====
tab_busca, tab_ia = st.tabs([t['busca_cat'], t['busca_ia']])

with tab_busca:
    busca = st.text_input(t['buscar_reg'], placeholder=t['placeholder_busca'])
    
    aba_escopo, aba_impacto = st.tabs([t['aba_escopo'], t['aba_impacto']])
    
    with aba_escopo:
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            set_subareas = set()
            if "Subárea do Conhecimento" in df_original.columns:
                for x in df_original["Subárea do Conhecimento"].unique():
                    if str(x).strip() not in ["", "-", "nan", "None"]:
                        for sub in str(x).split(","):
                            set_subareas.add(sub.strip())
            lista_subareas = sorted(list(set_subareas))
            subarea_sel = st.selectbox(t['subarea_lbl'], [t['todas']] + lista_subareas)
        
        with col_f2:
            set_indexadores = set()
            if "Indexador" in df_original.columns:
                for x in df_original["Indexador"].unique():
                    if str(x) != "-":
                        for idx in str(x).split(","):
                            set_indexadores.add(idx.strip())
            indexador_sel = st.multiselect(t['base_lbl'], sorted(list(set_indexadores)))
    
    with aba_impacto:
        col_f4, col_f5, col_f6 = st.columns(3)
        
        with col_f4:
            opcoes_jcr = sorted([str(x).strip() for x in df_original.get("Quartil JCR", pd.Series()).unique() if str(x).strip() not in ["", "-", "nan", "None"]]) if "Quartil JCR" in df_original.columns else ["Q1", "Q2", "Q3", "Q4"]
            q_jcr_sel = st.multiselect(t['jcr_lbl'], opcoes_jcr)
        
        with col_f5:
            opcoes_sjr = sorted([str(x).strip() for x in df_original.get("SJR Best Quartile", pd.Series()).unique() if str(x).strip() not in ["", "-", "nan", "None"]]) if "SJR Best Quartile" in df_original.columns else ["Q1", "Q2", "Q3", "Q4"]
            q_sjr_sel = st.multiselect(t['sjr_lbl'], opcoes_sjr)
        
        with col_f6:
            opcoes_ordenacao = ["Título"]
            if "SJR" in df_original.columns:
                opcoes_ordenacao.append("SJR (Prestígio)")
            criterio_ordem = st.selectbox(t['ordem_lbl'], options=opcoes_ordenacao)
    
    # FILTRAGEM
    df_filtrado = df_original.copy()
    
    if busca:
        df_filtrado = df_filtrado[
            df_filtrado[df_original.columns[0]].astype(str).str.contains(busca, case=False, na=False) |
            df_filtrado.get("ISSN", pd.Series()).astype(str).str.contains(busca, case=False, na=False)
        ]
    
    if subarea_sel != t['todas']:
        df_filtrado = df_filtrado[df_filtrado["Subárea do Conhecimento"].astype(str).str.contains(subarea_sel, case=False, na=False)]
    
    if len(indexador_sel) > 0:
        df_filtrado = df_filtrado[df_filtrado["Indexador"].astype(str).str.contains("|".join(indexador_sel), na=False)]
    
    if len(q_jcr_sel) > 0 and "Quartil JCR" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Quartil JCR"].astype(str).str.strip().isin(q_jcr_sel)]
    
    # Exibição
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(t['cat_tit'])
    
    total_itens = len(df_filtrado)
    if total_itens > 0:
        col_pag1, col_pag2 = st.columns([1.5, 2])
        with col_pag1:
            itens_por_pagina = st.selectbox(t['exibir_pag'], options=[20, 50, 100], index=1)
        
        total_paginas = (total_itens // itens_por_pagina) + (1 if total_itens % itens_por_pagina > 0 else 0)
        with col_pag2:
            pagina_atual = st.number_input(f"{t['pag_lbl']} (1 de {total_paginas}):", min_value=1, max_value=max(1, total_paginas), value=1)
        
        inicio = (pagina_atual - 1) * itens_por_pagina
        fim = inicio + itens_por_pagina
        df_da_pagina = df_filtrado.iloc[inicio:fim].copy()
        
        st.dataframe(df_da_pagina, use_container_width=True, hide_index=True)
        
        csv_pagina = df_da_pagina.to_csv(index=False, sep=';', encoding='utf-8-sig')
        st.download_button(label=f"{t['exportar_btn']} ({len(df_da_pagina)} itens)", data=csv_pagina, file_name="sciindex_pagina.csv", mime="text/csv")
    else:
        st.warning(t['aviso_nada'])

# ===== ABA 2: RECOMENDADOR INTELIGENTE (DISCOVERY-FIRST) =====
with tab_ia:
    st.markdown(f"### {t['ia_titulo']}")
    st.markdown(f"*{t['ia_subtitulo']}*")
    
    # Layout: Input à esquerda, Credenciais à direita
    col_input, col_meta = st.columns([2, 1])
    
    with col_input:
        titulo_artigo = st.text_input(t['ia_campo_titulo'], placeholder="Ex: Análise Epidemiológica de Saúde Coletiva...", key="ia_tit_input")
        resumo_artigo = st.text_area(t['ia_campo_resumo'], placeholder="Cole seu resumo aqui...", height=250, key="ia_res_input")
        disparar_busca = st.button(t['ia_btn_buscar'], type="primary", key="btn_ia_disparar")
    
    with col_meta:
        st.markdown(f"#### {t['ia_credencial_tit']}")
        
        # Tentar ler chave de secrets
        chave_secrets = ""
        try:
            if hasattr(st, "secrets") and st.secrets is not None:
                chave_secrets = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            pass
        
        placeholder_input = "🔑 Chave global ativa (opcional)" if chave_secrets else ""
        user_gemini_key = st.text_input(
            t['ia_chave_api'],
            type="password",
            placeholder=placeholder_input,
            key="ia_chave_input"
        )
        
        api_key_ativa = user_gemini_key.strip() if user_gemini_key else (chave_secrets.strip() if chave_secrets else "")
        
        if not api_key_ativa:
            with st.expander(t['ia_como_obter_titulo'], expanded=False):
                st.markdown(t['ia_como_obter_texto'], unsafe_allow_html=True)
        
        st.markdown(f"#### {t['ia_refinar_pesquisa']}")
        
        # Mapeamento de áreas
        grandes_areas_originais = sorted(list(df_original["Grande Área"].dropna().unique()))
        area_ia_opcoes = {t['todas']: "Todas"}
        for area in grandes_areas_originais:
            area_ia_opcoes[str(area)] = area
        
        area_ia_exibicao = st.selectbox(f"{t['filtro_area']} (IA)", list(area_ia_opcoes.keys()))
        area_ia = area_ia_opcoes[area_ia_exibicao]
        
        indexador_ia = st.selectbox(
            f"{t['filtro_indexador']} (IA)",
            [t['ia_todos']] + list(df_original["Indexador"].dropna().unique())
        )
        
        num_recomendacoes = st.slider(
            t['ia_num_rec'],
            min_value=3,
            max_value=20,
            value=5,
            step=1
        )
    
    # PROCESSAMENTO DE RECOMENDAÇÕES
    if disparar_busca:
        if not api_key_ativa:
            st.error("❌ Por favor, insira sua chave da API do Gemini no painel de Credenciais.")
        elif not titulo_artigo or not resumo_artigo:
            st.warning("⚠️ Preencha o Título e o Resumo do seu artigo.")
        else:
            # Gerar chave de cache
            cache_key = hashlib.md5(
                f"{titulo_artigo.strip().lower()}|{resumo_artigo.strip().lower()}|{num_recomendacoes}|{area_ia}|{indexador_ia}".encode("utf-8")
            ).hexdigest()
            
            # Verificar cache
            resultado_cache = cache_manager.get(cache_key)
            
            if resultado_cache:
                st.info("📦 Resultado recuperado do cache")
                recomendacoes = resultado_cache
                backend_usado = "cache"
            else:
                # Gerar novas recomendações
                status_container = st.empty()
                status_container.info(f"⏳ {t['ia_analisando']}")
                
                tempo_inicio = time.time()
                
                # Usar Discovery Recommender
                recommender = get_discovery_recommender(
                    df_local=df_original,
                    api_key_gemini=api_key_ativa,
                    prefer_ollama=False
                )
                
                recomendacoes, erro = recommender.recommend(
                    titulo=titulo_artigo,
                    resumo=resumo_artigo,
                    idioma=st.session_state.idioma,
                    top_n=num_recomendacoes
                )
                
                tempo_total = time.time() - tempo_inicio
                backend_usado = recommender.get_backend_name()
                
                # Log anônimo
                anonymous_logger.log_recommendation(
                    area_conhecimento=area_ia,
                    tempo_resposta_segundos=tempo_total,
                    num_resultados=len(recomendacoes) if recomendacoes else 0,
                    sucesso=(recomendacoes is not None),
                    idioma=st.session_state.idioma,
                    backend=backend_usado
                )
                
                status_container.empty()
                
                if erro:
                    st.error(f"❌ {erro}")
                    anonymous_logger.log_error(
                        tipo_erro="recomendacao_falhou",
                        componente="discovery_recommender",
                        mensagem=erro,
                        backend=backend_usado
                    )
                else:
                    # Cache result
                    cache_manager.set(
                        cache_key,
                        recomendacoes,
                        ttl=86400 * 7,  # 7 dias
                        source="gemini_discovery"
                    )
            
            # EXIBIÇÃO DE RESULTADOS
            if recomendacoes:
                if backend_usado == "local":
                    st.info("ℹ️ Resultado gerado pelo algoritmo local de relevância temática")
                elif backend_usado == "cache":
                    st.info("📦 Resultado recuperado do cache")
                else:
                    st.success(t['ia_sucesso'])
                
                for idx, rec in enumerate(recomendacoes, 1):
                    with st.container(border=True):
                        st.markdown(f"### #{idx} {rec['nome']}")
                        
                        # Buscar dados locais
                        col_titulo_df = df_original.columns[0]
                        registro = df_original[df_original[col_titulo_df].astype(str).str.lower() == rec['nome'].lower()]
                        
                        if not registro.empty:
                            reg = registro.iloc[0]
                            issn = str(reg.get("ISSN", "-"))
                            indexador = str(reg.get("Indexador", "-"))
                            quartil = str(reg.get("Quartil JCR", "-"))
                            sjr = str(reg.get("SJR", "-"))
                            homepage = str(reg.get("Homepage", ""))
                        else:
                            issn = indexador = quartil = sjr = "-"
                            homepage = ""
                        
                        st.caption(f"**ISSN:** {issn} | **Indexador:** {indexador} | **Quartil:** {quartil} | **SJR:** {sjr}")
                        
                        # Scores
                        aderencia = rec.get('aderencia', rec.get('revista_aderencia', 0))
                        st.markdown(f"🎯 **{t['ia_aderencia_escopo']}:** `{aderencia}%`")
                        st.markdown(f"💡 **{t['ia_card_motivo']}** {rec.get('justificativa', 'Periódico bem alinhado com seu trabalho.')}")
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        col_site, col_h5 = st.columns(2)
                        with col_site:
                            if homepage and homepage not in ["nan", "-", "None", ""]:
                                st.link_button(t['ia_card_site'] + " 🔗", homepage, type="primary", use_container_width=True)
                            else:
                                st.info(t['ia_card_sem_site'])
                        
                        with col_h5:
                            h5_link = str(reg.get("Índice h5", "")) if "Índice h5" in reg.index else ""
                            if h5_link and h5_link not in ["nan", "-", "None", ""]:
                                st.link_button("📊 h5-Index Google Scholar", h5_link, type="secondary", use_container_width=True)

# ===== FOOTER =====
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: #64748B; font-size: 0.85rem; padding: 20px;'>
    <p><strong>© 2026 João F. Soares-Quadros Jr. | PPGE - UFOP</strong></p>
    <p>🔓 <strong>Open Science Matters.</strong> No asks. No fees. No ads. Just use.</p>
</div>
""", unsafe_allow_html=True)
