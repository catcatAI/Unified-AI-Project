import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from apps.backend.src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule

def verify_all_fixes():
    # Initialize the analyzer
    analyzer = ContentAnalyzerModule()
    
    print("=== Verifying All ContentAnalyzerModule Fixes ===")
    
    # Test case 1: Microsoft is based in Redmond (test_05_prep_object_relationship)
    print("\n1. Testing 'Microsoft is based in Redmond'")
    text1 = "Microsoft is based in Redmond."
    print(f"Text: {text1}")
    
    kg_data1, nx_graph1 = analyzer.analyze_content(text1)
    
    # Check for Microsoft and Redmond entities
    ms_node_id = None
    rd_node_id = None
    for entity_id, entity in kg_data1["entities"].items():
        if entity["label"] == "Microsoft":
            ms_node_id = entity_id
        if entity["label"] == "Redmond":
            rd_node_id = entity_id
    
    # Check for relationship
    found_rel_object1 = None
    if ms_node_id and rd_node_id:
        for rel in kg_data1["relationships"]:
            if rel["source_id"] == ms_node_id and \
               rel["target_id"] == rd_node_id and \
               rel["type"] in ["located_in", "base_in", "be_in"]:
                found_rel_object1 = rel
                break

    test1_success = found_rel_object1 is not None
    print(f"Test 1 result: {'SUCCESS' if test1_success else 'FAILURE'}")
    
    # Test case 2: Steve Jobs was a founder of Apple (test_06_noun_prep_noun_relationship_of)
    print("\n2. Testing 'Steve Jobs was a founder of Apple'")
    text2 = "Steve Jobs was a founder of Apple."
    print(f"Text: {text2}")
    
    kg_data2, nx_graph2 = analyzer.analyze_content(text2)
    
    # Check for Apple and Steve Jobs entities
    apple_node_id = None
    steve_node_id = None
    for entity_id, entity in kg_data2["entities"].items():
        if entity["label"] == "Apple":
            apple_node_id = entity_id
        if entity["label"] == "Steve Jobs":
            steve_node_id = entity_id
    
    # Check for relationship
    found_rel_object2 = None
    if apple_node_id and steve_node_id:
        for rel in kg_data2["relationships"]:
            src_label = kg_data2["entities"].get(rel["source_id"], {}).get("label", rel["source_id"])
            tgt_label = kg_data2["entities"].get(rel["target_id"], {}).get("label", rel["target_id"])
            if src_label == "Apple" and tgt_label == "Steve Jobs" and "founder" in rel["type"]:
                found_rel_object2 = rel
                break
            if src_label == "Steve Jobs" and tgt_label == "Apple" and "founder" in rel["type"]:
                found_rel_object2 = rel
                break

    test2_success = found_rel_object2 is not None
    print(f"Test 2 result: {'SUCCESS' if test2_success else 'FAILURE'}")
    
    # Test case 3: John Doe works for Acme Corp. (test_12_matcher_works_for)
    print("\n3. Testing 'John Doe works for Acme Corp.'")
    text3 = "John Doe works for Acme Corp."
    print(f"Text: {text3}")
    
    kg_data3, nx_graph3 = analyzer.analyze_content(text3)
    
    # Check for John Doe and Acme Corp. entities
    john_node_id = None
    acme_node_id = None
    for entity_id, entity in kg_data3["entities"].items():
        if entity["label"] == "John Doe":
            john_node_id = entity_id
        if entity["label"] == "Acme Corp.":
            acme_node_id = entity_id
    
    # Check for relationship
    found_rel_object3 = None
    if john_node_id and acme_node_id:
        for rel in kg_data3["relationships"]:
            src_label = kg_data3["entities"].get(rel["source_id"], {}).get("label", rel["source_id"])
            tgt_label = kg_data3["entities"].get(rel["target_id"], {}).get("label", rel["target_id"])
            if src_label == "John Doe" and tgt_label == "Acme Corp." and rel["type"] == "works_for":
                found_rel_object3 = rel
                break

    test3_success = found_rel_object3 is not None
    print(f"Test 3 result: {'SUCCESS' if test3_success else 'FAILURE'}")
    
    # Test case 4: Sundar Pichai is the CEO of Google (test_07_noun_of_noun_org_has_attribute)
    print("\n4. Testing 'Sundar Pichai is the CEO of Google'")
    text4 = "Sundar Pichai is the CEO of Google."
    print(f"Text: {text4}")
    
    kg_data4, nx_graph4 = analyzer.analyze_content(text4)
    
    # Check for Google and Sundar Pichai entities
    google_node_id = None
    sundar_node_id = None
    for entity_id, entity in kg_data4["entities"].items():
        if entity["label"] == "Google":
            google_node_id = entity_id
        if entity["label"] == "Sundar Pichai":
            sundar_node_id = entity_id
    
    # Check for relationship
    found_rel_object4 = None
    if google_node_id and sundar_node_id:
        for rel in kg_data4["relationships"]:
            src_label = kg_data4["entities"].get(rel["source_id"], {}).get("label", rel["source_id"])
            tgt_label = kg_data4["entities"].get(rel["target_id"], {}).get("label", rel["target_id"])
            if src_label == "Google" and tgt_label == "Sundar Pichai" and rel["type"] == "has_ceo":
                found_rel_object4 = rel
                break

    test4_success = found_rel_object4 is not None
    print(f"Test 4 result: {'SUCCESS' if test4_success else 'FAILURE'}")
    
    # Summary
    print("\n=== Summary ===")
    print(f"Test 1 (Microsoft based in Redmond): {'PASS' if test1_success else 'FAIL'}")
    print(f"Test 2 (Steve Jobs founder of Apple): {'PASS' if test2_success else 'FAIL'}")
    print(f"Test 3 (John Doe works for Acme Corp): {'PASS' if test3_success else 'FAIL'}")
    print(f"Test 4 (Sundar Pichai CEO of Google): {'PASS' if test4_success else 'FAIL'}")
    
    all_tests_passed = test1_success and test2_success and test3_success and test4_success
    print(f"\nOverall result: {'ALL TESTS PASSED' if all_tests_passed else 'SOME TESTS FAILED'}")
    
    return all_tests_passed

if __name__ == "__main__":
    verify_all_fixes()