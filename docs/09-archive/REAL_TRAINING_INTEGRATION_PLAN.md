# 真实训练功能集成方案

## 概述

本文档描述了如何将项目中已有的真实神经网络训练功能（math_model和logic_model）集成到主训练系统中，替换当前的模拟训练系统。

## 集成目标

1. 保留现有的训练管理功能（暂停、继续、检查点等）
2. 集成真实的TensorFlow训练功能
3. 提供统一的训练接口
4. 支持多种训练场景（数学模型、逻辑模型等）

## 设计方案

### 1. 训练器架构改进

在现有的[ModelTrainer](../training/train_model.py)类中添加真实训练支持：

```python
class ModelTrainer:
    def __init__(self, config_path=None, preset_path=None):
        # 现有代码...
        self.tensorflow_available = self._check_tensorflow_availability()

    def _check_tensorflow_availability(self):
        """检查TensorFlow是否可用"""
        try:
            import tensorflow as tf
            return True
        except ImportError:
            return False

    def train_with_preset(self, scenario_name):
        """使用预设配置进行训练"""
        scenario = self.get_preset_scenario(scenario_name)
        if not scenario:
            return False

        # 根据场景类型选择训练方式
        target_models = scenario.get('target_models', [])
        if 'math_model' in target_models:
            return self._train_math_model(scenario)
        elif 'logic_model' in target_models:
            return self._train_logic_model(scenario)
        else:
            # 默认使用模拟训练
            return self._simulate_training(scenario)
```

### 2. 真实训练函数实现

添加专门的训练函数来调用真实的TensorFlow训练脚本：

```python
def _train_math_model(self, scenario):
    """训练数学模型"""
    if not self.tensorflow_available:
        logger.error("❌ TensorFlow不可用，无法训练数学模型")
        return False

    try:
        # 导入数学模型训练脚本
        from apps.backend.src.tools.math_model.train import main as train_math_model
        logger.info("🚀 开始训练数学模型...")
        train_math_model()
        logger.info("✅ 数学模型训练完成")
        return True
    except Exception as e:
        logger.error(f"❌ 数学模型训练失败: {e}")
        return False

def _train_logic_model(self, scenario):
    """训练逻辑模型"""
    if not self.tensorflow_available:
        logger.error("❌ TensorFlow不可用，无法训练逻辑模型")
        return False

    try:
        # 导入逻辑模型训练脚本
        from apps.backend.src.tools.logic_model.train_logic_model import main as train_logic_model
        logger.info("🚀 开始训练逻辑模型...")
        train_logic_model()
        logger.info("✅ 逻辑模型训练完成")
        return True
    except Exception as e:
        logger.error(f"❌ 逻辑模型训练失败: {e}")
        return False
```

### 3. 训练场景配置

在[training_preset.json](../training/configs/training_preset.json)中添加新的训练场景：

```json
{
  "training_scenarios": {
    "math_model_training": {
      "description": "训练数学计算模型",
      "datasets": ["arithmetic_train_dataset"],
      "epochs": 50,
      "batch_size": 64,
      "target_models": ["math_model"],
      "checkpoint_interval": 5
    },
    "logic_model_training": {
      "description": "训练逻辑推理模型",
      "datasets": ["logic_train_dataset"],
      "epochs": 50,
      "batch_size": 32,
      "target_models": ["logic_model"],
      "checkpoint_interval": 5
    }
  }
}
```

### 4. 训练管理器更新

更新[train-manager.bat](../tools/train-manager.bat)以支持新的训练选项：

```batch
echo Available training presets: (可用的訓練預設)
echo   1. quick_start - Quick training with mock data for testing (使用模擬數據進行快速訓練以進行測試)
echo   2. comprehensive_training - Full training with all available data (使用所有可用數據進行完整訓練)
echo   3. vision_focus - Focus on vision-related models (專注於視覺相關模型)
echo   4. audio_focus - Focus on audio-related models (專注於音頻相關模型)
echo   5. full_dataset_training - Full dataset training with auto-pause/resume (完整數據集訓練，支持自動暫停/繼續)
echo   6. math_model_training - Train mathematical calculation model (訓練數學計算模型)
echo   7. logic_model_training - Train logical reasoning model (訓練邏輯推理模型)
echo   8. Custom training (自定義訓練)
```

## 实施步骤

### 1. 修改训练脚本

修改[train_model.py](../training/train_model.py)以支持真实训练功能：

1. 添加TensorFlow可用性检查
2. 实现数学模型和逻辑模型的训练函数
3. 更新训练流程以调用真实训练

### 2. 更新配置文件

更新[training_preset.json](../training/configs/training_preset.json)以添加新的训练场景：

1. 添加数学模型训练场景
2. 添加逻辑模型训练场景

### 3. 更新训练管理器

更新[train-manager.bat](../tools/train-manager.bat)以支持新的训练选项：

1. 添加新的训练预设选项
2. 更新用户界面

### 4. 创建文档

创建使用文档说明如何使用真实训练功能：

1. 安装TensorFlow依赖
2. 准备训练数据
3. 运行真实训练

## 预期效果

1. 用户可以选择使用真实训练而不是模拟训练
2. 保留所有现有的训练管理功能
3. 提供更真实的训练体验
4. 支持项目中已有的神经网络模型
