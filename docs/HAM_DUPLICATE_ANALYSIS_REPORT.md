# HAM记忆系统重复实现分析报告

## 1. 文件基本信息
- 主实现文件: `D:\Projects\Unified-AI-Project\apps\backend\src\ai\memory\ham_memory_manager.py`
- 备份实现文件: `D:\Projects\Unified-AI-Project\backup_modules\ai_backup\memory\ham_memory_manager.py`
- 主实现文件大小: 56356 bytes
- 备份实现文件大小: 61448 bytes
- 主实现文件哈希: 2be1ff12e82e203eb72639384bfe4baf
- 备份实现文件哈希: 810a63ca0e119b087e388c090fd0a081
- 文件是否相同: 否

## 2. 函数对比分析
- 主实现函数数量: 0
- 备份实现函数数量: 3

### 2.1 主实现独有函数
无

### 2.2 备份实现独有函数
- `_mock_embed_texts`
- `__call__`
- `name`

### 2.3 实现不同的函数
- `__init__`
- `_generate_memory_id`
- `close`
- `_encrypt`
- `_decrypt`
- `_compress`
- `_decompress`
- `_abstract_text`
- `_rehydrate_text_gist`
- `_normalize_date`
- `_get_current_disk_usage_gb`
- `_simulate_disk_lag_and_check_limit`
- `_save_core_memory_to_file`
- `_load_core_memory_from_file`
- `store_experience`
- `retrieve_relevant_memories`
- `recall_gist`
- `recall_raw_gist`
- `_deserialize_memory`
- `query_by_date_range`
- `_perform_deletion_check`
- `_delete_old_experiences`
- `query_core_memory`
- `_fallback_score`
- `increment_metadata_field`

## 3. 建议
1. 详细审查备份实现中独有的函数，确认是否有用功能需要合并到主实现
2. 对于实现不同的函数，需要详细对比代码，选择更好的实现
3. 确保删除备份实现前，所有有用功能都已合并到主实现
