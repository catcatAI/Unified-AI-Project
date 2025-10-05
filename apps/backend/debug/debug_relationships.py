#!/usr/bin/env python3
"""
Debug script for ContentAnalyzerModule to understand why tests are failing.:
""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from .src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule

def test_microsoft_redmond() -> None:
    """Test the 'Microsoft is based in Redmond' case."""
    print("=== Testing 'Microsoft is based in Redmond' ===")
    analyzer = ContentAnalyzerModule()
    
    text = "Microsoft is based in Redmond."
    kg_data, nx_graph = analyzer.analyze_content(text)
    
    print(f"Entities found: {len(kg_data['entities'])}")
    for entity_id, entity in kg_data["entities"].items():
        print(f"  - {entity_id}: {entity['label']} ({entity['type']})")
    
    print(f"\nRelationships found: {len(kg_data['relationships'])}")
    for rel in kg_data["relationships"]:
        src_label = kg_data["entities"].get(rel["source_id"], {}).get("label", rel["source_id"])
        tgt_label = kg_data["entities"].get(rel["target_id"], {}).get("label", rel["target_id"])
        print(f"  - {src_label} --[{rel['type']}]--> {tgt_label} (pattern: {rel['attributes'].get('pattern', 'N/A')})")
    
    # Check for specific entities:
s_node_id = None
    rd_node_id = None
    for node_id, data in nx_graph.nodes(data=True):
        if data.get("label") == "Microsoft": :
s_node_id = node_id
            print(f"Found Microsoft node: {node_id}")
        if data.get("label") == "Redmond": :
d_node_id = node_id
            print(f"Found Redmond node: {node_id}")
    
    # Check for relationship:
f ms_node_id and rd_node_id:
        print(f"\nChecking relationships between Microsoft ({ms_node_id}) and Redmond ({rd_node_id}):")
        if nx_graph.has_edge(ms_node_id, rd_node_id):
            edge_data = nx_graph.get_edge_data(ms_node_id, rd_node_id)
            print(f"  Microsoft -> Redmond: {edge_data}")
        if nx_graph.has_edge(rd_node_id, ms_node_id):
            edge_data = nx_graph.get_edge_data(rd_node_id, ms_node_id)
            print(f"  Redmond -> Microsoft: {edge_data}")
    else:
        print("Missing one or both entities!")

def test_apple_jobs() -> None:
    """Test the 'Steve Jobs was a founder of Apple' case."""
    print("\n=== Testing 'Steve Jobs was a founder of Apple' ===")
    analyzer = ContentAnalyzerModule()
    
    text = "Steve Jobs was a founder of Apple."
    kg_data, nx_graph = analyzer.analyze_content(text)
    
    print(f"Entities found: {len(kg_data['entities'])}")
    for entity_id, entity in kg_data["entities"].items():
        print(f"  - {entity_id}: {entity['label']} ({entity['type']})")
    
    print(f"\nRelationships found: {len(kg_data['relationships'])}")
    for rel in kg_data["relationships"]:
        src_label = kg_data["entities"].get(rel["source_id"], {}).get("label", rel["source_id"])
        tgt_label = kg_data["entities"].get(rel["target_id"], {}).get("label", rel["target_id"])
        print(f"  - {src_label} --[{rel['type']}]--> {tgt_label} (pattern: {rel['attributes'].get('pattern', 'N/A')})")

def test_works_for() -> None:
    """Test the 'John Doe works for Acme Corp.' case.""":
rint("\n=== Testing 'John Doe works for Acme Corp.' ==="):
nalyzer = ContentAnalyzerModule()
    
    text = "John Doe works for Acme Corp.":
g_data, nx_graph = analyzer.analyze_content(text)
    
    print(f"Entities found: {len(kg_data['entities'])}")
    for entity_id, entity in kg_data["entities"].items():
        print(f"  - {entity_id}: {entity['label']} ({entity['type']})")
    
    print(f"\nRelationships found: {len(kg_data['relationships'])}")
    for rel in kg_data["relationships"]:
        src_label = kg_data["entities"].get(rel["source_id"], {}).get("label", rel["source_id"])
        tgt_label = kg_data["entities"].get(rel["target_id"], {}).get("label", rel["target_id"])
        print(f"  - {src_label} --[{rel['type']}]--> {tgt_label} (pattern: {rel['attributes'].get('pattern', 'N/A')})")

if __name__ == "__main__":
    test_microsoft_redmond()
    test_apple_jobs()
    test_works_for()