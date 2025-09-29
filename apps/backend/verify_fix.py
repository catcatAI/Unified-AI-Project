# -*- coding: utf-8 -*-
"""
Verification script to check if the fixes work
"""

import sys
import os

# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Change to the correct directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from learning.content_analyzer_module import ContentAnalyzerModule

def test_fixed_cases() -> None:
    """Test the cases that were previously failing"""
    print("=== Verifying fixes ===")
    
    # Test case 1: Microsoft is based in Redmond
    print("\n1. Testing 'Microsoft is based in Redmond'")
    analyzer = ContentAnalyzerModule()
    text = "Microsoft is based in Redmond."
    kg_data, nx_graph = analyzer.analyze_content(text)
    
    # Find entities
    ms_node_id = None
    rd_node_id = None
    for node_id, data in nx_graph.nodes(data=True):
        if data.get("label") == "Microsoft": ms_node_id = node_id
        if data.get("label") == "Redmond": rd_node_id = node_id
    
    # Check relationship exists
    relationship_found = False
    if ms_node_id and rd_node_id:
        if nx_graph.has_edge(ms_node_id, rd_node_id):
            edge_data = nx_graph.get_edge_data(ms_node_id, rd_node_id)
            if edge_data.get("type") == "located_in":
                relationship_found = True
    
    print(f"  Entities found: Microsoft={ms_node_id is not None}, Redmond={rd_node_id is not None}")
    print(f"  Relationship found: {relationship_found}")
    assert ms_node_id is not None, "Microsoft entity not found"
    assert rd_node_id is not None, "Redmond entity not found"
    assert relationship_found, "located_in relationship not found"
    print("  ✓ PASSED")
    
    # Test case 2: Steve Jobs was a founder of Apple
    print("\n2. Testing 'Steve Jobs was a founder of Apple'")
    analyzer = ContentAnalyzerModule()
    text = "Steve Jobs was a founder of Apple."
    kg_data, nx_graph = analyzer.analyze_content(text)
    
    # Find entities
    apple_node_id = None
    steve_node_id = None
    for node_id, data in nx_graph.nodes(data=True):
        if data.get("label") == "Apple": apple_node_id = node_id
        if data.get("label") == "Steve Jobs": steve_node_id = node_id
    
    # Check relationship exists: Apple --has_founder--> Steve Jobs
    relationship_found = False
    if apple_node_id and steve_node_id:
        if nx_graph.has_edge(apple_node_id, steve_node_id):
            edge_data = nx_graph.get_edge_data(apple_node_id, steve_node_id)
            if edge_data.get("type") == "has_founder":
                relationship_found = True
    
    print(f"  Entities found: Apple={apple_node_id is not None}, Steve Jobs={steve_node_id is not None}")
    print(f"  Relationship found: {relationship_found}")
    assert apple_node_id is not None, "Apple entity not found"
    assert steve_node_id is not None, "Steve Jobs entity not found"
    assert relationship_found, "has_founder relationship not found"
    print("  ✓ PASSED")
    
    # Test case 3: John Doe works for Acme Corp
    print("\n3. Testing 'John Doe works for Acme Corp.'")
    analyzer = ContentAnalyzerModule()
    text = "John Doe works for Acme Corp."
    kg_data, nx_graph = analyzer.analyze_content(text)
    
    # Find entities
    john_node_id = None
    acme_node_id = None
    for node_id, data in nx_graph.nodes(data=True):
        if data.get("label") == "John Doe": john_node_id = node_id
        if data.get("label") == "Acme Corp.": acme_node_id = node_id
    
    # Check relationship exists: John Doe --works_for--> Acme Corp.
    relationship_found = False
    if john_node_id and acme_node_id:
        if nx_graph.has_edge(john_node_id, acme_node_id):
            edge_data = nx_graph.get_edge_data(john_node_id, acme_node_id)
            if edge_data.get("type") == "works_for":
                relationship_found = True
    
    print(f"  Entities found: John Doe={john_node_id is not None}, Acme Corp.={acme_node_id is not None}")
    print(f"  Relationship found: {relationship_found}")
    assert john_node_id is not None, "John Doe entity not found"
    assert acme_node_id is not None, "Acme Corp. entity not found"
    assert relationship_found, "works_for relationship not found"
    print("  ✓ PASSED")
    
    print("\n=== All tests passed! ===")

if __name__ == "__main__":
    test_fixed_cases()