#!/usr/bin/env bash
# =============================================================================
# ANGELA-MATRIX: [L0] [α] [C] [L0]
# =============================================================================
#
# verify_change_gate.sh — single command gate for every change in this repo.
#
# WHY: several defects in this project were invisible in review and only showed
# up as behaviour (a regression that removed the ModelBus refinement pipeline
# for "你是誰" passed every targeted test). This gate makes the same checks
# mandatory for every change instead of remembered:
#
#   1. dirty-tree snapshot   (what the change actually touches)
#   2. targeted tests        (caller passes paths; else the usual suspect set)
#   3. full suite            (tests/ + apps/backend/tests/)
#   4. mypy                  (whole src — the ratchet is 0 new errors)
#   5. flake8 on CHANGED py  (whole-repo flake8 has a known pre-existing F541)
#   6. project map budget    (structure must stay inside the 10k line budget)
#   7. dirty-tree comparison (nothing changed that the gate did not expect)
#
# Usage:
#   scripts/verify_change_gate.sh                 # full gate
#   scripts/verify_change_gate.sh --quick         # skip the full suite
#   scripts/verify_change_gate.sh --tests a.py b.py
#   scripts/verify_change_gate.sh --no-map        # skip the project map
#
# Exit code 0 = all gates green AND the change set is unchanged by verification.
# =============================================================================

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 2

PY=".venv/bin/python"
FLAKE8=".venv/bin/flake8"
MYPY=".venv/bin/mypy"
PYTEST=".venv/bin/pytest"

QUICK=0
RUN_MAP=1
TARGET_TESTS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --quick) QUICK=1 ;;
    --no-map) RUN_MAP=0 ;;
    --tests)
      shift
      while [ $# -gt 0 ] && [ "${1#-}" = "$1" ]; do
        TARGET_TESTS+=("$1")
        shift
      done
      ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

FAIL=0
note() { printf '\n=== %s ===\n' "$1"; }
fail() { printf 'FAIL: %s\n' "$1"; FAIL=1; }

# --- 1. dirty-tree snapshot -------------------------------------------------
note "1/7 dirty tree before verification"
git status --porcelain > /tmp/gate_tree_before.txt
printf 'dirty entries: %s\n' "$(wc -l < /tmp/gate_tree_before.txt)"
CHANGED_PY="$(git status --porcelain | awk '{print $NF}' | grep '\.py$' || true)"

# --- 2. targeted tests ------------------------------------------------------
note "2/7 targeted tests"
if [ "${#TARGET_TESTS[@]}" -gt 0 ]; then
  TESTS=("${TARGET_TESTS[@]}")
elif [ -n "$CHANGED_PY" ]; then
  # Map each changed source file to a same-named test file when one exists,
  # otherwise fall back to the suites that own the request path.
  TESTS=()
  for f in $CHANGED_PY; do
    case "$f" in
      tests/*) TESTS+=("$f") ;;
    esac
  done
  if [ "${#TESTS[@]}" -eq 0 ]; then
    TESTS=(tests/services tests/api tests/unit)
  fi
else
  TESTS=(tests/services tests/api tests/unit)
fi
printf 'running: %s\n' "${TESTS[*]}"
"$PYTEST" "${TESTS[@]}" -q -p no:cacheprovider || fail "targeted tests"

# --- 3. full suite ---------------------------------------------------------
if [ "$QUICK" -eq 1 ]; then
  note "3/7 full suite SKIPPED (--quick)"
else
  note "3/7 full suite (tests/ + apps/backend/tests/)"
  "$PYTEST" tests/ apps/backend/tests/ -q -p no:cacheprovider || fail "full suite"
fi

# --- 4. mypy ----------------------------------------------------------------
note "4/7 mypy apps/backend/src"
"$MYPY" apps/backend/src || fail "mypy"

# --- 5. flake8 on changed python only ---------------------------------------
note "5/7 flake8 on changed python"
if [ -n "$CHANGED_PY" ]; then
  # shellcheck disable=SC2086
  "$FLAKE8" $CHANGED_PY || fail "flake8 on changed files"
else
  echo "no changed python files"
fi

# --- 6. project map budget --------------------------------------------------
if [ "$RUN_MAP" -eq 1 ]; then
  note "6/7 project map budget"
  python3 scripts/gen_project_map.py --budget 10000 | tail -3 || fail "project map"
else
  note "6/7 project map SKIPPED (--no-map)"
fi

# --- 7. nothing changed underneath us --------------------------------------
note "7/7 change set after verification"
git status --porcelain > /tmp/gate_tree_after.txt
if diff -q /tmp/gate_tree_before.txt /tmp/gate_tree_after.txt >/dev/null; then
  echo "change set unchanged by verification (expected)"
else
  echo "diff before/after verification:" >&2
  diff /tmp/gate_tree_before.txt /tmp/gate_tree_after.txt >&2
  fail "verification mutated the working tree (unexpected files)"
fi

note "RESULT"
if [ "$FAIL" -eq 0 ]; then
  echo "GATE GREEN"
else
  echo "GATE RED — see FAIL lines above"
fi
exit "$FAIL"
