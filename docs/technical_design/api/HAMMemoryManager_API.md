# HAMMemoryManager API 參考

`HAMMemoryManager` 是 Hierarchical Abstractive Memory (HAM) 系統的核心組件，負責處理記憶的存儲、檢索和管理。

## 目錄

- [類別概述](#類別概述)
- [初始化](#初始化)
- [方法](#方法)
  - [store_experience](#store_experience)
  - [recall_gist](#recall_gist)
  - [query_core_memory](#query_core_memory)
  - [其他方法](#其他方法)
- [數據類型](#數據類型)
- [使用範例](#使用範例)
- [錯誤處理](#錯誤處理)
- [注意事項](#注意事項)

## 類別概述

`HAMMemoryManager` 實現了一個分層抽象記憶系統，提供以下功能：

- 存儲經驗（文本或通用數據）
- 檢索特定記憶
- 基於多種條件查詢記憶
- 支持數據加密和壓縮
- 資源感知（磁盤空間、性能）

## 初始化

```python
def __init__(self, 
             core_storage_filename: str = "ham_core_memory.json",
             resource_awareness_service: Optional[Any] = None,
             personality_manager: Optional[Any] = None):
    """
    初始化 HAMMemoryManager 實例。
    
    參數:
        core_storage_filename (str): 持久化存儲的核心記憶文件名。
        resource_awareness_service: 資源感知服務，用於獲取模擬的資源限制。
        personality_manager: 個性管理器，用於個性化記憶管理。
    """
```

## 方法

### store_experience

```python
def store_experience(self, 
                   raw_data: Any, 
                   data_type: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    存儲一個新的經驗到記憶中。
    
    參數:
        raw_data: 要存儲的原始數據（文本或可序列化對象）
        data_type (str): 數據類型標識符（如 "dialogue_text"）
        metadata: 可選的元數據字典
        
    返回:
        str: 新創建的記憶ID
    """
```

### recall_gist

```python
def recall_gist(self, memory_id: str) -> Optional[HAMRecallResult]:
    """
    通過記憶ID檢索記憶的抽象摘要。
    
    參數:
        memory_id (str): 要檢索的記憶ID
        
    返回:
        Optional[HAMRecallResult]: 如果找到則返回記憶結果，否則返回None
    """
```

### query_core_memory

```python
def query_core_memory(self,
                    keywords: Optional[List[str]] = None,
                    date_range: Optional[Tuple[datetime, datetime]] = None,
                    data_type_filter: Optional[str] = None,
                    metadata_filters: Optional[Dict[str, Any]] = None,
                    user_id_for_facts: Optional[str] = None,
                    limit: int = 5,
                    sort_by_confidence: bool = False,
                    return_multiple_candidates: bool = False) -> List[HAMRecallResult]:
    """
    查詢核心記憶。
    
    參數:
        keywords: 用於搜索的關鍵字列表
        date_range: 日期範圍過濾器（開始日期，結束日期）
        data_type_filter: 數據類型過濾器
        metadata_filters: 元數據過濾條件
        user_id_for_facts: 用於過濾特定用戶的事實
        limit: 返回結果的最大數量
        sort_by_confidence: 是否按置信度排序（主要用於事實）
        return_multiple_candidates: 是否返回多個候選結果
        
    返回:
        List[HAMRecallResult]: 符合條件的記憶結果列表
    """
```

### 其他方法

- `_generate_memory_id()`: 生成唯一的記憶ID
- `_encrypt(data: bytes) -> bytes`: 加密數據
- `_decrypt(encrypted_data: bytes) -> Optional[bytes]`: 解密數據
- `_compress(data: bytes) -> bytes`: 壓縮數據
- `_decompress(compressed_data: bytes) -> Optional[bytes]`: 解壓縮數據
- `_load_core_memory_from_file()`: 從文件加載核心記憶
- `_save_core_memory_to_file()`: 將核心記憶保存到文件
- `_delete_old_experiences()`: 刪除舊的、不常用的記憶

## 數據類型

### HAMRecallResult

表示從記憶中檢索的結果。

```python
{
    "id": str,                   # 記憶ID
    "timestamp": str,            # 時間戳(ISO格式)
    "data_type": str,            # 數據類型
    "rehydrated_gist": Any,      # 再水合後的摘要
    "metadata": Dict[str, Any]   # 元數據
}
```

## 使用範例

### 存儲記憶

```python
# 初始化記憶管理器
ham = HAMMemoryManager()

# 存儲對話文本
metadata = {
    "speaker": "user",
    "emotion": "happy",
    "context": "greeting"
}
memory_id = ham.store_experience(
    "你好，今天天氣真好！",
    "dialogue_text",
    metadata
)
```

### 檢索記憶

```python
# 通過ID檢索
result = ham.recall_gist(memory_id)
if result:
    print(f"記憶內容: {result.rehydrated_gist}")
    print(f"元數據: {result.metadata}")
```

### 查詢記憶

```python
# 查詢包含特定關鍵字的記憶
from datetime import datetime, timedelta

# 查詢過去一天內包含"天氣"的對話
yesterday = datetime.now(timezone.utc) - timedelta(days=1)
results = ham.query_core_memory(
    keywords=["天氣"],
    data_type_filter="dialogue_text",
    date_range=(yesterday, datetime.now(timezone.utc))
)

for memory in results:
    print(f"[{memory.timestamp}] {memory.rehydrated_gist}")
```

## 錯誤處理

- 文件操作錯誤（如權限問題、磁盤空間不足）
- 加密/解密錯誤（如無效的加密密鑰）
- 數據序列化/反序列化錯誤
- 校驗和不匹配（數據損壞檢測）

## 注意事項

1. **加密密鑰管理**：
   - 使用 `MIKO_HAM_KEY` 環境變量設置加密密鑰
   - 如果未設置，將生成臨時密鑰（僅在當前會話中有效）

2. **性能考慮**：
   - 大規模數據集可能需要優化查詢性能
   - 定期清理舊的、不常用的記憶以釋放資源

3. **資源限制**：
   - 實現了基本的資源感知功能
   - 在磁盤空間不足時會觸發警告或錯誤

4. **線程安全**：
   - 當前實現不保證線程安全，應避免多線程並發訪問

5. **數據持久化**：
   - 記憶會自動保存到文件系統
   - 在程序正常關閉時會自動保存所有更改
