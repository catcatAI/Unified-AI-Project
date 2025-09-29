# pyright: reportMissingImports=false
import os
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union, TYPE_CHECKING
from datetime import datetime
import hashlib

# 定義類型別名
# 修复：使用更直接的类型定义方式
if TYPE_CHECKING:
    try:
        from chromadb.api import ClientAPI
        # 直接在需要的地方使用类型注解
    except ImportError:
        # 创建一个兼容的类型别名
        from typing import Protocol
        class ClientAPI(Protocol):
            """ChromaDB客户端API的协议定义"""
            def heartbeat(self) -> None: ...
            def get_or_create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> Any: ...
    # 定义客户端类型
    ChromaClientType = Union[ClientAPI, Any]
else:
    # 运行时定义一个通用类型
    ChromaClientType = Any

# 条件導入用于類型檢查，避免運行時導入錯誤
if TYPE_CHECKING:
    # 在類型檢查時嘗試導入
    try:
        import chromadb
        # 从正确的模块导入ClientAPI
        from chromadb.api import ClientAPI
    except ImportError:
        pass

# 運行時導入 - 使用更安全的方式處理導入錯誤

logger: Any = logging.getLogger(__name__)

class VectorStoreError(Exception):
    """向量存儲錯誤"""
    pass

class VectorMemoryStore:
    """增強的向量化記憶存儲，支持高級語義搜尋和記憶檢索"""
    
    def __init__(self, persist_directory="./chroma_db") -> None:
        # 使用明确的类型注解替代Union[Any, None]
        self.client: Optional[ChromaClientType] = None
        self.collection = None
        self.persist_directory = persist_directory
        self.search_history =   # 搜尋歷史
        self.memory_metadata_cache =   # 記憶元數據緩存
        
        # 配置選項
        self.config = {
            'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2',
            'max_search_results': 50,
            'similarity_threshold': 0.7,
            'enable_hybrid_search': True,
            'enable_semantic_clustering': True,
            'auto_cleanup_enabled': True,
            'max_memory_age_days': 365
        }
        
        self._initialize_vector_store
        
    def _initialize_vector_store(self):
        """初始化向量存儲"""
        try:
            import chromadb
            # 兼容不同版本的ChromaDB配置導入
            try:
                from chromadb.config import Settings
            except ImportError:
                # 嘗試直接從chromadb導入Settings
                if hasattr(chromadb, 'Settings'):
                    Settings = chromadb.Settings
                else:
                    # 使用本地實現
                    from .chroma_config import Settings
            
            import numpy as np # Import numpy here for the compatibility check
            # Check numpy compatibility - handle both 1.x and 2.x versions safely
            try:
                hasattr(np, 'float_')  # Safe check for numpy < 2.0
            except Exception:
                pass  # Skip if any compatibility issues

            # Prefer in-memory client by default to avoid network dependency during tests
            use_http = os.environ.get("CHROMA_HTTP_CLIENT", "0") == "1"
            if use_http:
                try:
                    self.client = chromadb.HttpClient(
                        host=os.environ.get("CHROMA_HOST", "localhost"),
                        port=int(os.environ.get("CHROMA_PORT", "8001")),  # 修正端口為8001
                        settings=Settings(
                            anonymized_telemetry=False
                        )
                    )
                    logger.info("VectorMemoryStore: Using HttpClient mode")
                except Exception as e:
                    logger.warning(f"VectorMemoryStore: HttpClient initialization failed: {e}. Falling back to EphemeralClient.")
                    self.client = chromadb.EphemeralClient(
                        settings=Settings(
                            anonymized_telemetry=False
                        )
                    )
            else:
                self.client = chromadb.EphemeralClient(
                    settings=Settings(
                        anonymized_telemetry=False
                    )
                )
                logger.info("VectorMemoryStore: Using EphemeralClient (in-memory) mode")
                
            # 修复：添加类型检查以确保client不为None
            if self.client is not None:
                self.collection = self.client.get_or_create_collection(
                    name="enhanced_ham_memories",
                    metadata={
                        "hnsw:space": "cosine",
                        "hnsw:construction_ef": 200,
                        "hnsw:M": 16
                    }
                )
            else:
                self.collection = None
            
            # 初始化高級功能
            self._setup_advanced_features
            
        except (AttributeError, ImportError) as e:
            self.client = None
            self.collection = None
            logger.error(f"VectorMemoryStore: Initialization failed due to dependency issue ({e}). Vector search will be disabled.")
        except Exception as e:
            self.client = None
            self.collection = None
            logger.error(f"VectorMemoryStore: An unexpected error occurred during initialization ({e}). Vector search will be disabled.")
    
    def _setup_advanced_features(self):
        """設置高級功能"""
        try:
            # 檢查現有記憶數量 - 使用正確的ChromaDB API
            if self.collection:
                try:
                    # 使用更可靠的方法檢查集合狀態
                    try:
                        # 獲取集合中的所有ID來計算記憶數量
                        all_ids = self.collection.get(include=)  # 只獲取ID，不包含其他數據
                        existing_count = len(all_ids['ids']) if 'ids' in all_ids else 0
                    except Exception as info_error:
                        logger.debug(f"Collection count check failed: {info_error}")
                        existing_count = 0  # 假設為空集合
                except Exception as e:
                    existing_count = 0  # 如果都失敗則假設為0
                    logger.warning(f"Could not get collection count: {e}")
                    
                logger.info(f"VectorMemoryStore: Found {existing_count} existing memories")
                
                # 如果啟用自動清理，執行維護任務
                if self.config.get('auto_cleanup_enabled'):
                    asyncio.create_task(self._schedule_maintenance)
                    
        except Exception as e:
            logger.warning(f"Error setting up advanced features: {e}")
    
    async def add_memory(self, memory_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """增強的添加記憶功能，支持更多元數據和自動分類"""
        if not self.collection:
            raise VectorStoreError("Vector store is not initialized. Cannot add memory.")
            
        metadata = metadata or 
        
        try:
            # 增強元數據
            enhanced_metadata = {
                **metadata,
                'timestamp': datetime.now.isoformat,
                'content_length': len(content),
                'content_hash': hashlib.md5(content.encode).hexdigest,
                'memory_type': metadata.get('memory_type', 'general'),
                'importance_score': metadata.get('importance_score', 0.5),
                'access_count': 0,
                'last_accessed': datetime.now.isoformat
            }
            
            # 自動分類和標籤
            auto_tags = await self._generate_automatic_tags(content)
            enhanced_metadata['auto_tags'] = auto_tags
            
            # 語義簡類
            semantic_category = await self._classify_semantic_category(content)
            enhanced_metadata['semantic_category'] = semantic_category
            
            # 添加到向量存儲
            self.collection.add(
                documents=[content],
                metadatas=[enhanced_metadata],
                ids=[memory_id]
            )
            
            # 更新緩存
            self.memory_metadata_cache[memory_id] = enhanced_metadata
            
            logger.info(f"Added memory {memory_id} with semantic category: {semantic_category}")
            
            return {
                'memory_id': memory_id,
                'status': 'success',
                'semantic_category': semantic_category,
                'auto_tags': auto_tags,
                'timestamp': enhanced_metadata['timestamp']
            }
            
        except Exception as e:
            logger.error(f"Failed to add memory {memory_id}: {e}")
            raise VectorStoreError(f"Failed to add memory: {e}")
    
    async def semantic_search(self, query: str, n_results: int = 10):
        """語義搜索"""
        if not self.collection:
            raise VectorStoreError("Vector store is not initialized. Cannot perform semantic search.")
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            return results
        except Exception as e:
            raise VectorStoreError(f"Semantic search failed: {e}")
    
    async def _generate_automatic_tags(self, content: str) -> List[str]:
        """自動生成標籤（模擬實現）"""
        _ = await asyncio.sleep(0.01)  # 模擬處理時間
        
        # 簡單的關鍵詞提取
        keywords = [
            'memory', 'information', 'data', 'knowledge', 'experience',
            'learning', 'analysis', 'processing', 'storage', 'retrieval'
        ]
        
        # 模擬基於內容的標籤生成
        content_lower = content.lower
        auto_tags = 
        
        for keyword in keywords:
            if keyword in content_lower:
                auto_tags.append(keyword)
        
        # 添加基於長度的標籤
        if len(content) > 500:
            auto_tags.append('long_content')
        elif len(content) < 50:
            auto_tags.append('short_content')
        else:
            auto_tags.append('medium_content')
        
        return auto_tags[:5]  # 限制標籤數量
    
    async def _classify_semantic_category(self, content: str) -> str:
        """語義分類（模擬實現）"""
        _ = await asyncio.sleep(0.01)
        
        # 簡單的分類邏輯
        content_lower = content.lower
        
        if any(word in content_lower for word in ['task', 'execute', 'action', 'perform']):
            return 'task_related'
        elif any(word in content_lower for word in ['emotion', 'feeling', 'mood', 'sentiment']):
            return 'emotional'
        elif any(word in content_lower for word in ['fact', 'information', 'data', 'knowledge']):
            return 'factual'
        elif any(word in content_lower for word in ['experience', 'memory', 'recall', 'remember']):
            return 'experiential'
        elif any(word in content_lower for word in ['goal', 'plan', 'strategy', 'objective']):
            return 'planning'
        else:
            return 'general'
    
    def _generate_search_id(self, query: str) -> str:
        """生成搜索 ID"""
        query_hash = hashlib.md5(query.encode).hexdigest[:8]
        return f"search_{query_hash}_{datetime.now.strftime('%H%M%S')}"
    
    async def _schedule_maintenance(self):
        """安排系統維護任務"""
        try:
            # 模擬維護任務
            _ = await asyncio.sleep(1)
            logger.info("Vector store maintenance completed")
        except Exception as e:
            logger.error(f"Maintenance task failed: {e}")
    
    async def get_memory_statistics(self) -> Dict[str, Any]:
        """獲取記憶統計信息"""
        if not self.collection:
            return {"error": "Vector store not initialized"}
        
        try:
            # 使用更可靠的方法獲取記憶統計
            try:
                # 獲取集合中的所有ID來計算記憶數量
                all_ids = self.collection.get(include=)  # 只獲取ID，不包含其他數據
                total_memories = len(all_ids['ids']) if 'ids' in all_ids else 0
            except Exception as info_error:
                logger.debug(f"Collection count check failed for statistics: {info_error}")
                total_memories = 0
            
            # 簡單統計
            statistics: Dict[str, Any] = {
                'total_memories': total_memories,
                'search_history_count': len(self.search_history),
                'cache_size': len(self.memory_metadata_cache),
                'last_updated': datetime.now.isoformat,
                'config': self.config
            }
            
            # 分類統計（模擬）
            categories = ['task_related', 'emotional', 'factual', 'experiential', 'planning', 'general']
            # 修复類型錯誤：使用正確的字典類型
            category_counts: Dict[str, int] = {cat: total_memories // len(categories) for cat in categories}
            statistics['category_distribution'] = category_counts
            
            return statistics
            
        except Exception as e:
            logger.error(f"Failed to get memory statistics: {e}")
            return {"error": str(e)}
    
    async def delete_memory(self, memory_id: str) -> Dict[str, Any]:
        """刪除記憶"""
        if not self.collection:
            raise VectorStoreError("Vector store is not initialized.")
        
        try:
            # 使用安全的ChromaDB delete API
            try:
                # 首先檢查記憶是否存在（簡化版本）
                logger.debug(f"Attempting to delete memory {memory_id}")
                
                # 直接嘗試刪除，由ChromaDB處理錯誤
                if hasattr(self.collection, 'delete'):
                    # 修复：直接调用delete方法而不是异步获取
                    self.collection.delete(ids=[memory_id])
                else:
                    logger.warning(f"Delete method not available for memory {memory_id}")
                    return {
                        'memory_id': memory_id,
                        'status': 'delete_not_supported',
                        'timestamp': datetime.now.isoformat
                    }
            except Exception as e:
                logger.error(f"Delete operation failed for memory {memory_id}: {e}")
                raise VectorStoreError(f"Failed to delete memory: {e}")
            
            # 清理緩存
            if memory_id in self.memory_metadata_cache:
                del self.memory_metadata_cache[memory_id]
            
            logger.info(f"Deleted memory {memory_id}")
            
            return {
                'memory_id': memory_id,
                'status': 'deleted',
                'timestamp': datetime.now.isoformat
            }
            
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            raise VectorStoreError(f"Failed to delete memory: {e}")