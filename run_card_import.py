"""
Angela Card Import Runner
=========================
Imports cards from Google Drive "卡片堆" folder through the CardImportPipeline.

Usage:
    python run_card_import.py                    # Full import with Drive auth
    python run_card_import.py --dry-run          # List files without importing
    python run_card_import.py --from-dir <path>  # Import from local directory
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

# Ensure backend src is in path
BACKEND_SRC = Path(__file__).resolve().parent / "apps" / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("card_import")


async def import_from_drive(args) -> int:
    """Import cards from Google Drive."""
    from integrations.google_drive_service import GoogleDriveService

    service = GoogleDriveService._create()
    logger.info("Authenticating with Google Drive...")
    if not service.authenticate():
        logger.error("Authentication failed. Run again to open browser.")
        return 1

    folder_name = args.folder or "卡片堆"
    logger.info(f"Listing files in '{folder_name}'...")

    files = service.list_files(query=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'")
    if not files:
        logger.error(f"Folder '{folder_name}' not found in Google Drive.")
        return 1

    folder_id = files[0]["id"]
    gdoc_files = service.list_files(query=f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.document'")

    logger.info(f"Found {len(gdoc_files)} Google Docs in '{folder_name}'.")

    if args.dry_run:
        for f in gdoc_files:
            logger.info(f"  [{f.get('id', '?')}] {f.get('name', '?')}")
        return 0

    from core.card.resolver.pipeline_orchestrator import CardImportPipeline
    from core.card.card_store import CardRegistry

    pipeline = CardImportPipeline()
    registry = CardRegistry()

    for gf in gdoc_files:
        name = gf.get("name", "unnamed")
        logger.info(f"Processing: {name}")
        try:
            content = service.download_file_content(gf["id"])
            if not content:
                logger.warning(f"  Empty content for {name}, skipping.")
                continue
            result = pipeline.run(content, source=f"gdrive://{gf['id']}")
            if result.success:
                for card in result.cards:
                    registry.add(card)
                logger.info(f"  Imported {len(result.cards)} card(s), {len(result.conflicts)} conflict(s).")
            else:
                logger.warning(f"  Pipeline returned no cards for {name}.")
        except Exception as e:
            logger.error(f"  Failed to process {name}: {e}", exc_info=True)

    _print_summary(registry)
    return 0


async def import_from_local(args) -> int:
    """Import cards from a local directory."""
    from core.card.resolver.pipeline_orchestrator import CardImportPipeline
    from core.card.card_store import CardRegistry

    local_dir = Path(args.from_dir)
    if not local_dir.is_dir():
        logger.error(f"Directory not found: {local_dir}")
        return 1

    md_files = list(local_dir.rglob("*.md")) + list(local_dir.rglob("*.txt"))
    logger.info(f"Found {len(md_files)} markdown/text files in {local_dir}.")

    if args.dry_run:
        for f in md_files:
            logger.info(f"  {f.relative_to(local_dir)}")
        return 0

    pipeline = CardImportPipeline()
    registry = CardRegistry()

    for fpath in md_files:
        rel = fpath.relative_to(local_dir)
        logger.info(f"Processing: {rel}")
        try:
            content = fpath.read_text(encoding="utf-8")
            result = pipeline.run(content, source=f"file://{fpath}")
            if result.success:
                for card in result.cards:
                    registry.add(card)
                logger.info(f"  Imported {len(result.cards)} card(s), {len(result.conflicts)} conflict(s).")
            else:
                logger.warning(f"  Pipeline returned no cards for {rel}.")
        except Exception as e:
            logger.error(f"  Failed to process {rel}: {e}", exc_info=True)

    _print_summary(registry)
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
    for t, count in sorted(by_type.items()):
        print(f"  {t}: {count}")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Angela Card Import Runner")
    parser.add_argument("--dry-run", action="store_true", help="List files without importing")
    parser.add_argument("--from-dir", help="Import from local directory instead of Drive")
    parser.add_argument("--folder", default="卡片堆", help="Google Drive folder name (default: 卡片堆)")
    args = parser.parse_args()

    if args.from_dir:
        exit_code = asyncio.run(import_from_local(args))
    else:
        exit_code = asyncio.run(import_from_drive(args))

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
