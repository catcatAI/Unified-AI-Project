# 訓練數據使用指南

## 已下載數據集

下載時間: 2025-08-24 00:59:19
數據位置: d:\Projects\Unified-AI-Project\data


### Flickr30K Sample
- **大小**: 2.5 GB
- **許可證**: CC BY 4.0
- **用途**: VisionService訓練
- **描述**: 視覺-語言理解數據集樣本
- **路徑**: `d:\Projects\Unified-AI-Project\data/flickr30k_sample/`


### Common Voice 中文樣本
- **大小**: 15.0 GB
- **許可證**: CC0
- **用途**: AudioService訓練
- **描述**: 中文語音識別數據集
- **路徑**: `d:\Projects\Unified-AI-Project\data/common_voice_zh/`


### MS COCO Captions
- **大小**: 1.2 GB
- **許可證**: CC BY 4.0
- **用途**: 多模態理解
- **描述**: 圖像描述數據集
- **路徑**: `d:\Projects\Unified-AI-Project\data/coco_captions/`


### Visual Genome Sample
- **大小**: 12.0 GB
- **許可證**: CC BY 4.0
- **用途**: CausalReasoningEngine訓練
- **描述**: 場景圖和關係理解
- **路徑**: `d:\Projects\Unified-AI-Project\data/visual_genome_sample/`


## 使用方法

### 1. 訓練 VisionService
```python
from src.services.vision_service import VisionService
from src.core_ai.memory.vector_store import VectorMemoryStore

# 使用 Flickr30K 或 COCO 數據
vision_service = VisionService()
# 訓練代碼...
```

### 2. 訓練 AudioService  
```python
from src.services.audio_service import AudioService

# 使用 Common Voice 數據
audio_service = AudioService()
# 訓練代碼...
```

### 3. 訓練 CausalReasoningEngine
```python
from src.core_ai.reasoning.causal_reasoning_engine import CausalReasoningEngine

# 使用 Visual Genome 數據
reasoning_engine = CausalReasoningEngine()
# 訓練代碼...
```

## 注意事項

1. **版權合規**: 所有數據集均為開源，請遵守各自的許可證條款
2. **存儲管理**: 定期清理不需要的數據以節省空間
3. **數據預處理**: 使用前建議進行數據清洗和格式化
4. **備份建議**: 重要的訓練結果建議備份到雲端
