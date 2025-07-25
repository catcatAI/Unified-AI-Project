# Deep Mapper

The Deep Mapper is a tool for mapping data between different representations. It is designed to be flexible and extensible, and can be used to map a wide variety of data types, including knowledge graphs, model parameters, and multi-modal data.

## Usage

To use the Deep Mapper, you need to create an instance of the `DeepMapper` class, providing a dictionary of mapping rules.

```python
from src.core_ai.deep_mapper import DeepMapper

mapping_rules = {
    "nodes": {
        "type": {
            "person": "character",
            "place": "location",
        }
    },
    "edges": {
        "type": {
            "located_in": "is_at"
        }
    }
}

mapper = DeepMapper(mapping_rules=mapping_rules)
```

### Mapping Data

You can map a `MappableDataObject` to a new representation using the `map` method.

```python
from src.shared.types import MappableDataObject

source_data = {
    "nodes": [
        {"id": "p1", "type": "person", "name": "Alice"},
        {"id": "l1", "type": "place", "name": "Park"},
    ],
    "edges": [
        {"source": "p1", "target": "l1", "type": "located_in"},
    ],
}

mdo = MappableDataObject(data=source_data)
mapped_mdo = mapper.map(mdo)
```

### Reverse Mapping Data

You can reverse map a `MappableDataObject` to its original representation using the `reverse_map` method.

```python
reverse_mapped_mdo = mapper.reverse_map(mapped_mdo)
```

## Example

For a complete example of how to use the Deep Mapper, see the `scripts/run_deep_mapper_example.py` script.
