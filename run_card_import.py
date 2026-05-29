"""
Angela Card Import Runner
=========================
Imports cards from Google Drive "卡片堆" folder through the CardImportPipeline.

Usage:
    python run_card_import.py                    # Full import with Drive auth
    python run_card_import.py --dry-run          # List files without importing
    python run_card_import.py --from-dir <path>  # Import from local directory
    python run_card_import.py --save <path>      # Save registry to JSON after import
    python run_card_import.py --load <path>      # Load existing registry before import
"""

import argparse
import asyncio
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List

# Ensure backend src is in path
BACKEND_SRC = Path(__file__).resolve().parent / "apps" / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("card_import")


# Adaptive card ID patterns — discover prefixes dynamically instead of hard-coding
CARD_ID_RE = re.compile(
    r"(?:角色卡|規則卡|設定卡|劇情節點卡|場景卡|角色代碼|卡片代碼)[：:\s]*"
    r"([A-Z][A-Za-z]+)[-\s]*(\d+)",
)

CARD_ID_SHORT_RE = re.compile(r"([A-Z][A-Za-z]+)[-\s]*(\d+)")

TEMPLATE_RE = re.compile(r"角色卡\s*([A-C])\s*[：:]")


def _split_card_content(content: str) -> List[str]:
    """Split content by card ID boundaries — works for any document format.

    Only splits on explicit card-type-prefixed IDs (角色卡：CC-43, 規則卡：RC-01)
    or template patterns (角色卡 A：). Bare short IDs (CC-xx) inside reference
    tables are ignored — they belong to the single card being described.
    """
    text = content.strip()
    if not text:
        return []

    # Primary: match card type prefix + ID (角色卡：CC-43, 規則卡：RC-01, etc.)
    matches = list(CARD_ID_RE.finditer(text))
    # Fallback: template pattern (角色卡 A：, 角色卡 B：, 角色卡 C：)
    if len(matches) < 2:
        matches = list(TEMPLATE_RE.finditer(text))
    if len(matches) < 2:
        return [text]

    # Split at each card ID boundary
    sections = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section = text[start:end].strip()
        if len(section) >= 30:
            sections.append(section)
    return sections if sections else [text]


async def import_from_drive(args) -> int:
    """Import cards from Google Drive."""
    from integrations.google_drive_service import GoogleDriveService

    service = GoogleDriveService._create()
    logger.info("Authenticating with Google Drive...")
    if not service.is_authenticated():
        logger.info("Opening browser for Google OAuth authorization...")
        if not service.authenticate():
            logger.error("Authentication failed or cancelled.")
            return 1

    folder_name = args.folder or "卡片堆"
    logger.info(f"Listing files in '{folder_name}'...")

    q = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    folders = service.list_files(query=q)
    if not folders:
        logger.error(f"Folder '{folder_name}' not found in Google Drive.")
        return 1

    root_id = folders[0]["id"]

    # Collect .gdoc files from all subfolders recursively
    def collect_gdocs(folder_id: str) -> List[Dict]:
        results = []
        q_docs = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.document'"
        results.extend(service.list_files(query=q_docs))
        q_sub = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder'"
        subfolders = service.list_files(query=q_sub)
        for sf in subfolders:
            results.extend(collect_gdocs(sf["id"]))
        return results

    gdoc_files = collect_gdocs(root_id)

    # Only skip obvious non-card files (novel chapters, version backups)
    card_files = [
        f for f in gdoc_files
        if not f.get("name", "").startswith("Ver ")
        and not f.get("name", "").startswith("V3.")
        and f.get("name") != "desktop.ini"
        and not re.search(r"第\s*\d+\s*章", f.get("name", ""))
    ]

    # Separate individual card files (named like "角色卡：...") from reference/group files
    CARD_FILE_PREFIX = re.compile(r"^(角色卡|規則卡|設定卡|劇情節點卡|場景卡)[：:]")
    individual_cards = [f for f in card_files if CARD_FILE_PREFIX.match(f.get("name", ""))]
    other_files = [f for f in card_files if not CARD_FILE_PREFIX.match(f.get("name", ""))]

    logger.info(
        f"Found {len(gdoc_files)} Google Docs total: "
        f"{len(individual_cards)} individual cards, {len(other_files)} reference/group files."
    )

    if args.dry_run:
        for f in card_files:
            logger.info(f"  [{f.get('id', '?')}] {f.get('name', '?')}")
        return 0

    from core.card.resolver.pipeline_orchestrator import CardImportPipeline
    from core.card.card_store import CardRegistry

    pipeline = CardImportPipeline()
    registry = CardRegistry()
    if args.load:
        registry.load(Path(args.load))

    def _process_file(gf, is_reference: bool = False) -> None:
        name = gf.get("name", "unnamed")
        logger.info(f"Processing: {name}" + (" (reference)" if is_reference else ""))
        try:
            content = service.download_file_content(gf["id"])
            if not content:
                logger.warning(f"  Empty content for {name}, skipping.")
                return
            sections = _split_card_content(content)
            for section in sections:
                result = pipeline.process(section, source_label=f"gdrive://{gf['id']}")
                if result.card and result.card.card_id:
                    cid, wl = result.card.card_id, result.card.world_line
                    key = result.card.qualified_id or f"{cid}@{wl}"
                    if is_reference and registry.get(key) is not None:
                        continue
                    registry.add(result.card)
                    logger.info(
                        f"  Imported {result.card.qualified_id} "
                        f"(stage={result.stage}, conf={result.confidence:.3f})"
                    )
                    if result.conflicts_total:
                        r, t = result.conflicts_resolved, result.conflicts_total
                        logger.info(f"    Conflicts: {r}/{t} resolved")
                else:
                    logger.warning(f"  No card from section in {name}.")
        except Exception as e:
            logger.error(f"  Failed to process {name}: {e}", exc_info=True)

    # Process individual card files first, then reference files (non-overwriting)
    for gf in individual_cards:
        _process_file(gf, is_reference=False)
    for gf in other_files:
        _process_file(gf, is_reference=True)

    _print_summary(registry)
    if args.save:
        registry.save(Path(args.save))
    return 0


async def import_from_local(args) -> int:
    """Import cards from a local directory."""
    from core.card.resolver.pipeline_orchestrator import CardImportPipeline
    from core.card.card_store import CardRegistry

    local_dir = Path(args.from_dir)
    if not local_dir.is_dir():
        logger.error(f"Directory not found: {local_dir}")
        return 1

    md_files = (
        list(local_dir.rglob("*.md"))
        + list(local_dir.rglob("*.txt"))
        + list(local_dir.rglob("*.gdoc"))
    )
    logger.info(f"Found {len(md_files)} markdown/text files in {local_dir}.")

    if args.dry_run:
        for f in md_files:
            logger.info(f"  {f.relative_to(local_dir)}")
        return 0

    pipeline = CardImportPipeline()
    registry = CardRegistry()
    if args.load:
        registry.load(Path(args.load))

    for fpath in md_files:
        rel = fpath.relative_to(local_dir)
        logger.info(f"Processing: {rel}")
        try:
            content = fpath.read_text(encoding="utf-8")
            sections = _split_card_content(content)
            for section in sections:
                result = pipeline.process(section, source_label=f"file://{fpath}")
                if result.card and result.card.card_id:
                    registry.add(result.card)
                    logger.info(
                        f"  Imported {result.card.qualified_id} "
                        f"(stage={result.stage}, conf={result.confidence:.3f})"
                    )
                else:
                    logger.warning(f"  No card from section in {rel}.")
        except Exception as e:
            logger.error(f"  Failed to process {rel}: {e}", exc_info=True)

    _print_summary(registry)
    if args.save:
        registry.save(Path(args.save))
    return 0


def _print_summary(registry) -> None:
    """Print import summary."""
    cards = registry.list_all()
    total = len(cards)
    by_type = {}
    for c in cards:
        t = getattr(c, "card_type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1

    print("\n" + "=" * 50)
    print(f"IMPORT SUMMARY: {total} card(s) in registry")
    print("-" * 50)
    for t, count in sorted(by_type.items(), key=lambda x: str(x[0])):
        print(f"  {t}: {count}")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Angela Card Import Runner")
    parser.add_argument("--dry-run", action="store_true", help="List files without importing")
    parser.add_argument("--from-dir", help="Import from local directory instead of Drive")
    parser.add_argument("--folder", default="卡片堆", help="Google Drive folder name (default: 卡片堆)")
    parser.add_argument("--save", help="Save registry to JSON file after import")
    parser.add_argument("--load", help="Load existing registry from JSON file before import")
    args = parser.parse_args()

    if args.from_dir:
        exit_code = asyncio.run(import_from_local(args))
    else:
        exit_code = asyncio.run(import_from_drive(args))

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
