import unittest
from apps.backend.src.ai.deep_mapper import DeepMapper
from apps.backend.src.shared.types import MappableDataObject

class TestDeepMapper(unittest.TestCase):

    def test_map(self) -> None:
        # Arrange
        source_data = {
            "nodes": [
                {"id": "p1", "type": "person", "name": "Alice"},
                {"id": "l1", "type": "place", "name": "Park"},
            ],
            "edges": [
                {"source": "p1", "target": "l1", "type": "located_in"},
            ],
        }
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
        mdo = MappableDataObject(data=source_data)
        mapper = DeepMapper(mapping_rules=mapping_rules)

        # Act
        mapped_mdo = mapper.map(mdo)

        # Assert
        expected_data = {
            "nodes": [
                {"id": "p1", "type": "character", "name": "Alice"},
                {"id": "l1", "type": "location", "name": "Park"},
            ],
            "edges": [
                {"source": "p1", "target": "l1", "type": "is_at"},
            ],
        }
        _ = self.assertEqual(mapped_mdo.data, expected_data)

    def test_reverse_map(self) -> None:
        # Arrange
        source_data = {
            "nodes": [
                {"id": "p1", "type": "character", "name": "Alice"},
                {"id": "l1", "type": "location", "name": "Park"},
            ],
            "edges": [
                {"source": "p1", "target": "l1", "type": "is_at"},
            ],
        }
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
        mdo = MappableDataObject(data=source_data)
        mapper = DeepMapper(mapping_rules=mapping_rules)

        # Act
        reverse_mapped_mdo = mapper.reverse_map(mdo)

        # Assert
        expected_data = {
            "nodes": [
                {"id": "p1", "type": "person", "name": "Alice"},
                {"id": "l1", "type": "place", "name": "Park"},
            ],
            "edges": [
                {"source": "p1", "target": "l1", "type": "located_in"},
            ],
        }
        _ = self.assertEqual(reverse_mapped_mdo.data, expected_data)

if __name__ == '__main__':
    _ = unittest.main()
