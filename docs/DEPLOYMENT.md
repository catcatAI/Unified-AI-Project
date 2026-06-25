# Angela AI - Deployment Guide

## Overview

This guide covers deploying Angela AI using Docker Compose.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Git

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/unified-ai-project.git
cd unified-ai-project
```

### 2. Configure Environment

Create a `.env` file in the root directory:

```bash
# Database
POSTGRES_DB=angela
POSTGRES_USER=angela
POSTGRES_PASSWORD=your_secure_password

# Redis
REDIS_PASSWORD=your_redis_password

# API
API_SECRET_KEY=your_api_secret_key

# Monitoring
GRAFANA_ADMIN_PASSWORD=your_grafana_password
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# Or start with monitoring
docker-compose --profile monitoring up -d
```

### 4. Verify Deployment

```bash
# Check service status
docker-compose ps

# Check backend health
curl http://localhost:8000/api/v1/ops/health

# Access Grafana dashboard
open http://localhost:3000
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| backend | 8000 | Angela AI API server |
| redis | 6379 | Cache and pub/sub |
| postgres | 5432 | Primary database |
| prometheus | 9090 | Metrics collection |
| grafana | 3000 | Metrics visualization |
| nginx | 80, 443 | Reverse proxy |

## Configuration

### Backend Configuration

Edit `configs/angela_config.yaml`:

```yaml
server:
  host: 0.0.0.0
  port: 8000
  workers: 4

database:
  url: postgresql://angela:angela@postgres:5432/angela

redis:
  url: redis://redis:6379/0
```

### Prometheus Configuration

Edit `configs/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'angela-backend'
    static_configs:
      - targets: ['backend:8000']
```

### Nginx Configuration

Edit `configs/nginx.conf`:

```nginx
upstream backend {
    server backend:8000;
}
```

## Production Deployment

### Using Docker Compose

```bash
# Start with docker-compose (standard docker-compose.yml)
docker-compose up -d
```

> Note: Kubernetes manifests (`k8s/`) and production override (`docker-compose.prod.yml`) are not yet implemented. See `.github/workflows/deploy.yml` for the current CI/CD pipeline (Docker build → ghcr.io → SSH staging/production).

## Monitoring

### Access Grafana

1. Open http://localhost:3000
2. Login with admin/admin
3. Navigate to Dashboards > Angela AI

### Access Prometheus

1. Open http://localhost:9090
2. View targets: Status > Targets
3. Query metrics: Graph

## Troubleshooting

### Backend Not Starting

```bash
# Check logs
docker-compose logs backend

# Check database connection
docker-compose exec postgres psql -U angela -d angela
```

### Redis Connection Issues

```bash
# Check Redis status
docker-compose exec redis redis-cli ping

# View Redis logs
docker-compose logs redis
```

### High Memory Usage

```bash
# Check container stats
docker stats

# Restart services
docker-compose restart backend
```

## Backup and Restore

### Backup Database

```bash
docker-compose exec postgres pg_dump -U angela angela > backup.sql
```

### Restore Database

```bash
cat backup.sql | docker-compose exec -T postgres psql -U angela -d angela
```

## Updating

```bash
# Pull latest images
docker-compose pull

# Restart services
docker-compose up -d
```

## Security Notes

- Change default passwords in production
- Enable SSL/TLS in Nginx configuration
- Use secrets management for sensitive data
- Regular security audits with Gitleaks
