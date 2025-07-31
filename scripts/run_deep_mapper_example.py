import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.core_ai.deep_mapper import DeepMapper
from src.shared.types import MappableDataObject

def main():
    # 1. Create a source knowledge graph
    source_kg = {
        "nodes": [
            {"id": "p1", "type": "person", "name": "Alice"},
            {"id": "p2", "type": "person", "name": "Bob"},
            {"id": "l1", "type": "place", "name": "Park"},
        ],
        "edges": [
            {"source": "p1", "target": "p2", "type": "knows"},
            {"source": "p1", "target": "l1", "type": "located_in"},
        ],
    }

    # 2. Create a MappableDataObject for the source knowledge graph
    mdo = MappableDataObject(data=source_kg)

    # 3. Initialize the DeepMapper and load the mapping rules
    mapper = DeepMapper()
    mapper.load_mapping_rules("data/game_data/knowledge_graph_mapping.json")

    # 4. Map the knowledge graph
    mapped_mdo = mapper.map(mdo)

    # 5. Print the mapped knowledge graph
    print("Mapped Knowledge Graph:")
    print(mapped_mdo.data)

    # 6. Reverse map the knowledge graph
    reverse_mapped_mdo = mapper.reverse_map(mapped_mdo)

    # 7. Print the reverse mapped knowledge graph
    print("\nReverse Mapped Knowledge Graph:")
    print(reverse_mapped_mdo.data)

if __name__ == "__main__":
    main()
