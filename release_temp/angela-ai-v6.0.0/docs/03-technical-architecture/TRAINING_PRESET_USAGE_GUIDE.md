# 训练预设使用指南

## 概述

本文档详细说明了如何使用 Unified-AI-Project 中的训练预设配置。预设配置提供了一种简化的方式来启动不同类型的训练任务，而无需手动配置所有参数。

## 预设配置文件

预设配置文件位于: `training/configs/training_preset.json`

该文件包含了多种训练场景的预设参数，包括数据集选择、训练轮数、批次大小等。

## 可用的训练场景

### 1. 快速开始 (Quick Start)
- **场景标识**: `quick_start`
- **适用场景**: 快速验证训练流程，测试模型基本功能
- **数据集**: 
  - vision_samples (视觉数据样本)
  - audio_samples (音频数据样本)
  - reasoning_samples (推理数据样本)
- **训练参数**:
  - 训练轮数: 3
  - 批次大小: 8
  - 目标模型: vision_service, audio_service, causal_reasoning_engine

### 2. 全面训练 (Comprehensive Training)
- **场景标识**: `comprehensive_training`
- **适用场景**: 完整训练所有模型，获得最佳性能
- **数据集**: 所有可用数据集
- **训练参数**:
  - 训练轮数: 50
  - 批次大小: 32
  - 目标模型: vision_service, audio_service, causal_reasoning_engine, multimodal_service

### 3. 视觉专注 (Vision Focus)
- **场景标识**: `vision_focus`
- **适用场景**: 专门训练视觉服务模型
- **数据集**: 视觉相关数据集
- **训练参数**:
  - 训练轮数: 30
  - 批次大小: 16
  - 目标模型: vision_service

### 4. 音频专注 (Audio Focus)
- **场景标识**: `audio_focus`
- **适用场景**: 专门训练音频服务模型
- **数据集**: 音频相关数据集
- **训练参数**:
  - 训练轮数: 20
  - 批次大小: 8
  - 目标模型: audio_service

## 使用方法

### 方法1: 使用训练管理器 (推荐)

1. 运行训练管理器:
   ```
   tools\train-manager.bat
   ```

2. 选择"开始训练"选项

3. 选择"使用预设配置开始训练"

4. 根据需要选择训练场景

### 方法2: 直接运行训练脚本

在 `apps/backend` 目录下运行:

```bash
# 激活虚拟环境
call venv\Scripts\activate.bat

# 使用预设配置训练
python ..\..\training\train_model.py --preset quick_start

# 或使用其他预设
python ..\..\training\train_model.py --preset comprehensive_training
python ..\..\training\train_model.py --preset vision_focus
python ..\..\training\train_model.py --preset audio_focus
```

## 输出文件

训练完成后，将在以下目录生成输出文件:

- **模型文件**: `training/models/`
- **检查点文件**: `training/checkpoints/`
- **训练报告**: `training/reports/`

## 自定义预设配置

如果您需要自定义预设配置，可以直接编辑 `training/configs/training_preset.json` 文件。

### 预设配置结构

```json
{
  "preset_name": "Unified-AI-Project Default Preset",
  "training_scenarios": {
    "场景标识": {
      "description": "场景描述",
      "datasets": ["数据集列表"],
      "epochs": 训练轮数,
      "batch_size": 批次大小,
      "target_models": ["目标模型列表"]
    }
  }
}
```

## 故障排除

### 1. 预设配置文件未找到
确保 `training/configs/training_preset.json` 文件存在。

### 2. 数据集路径错误
检查预设配置文件中的数据路径是否正确。

### 3. 训练失败
查看控制台输出和日志文件以获取更多信息。

## 最佳实践

1. **快速验证**: 使用"快速开始"场景验证训练流程
2. **完整训练**: 使用"全面训练"场景进行完整模型训练
3. **专项优化**: 使用专注场景对特定模型进行优化
4. **定期备份**: 定期备份训练模型和检查点文件
5. **性能监控**: 监控训练过程中的性能指标

## 相关文档

- [训练准备检查清单](TRAINING_PREPARATION_CHECKLIST.md)
- [训练配置文件说明](../README.md)
