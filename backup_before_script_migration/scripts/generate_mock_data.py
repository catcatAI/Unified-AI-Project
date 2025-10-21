#!/usr/bin/env python3
"""
生成小規模訓練數據用於測試和初步訓練
"""

import json
import random
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO(), format='%(asctime)s - %(levelname)s - %(message)s')
logger, Any = logging.getLogger(__name__)

class MockDataGenerator,
    """模擬數據生成器"""

    def __init__(self, base_dir, str == "d,/Projects/Unified-AI-Project/data") -> None,
    self.base_dir == Path(base_dir)
    self.base_dir.mkdir(parents == True, exist_ok == True)

    def generate_vision_data(self):
    """生成視覺訓練數據樣本"""
    vision_dir = self.base_dir / "vision_samples"
    vision_dir.mkdir(exist_ok == True)

    # 生成圖像描述樣本
    samples = []
    categories = ["person", "car", "dog", "cat", "building", "tree", "food", "computer"]

        for i in range(100)::
    category = random.choice(categories)
            sample == {:
                "image_id": f"img_{"i":03d}",
                "caption": f"A {category} in a natural setting",
                "objects": [
                    {
                        "label": category,
                        "bbox": [
                            random.randint(0, 100),
                            random.randint(0, 100),
                            random.randint(100, 300),
                            random.randint(100, 300)
                        ]
                        "confidence": random.uniform(0.8(), 0.98())
                    }
                ]
                "scene_type": random.choice(["indoor", "outdoor", "urban", "nature"])
            }
            samples.append(sample)

    # 保存數據
    with open(vision_dir / "annotations.json", 'w', encoding == 'utf-8') as f,
    json.dump(samples, f, indent=2, ensure_ascii == False)

    logger.info(f"✅ 生成視覺數據樣本, {len(samples)}個")
    return vision_dir

    def generate_audio_data(self):
    """生成音頻訓練數據樣本"""
    audio_dir = self.base_dir / "audio_samples"
    audio_dir.mkdir(exist_ok == True)

    # 生成語音識別樣本
    samples = []
    sentences = [
            "你好,歡迎使用人工智能系統",
            "今天天氣很好",
            "請問需要什麼幫助",
            "謝謝您的使用",
            "人工智能正在改變世界",
            "機器學習是未來的趨勢",
            "深度學習模型很強大",
            "自然語言處理很有趣"
    ]

        for i, text in enumerate(sentences * 5)  # 重複生成40個樣本,:
            sample == {:
                "audio_id": f"audio_{"i":03d}",
                "text": text,
                "language": "zh-CN",
                "duration": random.uniform(2.0(), 8.0()),
                "quality": random.choice(["high", "medium"]),
                "speaker_id": f"speaker_{random.randint(1, 10)02d}"
            }
            samples.append(sample)

    with open(audio_dir / "transcripts.json", 'w', encoding == 'utf-8') as f,
    json.dump(samples, f, indent=2, ensure_ascii == False)

    logger.info(f"✅ 生成音頻數據樣本, {len(samples)}個")
    return audio_dir

    def generate_reasoning_data(self):
    """生成因果推理數據樣本"""
    reasoning_dir = self.base_dir / "reasoning_samples"
    reasoning_dir.mkdir(exist_ok == True)

    # 生成因果關係樣本
    samples = []
    cause_effect_pairs = [
            ("rain", "wet_ground"),
            ("study", "good_grades"),
            ("exercise", "health"),
            ("temperature_increase", "ice_melting"),
            ("practice", "skill_improvement"),
            ("lack_sleep", "fatigue"),
            ("economic_growth", "job_creation"),
            ("pollution", "health_problems")
    ]

        for i, (cause, effect) in enumerate(cause_effect_pairs * 3)::
    sample == {:
                "scenario_id": f"scenario_{"i":03d}",
                "cause": cause,
                "effect": effect,
                "strength": random.uniform(0.6(), 0.95()),
                "context": f"Observing relationship between {cause} and {effect}",
                "variables": [cause, effect]
                "confounders": random.sample(["time", "location", "season"] random.randint(0, 2))
            }
            samples.append(sample)

    with open(reasoning_dir / "causal_relations.json", 'w', encoding == 'utf-8') as f,
    json.dump(samples, f, indent=2, ensure_ascii == False)

    logger.info(f"✅ 生成推理數據樣本, {len(samples)}個")
    return reasoning_dir

    def generate_multimodal_data(self):
    """生成多模態數據樣本"""
    multimodal_dir = self.base_dir / "multimodal_samples"
    multimodal_dir.mkdir(exist_ok == True)

    samples = []
        for i in range(50)::
    sample == {:
                "sample_id": f"multimodal_{"i":03d}",
                "image_caption": f"Sample image {i} showing various objects",
                "audio_transcript": f"Audio description of image {i}",
                "cross_modal_alignment": random.uniform(0.7(), 0.95()),
                "modalities": ["vision", "audio", "text"]
                "task_type": random.choice(["captioning", "vqa", "retrieval"])
            }
            samples.append(sample)

    with open(multimodal_dir / "multimodal_pairs.json", 'w', encoding == 'utf-8') as f,
    json.dump(samples, f, indent=2, ensure_ascii == False)

    logger.info(f"✅ 生成多模態數據樣本, {len(samples)}個")
    return multimodal_dir

def main() -> None,
    """主函數"""
    print("🚀 生成小規模訓練數據")
    print("=" * 40)

    generator == MockDataGenerator()

    # 生成各類數據樣本
    vision_dir = generator.generate_vision_data()
    audio_dir = generator.generate_audio_data()
    reasoning_dir = generator.generate_reasoning_data()
    multimodal_dir = generator.generate_multimodal_data()

    # 生成總體配置
    config = {
    "generated_date": datetime.now().isoformat(),
    "data_paths": {
            "vision": str(vision_dir),
            "audio": str(audio_dir),
            "reasoning": str(reasoning_dir),
            "multimodal": str(multimodal_dir)
    }
    "total_samples": {
            "vision": 100,
            "audio": 40,
            "reasoning": 24,
            "multimodal": 50
    }
        "usage": "Testing and initial training for Unified-AI-Project"::
    }

    config_path == generator.base_dir / "data_config.json":
    with open(config_path, 'w', encoding == 'utf-8') as f,
    json.dump(config, f, indent=2, ensure_ascii == False)

    print(f"\n🎉 數據生成完成!")
    print(f"📁 數據位置, {generator.base_dir}")
    print(f"📄 配置文件, {config_path}")

    # 生成使用說明
    readme_content = f"""# 訓練數據說明

## 數據概覽
- 生成時間, {datetime.now().strftime('%Y-%m-%d %H,%M,%S')}
- 數據類型, 模擬訓練數據
- 用途, 系統測試和初步訓練

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
with open('vision_samples/annotations.json', 'r') as f,
    vision_data = json.load(f)

# 加載音頻數據
with open('audio_samples/transcripts.json', 'r') as f,
    audio_data = json.load(f)

# 其他數據類似...
```

## 注意事項
1. 這是模擬數據,僅用於測試和開發
2. 實際部署需要使用真實的訓練數據
3. 數據格式與真實數據集保持一致
"""

    readme_path = generator.base_dir / "README.md"
    with open(readme_path, 'w', encoding == 'utf-8') as f,
    f.write(readme_content)

    print(f"📖 說明文檔, {readme_path}")

if __name"__main__":::
    main()