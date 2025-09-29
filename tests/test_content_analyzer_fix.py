import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from learning.content_analyzer_module import ContentAnalyzerModule

def test_content_analyzer() -> None:
    print("Testing ContentAnalyzerModule...")
    
    try:
        # Initialize the analyzer
        analyzer = ContentAnalyzerModule()
        print("✓ ContentAnalyzerModule initialized successfully")
        
        # Test basic entity extraction
        text = "Apple Inc. is a company. Steve Jobs was a person."
        print(f"Analyzing text: {text}")
        
        kg_data, nx_graph = analyzer.analyze_content(text)
        
        print(f"Entities found: {len(kg_data['entities'])}")
        for entity_id, entity in kg_data['entities'].items():
            print(f"  - {entity['label']} ({entity['type']})")
            
        # Check if Apple Inc. is found
        apple_inc_found = any(entity['label'] == 'Apple Inc.' for entity in kg_data['entities'].values())
        if apple_inc_found:
            print("✓ Apple Inc. entity found")
        else:
            print("✗ Apple Inc. entity not found")
            
        # Check if Steve Jobs is found
        steve_jobs_found = any(entity['label'] == 'Steve Jobs' for entity in kg_data['entities'].values())
        if steve_jobs_found:
            print("✓ Steve Jobs entity found")
        else:
            print("✗ Steve Jobs entity not found")
            
        return apple_inc_found and steve_jobs_found
        
    except Exception as e:
        print(f"✗ Error testing ContentAnalyzerModule: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_content_analyzer()
    if success:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed!")
        sys.exit(1)