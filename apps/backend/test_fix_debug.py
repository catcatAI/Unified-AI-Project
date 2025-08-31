import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule

def test_fix_debug():
    # Initialize the analyzer
    analyzer = ContentAnalyzerModule()
    
    # Test the specific case that's failing
    text = "Microsoft is based in Redmond."
    print(f"Analyzing text: {text}")
    
    # Process the text
    kg_data, nx_graph = analyzer.analyze_content(text)
    
    # Print entities
    print(f"\nEntities found: {len(kg_data['entities'])}")
    for entity_id, entity in kg_data["entities"].items():
        print(f"  {entity_id}: '{entity['label']}' (type: {entity['type']})")
    
    # Print relationships
    print(f"\nRelationships found: {len(kg_data['relationships'])}")
    for i, rel in enumerate(kg_data["relationships"]):
        src_label = kg_data["entities"].get(rel["source_id"], {}).get("label", rel["source_id"])
        tgt_label = kg_data["entities"].get(rel["target_id"], {}).get("label", rel["target_id"])
        print(f"  {i+1}. {src_label} --{rel['type']}--> {tgt_label} (pattern: {rel['attributes'].get('pattern', 'N/A')})")
    
    # Check for Microsoft and Redmond entities
    ms_node_id = None
    rd_node_id = None
    for entity_id, entity in kg_data["entities"].items():
        if entity["label"] == "Microsoft":
            ms_node_id = entity_id
        if entity["label"] == "Redmond":
            rd_node_id = entity_id
    
    print(f"\nMicrosoft node ID: {ms_node_id}")
    print(f"Redmond node ID: {rd_node_id}")
    
    # Check for relationship
    found_rel_object = None
    if ms_node_id and rd_node_id:
        for rel in kg_data["relationships"]:
            if rel["source_id"] == ms_node_id and \
               rel["target_id"] == rd_node_id and \
               rel["type"] in ["located_in", "base_in", "be_in"]:
                found_rel_object = rel
                break

    print(f"Found relationship: {found_rel_object}")
    
    if found_rel_object:
        print("SUCCESS: Found expected relationship!")
    else:
        print("FAILURE: Expected relationship not found!")

if __name__ == "__main__":
    test_fix_debug()