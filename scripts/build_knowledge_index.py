#!/usr/bin/env python3
"""Build the offline knowledge index from a public Wikipedia dump.

WHY this exists
---------------
The `facts` dimension answers questions about the world, and the curated
knowledge store only covers a few dozen subjects. Growing it by hand from the
evaluation questions would be teaching the test; ingesting a **general public
corpus** is what a learner actually does.

This script streams a MediaWiki dump (Simple English Wikipedia by default),
keeps the lead paragraph of every article, and writes a SQLite FTS5 index.
Nothing here knows about any benchmark: the input is the dump, the output is
an encyclopedia.

Usage:
    python3 scripts/download_knowledge_corpus.py     # fetch the dump first
    python3 scripts/build_knowledge_index.py         # build data/knowledge/wiki.sqlite
    python3 scripts/build_knowledge_index.py --check # verify the index exists
"""

from __future__ import annotations

import argparse
import bz2
import html
import re
import sqlite3
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DUMP = REPO_ROOT / "data" / "knowledge" / "simplewiki-latest-pages-articles.xml.bz2"
DEFAULT_DB = REPO_ROOT / "data" / "knowledge" / "wiki.sqlite"
SOURCE = "https://dumps.wikimedia.org/simplewiki/"
LICENSE = "CC BY-SA 4.0 (Simple English Wikipedia contributors)"

MAX_BODY = 1200
MIN_BODY = 40

_REF = re.compile(r"<ref[^>]*?/>|<ref[^>]*?>.*?</ref>", re.DOTALL | re.IGNORECASE)
_TAG = re.compile(r"<[^>]+>")
_LINK = re.compile(r"\[\[(?:[^\]|]*\|)?([^\]]+)\]\]")
_EXT_LINK = re.compile(r"\[https?://[^\]]*\]")
_QUOTES = re.compile(r"'{2,5}")
_SPACES = re.compile(r"[ \t\u00a0]+")

_SKIP_PREFIXES = (
    "{{",
    "|",
    "}}",
    "{|",
    "|}",
    "!",
    "*",
    "#",
    ":",
    ";",
    "==",
    "[[file:",
    "[[image:",
    "[[category:",
    "[[wikt:",
    "[[commons:",
    "<",
    "__",
)


_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_FILE_LINK = re.compile(r"\[\[(?:file|image|category|wikt|commons):[^\]]*\]\]", re.IGNORECASE)


def _strip_balanced(text: str) -> str:
    """Remove wiki templates and tables, balancing nested braces.

    Templates span lines (infoboxes, taxoboxes), so a line-based filter leaves
    their bodies behind -- that is how an article's lead became "pKa of water
    is incorrect.}}" and two articles disappeared entirely. Depth counting is
    the only correct way to remove them.
    """
    out: list[str] = []
    i = 0
    length = len(text)
    while i < length:
        if text.startswith("{{", i):
            depth = 0
            while i < length:
                if text.startswith("{{", i):
                    depth += 1
                    i += 2
                elif text.startswith("}}", i):
                    depth -= 1
                    i += 2
                    if depth == 0:
                        break
                else:
                    i += 1
            continue
        if text.startswith("{|", i):
            end = text.find("|}", i)
            i = length if end < 0 else end + 2
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def _clean(text: str) -> str:
    """Wikitext -> plain text (markup removed, not rewritten)."""
    text = _COMMENT.sub("", text)
    text = _strip_balanced(text)
    text = _REF.sub("", text)
    text = _FILE_LINK.sub("", text)
    text = _LINK.sub(r"\1", text)
    text = _EXT_LINK.sub("", text)
    text = html.unescape(text)  # before tag stripping: "&lt;br&gt;" is a tag
    text = _TAG.sub("", text)
    text = _QUOTES.sub("", text)
    return _SPACES.sub(" ", text).strip()


def _lead(wikitext: str) -> str:
    """The first prose paragraph of the article.

    Templates are removed *before* the line walk: an infobox spans lines and
    its inner fields look like prose ("A commonly quoted value ..."), so a
    line-based filter would start the lead inside it.
    """
    text = _strip_balanced(_COMMENT.sub("", wikitext))
    collected: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        lowered = stripped.lower()
        if lowered.startswith("==") and collected:
            break  # the intro section ends at the first heading
        if any(lowered.startswith(prefix) for prefix in _SKIP_PREFIXES):
            continue
        cleaned = _clean(stripped)
        if cleaned:
            collected.append(cleaned)
        if sum(len(part) for part in collected) >= MAX_BODY:
            break
    return _clean(" ".join(collected))[:MAX_BODY]


def build(dump: Path = DEFAULT_DUMP, db_path: Path = DEFAULT_DB) -> int:
    if not dump.is_file():
        print(f"missing dump: {dump}")
        print("run: python3 scripts/download_knowledge_corpus.py")
        return 2
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA journal_mode=OFF")
    connection.execute("PRAGMA synchronous=OFF")
    connection.execute(
        "CREATE VIRTUAL TABLE pages USING fts5(title, body, "
        "tokenize='unicode61 remove_diacritics 2')"
    )
    connection.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")

    page_open = re.compile(r"<page>")
    title_re = re.compile(r"<title>(.*?)</title>", re.DOTALL)
    ns_re = re.compile(r"<ns>(\d+)</ns>")
    text_re = re.compile(r"<text[^>]*>(.*?)</text>", re.DOTALL)

    started = time.time()
    kept = 0
    seen = 0
    pending: list[str] = []
    in_page = False

    def flush() -> int:
        nonlocal kept
        chunk = "".join(pending)
        pending.clear()
        title_match = title_re.search(chunk)
        if not title_match:
            return 0
        ns_match = ns_re.search(chunk)
        if ns_match and ns_match.group(1) != "0":
            return 0
        if "<redirect" in chunk[: chunk.find("<text") if "<text" in chunk else len(chunk)]:
            return 0
        text_match = text_re.search(chunk)
        if not text_match:
            return 0
        body = _lead(text_match.group(1))
        if len(body) < MIN_BODY:
            return 0
        title = html.unescape(title_re.sub(r"\1", title_match.group(0))).strip()
        connection.execute("INSERT INTO pages (title, body) VALUES (?, ?)", (title, body))
        kept += 1
        return 1

    with bz2.open(dump, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            seen += 1
            if not in_page:
                if page_open.search(line):
                    in_page = True
                    pending.append(line[line.find("<page>") :])
                continue
            pending.append(line)
            if "</page>" in line:
                in_page = False
                flush()
                if kept and kept % 20000 == 0:
                    connection.commit()
                    print(f"  {kept} articles ({seen} lines, {time.time() - started:.0f}s)")
        if in_page:
            flush()

    connection.execute("INSERT INTO meta VALUES ('source', ?)", (SOURCE,))
    connection.execute("INSERT INTO meta VALUES ('license', ?)", (LICENSE,))
    connection.execute("INSERT INTO meta VALUES ('built_at', ?)", (time.strftime("%Y-%m-%d"),))
    connection.execute("INSERT INTO meta VALUES ('articles', ?)", (str(kept),))
    connection.commit()
    connection.execute("INSERT INTO pages(pages) VALUES('optimize')")
    connection.commit()
    connection.close()
    print(f"indexed {kept} articles in {time.time() - started:.0f}s -> {db_path}")
    return 0 if kept else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", type=Path, default=DEFAULT_DUMP)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--check", action="store_true", help="verify the index exists")
    args = parser.parse_args()
    if args.check:
        if not args.db.is_file():
            print(f"missing index: {args.db}")
            return 1
        connection = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
        try:
            count = connection.execute("SELECT count(*) FROM pages").fetchone()[0]
        finally:
            connection.close()
        print(f"index ok: {count} articles ({args.db})")
        return 0
    return build(args.dump, args.db)


if __name__ == "__main__":
    sys.exit(main())
