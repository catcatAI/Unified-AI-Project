# Angela Matrix - 4D State: αβγδ (Cognitive-Emotional-Volitional-Memory)
# File: hyperlinked_parameters.py
# State: L5-Mature-Agentic (Mature Agent Capabilities)

"""
Hyperlinked Parameter Cluster
Implements Level 5 ASI dynamic parameter loading and management system
"""

import asyncio
import logging
import json
import hashlib
import pickle
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import weakref

logger = logging.getLogger(__name__)


class ParameterType(Enum):
    """Parameter type enumeration"""
    MODEL_WEIGHT = "model_weight"
    CONFIGURATION = "configuration"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    ALIGNMENT_PARAMETER = "alignment_parameter"
    NEURAL_NETWORK = "neural_network"
    ALGORITHM = "algorithm"


class LoadingStrategy(Enum):
    """Loading strategy enumeration"""
    LAZY = "lazy"                 # Lazy loading
    EAGER = "eager"               # Immediate loading
    ON_DEMAND = "on_demand"       # On-demand loading
    PREDICTIVE = "predictive"     # Predictive loading


@dataclass
class ParameterMetadata:
    """Parameter metadata"""
    parameter_id: str
    name: str
    parameter_type: ParameterType
    size_bytes: int
    checksum: str
    version: str
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = None
    last_accessed: datetime = None
    access_count: int = 0
    loading_strategy: LoadingStrategy = LoadingStrategy.LAZY


@dataclass
class ParameterLink:
    """Parameter link"""
    source_parameter_id: str
    target_parameter_id: str
    link_type: str
    strength: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class HyperlinkedParameterCluster:
    """
    Hyperlinked Parameter Cluster
    
    Implements:
    - Dynamic parameter loading
    - Parameter dependency management
    - Hyperlinked associations
    - Memory optimization
    - Version control
    """
    
    def __init__(self, cluster_id: str = "hyperlinked_parameter_cluster"):
        self.cluster_id = cluster_id
        
        # Parameter storage
        self.parameters: Dict[str, Any] = {}  # Actual parameter data
        self.parameter_metadata: Dict[str, ParameterMetadata] = {}  # Parameter metadata
        self.parameter_links: Dict[str, List[ParameterLink]] = {}  # Parameter links
        
        # Loading management
        self.loading_strategies: Dict[LoadingStrategy, Callable] = {
            LoadingStrategy.LAZY: self._lazy_load,
            LoadingStrategy.EAGER: self._eager_load,
            LoadingStrategy.ON_DEMAND: self._on_demand_load,
            LoadingStrategy.PREDICTIVE: self._predictive_load
        }
        
        # Memory management
        self.memory_limit_bytes = 1024 * 1024 * 1024  # 1GB
        self.current_memory_usage = 0
        self.weak_references: Dict[str, weakref.ref] = {}
        
        # Cache system
        self.cache: Dict[str, Any] = {}
        self.cache_max_size = 100
        self.cache_access_order: List[str] = []
        
        # Prediction system
        self.access_patterns: Dict[str, List[datetime]] = {}
        self.prediction_model = None
        
        # Statistics
        self.statistics = {
            "total_parameters": 0,
            "loaded_parameters": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "memory_usage": 0,
            "loading_times": {}
        }

    async def initialize(self):
        """Initialize the parameter cluster"""
        try:
            # Initialize prediction model
            await self._initialize_prediction_model()
            
            # Load core parameters
            await self._load_core_parameters()
            
            logger.info(f"[{self.cluster_id}] Hyperlinked parameter cluster initialized")
            
        except Exception as e:
            logger.error(f"[{self.cluster_id}] Initialization failed: {e}")
            raise

    async def register_parameter(
        self,
        parameter_id: str,
        parameter_data: Any,
        parameter_type: ParameterType,
        name: str = None,
        dependencies: List[str] = None,
        tags: List[str] = None,
        loading_strategy: LoadingStrategy = LoadingStrategy.LAZY,
        version: str = "1.0"
    ) -> bool:
        """Register a parameter"""
        try:
            # Check if parameter already exists
            if parameter_id in self.parameter_metadata:
                logger.warning(f"[{self.cluster_id}] Parameter {parameter_id} already exists, will be overwritten")
            
            # Calculate checksum
            data_bytes = pickle.dumps(parameter_data)
            checksum = hashlib.sha256(data_bytes).hexdigest()
            
            # Create metadata
            metadata = ParameterMetadata(
                parameter_id=parameter_id,
                name=name or parameter_id,
                parameter_type=parameter_type,
                size_bytes=len(data_bytes),
                checksum=checksum,
                version=version,
                dependencies=dependencies or [],
                tags=tags or [],
                created_at=datetime.now(),
                loading_strategy=loading_strategy
            )
            
            # Store metadata
            self.parameter_metadata[parameter_id] = metadata
            
            # Process parameter based on loading strategy
            if loading_strategy == LoadingStrategy.EAGER:
                self.parameters[parameter_id] = parameter_data
                self.current_memory_usage += metadata.size_bytes
            elif loading_strategy == LoadingStrategy.LAZY:
                # Lazy load, don't store data immediately
                pass
            else:
                # Preprocessing for other strategies
                await self._prepare_parameter(parameter_id, parameter_data, loading_strategy)
            
            # Update statistics
            self.statistics["total_parameters"] += 1
            
            logger.info(f"[{self.cluster_id}] Parameter {parameter_id} registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"[{self.cluster_id}] Parameter registration failed: {e}")
            return False

    async def get_parameter(self, parameter_id: str) -> Optional[Any]:
        """Get a parameter"""
        try:
            # Check cache
            if parameter_id in self.cache:
                self.statistics["cache_hits"] += 1
                self._update_cache_access_order(parameter_id)
                return self.cache[parameter_id]
            
            self.statistics["cache_misses"] += 1
            
            # Check if parameter exists
            if parameter_id not in self.parameter_metadata:
                logger.warning(f"[{self.cluster_id}] Parameter {parameter_id} does not exist")
                return None
            
            metadata = self.parameter_metadata[parameter_id]
            
            # Check if already loaded
            if parameter_id in self.parameters:
                parameter_data = self.parameters[parameter_id]
            else:
                # Load parameter based on loading strategy
                parameter_data = await self._load_parameter(parameter_id, metadata.loading_strategy)
                if parameter_data is None:
                    return None
            
            # Update access information
            metadata.last_accessed = datetime.now()
            metadata.access_count += 1
            self._record_access_pattern(parameter_id)
            
            # Cache parameter
            await self._cache_parameter(parameter_id, parameter_data)
            
            return parameter_data
            
        except Exception as e:
            logger.error(f"[{self.cluster_id}] Failed to get parameter: {e}")
            return None

    async def create_link(self, source_id: str, target_id: str, link_type: str, 
                          strength: float = 1.0, metadata: Dict[str, Any] = None):
        """Create a parameter link"""
        try:
            # Check if parameters exist
            if source_id not in self.parameter_metadata:
                logger.error(f"[{self.cluster_id}] Source parameter {source_id} does not exist")
                return False
            
            if target_id not in self.parameter_metadata:
                logger.error(f"[{self.cluster_id}] Target parameter {target_id} does not exist")
                return False
            
            # Create link
            link = ParameterLink(
                source_parameter_id=source_id,
                target_parameter_id=target_id,
                link_type=link_type,
                strength=strength,
                metadata=metadata or {}
            )
            
            # Store link
            if source_id not in self.parameter_links:
                self.parameter_links[source_id] = []
            
            self.parameter_links[source_id].append(link)
            
            logger.info(f"[{self.cluster_id}] Created link: {source_id} -> {target_id} ({link_type})")
            return True
            
        except Exception as e:
            logger.error(f"[{self.cluster_id}] Failed to create link: {e}")
            return False

    async def update_parameter(self, parameter_id: str, new_data: Any, new_version: str = None) -> bool:
        """Update a parameter"""
        try:
            if parameter_id not in self.parameter_metadata:
                logger.error(f"[{self.cluster_id}] Parameter {parameter_id} does not exist")
                return False
            
            old_metadata = self.parameter_metadata[parameter_id]
            
            # Calculate new checksum
            data_bytes = pickle.dumps(new_data)
            checksum = hashlib.sha256(data_bytes).hexdigest()
            
            # Update metadata
            old_metadata.checksum = checksum
            old_metadata.size_bytes = len(data_bytes)
            old_metadata.last_accessed = datetime.now()
            if new_version:
                old_metadata.version = new_version
            
            # Update data
            if parameter_id in self.parameters:
                # Calculate memory usage change
                old_size = len(pickle.dumps(self.parameters[parameter_id]))
                self.current_memory_usage -= old_size
                self.current_memory_usage += old_metadata.size_bytes
            self.parameters[parameter_id] = new_data
            
            # Clear cache
            if parameter_id in self.cache:
                del self.cache[parameter_id]
                self.cache_access_order.remove(parameter_id)
            
            logger.info(f"[{self.cluster_id}] Parameter {parameter_id} updated")
            return True
            
        except Exception as e:
            logger.error(f"[{self.cluster_id}] Parameter update failed: {e}")
            return False

    async def delete_parameter(self, parameter_id: str) -> bool:
        """Delete a parameter"""
        try:
            if parameter_id not in self.parameter_metadata:
                logger.error(f"[{self.cluster_id}] Parameter {parameter_id} does not exist")
                return False
            
            # Remove metadata
            metadata = self.parameter_metadata[parameter_id]
            del self.parameter_metadata[parameter_id]
            
            # Remove data
            if parameter_id in self.parameters:
                self.current_memory_usage -= metadata.size_bytes
                del self.parameters[parameter_id]
            
            # Remove from cache
            if parameter_id in self.cache:
                del self.cache[parameter_id]
                self.cache_access_order.remove(parameter_id)
            
            # Remove links
            if parameter_id in self.parameter_links:
                del self.parameter_links[parameter_id]
            
            # Remove links from other parameters pointing to this one
            for source_id, links in self.parameter_links.items():
                self.parameter_links[source_id] = [
                    link for link in links if link.target_parameter_id != parameter_id
                ]
            
            # Update statistics
            self.statistics["total_parameters"] -= 1
            
            logger.info(f"[{self.cluster_id}] Parameter {parameter_id} deleted")
            return True
            
        except Exception as e:
            logger.error(f"[{self.cluster_id}] Parameter deletion failed: {e}")
            return False

    async def get_cluster_status(self) -> Dict[str, Any]:
        """Get cluster status"""
        loaded_count = len(self.parameters)
        memory_usage_mb = self.current_memory_usage / (1024 * 1024)
        
        return {
            "cluster_id": self.cluster_id,
            "total_parameters": self.statistics["total_parameters"],
            "loaded_parameters": loaded_count,
            "memory_usage_mb": memory_usage_mb,
            "memory_limit_mb": self.memory_limit_bytes / (1024 * 1024),
            "cache_hit_rate": (
                self.statistics["cache_hits"] / 
                max(1, self.statistics["cache_hits"] + self.statistics["cache_misses"])
            ),
            "parameter_types": self._get_parameter_type_distribution(),
            "loading_strategies": self._get_loading_strategy_distribution(),
            "statistics": self.statistics
        }

    async def _load_parameter(self, parameter_id: str, strategy: LoadingStrategy) -> Optional[Any]:
        """Load parameter based on strategy"""
        try:
            if strategy in self.loading_strategies:
                loader = self.loading_strategies[strategy]
                return await loader(parameter_id)
            else:
                logger.error(f"[{self.cluster_id}] Unknown loading strategy: {strategy}")
                return None
                
        except Exception as e:
            logger.error(f"[{self.cluster_id}] Parameter loading failed: {e}")
            return None

    async def _lazy_load(self, parameter_id: str) -> Optional[Any]:
        """Lazy loading"""
        # Here should load from persistent storage
        # For example, we return simulated data
        await asyncio.sleep(0.1)  # Simulate loading time
        
        # Simulated loaded data
        mock_data = f"lazy_loaded_data_{parameter_id}"
        
        # Store to memory
        self.parameters[parameter_id] = mock_data
        self.current_memory_usage += len(pickle.dumps(mock_data))
        
        return mock_data

    async def _eager_load(self, parameter_id: str) -> Optional[Any]:
        """Immediate loading (already loaded)"""
        return self.parameters.get(parameter_id)

    async def _on_demand_load(self, parameter_id: str) -> Optional[Any]:
        """On-demand loading"""
        # Check memory limit
        await self._ensure_memory_available()
        
        # Load parameter
        return await self._lazy_load(parameter_id)

    async def _predictive_load(self, parameter_id: str) -> Optional[Any]:
        """Predictive loading"""
        # Predict and load related parameters based on access patterns
        related_params = await self._predict_related_parameters(parameter_id)
        
        # Preload related parameters
        for related_id in related_params:
            if related_id not in self.parameters:
                await self._lazy_load(related_id)
        
        return await self._lazy_load(parameter_id)

    async def _prepare_parameter(self, parameter_id: str, parameter_data: Any, strategy: LoadingStrategy):
        """Prepare parameter for specific strategy"""
        if strategy == LoadingStrategy.PREDICTIVE:
            # Preprocessing for predictive loading
            await self._analyze_parameter_patterns(parameter_id, parameter_data)

    async def _cache_parameter(self, parameter_id: str, parameter_data: Any):
        """Cache parameter"""
        # Check cache size limit
        if len(self.cache) >= self.cache_max_size:
            # Remove least used item
            oldest_id = self.cache_access_order.pop(0)
            del self.cache[oldest_id]
        
        # Add to cache
        self.cache[parameter_id] = parameter_data
        self.cache_access_order.append(parameter_id)

    def _update_cache_access_order(self, parameter_id: str):
        """Update cache access order"""
        if parameter_id in self.cache_access_order:
            self.cache_access_order.remove(parameter_id)
        self.cache_access_order.append(parameter_id)

    def _record_access_pattern(self, parameter_id: str):
        """Record access pattern"""
        if parameter_id not in self.access_patterns:
            self.access_patterns[parameter_id] = []
        
        self.access_patterns[parameter_id].append(datetime.now())
        
        # Limit history count
        if len(self.access_patterns[parameter_id]) > 100:
            self.access_patterns[parameter_id] = self.access_patterns[parameter_id][-50:]

    async def _ensure_memory_available(self):
        """Ensure enough memory is available"""
        while self.current_memory_usage > self.memory_limit_bytes * 0.8:
            # Remove least used parameter
            if not self.parameters:
                break
            
            # Find least used parameter
            least_used_id = min(
                self.parameters.keys(),
                key=lambda pid: self.parameter_metadata[pid].access_count
            )
            
            # Remove parameter
            metadata = self.parameter_metadata[least_used_id]
            self.current_memory_usage -= metadata.size_bytes
            del self.parameters[least_used_id]
            
            logger.info(f"[{self.cluster_id}] Memory insufficient, unloading parameter: {least_used_id}")

    async def _predict_related_parameters(self, parameter_id: str) -> List[str]:
        """Predict related parameters"""
        # Simplified prediction algorithm: based on link strength and access patterns
        related = []
        
        if parameter_id in self.parameter_links:
            # Sort by link strength
            links = sorted(
                self.parameter_links[parameter_id],
                key=lambda l: l.strength,
                reverse=True
            )
            
            # Return top 3 most related parameters
            related = [link.target_parameter_id for link in links[:3]]
        
        return related

    async def _analyze_parameter_patterns(self, parameter_id: str, parameter_data: Any):
        """Analyze parameter patterns"""
        # Here should implement more complex pattern analysis
        # For example, we record basic information
        pass

    async def _initialize_prediction_model(self):
        """Initialize prediction model"""
        # Here should initialize machine learning model
        # For example, we skip actual implementation
        pass

    async def _load_core_parameters(self):
        """Load core parameters"""
        # Here should load system core parameters
        # For example, we skip actual implementation
        pass

    def _get_parameter_type_distribution(self) -> Dict[str, int]:
        """Get parameter type distribution"""
        distribution = {}
        for metadata in self.parameter_metadata.values():
            type_name = metadata.parameter_type.value
            distribution[type_name] = distribution.get(type_name, 0) + 1
        return distribution

    def _get_loading_strategy_distribution(self) -> Dict[str, int]:
        """Get loading strategy distribution"""
        distribution = {}
        for metadata in self.parameter_metadata.values():
            strategy_name = metadata.loading_strategy.value
            distribution[strategy_name] = distribution.get(strategy_name, 0) + 1
        return distribution