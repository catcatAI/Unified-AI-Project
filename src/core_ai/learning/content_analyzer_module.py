import logging
import networkx as nx
import spacy
from typing import Dict, Any, Optional, List, TypedDict, Tuple

from src.shared.types.common_types import KGEntity, KGRelationship, KnowledgeGraph
from src.hsp.types import HSPFactPayload, HSPFactStatementStructured

logger = logging.getLogger(__name__)

# Define TypedDicts used in this module
class ProcessedTripleInfo(TypedDict):
    subject_id: str
    predicate_type: str
    object_id: str
    object_literal: Optional[str]
    object_datatype: Optional[str]

class CAHSPFactProcessingResult(TypedDict):
    updated_graph: bool
    processed_triple: Optional[ProcessedTripleInfo]

class ContentAnalyzerModule:
    """
    Analyzes text content to extract entities and relationships, building a knowledge graph.
    Also processes HSP facts to integrate into the knowledge graph.
    """
    def __init__(self, spacy_model_name: str = "en_core_web_sm", ontology_mappings: Optional[Dict[str, str]] = None):
        try:
            self.nlp = spacy.load(spacy_model_name)
            logger.info(f"ContentAnalyzerModule: spaCy model '{spacy_model_name}' loaded successfully.")
        except Exception as e:
            logger.error(f"ContentAnalyzerModule: Failed to load spaCy model '{spacy_model_name}': {e}")
            logger.warning("ContentAnalyzerModule will operate in a limited capacity without a loaded spaCy model.")
            self.nlp = None

        self.graph = nx.DiGraph()
        self.ontology_mapping = ontology_mappings if ontology_mappings is not None else self._load_default_ontology_mappings()
        self.internal_uri_prefixes = {
            "http://example.org/entity/": "cai_instance:ex_",
            "http://example.org/prop/": "cai_prop:ex_",
            "http://example.org/country/": "cai_type:Country_" # Example class mapping
        }
        logger.info("ContentAnalyzerModule initialized.")

    def _load_default_ontology_mappings(self) -> Dict[str, str]:
        # Placeholder for loading from a config file (e.g., YAML or JSON)
        # For now, hardcode a simple example
        return {
            "http://example.org/entity/": "cai_instance:ex_",
            "http://example.org/prop/": "cai_prop:ex_",
            "http://example.org/country/": "cai_type:Country" # Example mapping
        }

    def _map_uri_to_internal_id(self, uri: str) -> str:
        for prefix, internal_prefix in self.internal_uri_prefixes.items():
            if uri.startswith(prefix):
                return internal_prefix + uri[len(prefix):]
        return uri # Return original if no mapping

    def analyze_content(self, text_content: str) -> Tuple[KnowledgeGraph, nx.DiGraph]:
        if not self.nlp:
            logger.warning("analyze_content: spaCy model not loaded. Returning empty knowledge graph.")
            return {"entities": {}, "relationships": []}, nx.DiGraph()

        doc = self.nlp(text_content)
        entities: Dict[str, KGEntity] = {}
        relationships: List[KGRelationship] = []
        nx_graph = nx.DiGraph()

        # Entity Extraction
        for ent in doc.ents:
            entity_id = f"ent_{ent.label_.lower()}_{ent.text.lower().replace(' ', '_')}"
            entities[entity_id] = {
                "id": entity_id,
                "label": ent.text,
                "type": ent.label_,
                "attributes": {}
            }
            nx_graph.add_node(entity_id, label=ent.text, type=ent.label_)

        # Relationship Extraction (simplified SVO for demonstration)
        for token in doc:
            if token.dep_ == "ROOT" and token.pos_ == "VERB":
                subject = [child for child in token.children if child.dep_ == "nsubj"]
                obj = [child for child in token.children if child.dep_ == "dobj"]

                if subject and obj:
                    subj_ent = next((ent for ent in doc.ents if ent.text == subject[0].text), None)
                    obj_ent = next((ent for ent in doc.ents if ent.text == obj[0].text), None)

                    if subj_ent and obj_ent:
                        subj_id = f"ent_{subj_ent.label_.lower()}_{subj_ent.text.lower().replace(' ', '_')}"
                        obj_id = f"ent_{obj_ent.label_.lower()}_{obj_ent.text.lower().replace(' ', '_')}"
                        rel_type = token.lemma_

                        relationships.append({
                            "source_id": subj_id,
                            "target_id": obj_id,
                            "type": rel_type,
                            "attributes": {}
                        })
                        nx_graph.add_edge(subj_id, obj_id, type=rel_type)

        kg_data: KnowledgeGraph = {"entities": entities, "relationships": relationships}
        return kg_data, nx_graph

    def process_hsp_fact_content(self, hsp_fact_payload: HSPFactPayload, source_ai_id: str) -> CAHSPFactProcessingResult:
        updated_graph = False
        processed_triple: Optional[ProcessedTripleInfo] = None

        if hsp_fact_payload["statement_type"] == "natural_language":
            # Process natural language fact by analyzing it and adding to graph
            _, new_nx_graph = self.analyze_content(hsp_fact_payload["statement_nl"])
            self.graph = nx.compose(self.graph, new_nx_graph) # Merge graphs
            updated_graph = True
            logger.info(f"Processed NL HSP fact '{hsp_fact_payload["id"]}'. Graph updated.")

        elif hsp_fact_payload["statement_type"] == "semantic_triple":
            structured_statement = hsp_fact_payload["statement_structured"]
            s_uri = structured_statement["subject_uri"]
            p_uri = structured_statement["predicate_uri"]
            o_uri = structured_statement.get("object_uri")
            o_literal = structured_statement.get("object_literal")
            o_datatype = structured_statement.get("object_datatype")

            # Map URIs to internal IDs
            s_id = self._map_uri_to_internal_id(s_uri)
            p_type = p_uri.split('/')[-1] # Simple extraction for now

            o_id: str
            if o_uri:
                o_id = self._map_uri_to_internal_id(o_uri)
                o_label = o_uri.split('/')[-1] # Simple label from URI
                self.graph.add_node(o_id, label=o_label, type="HSP_URI_Entity") # Add object node
            elif o_literal is not None:
                o_id = f"literal_{o_literal.lower().replace(' ', '_')}_{hsp_fact_payload['id'][:4]}"
                self.graph.add_node(o_id, label=str(o_literal), type="Literal", datatype=o_datatype)
            else:
                logger.warning(f"Semantic triple fact {hsp_fact_payload['id']} missing object_uri or object_literal.")
                return {"updated_graph": False, "processed_triple": None}

            self.graph.add_node(s_id, label=s_uri.split('/')[-1], type="HSP_URI_Entity") # Add subject node
            self.graph.add_edge(s_id, o_id, type=p_type, original_predicate_uri=p_uri)
            updated_graph = True
            processed_triple = {
                "subject_id": s_id,
                "predicate_type": p_type,
                "object_id": o_id,
                "object_literal": o_literal,
                "object_datatype": o_datatype
            }
            logger.info(f"Processed semantic triple HSP fact '{hsp_fact_payload["id"]}'. Graph updated.")

        else:
            logger.warning(f"Unsupported HSP fact statement type: {hsp_fact_payload["statement_type"]}")

        return {"updated_graph": updated_graph, "processed_triple": processed_triple}
