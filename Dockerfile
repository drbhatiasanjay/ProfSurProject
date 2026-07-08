FROM us-east1-docker.pkg.dev/tempproject-462219/cloud-run-source-deploy/lifecycle-leverage-base:latest

WORKDIR /app

# Install torch CPU separately (too large for base image bake)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# App code only — all Python deps are pre-baked in the base image
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
