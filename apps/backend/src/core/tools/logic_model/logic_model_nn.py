import os
import json
import numpy as np
import sys
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Dict, List

# Add src directory to sys.path for dependency manager import
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# from ai.dependency_manager import dependency_manager
# from ai.compression.alpha_deep_model import DNADataChain

@dataclass
class LogicModelResult:
    """逻辑模型结果数据类"""
    input_proposition: str
    predicted_result: bool
    confidence: float
    processing_time: float
    timestamp: datetime
    dna_chain_id: Optional[str] = None

# Global variables to hold TensorFlow components, loaded on demand.
tf = None
Model = None
Input = None
Embedding = None
LSTM = None
Dense = None
Dropout = None
pad_sequences = None
to_categorical = None

def _ensure_tensorflow_is_imported():
    """
    Lazily imports TensorFlow and its Keras components using dependency manager.
    Catches a broader range of exceptions, including potential fatal errors on import.
    Returns True if successful, False otherwise.
    """
    global tf, Model, Input, Embedding, LSTM, Dense, Dropout, pad_sequences, to_categorical

    if tf is not None:
        return True

    # Check dependency manager first without triggering import
    if dependency_manager.is_available('tensorflow'):
        tf_module = dependency_manager.get_dependency('tensorflow')
        if tf_module:
            tf = tf_module
            # Populate globals if successful
            Model = getattr(tf.keras.models, 'Model', None)
            Input = getattr(tf.keras.layers, 'Input', None)
            Embedding = getattr(tf.keras.layers, 'Embedding', None)
            LSTM = getattr(tf.keras.layers, 'LSTM', None)
            Dense = getattr(tf.keras.layers, 'Dense', None)
            Dropout = getattr(tf.keras.layers, 'Dropout', None)
            pad_sequences = getattr(tf.keras.preprocessing.sequence, 'pad_sequences', None)
            to_categorical = getattr(tf.keras.utils, 'to_categorical', None)
            return True

    try:
        import tensorflow as tf_direct
        tf = tf_direct
        Model = tf.keras.models.Model
        Input = tf.keras.layers.Input
        Embedding = tf.keras.layers.Embedding
        LSTM = tf.keras.layers.LSTM
        Dense = tf.keras.layers.Dense
        Dropout = tf.keras.layers.Dropout
        pad_sequences = tf.keras.preprocessing.sequence.pad_sequences
        to_categorical = tf.keras.utils.to_categorical
        
        # Update dependency manager
        status = dependency_manager.get_status('tensorflow')
        if status:
            status.is_available = True
            status.module = tf
        return True
    except Exception as e:
        # Catch any exception during import, including fatal ones if possible.
        print(f"CRITICAL: Failed to import TensorFlow. Logic model NN functionality will be disabled. Error: {e}")
        status = dependency_manager.get_status('tensorflow')
        if status:
            status.is_available = False
            status.module = None
        # Set globals to None to ensure checks fail cleanly
        tf = None
        return False

def _tensorflow_is_available():
    """Check if TensorFlow is available without triggering an import."""
    # This function now relies on the lazy-loading mechanism.
    # It returns true only if _ensure_tensorflow_is_imported has been successfully called.
    return tf is not None

# DO NOT attempt to import TensorFlow on module load. It will be loaded lazily.
# _ensure_tensorflow_is_imported

# Define paths (relative to project root, assuming this script is in src/tools/logic_model)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
CHAR_MAP_SAVE_PATH = os.path.join(PROJECT_ROOT, "data/models/logic_model_char_maps.json")
MODEL_SAVE_PATH = os.path.join(PROJECT_ROOT, "data/models/logic_model_nn.keras")
TRAIN_DATA_PATH = os.path.join(PROJECT_ROOT, "data/raw_datasets/logic_train.json")

class LogicNNModel:
    def __init__(self, max_seq_len, vocab_size, embedding_dim=32, lstm_units=64) -> None:
        if not _ensure_tensorflow_is_imported:
            print("LogicNNModel: TensorFlow not available. This instance will be non-functional.")
            self.model = None
            self.dna_chains =   # DNA数据链存储
            self.prediction_history =   # 预测历史记录
            return
        self.max_seq_len = max_seq_len
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.lstm_units = lstm_units
        self.model = None # Build lazily
        self.dna_chains =   # DNA数据链存储
        self.prediction_history =   # 预测历史记录

    def _build_model(self):
        if not _tensorflow_is_available:
            print("Cannot build model: TensorFlow not available.")
            return
        input_layer = Input(shape=(self.max_seq_len,), name="input_proposition")
        embedding_layer = Embedding(input_dim=self.vocab_size,
                                    output_dim=self.embedding_dim,
                                    input_length=self.max_seq_len,
                                    name="embedding")(input_layer)
        lstm_layer = LSTM(self.lstm_units, name="lstm_layer")(embedding_layer)
        dropout_layer = Dropout(0.5, name="dropout")(lstm_layer)
        output_layer = Dense(2, activation='softmax', name="output_boolean")(dropout_layer)

        model = Model(inputs=input_layer, outputs=output_layer)
        model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        self.model = model

    def train(self, X_train, y_train, X_val, y_val, epochs=20, batch_size=32):
        if not _tensorflow_is_available or self.model is None:
            print("Cannot train model: TensorFlow not available or model not built.")
            return None
        print(f"Starting training: epochs={epochs}, batch_size={batch_size}")
        history = self.model.fit(X_train, y_train,
                                 epochs=epochs,
                                 batch_size=batch_size,
                                 validation_data=(X_val, y_val),
                                 verbose=1)
        print("Training complete.")
        return history

    def predict(self, proposition_str, char_to_token, dna_chain_id: Optional[str] = None):
        if not _tensorflow_is_available or self.model is None:
            print("Cannot predict: TensorFlow not available or model not built.")
            return False # Default/dummy return
        
        start_time = datetime.now
        
        tokens = [char_to_token.get(char, char_to_token.get('<UNK>', 0)) for char in proposition_str]
        padded_sequence = pad_sequences([tokens], maxlen=self.max_seq_len, padding='post', truncating='post')

        prediction = self.model.predict(padded_sequence, verbose=0)
        predicted_class = np.argmax(prediction, axis=1)[0]
        confidence = float(np.max(prediction, axis=1)[0])
        
        result_bool = bool(predicted_class)
        
        end_time = datetime.now
        processing_time = (end_time - start_time).total_seconds
        
        # Create result object
        result = LogicModelResult(
            input_proposition=proposition_str,
            predicted_result=result_bool,
            confidence=confidence,
            processing_time=processing_time,
            timestamp=end_time,
            dna_chain_id=dna_chain_id
        )
        
        # Add to prediction history
        self.prediction_history.append(result)
        
        # Add to DNA chain if provided
        if dna_chain_id:
            if dna_chain_id not in self.dna_chains:
                self.dna_chains[dna_chain_id] = DNADataChain(dna_chain_id)
            self.dna_chains[dna_chain_id].add_node(f"logic_prediction_{len(self.prediction_history)}")
        
        return result_bool

    def get_prediction_history(self) -> List[LogicModelResult]:
        """获取预测历史记录"""
        return self.prediction_history.copy

    def create_dna_chain(self, chain_id: str) -> DNADataChain:
        """创建新的DNA数据链"""
        if chain_id not in self.dna_chains:
            self.dna_chains[chain_id] = DNADataChain(chain_id)
        return self.dna_chains[chain_id]

    def get_dna_chain(self, chain_id: str) -> Optional[DNADataChain]:
        """获取DNA数据链"""
        return self.dna_chains.get(chain_id)

    def save_model(self, path):
        if not _tensorflow_is_available or self.model is None:
            print("Cannot save model: TensorFlow not available or model not built.")
            return
        self.model.save(path)
        print(f"Model saved to {path}")

    @classmethod
    def load_model(cls, model_path, char_maps_path):
        if not _ensure_tensorflow_is_imported:
            print("Cannot load model: TensorFlow not available.")
            return None
        with open(char_maps_path, 'r') as f:
            char_maps = json.load(f)

        loaded_model_tf = tf.keras.models.load_model(model_path)

        instance = cls(
            max_seq_len=char_maps['max_seq_len'],
            vocab_size=char_maps['vocab_size'],
            embedding_dim=loaded_model_tf.get_layer('embedding').output_dim,
            lstm_units=loaded_model_tf.get_layer('lstm_layer').units
        )
        instance.model = loaded_model_tf
        print(f"Model loaded from {model_path}")
        return instance

# --- Helper functions for data preparation ---
def get_logic_char_token_maps(dataset_path):
    if not _tensorflow_is_available:
        print("Cannot get char maps: TensorFlow not available.")
        return None, None, None, None
    propositions = 
    with open(dataset_path, 'r') as f:
        data = json.load(f)
        for item in data:
            propositions.append(item['proposition'])

    chars = set
    for prop in propositions:
        for char in prop:
            chars.add(char)

    final_vocab = ['<PAD>', '<UNK>'] + sorted(list(chars))
    final_vocab = sorted(list(set(final_vocab)), key=lambda x: (x != '<PAD>', x != '<UNK>', x))

    char_to_token = {char: i for i, char in enumerate(final_vocab)}
    token_to_char = {i: char for i, char in enumerate(final_vocab)}
    vocab_size = len(final_vocab)
    max_seq_len = max(len(prop) for prop in propositions) if propositions else 0
    
    return char_to_token, token_to_char, vocab_size, max_seq_len

def preprocess_logic_data(dataset_path, char_to_token, max_len, num_classes=2):
    """Preprocess logic data for training."""
    if not _tensorflow_is_available:
        print("Cannot preprocess data: TensorFlow not available.")
        return None, None
    
    propositions = 
    labels = 
    
    with open(dataset_path, 'r') as f:
        data = json.load(f)
        for item in data:
            propositions.append(item['proposition'])
            labels.append(item['answer'])
    
    # Convert propositions to sequences of tokens
    sequences = 
    for prop in propositions:
        tokens = [char_to_token.get(char, char_to_token.get('<UNK>', 0)) for char in prop]
        sequences.append(tokens)
    
    # Pad sequences
    X = pad_sequences(sequences, maxlen=max_len, padding='post', truncating='post')
    
    # Convert labels to categorical
    y = to_categorical(labels, num_classes=num_classes)
    
    return X, y