"""
ANGELA-MATRIX: [L0] [α] [C] [L0]
The script inventory must be complete and current.

The gap-closure plan listed "69 孤兒腳本逐個定級（留/刪/歸檔）" as open
work. The inventory (``scripts/INVENTORY.json``) is the triage record: every
script gets a category and a purpose, and ``referenced=false`` marks the
research one-offs that nothing points at.

These tests keep it honest: a new script cannot appear without being
triaged, and a stale entry fails.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "scripts" / "INVENTORY.json"
GENERATOR = ROOT / "scripts" / "gen_script_inventory.py"

VALID_CATEGORIES = {
    "analysis",
    "benchmark",
    "diagnostics",
    "experimental",
    "generation",
    "maintenance",
    "operations",
    "probe",
    "testing",
    "tool",
    "training",
    "validation",
    "verification",
}


def _load() -> dict:
    assert INVENTORY.exists(), f"{INVENTORY} is missing"
    data = json.loads(INVENTORY.read_text(encoding="utf-8"))
    return data["scripts"]


class TestScriptInventory:
    def test_every_script_is_triaged(self):
        inventory = _load()
        on_disk = {p.name for p in (ROOT / "scripts").glob("*.py")}
        on_disk.discard(GENERATOR.name)
        missing = sorted(on_disk - set(inventory))
        assert not missing, f"scripts not in the inventory: {missing}"

    def test_no_stale_entries(self):
        inventory = _load()
        on_disk = {p.name for p in (ROOT / "scripts").glob("*.py")}
        on_disk.discard(GENERATOR.name)
        extra = sorted(set(inventory) - on_disk)
        assert not extra, f"the inventory lists scripts that no longer exist: {extra}"

    def test_every_entry_has_a_category_and_a_purpose(self):
        for name, entry in _load().items():
            assert entry["category"] in VALID_CATEGORIES, f"{name}: {entry['category']}"
            assert entry["purpose"].strip(), f"{name} has no purpose"

    def test_the_inventory_is_current(self):
        """The committed inventory must match what the generator produces."""
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--check"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        assert result.returncode == 0, f"the inventory is stale:\n{result.stdout}{result.stderr}"

    def test_the_unreferenced_ones_are_explicitly_marked(self):
        """A script nobody points at must say so, not hide."""
        inventory = _load()
        unreferenced = [n for n, e in inventory.items() if not e["referenced"]]
        assert unreferenced, "the guard would be vacuous if every script were referenced"
        for name in unreferenced:
            assert inventory[name]["category"] in VALID_CATEGORIES
