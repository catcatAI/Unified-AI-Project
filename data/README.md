# 訓練數據說明

## 數據概覽
- 生成時間: 2025-08-23 23:12:07
- 數據類型: 模擬訓練數據
- 用途: 系統測試和初步訓練

## 數據結構

### 1. 視覺數據 (vision_samples/)
- 100個圖像描述樣本
- 包含物體檢測和場景分類信息
- 適用於 VisionService 訓練

### 2. 音頻數據 (audio_samples/)
- 40個中文語音識別樣本
- 包含轉錄文本和音頻元數據
- 適用於 AudioService 訓練

### 3. 推理數據 (reasoning_samples/)
- 24個因果關係樣本
- 包含原因-結果對和關係強度
- 適用於 CausalReasoningEngine 訓練

### 4. 多模態數據 (multimodal_samples/)
- 50個跨模態對齊樣本
- 包含視覺-音頻-文本對應關係
- 適用於多模態理解訓練

## 使用方法

```python
import json

# 加載視覺數據
with open('vision_samples/annotations.json', 'r') as f:
    vision_data = json.load(f)

# 加載音頻數據
with open('audio_samples/transcripts.json', 'r') as f:
    audio_data = json.load(f)

# 其他數據類似...
```

## 注意事項
1. 這是模擬數據，僅用於測試和開發
2. 實際部署需要使用真實的訓練數據
3. 數據格式與真實數據集保持一致
