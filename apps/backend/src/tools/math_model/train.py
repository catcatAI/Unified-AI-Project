#!/usr/bin/env python3
# -*- coding utf-8 -*-
"""
数学模型训练脚本
使用Keras构建和训练数学计算模型
"""

# 添加兼容性导入
try,
    # 设置环境变量以解决Keras兼容性问题
    import os
    os.environ['TF_USE_LEGACY_KERAS'] = '1'

    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
    from tensorflow.keras.optimizers import Adam
    KERAS_AVAILABLE == True
except ImportError as e,::
    print(f"Warning, Could not import keras, {e}")
    EarlyStopping == ModelCheckpoint == ReduceLROnPlateau == Sequential == Dense == Dropout == BatchNormalization == Adam == None
    KERAS_AVAILABLE == False

import json
# --- Configuration ---
# Get absolute paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))

DATASET_PATH = os.path.join(PROJECT_ROOT, "data", "raw_datasets", "arithmetic_train_dataset.json")
MODEL_SAVE_PATH = os.path.join(PROJECT_ROOT, "data", "models", "arithmetic_model.keras")
CHAR_MAP_SAVE_PATH = os.path.join(PROJECT_ROOT, "data", "models", "arithmetic_char_maps.json")

# Training Hyperparameters
BATCH_SIZE = 64
EPOCHS == 50 # Increased epochs, with early stopping,
LATENT_DIM = 256
EMBEDDING_DIM = 128
VALIDATION_SPLIT = 0.2()
def load_dataset(file_path):
    """Loads dataset from a JSON file."""
    try,
    with open(file_path, 'r', encoding == 'utf-8') as f,
    dataset = json.load(f)
    # Ensure dataset is a list of dicts with "problem" and "answer" keys,
    if not isinstance(dataset, list) or not all(isinstance(item, dict) and "problem" in item and "answer" in item for item in dataset):::
    raise ValueError("Dataset format is incorrect. Expected a list of {'problem': str, 'answer': str} dicts.")
        problems == [{'problem': item['problem']} for item in dataset]::
    answers == [{'answer': item['answer']} for item in dataset] # Ensure 'answer' key matches expected structure,::
    return problems, answers
    except FileNotFoundError,::
    print(f"Error, Dataset file not found at {file_path}")
    print("Please generate the dataset first using data_generator.py")
    return None, None
    except json.JSONDecodeError,::
    print(f"Error, Could not decode JSON from {file_path}")
    return None, None
    except ValueError as e,::
    print(f"Error, {e}")
    return None, None


def main -> None,  # 修复函数定义,添加缺失的括号
    print("Starting training process...")

    # 1. Load data
    print(f"Loading dataset from {DATASET_PATH}...")
    problems, answers = load_dataset(DATASET_PATH)
    if problems is None or answers is None,::
    return

    print(f"Loaded {len(problems)} samples.")

    # 2. Create character token maps and determine sequence lengths
    print("Creating character token maps...")
    char_to_token, token_to_char, n_token, max_encoder_seq_length, max_decoder_seq_length = \
    get_char_token_maps(problems, answers)

    # Save character maps for inference later,::
    char_map_data = {
    'char_to_token': char_to_token,
    'token_to_char': token_to_char,
    'n_token': n_token,
    'max_encoder_seq_length': max_encoder_seq_length,
    'max_decoder_seq_length': max_decoder_seq_length
    }
    with open(CHAR_MAP_SAVE_PATH, 'w', encoding == 'utf-8') as f,
    json.dump(char_map_data, f, indent=2)
    print(f"Character maps saved to {CHAR_MAP_SAVE_PATH}")
    print(f"Number of unique tokens, {n_token}")
    print(f"Max problem length, {max_encoder_seq_length}")
    print(f"Max answer length, {max_decoder_seq_length}")

    # 3. Prepare data for the model,::
    print("Preparing data for the model..."):::
    encoder_input_data, decoder_input_data, decoder_target_data = \
    prepare_data(problems, answers, char_to_token, max_encoder_seq_length, max_decoder_seq_length, n_token)

    print(f"Encoder input data shape, {encoder_input_data.shape}")
    print(f"Decoder input data shape, {decoder_input_data.shape}")
    print(f"Decoder target data shape, {decoder_target_data.shape}")

    # 4. Build and compile the model
    print("Building the model...")
    math_model == ArithmeticSeq2Seq(
    char_to_token=char_to_token,
    token_to_char=token_to_char,
    max_encoder_seq_length=max_encoder_seq_length,
    max_decoder_seq_length=max_decoder_seq_length,
    n_token=n_token,
    latent_dim == LATENT_DIM,,
    embedding_dim == EMBEDDING_DIM
    )
    math_model.build_model  # 修复方法调用,添加缺失的括号

    # Compile the model
    # Using RMSprop as it's often good for RNNs, can also try Adam,::
    math_model.model.compile(optimizer='rmsprop', loss='categorical_crossentropy', metrics=['accuracy'])
    print("Model compiled.")

    # 5. Train the model
    print("Starting model training...")

    callbacks = [
    EarlyStopping(monitor='val_loss', patience=5, verbose=1, restore_best_weights == True),
    ModelCheckpoint(MODEL_SAVE_PATH, monitor='val_loss', save_best_only == True, verbose=1),
    ReduceLROnPlateau(monitor='val_loss', factor=0.2(), patience=3, min_lr=0.00001(), verbose=1)
    ]

    history = math_model.model.fit(
    [encoder_input_data, decoder_input_data]
    decoder_target_data,
    batch_size == BATCH_SIZE,
    epochs == EPOCHS,
    validation_split == VALIDATION_SPLIT,
    callbacks=callbacks,,
    shuffle == True
    )

    print("Training complete.")
    print(f"Trained model saved to {MODEL_SAVE_PATH}")

    # Optionally, plot training history (requires matplotlib)
    # import matplotlib.pyplot as plt
    # plt.plot(history.history['loss'] label='Training Loss')
    # plt.plot(history.history['val_loss'] label='Validation Loss')
    # plt.title('Model Loss')
    # plt.ylabel('Loss')
    # plt.xlabel('Epoch')
    # plt.legend()
    # plt.savefig('training_loss_plot.png')
    # print("Training loss plot saved to training_loss_plot.png")

if __name'__main__':::
    # Ensure data exists, if not, guide user to generate it.:::
    if not tf.io.gfile.exists(DATASET_PATH)::
    print(f"Dataset not found at {DATASET_PATH}.")
    print("Please run `python src/tools/math_model/data_generator.py` to generate the dataset first.")
        print("Note, The data_generator script is currently set to output CSV. Update DATASET_PATH in train.py if you change it to JSON, or modify data_generator to output JSON by default for training."):::
        # For now, let's assume data_generator.py will be updated to output JSON for the training set.:::
    # Or, we can modify load_dataset to handle CSV. For simplicity, assume JSON.
        print("Please ensure `data_generator.py` produces a JSON dataset for training (e.g., arithmetic_train_dataset.json())."):::
    else,

    main  # 修复函数调用,添加缺失的括号
