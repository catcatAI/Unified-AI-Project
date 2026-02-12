# =============================================================================
# ANGELA-MATRIX: L2[记忆层] αβ [A] L2+
# =============================================================================
#
# 职责: 可映射数据对象，支持数据映射、压缩和分层
# 维度: 主要涉及 α (数据) 和 β (认知) 维度
# 安全: 使用 Key A (后端控制) 进行数据处理
# 成熟度: L2+ 等级理解数据结构的概念
#
# =============================================================================

import json
import zlib
from typing import Dict, Any, Optional
import logging
logger = logging.getLogger(__name__)

class MappableDataObject:
    """
    A generic data object that can be mapped, compressed, and layered.
    """

    def __init__(self, data: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Initializes the MappableDataObject.

        Args:
            data (Any): The raw data.
            metadata (Optional[Dict[str, Any]]): Additional metadata.
        """
        self.data = data
        self.metadata = metadata or {}
        self.compressed_data: Optional[bytes] = None
        self.layers: Dict[str, Any] = {}

    def compress(self):
        """
        Compresses the data using zlib.
        """
        if self.data is not None:
            serialized_data = json.dumps(self.data).encode('utf-8')
            self.compressed_data = zlib.compress(serialized_data)

    def decompress(self) -> Any:
        """
        Decompresses the data.
        """
        if self.compressed_data is not None:
            decompressed_data = zlib.decompress(self.compressed_data)
            return json.loads(decompressed_data.decode('utf-8'))
        return None

    def add_layer(self, layer_name: str, layer_data: Any):
        """
        Adds a new layer to the data object.

        Args:
            layer_name (str): The name of the layer.
            layer_data (Any): The data for the layer.
        """
        self.layers[layer_name] = layer_data

    def get_layer(self, layer_name: str) -> Optional[Any]:
        """
        Gets a layer from the data object.

        Args:
            layer_name (str): The name of the layer.

        Returns:
            Optional[Any]: The data for the layer, or None if the layer does not exist.
        """
        return self.layers.get(layer_name)
    
    def remove_layer(self, layer_name: str):
        """
        Removes a layer from the data object.

        Args:
            layer_name (str): The name of the layer.
        """
        if layer_name in self.layers:
            del self.layers[layer_name]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the object to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the object.
        """
        return {
            'data': self.data,
            'metadata': self.metadata,
            'layers': self.layers,
            'compressed': self.compressed_data is not None
        }
    
    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> 'MappableDataObject':
        """
        Creates a MappableDataObject from a dictionary.

        Args:
            data_dict (Dict[str, Any]): Dictionary representation.

        Returns:
            MappableDataObject: The created object.
        """
        obj = cls(data_dict.get('data'), data_dict.get('metadata'))
        obj.layers = data_dict.get('layers', {})
        if data_dict.get('compressed'):
            obj.compressed_data = data_dict.get('compressed_data')
        return obj