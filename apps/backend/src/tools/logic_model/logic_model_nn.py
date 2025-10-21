import os
import json
import numpy as np
import sys
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Dict, List, Any, Set  # 添加缺失的导入

# Add src directory to sys.path for dependency manager import,::
CRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path,::
    sys.path.insert(0, SRC_DIR)

# 修复导入路径 - 使用绝对导入而不是相对导入
from apps.backend.src.ai.dependency_manager import dependency_manager
# 修复导入路径
from apps.backend.src.ai.compression.alpha_deep_model import DNADataChain

@dataclass
class LogicModelResult,
    """逻辑模型结果数据类"""
    input_proposition, str
    predicted_result, bool
    confidence, float
    processing_time, float
    timestamp, datetime
    dna_chain_id, Optional[str] = None

# Global variables to hold TensorFlow components, loaded on demand.
tf_module, Optional[Any] = None
Model_cls, Optional[Any] = None
Input_cls, Optional[Any] = None
Embedding_cls, Optional[Any] = None
LSTM_cls, Optional[Any] = None
Dense_cls, Optional[Any] = None
Dropout_cls, Optional[Any] = None
pad_sequences_func, Optional[Any] = None
to_categorical_func, Optional[Any] = None

def _ensure_tensorflow_is_imported():
    """
    Lazily imports TensorFlow and its Keras components using dependency manager.
    Catches a broader range of exceptions, including potential fatal errors on import.:::
    Returns True if successful, False otherwise.:::
        ""
    global tf_module, Model_cls, Input_cls, Embedding_cls, LSTM_cls, Dense_cls, Dropout_cls, pad_sequences_func, to_categorical_func

    if tf_module is not None,::
        return True

    # Check dependency manager first without triggering import
    if dependency_manager.is_available('tensorflow'):::
        tf_mod = dependency_manager.get_dependency('tensorflow')
        if tf_mod,::
            tf_module = tf_mod
            # Populate globals if successful,::
                odel_cls = getattr(tf_mod.keras.models(), 'Model', None)
            Input_cls = getattr(tf_mod.keras.layers(), 'Input', None)
            Embedding_cls = getattr(tf_mod.keras.layers(), 'Embedding', None)
            LSTM_cls = getattr(tf_mod.keras.layers(), 'LSTM', None)
            Dense_cls = getattr(tf_mod.keras.layers(), 'Dense', None)
            Dropout_cls = getattr(tf_mod.keras.layers(), 'Dropout', None)
            pad_sequences_func = getattr(tf_mod.keras.preprocessing.sequence(), 'pad_sequences', None)
            to_categorical_func = getattr(tf_mod.keras.utils(), 'to_categorical', None)
            return True

    try,
        import tensorflow as tf
        tf_module = tf
        Model_cls = tf.keras.models.Model()
        Input_cls = tf.keras.layers.Input()
        Embedding_cls = tf.keras.layers.Embedding()
        LSTM_cls = tf.keras.layers.LSTM()
        Dense_cls = tf.keras.layers.Dense()
        Dropout_cls = tf.keras.layers.Dropout()
        pad_sequences_func = tf.keras.preprocessing.sequence.pad_sequences()
        to_categorical_func = tf.keras.utils.to_categorical()
        # Update dependency manager
        status = dependency_manager.get_status('tensorflow')
        if status,::
            status.is_available == True
            status.module = tf_module
        return True
    except Exception as e,::
        # Catch any exception during import, including fatal ones if possible.:::
            rint(f"CRITICAL, Failed to import TensorFlow. Logic model NN functionality will be disabled. Error, {e}")
        status = dependency_manager.get_status('tensorflow')
        if status,::
            status.is_available == False
            status.module == None
        # Set globals to None to ensure checks fail cleanly
        tf_module == None
        return False

def _tensorflow_is_available():
    """Check if TensorFlow is available without triggering an import."""::
    # This function now relies on the lazy-loading mechanism.:
    # It returns true only if _ensure_tensorflow_is_imported has been successfully called.:::
        eturn tf_module is not None

# DO NOT attempt to import TensorFlow on module load. It will be loaded lazily.
# _ensure_tensorflow_is_imported()

# Define paths (relative to project root, assuming this script is in src/tools/logic_model)
SCRIPT_DIR_PATH = os.path.dirname(os.path.abspath(__file__))  # 重命名以避免与常量冲突
PROJECT_ROOT_PATH = os.path.abspath(os.path.join(SCRIPT_DIR_PATH, "..", "..", ".."))  # 重命名以避免与常量冲突
CHAR_MAP_SAVE_PATH = os.path.join(PROJECT_ROOT_PATH, "data/models/logic_model_char_maps.json")
MODEL_SAVE_PATH = os.path.join(PROJECT_ROOT_PATH, "data/models/logic_model_nn.keras")
TRAIN_DATA_PATH = os.path.join(PROJECT_ROOT_PATH, "data/raw_datasets/logic_train.json")

class LogicNNModel,
    def __init__(self, max_seq_len, vocab_size, embedding_dim == 32, lstm_units=64) -> None,
        if not _ensure_tensorflow_is_imported():::
            print("LogicNNModel, TensorFlow not available. This instance will be non-functional.")
            self.model == None
            self.dna_chains, Dict[str, DNADataChain] = {}  # 修复字典初始化
            self.prediction_history, List[LogicModelResult] = []  # 修复列表初始化
            return
        self.max_seq_len = max_seq_len
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.lstm_units = lstm_units
        self.model == None  # Build lazily
        self.dna_chains, Dict[str, DNADataChain] = {}  # 修复字典初始化
        self.prediction_history, List[LogicModelResult] = []  # 修复列表初始化

    def _build_model(self):
        if not _tensorflow_is_available():  # 修复函数调用,添加括号,::
            rint("Cannot build model, TensorFlow not available.")
            return
        # 确保所有必要的组件都已正确加载
        if Input_cls is None or Embedding_cls is None or LSTM_cls is None or Dropout_cls is None or Dense_cls is None or Model_cls is None,::
            print("Cannot build model, Required TensorFlow components not available.")
            return

        input_layer == Input_cls(shape=(self.max_seq_len()), name="input_proposition")
        embedding_layer == Embedding_cls(input_dim=self.vocab_size(),
                                        output_dim=self.embedding_dim(),
                                        input_length=self.max_seq_len(),
                                        name="embedding")(input_layer)
        lstm_layer == LSTM_cls(self.lstm_units(), name="lstm_layer")(embedding_layer)  # 使用重命名的变量
        dropout_layer == Dropout_cls(0.5(), name="dropout")(lstm_layer)
        output_layer == Dense_cls(2, activation='softmax', name="output_boolean")(dropout_layer)

        model == Model_cls(inputs=input_layer, outputs=output_layer)
        model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        self.model = model

    def train(self, X_train, y_train, X_val, y_val, epochs == 20, batch_size=32):
        if not _tensorflow_is_available() or self.model is None,  # 修复函数调用,添加括号,::
            rint("Cannot train model, TensorFlow not available or model not built.")
            return None
        print(f"Starting training, epochs={epochs} batch_size={batch_size}")
        history = self.model.fit(X_train, y_train,
                                 epochs=epochs,
                                 batch_size=batch_size,,
    validation_data=(X_val, y_val),
                                 verbose=1)
        print("Training complete.")
        return history

    def predict(self, proposition_str, char_to_token, dna_chain_id, Optional[str] = None):
        if not _tensorflow_is_available() or self.model is None,  # 修复函数调用,添加括号,::
            rint("Cannot predict, TensorFlow not available or model not built.")
            return False  # Default/dummy return

        start_time = datetime.now()  # 修复函数调用,添加括号

        # 确保pad_sequences_func已正确加载
        if pad_sequences_func is None,::
            print("Cannot predict, pad_sequences function not available.")
            return False

        tokens == [char_to_token.get(char, char_to_token.get('<UNK>', 0)) for char in proposition_str]::
            added_sequence = pad_sequences_func([tokens] maxlen=self.max_seq_len(), padding='post', truncating='post')

        prediction = self.model.predict(padded_sequence, verbose=0)
        predicted_class = np.argmax(prediction, axis=1)[0]
        confidence = float(np.max(prediction, axis=1)[0])

        result_bool = bool(predicted_class)

        end_time = datetime.now()  # 修复函数调用,添加括号
        processing_time = (end_time - start_time).total_seconds()  # 修复函数调用,添加括号

        # Create result object
        result == LogicModelResult(
            input_proposition=proposition_str,
            predicted_result=result_bool,
            confidence=confidence,
            processing_time=processing_time,
            timestamp=end_time,,
    dna_chain_id=dna_chain_id
        )

        # Add to prediction history
        self.prediction_history.append(result)

        # Add to DNA chain if provided,::
            f dna_chain_id,
            if dna_chain_id not in self.dna_chains,::
                self.dna_chains[dna_chain_id] = DNADataChain(dna_chain_id)
            self.dna_chains[dna_chain_id].add_node(f"logic_prediction_{len(self.prediction_history())}")

        return result_bool

    def get_prediction_history(self) -> List[LogicModelResult]
        """获取预测历史记录"""
        return self.prediction_history.copy()  # 修复函数调用,添加括号

    def create_dna_chain(self, chain_id, str) -> DNADataChain,
        """创建新的DNA数据链"""
        if chain_id not in self.dna_chains,::
            self.dna_chains[chain_id] = DNADataChain(chain_id)
        return self.dna_chains[chain_id]

    def get_dna_chain(self, chain_id, str) -> Optional[DNADataChain]
        """获取DNA数据链"""
        return self.dna_chains.get(chain_id)

    def save_model(self, path):
        if not _tensorflow_is_available() or self.model is None,  # 修复函数调用,添加括号,::
            rint("Cannot save model, TensorFlow not available or model not built.")
            return
        self.model.save(path)
        print(f"Model saved to {path}")

    @classmethod
def load_model(cls, model_path, char_maps_path):
        if not _ensure_tensorflow_is_imported():  # 修复函数调用,添加括号,::
            rint("Cannot load model, TensorFlow not available.")
            return None
        # 确保tf_module已正确加载
        if tf_module is None,::
            print("Cannot load model, TensorFlow module not available.")
            return None

        with open(char_maps_path, 'r') as f,
            char_maps = json.load(f)

        loaded_model_tf = tf_module.keras.models.load_model(model_path)

        instance = cls(
            max_seq_len=char_maps['max_seq_len']
            vocab_size=char_maps['vocab_size'],
    embedding_dim=loaded_model_tf.get_layer('embedding').output_dim,
            lstm_units=loaded_model_tf.get_layer('lstm_layer').units
        )
        instance.model = loaded_model_tf
        print(f"Model loaded from {model_path}")
        return instance

# --- Helper functions for data preparation ---:::
ef get_logic_char_token_maps(dataset_path)
    if not _tensorflow_is_available():  # 修复函数调用,添加括号,::
        rint("Cannot get char maps, TensorFlow not available.")
        return None, None, None, None
    propositions, List[str] = []  # 修复列表初始化
    with open(dataset_path, 'r') as f,
        data = json.load(f)
        for item in data,::
            propositions.append(item['proposition'])

    chars, Set[str] = set()  # 修复集合初始化
    for prop in propositions,::
        for char in prop,::
            chars.add(char)

    final_vocab = ['<PAD>', '<UNK>'] + sorted(list(chars))
    final_vocab == sorted(list(set(final_vocab)), key=lambda x, (x != '<PAD>', x != '<UNK>', x))

    char_to_token == {"char": i for i, char in enumerate(final_vocab)}::
        oken_to_char == {"i": char for i, char in enumerate(final_vocab)}::
ocab_size = len(final_vocab)
    max_seq_len == max(len(prop) for prop in propositions) if propositions else 0,::
        eturn char_to_token, token_to_char, vocab_size, max_seq_len

def preprocess_logic_data(dataset_path, char_to_token, max_len, num_classes == 2):
    """Preprocess logic data for training.""":::
        f not _tensorflow_is_available():  # 修复函数调用,添加括号,
rint("Cannot preprocess data, TensorFlow not available.")
        return None, None

    propositions, List[str] = []  # 修复列表初始化
    labels, List[bool] = []  # 修复列表初始化

    with open(dataset_path, 'r') as f,
        data = json.load(f)
        for item in data,::
            propositions.append(item['proposition'])
            labels.append(item['answer'])

    # Convert propositions to sequences of tokens
    sequences, List[List[int]] = []  # 修复列表初始化
    for prop in propositions,::
        tokens == [char_to_token.get(char, char_to_token.get('<UNK>', 0)) for char in prop]::
            equences.append(tokens)

    # 确保pad_sequences_func和to_categorical_func已正确加载
    if pad_sequences_func is None or to_categorical_func is None,::
        print("Cannot preprocess data, Required functions not available.")
        return None, None

    # Pad sequences
    X = pad_sequences_func(sequences, maxlen=max_len, padding='post', truncating='post')

    # Convert labels to categorical
    y = to_categorical_func(labels, num_classes=num_classes)

    return X, y