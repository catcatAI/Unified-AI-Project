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
            cap_name = cap_name[len(self.agent_id) + 1:]
        if "_v" in cap_name:
            cap_name = cap_name.rsplit("_v", 1)[0]
        result_payload = {"request_id": request_id}
        if cap_name == "entity_linking":
            result_payload["status"] = "success"
            result_payload["payload"] = self._perform_entity_linking(params)
        elif cap_name == "relationship_extraction":
            result = self._extract_relationships(params.get("text", ""))
            result_payload["status"] = "success"
            result_payload["payload"] = {"relationships": result}
        elif cap_name == "graph_query":
            result = self._query_knowledge_graph(params.get("query", ""))
            result_payload["status"] = "success"
            result_payload["payload"] = {"result": result}
        else:
            result_payload["status"] = "failure"
            result_payload["error_details"] = {"error_code": "CAPABILITY_NOT_SUPPORTED"}
        await self.hsp_connector.send_task_result(result_payload, callback_address)

    def query_graph(self, query: str) -> Dict[str, Any]:
        """Query the knowledge graph (in-memory lookup)."""
        if not query:
            return {"status": "error", "message": "No query provided", "results": []}
        query_lower = query.lower()
        results = [{"entity": k, "properties": v} for k, v in self._entities.items() if query_lower in k.lower()]
        logger.info(f"query_graph: '{query}' -> {len(results)} results")
        return {"status": "success", "message": f"Found {len(results)} matching entities", "results": results}

    def add_entity(self, entity: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Add an entity to the knowledge graph."""
        if not entity:
            return {"status": "error", "message": "No entity name provided"}
        self._entities[entity] = properties
        logger.info(f"add_entity: '{entity}' with {len(properties)} properties")
        return {"status": "success", "message": f"Entity '{entity}' added successfully", "entity": entity, "properties": properties}

    def find_relations(self, entity_a: str, entity_b: str) -> Dict[str, Any]:
        """Find relations between two entities."""
        if not entity_a or not entity_b:
            return {"status": "error", "message": "Both entity names required", "relations": []}
        relations = [r for r in self._relations if r["source"] == entity_a and r["target"] == entity_b]
        logger.info(f"find_relations: '{entity_a}' <-> '{entity_b}' -> {len(relations)} relations")
        return {"status": "success", "message": f"Found {len(relations)} relations", "relations": relations}

