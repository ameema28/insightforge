# InsightForge Production Dockerfile
# Multi-stage build for smaller image size
# Cloud Run compatible: listens on PORT env var

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1     PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for pandas, matplotlib, and security
RUN apt-get update && apt-get install -y --no-install-recommends     gcc     g++     libgomp1     libffi-dev     libssl-dev     && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies FIRST (for layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create memory storage directory
RUN mkdir -p .memory

# Cloud Run requires listening on $PORT (defaults to 8080)
ENV PORT=8080
EXPOSE 8080

# Healthcheck for Cloud Run / container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3     CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/_stcore/health')" || exit 1

# Run Streamlit on the correct port and address
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true", "--browser.gatherUsageStats=false"]