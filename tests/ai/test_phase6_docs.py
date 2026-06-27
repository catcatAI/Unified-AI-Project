"""
Phase 6 Integration Tests — Polish & Launch
Tests for OpenAPI export, profiler, benchmark baseline, documentation
"""

from pathlib import Path

import pytest


class TestOpenAPIExport:
    """Tests for OpenAPI spec export"""

    def test_export_script_exists(self):
        script = Path("apps/backend/scripts/export_openapi.py")
        assert script.exists(), "export_openapi.py not found"

    def test_export_script_has_main(self):
        script = Path("apps/backend/scripts/export_openapi.py")
        content = script.read_text()
        assert "def export_openapi_spec" in content, "No export_openapi_spec function"


class TestProfiler:
    """Tests for profiling entry point"""

    def test_profiler_script_exists(self):
        script = Path("apps/backend/scripts/profiler.py")
        assert script.exists(), "profiler.py not found"

    def test_profiler_has_imports_mode(self):
        script = Path("apps/backend/scripts/profiler.py")
        content = script.read_text()
        assert "profile_imports" in content, "No profile_imports function"

    def test_profiler_has_memory_mode(self):
        script = Path("apps/backend/scripts/profiler.py")
        content = script.read_text()
        assert "profile_memory" in content, "No profile_memory function"


class TestBenchmarkBaseline:
    """Tests for benchmark baseline"""

    def test_baseline_script_exists(self):
        script = Path("apps/backend/scripts/benchmark_baseline.py")
        assert script.exists(), "benchmark_baseline.py not found"

    def test_baseline_script_has_benchmarks(self):
        script = Path("apps/backend/scripts/benchmark_baseline.py")
        content = script.read_text()
        assert "benchmark_ed3n" in content, "No ED3N benchmark"
        assert "benchmark_garden" in content, "No GARDEN benchmark"


class TestDocumentation:
    """Tests for documentation"""

    def test_readme_exists(self):
        readme = Path("README.md")
        assert readme.exists(), "README.md not found"

    def test_readme_has_content(self):
        readme = Path("README.md")
        content = readme.read_text()
        assert len(content) > 1000, "README.md too short"

    def test_architecture_exists(self):
        arch = Path("docs/ARCHITECTURE.md")
        assert arch.exists(), "ARCHITECTURE.md not found"

    def test_deployment_guide_exists(self):
        deploy = Path("docs/DEPLOYMENT.md")
        assert deploy.exists(), "DEPLOYMENT.md not found"

    def test_deployment_guide_has_content(self):
        deploy = Path("docs/DEPLOYMENT.md")
        content = deploy.read_text()
        assert "docker-compose" in content, "No docker-compose reference"


class TestProjectStructure:
    """Tests for project structure"""

    def test_has_github_workflows(self):
        workflows = Path(".github/workflows")
        assert workflows.exists(), ".github/workflows not found"

    def test_has_configs_directory(self):
        configs = Path("configs")
        assert configs.exists(), "configs directory not found"

    def test_has_tests_directory(self):
        tests = Path("tests")
        assert tests.exists(), "tests directory not found"
