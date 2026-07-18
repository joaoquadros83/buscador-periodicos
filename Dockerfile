# Dockerfile para API FastAPI do SciPubs Hybrid Recommender
FROM python:3.11-slim

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copia dependências primeiro (aproveita cache do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do projeto
COPY . .

# Pré-baixa o modelo sentence-transformers para evitar timeout na primeira requisição
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Expõe a porta da API
EXPOSE 8000

# Comando de inicialização
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
