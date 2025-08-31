import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule

def debug_test():
    # Initialize the analyzer
    analyzer = ContentAnalyzerModule()
    
    print("=== Debug Test ===")
    
    # Test case: Microsoft is based in Redmond
    text = "Microsoft is based in Redmond."
    print(f"Text: {text}")
    
    kg_data, nx_graph = analyzer.analyze_content(text)
    
    # Print entities
    print(f"Entities found: {len(kg_data['entities'])}")
    for entity_id, entity in kg_data["entities"].items():
        print(f"  {entity_id}: '{entity['label']}' (type: {entity['type']})")
    
    # Print relationships
    print(f"Relationships found: {len(kg_data['relationships'])}")
    for i, rel in enumerate(kg_data["relationships"]):
        src_label = kg_data["entities"].get(rel["source_id"], {}).get("label", rel["source_id"])
        tgt_label = kg_data["entities"].get(rel["target_id"], {}).get("label", rel["target_id"])
        print(f"  {i+1}. {src_label} --{rel['type']}--> {tgt_label} (pattern: {rel['attributes'].get('pattern', 'N/A')})")

if __name__ == "__main__":
    debug_test()