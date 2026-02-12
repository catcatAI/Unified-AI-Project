# Angela Matrix - 4D State: αβγδ (Cognitive-Emotional-Volitional-Memory)
# File: __init__.py
# State: L5-Mature-Agentic (Mature Agent Capabilities)

"""
Distributed Computing System Package
Implements Level 5 ASI hybrid distributed architecture for Angela AI
"""

from .distributed_coordinator import DistributedCoordinator
from .hyperlinked_parameters import HyperlinkedParameterCluster
import logging
logger = logging.getLogger(__name__)

__all__ = [
    'DistributedCoordinator',
    'HyperlinkedParameterCluster'
]