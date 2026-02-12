from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging
logger = logging.getLogger(__name__)

@dataclass
class CodeAnalysisResult:
    """代码分析结果数据类"""
    filepath: str
    analysis_timestamp: datetime
    classes: List[Dict[str, Any]] = field(default_factory=list)
    functions: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    complexity_score: float = 0.0
    dna_chain_id: Optional[str] = None
