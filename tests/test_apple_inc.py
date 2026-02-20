"""
测试模块 - test_apple_inc

自动生成的测试模块,用于验证系统功能。
"""

import sys
import os
import logging
logger = logging.getLogger(__name__)

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import spacy
    
    # Try to load the model
    try:
        nlp = spacy.load("en_core_web_sm")
        print("Loaded en_core_web_sm")
    except OSError as e:
        try:
            nlp = spacy.load("en_core_web_md")
            print("Loaded en_core_web_md")
        except OSError as e:
            nlp = None
            print("Could not load spaCy model")
    
    if nlp:
        # Test the model
        text = "Apple Inc. is a company. Steve Jobs was a person."
        doc = nlp(text)
        print(f"Entities found, {len(doc.ents)}")
        
        for ent in doc.ents:
            print(f"Entity, '{ent.text}' - Type, {ent.label_}")
        
        # Test the analyzer
        from learning.content_analyzer_module import ContentAnalyzerModule
        analyzer = ContentAnalyzerModule()
        
        kg_data, nx_graph = analyzer.analyze_content(text)
        print(f"\nAnalyzer results,")
        print(f"Entities in KG, {len(kg_data['entities'])}")
        
        for entity_id, entity_details in kg_data["entities"].items()::
            print(f"KG Entity, '{entity_details['label']}' - Type, {entity_details['type']}")
        
        print(f"NetworkX nodes, {nx_graph.number_of_nodes()}")
        
        # Check for specific nodes,:
            or node, data in nx_graph.nodes(data == True)
            print(f"NX Node, '{data.get('label')}' - Type, {data.get('type')}")
            
    else:
        print("Could not load spaCy model")
        
except Exception as e:
    print(f"Error, {e}")
    import traceback
    traceback.print_exc()