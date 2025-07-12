import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Embedding, LSTM, Dense, Dropout
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.utils import to_categorical

# Define paths (relative to project root, assuming this script is in src/tools/logic_model)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
CHAR_MAP_SAVE_PATH = os.path.join(PROJECT_ROOT, "data/models/logic_model_char_maps.json")
MODEL_SAVE_PATH = os.path.join(PROJECT_ROOT, "data/models/logic_model_nn.keras")
TRAIN_DATA_PATH = os.path.join(PROJECT_ROOT, "data/raw_datasets/logic_train.json")

# --- Vocabulary and Tokenization ---
# Define a fixed vocabulary for logical propositions
VOCAB = ['(', ')', 'A', 'N', 'D', 'O', 'R', 'T', 'F', 'L', 'S', 'E', 'U', ' ', 'N O T'] # Added 'N O T' for 'NOT '
# 'T R U E' -> T, R, U, E ; 'F A L S E' -> F, A, L, S, E
# Special tokens: PAD, START, END (optional, depends on seq2seq vs classifier)
# For a classifier, we might not need START/END if we pad and treat as fixed-length sequence.

# Simpler approach: tokenize characters.
# The get_logic_char_token_maps will generate this dynamically from data.

class LogicNNModel:
    def __init__(self, max_seq_len, vocab_size, embedding_dim=32, lstm_units=64):
        self.max_seq_len = max_seq_len
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.lstm_units = lstm_units
        self.model = self._build_model()

    def _build_model(self):
        input_layer = Input(shape=(self.max_seq_len,), name="input_proposition")
        embedding_layer = Embedding(input_dim=self.vocab_size,
                                    output_dim=self.embedding_dim,
                                    input_length=self.max_seq_len,
                                    name="embedding")(input_layer)
        lstm_layer = LSTM(self.lstm_units, name="lstm_layer")(embedding_layer)
        dropout_layer = Dropout(0.5, name="dropout")(lstm_layer) # Added dropout
        # Output layer: 2 units for True/False, or 1 unit with sigmoid for binary classification
        output_layer = Dense(2, activation='softmax', name="output_boolean")(dropout_layer)

        model = Model(inputs=input_layer, outputs=output_layer)
        model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        model.summary()
        return model

    def train(self, X_train, y_train, X_val, y_val, epochs=20, batch_size=32):
        # Placeholder for actual training callbacks
        print(f"Starting training: epochs={epochs}, batch_size={batch_size}")
        history = self.model.fit(X_train, y_train,
                                 epochs=epochs,
                                 batch_size=batch_size,
                                 validation_data=(X_val, y_val),
                                 verbose=1)
        print("Training complete.")
        return history

    def predict(self, proposition_str, char_to_token):
        # Preprocess the input string
        tokens = [char_to_token.get(char, char_to_token.get('<UNK>', 0)) for char in proposition_str]
        padded_sequence = pad_sequences([tokens], maxlen=self.max_seq_len, padding='post', truncating='post')

        prediction = self.model.predict(padded_sequence, verbose=0)
        predicted_class = np.argmax(prediction, axis=1)[0] # 0 for False, 1 for True (if classes are [F,T])
        return bool(predicted_class) # Convert to Python boolean

    def save_model(self, path):
        self.model.save(path)
        print(f"Model saved to {path}")

    @classmethod
    def load_model(cls, model_path, char_maps_path):
        # Load char maps to get max_seq_len and vocab_size
        with open(char_maps_path, 'r') as f:
            char_maps = json.load(f)

        loaded_model_tf = tf.keras.models.load_model(model_path)

        # Create an instance of LogicNNModel and assign the loaded tf.keras.Model
        # This is a bit of a workaround as we need the class structure.
        # A better way might be to save/load the config of the LogicNNModel instance.
        instance = cls(
            max_seq_len=char_maps['max_seq_len'],
            vocab_size=char_maps['vocab_size'],
            # embedding_dim and lstm_units should ideally be saved in char_maps or model config
            embedding_dim=loaded_model_tf.get_layer('embedding').output_dim,
            lstm_units=loaded_model_tf.get_layer('lstm_layer').units
        )
        instance.model = loaded_model_tf
        print(f"Model loaded from {model_path}")
        return instance

# --- Helper functions for data preparation ---
def get_logic_char_token_maps(dataset_path):
    """Reads dataset, creates and returns character maps and max_seq_len."""
    propositions = []
    with open(dataset_path, 'r') as f:
        data = json.load(f)
        for item in data:
            propositions.append(item['proposition'])

    chars = set()
    for prop in propositions:
        for char in prop:
            chars.add(char)

    sorted_chars = sorted(list(chars))
    # Add PAD and UNK tokens if not present, common practice
    # For this simple model, let's assume vocab is derived purely from data for now.
    # A more robust approach would define a fixed vocab including special tokens.
    # For simplicity, let's add a PAD token (0) and UNK token (1) if not covered.

    final_vocab = ['<PAD>', '<UNK>'] + sorted_chars # Ensure PAD is 0, UNK is 1
    # Remove duplicates if any char was already '<PAD>' or '<UNK>'
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
    """Loads, tokenizes, and pads data for the logic NN model."""
    propositions = []
    answers = []
    with open(dataset_path, 'r') as f:
        data = json.load(f)
        for item in data:
            propositions.append(item['proposition'])
            answers.append(item['answer']) # Expecting True/False booleans

    # Tokenize propositions
    sequences = [[char_to_token.get(char, char_to_token.get('<UNK>',0)) for char in prop] for prop in propositions]

    # Pad sequences
    X = pad_sequences(sequences, maxlen=max_seq_len, padding='post', truncating='post', value=char_to_token.get('<PAD>',0))

    # Convert answers to categorical (0 for False, 1 for True)
    y = np.array([1 if ans else 0 for ans in answers])
    y_categorical = to_categorical(y, num_classes=num_classes)

    return X, y_categorical

if __name__ == "__main__":
    print("Logic NN Model Script (for structure definition and basic tests)")

    # 1. Ensure data exists (or generate dummy for structural test)
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

    # 2. Get char maps
    try:
        c2t, t2c, v_size, max_len = get_logic_char_token_maps(TRAIN_DATA_PATH)
        print(f"Vocab size: {v_size}, Max seq len: {max_len}")

        # 3. Preprocess data (dummy version)
        X_dummy, y_dummy = preprocess_logic_data(TRAIN_DATA_PATH, c2t, max_len)
        print(f"X_dummy shape: {X_dummy.shape}, y_dummy shape: {y_dummy.shape}")

        # 4. Build model
        logic_model = LogicNNModel(max_seq_len=max_len, vocab_size=v_size)
        print("Model built.")

        # 5. Test prediction (on untrained model)
        test_prop = "true AND false"
        pred = logic_model.predict(test_prop, c2t)
        print(f"Prediction for '{test_prop}': {pred}") # Will be random

        # 6. Test save/load
        logic_model.save_model(MODEL_SAVE_PATH)
        loaded_logic_model = LogicNNModel.load_model(MODEL_SAVE_PATH, CHAR_MAP_SAVE_PATH)
        pred_loaded = loaded_logic_model.predict(test_prop, c2t)
        print(f"Prediction for '{test_prop}' from loaded model: {pred_loaded}")

        # Clean up dummy files created by this test
        if "dummy_train_data" in locals() and os.path.exists(TRAIN_DATA_PATH): # if dummy was created
             if json.load(open(TRAIN_DATA_PATH)) == dummy_train_data: # check if it's the dummy
                os.remove(TRAIN_DATA_PATH)
                print(f"Removed dummy {TRAIN_DATA_PATH}")
        if os.path.exists(CHAR_MAP_SAVE_PATH):
             # A bit risky if a real one was there, but for testing this is fine
             # Check if it was created based on dummy data
             maps_content = json.load(open(CHAR_MAP_SAVE_PATH))
             if maps_content['max_seq_len'] <= 25 : # Assuming dummy max_len is small
                os.remove(CHAR_MAP_SAVE_PATH)
                print(f"Removed dummy {CHAR_MAP_SAVE_PATH}")
        if os.path.exists(MODEL_SAVE_PATH):
            os.remove(MODEL_SAVE_PATH) # Remove dummy model
            print(f"Removed dummy {MODEL_SAVE_PATH}")


    except Exception as e:
        print(f"Error in __main__ block: {e}")

    print("logic_model_nn.py executed.")
