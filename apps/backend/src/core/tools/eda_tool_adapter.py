# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L2]
# =============================================================================

"""Safe, optional adapters for local EDA command-line tools."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import shutil
import signal
import time
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from core.system.config.magic_numbers import limit_value, timeout_value

logger = logging.getLogger(__name__)

_TOOL_NAMES = (
    "ngspice",
    "klayout",
    "magic",
    "kicad",
    "easyeda",
    "jlcone",
    "iverilog",
    "verilator",
    "yosys",
)
_EASYEDA_EXTENSIONS = frozenset({".json", ".zip", ".epro", ".epro2", ".elibz"})
_SAFE_LABEL = re.compile(r"[^A-Za-z0-9_.-]+")
_NGSPICE_ROW = re.compile(
    r"^\s*\d+\s+([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"
    r"\s+([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"
)
_KLAYOUT_MARKER = re.compile(r"EDA_KLAYOUT_JSON:(\{.*\})")
_MAGIC_TECH_FILE = re.compile(r"EDA_MAGIC_TECH_FILE=(.*)")
_MAGIC_TECH_NAME = re.compile(r"EDA_MAGIC_TECH_NAME=(.*)")
_MAGIC_READ_STATUS = re.compile(r"EDA_MAGIC_READ_STATUS=(.*)")
_MAGIC_LOAD_STATUS = re.compile(r"EDA_MAGIC_LOAD_STATUS=(.*)")
_MAGIC_BOX_STATUS = re.compile(r"EDA_MAGIC_BOX_STATUS=(.*)")
_MAGIC_DRC_STATUS = re.compile(r"EDA_MAGIC_DRC_STATUS=(.*)")
_MAGIC_DRC_COUNT = re.compile(r"Total DRC errors found:\s*(\d+)")
_MAGIC_WRITE_STATUS = re.compile(r"EDA_MAGIC_WRITE_STATUS=(.*)")


@dataclass(frozen=True)
class EdaWorkspace:
    """An isolated workspace for one EDA job."""

    job_id: str
    root: Path

    @property
    def input_dir(self) -> Path:
        return self.root / "input"

    @property
    def output_dir(self) -> Path:
        return self.root / "output"

    @property
    def logs_dir(self) -> Path:
        return self.root / "logs"


class EdaToolAdapter:
    """Run local EDA tools and explicit client/file bridges with bounded workspaces."""

    def __init__(
        self,
        config: Optional[Mapping[str, Any]] = None,
        output_root: Optional[os.PathLike[str] | str] = None,
    ) -> None:
        loaded = self._load_config()
        if config:
            loaded.update(dict(config))
        self.config: Dict[str, Any] = loaded
        self.enabled = bool(self.config.get("enabled", True))
        configured_root = output_root or self.config.get("output_root", "data/eda_runs")
        self.output_root = Path(configured_root).expanduser()
        if not self.output_root.is_absolute():
            self.output_root = (Path.cwd() / self.output_root).resolve()
        self.timeout = self._positive_float(
            self.config.get("timeout", timeout_value("system.eda.timeout", 30.0)),
            timeout_value("system.eda.timeout", 30.0),
        )
        self.probe_timeout = self._positive_float(
            self.config.get("probe_timeout_seconds", min(self.timeout, 15.0)),
            min(self.timeout, 15.0),
        )
        self.max_output_bytes = self._positive_int(
            self.config.get("max_output_bytes", 1_048_576), 1_048_576
        )
        self.max_input_bytes = self._positive_int(
            self.config.get("max_input_bytes", 268_435_456), 268_435_456
        )
        self.max_sweep_points = self._positive_int(
            self.config.get("max_sweep_points", limit_value("system.eda.max_sweep_points", 32)),
            32,
        )

    @staticmethod
    def _load_config() -> Dict[str, Any]:
        try:
            from core.system.config.tiered_loader import get_config

            loaded = get_config("system/eda")
            if isinstance(loaded, dict):
                return dict(loaded)
        except Exception:
            logger.warning("EDA config unavailable; using safe defaults", exc_info=True)
        return {}

    @staticmethod
    def _validate_spice_deck(deck: str) -> None:
        if not isinstance(deck, str) or not deck.strip():
            raise ValueError("SPICE deck must not be empty")
        if re.search(r"(?im)^\s*\.(?:control|shell|write|edit|include|lib)\b", deck):
            raise ValueError("SPICE deck contains a prohibited directive")

    @staticmethod
    def _positive_float(value: Any, default: float) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return default
        return parsed if parsed > 0 else default

    @staticmethod
    def _positive_int(value: Any, default: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return parsed if parsed > 0 else default

    @staticmethod
    def _layer_number(value: Any, default: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return parsed if 0 <= parsed <= 65_535 else default

    @staticmethod
    def _safe_label(label: str) -> str:
        cleaned = _SAFE_LABEL.sub("_", str(label or "job")).strip("._")
        return (cleaned or "job")[:64]

    @staticmethod
    def _version_line(text: str, tool: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return ""
        preferred = [line for line in lines if tool.lower() in line.lower()]
        return (preferred[0] if preferred else lines[0])[:200]

    def _tool_settings(self, tool: str) -> Dict[str, Any]:
        tools = self.config.get("tools", {})
        if not isinstance(tools, dict):
            return {}
        settings = tools.get(tool, {})
        return dict(settings) if isinstance(settings, dict) else {}

    def _resolve_tool(self, tool: str) -> Optional[str]:
        settings = self._tool_settings(tool)
        command = str(settings.get("command", tool) or "").strip()
        if not command:
            return None
        candidate = Path(command).expanduser()
        if candidate.is_absolute():
            resolved = str(candidate.resolve()) if candidate.is_file() else None
        else:
            resolved = shutil.which(command)
        if not resolved:
            return None
        if not os.access(resolved, os.X_OK):
            return None
        return resolved

    def _command_args(self, tool: str, *args: str) -> Optional[List[str]]:
        command = self._resolve_tool(tool)
        if command is None:
            return None
        prefix_args = self._tool_settings(tool).get("prefix_args", [])
        if not isinstance(prefix_args, list):
            prefix_args = []
        return [command, *[str(value) for value in prefix_args], *[str(value) for value in args]]

    def create_workspace(self, prefix: str = "eda") -> EdaWorkspace:
        """Create a unique workspace without sharing output paths across jobs."""
        safe_prefix = self._safe_label(prefix)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        job_id = f"{safe_prefix}_{stamp}_{uuid.uuid4().hex[:10]}"
        workspace = EdaWorkspace(job_id=job_id, root=self.output_root / job_id)
        workspace.input_dir.mkdir(parents=True, exist_ok=False)
        workspace.output_dir.mkdir(parents=True, exist_ok=False)
        workspace.logs_dir.mkdir(parents=True, exist_ok=False)
        return workspace

    def _ensure_inside_workspace(
        self, path: os.PathLike[str] | str, workspace: EdaWorkspace
    ) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = workspace.root / candidate
        resolved = candidate.resolve()
        try:
            resolved.relative_to(workspace.root.resolve())
        except ValueError as exc:
            raise ValueError("EDA input must stay inside the job workspace") from exc
        return resolved

    @staticmethod
    def _decode_output(value: bytes, limit: int) -> str:
        if len(value) > limit:
            value = value[:limit] + b"\n...[output truncated]"
        return value.decode("utf-8", errors="replace")

    @staticmethod
    async def _finish_process(process: asyncio.subprocess.Process) -> None:
        await process.wait()
        transport = getattr(process, "_transport", None)
        if transport is not None:
            transport.close()
            setattr(process, "_transport", None)

    async def _run(
        self,
        argv: Sequence[str],
        cwd: Path,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        command = [str(arg) for arg in argv]
        effective_timeout = self._positive_float(timeout or self.timeout, self.timeout)
        popen_kwargs: Dict[str, Any] = {
            "cwd": str(cwd),
            "stdout": asyncio.subprocess.PIPE,
            "stderr": asyncio.subprocess.PIPE,
        }
        if os.name == "posix":
            popen_kwargs["start_new_session"] = True
        started = time.perf_counter()
        try:
            process = await asyncio.create_subprocess_exec(*command, **popen_kwargs)
        except (OSError, ValueError) as exc:
            return {
                "return_code": None,
                "timed_out": False,
                "stdout": "",
                "stderr": str(exc),
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                "argv": command,
            }
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=effective_timeout
            )
            return_code = process.returncode
            await self._finish_process(process)
            return {
                "return_code": return_code,
                "timed_out": False,
                "stdout": self._decode_output(stdout or b"", self.max_output_bytes),
                "stderr": self._decode_output(stderr or b"", self.max_output_bytes),
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                "argv": command,
            }
        except asyncio.TimeoutError:
            try:
                if os.name == "posix":
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
            except ProcessLookupError:
                pass
            await self._finish_process(process)
            return {
                "return_code": None,
                "timed_out": True,
                "stdout": "",
                "stderr": f"timeout after {effective_timeout:.2f}s",
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                "argv": command,
            }

    def _artifact(self, path: Path, kind: str, workspace: EdaWorkspace) -> Optional[Dict[str, Any]]:
        if not path.is_file():
            return None
        try:
            size = path.stat().st_size
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            relative = str(path.resolve().relative_to(workspace.root.resolve()))
        except (OSError, ValueError) as exc:
            logger.warning("Unable to inspect EDA artifact %s", exc, exc_info=True)
            return None
        return {
            "type": kind,
            "path": str(path.resolve()),
            "relative_path": relative,
            "bytes": size,
            "sha256": digest,
        }

    def _artifacts(
        self, workspace: EdaWorkspace, entries: Sequence[Tuple[Path, str]]
    ) -> List[Dict[str, Any]]:
        artifacts = []
        for path, kind in entries:
            artifact = self._artifact(path, kind, workspace)
            if artifact:
                artifacts.append(artifact)
        return artifacts

    def write_text_artifact(
        self, workspace: EdaWorkspace, name: str, content: str, kind: str = "text"
    ) -> Dict[str, Any]:
        """Write a bounded, caller-selected artifact inside a job workspace."""
        safe_name = self._safe_label(name)
        path = workspace.output_dir / f"{safe_name}.txt"
        path.write_text(content, encoding="utf-8")
        artifact = self._artifact(path, kind, workspace)
        if artifact is None:
            raise OSError(f"Unable to create EDA artifact: {path}")
        return artifact

    @staticmethod
    def _validate_rtl_source(source: str) -> None:
        if not isinstance(source, str) or not source.strip():
            raise ValueError("RTL source must not be empty")
        if re.search(r"`include|\$readmem(?:h|b)", source, re.IGNORECASE):
            raise ValueError("RTL source contains a prohibited external load directive")

    def generate_rtl_artifact(
        self,
        workspace: EdaWorkspace,
        name: str,
        source: str,
    ) -> Dict[str, Any]:
        self._validate_rtl_source(source)
        safe_name = self._safe_label(name)
        path = self._ensure_inside_workspace(workspace.input_dir / f"{safe_name}.sv", workspace)
        path.write_text(source, encoding="utf-8")
        artifact = self._artifact(path, "systemverilog", workspace)
        if artifact is None:
            raise OSError(f"Unable to create RTL artifact: {path}")
        return {
            "status": "generated",
            "artifact": artifact,
            "source_kind": "structural_header_projection",
            "professional_hdl_simulation": False,
        }

    def _write_manifest(
        self, workspace: EdaWorkspace, payload: Mapping[str, Any]
    ) -> Dict[str, Any]:
        manifest = {
            "schema_version": "1.0",
            "job_id": workspace.job_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "workspace": str(workspace.root.resolve()),
            "result": dict(payload),
        }
        manifest_path = workspace.root / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        result = dict(payload)
        result["job_id"] = workspace.job_id
        result["workspace"] = str(workspace.root.resolve())
        result["manifest_path"] = str(manifest_path.resolve())
        return result

    def finalize(self, workspace: EdaWorkspace, payload: Mapping[str, Any]) -> Dict[str, Any]:
        """Persist the final job manifest and return its serializable result."""
        return self._write_manifest(workspace, payload)

    async def probe(self) -> Dict[str, Any]:
        """Probe installed tools and explicit file/GUI bridge integrations."""
        tools: Dict[str, Any] = {}
        for name in _TOOL_NAMES:
            settings = self._tool_settings(name)
            mode = str(settings.get("mode", "cli"))
            if mode in {"file_bridge", "cloud"}:
                tools[name] = {
                    "available": self.enabled,
                    "configured_command": settings.get("command", ""),
                    "mode": mode,
                    "headless": False,
                    "integration_status": "bridge_required",
                }
                continue
            command = self._resolve_tool(name)
            entry: Dict[str, Any] = {
                "available": command is not None,
                "configured_command": settings.get("command", name),
                "mode": mode,
            }
            if mode == "gui":
                entry["headless"] = False
                entry["integration_status"] = "gui_client" if command else "unavailable"
                version_file = settings.get("version_file")
                if command and version_file:
                    try:
                        version_path = Path(str(version_file)).expanduser()
                        if version_path.is_file():
                            entry["version"] = version_path.read_text(encoding="utf-8").strip()
                    except OSError as exc:
                        logger.warning(
                            "Unable to read %s version file: %s", name, exc, exc_info=True
                        )
            if command and mode == "cli":
                version_args = settings.get("version_args", [])
                if isinstance(version_args, list) and version_args:
                    version_command = self._command_args(name, *[str(arg) for arg in version_args])
                    if version_command:
                        version_run = await self._run(
                            version_command,
                            Path.cwd(),
                            self.probe_timeout,
                        )
                        version_text = (version_run["stdout"] + version_run["stderr"]).strip()
                        if version_run.get("return_code") == 0 and not version_run.get("timed_out"):
                            entry["version"] = self._version_line(version_text, name)
                        else:
                            entry["version_error"] = self._version_line(version_text, name)
            tools[name] = entry
        available = any(entry["available"] for entry in tools.values())
        return {"status": "success" if available else "unavailable", "tools": tools}

    @staticmethod
    def _parse_ngspice_log(path: Path) -> Dict[str, Any]:
        if not path.is_file():
            return {"point_count": 0, "cutoff_hz": None}
        rows: List[Tuple[float, float]] = []
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.warning("Unable to read ngspice log %s", exc, exc_info=True)
            return {"point_count": 0, "cutoff_hz": None}
        for line in text.splitlines():
            match = _NGSPICE_ROW.match(line)
            if not match:
                continue
            frequency, gain = float(match.group(1)), float(match.group(2))
            if frequency > 0:
                rows.append((frequency, gain))
        if not rows:
            return {"point_count": 0, "cutoff_hz": None}
        cutoff: Optional[float] = None
        for previous, current in zip(rows, rows[1:]):
            if previous[1] > -3.0 >= current[1]:
                span = previous[1] - current[1]
                ratio = (previous[1] + 3.0) / span if span else 0.0
                cutoff = previous[0] + ratio * (current[0] - previous[0])
                break
        return {
            "point_count": len(rows),
            "cutoff_hz": round(cutoff, 6) if cutoff is not None else None,
            "dc_gain_db": round(rows[0][1], 6),
            "final_gain_db": round(rows[-1][1], 6),
            "min_gain_db": round(min(row[1] for row in rows), 6),
            "max_gain_db": round(max(row[1] for row in rows), 6),
        }

    def build_rc_netlist(
        self,
        resistance_ohm: float = 1_000.0,
        capacitance_f: float = 1e-6,
        start_hz: float = 1.0,
        stop_hz: float = 1e6,
        points: int = 120,
    ) -> str:
        """Build a deterministic, bounded RC low-pass deck."""
        resistance = self._positive_float(resistance_ohm, 1_000.0)
        capacitance = self._positive_float(capacitance_f, 1e-6)
        start = self._positive_float(start_hz, 1.0)
        stop = self._positive_float(stop_hz, 1e6)
        point_count = max(20, min(int(points), 2_000))
        if stop <= start:
            stop = start * 1_000
        return (
            "Angela generated RC low-pass\n"
            "V1 in 0 DC 0 AC 1\n"
            f"R1 in out {resistance:.12g}\n"
            f"C1 out 0 {capacitance:.12g}\n"
            f".ac dec {point_count} {start:.12g} {stop:.12g}\n"
            ".print ac vdb(out)\n"
            ".end\n"
        )

    async def run_ngspice(
        self,
        deck: str,
        workspace: Optional[EdaWorkspace] = None,
        label: str = "circuit",
        finalize: bool = True,
    ) -> Dict[str, Any]:
        """Run a SPICE deck and parse the generated AC print table."""
        self._validate_spice_deck(deck)
        if len(deck.encode("utf-8")) > self.max_input_bytes:
            raise ValueError("SPICE deck exceeds configured input size limit")
        if not self.enabled:
            return {"status": "unavailable", "tool": "ngspice", "diagnostics": ["EDA disabled"]}
        job = workspace or self.create_workspace("ngspice")
        safe_label = self._safe_label(label)
        deck_path = job.input_dir / f"{safe_label}.cir"
        log_path = job.logs_dir / f"{safe_label}.log"
        deck_path.write_text(deck, encoding="utf-8")
        command = self._resolve_tool("ngspice")
        if command is None:
            payload = {
                "status": "unavailable",
                "tool": "ngspice",
                "artifacts": self._artifacts(job, [(deck_path, "netlist")]),
                "metrics": {},
                "diagnostics": ["ngspice executable not found"],
            }
            return self._write_manifest(job, payload) if finalize else payload
        run = await self._run([command, "-n", "-b", "-o", str(log_path), str(deck_path)], job.root)
        metrics = self._parse_ngspice_log(log_path)
        diagnostics = [run["stderr"]] if run["stderr"] else []
        if run["timed_out"]:
            status = "timeout"
            diagnostics.append(run["stderr"])
        elif run["return_code"] != 0:
            status = "error"
        elif not metrics.get("point_count"):
            status = "error"
            diagnostics.append("ngspice produced no parseable AC samples")
        else:
            status = "success"
        payload = {
            "status": status,
            "tool": "ngspice",
            "artifacts": self._artifacts(
                job, [(deck_path, "netlist"), (log_path, "simulation-log")]
            ),
            "metrics": metrics,
            "diagnostics": diagnostics,
            "command": run["argv"],
            "return_code": run["return_code"],
            "duration_ms": run["duration_ms"],
        }
        return self._write_manifest(job, payload) if finalize else payload

    async def generate_layout(
        self,
        workspace: Optional[EdaWorkspace] = None,
        label: str = "layout",
        width_um: float = 20.0,
        height_um: float = 10.0,
    ) -> Dict[str, Any]:
        """Generate and read back a small two-layer KLayout layout."""
        if not self.enabled:
            return {"status": "unavailable", "tool": "klayout", "diagnostics": ["EDA disabled"]}
        job = workspace or self.create_workspace("klayout")
        safe_label = self._safe_label(label)
        try:
            width = max(1, min(int(round(float(width_um) * 1_000)), 10_000_000))
            height = max(1, min(int(round(float(height_um) * 1_000)), 10_000_000))
        except (TypeError, ValueError) as exc:
            raise ValueError("layout dimensions must be numeric") from exc
        script_path = job.input_dir / f"{safe_label}.py"
        gds_relative = f"output/{safe_label}.gds"
        oas_relative = f"output/{safe_label}.oas"
        klayout_settings = self._tool_settings("klayout")
        layer_settings = klayout_settings.get("layers", {})
        if not isinstance(layer_settings, dict):
            layer_settings = {}
        metal1_layer = self._layer_number(layer_settings.get("metal1"), 49)
        via1_layer = self._layer_number(layer_settings.get("via1"), 50)
        script = f"""import json
import os
import pya

width = {width}
height = {height}
layout = pya.Layout()
layout.dbu = 0.001
top = layout.create_cell("ANGELA_EDA")
metal1 = layout.layer({metal1_layer}, 0)
via1 = layout.layer({via1_layer}, 0)
top.shapes(metal1).insert(pya.Box(0, 0, width, height))
top.shapes(metal1).insert(pya.Box(width // 10, height // 10, width // 2, height // 2))
top.shapes(via1).insert(pya.Box(width // 3, height // 3, width // 3 + 500, height // 3 + 500))
gds_path = {gds_relative!r}
oas_path = {oas_relative!r}
layout.write(gds_path)
layout.write(oas_path)
verified = pya.Layout()
verified.read(gds_path)
bbox = verified.top_cell().bbox()
print("EDA_KLAYOUT_JSON:" + json.dumps({{
    "readback_ok": os.path.getsize(gds_path) > 0,
    "gds_bytes": os.path.getsize(gds_path),
    "oas_bytes": os.path.getsize(oas_path),
    "bbox": [bbox.left, bbox.bottom, bbox.right, bbox.top],
}}))
"""
        script_path.write_text(script, encoding="utf-8")
        command = self._resolve_tool("klayout")
        if command is None:
            payload = {
                "status": "unavailable",
                "tool": "klayout",
                "artifacts": self._artifacts(job, [(script_path, "layout-script")]),
                "metrics": {},
                "diagnostics": ["klayout executable not found"],
            }
            return self._write_manifest(job, payload)
        run = await self._run([command, "-b", "-r", str(script_path)], job.root)
        combined = run["stdout"] + "\n" + run["stderr"]
        run_log_path = job.logs_dir / f"{safe_label}.log"
        run_log_path.write_text(combined, encoding="utf-8")
        marker = _KLAYOUT_MARKER.search(combined)
        try:
            metrics = json.loads(marker.group(1)) if marker else {}
        except json.JSONDecodeError:
            metrics = {}
        metrics.update(
            {
                "geometry_count": 3,
                "template_only": True,
                "design_depth": "template",
            }
        )
        gds_path = job.root / gds_relative
        oas_path = job.root / oas_relative
        diagnostics = [run["stderr"]] if run["stderr"] else []
        if run["timed_out"]:
            status = "timeout"
        elif run["return_code"] != 0 or not metrics.get("readback_ok"):
            status = "error"
            if not diagnostics:
                diagnostics.append("KLayout did not produce a readable GDS artifact")
        else:
            status = "success"
        payload = {
            "status": status,
            "tool": "klayout",
            "artifacts": self._artifacts(
                job,
                [
                    (script_path, "layout-script"),
                    (run_log_path, "layout-log"),
                    (gds_path, "gds"),
                    (oas_path, "oasis"),
                ],
            ),
            "metrics": metrics,
            "diagnostics": diagnostics,
            "command": run["argv"],
            "return_code": run["return_code"],
            "duration_ms": run["duration_ms"],
        }
        return self._write_manifest(job, payload)

    async def run_magic(
        self,
        input_layout: os.PathLike[str] | str,
        workspace: EdaWorkspace,
        label: str = "magic",
    ) -> Dict[str, Any]:
        """Attempt a Magic read/DRC/write pass and report PDK limitations honestly."""
        if not self.enabled:
            return {"status": "unavailable", "tool": "magic", "diagnostics": ["EDA disabled"]}
        safe_label = self._safe_label(label)
        input_path = self._ensure_inside_workspace(input_layout, workspace)
        if not input_path.is_file():
            raise FileNotFoundError(input_path)
        input_path_literal = json.dumps(str(input_path), ensure_ascii=False)
        output_path = workspace.output_dir / f"{safe_label}.gds"
        output_literal = json.dumps(str(output_path), ensure_ascii=False)
        script_path = workspace.input_dir / f"{safe_label}.tcl"
        rc_path = workspace.input_dir / f"{safe_label}.rc"
        rc_path.write_text("", encoding="utf-8")
        script = f"""set input_file [file normalize {input_path_literal}]
set output_file [file normalize {output_literal}]
puts "EDA_MAGIC_TECH_NAME=[tech name]"
puts "EDA_MAGIC_TECH_FILE=[tech filename]"
drc rulestats
set read_status [catch {{gds read $input_file}} read_message]
puts "EDA_MAGIC_READ_STATUS=$read_status $read_message"
set top_cell ""
foreach candidate [cellname list topcells] {{
    if {{$candidate eq "ANGELA_EDA"}} {{
        set top_cell $candidate
        break
    }}
}}
if {{$top_cell eq ""}} {{
    set top_cell [lindex [cellname list topcells] 0]
}}
if {{$top_cell eq ""}} {{
    set top_cell "ANGELA_EDA"
}}
set load_status [catch {{load $top_cell}} load_message]
puts "EDA_MAGIC_LOAD_STATUS=$load_status $load_message $top_cell"
select top cell
set box_status [catch {{box}} box_message]
puts "EDA_MAGIC_BOX_STATUS=$box_status $box_message"
puts "EDA_MAGIC_BOX=[box values]"
set drc_status [catch {{drc check}} drc_message]
puts "EDA_MAGIC_DRC_STATUS=$drc_status $drc_message"
drc count total
set write_status [catch {{gds write $output_file}} write_message]
puts "EDA_MAGIC_WRITE_STATUS=$write_status $write_message"
quit 0 -noprompt
"""
        script_path.write_text(script, encoding="utf-8")
        command = self._resolve_tool("magic")
        if command is None:
            payload = {
                "status": "unavailable",
                "tool": "magic",
                "artifacts": self._artifacts(workspace, [(script_path, "magic-script")]),
                "metrics": {},
                "diagnostics": ["magic executable not found"],
            }
            return self._write_manifest(workspace, payload)
        magic_settings = self.config.get("magic", {})
        if not isinstance(magic_settings, dict):
            magic_settings = {}
        configured_tech = str(magic_settings.get("tech", "") or "").strip()
        argv = [command, "-dnull", "-noconsole", "-rcfile", str(rc_path)]
        if configured_tech:
            argv.extend(["-T", configured_tech])
        argv.append(str(script_path))
        run = await self._run(argv, workspace.root)
        combined = run["stdout"] + "\n" + run["stderr"]
        run_log_path = workspace.logs_dir / f"{safe_label}.log"
        run_log_path.write_text(combined, encoding="utf-8")
        tech_file_match = _MAGIC_TECH_FILE.search(combined)
        tech_name_match = _MAGIC_TECH_NAME.search(combined)
        read_match = _MAGIC_READ_STATUS.search(combined)
        load_match = _MAGIC_LOAD_STATUS.search(combined)
        box_match = _MAGIC_BOX_STATUS.search(combined)
        drc_match = _MAGIC_DRC_STATUS.search(combined)
        drc_count_match = _MAGIC_DRC_COUNT.search(combined)
        write_match = _MAGIC_WRITE_STATUS.search(combined)

        def marker_value(match: Optional[re.Match[str]]) -> Optional[str]:
            if not match:
                return None
            value = match.group(1).strip()
            return value.split()[0] if value else ""

        tech_file = tech_file_match.group(1).strip() if tech_file_match else ""
        tech_name = tech_name_match.group(1).strip() if tech_name_match else ""
        rules_match = re.search(r"Total number of rules specifed in tech file:\s*(\d+)", combined)
        rules = int(rules_match.group(1)) if rules_match else 0
        pdk_ready = bool(tech_file and tech_name.lower() != "minimum" and rules > 0)
        read_status = marker_value(read_match)
        load_status = marker_value(load_match)
        box_status = marker_value(box_match)
        drc_status = marker_value(drc_match)
        drc_error_count = int(drc_count_match.group(1)) if drc_count_match else None
        write_status = marker_value(write_match)
        critical_pattern = re.compile(
            r"\b(?:error while reading|unknown layer|i/o error|no cif/gds output style|drc error)\b",
            re.IGNORECASE,
        )
        has_critical_error = bool(critical_pattern.search(combined))
        layout_loaded = read_status == "0" and load_status == "0" and box_status == "0"
        drc_clean = drc_status == "0" and drc_error_count == 0 and not has_critical_error
        diagnostics = [run["stderr"]] if run["stderr"] else []
        if not pdk_ready:
            diagnostics.append("Magic has no usable PDK/rule set; DRC was not certified")
        if has_critical_error:
            diagnostics.append("Magic reported a layout/DRC diagnostic")
        if drc_error_count is not None and drc_error_count > 0:
            diagnostics.append(f"Magic DRC reported {drc_error_count} errors")
        if not layout_loaded:
            diagnostics.append("Magic headless run did not load a selectable layout box")
        output_valid = output_path.is_file() and output_path.stat().st_size > 0
        if run["timed_out"]:
            status = "timeout"
        elif not pdk_ready:
            status = "missing_pdk"
        elif has_critical_error or not output_valid:
            status = "error"
        elif layout_loaded and drc_clean:
            status = "success"
        else:
            status = "degraded"
        metrics = {
            "pdk_ready": pdk_ready,
            "configured_tech": configured_tech,
            "tech_name": tech_name,
            "tech_file": tech_file,
            "rule_count": rules,
            "read_status": read_status,
            "load_status": load_status,
            "box_status": box_status,
            "drc_status": drc_status,
            "drc_error_count": drc_error_count,
            "write_status": write_status,
            "layout_loaded": layout_loaded,
            "drc_clean": drc_clean,
            "output_bytes": output_path.stat().st_size if output_path.is_file() else 0,
        }
        payload = {
            "status": status,
            "tool": "magic",
            "artifacts": self._artifacts(
                workspace,
                [
                    (script_path, "magic-script"),
                    (run_log_path, "magic-log"),
                    (output_path, "gds"),
                ],
            ),
            "metrics": metrics,
            "diagnostics": diagnostics,
            "command": run["argv"],
            "return_code": run["return_code"],
            "duration_ms": run["duration_ms"],
        }
        return self._write_manifest(workspace, payload)

    @staticmethod
    def _kicad_project_text(label: str) -> str:
        return (
            json.dumps(
                {
                    "board": {"design_settings": {"defaults": {}}},
                    "boards": [],
                    "cvpcb": {"equivalence_files": []},
                    "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
                    "meta": {"filename": f"{label}.kicad_pro", "version": 1},
                    "net_settings": {"classes": []},
                    "pcbnew": {"last_paths": {}},
                    "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
                    "sheets": [],
                    "text_variables": {},
                },
                indent=2,
            )
            + "\n"
        )

    @staticmethod
    def _kicad_schematic_text(label: str) -> str:
        schematic_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"angela:{label}:sch"))
        return f"""(kicad_sch (version 20230121) (generator eeschema)
  (uuid "{schematic_uuid}")
  (paper "A4")
  (title_block
    (title "Angela EDA Board")
    (rev "1")
  )
  (lib_symbols)
  (sheet_instances
    (path "/" (page "1"))
  )
)
"""

    @staticmethod
    def _kicad_board_text(width_mm: float, height_mm: float) -> str:
        right = round(10.0 + width_mm, 3)
        bottom = round(10.0 + height_mm, 3)
        return f"""(kicad_pcb (version 20221018) (generator pcbnew)
  (general
    (thickness 1.6)
  )
  (paper "A4")
  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (44 "Edge.Cuts" user)
  )
  (setup
    (pad_to_mask_clearance 0)
  )
  (net 0 "")
  (gr_rect
    (start 10 10)
    (end {right} {bottom})
    (stroke (width 0.1) (type solid))
    (fill none)
    (layer "Edge.Cuts")
  )
)
"""

    def _artifact_tree(
        self, workspace: EdaWorkspace, root: Path, kind: str
    ) -> List[Dict[str, Any]]:
        if not root.is_dir():
            return []
        entries = [(path, kind) for path in sorted(root.rglob("*")) if path.is_file()]
        return self._artifacts(workspace, entries)

    @staticmethod
    def _parse_kicad_drc(path: Path) -> Dict[str, Any]:
        if not path.is_file():
            return {"violation_count": 0, "unconnected_count": 0, "parsed": False}
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except (OSError, json.JSONDecodeError):
            return {"violation_count": 0, "unconnected_count": 0, "parsed": False}
        violations = data.get("violations", [])
        unconnected = data.get("unconnected_items", [])
        return {
            "violation_count": len(violations) if isinstance(violations, list) else 0,
            "unconnected_count": len(unconnected) if isinstance(unconnected, list) else 0,
            "parsed": True,
        }

    async def generate_kicad_board(
        self,
        workspace: Optional[EdaWorkspace] = None,
        label: str = "angela_board",
        width_mm: float = 40.0,
        height_mm: float = 30.0,
    ) -> Dict[str, Any]:
        """Generate a minimal KiCad project, run DRC, and export Gerbers."""
        if not self.enabled:
            return {"status": "unavailable", "tool": "kicad", "diagnostics": ["EDA disabled"]}
        job = workspace or self.create_workspace("kicad")
        safe_label = self._safe_label(label)
        width = max(5.0, min(float(width_mm), 500.0))
        height = max(5.0, min(float(height_mm), 500.0))
        board_path = job.input_dir / f"{safe_label}.kicad_pcb"
        project_path = job.input_dir / f"{safe_label}.kicad_pro"
        schematic_path = job.input_dir / f"{safe_label}.kicad_sch"
        board_text = self._kicad_board_text(width, height)
        board_path.write_text(board_text, encoding="utf-8")
        project_path.write_text(self._kicad_project_text(safe_label), encoding="utf-8")
        schematic_path.write_text(self._kicad_schematic_text(safe_label), encoding="utf-8")
        command = self._command_args("kicad")
        if command is None:
            payload = {
                "status": "unavailable",
                "tool": "kicad",
                "artifacts": self._artifacts(
                    job,
                    [
                        (board_path, "kicad-pcb"),
                        (project_path, "kicad-project"),
                        (schematic_path, "kicad-schematic"),
                    ],
                ),
                "metrics": {},
                "diagnostics": ["kicad-cli executable not found"],
            }
            return self._write_manifest(job, payload)
        drc_path = job.output_dir / f"{safe_label}.drc.json"
        gerber_dir = job.output_dir / f"{safe_label}_gerbers"
        gerber_dir.mkdir(parents=True, exist_ok=True)
        drc_run = await self._run(
            [
                *command,
                "pcb",
                "drc",
                "--format",
                "json",
                "--output",
                str(drc_path),
                "--exit-code-violations",
                str(board_path),
            ],
            job.root,
        )
        gerber_run = await self._run(
            [
                *command,
                "pcb",
                "export",
                "gerbers",
                "--output",
                str(gerber_dir),
                "--layers",
                "F.Cu,B.Cu,Edge.Cuts",
                str(board_path),
            ],
            job.root,
        )
        log_path = job.logs_dir / f"{safe_label}.log"
        log_path.write_text(
            "KICAD_DRC\n"
            + drc_run["stdout"]
            + "\n"
            + drc_run["stderr"]
            + "\nKICAD_GERBERS\n"
            + gerber_run["stdout"]
            + "\n"
            + gerber_run["stderr"],
            encoding="utf-8",
        )
        drc_metrics = self._parse_kicad_drc(drc_path)
        gerber_artifacts = self._artifact_tree(job, gerber_dir, "gerber")
        component_count = board_text.count("(footprint ")
        net_count = max(0, board_text.count("(net ") - 1)
        track_count = board_text.count("(segment ")
        via_count = board_text.count("(via ")
        diagnostics = [text for text in (drc_run["stderr"], gerber_run["stderr"]) if text]
        if drc_run["timed_out"] or gerber_run["timed_out"]:
            status = "timeout"
        elif gerber_run["return_code"] != 0 or not gerber_artifacts:
            status = "error"
        elif drc_run["return_code"] not in (0, 5) or not drc_metrics["parsed"]:
            status = "degraded"
        elif drc_metrics["violation_count"] or drc_metrics["unconnected_count"]:
            status = "degraded"
        else:
            status = "success"
        payload = {
            "status": status,
            "tool": "kicad",
            "artifacts": self._artifacts(
                job,
                [
                    (board_path, "kicad-pcb"),
                    (project_path, "kicad-project"),
                    (schematic_path, "kicad-schematic"),
                    (drc_path, "kicad-drc"),
                    (log_path, "kicad-log"),
                ],
            )
            + gerber_artifacts,
            "metrics": {
                "violation_count": drc_metrics["violation_count"],
                "unconnected_count": drc_metrics["unconnected_count"],
                "drc_parsed": drc_metrics["parsed"],
                "width_mm": width,
                "height_mm": height,
                "gerber_count": len(gerber_artifacts),
                "component_count": component_count,
                "net_count": net_count,
                "track_count": track_count,
                "via_count": via_count,
                "template_only": component_count == 0 and track_count == 0,
                "design_depth": (
                    "template" if component_count == 0 and track_count == 0 else "layout"
                ),
            },
            "diagnostics": diagnostics,
            "command": [drc_run["argv"], gerber_run["argv"]],
            "return_code": gerber_run["return_code"],
            "duration_ms": round(drc_run["duration_ms"] + gerber_run["duration_ms"], 2),
        }
        return self._write_manifest(job, payload)

    async def stage_easyeda_file(
        self,
        source: os.PathLike[str] | str,
        workspace: Optional[EdaWorkspace] = None,
        label: str = "easyeda_source",
    ) -> Dict[str, Any]:
        """Stage an EasyEDA Standard/Pro export for an EasyEDA client bridge."""
        if not self.enabled:
            return {"status": "unavailable", "tool": "easyeda", "diagnostics": ["EDA disabled"]}
        job = workspace or self.create_workspace("easyeda")
        source_path = Path(source).expanduser().resolve()
        suffix = source_path.suffix.lower()
        if suffix not in _EASYEDA_EXTENSIONS:
            raise ValueError(f"Unsupported EasyEDA export: {suffix or 'no extension'}")
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        if source_path.stat().st_size > self.max_input_bytes:
            raise ValueError("EasyEDA export exceeds configured input size limit")
        safe_label = self._safe_label(label)
        staged_path = job.input_dir / f"{safe_label}{suffix}"
        shutil.copy2(source_path, staged_path)
        bridge_artifact = self.write_text_artifact(
            job,
            f"{safe_label}_bridge",
            json.dumps(
                {
                    "mode": "file_bridge",
                    "source_name": source_path.name,
                    "format": suffix,
                    "staged_path": str(staged_path),
                    "requires_easyeda_client": True,
                },
                ensure_ascii=False,
                indent=2,
            ),
            "easyeda-bridge",
        )
        payload = {
            "status": "ready_for_client",
            "tool": "easyeda",
            "artifacts": self._artifacts(job, [(staged_path, "easyeda-source")])
            + [bridge_artifact],
            "metrics": {
                "mode": "file_bridge",
                "format": suffix,
                "requires_easyeda_client": True,
            },
            "diagnostics": [
                "EasyEDA has no supported standalone headless CLI; open the staged export in EasyEDA"
            ],
        }
        return self._write_manifest(job, payload)

    async def convert_easyeda_footprint(
        self,
        source: os.PathLike[str] | str,
        workspace: Optional[EdaWorkspace] = None,
        label: str = "easyeda_footprint",
    ) -> Dict[str, Any]:
        """Convert an EasyEDA Standard JSON footprint with KiCad's supported importer."""
        if not self.enabled:
            return {"status": "unavailable", "tool": "easyeda", "diagnostics": ["EDA disabled"]}
        source_path = Path(source).expanduser().resolve()
        if source_path.suffix.lower() != ".json" or not source_path.is_file():
            raise ValueError("EasyEDA footprint conversion requires an existing .json export")
        if source_path.stat().st_size > self.max_input_bytes:
            raise ValueError("EasyEDA export exceeds configured input size limit")
        job = workspace or self.create_workspace("easyeda_fp")
        safe_label = self._safe_label(label)
        staged_path = job.input_dir / f"{safe_label}.json"
        shutil.copy2(source_path, staged_path)
        converted_dir = job.output_dir / f"{safe_label}_kicad"
        command = self._command_args("kicad")
        if command is None:
            payload = {
                "status": "unavailable",
                "tool": "easyeda",
                "artifacts": self._artifacts(job, [(staged_path, "easyeda-source")]),
                "metrics": {},
                "diagnostics": ["kicad-cli is required for EasyEDA footprint conversion"],
            }
            return self._write_manifest(job, payload)
        run = await self._run(
            [*command, "fp", "upgrade", "--output", str(converted_dir), str(staged_path)],
            job.root,
        )
        log_path = job.logs_dir / f"{safe_label}.log"
        log_path.write_text(run["stdout"] + "\n" + run["stderr"], encoding="utf-8")
        converted = self._artifact_tree(job, converted_dir, "kicad-footprint")
        status = "success" if run["return_code"] == 0 and converted else "error"
        if run["timed_out"]:
            status = "timeout"
        payload = {
            "status": status,
            "tool": "easyeda",
            "artifacts": self._artifacts(
                job, [(staged_path, "easyeda-source"), (log_path, "conversion-log")]
            )
            + converted,
            "metrics": {"converted_file_count": len(converted)},
            "diagnostics": [run["stderr"]] if run["stderr"] else [],
            "command": run["argv"],
            "return_code": run["return_code"],
            "duration_ms": run["duration_ms"],
        }
        return self._write_manifest(job, payload)

    def prepare_easyeda_handoff(
        self,
        workspace: EdaWorkspace,
        artifacts: Sequence[Mapping[str, Any]],
        label: str = "easyeda_handoff",
    ) -> Dict[str, Any]:
        """Describe KiCad artifacts for a manual/official EasyEDA bridge handoff."""
        safe_label = self._safe_label(label)
        handoff = {
            "mode": "file_bridge",
            "requires_easyeda_client": True,
            "artifacts": [
                {
                    "type": item.get("type"),
                    "path": item.get("path"),
                    "sha256": item.get("sha256"),
                }
                for item in artifacts
            ],
        }
        handoff_artifact = self.write_text_artifact(
            workspace,
            safe_label,
            json.dumps(handoff, ensure_ascii=False, indent=2),
            "easyeda-handoff",
        )
        return {
            "status": "ready_for_client",
            "tool": "easyeda",
            "artifacts": [handoff_artifact],
            "metrics": {"mode": "file_bridge", "requires_easyeda_client": True},
            "diagnostics": ["No standalone EasyEDA CLI/API is assumed"],
        }

    def prepare_jlcone_handoff(
        self,
        workspace: EdaWorkspace,
        artifacts: Sequence[Mapping[str, Any]],
        label: str = "jlcone_handoff",
    ) -> Dict[str, Any]:
        """Create a JLCONE order-client handoff without placing an order."""
        safe_label = self._safe_label(label)
        order_files = [
            {
                "type": item.get("type"),
                "path": item.get("path"),
                "sha256": item.get("sha256"),
            }
            for item in artifacts
            if item.get("type") in {"gerber", "kicad-drc", "bom"}
        ]
        handoff = {
            "mode": "gui_client",
            "requires_jlcone_client": True,
            "places_order": False,
            "order_files": order_files,
        }
        handoff_artifact = self.write_text_artifact(
            workspace,
            safe_label,
            json.dumps(handoff, ensure_ascii=False, indent=2),
            "jlcone-handoff",
        )
        package_path = workspace.output_dir / f"{safe_label}.zip"
        usable_files = [item for item in order_files if Path(str(item["path"])).is_file()]
        if usable_files:
            with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for item in usable_files:
                    source = Path(str(item["path"]))
                    archive.write(source, arcname=source.name)
        package_artifact = self._artifact(package_path, "jlcone-package", workspace)
        handoff_artifacts = [handoff_artifact]
        if package_artifact:
            handoff_artifacts.append(package_artifact)
        return {
            "status": "ready_for_client" if usable_files else "bridge_required",
            "tool": "jlcone",
            "artifacts": handoff_artifacts,
            "metrics": {
                "mode": "gui_client",
                "requires_jlcone_client": True,
                "order_file_count": len(usable_files),
                "package_bytes": package_path.stat().st_size if package_path.is_file() else 0,
            },
            "diagnostics": [
                "JLCONE has no supported public headless ordering CLI; open the handoff in JLCONE"
            ],
        }


__all__ = ["EdaToolAdapter", "EdaWorkspace"]
