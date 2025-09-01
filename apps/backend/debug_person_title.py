import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from apps.backend.src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule

def debug_person_title():
    # Initialize the analyzer
    analyzer = ContentAnalyzerModule()
    
    print("=== Debugging PERSON_IS_TITLE_OF_ORG Pattern ===")
    
    # Test case: Steve Jobs was a founder of Apple
    text = "Steve Jobs was a founder of Apple."
    print(f"Text: {text}")
    
    kg_data, nx_graph = analyzer.analyze_content(text)
    
    # Print entities
    print(f"\nEntities found: {len(kg_data['entities'])}")
    for entity_id, entity in kg_data["entities"].items():
        print(f"  {entity_id}: '{entity['label']}' (type: {entity['type']})")
    
    # Print relationships
    print(f"\nRelationships found: {len(kg_data['relationships'])}")
    for i, rel in enumerate(kg_data['relationships']):
        src_label = kg_data["entities"].get(rel["source_id"], {}).get("label", rel["source_id"])
        tgt_label = kg_data["entities"].get(rel["target_id"], {}).get("label", rel["target_id"])
        print(f"  {i+1}. {src_label} --{rel['type']}--> {tgt_label} (pattern: {rel['attributes'].get('pattern', 'N/A')})")
    
    # Check for specific entities
    apple_node_id = None
    steve_jobs_node_id = None
    for entity_id, entity in kg_data["entities"].items():
        if entity["label"] == "Apple":
            apple_node_id = entity_id
        if entity["label"] == "Steve Jobs":
            steve_jobs_node_id = entity_id
    
    print(f"\nApple node ID: {apple_node_id}")
    print(f"Steve Jobs node ID: {steve_jobs_node_id}")
    
    # Check for relationship between Apple and Steve Jobs
    found_relationship = False
    if apple_node_id and steve_jobs_node_id:
        for rel in kg_data["relationships"]:
            if ((rel["source_id"] == apple_node_id and rel["target_id"] == steve_jobs_node_id) or
                (rel["source_id"] == steve_jobs_node_id and rel["target_id"] == apple_node_id)):
                found_relationship = True
                print(f"Found relationship: {rel}")
                break
    
    if found_relationship:
        print("\nSUCCESS: Found relationship between Apple and Steve Jobs!")
    else:
        print("\nFAILURE: No relationship found between Apple and Steve Jobs!")

if __name__ == "__main__":
    debug_person_title()