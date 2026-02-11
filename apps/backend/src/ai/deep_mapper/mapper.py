# Angela Matrix - 4D State: αβγδ (Cognitive-Emotional-Volitional-Memory)
# File: mapper.py
# State: L5-Mature-Agentic (Mature Agent Capabilities)

"""
Deep Mapper - Data transformation and mapping engine for Angela AI

A deep mapping engine that can map data between different representations,
supporting complex transformations and bidirectional mapping.
"""

import json
from typing import Dict, Any, Optional
from src.core.shared.types import MappableDataObject


class DeepMapper:
    """
    A deep mapping engine that can map data between different representations.
    
    This mapper supports:
    - Recursive nested data structure mapping
    - Bidirectional transformation
    - Rule-based mapping
    - Inverse mapping generation
    """

    def __init__(self, mapping_rules: Optional[Dict[str, Any]] = None) -> None:
        """
        Initializes the DeepMapper.

        Args:
            mapping_rules (Optional[Dict[str, Any]]): The mapping rules.
        """
        self.mapping_rules = mapping_rules or {}

    def load_mapping_rules(self, filepath: str):
        """
        Loads mapping rules from a file.

        Args:
            filepath (str): The path to the mapping rules file.
        """
        with open(filepath, 'r') as f:
            self.mapping_rules = json.load(f)

    def map(self, mdo: MappableDataObject) -> MappableDataObject:
        """
        Maps a MappableDataObject to a new representation.

        Args:
            mdo (MappableDataObject): The MappableDataObject to map.

        Returns:
            MappableDataObject: The mapped MappableDataObject.
        """
        mapped_data = self._recursive_map(mdo.data, self.mapping_rules)
        return MappableDataObject(data=mapped_data, metadata=mdo.metadata)

    def reverse_map(self, mdo: MappableDataObject) -> MappableDataObject:
        """
        Reverse maps a MappableDataObject to its original representation.

        Args:
            mdo (MappableDataObject): The MappableDataObject to reverse map.

        Returns:
            MappableDataObject: The reverse mapped MappableDataObject.
        """
        reverse_mapping_rules = self._invert_mapping_rules(self.mapping_rules)
        reverse_mapped_data = self._recursive_map(mdo.data, reverse_mapping_rules)
        return MappableDataObject(data=reverse_mapped_data, metadata=mdo.metadata)

    def _recursive_map(self, data: Any, rules: Dict[str, Any]) -> Any:
        """
        Recursively maps data according to rules.
        
        Args:
            data: The data to map
            rules: Mapping rules
            
        Returns:
            Mapped data
        """
        if isinstance(data, dict):
            new_dict = {}
            for key, value in data.items():
                if key in rules and isinstance(rules[key], dict):
                    new_dict[key] = self._recursive_map(value, rules[key])
                else:
                    new_key = rules.get(key, key)
                    new_dict[new_key] = self._recursive_map(value, rules)
            return new_dict
        elif isinstance(data, list):
            return [self._recursive_map(item, rules) for item in data]
        else:
            if isinstance(rules, dict) and data in rules:
                return rules[data]
            return data

    def _invert_mapping_rules(self, rules: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inverts mapping rules for reverse mapping.
        
        Args:
            rules: Original mapping rules
            
        Returns:
            Inverted mapping rules
        """
        inverted_rules = {}
        for key, value in rules.items():
            if isinstance(value, dict):
                inverted_rules[key] = self._invert_mapping_rules(value)
            else:
                inverted_rules[value] = key
        return inverted_rules