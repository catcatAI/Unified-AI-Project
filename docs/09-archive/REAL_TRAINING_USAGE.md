# 真实训练功能使用指南

## 概述

本文档说明如何使用Unified AI
Project中的真实训练功能。真实训练功能使用TensorFlow进行实际的神经网络训练，而不是模拟训练。

## 可用的真实训练选项

1. **real_math_model_training** - 使用TensorFlow进行真实的数学模型训练
2. **real_logic_model_training** - 使用TensorFlow进行真实的逻辑推理模型训练

## 使用方法

### 通过训练管理器使用

1. 运行训练管理器：

   ```
   tools\train-manager.bat
   ```

2. 选择"1. 🚀 Start Training (開始訓練)"

3. 在预设选项中选择：
   - 8. real_math_model_training - 真实数学模型训练
   - 9. real_logic_model_training - 真实逻辑推理模型训练

### 直接使用训练脚本

您也可以直接运行训练脚本：

```bash
# 切换到training目录
cd training

# 运行真实数学模型训练
python train_model.py --preset real_math_model_training

# 运行真实逻辑推理模型训练
python train_model.py --preset real_logic_model_training
```

## 模型架构

### 数学模型

- 使用LSTM编码器-解码器架构
- 输入序列编码为固定长度向量
- 解码器生成输出序列
- 适用于基本算术运算（加法、减法、乘法、除法）

### 逻辑推理模型

- 使用嵌入层+LSTM层+密集层的简单序列分类架构
- 适用于基本逻辑运算（AND、OR、NOT）

## 训练数据

### 数学模型数据

- 位置：`apps/backend/data/raw_datasets/arithmetic_train_dataset.json`
- 格式：JSON文件，包含输入表达式和期望输出
- 示例：{"input": "10 + 5", "target": "15"}

### 逻辑推理模型数据

- 位置：`apps/backend/data/raw_datasets/logic_train.json`
- 格式：JSON文件，包含逻辑表达式和布尔结果
- 示例：{"proposition": "true AND false", "answer": false}

## 模型输出

训练完成后，模型文件将保存在以下位置：

- 数学模型：`apps/backend/data/models/arithmetic_model.keras`
- 逻辑模型：`apps/backend/data/models/logic_model_nn.keras`

字符映射文件也将保存：

- 数学模型字符映射：`apps/backend/data/models/arithmetic_char_maps.json`
- 逻辑模型字符映射：`apps/backend/data/models/logic_model_char_maps.json`

## 验证训练结果

您可以运行测试脚本来验证训练结果：

```bash
python test_trained_models.py
```

这将测试训练好的模型是否能正确执行基本的数学和逻辑运算。

## 故障排除

### TensorFlow错误

如果遇到TensorFlow相关错误，请确保已安装正确版本：

```bash
pip install tensorflow
```

### 数据文件缺失

如果提示数据文件缺失，请先生成训练数据：

```bash
python apps/backend/src/tools/math_model/data_generator.py
python apps/backend/src/tools/logic_model/logic_data_generator.py
```

### 模型文件未找到

如果提示模型文件未找到，请确保训练已完成并且模型文件已正确保存。
