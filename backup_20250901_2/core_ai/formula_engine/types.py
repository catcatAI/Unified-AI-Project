from typing import TypedDict, Required, Optional, List, Dict, Any

class FormulaConfigEntry(TypedDict, total=False):
    name: Required[str]
    conditions: Required[List[str]]
    action: Required[str]
    description: Optional[str]
    parameters: Optional[Dict[str, Any]]
    priority: Optional[int]
    enabled: Optional[bool]
    version: Optional[str]
