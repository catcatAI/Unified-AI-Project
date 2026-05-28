# 真实训练功能使用指南

## 概述

本文档介绍了如何使用Unified-AI-Project中的真实神经网络训练功能，包括数学模型训练和逻辑模型训练。

## 功能特性

1. **真实TensorFlow训练**：使用真实的神经网络进行训练，而非模拟训练
2. **数学模型训练**：训练能够执行基本算术运算的序列到序列模型
3. **逻辑模型训练**：训练能够进行逻辑推理的神经网络模型
4. **完整的训练管理**：支持暂停、继续、检查点等训练管理功能
5. **自动依赖检查**：自动检测TensorFlow是否可用

## 环境准备

### 1. 安装TensorFlow依赖

确保已安装TensorFlow依赖：

```bash
# 进入项目根目录
cd Unified-AI-Project

# 激活虚拟环境
apps\backend\venv\Scripts\activate.bat

# 安装AI相关的依赖（包含TensorFlow）
pip install -e ".[ai_focused]"
```

### 2. 准备训练数据

#### 数学模型训练数据

生成数学训练数据：

```bash
# 激活虚拟环境
apps\backend\venv\Scripts\activate.bat

# 进入数学模型目录
cd apps\backend\src\tools\math_model

# 生成训练数据
python data_generator.py
```

#### 逻辑模型训练数据

生成逻辑训练数据：

```bash
# 激活虚拟环境
apps\backend\venv\Scripts\activate.bat

# 进入逻辑模型目录
cd apps\backend\src\tools\logic_model

# 生成训练数据
python logic_data_generator.py
```

## 使用方法

### 1. 通过训练管理器启动

```bash
# 运行训练管理器
tools\train-manager.bat
```

在菜单中选择相应的训练选项：

- 选项6：math_model_training - 训练数学计算模型
- 选项7：logic_model_training - 训练逻辑推理模型

### 2. 直接运行训练脚本

#### 训练数学模型

```bash
# 激活虚拟环境
apps\backend\venv\Scripts\activate.bat

# 进入训练目录
cd training

# 使用预设配置训练数学模型
python train_model.py --preset math_model_training
```

#### 训练逻辑模型

```bash
# 激活虚拟环境
apps\backend\venv\Scripts\activate.bat

# 进入训练目录
cd training

# 使用预设配置训练逻辑模型
python train_model.py --preset logic_model_training
```

### 3. 暂停和继续训练

#### 暂停训练

在训练过程中按 `Ctrl+C` 发送中断信号，训练会自动保存检查点并退出。

#### 继续训练

```bash
# 通过训练管理器继续训练
tools\train-manager.bat

# 选择继续训练选项（选项4）
# 然后选择相应的训练预设

# 或者直接运行训练脚本并添加--resume参数
cd training
python train_model.py --preset math_model_training --resume
```

## 训练配置

### 数学模型训练配置

```json
{
  "math_model_training": {
    "description": "Train mathematical calculation model",
    "datasets": ["arithmetic_train_dataset"],
    "epochs": 50,
    "batch_size": 64,
    "target_models": ["math_model"],
    "checkpoint_interval": 5
  }
}
```

### 逻辑模型训练配置

```json
{
  "logic_model_training": {
    "description": "Train logical reasoning model",
    "datasets": ["logic_train_dataset"],
    "epochs": 50,
    "batch_size": 32,
    "target_models": ["logic_model"],
    "checkpoint_interval": 5
  }
}
```

## 模型文件位置

训练完成后，模型文件将保存在以下位置：

- 数学模型：`data/models/arithmetic_model.keras`
- 逻辑模型：`data/models/logic_model_nn.keras`
- 检查点文件：`training/checkpoints/`
- 训练报告：`training/reports/`

## 性能说明

### 训练时间

真实训练比模拟训练需要更多时间：

- 数学模型训练：约30-60分钟（取决于硬件配置）
- 逻辑模型训练：约20-40分钟（取决于硬件配置）

### 硬件要求

- **推荐配置**：
  - CPU：4核或以上
  - 内存：8GB或以上
  - 磁盘空间：至少5GB可用空间

- **可选配置**：
  - GPU：支持CUDA的NVIDIA显卡可显著加速训练

## 故障排除

### TensorFlow导入错误

如果遇到TensorFlow导入错误：

1. 确保已正确安装TensorFlow依赖
2. 检查虚拟环境是否已激活
3. 确认Python版本兼容性（推荐3.8-3.11）

### 训练数据缺失

如果提示训练数据缺失：

1. 确保已生成相应的训练数据
2. 检查数据文件路径是否正确
3. 确认数据文件格式是否正确

### 内存不足

如果训练过程中出现内存不足错误：

1. 减小批次大小（batch_size）
2. 关闭其他占用内存的程序
3. 增加虚拟内存（页面文件）大小

## 最佳实践

### 1. 训练前准备

1. 确保有足够的磁盘空间
2. 关闭不必要的程序以释放内存
3. 备份重要数据

### 2. 训练过程中

1. 定期检查训练进度
2. 监控系统资源使用情况
3. 不要频繁中断训练

### 3. 训练完成后

1. 评估模型性能
2. 保存重要的模型文件
3. 清理不必要的检查点文件

## 高级用法

### 自定义训练参数

可以通过修改[training_preset.json](../training/configs/training_preset.json)文件来自定义训练参数：

```json
{
  "math_model_training": {
    "description": "Train mathematical calculation model",
    "datasets": ["arithmetic_train_dataset"],
    "epochs": 100,  // 增加训练轮数
    "batch_size": 32,  // 减小批次大小以节省内存
    "target_models": ["math_model"],
    "checkpoint_interval": 10
  }
}
```

### 使用GPU加速训练

如果系统有支持CUDA的NVIDIA显卡，训练将自动使用GPU加速。

检查GPU是否被使用：

```python
import tensorflow as tf
print("GPU可用:", tf.config.list_physical_devices('GPU'))
```

## 结论

通过集成真实训练功能，Unified-AI-Project现在支持使用真实的神经网络进行训练，提供了更强大的AI能力。用户可以选择使用数学模型进行算术运算训练，或使用逻辑模型进行逻辑推理训练，同时保留了所有原有的训练管理功能。