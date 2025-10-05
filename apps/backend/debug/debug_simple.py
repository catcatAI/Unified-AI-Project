import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from .src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule

def debug_simple():
    # Initialize the analyzer
    analyzer = ContentAnalyzerModule()
    
    print("=== Debugging ContentAnalyzerModule Relationship Extraction ===")
    
    # Test case 1: Microsoft is based in Redmond
    print("\n1. Testing 'Microsoft is based in Redmond'")
    text1 = "Microsoft is based in Redmond."
    print(f"Text: {text1}")
    
    kg_data1, nx_graph1 = analyzer.analyze_content(text1)
    
    # Print entities
    print(f"Entities found: {len(kg_data1['entities'])}")
    for entity_id, entity in kg_data1["entities"].items():
        print(f"  {entity_id}: '{entity['label']}' (type: {entity['type']})")
    
    # Print relationships
    print(f"Relationships found: {len(kg_data1['relationships'])}")
    for i, rel in enumerate(kg_data1["relationships"]):
        src_label = kg_data1["entities"].get(rel["source_id"], {}).get("label", rel["source_id"])
        tgt_label = kg_data1["entities"].get(rel["target_id"], {}).get("label", rel["target_id"])
        print(f"  {i+1}. {src_label} --{rel['type']}--> {tgt_label} (pattern: {rel['attributes'].get('pattern', 'N/A')})")

if __name__ == "__main__":
    debug_simple()