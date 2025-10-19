# 训练数据集位置总结报告

**报告日期**: 2025年10月11日  
**项目**: Unified AI Project  
**状态**: ✅ 完成

## 📝 重要说明

**注意**: 部分数据目录可能因为 `.gitignore` 文件的设置而在IDE中不可见，但实际存在于文件系统中。需要通过终端命令查看完整文件结构。

## 📋 概述

本报告总结了Unified AI Project项目中训练数据集的位置、结构和内容。

## 🗂️ 数据集位置

### 1. 主数据目录
```
项目根目录/data/
├── README.md                          # 数据集说明文档
├── data_config.json                   # 数据配置文件
├── vision_samples/                    # 视觉数据样本目录（可能包含被忽略的文件）
├── audio_samples/                     # 音频数据样本目录（可能包含被忽略的文件）
├── reasoning_samples/                 # 推理数据样本目录（可能包含被忽略的文件）
├── multimodal_samples/                # 多模态数据样本目录（可能包含被忽略的文件）
├── flickr30k_sample/                  # Flickr30k数据样本目录（被.gitignore忽略）
├── common_voice_zh/                   # Common Voice中文数据目录（被.gitignore忽略）
├── coco_captions/                     # COCO标注数据目录（被.gitignore忽略）
├── visual_genome_sample/              # Visual Genome数据样本目录（被.gitignore忽略）
└── concept_models_training_data/      # 概念模型训练数据目录（包含实际文件）
```

### 2. 原始数据集目录
```
项目根目录/data/raw_datasets/          # 逻辑模型训练数据目录（包含实际文件）
```

### 3. 训练配置目录
```
项目根目录/training/configs/
├── training_config.json               # 基本训练配置
├── training_preset.json               # 训练预设配置（详细说明数据集路径）
└── training_preset_fixed.json         # 修复后的训练预设配置
```

## 📊 数据集详情

### 根据训练预设配置文件 (training_preset.json) 中的信息：

### 1. Mock数据集
- **vision_samples**: `data/vision_samples` (100个样本)
- **audio_samples**: `data/audio_samples` (40个样本)
- **reasoning_samples**: `data/reasoning_samples` (24个样本)
- **multimodal_samples**: `data/multimodal_samples` (50个样本)

### 2. 概念模型数据集
- **concept_models_docs**: `data/concept_models_training_data/concept_models_docs_training_data.json` (1000个样本)
- **environment_simulation_data**: `data/concept_models_training_data/environment_simulation_data.json` (100个样本)
- **causal_reasoning_data**: `data/concept_models_training_data/causal_reasoning_data.json` (50个样本)
- **adaptive_learning_data**: `data/concept_models_training_data/adaptive_learning_data.json` (50个样本)
- **alpha_deep_model_data**: `data/concept_models_training_data/alpha_deep_model_data.json` (50个样本)

### 3. 下载数据集
- **flickr30k_sample**: `data/flickr30k_sample`
- **common_voice_zh**: `data/common_voice_zh`
- **coco_captions**: `data/coco_captions`
- **visual_genome_sample**: `data/visual_genome_sample`

## 📁 数据集类型

### 1. 图像相关数据集
- **图像标注数据**: flickr30k_sample, coco_captions, visual_genome_sample
- **视觉样本**: vision_samples

### 2. 音频相关数据集
- **语音数据**: common_voice_zh, audio_samples

### 3. 文本/推理相关数据集
- **因果关系数据**: reasoning_samples, causal_reasoning_data
- **概念模型文档**: concept_models_docs
- **环境模拟数据**: environment_simulation_data
- **自适应学习数据**: adaptive_learning_data
- **深度模型参数**: alpha_deep_model_data

### 4. 多模态数据集
- **跨模态数据**: multimodal_samples

## 🧪 训练数据生成器

### 1. 逻辑模型数据生成器
- **文件位置**: `apps/backend/src/core/tools/logic_model/logic_data_generator.py`
- **输出目录**: `data/raw_datasets/`
- **生成文件**: 
  - `logic_train.json` (5000个样本)
  - `logic_test.json` (1000个样本)

### 2. 数学模型数据生成器
- **文件位置**: `apps/backend/src/core/tools/math_model/data_generator.py`

## ⚠️ 当前状态

### 部分数据目录实际存在但可能被忽略
通过终端命令检查发现，部分数据目录实际包含文件，但由于 `.gitignore` 文件的设置，这些文件在IDE中可能不可见：

1. **`data/concept_models_training_data/` 目录包含多个JSON文件**:
   - `concept_models_docs_training_data.json`
   - `environment_simulation_data.json`
   - `causal_reasoning_data.json`
   - `adaptive_learning_data.json`
   - `alpha_deep_model_data.json`
   - `data_config.json`

2. **`data/raw_datasets/` 目录包含多个数据文件**:
   - `smoke_math.json`
   - `smoke_math_csv.csv`
   - `arithmetic_train_dataset.json`
   - 等其他数据文件

3. **`data/` 根目录包含**:
   - `test_image.jpg`
   - `test_audio.mp3`
   - `test_text.txt`
   - 以及其他测试文件

### 数据生成需求
需要运行相应的数据生成脚本来创建训练数据集：
1. 逻辑模型数据：运行 `logic_data_generator.py`
2. 数学模型数据：运行 `data_generator.py`
3. 其他数据集：需要手动下载或生成

## 🎯 下一步建议

### 1. 生成训练数据
```bash
# 生成逻辑模型训练数据
python apps/backend/src/core/tools/logic_model/logic_data_generator.py

# 生成数学模型训练数据
python apps/backend/src/core/tools/math_model/data_generator.py
```

### 2. 下载外部数据集
- 下载Flickr30k数据集到 `data/flickr30k_sample/`
- 下载Common Voice中文数据到 `data/common_voice_zh/`
- 下载COCO标注数据到 `data/coco_captions/`
- 下载Visual Genome数据到 `data/visual_genome_sample/`

### 3. 创建Mock数据
- 为vision_samples、audio_samples、reasoning_samples、multimodal_samples创建模拟数据

### 4. 检查.gitignore设置
检查 `.gitignore` 文件中的忽略规则，确保必要的数据文件不会被意外忽略，同时保持大型数据集不被提交到版本控制系统中。

## 📋 总结

Unified AI Project项目定义了完整的训练数据集结构和路径，但实际的数据文件尚未生成或下载。项目包含：

✅ **完整的数据集配置** - 在training_preset.json中详细定义  
✅ **数据生成脚本** - 逻辑模型和数学模型数据生成器  
✅ **清晰的目录结构** - 按数据类型和用途组织  
✅ **扩展性设计** - 支持多种数据类型和训练场景  

**下一步**: 运行数据生成脚本并下载外部数据集以完成训练数据准备。