import os
import json
import numpy as np
import sys # Added for debugging sys.path

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
    Lazily imports TensorFlow and its Keras components.
    Raises ImportError if TensorFlow is not installed or fails to import.
    """
    global tf, Model, Input, Embedding, LSTM, Dense, Dropout, pad_sequences, to_categorical
    print("Current sys.path:", sys.path) # Added for debugging
    if tf is None:
        try:
            _tf_module = __import__('tensorflow', fromlist=['keras'])
            _keras_preprocessing = __import__('tensorflow.keras.preprocessing.sequence', fromlist=['pad_sequences'])
            _keras_utils = __import__('tensorflow.keras.utils', fromlist=['to_categorical'])

            tf = _tf_module
            Model = tf.keras.models.Model
            Input = tf.keras.layers.Input
            Embedding = tf.keras.layers.Embedding
            LSTM = tf.keras.layers.LSTM
            Dense = tf.keras.layers.Dense
            Dropout = tf.keras.layers.Dropout
            pad_sequences = _keras_preprocessing.pad_sequences
            to_categorical = _keras_utils.to_categorical
        except ImportError as e:
            raise ImportError(
                "TensorFlow is required for this functionality, but it could not be imported. "
                "Please ensure TensorFlow is installed correctly. Original error: " + str(e)
            ) from e

# Define paths (relative to project root, assuming this script is in src/tools/logic_model)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
CHAR_MAP_SAVE_PATH = os.path.join(PROJECT_ROOT, "data/models/logic_model_char_maps.json")
MODEL_SAVE_PATH = os.path.join(PROJECT_ROOT, "data/models/logic_model_nn.keras")
TRAIN_DATA_PATH = os.path.join(PROJECT_ROOT, "data/raw_datasets/logic_train.json")

class LogicNNModel:
    def __init__(self, max_seq_len, vocab_size, embedding_dim=32, lstm_units=64):
        self.max_seq_len = max_seq_len
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.lstm_units = lstm_units
        self.model = None # Build lazily

    def _build_model(self):
        _ensure_tensorflow_is_imported()
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
        if self.model is None:
            self._build_model()
        print(f"Starting training: epochs={epochs}, batch_size={batch_size}")
        history = self.model.fit(X_train, y_train,
                                 epochs=epochs,
                                 batch_size=batch_size,
                                 validation_data=(X_val, y_val),
                                 verbose=1)
        print("Training complete.")
        return history

    def predict(self, proposition_str, char_to_token):
        if self.model is None:
            self._build_model()
        _ensure_tensorflow_is_imported()
        tokens = [char_to_token.get(char, char_to_token.get('<UNK>', 0)) for char in proposition_str]
        padded_sequence = pad_sequences([tokens], maxlen=self.max_seq_len, padding='post', truncating='post')

        prediction = self.model.predict(padded_sequence, verbose=0)
        predicted_class = np.argmax(prediction, axis=1)[0]
        return bool(predicted_class)

    def save_model(self, path):
        if self.model is None:
            raise ValueError("Model has not been built or loaded. Cannot save.")
        self.model.save(path)
        print(f"Model saved to {path}")

    @classmethod
    def load_model(cls, model_path, char_maps_path):
        _ensure_tensorflow_is_imported()
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
    propositions = []
    with open(dataset_path, 'r') as f:
        data = json.load(f)
        for item in data:
            propositions.append(item['proposition'])

    chars = set()
    for prop in propositions:
        for char in prop:
            chars.add(char)

    final_vocab = ['<PAD>', '<UNK>'] + sorted(list(chars))
    final_vocab = sorted(list(set(final_vocab)), key=lambda x: (x != '<PAD>', x != '<UNK>', x))

    char_to_token = {char: i for i, char in enumerate(final_vocab)}
    token_to_char = {i: char for i, char in enumerate(final_vocab)}
    vocab_size = len(final_vocab)
    max_seq_len = max(len(prop) for prop in propositions) if propositions else 0

    maps_to_save = {
        'char_to_token': char_to_token,
        'token_to_char': token_to_char,
        'vocab_size': vocab_size,
        'max_seq_len': max_seq_len
    }
    with open(CHAR_MAP_SAVE_PATH, 'w') as f:
        json.dump(maps_to_save, f, indent=2)
    print(f"Logic char maps saved to {CHAR_MAP_SAVE_PATH}")

    return char_to_token, token_to_char, vocab_size, max_seq_len

def preprocess_logic_data(dataset_path, char_to_token, max_seq_len, num_classes=2):
    _ensure_tensorflow_is_imported()
    propositions = []
    answers = []
    with open(dataset_path, 'r') as f:
        data = json.load(f)
        for item in data:
            propositions.append(item['proposition'])
            answers.append(item['answer'])

    sequences = [[char_to_token.get(char, char_to_token.get('<UNK>',0)) for char in prop] for prop in propositions]
    X = pad_sequences(sequences, maxlen=max_seq_len, padding='post', truncating='post', value=char_to_token.get('<PAD>',0))
    y = np.array([1 if ans else 0 for ans in answers])
    y_categorical = to_categorical(y, num_classes=num_classes)

    return X, y_categorical

if __name__ == "__main__":
    print("Logic NN Model Script (for structure definition and basic tests)")
    try:
        _ensure_tensorflow_is_imported()
        print("TensorFlow imported successfully.")

        if not os.path.exists(TRAIN_DATA_PATH):
            print(f"Training data {TRAIN_DATA_PATH} not found. Generating dummy data for test.")
            dummy_train_data = [
                {"proposition": "true AND false", "answer": False},
                {"proposition": "NOT true", "answer": False},
                {"proposition": "(true OR false) AND true", "answer": True}
            ]
            os.makedirs(os.path.dirname(TRAIN_DATA_PATH), exist_ok=True)
            with open(TRAIN_DATA_PATH, 'w') as f:
                json.dump(dummy_train_data, f)

        c2t, t2c, v_size, max_len = get_logic_char_token_maps(TRAIN_DATA_PATH)
        print(f"Vocab size: {v_size}, Max seq len: {max_len}")

        X_dummy, y_dummy = preprocess_logic_data(TRAIN_DATA_PATH, c2t, max_len)
        print(f"X_dummy shape: {X_dummy.shape}, y_dummy shape: {y_dummy.shape}")

        logic_model = LogicNNModel(max_seq_len=max_len, vocab_size=v_size)
        logic_model._build_model()
        print("Model built.")

        test_prop = "true AND false"
        pred = logic_model.predict(test_prop, c2t)
        print(f"Prediction for '{test_prop}': {pred}")

        logic_model.save_model(MODEL_SAVE_PATH)
        loaded_logic_model = LogicNNModel.load_model(MODEL_SAVE_PATH, CHAR_MAP_SAVE_PATH)
        pred_loaded = loaded_logic_model.predict(test_prop, c2t)
        print(f"Prediction for '{test_prop}' from loaded model: {pred_loaded}")

        if "dummy_train_data" in locals() and os.path.exists(TRAIN_DATA_PATH):
             if json.load(open(TRAIN_DATA_PATH)) == dummy_train_data:
                os.remove(TRAIN_DATA_PATH)
                print(f"Removed dummy {TRAIN_DATA_PATH}")
        if os.path.exists(CHAR_MAP_SAVE_PATH):
             maps_content = json.load(open(CHAR_MAP_SAVE_PATH))
             if maps_content['max_seq_len'] <= 25 :
                os.remove(CHAR_MAP_SAVE_PATH)
                print(f"Removed dummy {CHAR_MAP_SAVE_PATH}")
        if os.path.exists(MODEL_SAVE_PATH):
            os.remove(MODEL_SAVE_PATH)
            print(f"Removed dummy {MODEL_SAVE_PATH}")

    except ImportError as e:
        print(f"Skipping model test: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during the test: {e}")

    print("logic_model_nn.py executed.")