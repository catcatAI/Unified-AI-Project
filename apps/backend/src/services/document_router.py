"""
ANGELA-MATRIX: [L3] [β] [B] [L2]
DocumentRouter — handles document/card intents.
Reads files from a directory, processes them with LLM, and writes structured output.
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


def _extract_card_ids(content: str) -> Set[str]:
    """Extract all unique card IDs like CC-01, RC-06, NAT-01 from text."""
    ids = re.findall(r'\b([A-Z]+-\d+(?:-[A-Z])?)\b', content)
    return set(ids)


def _extract_card_ids_from_files(files: List[Path]) -> Dict[str, Dict[str, Any]]:
    """Pre-scan all files for card IDs and names to build a baseline inventory."""
    card_data: Dict[str, Dict[str, Any]] = {}
    for fpath in files:
        try:
            content = fpath.read_text(encoding="utf-8")
        except Exception:
            continue
        ids = _extract_card_ids(content)
        for id_ in ids:
            if id_ not in card_data:
                card_data[id_] = {"files": [], "name": "", "type": id_.split("-")[0]}
            card_data[id_]["files"].append(fpath.name)
        # Try to extract name following ID
        name_matches = re.findall(r'([A-Z]+-\d+(?:-[A-Z])?)\s+([^\n]+)', content)
        for id_, name in name_matches:
            if id_ in card_data:
                clean = name.strip()[:80]
                if clean and len(card_data[id_]["name"]) < len(clean):
                    card_data[id_]["name"] = clean
    return card_data


async def handle_document_intent(
    user_message: str,
    chat_svc: Any,
    user_name: str = "User",
) -> Dict[str, Any]:
    """
    Handle document/card processing intents.
    
    Improved version:
    1. Pre-scans all files for card IDs programmatically (baseline)
    2. Batches files and sends to LLM for analysis (Chinese prompts, more content)
    3. Generates structured summary document
    4. Writes output with verification against baseline
    """
    # Determine source directory
    path_match = re.search(r'[A-Za-z]:\\[^\s"\']+|data/[^\s]+|[A-Za-z]:/[^\s]+', user_message)
    source_dir = path_match.group(0) if path_match else ""
    
    CARD_DIR = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..", "data", "card_pile_downloaded"
    )
    CARD_DIR = os.path.abspath(CARD_DIR)
    
    if not source_dir:
        source_dir = CARD_DIR
    
    output_match = re.search(r'輸出到[：:]\s*([^\s]+)', user_message)
    if output_match:
        output_dir = output_match.group(1)
    else:
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
    
    # Step A: Pre-scan all files for card IDs (baseline inventory)
    logger.info(f"Pre-scanning {len(files)} files for card IDs...")
    baseline = _extract_card_ids_from_files(files)
    logger.info(f"Found {len(baseline)} unique card IDs in baseline scan")
    
    # Group baseline by type
    by_type: Dict[str, List[Tuple[str, str]]] = {}
    for id_, info in sorted(baseline.items(), key=lambda x: (x[1]["type"], x[0])):
        t = info["type"]
        if t not in by_type:
            by_type[t] = []
        by_type[t].append((id_, info["name"]))
    
    # Build a baseline reference text to include in final prompt
    baseline_lines = []
    for t in sorted(by_type.keys()):
        baseline_lines.append(f"\n=== {t} ({len(by_type[t])} cards) ===")
        for id_, name in by_type[t]:
            baseline_lines.append(f"  {id_}: {name}")
    baseline_text = "\n".join(baseline_lines)
    
    # Step B: Process files in batches with LLM
    all_results = []
    batch_size = 3  # Smaller batches = more content per file
    max_chars_per_file = 4000  # Increased from 2000
    
    total_batches = (len(files) + batch_size - 1) // batch_size
    
    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]
        batch_num = i // batch_size + 1
        batch_text_parts = []
        
        for f in batch:
            content = await _read_file_content(f)
            # Get first 4000 chars plus any card IDs in the rest
            head = content[:max_chars_per_file]
            tail_ids = set()
            if len(content) > max_chars_per_file:
                tail_ids = _extract_card_ids(content[max_chars_per_file:])
            
            fname = f.stem[:60]
            part = f"\n--- 檔案: {fname} ---\n{head}\n"
            if tail_ids:
                part += f"[後段出現的卡片ID: {', '.join(sorted(tail_ids))}]\n"
            batch_text_parts.append(part)
        
        batch_text = "".join(batch_text_parts)
        
        # Use Chinese prompts for better extraction of Chinese card content
        try:
            prompt = (
                f"請分析以下卡片檔案（第 {batch_num}/{total_batches} 批）：\n"
                f"{batch_text}\n\n"
                f"請從這些檔案中提取所有卡片資料，輸出格式為：\n"
                f"1. 卡片ID（如 CC-01, RC-06 等）\n"
                f"2. 卡片名稱\n"
                f"3. 卡片類型（角色卡/規則卡/組織卡/國家卡/場景卡/技能卡等）\n"
                f"4. 關鍵屬性（種族、性別、能力值等）\n"
                f"5. 與其他卡片的關聯\n\n"
                f"請確保列出該批次中出現的 **所有** 卡片ID，不要遺漏任何一張。"
            )
            text = await chat_svc.generate_text(prompt, max_tokens=1536, temperature=0.3)
            if text:
                all_results.append(text)
                # Also parse IDs from LLM response to cross-check
                llm_ids = _extract_card_ids(text)
                logger.info(f"Batch {batch_num}: LLM found {len(llm_ids)} card IDs")
        except Exception as e:
            logger.warning(f"Batch {batch_num} LLM analysis failed: {e}")
            all_results.append(f"[第 {batch_num} 批分析失敗]")
        
        await asyncio.sleep(0.5)
    
    # Write raw batch results as reference
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    raw_content = "\n\n---\n\n".join(all_results)
    await _write_output_file(output_path / "批次分析原始輸出.md", f"# 批次分析原始輸出\n\n共 {len(all_results)} 批次\n\n{raw_content}")
    
    # Step C: Generate final consolidated document
    combined_analysis = "\n\n---\n\n".join(all_results)
    
    # Count unique card IDs from LLM responses
    all_llm_ids = set()
    for result in all_results:
        all_llm_ids |= _extract_card_ids(result)
    
    final_prompt = (
        f"你是一個卡片遊戲開發文件生成助手。以下是從 {len(files)} 個卡片檔案中提取的批次分析結果。\n\n"
        f"{combined_analysis}\n\n"
        f"此外，以下是透過程式預先掃描到的 {len(baseline)} 張卡片基準清單（包含ID和名稱）：\n"
        f"```\n{baseline_text}\n```\n\n"
        f"請根據以上資訊，生成一份完整的卡片遊戲開發文件，要求如下：\n"
        f"1. **完整卡片索引**：按類型分組列出所有卡片（ID、名稱、類型、關鍵屬性）\n"
        f"2. **確保不遺漏**：基準清單中有 {len(baseline)} 張卡片，請確認你的索引包含全部\n"
        f"3. **衝突檢測**：找出卡片之間的矛盾或重疊\n"
        f"4. **缺失欄位補充**：建議需要補齊的資料欄位\n"
        f"5. **卡片關聯**：列出卡片之間的關聯關係\n\n"
        f"請用繁體中文輸出，格式為結構化的 Markdown 文檔。"
    )
    
    try:
        final_text = await chat_svc.generate_text(final_prompt, max_tokens=4096, temperature=0.3)
    except Exception as e:
        logger.error(f"Final document generation failed: {e}")
        final_text = f"# 卡片遊戲開發文件\n\n*生成失敗：{e}*"
    
    # Write main document
    index_doc = f"""# 卡片遊戲開發文件

## 生成資訊
- **來源**: {source_dir}
- **檔案數量**: {len(files)}
- **程式掃描卡片數**: {len(baseline)}
- **生成時間**: {datetime.datetime.now().isoformat()}

---

{final_text}
"""
    await _write_output_file(output_path / "卡片開發文件.md", index_doc)
    
    # Write the baseline inventory as a standalone reference
    inventory = f"""# 卡片基準清單（程式掃描）

## 統計
- **總卡片數**: {len(baseline)}
- **卡片類型數**: {len(by_type)}
- **檔案數**: {len(files)}
- **掃描時間**: {datetime.datetime.now().isoformat()}

## 按類型分類

"""
    for t in sorted(by_type.keys()):
        cards = by_type[t]
        inventory += f"### {t} ({len(cards)} 張)\n\n"
        for id_, name in cards:
            info = baseline[id_]
            file_list = ", ".join(sorted(set(info["files"]))[:3])
            name_display = name if name else "（名稱未找到）"
            inventory += f"| {id_} | {name_display} | {file_list} |\n"
        inventory += "\n"
    
    await _write_output_file(output_path / "卡片基準清單.md", inventory)
    
    # Write a simple file index
    cards_summary = f"""# 檔案索引

## 檔案清單 ({len(files)} 個檔案)

"""
    for i, f in enumerate(files, 1):
        first_line = (await _read_file_content(f)).split('\n')[0][:80]
        cards_summary += f"{i:3d}. **{f.stem}** — {first_line}\n"
    
    await _write_output_file(output_path / "檔案索引.md", cards_summary)
    
    # Verify completeness
    llm_ids_in_doc = _extract_card_ids(final_text)
    missing_in_llm = set(baseline.keys()) - llm_ids_in_doc
    extra_in_llm = llm_ids_in_doc - set(baseline.keys())
    
    verification = f"""# 驗證報告

## 數量對比
- **程式基準卡片數**: {len(baseline)}
- **LLM 最終文件中出現的卡片ID**: {len(llm_ids_in_doc)}
- **批次分析中出現的卡片ID**: {len(all_llm_ids)}

## 缺失卡片（基準有但 LLM 文件中沒有）
"""
    if missing_in_llm:
        for id_ in sorted(missing_in_llm):
            info = baseline[id_]
            verification += f"- {id_}: {info['name']} (出現在 {', '.join(sorted(set(info['files'])))})\n"
    else:
        verification += "- 無缺失 ✅\n"
    
    verification += f"\n## 額外卡片（LLM 文件中有但基準沒有的）\n"
    if extra_in_llm:
        for id_ in sorted(extra_in_llm):
            verification += f"- {id_}\n"
    else:
        verification += "- 無額外卡片 ✅\n"
    
    await _write_output_file(output_path / "驗證報告.md", verification)
    
    return {
        "response_text": (
            f"✅ 已完成 {len(files)} 個檔案的處理！\n\n"
            f"📊 統計：\n"
            f"   - 程式掃描卡片數：{len(baseline)} 張\n"
            f"   - LLM 批次分析卡片ID：{len(all_llm_ids)} 張\n"
            f"   - 卡片類型：{len(by_type)} 種\n"
            f"\n"
            f"📄 輸出到 {output_dir}：\n"
            f"   - 卡片開發文件.md（完整文檔）\n"
            f"   - 卡片基準清單.md（程式掃描基準）\n"
            f"   - 批次分析原始輸出.md（各批次原始分析）\n"
            f"   - 驗證報告.md（完整性比對）\n"
            f"   - 檔案索引.md（檔案清單）\n"
            f"\n"
            f"{'⚠️ ' + str(len(missing_in_llm)) + ' 張卡片在 LLM 文件中缺失，請查看驗證報告。' if missing_in_llm else '✅ 所有卡片均已包含！'}"
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
