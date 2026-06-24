FROM python:3.11-slim

WORKDIR /app

# System deps for scientific packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ curl && \
    rm -rf /var/lib/apt/lists/*

# Install all deps except torch (torch is behind HAS_TORCH gate — graceful no-op on Cloud Run)
COPY requirements.txt .
RUN pip install --no-cache-dir $(grep -v "^torch" requirements.txt | grep -v "^#" | grep -v "^$")

# App code
COPY . .

# Streamlit config
RUN mkdir -p /app/.streamlit
COPY .streamlit/config.toml /app/.streamlit/config.toml

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true", \
    "--browser.gatherUsageStats=false"]
