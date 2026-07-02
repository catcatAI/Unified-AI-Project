# =============================================================================
# ANGELA-MATRIX: [L3] [γ] [C] [L2]
# =============================================================================

import json
import logging
from typing import List, Tuple

from .telemetry import TelemetryCollector

logger = logging.getLogger(__name__)


class IOAnalyzer:
    """
    Produces structured I/O analysis reports from TelemetryCollector data.
    """

    def __init__(self, collector: TelemetryCollector):
        self.collector = collector

    def generate_report(self, format: str = "text") -> str:
        if format == "json":
            return self._generate_json()
        return self._generate_text()

    def _generate_json(self) -> str:
        summary = self.collector.get_summary()
        reflex_report = self.collector.get_reflex_report()
        histograms = {}
        for stage in summary.get("stages", {}):
            histograms[stage] = self.collector.get_latency_histogram(stage)
        return json.dumps(
            {
                "summary": summary,
                "reflex_patterns": [
                    {"pattern": p, "count": c, "pct": pct}
                    for p, c, pct in reflex_report
                ],
                "latency_histograms": histograms,
            },
            ensure_ascii=False,
            indent=2,
        )

    def _generate_text(self) -> str:
        lines: List[str] = []
        lines.append("=" * 64)
        lines.append("  ED3N I/O Analysis Report")
        lines.append("=" * 64)
        lines.append("")
        lines.append(self._latency_section())
        lines.append("")
        lines.append(self._reflex_section())
        lines.append("")
        lines.append(self._cache_section())
        lines.append("")
        lines.append(self._fallback_section())
        lines.append("")
        lines.append(self._confidence_section())
        lines.append("=" * 64)
        return "\n".join(lines)

    def _latency_section(self) -> str:
        summary = self.collector.get_summary()
        stages = summary.get("stages", {})
        if not stages:
            return "  Latency: no data"
        lines = ["  Latency Per Stage (ms):", ""]
        lines.append(
            f"  {'Stage':<20} {'Count':<8} {'Avg':<10} {'Min':<10} "
            f"{'Max':<10} {'P50':<10} {'P95':<10} {'P99':<10}"
        )
        lines.append("  " + "-" * 88)
        for stage_name, metrics in sorted(stages.items()):
            lines.append(
                f"  {stage_name:<20} {metrics['count']:<8} "
                f"{metrics['avg_ms']:<10} {metrics['min_ms']:<10} "
                f"{metrics['max_ms']:<10} {metrics['p50_ms']:<10} "
                f"{metrics['p95_ms']:<10} {metrics['p99_ms']:<10}"
            )
        return "\n".join(lines)

    def _reflex_section(self) -> str:
        report = self.collector.get_reflex_report()
        if not report:
            return "  Reflex Patterns: no matches recorded"
        lines = ["  Top Reflex Patterns (by match count):", ""]
        lines.append(
            f"  {'Pattern':<30} {'Count':<10} {'% of Queries':<15}"
        )
        lines.append("  " + "-" * 55)
        for pattern, count, pct in report[:20]:
            lines.append(f"  {pattern:<30} {count:<10} {pct:<15}")
        return "\n".join(lines)

    def _cache_section(self) -> str:
        summary = self.collector.get_summary()
        hits = summary.get("cache_hits", 0)
        misses = summary.get("cache_misses", 0)
        rate = summary.get("cache_hit_rate", 0.0)
        total = hits + misses
        if total == 0:
            return "  Dictionary Encode Cache: no data"
        return (
            f"  Dictionary Encode Cache:\n"
            f"    Hits:     {hits}\n"
            f"    Misses:   {misses}\n"
            f"    Total:    {total}\n"
            f"    Hit Rate: {rate:.2%}"
        )

    def _fallback_section(self) -> str:
        summary = self.collector.get_summary()
        count = summary.get("fallback_count", 0)
        rate = summary.get("fallback_rate", 0.0)
        total = summary.get("total_queries", 0)
        if total == 0:
            return "  Fallback: no data"
        top_fallback_inputs = self._top_fallback_inputs(5)
        lines = ["  Fallback Analysis:", ""]
        lines.append(
            f"    Total Queries: {total}\n"
            f"    Fallback Count: {count}\n"
            f"    Fallback Rate:  {rate:.2%}"
        )
        if top_fallback_inputs:
            lines.append("")
            lines.append("  Most Common Fallback-Triggering Inputs:")
            for i, (text, freq) in enumerate(top_fallback_inputs, 1):
                lines.append(f"    {i}. {text!r} (x{freq})")
        return "\n".join(lines)

    def _confidence_section(self) -> str:
        summary = self.collector.get_summary()
        avg = summary.get("confidence_avg", 0.0)
        total = summary.get("total_queries", 0)
        if total == 0:
            return "  Confidence Distribution: no data"
        bucket_counts: List[int] = [0, 0, 0, 0, 0]
        bucket_labels = ["0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"]
        for rec in self.collector._records:
            conf = rec.get("confidence", 0.0)
            if conf < 0.2:
                bucket_counts[0] += 1
            elif conf < 0.4:
                bucket_counts[1] += 1
            elif conf < 0.6:
                bucket_counts[2] += 1
            elif conf < 0.8:
                bucket_counts[3] += 1
            else:
                bucket_counts[4] += 1
        lines = ["  Confidence Distribution:", ""]
        lines.append(
            f"    Average Confidence: {avg:.4f}  (over {total} queries)"
        )
        lines.append("")
        lines.append(f"  {'Bucket':<15} {'Count':<10} {'%':<10}")
        lines.append("  " + "-" * 35)
        for label, cnt in zip(bucket_labels, bucket_counts):
            pct = round(cnt / total * 100, 2) if total else 0.0
            lines.append(f"  {label:<15} {cnt:<10} {pct:<10}")
        return "\n".join(lines)

    def _top_fallback_inputs(self, n: int = 5) -> List[Tuple[str, int]]:
        counter: dict = {}
        for rec in self.collector._records:
            if rec.get("is_fallback") and rec.get("input_text"):
                text = rec["input_text"]
                counter[text] = counter.get(text, 0) + 1
        sorted_items = sorted(counter.items(), key=lambda x: x[1], reverse=True)
        return sorted_items[:n]
