from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import yaml

from apps.backend.src.core.system.module_manager.scanner import ModuleScanner, ValidationError
from apps.backend.src.core.system.module_manager.models import ModuleKind


VALID_YAML = {
    "name": "test_module",
    "version": "1.0.0",
    "kind": "service",
    "lifecycle": {"init": "test_module.init"},
}


def _write_module(tmpdir: str, subdir: str, data: dict) -> Path:
    mod_dir = Path(tmpdir) / subdir
    mod_dir.mkdir(parents=True, exist_ok=True)
    yaml_path = mod_dir / "module.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(data, f)
    return yaml_path


def _scanner(tmpdir: str) -> ModuleScanner:
    return ModuleScanner(scan_paths=[Path(tmpdir)])


class TestDiscover:
    def test_discover_finds_module_yaml(self):
        with TemporaryDirectory() as tmpdir:
            _write_module(tmpdir, "test_mod", VALID_YAML)
            scanner = _scanner(tmpdir)
            result = scanner.discover()
            assert len(result) == 1
            assert result[0].name == "test_module"

    def test_discover_empty_dir(self):
        with TemporaryDirectory() as tmpdir:
            scanner = _scanner(tmpdir)
            result = scanner.discover()
            assert result == []

    def test_discover_invalid_yaml(self):
        with TemporaryDirectory() as tmpdir:
            yaml_path = Path(tmpdir) / "test_mod" / "module.yaml"
            yaml_path.parent.mkdir(parents=True)
            with open(yaml_path, "w") as f:
                f.write("- one\n- two\n")
            scanner = _scanner(tmpdir)
            with pytest.raises(ValidationError, match="root must be a mapping"):
                scanner.discover()

    def test_discover_missing_name(self):
        with TemporaryDirectory() as tmpdir:
            data = VALID_YAML.copy()
            del data["name"]
            _write_module(tmpdir, "test_mod", data)
            scanner = _scanner(tmpdir)
            with pytest.raises(ValidationError, match="name is required"):
                scanner.discover()

    def test_discover_missing_version(self):
        with TemporaryDirectory() as tmpdir:
            data = VALID_YAML.copy()
            del data["version"]
            _write_module(tmpdir, "test_mod", data)
            scanner = _scanner(tmpdir)
            with pytest.raises(ValidationError, match="version is required"):
                scanner.discover()

    def test_discover_missing_init(self):
        with TemporaryDirectory() as tmpdir:
            data = VALID_YAML.copy()
            del data["lifecycle"]
            _write_module(tmpdir, "test_mod", data)
            scanner = _scanner(tmpdir)
            with pytest.raises(ValidationError, match="lifecycle.init is required"):
                scanner.discover()

    def test_discover_invalid_kind(self):
        with TemporaryDirectory() as tmpdir:
            data = VALID_YAML.copy()
            data["kind"] = "bogus"
            _write_module(tmpdir, "test_mod", data)
            scanner = _scanner(tmpdir)
            with pytest.raises(ValidationError, match="unknown kind"):
                scanner.discover()

    def test_discover_multiple_modules(self):
        with TemporaryDirectory() as tmpdir:
            yaml_a = dict(VALID_YAML, name="alpha")
            yaml_b = dict(VALID_YAML, name="beta")
            _write_module(tmpdir, "b_mod", yaml_b)
            _write_module(tmpdir, "a_mod", yaml_a)
            scanner = _scanner(tmpdir)
            result = scanner.discover()
            assert len(result) == 2
            assert result[0].name == "alpha"
            assert result[1].name == "beta"

    def test_discover_optional_fields(self):
        with TemporaryDirectory() as tmpdir:
            data = {
                "name": "rich_module",
                "version": "2.1.0",
                "kind": "adapter",
                "description": "A rich module with all fields",
                "depends_on": {
                    "required": ["core"],
                    "optional": ["logging"],
                },
                "provides": {
                    "services": [
                        {"name": "svc1", "interface": "ISvc", "type": "factory"},
                    ],
                    "adapters": [
                        {"name": "adp1", "interface": "IAdp"},
                    ],
                },
                "lifecycle": {
                    "init": "rich_module.init",
                    "start": "rich_module.start",
                    "stop": "rich_module.stop",
                    "health": {"endpoint": "/health", "interval": 10, "timeout": 3},
                    "hooks": [
                        {"event": "pre_init", "handler": "rich_module.pre_init"},
                    ],
                    "thread_safe": False,
                },
                "config": {"key": "value"},
            }
            _write_module(tmpdir, "rich_mod", data)
            scanner = _scanner(tmpdir)
            result = scanner.discover()
            assert len(result) == 1
            desc = result[0]
            assert desc.name == "rich_module"
            assert desc.version == "2.1.0"
            assert desc.kind == ModuleKind.ADAPTER
            assert desc.description == "A rich module with all fields"
            assert desc.depends_on.required == ["core"]
            assert desc.depends_on.optional == ["logging"]
            assert len(desc.provides.services) == 1
            assert desc.provides.services[0].name == "svc1"
            assert desc.provides.services[0].interface == "ISvc"
            assert desc.provides.services[0].type == "factory"
            assert len(desc.provides.adapters) == 1
            assert desc.provides.adapters[0].name == "adp1"
            assert desc.provides.adapters[0].interface == "IAdp"
            assert desc.lifecycle.init == "rich_module.init"
            assert desc.lifecycle.start == "rich_module.start"
            assert desc.lifecycle.stop == "rich_module.stop"
            assert desc.lifecycle.health.endpoint == "/health"
            assert desc.lifecycle.health.interval == 10
            assert desc.lifecycle.health.timeout == 3
            assert len(desc.lifecycle.hooks) == 1
            assert desc.lifecycle.hooks[0].event == "pre_init"
            assert desc.lifecycle.hooks[0].handler == "rich_module.pre_init"
            assert desc.lifecycle.thread_safe is False
            assert desc.config == {"key": "value"}

    def test_discover_thread_safe_default(self):
        with TemporaryDirectory() as tmpdir:
            data = VALID_YAML.copy()
            _write_module(tmpdir, "test_mod", data)
            scanner = _scanner(tmpdir)
            result = scanner.discover()
            assert result[0].lifecycle.thread_safe is True

    def test_discover_thread_safe_false(self):
        with TemporaryDirectory() as tmpdir:
            data = {
                "name": "unsafe_mod",
                "version": "1.0.0",
                "kind": "service",
                "lifecycle": {
                    "init": "unsafe_mod.init",
                    "thread_safe": False,
                },
            }
            _write_module(tmpdir, "unsafe_mod", data)
            scanner = _scanner(tmpdir)
            result = scanner.discover()
            assert result[0].lifecycle.thread_safe is False
