import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from apps.backend.src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule

def debug_content_analyzer():
    # Initialize the analyzer
    analyzer = ContentAnalyzerModule()
    
    print("=== Debugging ContentAnalyzerModule Relationship Extraction ===")
    
    # Test case 1: Microsoft is based in Redmond (test_05_prep_object_relationship)
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
    
    # Check for Microsoft and Redmond entities
    ms_node_id = None
    rd_node_id = None
    for entity_id, entity in kg_data1["entities"].items():
        if entity["label"] == "Microsoft":
            ms_node_id = entity_id
        if entity["label"] == "Redmond":
            rd_node_id = entity_id
    
    print(f"Microsoft node ID: {ms_node_id}")
    print(f"Redmond node ID: {rd_node_id}")
    
    # Check for relationship
    found_rel_object = None
    if ms_node_id and rd_node_id:
        for rel in kg_data1["relationships"]:
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
        
    # Test case 2: Steve Jobs was a founder of Apple (test_06_noun_prep_noun_relationship_of)
    print("\n\n2. Testing 'Steve Jobs was a founder of Apple'")
    text2 = "Steve Jobs was a founder of Apple."
    print(f"Text: {text2}")
    
    kg_data2, nx_graph2 = analyzer.analyze_content(text2)
    
    # Print entities
    print(f"Entities found: {len(kg_data2['entities'])}")
    for entity_id, entity in kg_data2["entities"].items():
        print(f"  {entity_id}: '{entity['label']}' (type: {entity['type']})")
    
    # Print relationships
    print(f"Relationships found: {len(kg_data2['relationships'])}")
    for i, rel in enumerate(kg_data2["relationships"]):
        src_label = kg_data2["entities"].get(rel["source_id"], {}).get("label", rel["source_id"])
        tgt_label = kg_data2["entities"].get(rel["target_id"], {}).get("label", rel["target_id"])
        print(f"  {i+1}. {src_label} --{rel['type']}--> {tgt_label} (pattern: {rel['attributes'].get('pattern', 'N/A')})")
    
    # Check for Apple and Steve Jobs entities
    apple_node_id = None
    steve_node_id = None
    for entity_id, entity in kg_data2["entities"].items():
        if entity["label"] == "Apple":
            apple_node_id = entity_id
        if entity["label"] == "Steve Jobs":
            steve_node_id = entity_id
    
    print(f"Apple node ID: {apple_node_id}")
    print(f"Steve Jobs node ID: {steve_node_id}")
    
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

    print(f"Found relationship: {found_rel_object2}")
    
    if found_rel_object2:
        print("SUCCESS: Found expected relationship!")
    else:
        print("FAILURE: Expected relationship not found!")

    # Test case 3: John Doe works for Acme Corp. (test_12_matcher_works_for)
    print("\n\n3. Testing 'John Doe works for Acme Corp.'")
    text3 = "John Doe works for Acme Corp."
    print(f"Text: {text3}")
    
    kg_data3, nx_graph3 = analyzer.analyze_content(text3)
    
    # Print entities
    print(f"Entities found: {len(kg_data3['entities'])}")
    for entity_id, entity in kg_data3["entities"].items():
        print(f"  {entity_id}: '{entity['label']}' (type: {entity['type']})")
    
    # Print relationships
    print(f"Relationships found: {len(kg_data3['relationships'])}")
    for i, rel in enumerate(kg_data3["relationships"]):
        src_label = kg_data3["entities"].get(rel["source_id"], {}).get("label", rel["source_id"])
        tgt_label = kg_data3["entities"].get(rel["target_id"], {}).get("label", rel["target_id"])
        print(f"  {i+1}. {src_label} --{rel['type']}--> {tgt_label} (pattern: {rel['attributes'].get('pattern', 'N/A')})")
    
    # Check for John Doe and Acme Corp. entities
    john_node_id = None
    acme_node_id = None
    for entity_id, entity in kg_data3["entities"].items():
        if entity["label"] == "John Doe":
            john_node_id = entity_id
        if entity["label"] == "Acme Corp.":
            acme_node_id = entity_id
    
    print(f"John Doe node ID: {john_node_id}")
    print(f"Acme Corp. node ID: {acme_node_id}")
    
    # Check for relationship
    found_rel_object3 = None
    if john_node_id and acme_node_id:
        for rel in kg_data3["relationships"]:
            src_label = kg_data3["entities"].get(rel["source_id"], {}).get("label", rel["source_id"])
            tgt_label = kg_data3["entities"].get(rel["target_id"], {}).get("label", rel["target_id"])
            if src_label == "John Doe" and tgt_label == "Acme Corp." and rel["type"] == "works_for":
                found_rel_object3 = rel
                break

    print(f"Found relationship: {found_rel_object3}")
    
    if found_rel_object3:
        print("SUCCESS: Found expected relationship!")
    else:
        print("FAILURE: Expected relationship not found!")

    # Test case 4: Innovate Corp is located in Silicon Valley (test_11_matcher_located_in)
    print("\n\n4. Testing 'Innovate Corp is located in Silicon Valley'")
    text4 = "Innovate Corp is located in Silicon Valley."
    print(f"Text: {text4}")
    
    kg_data4, nx_graph4 = analyzer.analyze_content(text4)
    
    # Print entities
    print(f"Entities found: {len(kg_data4['entities'])}")
    for entity_id, entity in kg_data4["entities"].items():
        print(f"  {entity_id}: '{entity['label']}' (type: {entity['type']})")
    
    # Print relationships
    print(f"Relationships found: {len(kg_data4['relationships'])}")
    for i, rel in enumerate(kg_data4["relationships"]):
        src_label = kg_data4["entities"].get(rel["source_id"], {}).get("label", rel["source_id"])
        tgt_label = kg_data4["entities"].get(rel["target_id"], {}).get("label", rel["target_id"])
        print(f"  {i+1}. {src_label} --{rel['type']}--> {tgt_label} (pattern: {rel['attributes'].get('pattern', 'N/A')})")
    
    # Check for Innovate Corp and Silicon Valley entities
    innovate_node_id = None
    valley_node_id = None
    for entity_id, entity in kg_data4["entities"].items():
        if entity["label"] == "Innovate Corp":
            innovate_node_id = entity_id
        if entity["label"] == "Silicon Valley":
            valley_node_id = entity_id
    
    print(f"Innovate Corp node ID: {innovate_node_id}")
    print(f"Silicon Valley node ID: {valley_node_id}")
    
    # Check for relationship
    found_rel_object4 = None
    if innovate_node_id and valley_node_id:
        for rel in kg_data4["relationships"]:
            src_label = kg_data4["entities"].get(rel["source_id"], {}).get("label", rel["source_id"])
            tgt_label = kg_data4["entities"].get(rel["target_id"], {}).get("label", rel["target_id"])
            if src_label == "Innovate Corp" and tgt_label == "Silicon Valley" and rel["type"] == "located_in":
                found_rel_object4 = rel
                break

    print(f"Found relationship: {found_rel_object4}")
    
    if found_rel_object4:
        print("SUCCESS: Found expected relationship!")
    else:
        print("FAILURE: Expected relationship not found!")

if __name__ == "__main__":
    debug_content_analyzer()