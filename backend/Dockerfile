# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 \
    EMBEDDING_CACHE_DIR=/opt/fastembed-cache

WORKDIR /app

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

RUN --mount=type=cache,target=/tmp/fastembed-cache python -c "import os, shutil; from fastembed import TextEmbedding; source = '/tmp/fastembed-cache'; model = TextEmbedding(os.environ['EMBEDDING_MODEL'], cache_dir=source, threads=1); next(model.embed(['warmup'])); shutil.copytree(source, os.environ['EMBEDDING_CACHE_DIR'], dirs_exist_ok=True)"

COPY app ./app
COPY scripts ./scripts
COPY data ./data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

