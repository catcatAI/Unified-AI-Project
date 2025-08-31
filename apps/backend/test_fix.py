import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule

def test_entity_extraction():
    """Test entity extraction and relationship creation"""
    analyzer = ContentAnalyzerModule()
    
    # Test simple entity extraction
    text = "Apple Inc. is a company. Steve Jobs was a person."
    kg_data, nx_graph = analyzer.analyze_content(text)
    
    print(f"Entities extracted: {len(kg_data['entities'])}")
    print(f"Nodes in graph: {nx_graph.number_of_nodes()}")
    print(f"Entities match: {len(kg_data['entities']) == nx_graph.number_of_nodes()}")
    
    # Print entities
    for entity_id, entity in kg_data["entities"].items():
        print(f"Entity: {entity['label']} (Type: {entity['type']})")
    
    # Test located_in relationship
    text2 = "Microsoft is based in Redmond."
    kg_data2, nx_graph2 = analyzer.analyze_content(text2)
    
    print(f"\nLocated_in test:")
    print(f"Entities extracted: {len(kg_data2['entities'])}")
    print(f"Nodes in graph: {nx_graph2.number_of_nodes()}")
    print(f"Relationships: {len(kg_data2['relationships'])}")
    
    for rel in kg_data2["relationships"]:
        src_label = kg_data2["entities"][rel["source_id"]]["label"]
        tgt_label = kg_data2["entities"][rel["target_id"]]["label"]
        print(f"Relationship: {src_label} --{rel['type']}--> {tgt_label}")
    
    # Test works_for relationship
    text3 = "John Doe works for Acme Corp."
    kg_data3, nx_graph3 = analyzer.analyze_content(text3)
    
    print(f"\nWorks_for test:")
    print(f"Entities extracted: {len(kg_data3['entities'])}")
    print(f"Nodes in graph: {nx_graph3.number_of_nodes()}")
    print(f"Relationships: {len(kg_data3['relationships'])}")
    
    for rel in kg_data3["relationships"]:
        src_label = kg_data3["entities"][rel["source_id"]]["label"]
        tgt_label = kg_data3["entities"][rel["target_id"]]["label"]
        print(f"Relationship: {src_label} --{rel['type']}--> {tgt_label}")

if __name__ == "__main__":
    test_entity_extraction()