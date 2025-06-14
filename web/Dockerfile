FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY web/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY web/server.py .

# Create scripts directory and copy install script (from repository root)
RUN mkdir -p scripts
COPY install.sh ./scripts/install.sh

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "server:app"]
