#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逻辑模型训练脚本
使用Keras构建和训练逻辑推理模型
"""

import json
import os
import sys

# Add src directory to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# 添加兼容性导入
# 使用小写变量名避免常量重定义错误
keras_available = False
EarlyStopping = None
ModelCheckpoint = None
ReduceLROnPlateau = None
Sequential = None
Dense = None
Dropout = None
BatchNormalization = None
Adam = None
tf = None

try:
    # 设置环境变量以解决Keras兼容性问题
    os.environ['TF_USE_LEGACY_KERAS'] = '1'
    
    import tensorflow as tf_imported
    tf = tf_imported
    
    # 尝试导入Keras组件
    if hasattr(tf_imported, 'keras'):
        keras_module = tf_imported.keras
        if hasattr(keras_module, 'callbacks'):
            callbacks_module = keras_module.callbacks
            EarlyStopping = getattr(callbacks_module, 'EarlyStopping', None)
            ModelCheckpoint = getattr(callbacks_module, 'ModelCheckpoint', None)
            ReduceLROnPlateau = getattr(callbacks_module, 'ReduceLROnPlateau', None)
        
        if hasattr(keras_module, 'models'):
            models_module = keras_module.models
            Sequential = getattr(models_module, 'Sequential', None)
            
        if hasattr(keras_module, 'layers'):
            layers_module = keras_module.layers
            Dense = getattr(layers_module, 'Dense', None)
            Dropout = getattr(layers_module, 'Dropout', None)
            BatchNormalization = getattr(layers_module, 'BatchNormalization', None)
            
        if hasattr(keras_module, 'optimizers'):
            optimizers_module = keras_module.optimizers
            Adam = getattr(optimizers_module, 'Adam', None)
        
        keras_available = True
except ImportError as e:
    print(f"Warning: Could not import tensorflow: {e}")
    # 保持默认值为None和False

# 修复导入路径
sys.path.append(os.path.join(SCRIPT_DIR))
try:
    from logic_model_nn import LogicNNModel, get_logic_char_token_maps, preprocess_logic_data
except ImportError as e:
    print(f"Error importing from logic_model_nn: {e}")
    print("Ensure logic_model_nn.py is in the same directory and src is in sys.path.")
    sys.exit(1)

# --- Configuration ---
TRAIN_DATA_PATH = os.path.join(PROJECT_ROOT, "data/raw_datasets/logic_train.json")
MODEL_SAVE_PATH = os.path.join(PROJECT_ROOT, "data/models/logic_model_nn.keras")
CHAR_MAP_SAVE_PATH = os.path.join(PROJECT_ROOT, "data/models/logic_model_char_maps.json") # Consistent with logic_model_nn.py

# Training Hyperparameters
BATCH_SIZE = 32
EPOCHS = 50 # Can be adjusted, EarlyStopping will help
EMBEDDING_DIM = 32 # Should match model definition if not loaded from char_map
LSTM_UNITS = 64    # Should match model definition if not loaded from char_map
VALIDATION_SPLIT = 0.1 # Using a portion of the training data for validation during training

def load_logic_dataset(file_path):
    """Loads the logic dataset from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        if not isinstance(dataset, list) or \
           not all(isinstance(item, dict) and "proposition" in item and "answer" in item for item in dataset):
            raise ValueError("Dataset format is incorrect. Expected list of {'proposition': str, 'answer': bool}.")
        return dataset
    except FileNotFoundError:
        print(f"Error: Dataset file not found at {file_path}")
        print("Please generate the dataset first using logic_data_generator.py")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
    except ValueError as e:
        print(f"Error: {e}")
    return None

def main -> None:  # 修复函数定义，添加缺失的括号
    print("Starting Logic NN Model training process...")

    # 1. Load data
    print(f"Loading training dataset from {TRAIN_DATA_PATH}...")
    dataset = load_logic_dataset(TRAIN_DATA_PATH)
    if dataset is None:
        return
    print(f"Loaded {len(dataset)} training samples.")

    # 2. Create/Load character token maps and determine sequence lengths
    # get_logic_char_token_maps already saves the maps to CHAR_MAP_SAVE_PATH
    print("Creating/Loading character token maps...")
    char_to_token, token_to_char, vocab_size, max_seq_len = \
        get_logic_char_token_maps(TRAIN_DATA_PATH) # This function now also saves the map

    print(f"Vocabulary Size: {vocab_size}")
    print(f"Max Sequence Length: {max_seq_len}")

    # 3. Preprocess data
    print("Preprocessing data for the model...")
    X, y_categorical = preprocess_logic_data(TRAIN_DATA_PATH, char_to_token, max_seq_len, num_classes=2)
    
    # 检查数据是否成功加载
    if X is None or y_categorical is None:
        print("Error: Failed to preprocess data.")
        return

    print(f"X (input data) shape: {X.shape}")
    print(f"y (target data) shape: {y_categorical.shape}")

    # 4. Split data into training and validation (if not using fit's validation_split)
    # Using validation_split in model.fit is simpler here.
    # X_train, X_val, y_train, y_val = train_test_split(X, y_categorical, test_size=VALIDATION_SPLIT, random_state=42)
    # print(f"Training samples: {len(X_train)}, Validation samples: {len(X_val)}")


    # 5. Build the model
    print("Building the LogicNNModel...")
    logic_nn_model = LogicNNModel(
        max_seq_len=max_seq_len,
        vocab_size=vocab_size,
        embedding_dim=EMBEDDING_DIM,
        lstm_units=LSTM_UNITS
    )
    # The model is compiled within _build_model in LogicNNModel class

    # 6. Train the model
    print("Starting model training...")

    # 检查Keras组件是否可用
    if not keras_available:
        print("Error: Keras components not available.")
        return

    # 创建回调函数列表，检查各个组件是否可用
    callbacks = 
    if EarlyStopping is not None:
        callbacks.append(EarlyStopping(monitor='val_loss', patience=5, verbose=1, restore_best_weights=True))
    if ModelCheckpoint is not None:
        callbacks.append(ModelCheckpoint(MODEL_SAVE_PATH, monitor='val_loss', save_best_only=True, verbose=1))
    if ReduceLROnPlateau is not None:
        callbacks.append(ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=3, min_lr=0.00001, verbose=1))
    
    # 如果没有可用的回调函数，创建一个空列表
    if not callbacks:
        print("Warning: No Keras callbacks available.")
        callbacks = 

    # 确保模型存在且可调用
    if hasattr(logic_nn_model, 'model') and logic_nn_model.model is not None:
        history = logic_nn_model.model.fit(
            X, y_categorical, # Using all data, with validation_split in fit
            epochs=EPOCHS,
            batch_size=BATCH_SIZE,
            validation_split=VALIDATION_SPLIT, # Uses last 10% of data for validation
            callbacks=callbacks,
            shuffle=True
        )
    else:
        print("Error: Model is not available for training.")
        return

    print("Training complete.")
    # The ModelCheckpoint callback saves the best model automatically to MODEL_SAVE_PATH
    # logic_nn_model.save_model(MODEL_SAVE_PATH) # This would save the *final* state, not necessarily best

    print(f"Best trained model weights saved to {MODEL_SAVE_PATH}")
    print(f"Character maps used for this model are saved at {CHAR_MAP_SAVE_PATH}")

    # Optional: Plot training history (requires matplotlib)
    # import matplotlib.pyplot as plt
    # plt.plot(history.history['accuracy'], label='Training Accuracy')
    # plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
    # plt.title('Model Accuracy')
    # plt.ylabel('Accuracy')
    # plt.xlabel('Epoch')
    # plt.legend
    # plt.savefig('logic_model_training_accuracy.png')
    # print("Training accuracy plot saved to logic_model_training_accuracy.png")

if __name__ == '__main__':
    # Ensure training data exists
    if not os.path.exists(TRAIN_DATA_PATH):
        print(f"Training data JSON file not found at {TRAIN_DATA_PATH}.")
        print("Please run `logic_data_generator.py` first to create 'logic_train.json'.")
    else:
        main  # 修复函数调用，添加缺失的括号