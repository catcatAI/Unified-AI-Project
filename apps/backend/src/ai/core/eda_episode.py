# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================

from __future__ import annotations

import hashlib
import json
import math
import uuid
from typing import Any, Dict, Mapping, Sequence

EDA_EPISODE_SCHEMA_VERSION = "eda-episode/1"
_SENSITIVE_KEY_PARTS = (
    "token",
    "secret",
    "password",
    "cookie",
    "authorization",
    "credential",
    "account",
    "path",
    "filename",
)


def _short_text(value: Any, limit: int = 256) -> str:
    return str(value if value is not None else "")[:limit]


def _sanitize(value: Any, key: str = "") -> Any:
    normalized_key = key.lower()
    if any(part in normalized_key for part in _SENSITIVE_KEY_PARTS):
        return None
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, str):
        return value[:256]
    if isinstance(value, Mapping):
        sanitized: Dict[str, Any] = {}
        for raw_key, raw_value in list(value.items())[:64]:
            key_text = _short_text(raw_key, 64)
            child = _sanitize(raw_value, key_text)
            if child is not None:
                sanitized[key_text] = child
        return sanitized
    if isinstance(value, (list, tuple, set)):
        sanitized_list = []
        for item in list(value)[:64]:
            child = _sanitize(item, key)
            if child is not None:
                sanitized_list.append(child)
        return sanitized_list
    return _short_text(value)


def _status(result: Mapping[str, Any]) -> str:
    return str(result.get("status", "unavailable"))


def _number(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def _check(checks: list[bool], reasons: list[str], condition: bool, reason: str) -> None:
    checks.append(bool(condition))
    if not condition:
        reasons.append(reason)


def _evaluate_pcb(results: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    kicad = results.get("kicad", {})
    metrics = kicad.get("metrics", {})
    if not isinstance(metrics, Mapping):
        metrics = {}
    checks: list[bool] = []
    reasons: list[str] = []
    _check(checks, reasons, _status(kicad) == "success", "kicad_status_not_success")
    _check(checks, reasons, metrics.get("drc_parsed") is True, "kicad_drc_not_parsed")
    _check(
        checks,
        reasons,
        int(_number(metrics.get("violation_count"), -1)) == 0,
        "kicad_has_violations",
    )
    _check(
        checks,
        reasons,
        int(_number(metrics.get("unconnected_count"), -1)) == 0,
        "kicad_has_unconnected_items",
    )
    _check(
        checks,
        reasons,
        int(_number(metrics.get("gerber_count"), 0)) > 0,
        "kicad_has_no_gerbers",
    )
    component_count = int(_number(metrics.get("component_count"), 0))
    track_count = int(_number(metrics.get("track_count"), 0))
    template_only = metrics.get("template_only") is True or (
        component_count == 0 and track_count == 0
    )
    _check(checks, reasons, not template_only, "pcb_template_only")
    for name in ("easyeda", "jlcone"):
        if name not in results:
            continue
        result = results[name]
        status = _status(result)
        if status not in {"skipped", "success", "ready_for_client", "bridge_required"}:
            reasons.append(f"{name}_handoff_not_ready")
    quality = round(sum(checks) / len(checks), 4) if checks else 0.0
    eligible = not reasons
    return {
        "status": "eligible" if eligible else "quarantined",
        "eligible": eligible,
        "quality": quality,
        "reasons": reasons,
        "metrics": {
            "violation_count": metrics.get("violation_count"),
            "unconnected_count": metrics.get("unconnected_count"),
            "gerber_count": metrics.get("gerber_count"),
            "component_count": metrics.get("component_count"),
            "net_count": metrics.get("net_count"),
            "track_count": metrics.get("track_count"),
            "template_only": template_only,
            "design_depth": metrics.get("design_depth", "template" if template_only else "layout"),
        },
    }


def _evaluate_ic(results: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    layout = results.get("layout", {})
    simulation = results.get("simulation", {})
    exploration = results.get("exploration", {})
    magic = results.get("magic", {})
    layout_metrics = layout.get("metrics", {})
    simulation_metrics = simulation.get("metrics", {})
    magic_metrics = magic.get("metrics", {})
    if not isinstance(layout_metrics, Mapping):
        layout_metrics = {}
    if not isinstance(simulation_metrics, Mapping):
        simulation_metrics = {}
    if not isinstance(magic_metrics, Mapping):
        magic_metrics = {}
    checks: list[bool] = []
    reasons: list[str] = []
    _check(checks, reasons, _status(layout) == "success", "layout_status_not_success")
    _check(checks, reasons, layout_metrics.get("template_only") is not True, "layout_template_only")
    _check(checks, reasons, _status(simulation) == "success", "simulation_status_not_success")
    _check(
        checks,
        reasons,
        int(_number(simulation_metrics.get("point_count"), 0)) > 0,
        "simulation_has_no_samples",
    )
    _check(
        checks,
        reasons,
        simulation_metrics.get("cutoff_hz") is not None,
        "simulation_cutoff_missing",
    )
    if _status(exploration) not in {"skipped", "unavailable"}:
        _check(
            checks,
            reasons,
            _status(exploration) == "success",
            "exploration_status_not_success",
        )
        _check(
            checks,
            reasons,
            int(_number(exploration.get("successful_count"), 0)) > 0,
            "exploration_has_no_successful_points",
        )
    _check(checks, reasons, _status(magic) == "success", "magic_status_not_success")
    _check(checks, reasons, magic_metrics.get("pdk_ready") is True, "magic_pdk_not_ready")
    _check(checks, reasons, magic_metrics.get("drc_clean") is True, "magic_drc_not_clean")
    quality = round(sum(checks) / len(checks), 4) if checks else 0.0
    eligible = not reasons
    return {
        "status": "eligible" if eligible else "quarantined",
        "eligible": eligible,
        "quality": quality,
        "reasons": reasons,
        "metrics": {
            "point_count": simulation_metrics.get("point_count"),
            "cutoff_hz": simulation_metrics.get("cutoff_hz"),
            "exploration_points": exploration.get("successful_count", 0),
            "magic_rule_count": magic_metrics.get("rule_count"),
            "layout_template_only": layout_metrics.get("template_only"),
            "layout_design_depth": layout_metrics.get("design_depth", "template"),
        },
    }


def _evaluate_ai_card_reference(results: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    result = results.get("ai_card_reference", {})
    if not isinstance(result, Mapping):
        result = {}
    validation = result.get("validation", {})
    if not isinstance(validation, Mapping):
        validation = {}
    checks = result.get("checks", {})
    if not isinstance(checks, Mapping):
        checks = {}
    hierarchy = result.get("hierarchy", {})
    if not isinstance(hierarchy, Mapping):
        hierarchy = {}
    die = hierarchy.get("die", {})
    if not isinstance(die, Mapping):
        die = {}
    card = hierarchy.get("card", {})
    if not isinstance(card, Mapping):
        card = {}
    host = hierarchy.get("host", {})
    if not isinstance(host, Mapping):
        host = {}
    l1 = die.get("l1_cache", {})
    if not isinstance(l1, Mapping):
        l1 = {}
    l2 = card.get("l2_memory", {})
    if not isinstance(l2, Mapping):
        l2 = {}
    l3 = host.get("l3", {})
    if not isinstance(l3, Mapping):
        l3 = {}
    check_values: list[bool] = []
    reasons: list[str] = []
    _check(
        check_values,
        reasons,
        str(result.get("status", "")) in {"partial", "pass"},
        "ai_card_status_invalid",
    )
    _check(check_values, reasons, validation.get("level") == "L1", "ai_card_not_l1")
    _check(
        check_values,
        reasons,
        validation.get("mode") == "software_only",
        "ai_card_not_software_only",
    )
    _check(
        check_values,
        reasons,
        validation.get("professional_hdl_simulation") is False,
        "ai_card_claims_hdl_simulation",
    )
    _check(
        check_values,
        reasons,
        validation.get("physical_hardware") is False,
        "ai_card_claims_physical_hardware",
    )
    for key in (
        "secondary_update_partition_contract",
        "cache_partition_valid",
        "power_budget_within_prototype_limit",
        "dma_completes_with_backpressure",
        "weight_update_contract",
    ):
        _check(check_values, reasons, checks.get(key) is True, f"ai_card_{key}_failed")
    _check(
        check_values,
        reasons,
        l1.get("implementation") == "self_developed_cache",
        "ai_card_l1_not_die_internal",
    )
    _check(
        check_values,
        reasons,
        l2.get("implementation") == "purchased_memory",
        "ai_card_l2_not_purchased_memory",
    )
    _check(check_values, reasons, l3.get("interface") == "PCIe", "ai_card_l3_not_pcie")
    quality = round(sum(check_values) / len(check_values), 4) if check_values else 0.0
    eligible = not reasons
    return {
        "status": "eligible" if eligible else "quarantined",
        "eligible": eligible,
        "quality": quality,
        "reasons": reasons,
        "deferred": (
            []
            if result.get("cost", {}).get("decision") != "BLOCKED_PENDING_QUOTES"
            else ["cost_verified"]
        ),
        "metrics": {
            "status": result.get("status"),
            "l1_scope": l1.get("scope"),
            "l2_scope": l2.get("scope"),
            "l3_interface": l3.get("interface"),
            "cost_decision": result.get("cost", {}).get("decision"),
        },
    }


def _evaluate_rtl(results: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    result = results.get("rtl", {})
    if not isinstance(result, Mapping):
        result = {}
    header = result.get("header_recalculation", {})
    if not isinstance(header, Mapping):
        header = {}
    artifact = result.get("rtl_artifact", {})
    if not isinstance(artifact, Mapping):
        artifact = {}
    testbench = result.get("testbench_artifact", {})
    if not isinstance(testbench, Mapping):
        testbench = {}
    checks: list[bool] = []
    reasons: list[str] = []
    _check(
        checks,
        reasons,
        result.get("status") == "generated_structural_projection",
        "rtl_not_generated",
    )
    _check(checks, reasons, result.get("validation_level") == "L1", "rtl_not_l1")
    _check(
        checks,
        reasons,
        result.get("professional_hdl_simulation") is False,
        "rtl_claims_simulation",
    )
    _check(checks, reasons, result.get("physical_hardware") is False, "rtl_claims_physical")
    _check(checks, reasons, result.get("architecture_frozen") is False, "rtl_claims_frozen")
    _check(checks, reasons, header.get("checks_pass") is True, "rtl_header_checks_failed")
    _check(checks, reasons, artifact.get("type") == "systemverilog", "rtl_artifact_missing")
    _check(
        checks,
        reasons,
        testbench.get("type") == "systemverilog",
        "rtl_testbench_artifact_missing",
    )
    quality = round(sum(checks) / len(checks), 4) if checks else 0.0
    eligible = not reasons
    return {
        "status": "eligible" if eligible else "quarantined",
        "eligible": eligible,
        "quality": quality,
        "reasons": reasons,
        "deferred": ["hdl_simulation", "synthesis", "architecture_freeze", "physical_hardware"],
        "metrics": {
            "status": result.get("status"),
            "source_kind": result.get("source_kind"),
            "header_scope": header.get("scope"),
            "header_checks_pass": header.get("checks_pass"),
            "rtl_artifact_type": artifact.get("type"),
        },
    }


def evaluate_eda_result(
    workflow: str,
    results: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    """Return a deterministic, conservative quality verdict for an EDA episode."""
    if workflow == "pcb":
        return _evaluate_pcb(results)
    if workflow == "ic":
        return _evaluate_ic(results)
    if workflow == "ai_card_reference":
        return _evaluate_ai_card_reference(results)
    if workflow == "rtl":
        return _evaluate_rtl(results)
    return {
        "status": "quarantined",
        "eligible": False,
        "quality": 0.0,
        "reasons": ["unknown_workflow"],
        "metrics": {},
    }


def _tool_versions(tools: Mapping[str, Any]) -> Dict[str, Dict[str, str]]:
    versions: Dict[str, Dict[str, str]] = {}
    for name, entry in tools.items():
        if not isinstance(entry, Mapping):
            continue
        version = entry.get("version") or entry.get("version_error")
        if not version:
            continue
        record = {"version": _short_text(version, 200)}
        for field in ("mode", "integration_status"):
            value = entry.get(field)
            if value:
                record[field] = _short_text(value, 80)
        versions[_short_text(name, 64)] = record
    return versions


def _artifact_references(artifacts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    for artifact in list(artifacts)[:256]:
        if not isinstance(artifact, Mapping):
            continue
        digest = str(artifact.get("sha256", "")).lower()
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            continue
        reference: dict[str, Any] = {
            "type": _short_text(artifact.get("type", "artifact"), 64),
            "sha256": digest,
        }
        size = artifact.get("bytes")
        if isinstance(size, int) and size >= 0:
            reference["bytes"] = size
        references.append(reference)
    return references


def build_eda_episode(
    workflow: str,
    parameters: Mapping[str, Any],
    tools: Mapping[str, Any],
    results: Mapping[str, Mapping[str, Any]],
    artifacts: Sequence[Mapping[str, Any]],
    intent_tags: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build a sanitized, replayable EDA learning episode."""
    safe_parameters = _sanitize(parameters)
    if not isinstance(safe_parameters, dict):
        safe_parameters = {}
    safe_tags = [tag for tag in (_short_text(value, 64) for value in intent_tags) if tag]
    outcome = evaluate_eda_result(workflow, results)
    versions = _tool_versions(tools)
    fingerprint_payload = {
        "workflow": workflow,
        "parameters": safe_parameters,
        "tool_versions": versions,
        "outcome": {
            "status": outcome["status"],
            "eligible": outcome["eligible"],
            "quality": outcome["quality"],
            "reasons": outcome["reasons"],
        },
    }
    fingerprint = hashlib.sha256(
        json.dumps(
            fingerprint_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": EDA_EPISODE_SCHEMA_VERSION,
        "episode_id": f"{workflow}_{uuid.uuid4().hex[:16]}",
        "fingerprint": fingerprint,
        "workflow": workflow,
        "intent_tags": safe_tags[:32],
        "parameters": safe_parameters,
        "tool_versions": versions,
        "outcome": outcome,
        "artifacts": _artifact_references(artifacts),
        "governance": {
            "network": False,
            "account_control": False,
            "order_placement": False,
            "human_approval_required": True,
        },
    }


__all__ = [
    "EDA_EPISODE_SCHEMA_VERSION",
    "build_eda_episode",
    "evaluate_eda_result",
]
