"""
DocumentBuilder — 多段生成 + 拼接系統
=====================================
用於需要超過單次 LLM 輸出的長文檔構建。

流程：
1. 接收任務描述 + 輸出格式
2. 查詢 TemplateLibrary 是否有已學習的格式（anchor_learning）
3. 將任務分成章節/段落
4. 每段獨立呼叫 LLM（最多 max_segments 段）
5. 拼接結果
6. 若有用戶回饋，學習該格式到 TemplateLibrary

設計原則：
- Angela 的 8D 軸狀態影響風格參數
- 結果透過 anchor_learning 持久化為格式模板
- 段數由 complexity 決定（高複雜度 → 段數增加）
"""

import asyncio
import json
import logging
import time
import uuid
import re
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, TYPE_CHECKING

logger = logging.getLogger(__name__)

try:
    from core.intent_registry import IntentRegistry
    _intent_registry = IntentRegistry()
except ImportError:
    _intent_registry = None

if TYPE_CHECKING:
    from core.autonomous.eta_axis_state import EtaAxisState


@dataclass
class DocSegment:
    index: int
    title: str
    prompt_suffix: str
    content: str = ""
    tokens: int = 0
    time_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class DocumentBuildResult:
    task_id: str
    full_text: str
    segments: List[DocSegment]
    total_segments: int
    successful_segments: int
    total_time_ms: float
    format_id: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentBuilder:
    """
    多段 LLM 生成 + 拼接器。
    支援格式學習（透過 TemplateLibrary）。
    支援 TRPG Codex 知識增強（查詢 HAMMemoryManager）。
    """

    def __init__(
        self,
        llm_generate_fn: Callable[..., Any],
        template_library: Optional[Any] = None,
        anchor_learning: Optional[Any] = None,
        memory_manager: Optional[Any] = None,
        max_segments: int = 8,
        tokens_per_segment: int = 512,
    ):
        self.llm_generate = llm_generate_fn
        self.template_library = template_library
        self.anchor_learning = anchor_learning
        self.memory_manager = memory_manager
        self.max_segments = max_segments
        self.tokens_per_segment = tokens_per_segment
        self._format_counter: int = 0
        self.eta_state: Optional["EtaAxisState"] = None
        self._segment_timeout_seconds: float = 15.0

    def _update_eta(self, execution_count_delta: int = 1) -> None:
        """Update eta_state after segment completion (B10: eta axis tracks execution load)."""
        if self.eta_state:
            self.eta_state.execution_count += execution_count_delta

    async def _load_fantasy_codex(self, query: str) -> Dict[str, Any]:
        """查詢 HAMMemoryManager 中的 TRPG Codex 數據（B6: 統一為唯一來源）"""
        if not self.memory_manager:
            return {}
        try:
            results = await self.memory_manager.query_core_memory(
                keywords=["trpg_codex", query],
                data_type_filter="trpg_codex",
                limit=10,
            )
            codex_data = {}
            for m in results:
                content = m.get("content", "")
                if "TRPG Knowledge" in content:
                    try:
                        json_str = content.split("TRPG Knowledge", 1)[1]
                        json_str = json_str.split("):", 1)[1] if "):" in json_str else json_str
                        codex_data = json.loads(json_str)
                    except (json.JSONDecodeError, IndexError):
                        pass
            return codex_data
        except Exception as e:
            logger.debug(f"[DocumentBuilder] Codex query failed: {e}")
            return {}

    def _load_format_from_memory(self, task_type: str) -> Optional[Dict[str, Any]]:
        """從 TemplateLibrary 查找已學習的輸出格式"""
        if not self.template_library:
            return None
        try:
            templates = self.template_library.get_by_category(task_type)
            if templates:
                best = templates[0]
                return {
                    "format_id": best.id,
                    "content": best.content,
                    "metadata": best.metadata,
                }
        except Exception as e:
            logger.debug(f"Format lookup failed: {e}")
        return None

    def _learn_format(
        self,
        task_type: str,
        user_query: str,
        result_text: str,
        segments: List[DocSegment],
    ) -> str:
        """將成功的輸出格式寫入 TemplateLibrary（透過 anchor_learning）

        B11 FIX: 每次成功都寫入會累積重複。新增 dedup 邏輯：
        - 相同 task_type + 相同關鍵字組合 → 視為重複，不寫入
        """
        if not self.template_library:
            return ""
        try:
            keywords = self._extract_keywords(user_query)
            keyword_key = tuple(sorted(kw.lower() for kw in keywords))

            dedup_key = (task_type, keyword_key)
            if hasattr(self, "_learned_format_keys") and dedup_key in self._learned_format_keys:
                logger.debug(f"[DocumentBuilder] Skipping duplicate format: {dedup_key}")
                return ""
            if not hasattr(self, "_learned_format_keys"):
                self._learned_format_keys: set = set()
            self._learned_format_keys.add(dedup_key)

            self._format_counter += 1
            from ai.memory.memory_template import MemoryTemplate, ResponseCategory, create_template

            category_map = {
                "character_card": ResponseCategory.CHARACTER_CARD,
                "document": ResponseCategory.DOCUMENT,
                "research": ResponseCategory.RESEARCH,
                "plan": ResponseCategory.PLAN,
            }
            format_id = f"format_{task_type}_{self._format_counter:03d}"
            template = create_template(
                content=result_text,
                category=category_map.get(task_type, ResponseCategory.UNKNOWN),
                keywords=self._extract_keywords(user_query),
                metadata={
                    "task_type": task_type,
                    "segments": len(segments),
                    "learned_from": user_query[:100],
                    "created_at": time.time(),
                },
            )
            self.template_library.add_custom_template(template)
            logger.info(f"Learned format: {format_id} (type={task_type})")
            return format_id
        except Exception as e:
            logger.warning(f"Format learning failed: {e}")
            return ""

    def _extract_keywords(self, text: str) -> List[str]:
        words = re.findall(r"[\w\u4e00-\u9fff]{2,}", text)
        stop = {"的", "是", "了", "在", "和", "與", "或", "但", "之", "於", "被", "為", "有", "我", "你", "他", "她", "它", "這", "那", "個", "一", "不", "就", "也", "都", "可以", "要", "會", "能", "一個", "什麼", "怎麼", "如何", "為什麼"}
        return [w for w in words if w not in stop and len(w) > 1][:10]

    def _detect_task_type(self, query: str) -> str:
        """從查詢推斷任務類型，用於格式匹配"""
        if _intent_registry:
            return _intent_registry.detect_task_type(query)
        query_lower = query.lower()
        if any(kw in query_lower for kw in ["角色", "角色卡", "生成角色", "人物", "人物卡"]):
            return "character_card"
        elif any(kw in query_lower for kw in ["報告", "文件", "整理", "彙整"]):
            return "document"
        elif any(kw in query_lower for kw in ["搜尋", "查找", "研究", "找資料"]):
            return "research"
        elif any(kw in query_lower for kw in ["規劃", "策劃", "設計", "project"]):
            return "plan"
        return "general"

    def _build_system_prompt(
        self, task_type: str, segment_index: int, total_segments: int,
        learned_format: Optional[str] = None, codex_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """根據任務類型構建段落系統提示"""
        format_hint = ""
        if learned_format:
            format_hint = f"\n輸出格式參考：\n{learned_format}"

        codex_hint = ""
        if codex_data and task_type == "character_card":
            characters = codex_data.get("characters", {})
            if characters:
                sample = list(characters.items())[:3]
                codex_hint = "\n\n【TRPG Codex 參考】現有角色參考：\n"
                for name, data in sample:
                    if isinstance(data, dict):
                        desc = data.get("description", data.get("title", str(data)))
                        codex_hint += f"  - {name}: {desc[:80]}\n"

        type_hints = {
            "character_card": "以 JSON 格式輸出角色設定卡。包含：名稱、等級、武器、技能、背景故事、性格描述。" + format_hint + codex_hint,
            "document": "以結構化 Markdown 格式輸出。包含章節標題和內容。" + format_hint,
            "research": "以摘要列表格式輸出。包含標題、來源、重點說明。" + format_hint,
            "plan": "以步驟列表格式輸出。包含每步的名稱、說明、預期結果。" + format_hint,
            "general": "直接輸出內容，保持連貫性。" + format_hint,
        }
        hint = type_hints.get(task_type, type_hints["general"])
        return (
            f"你是一個專業的內容生成助手。\n"
            f"這是長文檔的第 {segment_index + 1}/{total_segments} 段落。\n"
            f"{hint}\n"
            "請只輸出本段內容，不要加標題或總結。"
        )

    def _decompose_into_segments(
        self,
        query: str,
        task_type: str,
        complexity: float = 0.5,
    ) -> List[DocSegment]:
        """將任務分解為段落列表"""
        n_segments = max(2, min(self.max_segments, int(complexity * self.max_segments) + 1))

        if task_type == "character_card":
            titles = ["基本信息", "戰鬥屬性", "技能設定", "背景故事"]
            suffixes = [
                "生成角色的基本資訊：名稱、稱號、髮色、瞳色、性格關鍵詞。",
                "生成角色的戰鬥屬性：HP、攻擊力、防御力、速度、稀有度。",
                "生成角色的核心技能與被動技，包括技能名稱、冷卻、效果描述。",
                "生成角色的背景故事（100-200字），解釋戰艦名稱與人格的關聯。",
            ]
        elif task_type == "document":
            titles = ["摘要", "背景與目的", "主要內容", "分析與討論", "結論與建議"]
            suffixes = [
                "撰寫本文件的摘要（50-100字）。",
                "說明背景與目的（100-200字）。",
                "詳細說明主要內容（300-500字）。",
                "進行分析與討論（200-300字）。",
                "總結結論與建議（100-200字）。",
            ]
        elif task_type == "research":
            titles = ["搜索關鍵詞", "資料整理", "分析摘要", "引用來源"]
            suffixes = [
                "列出搜索關鍵詞與策略。",
                "整理收集到的資料要點。",
                "分析資料的關鍵發現與見解。",
                "列出引用來源與相關連結。",
            ]
        elif task_type == "plan":
            titles = ["目標確認", "步驟一", "步驟二", "步驟三", "風險評估"]
            suffixes = [
                "確認最終目標與約束條件。",
                "第一步的具體行動與負責項目。",
                "第二步的具體行動與負責項目。",
                "第三步的具體行動與負責項目。",
                "識別潛在風險與對應措施。",
            ]
        else:
            titles = [f"段落{i+1}" for i in range(n_segments)]
            suffixes = [f"生成第 {i+1} 段內容，主題：{query}" for i in range(n_segments)]

        if len(titles) > n_segments:
            titles = titles[:n_segments]
            suffixes = suffixes[:n_segments]

        return [
            DocSegment(index=i, title=titles[i], prompt_suffix=suffixes[i])
            for i in range(len(titles))
        ]

    async def build(
        self,
        query: str,
        state_context: Optional[Dict[str, Any]] = None,
        complexity: float = 0.5,
        learn_from_output: bool = True,
        user_feedback: Optional[str] = None,
    ) -> DocumentBuildResult:
        """
        主構建方法。
        - 若有 user_feedback，用反饋作為格式修正
        - 否則查詢 TemplateLibrary → 找不到則從頭生成
        """
        task_id = f"doc_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        state_context = state_context or {}

        task_type = self._detect_task_type(query)
        learned_format = None
        if not user_feedback:
            mem_result = self._load_format_from_memory(task_type)
            if mem_result:
                learned_format = mem_result.get("content")

        if user_feedback:
            learned_format = user_feedback
            task_type = "user_format"

        codex_data = {}
        if task_type == "character_card" and not user_feedback:
            codex_data = await self._load_fantasy_codex(query)

        segments = self._decompose_into_segments(query, task_type, complexity)
        results: List[DocSegment] = []

        for seg in segments:
            seg_start = time.time()
            system_prompt = self._build_system_prompt(task_type, seg.index, len(segments), learned_format, codex_data)
            user_prompt = f"{query}\n\n指示：{seg.prompt_suffix}"

            try:
                text = await asyncio.wait_for(
                    self.llm_generate(
                        prompt=user_prompt,
                        max_tokens=self.tokens_per_segment,
                        temperature=0.75,
                        system_prompt=system_prompt,
                    ),
                    timeout=self._segment_timeout_seconds,
                )
                seg.content = text
                seg.time_ms = (time.time() - seg_start) * 1000
                seg.tokens = len(text.split()) * 1.3
                logger.info(f"[DocumentBuilder] Segment {seg.index+1}/{len(segments)} done in {seg.time_ms:.0f}ms")
            except asyncio.TimeoutError:
                seg.error = f"Segment timeout after {self._segment_timeout_seconds}s"
                seg.time_ms = self._segment_timeout_seconds * 1000
                logger.warning(f"[DocumentBuilder] Segment {seg.index} timed out after {self._segment_timeout_seconds}s")
            except Exception as e:
                seg.error = str(e)
                logger.warning(f"[DocumentBuilder] Segment {seg.index} failed: {e}")

            results.append(seg)

            if self.eta_state:
                self.eta_state.execution_count += 1

        full_text = "\n\n".join(
            f"### {s.title}\n{s.content}" for s in results if s.content
        )
        format_id = ""
        if learn_from_output and not user_feedback and sum(1 for s in results if s.content) >= len(results) * 0.6:
            format_id = self._learn_format(task_type, query, full_text, results)

        return DocumentBuildResult(
            task_id=task_id,
            full_text=full_text,
            segments=results,
            total_segments=len(results),
            successful_segments=sum(1 for s in results if s.content),
            total_time_ms=(time.time() - start_time) * 1000,
            format_id=format_id,
            metadata={
                "task_type": task_type,
                "complexity": complexity,
                "learned": bool(format_id),
                "user_feedback": bool(user_feedback),
            },
        )