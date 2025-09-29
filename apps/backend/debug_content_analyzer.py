#!/usr/bin/env python3
"""
Debug script for ContentAnalyzerModule to understand why tests are failing.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from apps.backend.src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule

# Create an instance of the ContentAnalyzerModule
analyzer = ContentAnalyzerModule()

# Test the specific case
text = "Paris is the capital of France."
print(f"Analyzing text: {text}")
kg_data, nx_graph = analyzer.analyze_content(text)

print(f"Entities: {kg_data['entities']}")
print(f"Relationships: {kg_data['relationships']}")

# Check for the specific relationship
found_relationship = False
for rel in kg_data['relationships']:
    source_label = kg_data['entities'][rel['source_id']]['label']
    target_label = kg_data['entities'][rel['target_id']]['label']
    if source_label == "France" and target_label == "Paris" and rel['type'] == "has_capital":
        found_relationship = True
        break

print(f"Found has_capital relationship: {found_relationship}")

def test_content_analyzer() -> None:
    # Initialize the ContentAnalyzerModule
    analyzer = ContentAnalyzerModule()
    
    # Test cases from the failing tests
    test_cases = [
        "Apple Inc. is a company. Steve Jobs was a person.",
        "Steve Jobs was a founder of Apple.",
        "Sundar Pichai is the CEO of Google.",
        "Paris is the capital of France.",
        "Microsoft is based in Redmond.",
        "John Doe works for Acme Corp.",
        "Satya Nadella is CEO of Microsoft.",
        "Jane Doe is Founder of ExampleCorp."
    ]
    
    for i, text in enumerate(test_cases):
        print(f"\n=== Test Case {i+1}: {text} ===")
        try:
            kg_data, nx_graph = analyzer.analyze_content(text)
            
            print(f"Entities ({len(kg_data['entities'])}):")
            for entity_id, entity in kg_data["entities"].items():
                print(f"  {entity_id}: {entity['label']} ({entity['type']})")
                
            print(f"Relationships ({len(kg_data['relationships'])}):")
            for rel in kg_data["relationships"]:
                source_label = kg_data["entities"].get(rel["source_id"], {}).get("label", rel["source_id"])
                target_label = kg_data["entities"].get(rel["target_id"], {}).get("label", rel["target_id"])
                print(f"  {source_label} --[{rel['type']}]--> {target_label} (pattern: {rel['attributes'].get('pattern', 'N/A')})")
                
            print(f"Graph nodes: {nx_graph.number_of_nodes()}")
            print(f"Graph edges: {nx_graph.number_of_edges()}")
            
        except Exception as e:
            print(f"Error processing text: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_content_analyzer()