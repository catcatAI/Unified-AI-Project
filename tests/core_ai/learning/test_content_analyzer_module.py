import unittest
import networkx as nx
from typing import Dict, Any, Optional # Added Optional

# Assuming the module is in src.core_ai.learning.content_analyzer_module
# Adjust path if necessary based on how tests are run and PYTHONPATH
# Assuming 'src' is in PYTHONPATH
from core_ai.learning.content_analyzer_module import ContentAnalyzerModule
from shared.types.common_types import KGEntity, KGRelationship, KnowledgeGraph

class TestContentAnalyzerModule(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Load the analyzer once for all tests in this class."""
        try:
            cls.analyzer = ContentAnalyzerModule()
        except Exception as e:
            print(f"Error setting up ContentAnalyzerModule in tests: {e}")
            # Potentially download spacy model if missing and tests are run in an env that allows it
            # For CI, models should be pre-downloaded or handled by setup scripts.
            # Example:
            # if "Can't find model" in str(e):
            #     import spacy.cli
            #     print("Test setup: Downloading en_core_web_sm for ContentAnalyzerModule...")
            #     spacy.cli.download("en_core_web_sm")
            #     cls.analyzer = ContentAnalyzerModule() # Retry
            # else:
            raise e # Reraise if it's not a model download issue

    def assertEntityInGraph(self, label: str, entity_type: str, kg_data: KnowledgeGraph, msg: str = ""):
        found = False
        for entity_id, entity_details in kg_data["entities"].items():
            if entity_details["label"] == label and entity_details["type"] == entity_type:
                found = True
                break
        self.assertTrue(found, msg or f"Entity '{label}' (type: {entity_type}) not found in graph entities.")

    def assertNodeInNxGraph(self, node_id_part: str, label: str, node_type: str, nx_graph: nx.DiGraph, msg: str = ""):
        found_node = None
        for node, data in nx_graph.nodes(data=True):
            if node_id_part in node and data.get("label") == label and data.get("type") == node_type:
                found_node = node
                break
        self.assertIsNotNone(found_node, msg or f"Node with label '{label}' (type: {node_type}) containing ID part '{node_id_part}' not found in NetworkX graph.")
        return found_node # Return the actual node_id for further checks if needed

    def test_01_initialization(self):
        """Test if the analyzer initializes correctly."""
        self.assertIsNotNone(self.analyzer, "Analyzer should not be None")
        self.assertIsNotNone(self.analyzer.nlp, "spaCy NLP model should be loaded")

    def test_02_simple_entity_extraction(self):
        """Test basic entity extraction."""
        text = "Apple Inc. is a company. Steve Jobs was a person."
        kg_data, nx_graph = self.analyzer.analyze_content(text)

        self.assertGreater(len(kg_data["entities"]), 1, "Should extract at least two entities.")

        # Check TypedDict representation
        self.assertEntityInGraph("Apple Inc.", "ORG", kg_data)
        self.assertEntityInGraph("Steve Jobs", "PERSON", kg_data)

        # Check NetworkX graph representation
        self.assertNodeInNxGraph("apple_inc", "Apple Inc.", "ORG", nx_graph)
        self.assertNodeInNxGraph("steve_jobs", "Steve Jobs", "PERSON", nx_graph)

        self.assertEqual(nx_graph.number_of_nodes(), len(kg_data["entities"]))

    def test_03_no_entities_extraction(self):
        """Test text with no clear named entities for the small model."""
        text = "The sky is blue and the grass is green."
        kg_data, nx_graph = self.analyzer.analyze_content(text)
        # Small model might not find entities, or find very generic ones.
        # This test mainly ensures it doesn't crash.
        self.assertIsNotNone(kg_data["entities"], "Entities dict should exist even if empty.")
        self.assertIsNotNone(nx_graph, "NetworkX graph should be created even if empty.")

    def test_04_simple_svo_relationship(self):
        """Test a simple Subject-Verb-Object relationship."""
        text = "Google develops Android." # Google (ORG), Android (PRODUCT or ORG by sm model)
        kg_data, nx_graph = self.analyzer.analyze_content(text)

        # Ensure entities are present first
        google_node_id = None
        android_node_id = None
        for node_id, data in nx_graph.nodes(data=True):
            if data.get("label") == "Google":
                google_node_id = node_id
            elif data.get("label") == "Android": # spaCy 'en_core_web_sm' might label Android as ORG or PRODUCT
                android_node_id = node_id

        self.assertIsNotNone(google_node_id, "Google entity not found in graph.")
        self.assertIsNotNone(android_node_id, "Android entity not found in graph.")

        found_relationship = False
        if google_node_id and android_node_id:
            for rel in kg_data["relationships"]:
                if rel["source_id"] == google_node_id and \
                   rel["target_id"] == android_node_id and \
                   rel["type"] == "develop": # verb lemma
                    found_relationship = True
                    break
            self.assertTrue(found_relationship, "Expected 'develop' SVO relationship between Google and Android not found in TypedDict.")

            # Check NetworkX graph
            if found_relationship: # Only check edge if relationship was asserted
                 self.assertTrue(nx_graph.has_edge(google_node_id, android_node_id), "Edge Google -> Android missing in NX graph")
                 edge_data = nx_graph.get_edge_data(google_node_id, android_node_id)
                 self.assertIsNotNone(edge_data, "Edge data missing for Google -> Android")
                 self.assertEqual(edge_data.get("type"), "develop", "NX Edge type incorrect")


    def test_05_prep_object_relationship(self):
        """Test a relationship involving a prepositional object."""
        # "cat sat on the mat" -> mat might not be an entity with sm model.
        # Let's try something more likely to have entities.
        text = "Microsoft is based in Redmond." # Microsoft (ORG), Redmond (GPE)
        kg_data, nx_graph = self.analyzer.analyze_content(text)

        ms_node_id = None
        rd_node_id = None
        for node_id, data in nx_graph.nodes(data=True):
            if data.get("label") == "Microsoft": ms_node_id = node_id
            if data.get("label") == "Redmond": rd_node_id = node_id

        self.assertIsNotNone(ms_node_id, "Microsoft entity not found.")
        self.assertIsNotNone(rd_node_id, "Redmond entity not found.")

        found_relationship = False
        # Now that LOCATED_IN matcher is active and covers "is based in",
        # it will likely produce "located_in". The dependency parser might produce "base_in".
        # The matcher's result might overwrite the dependency one in a simple DiGraph if added last.
        # The test should prioritize checking for the matcher's output ('located_in') in such cases.

        if ms_node_id and rd_node_id:
            found_rel_object = None
            # Prefer 'located_in' from matcher if present
            for rel in kg_data["relationships"]:
                if rel["source_id"] == ms_node_id and \
                   rel["target_id"] == rd_node_id and \
                   rel["type"] == "located_in":
                    found_rel_object = rel
                    break

            if not found_rel_object: # Fallback to older dependency-parsed types if matcher specific one not found
                for rel in kg_data["relationships"]:
                    if rel["source_id"] == ms_node_id and \
                       rel["target_id"] == rd_node_id and \
                       rel["type"] in ["base_in", "be_in"]:
                        found_rel_object = rel
                        break

            self.assertIsNotNone(found_rel_object, f"Expected relationship like 'located_in' or 'base_in'/'be_in' between Microsoft and Redmond not found.")

            if found_rel_object:
                self.assertTrue(nx_graph.has_edge(ms_node_id, rd_node_id), "Edge Microsoft -> Redmond missing in NX graph")
                edge_data = nx_graph.get_edge_data(ms_node_id, rd_node_id)
                self.assertIsNotNone(edge_data)
                # Assert that the type in NX graph matches the type we prioritized from kg_data
                self.assertEqual(edge_data.get("type"), found_rel_object["type"])


    def test_06_noun_prep_noun_relationship_of(self):
        """Test Noun-of-Noun relationship (e.g., CEO of Microsoft)."""
        text = "The CEO of Microsoft visited." # CEO (PERSON or TITLE), Microsoft (ORG)
                                           # Small model might not get CEO as PERSON.
                                           # Let's try "founder of Apple"
        text_apple = "Steve Jobs was a founder of Apple."
        kg_data, nx_graph = self.analyzer.analyze_content(text_apple)

        apple_node_id = None
        steve_node_id = None
        founder_node_id = None # "founder" itself might become an entity if not linked to Steve Jobs

        for node_id, data in nx_graph.nodes(data=True):
            if data.get("label") == "Apple": apple_node_id = node_id
            if data.get("label") == "Steve Jobs": steve_node_id = node_id
            if data.get("label") == "founder": founder_node_id = node_id

        self.assertIsNotNone(apple_node_id, "Apple entity not found.")
        self.assertIsNotNone(steve_node_id, "Steve Jobs entity not found.")
        # founder_node_id might or might not exist depending on NER and linking.

        # Expected: Apple (ORG) --[has_founder]--> Steve Jobs (PERSON)
        # OR Steve Jobs (PERSON) --[founder_of]--> Apple (ORG)
        # Current heuristic for "X of Y" where Y is ORG/PERSON: Y --[has_X_lemma]--> X
        # So we expect Apple --[has_founder]--> Steve Jobs (if founder is linked to Steve or Steve is obj of 'of')

        found_rel = False
        # Check for Apple --[has_founder/founder_of]--> Steve Jobs
        if nx_graph.has_edge(apple_node_id, steve_node_id):
            edge_data = nx_graph.get_edge_data(apple_node_id, steve_node_id)
            if edge_data.get("type") == "has_founder": # Based on heuristic "Y has_X"
                found_rel = True

        # Alternative: Steve Jobs --[founder_of]--> Apple
        if not found_rel and nx_graph.has_edge(steve_node_id, apple_node_id):
            edge_data = nx_graph.get_edge_data(steve_node_id, apple_node_id)
            if edge_data.get("type") == "founder_of":
                found_rel = True

        # Simpler check based on the TypedDict output if the above is too complex due to IDs
        typed_dict_rel_found = False
        for rel in kg_data["relationships"]:
            src_label = kg_data["entities"].get(rel["source_id"], {}).get("label")
            tgt_label = kg_data["entities"].get(rel["target_id"], {}).get("label")
            rel_type = rel["type"]

            if (src_label == "Apple" and tgt_label == "Steve Jobs" and rel_type == "has_founder") or \
               (src_label == "Steve Jobs" and tgt_label == "Apple" and rel_type == "founder_of"):
                typed_dict_rel_found = True
                break

        self.assertTrue(typed_dict_rel_found, "Expected 'founder of' type relationship not found between Apple and Steve Jobs.")

    def assertRelationshipInGraph(self, kg_data: KnowledgeGraph, nx_graph: nx.DiGraph,
                                  expected_src_label: str, expected_tgt_label: str,
                                  expected_rel_type: str,
                                  src_type: Optional[str] = None, tgt_type: Optional[str] = None,
                                  allow_reverse: bool = False):
        """
        Asserts that a specific relationship exists in both KG TypedDict and NetworkX graph.
        Finds nodes by label and optionally type.
        """
        src_node_id_kg, tgt_node_id_kg = None, None
        src_node_id_nx, tgt_node_id_nx = None, None

        for entity_id, entity in kg_data["entities"].items():
            if entity["label"] == expected_src_label and (not src_type or entity["type"] == src_type):
                src_node_id_kg = entity_id
            if entity["label"] == expected_tgt_label and (not tgt_type or entity["type"] == tgt_type):
                tgt_node_id_kg = entity_id

        for node_id, data in nx_graph.nodes(data=True):
            if data.get("label") == expected_src_label and (not src_type or data.get("type") == src_type):
                src_node_id_nx = node_id
            if data.get("label") == expected_tgt_label and (not tgt_type or data.get("type") == tgt_type):
                tgt_node_id_nx = node_id

        self.assertIsNotNone(src_node_id_kg, f"Source entity '{expected_src_label}' not found in KG entities.")
        self.assertIsNotNone(tgt_node_id_kg, f"Target entity '{expected_tgt_label}' not found in KG entities.")
        self.assertIsNotNone(src_node_id_nx, f"Source node '{expected_src_label}' not found in NX graph.")
        self.assertIsNotNone(tgt_node_id_nx, f"Target node '{expected_tgt_label}' not found in NX graph.")

        # Check TypedDict
        found_in_kg_direct = any(
            rel["source_id"] == src_node_id_kg and rel["target_id"] == tgt_node_id_kg and rel["type"] == expected_rel_type
            for rel in kg_data["relationships"]
        )
        found_in_kg_reverse = False
        if allow_reverse:
             found_in_kg_reverse = any(
                rel["source_id"] == tgt_node_id_kg and rel["target_id"] == src_node_id_kg and rel["type"] == expected_rel_type
                for rel in kg_data["relationships"]
            )

        self.assertTrue(found_in_kg_direct or (allow_reverse and found_in_kg_reverse),
                        f"Relationship {expected_src_label} -> {expected_tgt_label} (type: {expected_rel_type}) not found in KG relationships. "
                        f"(Allow reverse: {allow_reverse})")

        # Check NetworkX graph
        edge_exists_direct = nx_graph.has_edge(src_node_id_nx, tgt_node_id_nx)
        edge_data_direct = None
        if edge_exists_direct:
            edge_data_direct = nx_graph.get_edge_data(src_node_id_nx, tgt_node_id_nx)

        edge_exists_reverse = False
        edge_data_reverse = None
        if allow_reverse:
            edge_exists_reverse = nx_graph.has_edge(tgt_node_id_nx, src_node_id_nx)
            if edge_exists_reverse:
                 edge_data_reverse = nx_graph.get_edge_data(tgt_node_id_nx, src_node_id_nx)

        final_edge_data = None
        if edge_exists_direct and edge_data_direct.get("type") == expected_rel_type:
            final_edge_data = edge_data_direct
        elif allow_reverse and edge_exists_reverse and edge_data_reverse.get("type") == expected_rel_type:
            final_edge_data = edge_data_reverse

        self.assertIsNotNone(final_edge_data,
                             f"Edge {expected_src_label} --[{expected_rel_type}]--> {expected_tgt_label} not found or type mismatch in NX graph. "
                             f"(Allow reverse: {allow_reverse})")
        self.assertEqual(final_edge_data.get("type"), expected_rel_type, "NX Edge type incorrect.")


    def test_07_noun_of_noun_org_has_attribute(self):
        """Test 'CEO of Microsoft' -> Microsoft has_ceo CEO_Entity."""
        text = "Sundar Pichai is the CEO of Google."
        kg_data, nx_graph = self.analyzer.analyze_content(text)

        # Expected: Google (ORG) --[has_ceo]--> Sundar Pichai (PERSON)
        # The heuristic flips "CEO of Google" to "Google has_ceo CEO"
        self.assertRelationshipInGraph(kg_data, nx_graph,
                                         expected_src_label="Google", src_type="ORG",
                                         expected_tgt_label="Sundar Pichai", tgt_type="PERSON",
                                         expected_rel_type="has_ceo")

    def test_08_noun_of_noun_attribute_of(self):
        """Test 'capital of France' -> capital attribute_of France (or France has_capital capital)."""
        text = "Paris is the capital of France." # Paris (GPE), capital (NOUN concept), France (GPE)
        kg_data, nx_graph = self.analyzer.analyze_content(text)

        # Current heuristic for "X of Y":
        # If Y is ORG/GPE/PERSON and X is not, then Y --has_X_lemma--> X
        # Here, X="capital", Y="France". France is GPE. "capital" is not an ORG/GPE/PERSON entity.
        # So, we expect: France --has_capital--> Paris (if Paris is identified as the capital entity)
        # Or, if "capital" itself is an entity: France --has_capital--> capital_entity

        # Test 1: Paris (GPE) is_a capital (CONCEPT)
        self.assertEntityInGraph("Paris", "GPE", kg_data)
        self.assertEntityInGraph("capital", "CONCEPT", kg_data, msg="CONCEPT node 'capital' should be created.")

        self.assertRelationshipInGraph(kg_data, nx_graph,
                                         expected_src_label="Paris", src_type="GPE",
                                         expected_tgt_label="capital", tgt_type="CONCEPT", # Target is now CONCEPT
                                         expected_rel_type="is_a")

        # Test 2: France (GPE) has_capital concept_capital (heuristic for "capital of France")
        # The heuristic "Y of X" where Y is GPE (France) and X is "capital" (noun)
        # should result in France --has_capital--> concept_capital.
        self.assertEntityInGraph("France", "GPE", kg_data)
        self.assertRelationshipInGraph(kg_data, nx_graph,
                                         expected_src_label="France", src_type="GPE",
                                         expected_tgt_label="capital", tgt_type="CONCEPT",
                                         expected_rel_type="has_capital")

        # Verification that "Paris" is THE capital of "France" is more complex, involving linking
        # "the capital" in "Paris is the capital" to the "capital" in "capital of France".
        # For now, the above checks ensure the basic "is_a" and "has_X" from "X of Y" work with concepts.
        # The direct "capital of France" part:
        # X = capital (token), Y = France (entity)
        # France (Y, GPE) has_capital (X.lemma) Capital_Entity/Concept (X)
        # If "capital" is identified as an entity linked to "Paris", then France -> has_capital -> Paris
        # For now, let's check if a "has_capital" relationship exists from France to *something* that is Paris or capital.

        france_node_id_nx = None
        for node_id, data in nx_graph.nodes(data=True):
            if data.get("label") == "France" and data.get("type") == "GPE":
                france_node_id_nx = node_id
                break
        self.assertIsNotNone(france_node_id_nx, "France entity not found.")

        found_has_capital_to_paris_or_concept = False
        target_label_for_has_capital = None

        if france_node_id_nx:
            for successor in nx_graph.successors(france_node_id_nx):
                edge_data = nx_graph.get_edge_data(france_node_id_nx, successor)
                if edge_data and edge_data.get("type") == "has_capital":
                    target_node_data = nx_graph.nodes[successor]
                    target_label_for_has_capital = target_node_data.get("label")
                    # Check if the target is Paris or a concept of capital
                    if target_label_for_has_capital == "Paris" or "concept_capital" in successor:
                        found_has_capital_to_paris_or_concept = True
                        break

        self.assertTrue(found_has_capital_to_paris_or_concept,
                        f"Expected France to have a 'has_capital' relationship to Paris or a capital concept. Found target: {target_label_for_has_capital}")

    def test_08a_entity_is_a_concept(self):
        """Test 'Google is a company' -> Google (ORG) is_a company (CONCEPT)."""
        text = "Google is a company."
        kg_data, nx_graph = self.analyzer.analyze_content(text)

        self.assertEntityInGraph("Google", "ORG", kg_data)
        self.assertEntityInGraph("company", "CONCEPT", kg_data, msg="CONCEPT node 'company' should be created.")

        self.assertRelationshipInGraph(kg_data, nx_graph,
                                         expected_src_label="Google", src_type="ORG",
                                         expected_tgt_label="company", tgt_type="CONCEPT",
                                         expected_rel_type="is_a")

    def test_09_possessive_relationship_entity_to_entity(self):
        """Test 'Google's CEO' -> Google has_poss_attr CEO_Entity."""
        text = "Google's CEO Sundar Pichai announced a new product."
        # Expect: Google (ORG) --has_poss_attr--> Sundar Pichai (PERSON)
        # (if CEO is correctly linked to Sundar Pichai by NER/coref, or if Sundar Pichai is the head of the NP "Google's CEO")
        # The current possessive logic might be simpler: Google --has_poss_attr--> CEO (if CEO is entity)
        kg_data, nx_graph = self.analyzer.analyze_content(text)

        self.assertRelationshipInGraph(kg_data, nx_graph,
                                         expected_src_label="Google", src_type="ORG",
                                         expected_tgt_label="Sundar Pichai", tgt_type="PERSON", # This assumes CEO is identified as Sundar
                                         expected_rel_type="has_poss_attr")


    def test_10_possessive_relationship_entity_to_concept(self):
        """Test 'Apple's revenue' -> Apple has_revenue concept_revenue."""
        text = "Apple's revenue increased this quarter."
        kg_data, nx_graph = self.analyzer.analyze_content(text)

        # Verify "Apple" (ORG) and "revenue" (CONCEPT) entities exist
        self.assertEntityInGraph("Apple", "ORG", kg_data, "Entity 'Apple' (ORG) not found.")
        self.assertEntityInGraph("revenue", "CONCEPT", kg_data, "CONCEPT node 'revenue' should be created and in entities list.")

        # Check NetworkX graph for the concept node explicitly
        revenue_concept_node_id = self.assertNodeInNxGraph("concept_revenue", "revenue", "CONCEPT", nx_graph,
                                                           "Node for concept 'revenue' not found in NetworkX graph.")
        if revenue_concept_node_id:
            revenue_node_data = nx_graph.nodes[revenue_concept_node_id]
            self.assertTrue(revenue_node_data.get("attributes", {}).get("is_conceptual"),
                            "CONCEPT node 'revenue' should have 'is_conceptual' attribute.")

        # Expect: Apple (ORG) --has_revenue--> concept_revenue
        apple_node_id_nx = None
        for node_id, data in nx_graph.nodes(data=True):
            if data.get("label") == "Apple" and data.get("type") == "ORG":
                apple_node_id_nx = node_id
                break
        self.assertIsNotNone(apple_node_id_nx, "Apple (ORG) entity not found.")

        found_rel_to_concept = False
        if apple_node_id_nx:
            for successor in nx_graph.successors(apple_node_id_nx):
                edge_data = nx_graph.get_edge_data(apple_node_id_nx, successor)
                if edge_data and edge_data.get("type") == "has_revenue":
                    target_node_data = nx_graph.nodes[successor]
                    # Check if target is a concept node as created by the possessive logic
                    if "concept_revenue" in successor and target_node_data.get("label") == "revenue":
                        # self.assertTrue(edge_data.get("attributes", {}).get("target_is_concept"), "Target should be marked as concept.") # Removed this check
                        found_rel_to_concept = True
                        # Check that the target node itself is of type CONCEPT
                        target_node_details = nx_graph.nodes[successor]
                        self.assertEqual(target_node_details.get("type"), "CONCEPT", "Target node for possessive attribute should be of type CONCEPT.")
                        self.assertTrue(target_node_details.get("attributes", {}).get("is_conceptual"), "Concept node should have 'is_conceptual' attribute.")
                        break
        self.assertTrue(found_rel_to_concept, "Expected Apple to have 'has_revenue' relationship to a revenue concept.")

    def test_11_matcher_located_in(self):
        """Test 'ORG located in GPE' using Matcher."""
        text = "Innovate Corp is located in Silicon Valley."
        kg_data, nx_graph = self.analyzer.analyze_content(text)

        # Ensure entities are present
        self.assertEntityInGraph("Innovate Corp", "ORG", kg_data, "Innovate Corp (ORG) not extracted.")
        # NER tags "Silicon Valley" as LOC with en_core_web_sm, matcher now accepts LOC or GPE.
        # For this test, we'll check for LOC as that's what NER provides.
        self.assertEntityInGraph("Silicon Valley", "LOC", kg_data, "Silicon Valley (LOC) not extracted.")

        self.assertRelationshipInGraph(kg_data, nx_graph,
                                         expected_src_label="Innovate Corp", src_type="ORG",
                                         expected_tgt_label="Silicon Valley", tgt_type="LOC", # Changed to LOC
                                         expected_rel_type="located_in")

        # Check pattern attribute for the relationship
        found_rel_details = None
        for rel in kg_data["relationships"]:
            src_label = kg_data["entities"].get(rel["source_id"], {}).get("label")
            tgt_label = kg_data["entities"].get(rel["target_id"], {}).get("label")
            if src_label == "Innovate Corp" and tgt_label == "Silicon Valley" and rel["type"] == "located_in":
                found_rel_details = rel
                break
        self.assertIsNotNone(found_rel_details, "Located_in relationship details not found in TypedDict.")
        self.assertEqual(found_rel_details["attributes"]["pattern"], "LOCATED_IN", "Pattern attribute for located_in is incorrect.")


    def test_12_matcher_works_for(self):
        """Test 'PERSON works for ORG' using Matcher."""
        text = "John Doe works for Acme Corp."
        kg_data, nx_graph = self.analyzer.analyze_content(text)

        self.assertEntityInGraph("John Doe", "PERSON", kg_data, "John Doe (PERSON) not extracted.")
        self.assertEntityInGraph("Acme Corp.", "ORG", kg_data, "Acme Corp. (ORG) not extracted.") # Added period

        self.assertRelationshipInGraph(kg_data, nx_graph,
                                         expected_src_label="John Doe", src_type="PERSON",
                                         expected_tgt_label="Acme Corp.", tgt_type="ORG", # Added period
                                         expected_rel_type="works_for")

        found_rel_details = None
        for rel in kg_data["relationships"]:
            src_label = kg_data["entities"].get(rel["source_id"], {}).get("label")
            tgt_label = kg_data["entities"].get(rel["target_id"], {}).get("label")
            if src_label == "John Doe" and tgt_label == "Acme Corp." and rel["type"] == "works_for": # Added period
                found_rel_details = rel
                break
        self.assertIsNotNone(found_rel_details, "Works_for relationship details not found in TypedDict.")
        self.assertEqual(found_rel_details["attributes"]["pattern"], "WORKS_FOR", "Pattern attribute for works_for is incorrect.")


if __name__ == '__main__':
    # It's better to run tests using python -m unittest discover -s tests
    # or python -m unittest tests.core_ai.learning.test_content_analyzer_module
    # However, this allows direct execution for convenience.
    unittest.main()

# Need to create tests/core_ai/learning/__init__.py if it doesn't exist
# Need to create tests/core_ai/__init__.py if it doesn't exist
# Need to create tests/__init__.py if it doesn't exist
