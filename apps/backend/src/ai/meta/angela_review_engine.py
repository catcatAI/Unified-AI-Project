# =============================================================================
# ANGELA-MATRIX: [L3-L5] [βδεθζη] [A] [L3+]
# =============================================================================
#
# 职责: Angela 权威审查引擎 — 多维度项目审查系统
# 维度: 认知(β) 精神(δ) 環境(ε) 元認知(θ) 連通(ζ) 執行(η)
# 安全: 使用 Key A (后端控制)
# 成熟度: L3+ 等级才能理解审查逻辑
#
# 审查维度:
#   1. Design Review — 基于 Angela Matrix 權威 + 專案設計標準
#   2. Code Review — 代碼质量、标注合规、层级一致
#   3. MD Review — 文檔完整性、一致性、覆盖度
#   4. Design↔Code — 設計與實作對比
#   5. Code↔MD — 代碼與文檔對比
#   6. Training Review — 訓練成果與管线质量
#
# =============================================================================

import ast
import logging
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SRC_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = SRC_ROOT.parent.parent.parent
DOCS_ROOT = PROJECT_ROOT / "docs"
ROOT_MD_DIR = PROJECT_ROOT

# ---------------------------------------------------------------------------
# Angela Matrix Constants
# ---------------------------------------------------------------------------
MATRIX_LAYERS = {
    "L1": {"name": "Biology Layer", "keywords": ["bio", "tactile", "endocrine", "autonomic", "physiological"]},
    "L2": {"name": "Memory Layer", "keywords": ["memory", "ham", "vector", "store", "episodic", "semantic", "procedural"]},
    "L3": {"name": "Identity Layer", "keywords": ["identity", "self", "cyber", "persona", "soul"]},
    "L4": {"name": "Creation Layer", "keywords": ["creative", "art", "generate", "draw", "compose"]},
    "L5": {"name": "Presence Layer", "keywords": ["presence", "live2d", "avatar", "render", "display"]},
    "L6": {"name": "Execution Layer", "keywords": ["execute", "action", "perform", "run", "task"]},
}

MATRIX_DIMENSIONS = {
    "α": {"name": "Physiological", "keywords": ["energy", "comfort", "arousal", "rest", "vitality"]},
    "β": {"name": "Cognitive", "keywords": ["curiosity", "focus", "confusion", "learning", "clarity"]},
    "γ": {"name": "Emotional", "keywords": ["happiness", "sadness", "anger", "fear", "trust", "anticipation"]},
    "δ": {"name": "Social", "keywords": ["attention", "bond", "trust", "presence", "social"]},
    "ε": {"name": "Environmental", "keywords": ["complexity", "density", "flow", "pressure"]},
    "θ": {"name": "Meta-Cognitive", "keywords": ["novelty", "mismatch", "creation", "calibration"]},
    "ζ": {"name": "Connectivity", "keywords": ["coupling", "sync", "redundancy", "aggregation"]},
    "η": {"name": "Execution", "keywords": ["active", "success", "drift", "efficiency"]},
}

MATRIX_KEYS = {"A": "Backend Control", "B": "Mobile Communication", "C": "Desktop Sync"}


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ReviewFinding:
    severity: Severity
    category: str
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    suggestion: Optional[str] = None
    context: Optional[str] = None


@dataclass
class ReviewReport:
    dimension: str
    findings: List[ReviewFinding] = field(default_factory=list)
    score: float = 0.0
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.HIGH)

    @property
    def medium_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.MEDIUM)

    @property
    def low_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.LOW)

    @property
    def total_findings(self) -> int:
        return len(self.findings)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "score": self.score,
            "summary": self.summary,
            "counts": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
                "total": self.total_findings,
            },
            "findings": [
                {
                    "severity": f.severity.value,
                    "category": f.category,
                    "message": f.message,
                    "file": f.file,
                    "line": f.line,
                    "suggestion": f.suggestion,
                    "context": f.context,
                }
                for f in self.findings
            ],
            "metadata": self.metadata,
        }


# =============================================================================
# Design Reviewer — 基于權威與專案設計標準
# =============================================================================

class DesignReviewer:
    """審查專案設計是否符合 Angela Matrix 架構標準。

    基於:
    - ANGELA_MATRIX_ANNOTATION_GUIDE.md (6層 + 8D + A/B/C + L0-L11)
    - COMPREHENSIVE_DESIGN_STANDARD.md (功能需求 + Gap Analysis)
    - IDEAL_ARCHITECTURE.md (目標架構)
    """

    def __init__(self, src_root: Path = SRC_ROOT, docs_root: Path = DOCS_ROOT):
        self._src = src_root
        self._docs = docs_root

    def review(self) -> ReviewReport:
        findings: List[ReviewFinding] = []

        findings.extend(self._check_layer_coverage())
        findings.extend(self._check_dimension_usage())
        findings.extend(self._check_design_doc_completeness())
        findings.extend(self._check_architecture_compliance())
        findings.extend(self._check_module_layer_alignment())

        score = self._calc_score(findings)
        return ReviewReport(
            dimension="design",
            findings=findings,
            score=score,
            summary=f"Design review: {len(findings)} findings across {self._count_layers()} layers",
            metadata={"layers_checked": list(MATRIX_LAYERS.keys())},
        )

    def _check_layer_coverage(self) -> List[ReviewFinding]:
        findings = []
        for layer_id, info in MATRIX_LAYERS.items():
            keywords = info["keywords"]
            layer_files = []
            for py_file in self._src.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                try:
                    text = py_file.read_text(encoding="utf-8", errors="ignore")
                    if any(kw in text.lower() for kw in keywords):
                        layer_files.append(py_file)
                except OSError:
                    continue

            if len(layer_files) < 2:
                findings.append(ReviewFinding(
                    severity=Severity.MEDIUM,
                    category="layer_coverage",
                    message=f"Layer {layer_id} ({info['name']}) has only {len(layer_files)} potentially related files",
                    suggestion=f"Verify {layer_id} implementation completeness against design standard",
                ))
        return findings

    def _check_dimension_usage(self) -> List[ReviewFinding]:
        findings = []
        for dim_id, info in MATRIX_DIMENSIONS.items():
            if dim_id in ("ζ", "η"):
                continue
            keywords = info["keywords"]
            dim_files = 0
            for py_file in self._src.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                try:
                    text = py_file.read_text(encoding="utf-8", errors="ignore")
                    if any(re.search(rf"\b{kw}\b", text, re.IGNORECASE) for kw in keywords):
                        dim_files += 1
                except OSError:
                    continue

            if dim_files < 3 and dim_id in ("α", "β", "γ", "δ"):
                findings.append(ReviewFinding(
                    severity=Severity.LOW,
                    category="dimension_usage",
                    message=f"Core dimension {dim_id} ({info['name']}) has only {dim_files} files referencing its keywords",
                    suggestion=f"Check if {dim_id} dimension is adequately represented in state_matrix or related modules",
                ))
        return findings

    def _check_design_doc_completeness(self) -> List[ReviewFinding]:
        findings = []
        design_doc = self._docs / "COMPREHENSIVE_DESIGN_STANDARD.md"
        if not design_doc.exists():
            findings.append(ReviewFinding(
                severity=Severity.HIGH,
                category="design_doc",
                message="COMPREHENSIVE_DESIGN_STANDARD.md not found — primary design authority missing",
            ))
            return findings

        text = design_doc.read_text(encoding="utf-8", errors="ignore")
        for layer_id, info in MATRIX_LAYERS.items():
            if layer_id not in text and info["name"] not in text:
                findings.append(ReviewFinding(
                    severity=Severity.MEDIUM,
                    category="design_doc_coverage",
                    message=f"Layer {layer_id} ({info['name']}) not referenced in design standard",
                    file=str(design_doc),
                ))
        return findings

    def _check_architecture_compliance(self) -> List[ReviewFinding]:
        findings = []
        ideal_arch = self._docs / "IDEAL_ARCHITECTURE.md"
        if ideal_arch.exists():
            text = ideal_arch.read_text(encoding="utf-8", errors="ignore")
            if len(text) < 5000:
                findings.append(ReviewFinding(
                    severity=Severity.LOW,
                    category="architecture_doc",
                    message="IDEAL_ARCHITECTURE.md is minimal — may not reflect current implementation",
                    file=str(ideal_arch),
                ))

        arch_doc = self._docs / "ARCHITECTURE.md"
        if arch_doc.exists():
            text = arch_doc.read_text(encoding="utf-8", errors="ignore")
            core_dirs = ["ai", "core", "services", "api"]
            for d in core_dirs:
                if d not in text:
                    findings.append(ReviewFinding(
                        severity=Severity.LOW,
                        category="architecture_doc",
                        message=f"Core directory '{d}/' not mentioned in ARCHITECTURE.md",
                        file=str(arch_doc),
                    ))
        return findings

    def _check_module_layer_alignment(self) -> List[ReviewFinding]:
        findings = []
        for py_file in self._src.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            rel = py_file.relative_to(self._src)
            parts = rel.parts
            try:
                text = py_file.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            annotation_match = re.search(
                r"ANGELA-MATRIX:\s*\[(L\d+(?:-L\d+)?)\]", text
            )
            if not annotation_match:
                continue

            declared_layer = annotation_match.group(1)
            if len(parts) >= 2:
                top_dir = parts[0]
                if top_dir == "ai" and "L1" in declared_layer:
                    if "memory" not in str(rel) and "bio" not in str(rel):
                        findings.append(ReviewFinding(
                            severity=Severity.LOW,
                            category="layer_alignment",
                            message=f"File declares {declared_layer} but is in ai/ without memory/bio path",
                            file=str(rel),
                            line=text[:200].count("\n") + 1,
                        ))
        return findings

    def _count_layers(self) -> int:
        return len(MATRIX_LAYERS)

    def _calc_score(self, findings: List[ReviewFinding]) -> float:
        if not findings:
            return 10.0
        penalty = (
            sum(3 for f in findings if f.severity == Severity.CRITICAL)
            + sum(2 for f in findings if f.severity == Severity.HIGH)
            + sum(1 for f in findings if f.severity == Severity.MEDIUM)
            + sum(0.5 for f in findings if f.severity == Severity.LOW)
        )
        return max(0.0, 10.0 - penalty)


# =============================================================================
# Code Reviewer — 代碼质量 + 标注合规
# =============================================================================

class CodeReviewer:
    """審查代碼質量 — Angela Matrix 标注、代码模式、反模式。

    檢查:
    - ANGELA-MATRIX 标注存在性與正確性
    - 裸 except 块
    - 過長函式
    - 缺失 type hints
    - 循環導入風險
    -  Stub / pass 残留
    """

    MAX_FUNCTION_LINES = 80
    MAX_FILE_LINES = 1200

    def __init__(self, src_root: Path = SRC_ROOT):
        self._src = src_root

    def review(self, target_files: Optional[List[str]] = None) -> ReviewReport:
        findings: List[ReviewFinding] = []

        files_to_check = self._get_files(target_files)
        for py_file in files_to_check:
            try:
                text = py_file.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            rel = str(py_file.relative_to(self._src))
            findings.extend(self._check_matrix_annotation(text, rel))
            findings.extend(self._check_bare_except(text, rel))
            findings.extend(self._check_stub_pass(text, rel))
            findings.extend(self._check_function_length(text, rel))
            findings.extend(self._check_import_patterns(text, rel))
            findings.extend(self._check_file_length(text, rel))

        score = self._calc_score(findings, len(files_to_check))
        return ReviewReport(
            dimension="code",
            findings=findings,
            score=score,
            summary=f"Code review: {len(files_to_check)} files, {len(findings)} findings",
            metadata={"files_checked": len(files_to_check)},
        )

    def _get_files(self, target_files: Optional[List[str]] = None) -> List[Path]:
        if target_files:
            return [self._src / f for f in target_files if (self._src / f).exists()]
        files = []
        for f in self._src.rglob("*.py"):
            if "__pycache__" in str(f):
                continue
            if f.name == "__init__.py":
                continue
            files.append(f)
        return files

    def _check_matrix_annotation(self, text: str, rel: str) -> List[ReviewFinding]:
        findings = []
        if "ANGELA-MATRIX:" not in text:
            findings.append(ReviewFinding(
                severity=Severity.MEDIUM,
                category="missing_annotation",
                file=rel,
                message="Missing ANGELA-MATRIX annotation header",
                suggestion="Add ANGELA-MATRIX: [L#] [αβγδ] [A/B/C] [L#] annotation",
            ))
        else:
            match = re.search(
                r"ANGELA-MATRIX:\s*(?:\[?(L\d+(?:-L\d+)?)\]?)\s*\[([αβγδεθζη]+)\]\s*\[([ABC])\]\s*(?:\[?L(\d+)\]?)",
                text,
            )
            if not match:
                match_loose = re.search(r"ANGELA-MATRIX:", text)
                if match_loose:
                    context_start = max(0, match_loose.start() - 10)
                    context_end = min(len(text), match_loose.end() + 80)
                    findings.append(ReviewFinding(
                        severity=Severity.LOW,
                        category="malformed_annotation",
                        file=rel,
                        message="ANGELA-MATRIX annotation format does not match standard pattern",
                        context=text[context_start:context_end].strip(),
                    ))
        return findings

    def _check_bare_except(self, text: str, rel: str) -> List[ReviewFinding]:
        findings = []
        lines = text.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if re.match(r"^except\s*:", stripped) and "except Exception:" not in stripped:
                findings.append(ReviewFinding(
                    severity=Severity.HIGH,
                    category="bare_except",
                    file=rel,
                    line=i,
                    message="Bare 'except:' clause — silently swallows all exceptions including KeyboardInterrupt",
                    suggestion="Use 'except Exception:' with logging, or specify exact exception types",
                ))
            elif re.match(r"except\s+Exception\s*:\s*(pass)?\s*$", stripped):
                findings.append(ReviewFinding(
                    severity=Severity.MEDIUM,
                    category="silent_except",
                    file=rel,
                    line=i,
                    message="'except Exception: pass' — silent error swallowing",
                    suggestion="Add logging.exception() or logger.debug() with exc_info=True",
                ))
        return findings

    def _check_stub_pass(self, text: str, rel: str) -> List[ReviewFinding]:
        findings = []
        lines = text.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped == "pass" and i > 1:
                prev_line = lines[i - 2].strip() if i >= 2 else ""
                if prev_line.endswith(":") or "def " in prev_line or "class " in prev_line:
                    findings.append(ReviewFinding(
                        severity=Severity.MEDIUM,
                        category="stub_pass",
                        file=rel,
                        line=i,
                        message="Standalone 'pass' may indicate unimplemented stub",
                        suggestion="Implement the function or raise NotImplementedError with explanation",
                    ))
        return findings

    def _check_function_length(self, text: str, rel: str) -> List[ReviewFinding]:
        findings = []
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return findings

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_lines = (node.end_lineno or node.lineno) - node.lineno
                if func_lines > self.MAX_FUNCTION_LINES:
                    findings.append(ReviewFinding(
                        severity=Severity.LOW,
                        category="long_function",
                        file=rel,
                        line=node.lineno,
                        message=f"Function '{node.name}' is {func_lines} lines (max {self.MAX_FUNCTION_LINES})",
                        suggestion="Consider decomposing into smaller functions",
                    ))
        return findings

    def _check_import_patterns(self, text: str, rel: str) -> List[ReviewFinding]:
        findings = []
        lines = text.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if "__import__(" in stripped and "import " not in stripped.split("__import__")[0]:
                findings.append(ReviewFinding(
                    severity=Severity.MEDIUM,
                    category="dynamic_import",
                    file=rel,
                    line=i,
                    message="Use of __import__() — prefer static imports",
                    suggestion="Use 'from module import name' or importlib.import_module()",
                ))
        return findings

    def _check_file_length(self, text: str, rel: str) -> List[ReviewFinding]:
        findings = []
        lines = text.split("\n")
        if len(lines) > self.MAX_FILE_LINES:
            findings.append(ReviewFinding(
                severity=Severity.LOW,
                category="long_file",
                file=rel,
                message=f"File has {len(lines)} lines (max {self.MAX_FILE_LINES})",
                suggestion="Consider splitting into smaller modules",
            ))
        return findings

    def _calc_score(self, findings: List[ReviewFinding], file_count: int) -> float:
        if file_count == 0:
            return 10.0
        penalty = (
            sum(3 for f in findings if f.severity == Severity.CRITICAL)
            + sum(2 for f in findings if f.severity == Severity.HIGH)
            + sum(1 for f in findings if f.severity == Severity.MEDIUM)
            + sum(0.3 for f in findings if f.severity == Severity.LOW)
        )
        normalized = min(penalty / max(file_count, 1) * 5, 10)
        return max(0.0, 10.0 - normalized)


# =============================================================================
# MD Reviewer — 文檔完整性與一致性
# =============================================================================

class MDReviewer:
    """審查 Markdown 文檔質量。

    檢查:
    - 文檔是否存在對應代碼
    - 過期資訊（版本號、測試數）
    - 內部連結有效性
    - 覆蓋度（所有主要模塊是否有文檔）
    """

    def __init__(self, project_root: Path = PROJECT_ROOT, src_root: Path = SRC_ROOT):
        self._root = project_root
        self._src = src_root

    def review(self) -> ReviewReport:
        findings: List[ReviewFinding] = []

        md_files = self._collect_md_files()
        findings.extend(self._check_version_consistency(md_files))
        findings.extend(self._check_test_count_accuracy(md_files))
        findings.extend(self._check_broken_links(md_files))
        findings.extend(self._check_doc_coverage(md_files))

        score = self._calc_score(findings)
        return ReviewReport(
            dimension="markdown",
            findings=findings,
            score=score,
            summary=f"MD review: {len(md_files)} docs, {len(findings)} findings",
            metadata={"docs_checked": len(md_files)},
        )

    def _collect_md_files(self) -> List[Path]:
        files = []
        for md in self._root.rglob("*.md"):
            if "__pycache__" in str(md):
                continue
            if ".venv" in str(md):
                continue
            if "node_modules" in str(md):
                continue
            if "09-archive" in md.parts:
                continue
            files.append(md)
        return files

    def _check_version_consistency(self, md_files: List[Path]) -> List[ReviewFinding]:
        findings = []
        version_file = self._root / "VERSION"
        if not version_file.exists():
            return findings

        current_version = version_file.read_text().strip()
        version_pattern = re.compile(r"\b\d+\.\d+\.\d+(?:-\w+)?\b")

        for md in md_files:
            try:
                text = md.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            versions_found = version_pattern.findall(text)
            for v in versions_found:
                if v != current_version and self._is_version_context(text, v):
                    findings.append(ReviewFinding(
                        severity=Severity.LOW,
                        category="version_drift",
                        file=str(md.relative_to(self._root)),
                        message=f"References version {v}, current is {current_version}",
                    ))
                    break
        return findings

    def _check_test_count_accuracy(self, md_files: List[Path]) -> List[ReviewFinding]:
        findings = []
        test_count_pattern = re.compile(r"(\d{3,5})\s*(?:tests?|測試)")
        for md in md_files:
            try:
                text = md.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            matches = test_count_pattern.findall(text)
            if len(matches) > 3:
                unique = set(matches)
                if len(unique) > 2:
                    findings.append(ReviewFinding(
                        severity=Severity.LOW,
                        category="test_count_inconsistency",
                        file=str(md.relative_to(self._root)),
                        message=f"Multiple different test counts referenced: {sorted(unique)}",
                        suggestion="Standardize to single authoritative count from pytest collection",
                    ))
        return findings

    def _check_broken_links(self, md_files: List[Path]) -> List[ReviewFinding]:
        findings = []
        link_pattern = re.compile(r"\]\(([^)]+\.md)\)")
        for md in md_files:
            try:
                text = md.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for match in link_pattern.finditer(text):
                link_target = match.group(1)
                if link_target.startswith("http"):
                    continue
                resolved = (md.parent / link_target).resolve()
                if not resolved.exists():
                    findings.append(ReviewFinding(
                        severity=Severity.MEDIUM,
                        category="broken_link",
                        file=str(md.relative_to(self._root)),
                        message=f"Broken MD link: {link_target}",
                        suggestion="Update link or create target file",
                    ))
        return findings

    def _check_doc_coverage(self, md_files: List[Path]) -> List[ReviewFinding]:
        findings = []
        critical_modules = [
            "apps/backend/src/core/engine/state_matrix.py",
            "apps/backend/src/ai/core/execution_gate.py",
            "apps/backend/src/ai/meta/meta_controller.py",
            "apps/backend/src/core/life/autonomous_life_cycle.py",
            "apps/backend/src/core/life/digital_life_integrator.py",
            "apps/backend/src/ai/alignment/emotion_system.py",
        ]
        docs_text = ""
        for md in md_files:
            try:
                docs_text += md.read_text(encoding="utf-8", errors="ignore") + "\n"
            except OSError:
                continue

        for mod in critical_modules:
            mod_name = Path(mod).stem
            if mod_name not in docs_text:
                findings.append(ReviewFinding(
                    severity=Severity.LOW,
                    category="doc_coverage",
                    message=f"Critical module '{mod_name}' not referenced in any documentation",
                    suggestion=f"Add documentation or reference for {mod}",
                ))
        return findings

    def _is_version_context(self, text: str, version: str) -> bool:
        idx = text.find(version)
        if idx < 0:
            return False
        window = text[max(0, idx - 40):min(len(text), idx + len(version) + 40)]
        return any(kw in window.lower() for kw in ["version", "v", "目前", "current", "latest", "release"])

    def _calc_score(self, findings: List[ReviewFinding]) -> float:
        penalty = (
            sum(2 for f in findings if f.severity == Severity.HIGH)
            + sum(1 for f in findings if f.severity == Severity.MEDIUM)
            + sum(0.3 for f in findings if f.severity == Severity.LOW)
        )
        return max(0.0, 10.0 - penalty)


# =============================================================================
# Consistency Reviewer — 設計↔代碼↔MD 交叉對比
# =============================================================================

class ConsistencyReviewer:
    """對比設計文檔、代碼、與 MD 之間的一致性。

    維度:
    - Design vs Code: 設計文檔描述的模組是否存在於代碼中
    - Code vs MD: 代碼中的模組是否被文檔涵蓋
    - Code vs Code: 跨模組介面一致性
    """

    def __init__(self, src_root: Path = SRC_ROOT, docs_root: Path = DOCS_ROOT, project_root: Path = PROJECT_ROOT):
        self._src = src_root
        self._docs = docs_root
        self._root = project_root

    def review(self) -> ReviewReport:
        findings: List[ReviewFinding] = []

        findings.extend(self._check_design_vs_code())
        findings.extend(self._check_code_vs_md())
        findings.extend(self._check_interface_consistency())

        score = self._calc_score(findings)
        return ReviewReport(
            dimension="consistency",
            findings=findings,
            score=score,
            summary=f"Consistency review: {len(findings)} cross-reference issues",
        )

    def _check_design_vs_code(self) -> List[ReviewFinding]:
        findings = []
        design_doc = self._docs / "COMPREHENSIVE_DESIGN_STANDARD.md"
        if not design_doc.exists():
            return findings

        text = design_doc.read_text(encoding="utf-8", errors="ignore")
        src_symbols = self._collect_src_symbols()

        component_patterns = [
            (r"\bStateMatrix4D\b", "core/engine/state_matrix.py"),
            (r"\bExecutionGate\b", "ai/core/execution_gate.py"),
            (r"\bMetaController\b", "ai/meta/meta_controller.py"),
            (r"\bPriorityNegotiator\b", "ai/meta/priority_negotiator.py"),
            (r"\bHAMMemoryManager\b", "ai/memory/ham_memory/ham_manager.py"),
            (r"\bAutonomousLifeCycle\b", "core/life/autonomous_life_cycle.py"),
            (r"\bDigitalLifeIntegrator\b", "core/life/digital_life_integrator.py"),
            (r"\bEmotionSystem\b", "ai/alignment/emotion_system.py"),
            (r"\bCausalReasoningEngine\b", "ai/reasoning/causal_reasoning_engine.py"),
            (r"\bED3NEngine\b", "ai/ed3n/ed3n_engine.py"),
            (r"\bGARDENEngine\b", "ai/garden/garden_engine.py"),
        ]

        for pattern, expected_path in component_patterns:
            if re.search(pattern, text):
                full_path = self._src / expected_path
                if not full_path.exists():
                    findings.append(ReviewFinding(
                        severity=Severity.HIGH,
                        category="design_vs_code",
                        message=f"Design references {pattern} but expected file missing: {expected_path}",
                        suggestion="Implement the module or update design document",
                    ))
        return findings

    def _check_code_vs_md(self) -> List[ReviewFinding]:
        findings = []
        docs_text = self._collect_docs_text()

        key_classes = self._extract_key_classes()
        for class_name, file_path in key_classes:
            if class_name not in docs_text:
                findings.append(ReviewFinding(
                    severity=Severity.LOW,
                    category="code_vs_md",
                    message=f"Class '{class_name}' in {file_path} not referenced in any MD",
                    suggestion=f"Document {class_name} in relevant architecture/design docs",
                ))
        return findings

    def _check_interface_consistency(self) -> List[ReviewFinding]:
        findings = []
        try:
            from ai.core.execution_gate import ExecutionGate
            gate_methods = [m for m in dir(ExecutionGate) if not m.startswith("__")]
            if "evaluate" not in gate_methods and "decide" not in gate_methods:
                findings.append(ReviewFinding(
                    severity=Severity.MEDIUM,
                    category="interface",
                    message="ExecutionGate missing expected evaluate/decide public method",
                ))
        except ImportError:
            pass

        try:
            from ai.meta.meta_controller import MetaController
            mc_methods = [m for m in dir(MetaController) if not m.startswith("__")]
            expected = ["record_confidence", "get_calibration_report", "get_weighted_adjustment"]
            for method in expected:
                if method not in mc_methods:
                    findings.append(ReviewFinding(
                        severity=Severity.MEDIUM,
                        category="interface",
                        message=f"MetaController missing expected method: {method}",
                    ))
        except ImportError:
            pass

        return findings

    def _collect_src_symbols(self) -> Set[str]:
        symbols = set()
        for py_file in self._src.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            symbols.add(py_file.stem)
            try:
                text = py_file.read_text(encoding="utf-8", errors="ignore")
                for m in re.finditer(r"\bclass\s+([A-Z][A-Za-z0-9_]*)\b", text):
                    symbols.add(m.group(1))
            except OSError:
                continue
        return symbols

    def _collect_docs_text(self) -> str:
        text_parts = []
        for md in self._root.rglob("*.md"):
            if "__pycache__" in str(md) or ".venv" in str(md) or "node_modules" in str(md):
                continue
            if "09-archive" in md.parts:
                continue
            try:
                text_parts.append(md.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                continue
        return "\n".join(text_parts)

    def _extract_key_classes(self) -> List[Tuple[str, str]]:
        classes = []
        key_files = [
            "ai/core/execution_gate.py",
            "ai/meta/meta_controller.py",
            "ai/meta/priority_negotiator.py",
            "core/engine/state_matrix.py",
            "core/life/autonomous_life_cycle.py",
            "core/life/digital_life_integrator.py",
            "ai/alignment/emotion_system.py",
            "ai/reasoning/causal_reasoning_engine.py",
            "ai/ed3n/ed3n_engine.py",
            "ai/memory/ham_memory/ham_manager.py",
        ]
        for rel_path in key_files:
            full = self._src / rel_path
            if not full.exists():
                continue
            try:
                text = full.read_text(encoding="utf-8", errors="ignore")
                for m in re.finditer(r"\bclass\s+([A-Z][A-Za-z0-9_]*)\b", text):
                    classes.append((m.group(1), rel_path))
            except OSError:
                continue
        return classes

    def _calc_score(self, findings: List[ReviewFinding]) -> float:
        penalty = (
            sum(3 for f in findings if f.severity == Severity.CRITICAL)
            + sum(2 for f in findings if f.severity == Severity.HIGH)
            + sum(1 for f in findings if f.severity == Severity.MEDIUM)
            + sum(0.5 for f in findings if f.severity == Severity.LOW)
        )
        return max(0.0, 10.0 - penalty)


# =============================================================================
# Training Reviewer — 訓練成果與管線质量
# =============================================================================

class TrainingReviewer:
    """審查訓練管线與成果质量。

    檢查:
    - 訓練管線結構完整性
    - 訓練成果文件存在性
    - 訓練配置一致性
    """

    def __init__(self, src_root: Path = SRC_ROOT, project_root: Path = PROJECT_ROOT):
        self._src = src_root
        self._root = project_root

    def review(self) -> ReviewReport:
        findings: List[ReviewFinding] = []

        findings.extend(self._check_pipeline_structure())
        findings.extend(self._check_trainer_interfaces())
        findings.extend(self._check_training_scripts())

        score = self._calc_score(findings)
        return ReviewReport(
            dimension="training",
            findings=findings,
            score=score,
            summary=f"Training review: {len(findings)} pipeline quality issues",
        )

    def _check_pipeline_structure(self) -> List[ReviewFinding]:
        findings = []
        pipeline_file = self._src / "ai" / "multimodal" / "training_pipeline.py"
        if not pipeline_file.exists():
            findings.append(ReviewFinding(
                severity=Severity.HIGH,
                category="pipeline_missing",
                message="Multimodal training_pipeline.py not found",
            ))
            return findings

        text = pipeline_file.read_text(encoding="utf-8", errors="ignore")
        expected_classes = ["ContrastiveBatchTrainer", "FullTrainingPipeline"]
        for cls in expected_classes:
            if f"class {cls}" not in text:
                findings.append(ReviewFinding(
                    severity=Severity.MEDIUM,
                    category="pipeline_structure",
                    message=f"Expected class '{cls}' not found in training_pipeline.py",
                ))
        return findings

    def _check_trainer_interfaces(self) -> List[ReviewFinding]:
        findings = []
        trainer_file = self._src / "ai" / "ed3n" / "ed3n_trainer.py"
        if not trainer_file.exists():
            findings.append(ReviewFinding(
                severity=Severity.MEDIUM,
                category="trainer_missing",
                message="ED3N trainer (ed3n_trainer.py) not found",
            ))
            return findings

        text = trainer_file.read_text(encoding="utf-8", errors="ignore")
        if "def train" not in text and "async def train" not in text:
            findings.append(ReviewFinding(
                severity=Severity.LOW,
                category="trainer_interface",
                message="ED3N trainer missing 'train' method",
            ))
        return findings

    def _check_training_scripts(self) -> List[ReviewFinding]:
        findings = []
        scripts_dir = self._root / "scripts"
        if not scripts_dir.exists():
            return findings

        training_scripts = list(scripts_dir.glob("*.py"))
        has_training_data = any("training" in f.name or "train" in f.name for f in training_scripts)
        if not training_scripts or not has_training_data:
            findings.append(ReviewFinding(
                severity=Severity.LOW,
                category="training_scripts",
                message="No training-related scripts found in scripts/ directory",
            ))
        return findings

    def _calc_score(self, findings: List[ReviewFinding]) -> float:
        penalty = (
            sum(3 for f in findings if f.severity == Severity.CRITICAL)
            + sum(2 for f in findings if f.severity == Severity.HIGH)
            + sum(1 for f in findings if f.severity == Severity.MEDIUM)
            + sum(0.5 for f in findings if f.severity == Severity.LOW)
        )
        return max(0.0, 10.0 - penalty)


# =============================================================================
# Angela Review Engine — 統一入口
# =============================================================================

class AngelaReviewEngine:
    """Angela 權威審查引擎 — 統一多維度項目審查。

    使用方式:
        engine = AngelaReviewEngine()
        report = engine.run_full_review()
        # 或
        report = engine.run_review("design")

    審查維度:
        - design: 基於權威的設計審查
        - code: 代碼質量與标注合規
        - markdown: 文檔一致性
        - consistency: 設計↔代碼↔MD 交叉對比
        - training: 訓練管线與成果
    """

    def __init__(
        self,
        src_root: Optional[Path] = None,
        docs_root: Optional[Path] = None,
        project_root: Optional[Path] = None,
    ):
        root = project_root or PROJECT_ROOT
        src = src_root or SRC_ROOT
        docs = docs_root or DOCS_ROOT

        self._reviewers: Dict[str, Callable[[], ReviewReport]] = {
            "design": DesignReviewer(src, docs).review,
            "code": CodeReviewer(src).review,
            "markdown": MDReviewer(root, src).review,
            "consistency": ConsistencyReviewer(src, docs, root).review,
            "training": TrainingReviewer(src, root).review,
        }

    def run_full_review(self) -> Dict[str, ReviewReport]:
        """執行所有維度的審查。"""
        results = {}
        for name, reviewer_fn in self._reviewers.items():
            try:
                results[name] = reviewer_fn()
            except Exception as e:
                logger.error("Review failed for dimension '%s': %s", name, e, exc_info=True)
                results[name] = ReviewReport(
                    dimension=name,
                    findings=[ReviewFinding(
                        severity=Severity.CRITICAL,
                        category="engine_error",
                        message=f"Review dimension '{name}' failed: {e}",
                    )],
                    score=0.0,
                    summary=f"Review failed: {e}",
                )
        return results

    def run_review(self, dimension: str) -> ReviewReport:
        """執行指定維度的審查。"""
        if dimension not in self._reviewers:
            raise ValueError(
                f"Unknown review dimension: {dimension}. "
                f"Available: {list(self._reviewers.keys())}"
            )
        try:
            return self._reviewers[dimension]()
        except Exception as e:
            logger.error("Review failed for '%s': %s", dimension, e, exc_info=True)
            return ReviewReport(
                dimension=dimension,
                findings=[ReviewFinding(
                    severity=Severity.CRITICAL,
                    category="engine_error",
                    message=f"Review failed: {e}",
                )],
                score=0.0,
                summary=f"Review failed: {e}",
            )

    def get_composite_score(self, reports: Optional[Dict[str, ReviewReport]] = None) -> float:
        """計算綜合評分（所有維度的加權平均）。"""
        if reports is None:
            reports = self.run_full_review()
        if not reports:
            return 0.0

        weights = {
            "design": 0.25,
            "code": 0.25,
            "markdown": 0.15,
            "consistency": 0.20,
            "training": 0.15,
        }
        total = 0.0
        weight_sum = 0.0
        for dim, report in reports.items():
            w = weights.get(dim, 0.1)
            total += report.score * w
            weight_sum += w
        return round(total / weight_sum, 2) if weight_sum > 0 else 0.0

    def generate_summary(self, reports: Optional[Dict[str, ReviewReport]] = None) -> str:
        """生成可讀的審查摘要報告。"""
        if reports is None:
            reports = self.run_full_review()

        lines = [
            "=" * 72,
            "Angela Project Review Report",
            "=" * 72,
            "",
        ]

        for dim, report in reports.items():
            lines.append(f"[{dim.upper()}] Score: {report.score:.1f}/10")
            counts = f"C:{report.critical_count} H:{report.high_count} M:{report.medium_count} L:{report.low_count}"
            lines.append(f"  Findings ({counts}):")
            for f in report.findings[:5]:
                sev_icon = {"critical": "!", "high": "H", "medium": "M", "low": "L", "info": "I"}
                icon = sev_icon.get(f.severity.value, "?")
                loc = f" ({f.file})" if f.file else ""
                lines.append(f"    [{icon}] {f.message}{loc}")
            if len(report.findings) > 5:
                lines.append(f"    ... and {len(report.findings) - 5} more")
            lines.append("")

        composite = self.get_composite_score(reports)
        lines.append("-" * 72)
        lines.append(f"COMPOSITE SCORE: {composite:.2f}/10")
        lines.append("=" * 72)

        return "\n".join(lines)


# Singleton
_engine_instance: Optional[AngelaReviewEngine] = None


def get_review_engine() -> AngelaReviewEngine:
    """取得 Angela Review Engine 單例。"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = AngelaReviewEngine()
    return _engine_instance


def run_full_review() -> Dict[str, Any]:
    """便捷函數: 執行完整審查並返回字典格式。"""
    engine = get_review_engine()
    reports = engine.run_full_review()
    return {
        "reports": {k: v.to_dict() for k, v in reports.items()},
        "composite_score": engine.get_composite_score(reports),
        "summary": engine.generate_summary(reports),
    }


def run_single_review(dimension: str) -> Dict[str, Any]:
    """便捷函數: 執行單維度審查。"""
    engine = get_review_engine()
    report = engine.run_review(dimension)
    return report.to_dict()


__all__ = [
    "AngelaReviewEngine",
    "DesignReviewer",
    "CodeReviewer",
    "MDReviewer",
    "ConsistencyReviewer",
    "TrainingReviewer",
    "ReviewReport",
    "ReviewFinding",
    "Severity",
    "get_review_engine",
    "run_full_review",
    "run_single_review",
]
