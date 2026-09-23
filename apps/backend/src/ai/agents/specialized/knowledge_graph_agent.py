# =============================================================================
# ANGELA-MATRIX: L2[记忆层] β [A] L3+
# =============================================================================
#
# 职责: 知识图谱代理，管理和查询知识图谱
# 维度: 涉及认知维度 (β) 的知识推理和关联
# 安全: 使用 Key A (后端控制) 进行知识图谱访问控制
# 成熟度: L3+ 等级可以进行复杂的知识推理
#
# 能力:
# - graph_query: 知识图谱查询
# - entity_extraction: 实体抽取
# - relation_extraction: 关系抽取
# - knowledge_integration: 知识集成
#
# =============================================================================

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class KnowledgeGraphAgent:
    """Agent for querying and managing a knowledge graph."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        self.config = config or {}
        self.agent_id = kwargs.get("agent_id")
        self.hsp_connector: Optional[Any] = None
        self.capabilities = [
            {
                "name": "entity_linking",
                "capability_id": "entity_linking",
                "description": "將文本中的實體連接到知識圖譜",
                "version": "1.0.0",
            },
            {
                "name": "relationship_extraction",
                "capability_id": "relationship_extraction",
                "description": "從文本中提取實體關係",
                "version": "1.0.0",
            },
            {
                "name": "graph_query",
                "capability_id": "graph_query",
                "description": "查詢知識圖譜",
                "version": "1.0.0",
            },
        ]
        self._entities: Dict[str, Dict[str, Any]] = {}
        self._relations: List[Dict[str, Any]] = []
        logger.info(f"KnowledgeGraphAgent initialized with config: {self.config}")

    async def handle_task_request(self, task_payload, sender_ai_id, envelope):
        capability_id_filter = task_payload.get("capability_id_filter", "")
        params = task_payload.get("parameters", {})
        request_id = task_payload.get("request_id", "")
        callback_address = task_payload.get("callback_address", "")
        cap_name = capability_id_filter
        if self.agent_id and cap_name.startswith(self.agent_id + "_"):
            cap_name = cap_name[len(self.agent_id) + 1 :]
        if "_v" in cap_name:
            cap_name = cap_name.rsplit("_v", 1)[0]
        result_payload = {"request_id": request_id}
        if cap_name == "entity_linking":
            # R87 死路徑 #12：此前呼叫不存在的 self._perform_entity_linking ——
            # 能力已對外註冊（self.capabilities），但一執行就 AttributeError。
            # 改為基於既有 _entities 的字典前綴/子字串匹配實作。
            result_payload["status"] = "success"
            result_payload["payload"] = self._perform_entity_linking(params)
        elif cap_name == "relationship_extraction":
            result: List[Dict[str, Any]] = self._extract_relationships(params.get("text", ""))
            result_payload["status"] = "success"
            result_payload["payload"] = {"relationships": result}
        elif cap_name == "graph_query":
            graph_result: Dict[str, Any] = self.query_graph(params.get("query", ""))
            result_payload["status"] = "success"
            result_payload["payload"] = {"result": graph_result}
        else:
            result_payload["status"] = "failure"
            result_payload["error_details"] = {"error_code": "CAPABILITY_NOT_SUPPORTED"}
        if self.hsp_connector is None:
            logger.warning(
                f"KnowledgeGraphAgent hsp_connector not set; dropping task result for request {request_id}",
            )
            return
        await self.hsp_connector.send_task_result(result_payload, callback_address)

    def _perform_entity_linking(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """把 params.text 中的提及連接到已知實體（子字串匹配）。

        R87 補齊：capability "entity_linking" 已對外註冊，但此前處理函式
        不存在——請求一來就 AttributeError 被上層吞掉。以 _entities
        字典做不區分大小寫的出現匹配，回傳提及位置與實體。
        """
        text = str(params.get("text", ""))
        if not text or not self._entities:
            return {"mentions": []}
        text_lower = text.lower()
        mentions: List[Dict[str, Any]] = [
            {
                "entity": entity,
                "properties": properties,
                "position": text_lower.find(entity.lower()),
            }
            for entity, properties in self._entities.items()
            if entity.lower() in text_lower
        ]
        mentions.sort(key=lambda m: int(m["position"]))
        return {"mentions": mentions}

    def _extract_relationships(self, text: str) -> List[Dict[str, Any]]:
        """從文本抽取已知實體對的關係（以既有 _relations 過濾）。

        R87 補齊：capability "relationship_extraction" 已對外註冊，但此前
        處理函式不存在。列出文本中同時出現的實體對之間的已知關係；
        文本中出現但無已知關係的實體對不虛構（誠實回傳 known=false）。
        """
        if not text or not self._entities:
            return []
        text_lower = text.lower()
        present = [e for e in self._entities if e.lower() in text_lower]
        results: List[Dict[str, Any]] = []
        for i, source in enumerate(present):
            for target in present[i + 1 :]:
                known = [
                    r
                    for r in self._relations
                    if r.get("source") == source
                    and r.get("target") == target
                    or r.get("source") == target
                    and r.get("target") == source
                ]
                if known:
                    results.extend(known)
                else:
                    results.append({"source": source, "target": target, "known": False})
        return results

    def query_graph(self, query: str) -> Dict[str, Any]:
        """Query the knowledge graph (in-memory lookup)."""
        if not query:
            return {"status": "error", "message": "No query provided", "results": []}
        query_lower = query.lower()
        results = [
            {"entity": k, "properties": v}
            for k, v in self._entities.items()
            if query_lower in k.lower()
        ]
        logger.info(f"query_graph: '{query}' -> {len(results)} results")
        return {
            "status": "success",
            "message": f"Found {len(results)} matching entities",
            "results": results,
        }

    def add_entity(self, entity: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Add an entity to the knowledge graph."""
        if not entity:
            return {"status": "error", "message": "No entity name provided"}
        self._entities[entity] = properties
        logger.info(f"add_entity: '{entity}' with {len(properties)} properties")
        return {
            "status": "success",
            "message": f"Entity '{entity}' added successfully",
            "entity": entity,
            "properties": properties,
        }

    def find_relations(self, entity_a: str, entity_b: str) -> Dict[str, Any]:
        """Find relations between two entities."""
        if not entity_a or not entity_b:
            return {"status": "error", "message": "Both entity names required", "relations": []}
        relations = [
            r for r in self._relations if r["source"] == entity_a and r["target"] == entity_b
        ]
        logger.info(f"find_relations: '{entity_a}' <-> '{entity_b}' -> {len(relations)} relations")
        return {
            "status": "success",
            "message": f"Found {len(relations)} relations",
            "relations": relations,
        }
