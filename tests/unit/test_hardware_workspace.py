"""三區工作區結構 + 打包規則鎖（hardware/README.md 打包規則 1-5）。

這些測試把「研究/元件/組件 × 完成/未完成」的邊界變成可執行紅線：
- 完成組件的打包清單只許引用 components/done/
- 複製進包的元件卡與來源逐位元一致
- wip 區不得出現 package_manifest、不得宣稱 complete
- done 元件卡必須真的 complete
- 三區 README 與 census 新檔必須存在（防重組後孤兒檔）
"""

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
HARDWARE = REPO / "hardware"
DONE_ASSY = HARDWARE / "assemblies/done/edge_card"
WIP_ASSY = HARDWARE / "assemblies/wip"
COMP_DONE = HARDWARE / "components/done"
COMP_WIP = HARDWARE / "components/wip"
RESEARCH = HARDWARE / "research"


class TestWorkspaceLayout:
    """三區目錄與 README 地圖在位。"""

    def test_three_zones_exist(self):
        assert (HARDWARE / "research").is_dir()
        assert (COMP_DONE).is_dir()
        assert (COMP_WIP).is_dir()
        assert (HARDWARE / "assemblies/done").is_dir()
        assert (WIP_ASSY).is_dir()

    def test_zone_readmes_exist(self):
        for rel in (
            "README.md",
            "research/README.md",
            "components/README.md",
            "assemblies/README.md",
        ):
            assert (HARDWARE / rel).is_file(), f"missing {rel}"

    def test_done_assembly_has_manifest_and_report(self):
        assert (DONE_ASSY / "package_manifest.yaml").is_file()
        assert (DONE_ASSY / "simulation_report.md").is_file()


class TestPackagingRules:
    """打包規則 1-3：done 自含、只引用 done、wip 禁打包。"""

    def _manifest(self):
        return yaml.safe_load((DONE_ASSY / "package_manifest.yaml").read_text(encoding="utf-8"))

    def test_manifest_sources_point_into_components_done(self):
        m = self._manifest()
        assert m["components"], "manifest must list components"
        for entry in m["components"]:
            src = entry["source"]
            assert src.startswith(
                "hardware/components/done/"
            ), f"packaged source not from components/done: {src}"
            assert "wip" not in src, f"wip component packaged: {src}"

    def test_manifest_not_packaged_lists_wip(self):
        m = self._manifest()
        not_packed = m["not_packaged"]
        assert not_packed, "should explicitly record wip components excluded"
        for item in not_packed:
            assert "wip" in item, f"non-wip in not_packaged: {item}"

    def test_wip_assemblies_have_no_manifest(self):
        assert not list(
            WIP_ASSY.rglob("package_manifest.yaml")
        ), "wip assembly must not ship a package_manifest"

    def test_copies_match_done_sources_byte_for_byte(self):
        m = self._manifest()
        for entry in m["components"]:
            src = REPO / entry["source"]
            dst = DONE_ASSY / entry["copy"]
            assert src.is_file(), f"source gone: {src}"
            assert dst.is_file(), f"copy gone: {dst}"
            assert src.read_bytes() == dst.read_bytes(), f"stale copy: {dst} differs from {src}"


class TestStatusDiscipline:
    """規則 4-5：status 欄位即真相，完成/未完成不得互稱。"""

    def test_done_component_cards_are_complete(self):
        cards = sorted(COMP_DONE.glob("*.yaml"))
        assert cards, "done component library empty"
        for card in cards:
            data = yaml.safe_load(card.read_text(encoding="utf-8"))
            assert data["status"] == "complete", f"{card.name} in done/ but status={data['status']}"

    def test_wip_component_cards_never_complete(self):
        for card in sorted(COMP_WIP.rglob("*.yaml")):
            data = yaml.safe_load(card.read_text(encoding="utf-8"))
            assert data["status"] != "complete", f"{card.name} in wip/ but claims complete"

    def test_wip_assembly_task_status_not_complete(self):
        for doc in sorted(WIP_ASSY.rglob("*.yaml")):
            data = yaml.safe_load(doc.read_text(encoding="utf-8"))
            status = data.get("status", "")
            assert "complete" not in str(
                status
            ), f"{doc.relative_to(REPO)} in wip/ but status={status}"


class TestCensusIntegrity:
    """重組不破 census：被鎖檔案在位、README 不入掃描根、新檔有引用者。"""

    KNOWN = {
        "ai_compute_card_task",
        "component_registry",
        "concept_design",
        "secondary_compute_draft",
        "mvu_reference_spec",
        "DERIVED_ESTIMATES",
    }

    def test_known_files_still_exist_after_move(self):
        candidates = list(HARDWARE.rglob("*"))
        names = {p.stem for p in candidates if p.is_file()}
        for stem in self.KNOWN:
            assert stem in names, f"census-known file lost: {stem}"

    def test_new_stems_referenced_somewhere(self):
        """新加入掃描範圍的檔名必須在 repo 程式/測試/規格裡被字面提到。"""
        new_stems = {
            "compute_module_orin_nx",
            "m2_2230_module_class",
            "cooling_fan_40mm",
            "m2_ssd_part_selection",
            "package_manifest",
            "simulation_report",
        }
        scan_roots = [
            REPO / "tests",
            REPO / "scripts",
            REPO / "apps/backend/src",
            REPO / "hardware",
        ]
        corpus = []
        for root in scan_roots:
            for pat in ("*.py", "*.yaml", "*.md"):
                corpus.extend(
                    p.read_text(encoding="utf-8", errors="ignore") for p in root.rglob(pat)
                )
        joined = "\n".join(corpus)
        for stem in new_stems:
            assert stem in joined, f"orphan stem (not referenced anywhere): {stem}"
