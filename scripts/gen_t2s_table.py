#!/usr/bin/env python3
"""繁→簡字元對照表生成器 — 從倉庫自帶的 CC-CEDICT 推導，零外部依賴。

為什麼需要：模板庫（templates_data.json）與情感詞彙全是簡體，使用者打繁體
（「我好難過」「想你」）時逐字比對全數落空，路由因此退化到隨機模板。修法是
在「匹配」前把輸入折成簡體 — 但專案禁用新外部依賴（opencc/zhconv 皆不可用），
所以改由倉庫已經下載的 CC-CEDICT 自己推導。

來源：data/dictionaries/cedict_1_0_ts_utf-8_mdbg.txt.gz
      （scripts/download_datasets.py 產物，data/ 已 gitignore）

來源檔每行格式： 傳統 簡體 [pin1 yin1] /defs/
只取「傳統與簡體同長度」的條目逐字配對；同一傳統字對到多個簡體字時取
出現次數最高者（實測 3679 字中僅 22 字有歧義）。

產物：apps/backend/src/ai/core/t2s_table.py（Generated，手不改）

用法：
    python scripts/gen_t2s_table.py            # 寫檔
    python scripts/gen_t2s_table.py --check    # 只驗證產物是否為最新

退出碼：0 成功 / 1 來源缺失 / 2 產物過期（--check）
"""

import argparse
import collections
import gzip
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CEDICT_GZ = REPO_ROOT / "data" / "dictionaries" / "cedict_1_0_ts_utf-8_mdbg.txt.gz"
OUT_PATH = REPO_ROOT / "apps" / "backend" / "src" / "ai" / "core" / "t2s_table.py"

_ENTRY_RE = re.compile(r"^(\S+)\s+(\S+)\s+\[")
_CHUNK = 96  # characters per source line (readability; E501 is ignored repo-wide)


def build_pairs() -> dict:
    """Return {traditional_char: simplified_char} from CC-CEDICT."""
    if not CEDICT_GZ.exists():
        print(
            f"missing source: {CEDICT_GZ}\n"
            "run `python scripts/download_datasets.py` first (data/ is git-ignored)",
            file=sys.stderr,
        )
        raise SystemExit(1)

    counts: dict = collections.Counter()
    with gzip.open(CEDICT_GZ, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("#"):
                continue
            match = _ENTRY_RE.match(line)
            if not match:
                continue
            traditional, simplified = match.group(1), match.group(2)
            # Only 1:1 length pairs give an unambiguous per-character mapping.
            if len(traditional) != len(simplified):
                continue
            for old, new in zip(traditional, simplified):
                if old != new:
                    counts[(old, new)] += 1

    by_char: dict = collections.defaultdict(list)
    for (old, new), seen in counts.items():
        by_char[old].append((seen, new))

    pairs = {}
    for old, options in by_char.items():
        # Frequency-weighted pick; CC-CEDICT lists the dominant reading first.
        options.sort(reverse=True)
        pairs[old] = options[0][1]
    return pairs


def render(pairs: dict) -> str:
    """Render the generated module source."""
    ordered = sorted(pairs.items(), key=lambda kv: ord(kv[0]))
    traditional = "".join(old for old, _ in ordered)
    simplified = "".join(new for _, new in ordered)

    def literal(name: str, value: str) -> str:
        lines = [f"{name} = ("]
        for start in range(0, len(value), _CHUNK):
            lines.append(f'    "{value[start:start + _CHUNK]}"')
        lines.append(")")
        return "\n".join(lines)

    return (
        '"""Traditional → Simplified character table — GENERATED, do not hand-edit.\n'
        "\n"
        "Regenerate with:  python scripts/gen_t2s_table.py\n"
        "Source: CC-CEDICT (MDBG, CC BY-SA 4.0) shipped by scripts/download_datasets.py\n"
        "Consumed by: ai/core/unicode_utils.to_simplified()\n"
        '"""\n'
        "\n"
        "# =============================================================================\n"
        "# ANGELA-MATRIX: [L1] [α] [A] [L1]\n"
        "# =============================================================================\n"
        "\n"
        "# Parallel strings: TRADITIONAL[i] folds to SIMPLIFIED[i]. Same length is\n"
        "# asserted by the consumer, so a truncated regeneration fails loudly.\n"
        f"{literal('TRADITIONAL', traditional)}\n"
        "\n"
        f"{literal('SIMPLIFIED', simplified)}\n"
        "\n"
        f"PAIR_COUNT = {len(ordered)}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed artifact matches the source (exit 2 if stale)",
    )
    args = parser.parse_args()

    source = render(build_pairs())
    if args.check:
        current = OUT_PATH.read_text(encoding="utf-8") if OUT_PATH.exists() else ""
        if current != source:
            print(f"stale: {OUT_PATH} — regenerate with scripts/gen_t2s_table.py")
            return 2
        print(f"up to date: {OUT_PATH}")
        return 0

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(source, encoding="utf-8")
    pairs = int(source.rsplit("PAIR_COUNT = ", 1)[1])
    print(f"wrote {OUT_PATH} ({pairs} character pairs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
