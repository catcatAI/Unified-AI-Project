"""
ANGELA-MATRIX: [L3] [β] [B] [L0]
.gdoc reader — reads .gdoc shortcut files and exports content via Google Drive API.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from integrations.google_drive_service import get_drive_service

logger = logging.getLogger(__name__)


def read_gdoc_file(gdoc_path: str) -> Optional[str]:
    """
    Read a .gdoc shortcut file, extract the doc_id, and fetch the
    document content as plain text via the Google Drive API.

    Returns None if the file cannot be read or the export fails.
    """
    path = Path(gdoc_path)
    if not path.exists():
        logger.error(f".gdoc file not found: {gdoc_path}", exc_info=True)
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            meta = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to read .gdoc file {gdoc_path}: {e}", exc_info=True)
        return None

    doc_id = meta.get("doc_id")
    if not doc_id:
        url = meta.get("url", "")
        if "/d/" in url:
            doc_id = url.split("/d/")[1].split("/")[0]
    if not doc_id:
        logger.error(f"No doc_id found in .gdoc file: {gdoc_path}", exc_info=True)
        return None

    drive = get_drive_service()
    return drive.export_gdoc(doc_id)


__all__ = ["read_gdoc_file"]
