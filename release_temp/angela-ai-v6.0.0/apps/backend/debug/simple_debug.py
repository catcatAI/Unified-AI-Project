import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from .src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule

# Initialize the ContentAnalyzerModule
analyzer = ContentAnalyzerModule()

# Simple test
text = 'Microsoft is based in Redmond.'
print(f'Analyzing: {text}')
kg_data, nx_graph = analyzer.analyze_content(text)

print(f'Entities: {len(kg_data["entities"])}')
for entity_id, entity in kg_data['entities'].items():
    print(f'  {entity_id}: {entity["label"]} ({entity["type"]})')

print(f'Relationships: {len(kg_data["relationships"])}')
for rel in kg_data['relationships']:
    source_label = (
        kg_data['entities'].get(rel['source_id'], {}).get('label', rel['source_id'])
    )
    target_label = (
        kg_data['entities'].get(rel['target_id'], {}).get('label', rel['target_id'])
    )
    print(f'  {source_label} --[{rel["type"]}]--> {target_label}')

print(f'Graph nodes: {nx_graph.number_of_nodes()}')
print(f'Graph edges: {nx_graph.number_of_edges()}')
