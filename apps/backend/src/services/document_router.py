"""
ANGELA-MATRIX: [L3] [β] [B] [L2]
DocumentRouter — generic tiered document processor.
Tier 1: Local models (ED3N/GARDEN) — fast, autonomous.
Tier 2: LLM fallback — only when local confidence is low.
Tier 3: Learn from LLM → local handles similar tasks next time.

Operation types with distinct information retention rates:
  - organize  (整理):   retain 80-100% — restructure formatting, keep all content
  - summarize (總結):   retain 10-20%  — extract key points, link to original
  - optimize  (優化):   retain 60-80%  — trim excess, keep core content intact
  - analyze   (分析):   retain 100%   — extract structure/patterns, add insight
  - categorize(分類):   retain 100%   — sort into categories
  - list      (列出):   retain 100%   — enumerate files
"""

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import datetime

from core.utils import safe_error

logger = logging.getLogger(__name__)

_OPERATIONS = {
    "organize":    {"label": "整理", "retention": (0.80, 1.00), "desc": "重構格式，保留所有內容"},
    "summarize":   {"label": "總結", "retention": (0.10, 0.20), "desc": "提取關鍵要點，附原始連結"},
    "optimize":    {"label": "優化", "retention": (0.60, 0.80), "desc": "裁剪多餘內容，保留核心"},
    "analyze":     {"label": "分析", "retention": (1.00, 1.00), "desc": "提取結構/模式，增加洞察"},
    "categorize":  {"label": "分類", "retention": (1.00, 1.00), "desc": "按類別分類歸檔"},
    "list":        {"label": "列出", "retention": (1.00, 1.00), "desc": "枚舉檔案清單"},
}

_EXAMPLES_DIR = Path(__file__).parent.parent.parent.parent / "data"
_EXAMPLES_PATH = _EXAMPLES_DIR / "document_examples.json"


# ═══════════════════════════════════════════════
# File utilities
# ═══════════════════════════════════════════════

async def _list_text_files(directory: str) -> List[Path]:
    path = Path(directory)
    if not path.exists() or not path.is_dir():
        return []
    files = []
    for ext in (".md", ".txt", ".json", ".csv", ".yaml", ".yml", ".xml", ".html"):
        files.extend(sorted(path.glob(f"*{ext}")))
    return files


async def _read_file_content(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"Failed to read {file_path}: {e}")
        return f"[Error reading {file_path.name}: {safe_error(e)}]"


async def _write_output_file(file_path: Path, content: str) -> bool:
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        logger.info(f"Written {len(content)} chars to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write {file_path}: {e}")
        return False


def _parse_task_type(user_message: str) -> Tuple[str, str]:
    msg_lower = user_message.lower()
    if any(k in msg_lower for k in ("優化", "optimize", "精簡", "潤飾", "refine")):
        return "optimize", "優化文件"
    if any(k in msg_lower for k in ("整理", "organize", "分類", "歸檔", "sort", "classify", "歸納")):
        return "organize", "整理文件"
    if any(k in msg_lower for k in ("摘要", "總結", "summarize", "summary", "濃縮")):
        return "summarize", "摘要文件"
    if any(k in msg_lower for k in ("分析", "analyze", "解析", "提取", "extract")):
        return "analyze", "分析文件"
    if any(k in msg_lower for k in ("列出", "list", "索引", "index", "目錄")):
        return "list", "列出文件"
    return "summarize", "摘要文件"


def _extract_source_dir(user_message: str) -> str:
    path_match = re.search(r'[A-Za-z]:\\[^\s"\']+|data/[^\s]+|[A-Za-z]:/[^\s]+', user_message)
    return path_match.group(0) if path_match else ""


# ═══════════════════════════════════════════════
# Example store (learned from LLM, reused by local)
# ═══════════════════════════════════════════════

_examples_cache: Optional[Dict[str, List[Dict]]] = None


def _load_examples() -> Dict[str, List[Dict]]:
    global _examples_cache
    if _examples_cache is not None:
        return _examples_cache
    try:
        _EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)
        if _EXAMPLES_PATH.exists():
            with open(_EXAMPLES_PATH, "r", encoding="utf-8") as f:
                _examples_cache = json.load(f)
        else:
            _examples_cache = {}
    except Exception as e:
        logger.debug(f"Failed to load document examples: {e}")
        _examples_cache = {}
    return _examples_cache


def _save_examples(examples: Dict[str, List[Dict]]) -> None:
    try:
        _EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)
        with open(_EXAMPLES_PATH, "w", encoding="utf-8") as f:
            json.dump(examples, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save document examples: {e}")


def _find_local_match(task_type: str, source_dir: str, files: List[Path]) -> Optional[Dict]:
    examples = _load_examples()
    task_examples = examples.get(task_type, [])
    if not task_examples:
        return None

    file_count = len(files)
    file_names = {f.name for f in files}
    for ex in task_examples:
        ex_files = set(ex.get("file_names", []))
        overlap = file_names & ex_files
        if len(overlap) >= min(file_count, ex.get("file_count", 0)) * 0.5:
            logger.info(f"Local match found for task '{task_type}' ({len(overlap)}/{file_count} files overlap)")
            return ex
    return None


# ═══════════════════════════════════════════════
# Tier 1: Local processing (ED3N / GARDEN)
# ═══════════════════════════════════════════════

async def _try_local_processing(
    user_message: str, task_type: str, source_dir: str, files: List[Path]
) -> Optional[Dict]:
    op = _OPERATIONS.get(task_type, _OPERATIONS["summarize"])
    retention_min, retention_max = op["retention"]
    retention_pct = f"{int(retention_min*100)}%～{int(retention_max*100)}%"
    retention_note = f"（保留率：{retention_pct}，{op['desc']}）"

    matched = _find_local_match(task_type, source_dir, files)
    if matched:
        return {
            "response_text": matched.get("response", f"已從先前經驗完成{op['label']}任務{retention_note}。"),
            "output_files": matched.get("output_files", []),
            "source": "document_router_local",
            "route": "document_router",
        }

    try:
        from ai.ed3n.ed3n_engine import ED3NEngine
        engine = ED3NEngine.get_instance()
        file_summaries = []
        for f in files[:5]:
            content = await _read_file_content(f)
            result = await engine.process(content[:2000], depth="shallow")
            if result and result.get("output"):
                file_summaries.append(f"{f.name}: {result['output'][:200]}")
        if file_summaries:
            summary = "\n".join(file_summaries)
            return {
                "response_text": f"【{op['label']}】目錄 {source_dir} 中有 {len(files)} 個文件 {retention_note}：\n\n{summary}",
                "source": "document_router_local",
                "route": "document_router",
            }
    except Exception as e:
        logger.debug(f"ED3N local processing unavailable: {e}")

    try:
        from ai.garden.garden_engine import GARDENEngine
        engine = GARDENEngine()
        file_summaries = []
        for f in files[:5]:
            content = await _read_file_content(f)
            result = await engine.process(content[:2000])
            if result and result.get("output"):
                file_summaries.append(f"{f.name}: {result['output'][:200]}")
        if file_summaries:
            summary = "\n".join(file_summaries)
            return {
                "response_text": f"【{op['label']}】目錄 {source_dir} 中有 {len(files)} 個文件 {retention_note}：\n\n{summary}",
                "source": "document_router_local",
                "route": "document_router",
            }
    except Exception as e:
        logger.debug(f"GARDEN local processing unavailable: {e}")

    return None


# ═══════════════════════════════════════════════
# Tier 2: LLM fallback
# ═══════════════════════════════════════════════

async def _try_llm_processing(
    user_message: str, task_type: str, source_dir: str, files: List[Path], chat_svc: Any
) -> Optional[Dict]:
    if not files:
        return None

    op = _OPERATIONS.get(task_type, _OPERATIONS["summarize"])
    task_label = op["label"]
    retention_min, retention_max = op["retention"]
    retention_pct = f"{int(retention_min*100)}%～{int(retention_max*100)}%"
    file_list_text = "\n".join(f"{i+1}. {f.name} ({f.stat().st_size}B)" for i, f in enumerate(files))

    try:
        prompt = (
            f"請{task_label}以下目錄中的文件。目錄：{source_dir}\n\n"
            f"文件清單（共 {len(files)} 個）：\n{file_list_text}\n\n"
            f"操作類型：{task_label}（{op['desc']}）\n"
            f"資訊保留率要求：原始內容的 {retention_pct} 必須保留。\n"
            f"⚠ 請嚴格遵循保留率，不要和其他操作類型（整理/總結/優化）混用。\n\n"
            f"請根據文件內容進行{task_label}，輸出結構化的 Markdown 報告。"
        )
        file_contents = []
        for f in files:
            content = await _read_file_content(f)
            file_contents.append(f"\n--- {f.name} ---\n{content[:3000]}")
        content_block = "".join(file_contents)

        full_prompt = (
            f"請{task_label}以下文件。\n\n"
            f"操作類型：{task_label}（{op['desc']}）\n"
            f"資訊保留率要求：原始內容的 {retention_pct} 必須保留。\n"
            f"⚠ 嚴禁將此操作與其他類型混淆。\n\n"
            f"文件內容：\n{content_block}\n\n"
            f"請輸出結構化的 Markdown 報告，包含每個文件的{task_label}結果。"
        )
        text = await chat_svc.generate_text(full_prompt, max_tokens=2048, temperature=0.3)
        if not text:
            return None

        return {
            "response_text": text,
            "source": "document_router_llm",
            "route": "document_router",
        }
    except Exception as e:
        logger.warning(f"LLM document processing failed: {e}")
        return None


# ═══════════════════════════════════════════════
# Tier 3: Learn from LLM output → local models
# ═══════════════════════════════════════════════

async def _learn_from_llm_output(
    task_type: str, source_dir: str, files: List[Path], llm_output: str
) -> None:
    op = _OPERATIONS.get(task_type, _OPERATIONS["summarize"])
    examples = _load_examples()
    if task_type not in examples:
        examples[task_type] = []
    examples[task_type].append({
        "operation": task_type,
        "label": op["label"],
        "retention_min": op["retention"][0],
        "retention_max": op["retention"][1],
        "description": op["desc"],
        "source_dir": source_dir,
        "file_names": [f.name for f in files],
        "file_count": len(files),
        "response": llm_output[:500],
        "timestamp": datetime.datetime.now().isoformat(),
    })
    if len(examples[task_type]) > 20:
        examples[task_type] = examples[task_type][-20:]
    _save_examples(examples)

    try:
        from ai.ed3n.ed3n_engine import ED3NEngine
        engine = ED3NEngine.get_instance()
        engine.learn_reflex(f"doc_{task_type}", llm_output[:200])
    except Exception:
        pass

    try:
        from ai.garden.garden_engine import GARDENEngine
        engine = GARDENEngine()
        for f in files[:3]:
            content = await _read_file_content(f)
            engine.learn_from_interaction(content[:1000], llm_output[:1000], confidence=0.5)
    except Exception:
        pass


# ═══════════════════════════════════════════════
# Main entry point
# ═══════════════════════════════════════════════

async def handle_document_intent(
    user_message: str,
    chat_svc: Any,
    user_name: str = "User",
) -> Dict[str, Any]:
    task_type, task_label = _parse_task_type(user_message)
    source_dir = _extract_source_dir(user_message)
    logger.info(f"DocumentRouter: task={task_type}, source={source_dir}")

    output_dir = ""
    output_match = re.search(r'輸出到[：:]\s*([^\s]+)', user_message)
    if output_match:
        output_dir = output_match.group(1)

    files = await _list_text_files(source_dir) if source_dir else []
    if not files and source_dir:
        return {
            "response_text": f"在 {source_dir} 中找不到任何可讀取的文檔。",
            "source": "document_router",
            "route": "document_router",
        }
    if not files:
        return {
            "response_text": "請指定要處理的目錄路徑。例如：「整理 data/docs/ 裡的文件」",
            "source": "document_router",
            "route": "document_router",
        }

    tier_result = None

    # Tier 1: Local
    tier_result = await _try_local_processing(user_message, task_type, source_dir, files)

    # Tier 2: LLM fallback (only if local returned low-quality or no result)
    if not tier_result:
        tier_result = await _try_llm_processing(user_message, task_type, source_dir, files, chat_svc)

    if not tier_result:
        op = _OPERATIONS.get(task_type, _OPERATIONS["summarize"])
        simple_list = "\n".join(f"- {f.name}" for f in files[:20])
        extra = f"\n...及其他 {len(files)-20} 個" if len(files) > 20 else ""
        tier_result = {
            "response_text": f"【{op['label']}】目錄 {source_dir} 中有 {len(files)} 個文件：\n{simple_list}{extra}",
            "source": "document_router",
            "route": "document_router",
        }

    # Tier 3: Learn from LLM output (if LLM was used)
    if tier_result.get("source") == "document_router_llm":
        await _learn_from_llm_output(task_type, source_dir, files, tier_result.get("response_text", ""))

    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        await _write_output_file(
            output_path / f"{task_label}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.md",
            tier_result.get("response_text", "")
        )

    return {
        "response_text": tier_result.get("response_text", "處理完成。"),
        "source": tier_result.get("source", "document_router"),
        "route": tier_result.get("route", "document_router"),
        "operation": task_type,
        "operation_label": _OPERATIONS.get(task_type, _OPERATIONS["summarize"])["label"],
    }


async def try_intent_routing(
    user_message: str,
    chat_svc: Any,
    user_name: str = "User",
    context: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    try:
        from core.intent_registry import IntentRegistry

        registry = IntentRegistry()
        intent_name, confidence = registry.detect(user_message)

        if intent_name is None or confidence < 0.3:
            return None

        logger.info(f"IntentRegistry detected: {intent_name} (confidence={confidence:.2f})")

        if intent_name in ("document", "character_card", "google_drive"):
            if context:
                context["_detected_intent"] = intent_name
                context["_intent_confidence"] = confidence
            return await handle_document_intent(user_message, chat_svc, user_name)

        if context:
            context["_detected_intent"] = intent_name
            context["_intent_confidence"] = confidence

    except Exception as e:
        logger.debug(f"Intent routing unavailable: {e}")

    return None


__all__ = ["try_intent_routing", "handle_document_intent"]
