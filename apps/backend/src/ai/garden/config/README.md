# GARDEN-1G Configuration Directory

This directory contains JSON configuration files for the GARDEN-1G model.

## File Format

Each JSON file can contain:
- `reflex_patterns`: `Dict[str, str]` - Fast pattern → response mappings
- `dictionary_entries`: `List[Dict]` - Concept entries with surface forms and relations
- `garden_config`: `Dict` - Engine parameters (optional)

## Example

```json
{
  "reflex_patterns": {
    "你好": "你好！很高兴见到你！"
  },
  "dictionary_entries": [
    {
      "key": "my_custom_concept",
      "surface_forms": {"zh": "自定義概念", "en": "custom concept"},
      "relations": {"mapping": ["g1"]},
      "confidence": 0.9
    }
  ],
  "garden_config": {
    "top_k": 8,
    "similarity_threshold": 0.30
  }
}
```
