import asyncio
import uuid
import json
import logging
from typing import Dict, Any, List

from apps.backend.src.ai.agents.base.base_agent import BaseAgent
from apps.backend.src.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope
from apps.backend.src.tools.tool_dispatcher import ToolDispatcher

class KnowledgeGraphAgent(BaseAgent):
    """
    A specialized agent for knowledge graph tasks like entity linking,
    relationship extraction, and graph querying.
    """
    def __init__(self, agent_id: str):
        capabilities = [
            {
                "capability_id": f"{agent_id}_entity_linking_v1.0",
                "name": "entity_linking",
                "description": "Links entities in text to a knowledge base.",
                "version": "1.0",
                "parameters": [
                    {"name": "text", "type": "string", "required": True, "description": "Text content for entity linking"},
                    {"name": "knowledge_base", "type": "string", "required": False, "description": "Knowledge base to use for linking"}
                ],
                "returns": {"type": "object", "description": "Linked entities with their identifiers."}
            },
            {
                "capability_id": f"{agent_id}_relationship_extraction_v1.0",
                "name": "relationship_extraction",
                "description": "Extracts relationships between entities from text.",
                "version": "1.0",
                "parameters": [
                    {"name": "text", "type": "string", "required": True, "description": "Text content for relationship extraction"}
                ],
                "returns": {"type": "object", "description": "Extracted relationships between entities."}
            },
            {
                "capability_id": f"{agent_id}_graph_query_v1.0",
                "name": "graph_query",
                "description": "Queries a knowledge graph for information.",
                "version": "1.0",
                "parameters": [
                    {"name": "query", "type": "string", "required": True, "description": "Query to execute on the knowledge graph"},
                    {"name": "graph_id", "type": "string", "required": False, "description": "Identifier of the knowledge graph to query"}
                ],
                "returns": {"type": "object", "description": "Results of the knowledge graph query."}
            }
        ]
        super().__init__(agent_id=agent_id, capabilities=capabilities)
        logging.info(f"[{self.agent_id}] KnowledgeGraphAgent initialized with capabilities: {[cap['name'] for cap in capabilities]}")

    async def handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
        request_id = task_payload.get("request_id")
        capability_id = task_payload.get("capability_id_filter", "")
        params = task_payload.get("parameters", {})

        logging.info(f"[{self.agent_id}] Handling task {request_id} for capability '{capability_id}'")

        try:
            if "entity_linking" in capability_id:
                result = self._perform_entity_linking(params)
                result_payload = self._create_success_payload(request_id, result)
            elif "relationship_extraction" in capability_id:
                result = self._extract_relationships(params)
                result_payload = self._create_success_payload(request_id, result)
            elif "graph_query" in capability_id:
                result = self._query_knowledge_graph(params)
                result_payload = self._create_success_payload(request_id, result)
            else:
                result_payload = self._create_failure_payload(request_id, "CAPABILITY_NOT_SUPPORTED", f"Capability '{capability_id}' is not supported by this agent.")
        except Exception as e:
            logging.error(f"[{self.agent_id}] Error processing task {request_id}: {e}")
            result_payload = self._create_failure_payload(request_id, "EXECUTION_ERROR", str(e))

        if self.hsp_connector and task_payload.get("callback_address"):
            callback_topic = task_payload["callback_address"]
            await self.hsp_connector.send_task_result(result_payload, callback_topic)
            logging.info(f"[{self.agent_id}] Sent task result for {request_id} to {callback_topic}")

    def _perform_entity_linking(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Links entities in text to a knowledge base."""
        text = params.get('text', '')
        knowledge_base = params.get('knowledge_base', 'default')
        
        if not text:
            raise ValueError("No text provided for entity linking")
        
        # Simple entity linking implementation
        # In a real implementation, this would use a proper knowledge base
        entities = []
        words = text.split()
        
        # Simple heuristic: assume capitalized words are entities
        for i, word in enumerate(words):
            # Remove punctuation
            clean_word = word.strip('.,!?;:"()[]{}')
            if clean_word and clean_word[0].isupper() and len(clean_word) > 1:
                entities.append({
                    "text": clean_word,
                    "start": text.find(clean_word),
                    "end": text.find(clean_word) + len(clean_word),
                    "kb_id": f"kb:{clean_word.lower()}",
                    "confidence": 0.8
                })
        
        return {
            "entities": entities,
            "knowledge_base": knowledge_base,
            "total_entities": len(entities)
        }

    def _extract_relationships(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts relationships between entities from text."""
        text = params.get('text', '')
        
        if not text:
            raise ValueError("No text provided for relationship extraction")
        
        # Simple relationship extraction implementation
        # In a real implementation, this would use a proper NLP model
        relationships = []
        
        # Simple heuristic: look for patterns like "X is Y" or "X has Y"
        words = text.split()
        for i in range(len(words) - 2):
            # Pattern: "X is Y"
            if words[i+1].lower() in ['is', 'are', 'was', 'were']:
                subject = words[i].strip('.,!?;:"()[]{}')
                obj = words[i+2].strip('.,!?;:"()[]{}')
                if subject and obj:
                    relationships.append({
                        "subject": subject,
                        "predicate": "is",
                        "object": obj,
                        "confidence": 0.7
                    })
            
            # Pattern: "X has Y"
            elif words[i+1].lower() in ['has', 'have', 'had']:
                subject = words[i].strip('.,!?;:"()[]{}')
                obj = words[i+2].strip('.,!?;:"()[]{}')
                if subject and obj:
                    relationships.append({
                        "subject": subject,
                        "predicate": "has",
                        "object": obj,
                        "confidence": 0.7
                    })
        
        return {
            "relationships": relationships,
            "total_relationships": len(relationships)
        }

    def _query_knowledge_graph(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Queries a knowledge graph for information."""
        query = params.get('query', '')
        graph_id = params.get('graph_id', 'default')
        
        if not query:
            raise ValueError("No query provided for knowledge graph query")
        
        # Simple knowledge graph query implementation
        # In a real implementation, this would interface with a proper knowledge graph database
        results = []
        
        # Simple pattern matching for queries
        if "capital" in query.lower() and "france" in query.lower():
            results.append({
                "entity": "France",
                "property": "capital",
                "value": "Paris",
                "confidence": 0.95
            })
        elif "population" in query.lower() and "china" in query.lower():
            results.append({
                "entity": "China",
                "property": "population",
                "value": "1.4 billion",
                "confidence": 0.9
            })
        elif "located" in query.lower() and "egypt" in query.lower():
            results.append({
                "entity": "Egypt",
                "property": "location",
                "value": "North Africa",
                "confidence": 0.85
            })
        else:
            # Generic response for other queries
            results.append({
                "query": query,
                "result": f"No specific information found for '{query}'. This is a placeholder response.",
                "confidence": 0.1
            })
        
        return {
            "results": results,
            "graph_id": graph_id,
            "total_results": len(results)
        }

    def _create_success_payload(self, request_id: str, result: Any) -> HSPTaskResultPayload:
        return HSPTaskResultPayload(
            request_id=request_id,
            status="success",
            payload=result
        )

    def _create_failure_payload(self, request_id: str, error_code: str, error_message: str) -> HSPTaskResultPayload:
        return HSPTaskResultPayload(
            request_id=request_id,
            status="failure",
            error_details={"error_code": error_code, "error_message": error_message}
        )

if __name__ == '__main__':
    async def main():
        agent_id = f"did:hsp:knowledge_graph_agent_{uuid.uuid4().hex[:6]}"
        agent = KnowledgeGraphAgent(agent_id=agent_id)
        await agent.start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nKnowledgeGraphAgent manually stopped.")