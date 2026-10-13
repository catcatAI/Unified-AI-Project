#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [βγδ] [B] [L3-L5]
# =============================================================================
"""测试结果处理主脚本。

读取 pytest 的 JUnit XML（或同构的 JSON）测试结果，输出统计摘要，可选地与基线
比较（回归检测）与追踪历史趋势，并可选择发出邮件通知。

审计修正 (2026-10-13)：旧版本是 placeholder——无论 `results_file` 是否存在都只做
`logger.info("Processing test results...")` 然后 `return True`，调用方因此永远得到
退出码 0（`sys.exit(0)`），即使文件根本不存在。现在会真正读取并解析文件；输入
缺失、格式错误或解析不出任何测试用例时回传 False（退出码 1），不再假报成功。
"""

import argparse
import json
import logging
import os
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# 读取与解析
# =============================================================================
def _load_report_generator():
    """从同目录载入 TestReportGenerator。

    该脚本可能以 `python scripts/utils/process_test_results.py` 直接执行，此时
    sys.path[0] 是 scripts/utils/ 而非仓库根目录，`import scripts.*` 会失败；
    因此以显式路径载入同层模块，不依赖 cwd 或 sys.path。
    """
    import importlib.util

    module_path = Path(__file__).resolve().parent / "generate_test_report.py"
    if not module_path.is_file():
        logger.error("generate_test_report.py not found next to this script: %s", module_path)
        return None
    spec = importlib.util.spec_from_file_location("_angela_generate_test_report", module_path)
    if spec is None or spec.loader is None:  # pragma: no cover - 极少数平台
        logger.error("Cannot create import spec for %s", module_path)
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "TestReportGenerator", None)


def _parse_junit_xml(path: str) -> Optional[Dict[str, Any]]:
    """以既有的 TestReportGenerator 解析 JUnit XML。

    沿用单一实作，避免解析逻辑分叉（该解析器的 <testsuite> 遍历与变量名 bug
    已于 2026-10-12 修复）。
    """
    generator_cls = _load_report_generator()
    if generator_cls is None:
        return None

    # 只借用解析器；把 report_dir 指向既有目录，避免仅为了解析就建立 test_reports/。
    generator = generator_cls(report_dir=str(Path(path).parent))
    parsed = generator.parse_junit_xml(path)
    if not parsed or not parsed.get("test_cases"):
        logger.error("No test cases found in %s — file is empty or not a JUnit report", path)
        return None
    return parsed


def _normalise_json(data: Dict[str, Any], path: str) -> Optional[Dict[str, Any]]:
    """校验 JSON 结果，schema 与 TestReportGenerator 的输出一致。"""
    cases = data.get("test_cases")
    if not isinstance(cases, list):
        logger.error(
            "Results file %s: JSON must contain a 'test_cases' list "
            "(same shape as generate_test_report.py output)",
            path,
        )
        return None
    return {
        "timestamp": data.get("timestamp", ""),
        "test_cases": cases,
    }


def _load_results(path: str) -> Optional[Dict[str, Any]]:
    """读取测试结果文件（JUnit XML 或 JSON）；无法使用时回传 None。"""
    p = Path(path)
    if not p.is_file():
        logger.error("Results file not found: %s", path)
        return None
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except OSError as e:
        logger.error("Cannot read results file %s: %s", path, e)
        return None

    if text.lstrip().startswith("<"):
        return _parse_junit_xml(path)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        logger.error("Results file %s is neither JUnit XML nor valid JSON: %s", path, e)
        return None
    if not isinstance(data, dict):
        logger.error("Results file %s: expected a JSON object, got %s", path, type(data).__name__)
        return None
    return _normalise_json(data, path)


# =============================================================================
# 统计与比较
# =============================================================================
def _summarise(test_results: Dict[str, Any]) -> Dict[str, Any]:
    """计算总数/通过/失败/跳过与通过率。未知状态一律计入失败，不假装通过。"""
    cases = test_results.get("test_cases") or []
    counts = {"total": len(cases), "passed": 0, "failed": 0, "skipped": 0}
    for case in cases:
        outcome = str(case.get("outcome", "")).lower()
        if outcome in ("passed", "failed", "skipped"):
            counts[outcome] += 1
        else:
            logger.warning(
                "Unknown outcome %r for test %s — counted as failed",
                case.get("outcome"),
                _case_key(case),
            )
            counts["failed"] += 1
    executed = counts["passed"] + counts["failed"]
    counts["pass_rate"] = round(counts["passed"] / executed, 4) if executed else 0.0
    return counts


def _case_key(case: Dict[str, Any]) -> str:
    return f"{case.get('module', '')}::{case.get('name', '')}"


def _outcomes_by_key(test_results: Dict[str, Any]) -> Dict[str, str]:
    return {
        _case_key(c): str(c.get("outcome", "")).lower()
        for c in (test_results.get("test_cases") or [])
    }


def _compare_baseline(
    current: Dict[str, Any], baseline: Dict[str, Any]
) -> Tuple[List[str], List[str], List[str]]:
    """回傳 (regressions, fixed, new_tests)。

    regression = 基线通过、本次失败；fixed = 基线失败、本次通过；
    new_tests = 只出现在本次结果中的用例。
    """
    cur = _outcomes_by_key(current)
    base = _outcomes_by_key(baseline)
    regressions = [k for k, v in cur.items() if v == "failed" and base.get(k) == "passed"]
    fixed = [k for k, v in cur.items() if v == "passed" and base.get(k) == "failed"]
    new_tests = [k for k in cur if k not in base]
    return regressions, fixed, new_tests


def _trend(history: List[Dict[str, Any]]) -> List[Tuple[str, Dict[str, Any]]]:
    """(label, counts) 列表，按传入顺序；label 用结果的 timestamp 或序号。"""
    out: List[Tuple[str, Dict[str, Any]]] = []
    for i, results in enumerate(history, 1):
        label = results.get("timestamp") or f"run {i}"
        out.append((str(label), _summarise(results)))
    return out


# =============================================================================
# 邮件通知
# =============================================================================
def _send_email(subject: str, body: str, recipients: List[str]) -> bool:
    """发送邮件；未配置 SMTP 时明确警告并回传 False（不静默假装已寄出）。"""
    host = os.getenv("SMTP_HOST")
    if not host:
        logger.warning(
            "send_email requested but SMTP_HOST is not set — no email was sent "
            "(set SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASSWORD to enable)"
        )
        return False
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = user or "angela-ci@localhost"
    message["To"] = ", ".join(recipients)
    message.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.starttls()
            if user and password:
                smtp.login(user, password)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException) as e:
        logger.error("Failed to send email via %s:%s: %s", host, port, e)
        return False
    logger.info("Email notification sent to %s", ", ".join(recipients))
    return True


# =============================================================================
# 主流程
# =============================================================================
def process_test_results(
    results_file: str,
    baseline_file: Optional[str] = None,
    historical_files: Optional[list] = None,
    send_email: bool = False,
    recipient_emails: Optional[list] = None,
) -> bool:
    """处理测试结果的完整流程。分析失败或输入不可用时回传 False。"""
    logger.info("Processing test results: %s", results_file)

    current = _load_results(results_file)
    if current is None:
        return False

    counts = _summarise(current)
    lines = [
        f"Total:   {counts['total']}",
        f"Passed:  {counts['passed']}",
        f"Failed:  {counts['failed']}",
        f"Skipped: {counts['skipped']}",
        f"Pass rate (passed / executed): {counts['pass_rate']:.2%}",
    ]

    if baseline_file:
        baseline = _load_results(baseline_file)
        if baseline is None:
            logger.error("Baseline file unusable: %s", baseline_file)
            return False
        regressions, fixed, new_tests = _compare_baseline(current, baseline)
        lines.append(
            f"Baseline comparison: {len(regressions)} regression(s), "
            f"{len(fixed)} fixed, {len(new_tests)} new test(s)"
        )
        for key in regressions:
            lines.append(f"  REGRESSION: {key}")
        for key in fixed:
            lines.append(f"  FIXED: {key}")
        if regressions:
            logger.warning("%d regression(s) vs baseline", len(regressions))

    if historical_files:
        history: List[Dict[str, Any]] = [current]
        for hist_path in historical_files:
            loaded = _load_results(hist_path)
            if loaded is None:
                logger.error("Historical file unusable: %s", hist_path)
                return False
            history.append(loaded)
        lines.append("Trend (oldest → newest):")
        for label, hist_counts in _trend(history):
            lines.append(
                f"  {label}: {hist_counts['passed']}/{hist_counts['total']} "
                f"passed ({hist_counts['pass_rate']:.2%})"
            )

    summary = "\n".join(lines)
    logger.info("Test result summary:\n%s", summary)

    if send_email:
        if not recipient_emails:
            logger.error("send_email=True but no recipients given")
            return False
        _send_email(
            subject=f"Test results: {counts['passed']}/{counts['total']} passed",
            body=summary,
            recipients=list(recipient_emails),
        )

    return True


def main() -> None:
    """主函数"""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description="处理测试结果的完整流程")
    parser.add_argument("results_file", help="测试结果文件路径（JUnit XML 或 JSON）")
    parser.add_argument("--baseline", help="基线测试结果文件路径")
    parser.add_argument("--historical", nargs="*", help="历史测试结果文件列表")
    parser.add_argument("--send-email", action="store_true", help="是否发送邮件通知")
    parser.add_argument("--recipients", nargs="*", help="邮件接收者列表")

    args = parser.parse_args()

    success = process_test_results(
        results_file=args.results_file,
        baseline_file=args.baseline,
        historical_files=args.historical,
        send_email=args.send_email,
        recipient_emails=args.recipients,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
