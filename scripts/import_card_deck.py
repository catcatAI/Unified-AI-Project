"""
Card Deck Import Script — 從 Google Drive 本地路徑讀取 .gdoc 並匯入 CardRegistry.

使用方式:
  1. 確保 Google Drive 已同步到本地 (G:\我的雲端硬碟\卡片堆)
  2. 確保 apps/backend/config/credentials.json 存在
  3. 執行: python scripts/import_card_deck.py

或使用 --local-only 模式（僅從文件名稱提取結構，不讀取內容）:
  python scripts/import_card_deck.py --local-only
"""

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_SRC = PROJECT_ROOT / "apps" / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Card deck path
CARD_DECK_PATH = Path(r"G:\我的雲端硬碟\卡片堆")
OUTPUT_DIR = PROJECT_ROOT / "data"
OUTPUT_FILE = OUTPUT_DIR / "card_registry.json"
INVENTORY_FILE = OUTPUT_DIR / "card_deck_inventory.json"


def scan_card_files(base_path: Path) -> List[Dict[str, Any]]:
    """Scan all .gdoc files and extract metadata from filenames."""
    results = []
    
    for root, dirs, files in os.walk(base_path):
        for f in files:
            if f.endswith(".gdoc") and f != "desktop.ini":
                full_path = Path(root) / f
                rel_path = full_path.relative_to(base_path)
                name = f.replace(".gdoc", "")
                
                # Detect card type and ID from filename
                card_id, card_type = detect_card_type(name)
                
                # Detect world line
                world_line = ""
                if "迴廊" in str(rel_path) or "多元宇宙" in name:
                    world_line = "W01"
                elif "艦娘" in str(rel_path):
                    world_line = "W02"
                
                results.append({
                    "card_id": card_id,
                    "name": name,
                    "type": card_type,
                    "path": str(rel_path),
                    "full_path": str(full_path),
                    "world_line": world_line,
                    "has_explicit_id": card_id is not None,
                })
    
    return results


def detect_card_type(name: str) -> Tuple[Optional[str], str]:
    """Detect card ID and type from filename."""
    # Explicit ID patterns
    patterns = [
        (r"CC[-\s]?(\d+)", "CC", "CHARACTER"),
        (r"RC[-\s]?(\d+)", "RC", "RULE"),
        (r"NAT[-\s]?(\d+)", "NAT", "NATION"),
        (r"ORG[-\s]?(\d+)", "ORG", "ORGANIZATION"),
        (r"EP[-\s]?(\d+)", "E", "EVENT"),
        (r"SL[-\s]?(\d+)", "SL", "STORY_LINE"),
        (r"SC[-\s]?(\d+)", "SC", "SCENE"),
        (r"WC[-\s]?(\d+)", "WC", "WORLD_CORE"),
        (r"SK[-\s]?(\d+)", "SK", "SKILL"),
        (r"IT[-\s]?(\d+)", "IT", "ITEM"),
        (r"UM[-\s]?(\d+)", "UM", "UNIVERSAL_MECHANISM"),
        (r"WT[-\s]?(\d+)", "WT", "WORK_TOOL"),
        (r"TP[-\s]?([A-C])", "TP", "PLAYER_TEMPLATE"),
        (r"MF[-\s]?(\d+)", "MF", "META_FORMULA"),
        (r"SLex[-\s]?(\d+)", "SLex", "SAFETY_LEXICON"),
        (r"CCK[-\s]?(\d+)", "CCK", "META_SETTING"),
    ]
    
    for pattern, prefix, card_type in patterns:
        m = re.search(pattern, name)
        if m:
            return f"{prefix}-{m.group(1)}", card_type
    
    # Chinese keyword detection
    if "角色卡" in name:
        return None, "CHARACTER"
    if "場景卡" in name:
        return None, "SCENE"
    if "規則卡" in name:
        return None, "RULE"
    if "國家卡" in name:
        return None, "NATION"
    if "組織卡" in name:
        return None, "ORGANIZATION"
    if "設定卡" in name or "設定" in name:
        return None, "SETTING"
    if "劇情" in name or "事件" in name:
        return None, "EVENT"
    if "卡組" in name:
        return None, "CARD_SET"
    if "目錄" in name or "統計" in name:
        return None, "INDEX"
    if "token" in name.lower():
        return None, "TOKEN_DEF"
    
    return None, "OTHER"


def try_read_gdoc_content(gdoc_path: str) -> Optional[str]:
    """Try to read .gdoc file content via Google Drive API."""
    try:
        from core.card.parser.gdoc_reader import read_gdoc_file
        return read_gdoc_file(gdoc_path)
    except Exception as e:
        logger.debug(f"Could not read {gdoc_path}: {e}")
        return None


def create_card_from_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
    """Create a card dictionary from filename metadata."""
    from datetime import datetime
    
    card = {
        "card_id": meta["card_id"] or f"UNASSIGNED-{hash(meta['path']) % 10000:04d}",
        "world_line": meta["world_line"],
        "qualified_id": "",
        "alternate_selves": [],
        "card_type": meta["type"],
        "name": meta["name"],
        "core_trait": "",
        "meta_data": {"source_path": meta["path"]},
        "custom_fields": {},
        "tokens": [],
        "social_distance": [],
        "history_events": [],
        "source_files": [{
            "path": meta["path"],
            "doc_id": "",
            "last_write_time": datetime.now().isoformat(),
            "raw_text": "",
        }],
        "conflicts": [],
        "visual_data": None,
    }
    
    if meta["world_line"]:
        card["qualified_id"] = f"{card['card_id']}@{meta['world_line']}"
    else:
        card["qualified_id"] = card["card_id"]
    
    return card


def main():
    parser = argparse.ArgumentParser(description="Import card deck from Google Drive")
    parser.add_argument("--local-only", action="store_true", 
                        help="Only extract metadata from filenames, don't read gdoc content")
    parser.add_argument("--output", type=str, default=str(OUTPUT_FILE),
                        help="Output JSON file path")
    args = parser.parse_args()
    
    logger.info(f"Scanning card deck at {CARD_DECK_PATH}")
    
    if not CARD_DECK_PATH.exists():
        logger.error(f"Card deck path not found: {CARD_DECK_PATH}")
        return
    
    # Scan all files
    files = scan_card_files(CARD_DECK_PATH)
    logger.info(f"Found {len(files)} .gdoc files")
    
    # Save inventory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(INVENTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(files, f, ensure_ascii=False, indent=2)
    logger.info(f"Inventory saved to {INVENTORY_FILE}")
    
    # Create cards
    cards = []
    for meta in files:
        card = create_card_from_metadata(meta)
        
        # Try to read content if not --local-only
        if not args.local_only:
            content = try_read_gdoc_content(meta["full_path"])
            if content:
                card["meta_data"]["raw_text"] = content[:5000]  # Store first 5000 chars
                logger.info(f"  Read content for {card['card_id']}: {len(content)} chars")
        
        cards.append(card)
    
    # Save registry
    registry = {card["qualified_id"]: card for card in cards}
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    logger.info(f"Registry saved to {args.output} ({len(cards)} cards)")
    
    # Print summary
    by_type = {}
    for card in cards:
        t = card["card_type"]
        by_type[t] = by_type.get(t, 0) + 1
    
    print("\n=== Card Type Summary ===")
    for t, count in sorted(by_type.items()):
        print(f"  {t}: {count}")
    print(f"  TOTAL: {len(cards)}")
    
    explicit = sum(1 for c in cards if c["card_id"] and not c["card_id"].startswith("UNASSIGNED"))
    print(f"\n  With explicit ID: {explicit}")
    print(f"  Need manual ID assignment: {len(cards) - explicit}")


if __name__ == "__main__":
    main()
