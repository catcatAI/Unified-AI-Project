#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数学模型训练脚本
使用Keras构建和训练数学计算模型
"""

import os
import json
import logging

# 添加兼容性导入
try:
    # 设置环境变量以解决Keras兼容性问题
    os.environ['TF_USE_LEGACY_KERAS'] = '1'

    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
    from tensorflow.keras.optimizers import Adam
    import tensorflow as tf
    KERAS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import keras, {e}")
    EarlyStopping = ModelCheckpoint = ReduceLROnPlateau = Sequential = Dense = Dropout = BatchNormalization = Adam = None
    tf = None
    KERAS_AVAILABLE = False

# Configuration
# Get absolute paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))

DATASET_PATH = os.path.join(PROJECT_ROOT, "data", "raw_datasets", "arithmetic_train_dataset.json")
MODEL_SAVE_PATH = os.path.join(PROJECT_ROOT, "data", "models", "arithmetic_model.keras")
CHAR_MAP_SAVE_PATH = os.path.join(PROJECT_ROOT, "data", "models", "arithmetic_char_maps.json")

# Training Hyperparameters
BATCH_SIZE = 64
EPOCHS = 50  # Increased epochs, with early stopping
LATENT_DIM = 256
EMBEDDING_DIM = 128
VALIDATION_SPLIT = 0.2

# Add src directory to path
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in os.sys.path:
    os.sys.path.insert(0, SRC_DIR)

# Import helper functions
try:
    from src.tools.math_model.data_processor import (
        load_dataset, 
        get_char_token_maps, 
        prepare_data,
        ArithmeticSeq2Seq
    )
except ImportError:
    # Define placeholder functions if not available
    def load_dataset(file_path):
        """从JSON文件加载数据集"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
            # 确保数据集是包含"problem"和"answer"键的字典列表
            if not isinstance(dataset, list) or not all(isinstance(item, dict) and "problem" in item and "answer" in item for item in dataset):
                raise ValueError("数据集格式不正确。期望包含{'problem': str, 'answer': str}字典的列表。")
            problems = [item['problem'] for item in dataset]
            answers = [item['answer'] for item in dataset]
            return problems, answers
        except FileNotFoundError:
            print(f"Error: 数据集文件未找到于 {file_path}")
            print("请先使用data_generator.py生成数据集")
            return None, None
        except json.JSONDecodeError:
            print(f"Error: 无法从 {file_path} 解码JSON")
            return None, None
        except ValueError as e:
            print(f"Error: {e}")
            return None, None
    
    def get_char_token_maps(problems, answers):
        """获取字符令牌映射"""
        all_chars = set()
        for p in problems:
            all_chars.update(p)
        for a in answers:
            all_chars.update(a)
        
        char_to_token = {c: i+1 for i, c in enumerate(sorted(all_chars))}
        char_to_token['\t'] = 0  # Start token
        char_to_token['\n'] = len(char_to_token)  # End token
        token_to_char = {i: c for c, i in char_to_token.items()}
        n_token = len(char_to_token)
        
        max_encoder_seq_length = max(len(p) for p in problems) + 1
        max_decoder_seq_length = max(len(a) for a in answers) + 2
        
        return char_to_token, token_to_char, n_token, max_encoder_seq_length, max_decoder_seq_length
    
    def prepare_data(problems, answers, char_to_token, max_encoder_seq_length, max_decoder_seq_length, n_token):
        """准备模型数据"""
        import numpy as np
        
        num_samples = len(problems)
        encoder_input_data = np.zeros((num_samples, max_encoder_seq_length, n_token), dtype='float32')
        decoder_input_data = np.zeros((num_samples, max_decoder_seq_length, n_token), dtype='float32')
        decoder_target_data = np.zeros((num_samples, max_decoder_seq_length, n_token), dtype='float32')
        
        for i, (input_text, target_text) in enumerate(zip(problems, answers)):
            for t, char in enumerate(input_text):
                encoder_input_data[i, t, char_to_token.get(char, 0)] = 1.0
            encoder_input_data[i, len(input_text), char_to_token['\t']] = 1.0
            
            for t, char in enumerate(target_text):
                decoder_input_data[i, t, char_to_token.get(char, 0)] = 1.0
                if t > 0:
                    decoder_target_data[i, t-1, char_to_token.get(char, 0)] = 1.0
            decoder_input_data[i, len(target_text), char_to_token['\n']] = 1.0
            decoder_target_data[i, len(target_text), char_to_token['\n']] = 1.0
        
        return encoder_input_data, decoder_input_data, decoder_target_data
    
    class ArithmeticSeq2Seq:
        """算术序列到序列模型"""
        def __init__(self, char_to_token, token_to_char, max_encoder_seq_length, 
                     max_decoder_seq_length, n_token, latent_dim=256, embedding_dim=128):
            self.char_to_token = char_to_token
            self.token_to_char = token_to_char
            self.max_encoder_seq_length = max_encoder_seq_length
            self.max_decoder_seq_length = max_decoder_seq_length
            self.n_token = n_token
            self.latent_dim = latent_dim
            self.embedding_dim = embedding_dim
            self.model = None
        
        def build_model(self):
            """构建模型"""
            if not KERAS_AVAILABLE:
                print("Keras不可用，无法构建模型")
                return
            
            from tensorflow.keras.layers import Input, LSTM, Embedding, Dense
            from tensorflow.keras.models import Model
            
            # Encoder
            encoder_inputs = Input(shape=(None, self.n_token))
            encoder = LSTM(self.latent_dim, return_state=True)
            encoder_outputs, state_h, state_c = encoder(encoder_inputs)
            encoder_states = [state_h, state_c]
            
            # Decoder
            decoder_inputs = Input(shape=(None, self.n_token))
            decoder_lstm = LSTM(self.latent_dim, return_sequences=True, return_state=True)
            decoder_outputs, _, _ = decoder_lstm(decoder_inputs, initial_state=encoder_states)
            decoder_dense = Dense(self.n_token, activation='softmax')
            decoder_outputs = decoder_dense(decoder_outputs)
            
            # Model
            self.model = Model([encoder_inputs, decoder_inputs], decoder_outputs)
            self.encoder_model = Model(encoder_inputs, encoder_states)
            
            decoder_state_input_h = Input(shape=(self.latent_dim,))
            decoder_state_input_c = Input(shape=(self.latent_dim,))
            decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]
            
            decoder_outputs2, state_h2, state_c2 = decoder_lstm(
                decoder_inputs, initial_state=decoder_states_inputs)
            decoder_states = [state_h2, state_c2]
            decoder_outputs2 = decoder_dense(decoder_outputs2)
            
            self.decoder_model = Model(
                [decoder_inputs] + decoder_states_inputs,
                [decoder_outputs2] + decoder_states)


def main() -> None:
    """主训练函数"""
    print("开始训练过程...")

    # 1. 加载数据
    print(f"从 {DATASET_PATH} 加载数据集...")
    problems, answers = load_dataset(DATASET_PATH)
    if problems is None or answers is None:
        return

    print(f"已加载 {len(problems)} 个样本。")

    # 2. 创建字符令牌映射并确定序列长度
    print("创建字符令牌映射...")
    char_to_token, token_to_char, n_token, max_encoder_seq_length, max_decoder_seq_length = \
        get_char_token_maps(problems, answers)

    # 保存字符映射以供后续推理使用
    char_map_data = {
        'char_to_token': char_to_token,
        'token_to_char': token_to_char,
        'n_token': n_token,
        'max_encoder_seq_length': max_encoder_seq_length,
        'max_decoder_seq_length': max_decoder_seq_length
    }
    with open(CHAR_MAP_SAVE_PATH, 'w', encoding='utf-8') as f:
        json.dump(char_map_data, f, indent=2)
    print(f"字符映射已保存到 {CHAR_MAP_SAVE_PATH}")
    print(f"唯一令牌数量: {n_token}")
    print(f"最大问题长度: {max_encoder_seq_length}")
    print(f"最大答案长度: {max_decoder_seq_length}")

    # 3. 准备模型数据
    print("准备模型数据...")
    encoder_input_data, decoder_input_data, decoder_target_data = \
        prepare_data(problems, answers, char_to_token, max_encoder_seq_length,
                    max_decoder_seq_length, n_token)

    print(f"编码器输入数据形状: {encoder_input_data.shape}")
    print(f"解码器输入数据形状: {decoder_input_data.shape}")
    print(f"解码器目标数据形状: {decoder_target_data.shape}")

    # 4. 构建和编译模型
    print("构建模型...")
    math_model = ArithmeticSeq2Seq(
        char_to_token=char_to_token,
        token_to_char=token_to_char,
        max_encoder_seq_length=max_encoder_seq_length,
        max_decoder_seq_length=max_decoder_seq_length,
        n_token=n_token,
        latent_dim=LATENT_DIM,
        embedding_dim=EMBEDDING_DIM
    )
    math_model.build_model()

    # 编译模型
    # 使用RMSprop，因为它通常对RNN效果好，也可以尝试Adam
    if KERAS_AVAILABLE:
        math_model.model.compile(
            optimizer='rmsprop',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        print("模型已编译。")

        # 5. 训练模型
        print("开始模型训练...")

        callbacks = [
            EarlyStopping(monitor='val_loss', patience=5, verbose=1, restore_best_weights=True),
            ModelCheckpoint(MODEL_SAVE_PATH, monitor='val_loss', save_best_only=True, verbose=1),
            ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=3, min_lr=0.00001, verbose=1)
        ]

        history = math_model.model.fit(
            [encoder_input_data, decoder_input_data],
            decoder_target_data,
            batch_size=BATCH_SIZE,
            epochs=EPOCHS,
            validation_split=VALIDATION_SPLIT,
            callbacks=callbacks,
            shuffle=True
        )

        print("训练完成。")
        print(f"训练模型已保存到 {MODEL_SAVE_PATH}")

        # 可选，绘制训练历史（需要matplotlib）
        # import matplotlib.pyplot as plt
        # plt.plot(history.history['loss'], label='Training Loss')
        # plt.plot(history.history['val_loss'], label='Validation Loss')
        # plt.title('Model Loss')
        # plt.ylabel('Loss')
        # plt.xlabel('Epoch')
        # plt.legend()
        # plt.savefig('training_loss_plot.png')
        # print("训练损失图已保存到 training_loss_plot.png")
    else:
        print("Keras不可用，跳过训练")


if __name__ == "__main__":
    # 确保数据存在，如果不存在，引导用户生成
    if tf is None or not tf.io.gfile.exists(DATASET_PATH):
        print(f"数据集未找到于 {DATASET_PATH}。")
        print("请先运行 `python src/tools/math_model/data_generator.py` 生成数据集。")
        print("注意：data_generator脚本目前设置为输出CSV。如果您将其更改为JSON，请更新train.py中的DATASET_PATH，")
        print("或者修改data_generator默认输出JSON用于训练。")
        print("请确保 `data_generator.py` 生成用于训练的JSON数据集（例如 arithmetic_train_dataset.json）。")
    else:
        main()
