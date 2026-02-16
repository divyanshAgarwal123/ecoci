# Use Python 3.12 slim image for efficient Cloud Run deployment
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scripts/ scripts/
COPY agents/ agents/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV RUN_MODE=server

# Create non-root user for security
RUN useradd -m -u 1000 ecoci && chown -R ecoci:ecoci /app
USER ecoci

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run webhook server
CMD ["python", "-m", "scripts.ecoci.webhook_trigger"]
