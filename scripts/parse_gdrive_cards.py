#!/usr/bin/env python3
"""
parse_gdrive_cards.py — 解析 Google Drive 下載的卡片堆檔案

掃描 gdrive_export/ 目錄，分類所有檔案，提取結構化卡片資料，
產出：
  1. gdrive_inventory.md — 完整檔案目錄與分類
  2. gdrive_cards.json — 提取的結構化卡片資料
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

EXPORT_DIR = Path(__file__).resolve().parent.parent / "apps" / "game-rpg" / "data" / "gdrive_export"
OUTPUT_MD = Path(__file__).resolve().parent.parent / "apps" / "crystal-cards" / "game-data" / "gdrive-inventory.md"
OUTPUT_JSON = Path(__file__).resolve().parent.parent / "apps" / "game-rpg" / "data" / "gdrive_cards.json"

# ─── Classification patterns ───
CARD_TYPE_PATTERNS = [
    (r"角色卡[：:]?\s*(CC-?\d+|C\d+)", "角色卡", "character"),
    (r"角色卡[：:]?\s*(.+)", "角色卡", "character"),
    (r"(CC-?\d+).*角色卡", "角色卡", "character"),
    (r"國家卡[：:]?\s*(NAT-?\d+)", "國家卡", "nation"),
    (r"國家卡[：:]?\s*(.+)", "國家卡", "nation"),
    (r"組織卡[：:]?\s*(ORG-?\d+)", "組織卡", "organization"),
    (r"組織卡[：:]?\s*(.+)", "組織卡", "organization"),
    (r"規則卡[：:]?\s*(RC-?\d+)", "規則卡", "rule"),
    (r"規則卡[：:]?\s*(.+)", "規則卡", "rule"),
    (r"場景卡[：:]?\s*(S\d+)", "場景卡", "scene"),
    (r"場景卡[：:]?\s*(.+)", "場景卡", "scene"),
    (r"劇情節點卡[：:]?\s*(EP-?\d+)", "劇情節點卡", "event"),
    (r"劇情節點卡[：:]?\s*(.+)", "劇情節點卡", "event"),
    (r"世界觀[：:]?\s*(.+)", "世界觀卡", "worldview"),
    (r"設定卡[：:]?\s*(.+)", "設定卡", "setting"),
]

FILE_TYPE_PATTERNS = [
    (r"Ver\s*\d", "設定集版本", "setting_collection"),
    (r"設定集|設定整理|設定詳細", "設定集", "setting_collection"),
    (r"章節|第.幕|序章", "小說章節", "novel_chapter"),
    (r"小說|書名|出版稿|書寫集", "小說/出版", "novel"),
    (r"卡組|卡片總目錄|卡片總覽", "卡組總覽", "card_collection"),
    (r"設計稿|設計藍圖|核心設計", "設計文檔", "design"),
    (r"統計|總數|清單|目錄|歸檔", "統計/目錄", "inventory"),
    (r"補充|更新|修正|修復", "補充/修正", "patch"),
    (r"角色軌跡|基調|物種分類", "世界觀設定", "worldbuilding"),
    (r"完整角色卡清單", "角色清單", "character_list"),
]

# ─── Structured field extractors ───
FIELD_PATTERNS = {
    "card_id": r"卡片代碼\s+(.+)",
    "name": r"名稱\s+(.+)",
    "card_type": r"類型\s+(.+)",
    "world_line": r"所屬世界線\s+(.+)",
    "race": r"(?:種族|成員種族)\s+(.+)",
    "location": r"(?:地點|所在地|位置|首都)\s+(.+)",
    "desc": r"(?:描述|一條總結)\s+(.+)",
    "hp": r"HP\s*[:：]?\s*(\d+)",
    "atk": r"(?:ATK|攻擊力)\s*[:：]?\s*(\d+)",
    "def_": r"(?:DEF|防禦力)\s*[:：]?\s*(\d+)",
    "spd": r"(?:SPD|速度)\s*[:：]?\s*(\d+)",
}


def classify_file(filename: str, content: str) -> Tuple[str, str, str]:
    """Classify a file by its name and content. Returns (category, subcategory, card_id)."""
    name_lower = filename.lower()

    # Try card type patterns on filename
    for pattern, card_type, subcategory in CARD_TYPE_PATTERNS:
        m = re.search(pattern, filename)
        if m:
            card_id = m.group(1) if m.lastindex else ""
            return card_type, subcategory, card_id.strip()

    # Try file type patterns on filename
    for pattern, category, subcategory in FILE_TYPE_PATTERNS:
        if re.search(pattern, filename, re.IGNORECASE):
            return category, subcategory, ""

    # Try content-based classification
    first_500 = content[:500]
    for pattern, card_type, subcategory in CARD_TYPE_PATTERNS:
        m = re.search(pattern, first_500)
        if m:
            card_id = m.group(1) if m.lastindex else ""
            return card_type, subcategory, card_id.strip()

    for pattern, category, subcategory in FILE_TYPE_PATTERNS:
        if re.search(pattern, first_500, re.IGNORECASE):
            return category, subcategory, ""

    return "未分類", "unknown", ""


def extract_structured_fields(content: str) -> Dict[str, Any]:
    """Extract structured fields from card content."""
    fields = {}
    for field_name, pattern in FIELD_PATTERNS.items():
        m = re.search(pattern, content)
        if m:
            fields[field_name] = m.group(1).strip()

    # Extract table-like data (項目 內容 pairs)
    table_rows = re.findall(r"(\S+)\s{2,}(.+?)(?:\r?\n|$)", content)
    for key, value in table_rows:
        if key in ("項目", "內容", "---", ""):
            continue
        if key not in fields and len(value) > 2 and len(value) < 500:
            fields[key] = value.strip()

    return fields


def extract_abilities(content: str) -> List[str]:
    """Extract abilities/skills from content."""
    abilities = []
    patterns = [
        r"(?:能力|技能|特殊能力)[：:]?\s*(.+)",
        r"(?:Token|token)[：:]?\s*(.+)",
    ]
    for pattern in patterns:
        for m in re.finditer(pattern, content):
            text = m.group(1).strip()
            # Split by common separators
            parts = re.split(r"[,，、/]", text)
            abilities.extend(p.strip() for p in parts if p.strip())
    return abilities[:10]  # Limit


def parse_file(filepath: Path) -> Dict[str, Any]:
    """Parse a single gdrive_export file."""
    try:
        content = filepath.read_text(encoding="utf-8-sig")
    except Exception as e:
        return {"error": str(e)}

    filename = filepath.stem
    category, subcategory, card_id = classify_file(filename, content)

    result = {
        "filename": filepath.name,
        "name": filename,
        "category": category,
        "subcategory": subcategory,
        "card_id": card_id,
        "size_bytes": filepath.stat().st_size,
        "line_count": content.count("\n") + 1,
    }

    # Extract structured fields if it's a card
    if subcategory in ("character", "nation", "organization", "rule", "scene", "event"):
        fields = extract_structured_fields(content)
        result["fields"] = fields
        abilities = extract_abilities(content)
        if abilities:
            result["abilities"] = abilities

    # Extract first meaningful line as summary
    lines = [l.strip() for l in content.split("\n") if l.strip() and l.strip() != "---"]
    if lines:
        result["summary"] = lines[0][:200]

    return result


def main():
    print("=" * 60)
    print("  Google Drive 卡片堆解析器")
    print("=" * 60)

    if not EXPORT_DIR.exists():
        print(f"❌ 找不到 {EXPORT_DIR}")
        print("   請先執行 sync_card_deck.py 下載檔案")
        return

    # Find all .txt files (some filenames have newlines, handle both)
    files = sorted(EXPORT_DIR.glob("*.txt"))
    print(f"\n📂 找到 {len(files)} 個檔案")

    # Parse all files
    all_cards = []
    by_category = {}

    for f in files:
        card = parse_file(f)
        all_cards.append(card)
        cat = card["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(card)

    # Print summary
    print("\n📊 分類統計：")
    for cat in sorted(by_category.keys()):
        items = by_category[cat]
        print(f"  {cat}: {len(items)} 個檔案")
        for item in items[:3]:
            cid = item.get("card_id", "")
            name = item["name"][:50]
            print(f"    - {cid} {name}" if cid else f"    - {name}")
        if len(items) > 3:
            print(f"    ... 還有 {len(items)-3} 個")

    # Generate MD inventory
    md_lines = [
        "# Google Drive 卡片堆 — 完整檔案目錄",
        "",
        f"> 解析日期：2026-08-30 | 總計 **{len(files)} 個檔案**",
        "",
        "## 分類統計",
        "",
        "| 類別 | 數量 |",
        "|------|------|",
    ]
    for cat in sorted(by_category.keys()):
        md_lines.append(f"| {cat} | {len(by_category[cat])} |")
    md_lines.append(f"| **合計** | **{len(files)}** |")
    md_lines.append("")

    for cat in sorted(by_category.keys()):
        md_lines.append(f"## {cat}")
        md_lines.append("")
        for item in by_category[cat]:
            cid = item.get("card_id", "")
            name = item["name"]
            lines = item.get("line_count", 0)
            summary = item.get("summary", "")[:100]
            md_lines.append(f"- **{name}** ({lines} 行)")
            if summary:
                md_lines.append(f"  > {summary}")
            if item.get("fields"):
                for k, v in list(item["fields"].items())[:5]:
                    md_lines.append(f"  - {k}: {v}")
            md_lines.append("")

    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"\n📄 MD 目錄已產出：{OUTPUT_MD}")

    # Save JSON
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(all_cards, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"📄 JSON 資料已產出：{OUTPUT_JSON}")

    # Count extractable cards
    extractable = [c for c in all_cards if c.get("card_id")]
    print(f"\n🎯 可提取的結構化卡片：{len(extractable)} 張")
    for c in extractable:
        print(f"  [{c['category']}] {c['card_id']}: {c['name'][:60]}")


if __name__ == "__main__":
    main()
