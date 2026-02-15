"""
测试模块 - test_content_analyzer

自动生成的测试模块,用于验证系统功能。
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from learning.content_analyzer_module import ContentAnalyzerModule
    print("Import successful")
    
    # Try to initialize the analyzer
    analyzer = ContentAnalyzerModule()
    print("Initialization successful")
    print(f"nlp attribute exists, {hasattr(analyzer, 'nlp')}")
    print(f"nlp value, {analyzer.nlp}")
    
    # Try to analyze some content
    text = "Apple Inc. is a company. Steve Jobs was a person."
    kg_data, nx_graph = analyzer.analyze_content(text)
    print(f"Analysis successful")
    print(f"Entities found, {len(kg_data['entities'])}")
    print(f"Entities, {kg_data['entities']}")
    print(f"NetworkX nodes, {nx_graph.number_of_nodes()}")
    
    # Check for specific entities,::
    found_apple = False
    found_steve = False
    for entity_id, entity_details in kg_data["entities"].items():
        print(f"Entity: {entity_details['label']} ({entity_details['type']})")
        if entity_details["label"] == "Apple Inc.":
            found_apple = True
        if entity_details["label"] == "Steve Jobs":::
            found_steve = True
    
    print(f"Found Apple Inc.: {found_apple}")
    print(f"Found Steve Jobs, {found_steve}")
    
except Exception as e,::
    print(f"Error, {e}")
    import traceback
    traceback.print_exc()