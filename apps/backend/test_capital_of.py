import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Fix the import path
try:
    from ai.learning.content_analyzer_module import ContentAnalyzerModule
except ImportError:
    # Try alternative import path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from src.ai.learning.content_analyzer_module import ContentAnalyzerModule

def test_capital_of_pattern():
    # Initialize the ContentAnalyzerModule
    analyzer = ContentAnalyzerModule(spacy_model_name="en_core_web_sm")
    
    # Test text
    text = "Paris is the capital of France."
    print(f"Testing text: {text}")
    
    # Analyze the content
    kg_data, nx_graph = analyzer.analyze_content(text)
    
    # Print results
    print("\nEntities:")
    for entity_id, entity in kg_data["entities"].items():
        print(f"  {entity_id}: {entity['label']} ({entity['type']})")
    
    print("\nRelationships:")
    for rel in kg_data["relationships"]:
        source_label = kg_data["entities"][rel["source_id"]]["label"]
        target_label = kg_data["entities"][rel["target_id"]]["label"]
        print(f"  {source_label} --{rel['type']}--> {target_label}")
    
    # Check if we have the expected relationship: France --has_capital--> Paris
    found_expected_rel = False
    for rel in kg_data["relationships"]:
        source_label = kg_data["entities"][rel["source_id"]]["label"]
        target_label = kg_data["entities"][rel["target_id"]]["label"]
        if source_label == "France" and target_label == "Paris" and rel["type"] == "has_capital":
            found_expected_rel = True
            break
    
    if found_expected_rel:
        print("\n✓ Found expected relationship: France --has_capital--> Paris")
    else:
        print("\n✗ Did not find expected relationship: France --has_capital--> Paris")
        
        # Let's see if we have any other capital-related relationships
        print("\nLooking for any capital-related relationships:")
        for rel in kg_data["relationships"]:
            source_label = kg_data["entities"][rel["source_id"]]["label"]
            target_label = kg_data["entities"][rel["target_id"]]["label"]
            if "capital" in rel["type"]:
                print(f"  Found: {source_label} --{rel['type']}--> {target_label}")

if __name__ == "__main__":
    test_capital_of_pattern()