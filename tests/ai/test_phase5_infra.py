"""
Phase 5 Integration Tests — Infrastructure
Tests for Dockerfile, docker-compose, Prometheus config, Nginx config
"""

import os
from pathlib import Path

import pytest

# 存在性測試錨定 repo 根（2026-10-18 稽核：相對路徑從 apps/backend 跑必炸）
_REPO = Path(__file__).resolve().parents[2]


class TestDockerfile:
    """Tests for root Dockerfile"""

    def test_dockerfile_exists(self):
        dockerfile = _REPO / "Dockerfile"
        assert dockerfile.exists(), "Root Dockerfile not found"

    def test_dockerfile_has_multi_stage(self):
        dockerfile = _REPO / "Dockerfile"
        content = dockerfile.read_text()
        assert "FROM" in content, "No FROM instruction"
        assert content.count("FROM") >= 2, "Not a multi-stage build"

    def test_dockerfile_has_healthcheck(self):
        dockerfile = _REPO / "Dockerfile"
        content = dockerfile.read_text()
        assert "HEALTHCHECK" in content, "No HEALTHCHECK instruction"

    def test_dockerfile_has_non_root_user(self):
        dockerfile = _REPO / "Dockerfile"
        content = dockerfile.read_text()
        assert "useradd" in content or "USER" in content, "No non-root user"


class TestDockerCompose:
    """Tests for docker-compose.yml"""

    def test_docker_compose_exists(self):
        compose = _REPO / "docker-compose.yml"
        assert compose.exists(), "docker-compose.yml not found"

    def test_docker_compose_has_backend(self):
        compose = _REPO / "docker-compose.yml"
        content = compose.read_text()
        assert "backend:" in content, "No backend service"

    def test_docker_compose_has_redis(self):
        compose = _REPO / "docker-compose.yml"
        content = compose.read_text()
        assert "redis:" in content, "No redis service"

    def test_docker_compose_has_postgres(self):
        compose = _REPO / "docker-compose.yml"
        content = compose.read_text()
        assert "postgres:" in content, "No postgres service"

    def test_docker_compose_has_prometheus(self):
        compose = _REPO / "docker-compose.yml"
        content = compose.read_text()
        assert "prometheus:" in content, "No prometheus service"

    def test_docker_compose_has_grafana(self):
        compose = _REPO / "docker-compose.yml"
        content = compose.read_text()
        assert "grafana:" in content, "No grafana service"

    def test_docker_compose_has_nginx(self):
        compose = _REPO / "docker-compose.yml"
        content = compose.read_text()
        assert "nginx:" in content, "No nginx service"


class TestPrometheusConfig:
    """Tests for Prometheus configuration"""

    def test_prometheus_config_exists(self):
        config = _REPO / "configs/prometheus.yml"
        assert config.exists(), "prometheus.yml not found"

    def test_prometheus_has_scrape_config(self):
        config = _REPO / "configs/prometheus.yml"
        content = config.read_text()
        assert "scrape_configs:" in content, "No scrape_configs"

    def test_prometheus_has_backend_target(self):
        config = _REPO / "configs/prometheus.yml"
        content = config.read_text()
        assert "backend:8000" in content, "No backend target"

    def test_prometheus_has_alert_rules(self):
        config = _REPO / "configs/prometheus.yml"
        content = config.read_text()
        assert "alert_rules.yml" in content or "rule_files:" in content, "No alert rules"


class TestNginxConfig:
    """Tests for Nginx configuration"""

    def test_nginx_config_exists(self):
        config = _REPO / "configs/nginx.conf"
        assert config.exists(), "nginx.conf not found"

    def test_nginx_has_upstream(self):
        config = _REPO / "configs/nginx.conf"
        content = config.read_text()
        assert "upstream" in content, "No upstream definition"

    def test_nginx_has_ssl(self):
        config = _REPO / "configs/nginx.conf"
        content = config.read_text()
        assert "ssl" in content.lower(), "No SSL configuration"

    def test_nginx_has_rate_limiting(self):
        config = _REPO / "configs/nginx.conf"
        content = config.read_text()
        assert "limit_req" in content, "No rate limiting"


class TestGrafanaConfig:
    """Tests for Grafana configuration"""

    def test_grafana_datasource_exists(self):
        datasource = _REPO / "configs/grafana/datasources/prometheus.yml"
        assert datasource.exists(), "Grafana datasource not found"

    def test_grafana_dashboard_config_exists(self):
        dashboard = _REPO / "configs/grafana/dashboards/dashboard.yml"
        assert dashboard.exists(), "Grafana dashboard config not found"


class TestDeployWorkflow:
    """Tests for deploy workflow"""

    def test_deploy_workflow_exists(self):
        workflow = _REPO / ".github/workflows/deploy.yml"
        assert workflow.exists(), "deploy.yml not found"

    def test_deploy_workflow_has_build_job(self):
        workflow = _REPO / ".github/workflows/deploy.yml"
        content = workflow.read_text()
        assert "build:" in content, "No build job"

    def test_deploy_workflow_has_deploy_job(self):
        workflow = _REPO / ".github/workflows/deploy.yml"
        content = workflow.read_text()
        assert "deploy-staging:" in content or "deploy-production:" in content, "No deploy job"
