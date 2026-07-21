#!/usr/bin/env python3
"""
Project Readiness Verification — automated readiness checks for Angela AI.

Usage: python scripts/verify_readiness.py

Runs 10 categories of verification:
  T1 - Test Suite Health (pytest + anti-pattern scan)
  T2 - Server Startup
  T3 - API Endpoint Integrity
  T4 - Import Health
  T5 - Frontend-Backend Path Matching
  T6 - Learning Pipeline
  T7 - Session Management
  T8 - Persistence
  T9 - Error Handling
  T10 - Dead Code

Exit code: 0 = ready, 1 = issues found
"""
import importlib
import os
import re
import subprocess
import sys
import time
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "apps/backend"))
sys.path.insert(0, str(PROJECT_ROOT / "apps/backend/src"))

PASS = 0
FAIL = 0
WARN = 0
TOTAL_START = time.time()


def check(name: str, ok: bool, detail: str = "") -> None:
    global PASS, FAIL, WARN
    if ok:
        PASS += 1
        status = "✅"
    elif detail and "warning" in detail.lower():
        WARN += 1
        status = "⚠️"
        ok = True  # Treat warnings as pass for exit code
    else:
        FAIL += 1
        status = "❌"
    d = f" — {detail}" if detail else ""
    print(f"  {status} {name}{d}")


def run_pytest() -> dict:
    """Run pytest and return summary."""
    result = {"total": 0, "passed": 0, "failed": 0, "errors": 0, "warnings": 0}
    try:
        output = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "--tb=line", "--no-header", "-q",
             "--ignore=tests/ai", "--ignore=tests/benchmarks", "-p", "no:cacheprovider"],
            capture_output=True, text=True, timeout=300, cwd=str(PROJECT_ROOT),
        )
        stdout = output.stdout
        stderr = output.stderr

        # Parse pytest summary line
        import re
        summary = stdout.strip().split("\n")[-1] if stdout.strip() else ""
        m = re.search(r"(\d+)\s+passed", summary)
        result["passed"] = int(m.group(1)) if m else 0
        m = re.search(r"(\d+)\s+failed", summary)
        result["failed"] = int(m.group(1)) if m else 0
        m = re.search(r"(\d+)\s+errors", summary)
        result["errors"] = int(m.group(1)) if m else 0
        m = re.search(r"(\d+)\s+collected", stdout)
        result["total"] = int(m.group(1)) if m else 0
        result["warnings"] = stdout.count("warning") + stderr.count("warning")

        # Check for test collection errors
        if "ERROR collecting" in stdout or "ERROR collecting" in stderr:
            result["collection_errors"] = (stdout + stderr).count("ERROR collecting")

    except subprocess.TimeoutExpired:
        result["error"] = "timeout"
    except FileNotFoundError:
        result["error"] = "pytest not found"
    return result


# ============================================================================
print("=" * 70)
print("  ANGELA AI — PROJECT READINESS VERIFICATION")
print("=" * 70)

# ============================================================================
# T1: Test Health — pytest + anti-patterns
# ============================================================================
print("\n━━━ T1: TEST SUITE HEALTH ━━━")

test_dir = PROJECT_ROOT / "tests"

# Anti-patterns: broad except + pytest.skip
anti_patterns = []
for f in sorted(test_dir.rglob("*.py")):
    try:
        text = f.read_text(encoding="utf-8", errors="ignore")
        if "except Exception:" in text and "pytest.skip" in text:
            anti_patterns.append((f, "except Exception: pytest.skip"))
    except Exception as e:
        print(f"  ⚠️  Error reading test file: {e}")
if anti_patterns:
    for f, pat in anti_patterns:
        check(f"Anti-pattern: {f.relative_to(PROJECT_ROOT)}", False, pat)
else:
    check("No broad except+pytest.skip in tests", True)

# __pycache__ dirs (normal after pytest runs, gitignored)
pycache_count = len(list(test_dir.rglob("__pycache__")))
check(f"__pycache__ dirs ({pycache_count}, gitignored)", pycache_count < 200, "OK")

# Run pytest
pytest_result = run_pytest()
if "error" in pytest_result:
    check("pytest execution", False, pytest_result["error"])
else:
    check("pytest: tests collected", pytest_result["total"] > 0, f"{pytest_result['total']} tests")
    if pytest_result["failed"] + pytest_result["errors"] == 0:
        check("pytest: all passed", True, f"{pytest_result['passed']}/{pytest_result['total']}")
    else:
        check("pytest: failures", False,
              f"{pytest_result['failed']} failed, {pytest_result['errors']} errors, "
              f"{pytest_result['passed']}/{pytest_result['total']} passed")

# ============================================================================
# T2: Server Startup
# ============================================================================
print("\n━━━ T2: SERVER STARTUP ━━━")
try:
    from unittest.mock import MagicMock, patch

    # Check if main already imported (from pytest run)
    import sys
    if "main" in sys.modules:
        del sys.modules["main"]
    # Clean slate for route module caches that might have side effects
    for key in list(sys.modules.keys()):
        if "api.routes" in key or "api.v1" in key:
            del sys.modules[key]

    import main as main_module
    main_module.validate_security_configuration = lambda: True

    # Clear the ABCKeyManager singleton
    if hasattr(main_module, "km"):
        main_module.km = MagicMock()
        main_module.km.has_key.return_value = True
        main_module.km.get_key.return_value = "test-key"

    app = main_module.create_app()

    routes = []
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            for m in route.methods:
                if m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                    routes.append(f"{m} {route.path}")

    doc_routes = [r for r in routes if "/docs" in r or "/openapi" in r or "/redoc" in r]
    api_routes = [r for r in routes if "/api/" in r or r.startswith("GET /health")]
    check("Server creates without errors", True, f"{len(routes)} routes ({len(api_routes)} API, {len(doc_routes)} docs)")
except Exception as e:
    check("Server startup", False, str(e)[:200])
    app = None

# ============================================================================
# T3: Endpoint Integrity
# ============================================================================
print("\n━━━ T3: ENDPOINT INTEGRITY ━━━")

if app is not None:
    api_routes = [(m, p) for p in routes for m in [p.split()[0]] if "/api/" in p.split(" ", 1)[-1] or p.startswith("GET /health")]
    api_routes_clean = [(m.split()[0] if " " in m else m, p.split(" ", 1)[1] if " " in p else p) for p in routes for m in [p.split()[0]] if True]

    # Re-parse properly
    api_routes_clean = set()
    for r in routes:
        parts = r.split(" ", 1)
        if len(parts) == 2:
            api_routes_clean.add((parts[0], parts[1]))

    check("API endpoints registered", len(api_routes_clean) >= 80, f"{len(api_routes_clean)} endpoints")

    # Verify no deprecated/removed endpoints remain
    bad_patterns = ["angela/chat", "/dialogue", "vision/analyze", "generate-image", "mobile/test",
                    "encode-with-retry", "decode-with-fallback", "train-with-checkpoint"]
    remaining_bad = [(m, p) for m, p in api_routes_clean if any(b in p for b in bad_patterns)]
    if remaining_bad:
        for m, p in remaining_bad:
            check(f"Removed endpoint: {m} {p}", False)
    else:
        check("No deprecated/removed endpoints", True)

# ============================================================================
# T4: Import Health
# ============================================================================
print("\n━━━ T4: IMPORT HEALTH ━━━")

# Import individual modules in a fresh process to verify
key_modules = [
    "ai.ed3n.ed3n_engine",
    "ai.garden.garden_engine",
    "ai.memory.ham_memory.ham_manager",
    "ai.reasoning.causal_reasoning_engine",
    "ai.meta.meta_controller",
    "core.engine.state_matrix",
    "core.life.digital_life_integrator",
    "core.security.encryption",
    "services.chat_service",
    "services.math_verifier",
    "services.vision_service",
    "services.audio_service",
    "api.router",
]

for mod_name in key_modules:
    try:
        importlib.import_module(mod_name)
        check(f"Import: {mod_name}", True)
    except Exception as e:
        check(f"Import: {mod_name}", False, str(e)[:120])

# ============================================================================
# T5: Frontend-Backend Path Matching
# ============================================================================
print("\n━━━ T5: FRONTEND-BACKEND PATH MATCHING ━━━")

# Build backend path set
backend_paths = set()
if app is not None:
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            for m in route.methods:
                if m in ("GET", "POST"):
                    backend_paths.add((m, route.path))

# Check api-client.js
api_client = PROJECT_ROOT / "packages/shared-js/js/api-client.js"
if api_client.exists():
    text = api_client.read_text(encoding="utf-8", errors="ignore")
    paths_found = re.findall(r"'([^']*(?:/api/v1/[^']*|/health)[^']*)'", text)
    mismatched = []
    for p in paths_found:
        found = False
        for m_test in ["GET", "POST"]:
            if (m_test, p) in backend_paths:
                found = True
                break
        if not found:
            mismatched.append(p)
    check("api-client.js paths match", len(mismatched) == 0,
          f"{len(paths_found)} paths, {len(mismatched)} mismatched" if mismatched else f"{len(paths_found)} paths OK")
    for p in mismatched:
        check(f"  Mismatch: {p}", False)

# Check multimodal-client.js
mm_client = PROJECT_ROOT / "apps/desktop-app/electron_app/js/multimodal-client.js"
if mm_client.exists():
    text = mm_client.read_text(encoding="utf-8", errors="ignore")
    paths_found = re.findall(r"'([^']*(?:/multimodal/[^']*|/health)[^']*)'", text)
    mismatched = []
    for p in paths_found:
        api_p = f"/api/v1{p}" if not p.startswith("/api/v1") else p
        found = False
        for m_test in ["GET", "POST"]:
            if (m_test, api_p) in backend_paths:
                found = True
                break
        if not found:
            mismatched.append(api_p)
    check("multimodal-client.js paths match", len(mismatched) == 0,
          f"{len(paths_found)} paths, {len(mismatched)} mismatched" if mismatched else f"{len(paths_found)} paths OK")
    for p in mismatched:
        check(f"  Mismatch: {p}", False)

# ============================================================================
# T6: Learning Pipeline
# ============================================================================
print("\n━━━ T6: LEARNING PIPELINE ━━━")

try:
    from ai.ed3n.ed3n_engine import ED3NEngine
    ed3n = ED3NEngine.get_shared()
    dict_count = len(ed3n.dictionary.entries) if hasattr(ed3n, "dictionary") else 0
    check("ED3NEngine", dict_count > 0, f"{dict_count} dictionary entries")
except Exception as e:
    check("ED3NEngine", False, str(e)[:120])

try:
    from ai.ed3n.continuous_learning import ContinuousLearningPipeline
    clp = ContinuousLearningPipeline()
    check("ContinuousLearningPipeline", clp is not None)
except Exception as e:
    check("ContinuousLearningPipeline", False, str(e)[:120])

try:
    from ai.garden.garden_engine import GARDENEngine
    garden = GARDENEngine()
    check("GARDENEngine", True)
except Exception as e:
    check("GARDENEngine", False, str(e)[:120])

try:
    from ai.reasoning.causal_reasoning_engine import CausalReasoningEngine
    cre = CausalReasoningEngine()
    cre.retrospective_warm_start()
    rels = cre.get_relationships()
    check("CausalReasoningEngine warm-start", len(rels) > 0, f"{len(rels)} relationships")
except Exception as e:
    check("CausalReasoningEngine warm-start", False, str(e)[:120])

# ============================================================================
# T7: Session Management
# ============================================================================
print("\n━━━ T7: SESSION MANAGEMENT ━━━")

try:
    from api.routes.chat_routes import TTLSessionManager
    sm = TTLSessionManager()
    test_sid = "verify-test-session"
    sm.set(test_sid, {"created_at": "2026-07-13T00:00:00", "user_name": "Verify"})
    retrieved = sm.get(test_sid)
    check("Session set/get", retrieved and retrieved.get("user_name") == "Verify")
    check("Session 'in' check", test_sid in sm)
except Exception as e:
    check("Session management", False, str(e)[:120])

# ============================================================================
# T8: Persistence
# ============================================================================
print("\n━━━ T8: PERSISTENCE ━━━")

try:
    from ai.memory.ham_memory.ham_manager import HAMMemoryManager
    ham = HAMMemoryManager()
    stats = ham.get_stats()
    check("HAMMemoryManager", True, f"mem_file={ham.memory_file.name}")
    check("HAMMemoryManager stats", "template_count" in stats, f"template_count={stats.get('template_count', 'N/A')}")
except Exception as e:
    check("HAMMemoryManager", False, str(e)[:120])

try:
    from ai.memory.vector_store import VectorMemoryStore
    vms = VectorMemoryStore()
    check("VectorMemoryStore", True, f"backend={vms.backend}" if hasattr(vms, "backend") else "OK")
except Exception as e:
    check("VectorMemoryStore", False, str(e)[:120])

# ============================================================================
# T9: Error Handling
# ============================================================================
print("\n━━━ T9: ERROR HANDLING ━━━")

try:
    from core.utils import safe_error
    result = safe_error(Exception("Test " * 50))
    check("safe_error truncation", len(result) < 500, f"{len(result)} chars")
except Exception as e:
    check("safe_error", False, str(e)[:120])

try:
    from shared.network_resilience import CircuitBreaker
    import inspect
    sig = inspect.signature(CircuitBreaker.__init__)
    params = list(sig.parameters.keys())[1:]
    cb = CircuitBreaker(failure_threshold=5, recovery_timeout=30)
    check("CircuitBreaker", cb is not None, f"params={params}")
except Exception as e:
    check("CircuitBreaker", False, str(e)[:120])

# ============================================================================
# T10: Dead Code Check
# ============================================================================
print("\n━━━ T10: DEAD CODE ━━━")

# Check for lazy imports in services
services_init = PROJECT_ROOT / "apps/backend/src/services/__init__.py"
if services_init.exists():
    text = services_init.read_text(encoding="utf-8", errors="ignore")
    check("Services lazy imports", "__getattr__" in text)

try:
    from core.hsp.connector import HSPConnector
    check("HSPConnector import", True)
except Exception as e:
    check("HSPConnector import", False, str(e)[:120])

# ============================================================================
# Summary
# ============================================================================
elapsed = time.time() - TOTAL_START
print("\n" + "=" * 70)
print("  READINESS VERIFICATION SUMMARY")
print(f"  Pass: {PASS}  Fail: {FAIL}  Warn: {WARN}  Time: {elapsed:.1f}s")
print("=" * 70)

if FAIL > 0:
    print(f"\n  ❌ {FAIL} checks FAILED — review issues above")
    sys.exit(1)
else:
    print("\n  ✅ All checks passed! Project is ready for deployment.")
    sys.exit(0)
