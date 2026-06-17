# =============================================================================
# Angela AI - Multi-stage Dockerfile
# =============================================================================

# Stage 1: Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (for caching)
COPY apps/backend/pyproject.toml ./
COPY apps/backend/src ./src

# Install Python dependencies
RUN pip install --no-cache-dir --prefix=/install .[standard]

# Stage 2: Production stage
FROM python:3.11-slim as production

# Create non-root user
RUN groupadd -r angela && useradd -r -g angela -d /app -s /sbin/nologin angela

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY apps/backend/src ./src
COPY apps/backend/pyproject.toml ./

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/configs && \
    chown -R angela:angela /app

# Switch to non-root user
USER angela

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/ops/health || exit 1

# Expose port
EXPOSE 8000

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
