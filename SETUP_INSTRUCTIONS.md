# Setup SciPubs com Discovery-First + Gemini Fallback

## 🎯 Visão Geral

Este setup implementa a arquitetura **Discovery-First com Gemini Fallback** para o SciPubs.

### Características:
- ✅ **100% Gratuito**: Usuários fornecem suas próprias chaves Gemini
- ✅ **Fallback Inteligente**: Se API falhar, usa algoritmo local
- ✅ **Cache Automático**: Reutiliza resultados recentes
- ✅ **Logging Anônimo**: Sem rastreamento de dados pessoais
- ✅ **Validação Robusta**: Tratamento de erros em todas as camadas

## 📋 Estrutura de Arquivos Criada

```
app-revista/
├── services/
│   ├── __init__.py                    # Factory functions e validação
│   ├── discovery_recommender.py       # Motor de recomendação
│   ├── cache_manager.py              # Cache com SQLite
│   └── article_evaluator.py          # Avaliador de artigos
├── utils/
│   ├── __init__.py
│   ├── validators.py                 # Validadores de dados
│   ├── fuzzy_matcher.py             # Matching de strings
│   ├── normalizer.py                # Normalização
│   └── logger.py                    # Logger anônimo
├── data/                            # Cache SQLite
├── logs/                            # Logs anônimos
├── app.py                           # (SERÁ ATUALIZADO)
├── requirements.txt                 # (ATUALIZADO)
└── SETUP_INSTRUCTIONS.md            # Este arquivo
```

## 🚀 Passo-a-Passo de Implementação

### 1. Fazer Pull da Branch

```bash
cd C:\Users\jquad\Documents\app-revista
git fetch origin
git checkout feature/discovery-first-gemini-fallback
```

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 3. Testar Validação de Dependências

```python
import streamlit as st
from services import validate_dependencies, validate_gemini_key

# Valida instalação
if validate_dependencies():
    print("✅ Todas as dependências OK")

# Testa com chave de teste
key_valida, msg = validate_gemini_key("sua_chave_gemini_aqui")
print(f"{msg}")
```

### 4. Usar no app.py

```python
import streamlit as st
from services import (
    validate_dependencies,
    get_discovery_recommender,
    get_cache_manager,
    get_anonymous_logger
)

# No início do app
if not validate_dependencies():
    st.stop()

# Usar os componentes
cache = get_cache_manager()
logger = get_anonymous_logger()

# Gerar recomendações
recommender = get_discovery_recommender(
    df_local=df_original,
    api_key_gemini=user_api_key,
    prefer_ollama=False  # Usar Gemini em Streamlit Cloud
)

journal_list, erro = recommender.recommend(
    titulo="Seu Título",
    resumo="Seu Resumo",
    idioma="Português",
    top_n=20
)
```

## ⚙️ Configuração do Streamlit Cloud

### secrets.toml

```toml
# Opcional: chave Gemini global (será sobrescrita pela chave do usuário)
# GEMINI_API_KEY = "sua_chave_aqui"

# Firebase (se usar)
[firebase]
type = "service_account"
project_id = "seu_projeto"
# ... resto das credenciais
```

## 🔍 Debugging

### Logs

Os logs estão em `logs/scipubs_YYYY-MM-DD.jsonl`

```python
from utils.logger import AnonymousLogger

logger = AnonymousLogger()
stats = logger.get_stats(dias=7)
print(stats)
```

### Cache

```python
from services.cache_manager import CacheManager

cache = CacheManager()
print(cache.get_stats())
cache.cleanup_expired()
```

## 📊 Fluxo de Uso

1. **Usuário entra no app**
   - Digite ou cole a chave Gemini (opcional)
   - Preench título e resumo

2. **Sistema processa**
   - Valida chave Gemini
   - Verifica cache
   - Chama Gemini API
   - Em caso de erro, usa fallback local

3. **Resultados exibidos**
   - Lista de revistas recomendadas
   - Índices de aderência
   - Probabilidade de aceitação
   - Links para sites oficiais

4. **Logging anônimo**
   - Registra tempo de resposta
   - Conta de sucessos/erros
   - Área de conhecimento
   - Backend utilizado (gemini/local)

## 🔒 Segurança

- ✅ **Chaves não são logadas**
- ✅ **Sem rastreamento de usuários**
- ✅ **Logs rotacionam automaticamente**
- ✅ **Dados pessoais nunca são armazenados**

## 📝 Próximas Etapas

1. Testar em staging (seu PC local)
2. Fazer merge da branch para `main`
3. Deploy em Streamlit Cloud
4. Monitorar logs nos primeiros dias

## ❓ FAQ

**P: Preciso instalar Ollama?**
R: Não! Em Streamlit Cloud, usamos Gemini diretamente.

**P: E se a chave Gemini expirar?**
R: Cai para algoritmo local automaticamente. O app continua funcionando.

**P: Como gero uma chave Gemini?**
R: Acesse https://aistudio.google.com e clique em "Get API Key".

**P: Os dados são armazenados?**
R: Apenas logs anônimos (sem título, resumo ou dados pessoais).

## 🆘 Suporte

Em caso de problemas:
1. Verifique `logs/scipubs_*.jsonl`
2. Teste com: `python -c "from services import validate_dependencies; validate_dependencies()"`
3. Veja `requirements.txt` para versões exatas
