# ── Campaign Validator Agent — Docker Image ────────────────────────────────
# Base: Python 3.11 slim for a small final image
FROM python:3.11-slim

# Metadata
LABEL maintainer="Drayvn Platform"
LABEL description="Campaign Validator Agent — HITL influencer post validation using Google ADK + Gemini"

# Set working directory
WORKDIR /app

# ── System dependencies ────────────────────────────────────────────────────
# curl is needed for the Streamlit health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ────────────────────────────────────────────────────
# Install deps first (layer cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application code ───────────────────────────────────────────────────────
COPY app.py .
COPY pages/ pages/
COPY campaign_validator/ campaign_validator/
COPY docs/ docs/
COPY README.md .

# ── Runtime directories ────────────────────────────────────────────────────
# images/  — mount a volume here to persist uploaded images
# campaign.db — mount a volume here to persist the SQLite database
RUN mkdir -p images

# ── Streamlit config ───────────────────────────────────────────────────────
# Disable the Streamlit "first-run" browser popup and telemetry
RUN mkdir -p /root/.streamlit && \
    printf '[general]\nemail = ""\n' > /root/.streamlit/credentials.toml && \
    printf '[server]\nheadless = true\nport = 8501\naddress = "0.0.0.0"\n[browser]\ngatherUsageStats = false\n' \
        > /root/.streamlit/config.toml

# ── Exposed port ───────────────────────────────────────────────────────────
EXPOSE 8501

# ── Health check ───────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# ── Entrypoint ─────────────────────────────────────────────────────────────
# Use PYTHONIOENCODING=utf-8 to handle emoji in Streamlit output on all platforms
ENV PYTHONIOENCODING=utf-8
CMD ["python", "-m", "streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
