"""
ANGELA-MATRIX: [L3] [β] [B] [L2]
DocumentRouter — handles document/card intents.
Reads files from a directory, processes them with LLM, and writes structured output.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import datetime

from core.utils import safe_error

logger = logging.getLogger(__name__)


async def _list_text_files(directory: str) -> List[Path]:
    """List all text/markdown files in a directory (non-recursive)."""
    path = Path(directory)
    if not path.exists() or not path.is_dir():
        return []
    files = []
    for ext in (".md", ".txt", ".json", ".csv", ".yaml", ".yml", ".xml", ".html"):
        files.extend(sorted(path.glob(f"*{ext}")))
    return files


async def _read_file_content(file_path: Path) -> str:
    """Read file content with error handling."""
    try:
        return file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"Failed to read {file_path}: {e}")
        return f"[Error reading {file_path.name}: {safe_error(e)}]"


async def _write_output_file(file_path: Path, content: str) -> bool:
    """Write content to a file, creating parent directories as needed."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        logger.info(f"Written {len(content)} chars to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write {file_path}: {e}")
        return False


async def handle_document_intent(
    user_message: str,
    chat_svc: Any,
    user_name: str = "User",
) -> Dict[str, Any]:
    """
    Handle document/card processing intents.
    
    Steps:
    1. Extract directory path from message (or use default card pile)
    2. Read all text files from the directory
    3. For each file (or batches), send to LLM for analysis
    4. Generate a structured summary document
    5. Write output to the specified location
    
    Returns a response dict compatible with chat_routes format.
    """
    # Determine source directory
    # Check if user specified a path in the message
    import re
    path_match = re.search(r'[A-Za-z]:\\[^\s"\']+', user_message)
    source_dir = path_match.group(0) if path_match else ""
    
    # Default to card pile if no path specified and keywords match
    CARD_DIR = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..", "data", "card_pile_downloaded"
    )
    CARD_DIR = os.path.abspath(CARD_DIR)
    
    if not source_dir:
        source_dir = CARD_DIR
    
    # Determine output directory
    output_match = re.search(r'輸出到[：:]\s*([^\s]+)', user_message)
    if output_match:
        output_dir = output_match.group(1)
    else:
        # Default output: next to card pile or a default location
        output_dir = r"G:\我的雲端硬碟\卡片開發"
    
    logger.info(f"DocumentRouter: source={source_dir}, output={output_dir}")
    
    # Read files
    files = await _list_text_files(source_dir)
    if not files:
        return {
            "response_text": f"在 {source_dir} 中找不到任何可讀取的文檔。",
            "source": "document_router",
            "route": "document_router",
        }
    
    # If there are many files, process in batches
    all_results = []
    batch_size = 5  # Send 5 files per LLM call
    
    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]
        batch_text = ""
        for f in batch:
            content = await _read_file_content(f)
            fname = f.stem[:50]
            batch_text += f"\n--- File: {fname} ---\n{content[:2000]}\n"
        
        # Ask LLM to analyze this batch (use generate_text to bypass memory/template matching)
        try:
            prompt = (
                f"Analyze the following card game documents (batch {i//batch_size + 1}/{(len(files)-1)//batch_size + 1}):\n"
                f"{batch_text}\n\n"
                f"For each document, identify: card type, name, key attributes, relationships, and any conflicts.\n"
                f"Format your response as structured notes."
            )
            text = await chat_svc.generate_text(prompt, max_tokens=1024, temperature=0.3)
            if text:
                all_results.append(text)
        except Exception as e:
            logger.warning(f"Batch {i//batch_size + 1} LLM analysis failed: {e}")
            all_results.append(f"[Batch {i//batch_size + 1} analysis unavailable]")
        
        # Small delay between batches
        await asyncio.sleep(0.5)
    
    # Generate the final consolidated document
    combined_analysis = "\n\n".join(all_results)
    
    final_prompt = (
        f"Based on the following analysis of {len(files)} card documents, "
        f"create a comprehensive card game development document.\n\n"
        f"{combined_analysis}\n\n"
        f"Please create:\n"
        f"1. A complete INDEX of all cards organized by category\n"
        f"2. For each card, list: ID, Name, Type, and Key Attributes\n"
        f"3. Note any conflicts or inconsistencies found\n"
        f"4. Suggest missing fields that should be added\n\n"
        f"Format as a well-structured markdown document."
    )
    
    try:
        final_text = await chat_svc.generate_text(final_prompt, max_tokens=2048, temperature=0.3)
    except Exception as e:
        logger.error(f"Final document generation failed: {e}")
        final_text = f"# Card Game Development Document\n\n*Generation failed: {e}*\n\n## Batch Analyses\n\n{combined_analysis}"
    
    # Write output files
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Write the main document
    index_doc = f"""# 卡片遊戲開發文件

## 生成資訊
- **來源**: {source_dir}
- **卡片數量**: {len(files)}
- **生成時間**: {datetime.datetime.now().isoformat()}

---

{final_text}
"""
    await _write_output_file(output_path / "卡片開發文件.md", index_doc)
    
    # Also write individual card summaries
    cards_summary = f"""# 卡片清單

## 文件索引 ({len(files)} 個檔案)

"""
    for i, f in enumerate(files, 1):
        first_line = (await _read_file_content(f)).split('\n')[0][:80]
        cards_summary += f"{i:3d}. **{f.stem}** — {first_line}\n"
    
    await _write_output_file(output_path / "卡片索引.md", cards_summary)
    
    return {
        "response_text": (
            f"✅ 已完成 {len(files)} 個文件的處理！\n\n"
            f"📄 開發文檔已輸出到：{output_dir}\n"
            f"   - 卡片開發文件.md（完整文檔）\n"
            f"   - 卡片索引.md（文件清單）\n\n"
            f"LLM 批次分析：{len(all_results)}/{len(files)} 文件處理成功。"
        ),
        "source": "document_router",
        "route": "document_router",
    }


async def try_intent_routing(
    user_message: str,
    chat_svc: Any,
    user_name: str = "User",
    context: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Try to route a message based on IntentRegistry detection.
    Returns a response dict if handled, None if should fall through to normal pipeline.
    """
    try:
        from core.intent_registry import IntentRegistry
        
        registry = IntentRegistry()
        intent_name, confidence = registry.detect(user_message)
        
        if intent_name is None or confidence < 0.3:
            return None
        
        logger.info(f"IntentRegistry detected: {intent_name} (confidence={confidence:.2f})")
        
        # Route based on intent
        if intent_name in ("document", "character_card", "google_drive"):
            if context:
                context["_detected_intent"] = intent_name
                context["_intent_confidence"] = confidence
            
            return await handle_document_intent(user_message, chat_svc, user_name)
        
        # Fall through for other intents (math, code, etc. — handled by existing pipeline)
        if context:
            context["_detected_intent"] = intent_name
            context["_intent_confidence"] = confidence
        
    except Exception as e:
        logger.debug(f"Intent routing unavailable: {e}")
    
    return None


__all__ = ["try_intent_routing", "handle_document_intent"]
