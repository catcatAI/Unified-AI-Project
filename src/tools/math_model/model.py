import numpy as np
import json

# Global variables to hold TensorFlow components, loaded on demand.
tf = None
Model = None
Input = None
LSTM = None
Dense = None
Embedding = None

_tensorflow_is_available = False

def _ensure_tensorflow_is_imported():
    """
    Lazily imports TensorFlow and its Keras components.
    Returns True if successful, False otherwise.
    """
    global tf, Model, Input, LSTM, Dense, Embedding, _tensorflow_is_available
    if tf is None:
        try:
            # Hide the import from static analysis to avoid premature dependency checks
            _tf_module = __import__('tensorflow', fromlist=['keras'])
            
            tf = _tf_module
            Model = tf.keras.models.Model
            Input = tf.keras.layers.Input
            LSTM = tf.keras.layers.LSTM
            Dense = tf.keras.layers.Dense
            Embedding = tf.keras.layers.Embedding
            _tensorflow_is_available = True
            return True
        except ImportError as e:
            print(f"Warning: TensorFlow could not be imported. Math model functionality will be disabled. Error: {e}")
            _tensorflow_is_available = False
            return False
        except Exception as e:
            print(f"Warning: An unexpected error occurred during TensorFlow import. Math model functionality will be disabled. Error: {e}")
            _tensorflow_is_available = False
            return False
    return _tensorflow_is_available

# Attempt to import TensorFlow on module load
_ensure_tensorflow_is_imported()

class ArithmeticSeq2Seq:
    def __init__(self, char_to_token, token_to_char, max_encoder_seq_length, max_decoder_seq_length, n_token, latent_dim=256, embedding_dim=128):
        if not _tensorflow_is_available:
            print("ArithmeticSeq2Seq: TensorFlow not available. This instance will be non-functional.")
            self.char_to_token = char_to_token
            self.token_to_char = token_to_char
            self.max_encoder_seq_length = max_encoder_seq_length
            self.max_decoder_seq_length = max_decoder_seq_length
            self.n_token = n_token
            self.latent_dim = latent_dim
            self.embedding_dim = embedding_dim
            self.model = None
            self.encoder_model = None
            self.decoder_model = None
            return

        self.char_to_token = char_to_token
        self.token_to_char = token_to_char
        self.max_encoder_seq_length = max_encoder_seq_length
        self.max_decoder_seq_length = max_decoder_seq_length
        self.n_token = n_token
        self.latent_dim = latent_dim
        self.embedding_dim = embedding_dim

        self.model = None
        self.encoder_model = None
        self.decoder_model = None
        # Model is built on-demand when needed (e.g., during predict or load)
        # to avoid requiring TensorFlow at initialization.

    def _build_inference_models(self):
        """Builds the model structure for training and inference."""
        if not _tensorflow_is_available:
            print("Cannot build inference models: TensorFlow not available.")
            return
        _ensure_tensorflow_is_imported() # Lazy import of TensorFlow

        # Encoder
        encoder_inputs = Input(shape=(None,), name="encoder_inputs")
        encoder_embedding = Embedding(self.n_token, self.embedding_dim, name="encoder_embedding")(encoder_inputs)
        encoder_lstm_layer = LSTM(self.latent_dim, return_state=True, name="encoder_lstm")
        _, state_h, state_c = encoder_lstm_layer(encoder_embedding)
        encoder_states = [state_h, state_c]

        # Decoder
        decoder_inputs = Input(shape=(None,), name="decoder_inputs")
        decoder_embedding_layer_instance = Embedding(self.n_token, self.embedding_dim, name="decoder_embedding")
        decoder_embedding = decoder_embedding_layer_instance(decoder_inputs)
        decoder_lstm_layer = LSTM(self.latent_dim, return_sequences=True, return_state=True, name="decoder_lstm")
        decoder_outputs, _, _ = decoder_lstm_layer(decoder_embedding, initial_state=encoder_states)

        decoder_dense_layer = Dense(self.n_token, activation='softmax', name="decoder_dense")
        decoder_outputs = decoder_dense_layer(decoder_outputs)

        self.model = Model([encoder_inputs, decoder_inputs], decoder_outputs)

        # Inference models
        self.encoder_model = Model(encoder_inputs, encoder_states)

        decoder_state_input_h = Input(shape=(self.latent_dim,), name="decoder_state_input_h")
        decoder_state_input_c = Input(shape=(self.latent_dim,), name="decoder_state_input_c")
        decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]

        decoder_embedding_inf = decoder_embedding_layer_instance(decoder_inputs)

        decoder_outputs_inf, state_h_inf, state_c_inf = decoder_lstm_layer(
            decoder_embedding_inf, initial_state=decoder_states_inputs)
        decoder_states_inf = [state_h_inf, state_c_inf]
        decoder_outputs_inf = decoder_dense_layer(decoder_outputs_inf)

        self.decoder_model = Model(
            [decoder_inputs] + decoder_states_inputs,
            [decoder_outputs_inf] + decoder_states_inf
        )

    def _string_to_tokens(self, input_string, max_len, is_target=False):
        if not _tensorflow_is_available:
            print("Cannot convert string to tokens: TensorFlow not available.")
            return np.array([])
        tokens = np.zeros((1, max_len), dtype='float32')
        if is_target:
            processed_string = '\t' + input_string + '\n'
        else:
            processed_string = input_string

        for t, char in enumerate(processed_string):
            if t < max_len:
                if char in self.char_to_token:
                    tokens[0, t] = self.char_to_token[char]
                else:
                    tokens[0, t] = self.char_to_token.get('UNK', 0)
            else:
                break
        return tokens

    def predict_sequence(self, input_seq_str: str) -> str:
        if not _tensorflow_is_available or not self.encoder_model or not self.decoder_model:
            print("Cannot predict sequence: TensorFlow not available or models not built.")
            return "Error: Math model is not available."

        input_seq = self._string_to_tokens(input_seq_str, self.max_encoder_seq_length, is_target=False)
        if input_seq.size == 0: # Handle case where _string_to_tokens failed due to TF unavailability
            return "Error: Math model is not available."

        states_value = self.encoder_model.predict(input_seq, verbose=0)

        target_seq = np.zeros((1, 1))

        if '\t' not in self.char_to_token:
            # This should ideally be caught during char map generation/loading
            return "Error: Start token '\t' not found in char_to_token map."
        target_seq[0, 0] = self.char_to_token['\t']

        stop_condition = False
        decoded_sentence = ''

        for _ in range(self.max_decoder_seq_length + 1):
            output_tokens, h, c = self.decoder_model.predict([target_seq] + states_value, verbose=0)

            sampled_token_index = np.argmax(output_tokens[0, -1, :])
            sampled_char = self.token_to_char.get(str(sampled_token_index), 'UNK') # Ensure key is string for lookup

            if sampled_char == '\n' or sampled_char == 'UNK' or len(decoded_sentence) >= self.max_decoder_seq_length:
                stop_condition = True
                break

            decoded_sentence += sampled_char

            target_seq = np.zeros((1, 1))
            target_seq[0, 0] = sampled_token_index
            states_value = [h, c]

        return decoded_sentence

    @classmethod
    def load_for_inference(cls, model_weights_path, char_maps_path):
        """Loads a trained model and its character maps for inference."""
        if not _tensorflow_is_available:
            print("Cannot load model for inference: TensorFlow not available.")
            return None
        _ensure_tensorflow_is_imported() # Lazy import of TensorFlow
        try:
            with open(char_maps_path, 'r', encoding='utf-8') as f:
                char_map_data = json.load(f)

            char_to_token = char_map_data['char_to_token']
            # JSON saves all keys as strings, so convert token_to_char keys back to int for TF, then back to str for our use
            token_to_char = {str(k): v for k, v in char_map_data['token_to_char'].items()}
            n_token = char_map_data['n_token']
            max_encoder_seq_length = char_map_data['max_encoder_seq_length']
            max_decoder_seq_length = char_map_data['max_decoder_seq_length']
            latent_dim = char_map_data.get('latent_dim', 256)
            embedding_dim = char_map_data.get('embedding_dim', 128)

            instance = cls(char_to_token, token_to_char, max_encoder_seq_length,
                           max_decoder_seq_length, n_token, latent_dim, embedding_dim)

            instance._build_inference_models()
            instance.model.load_weights(model_weights_path)
            print(f"Model loaded successfully from {model_weights_path}")
            return instance

        except FileNotFoundError:
            print(f"Error: Model or char map file not found. Searched: {model_weights_path}, {char_maps_path}")
            return None
        except Exception as e:
            print(f"Error loading model for inference: {e}")
            return None


# --- Helper functions for preparing data (can be moved to a utils.py or train.py) ---
def get_char_token_maps(problems, answers):
    if not _tensorflow_is_available:
        print("Cannot get char maps: TensorFlow not available.")
        return {}, {}, 0, 0, 0
    input_texts = [p['problem'] for p in problems]
    target_texts = ['\t' + a['answer'] + '\n' for a in answers]

    all_chars = set()
    for text in input_texts:
        for char in text:
            all_chars.add(char)
    for text in target_texts:
        for char in text:
            all_chars.add(char)

    all_chars = sorted(list(all_chars))
    all_chars.append('UNK')

    char_to_token = dict([(char, i) for i, char in enumerate(all_chars)])
    token_to_char = dict([(i, char) for i, char in enumerate(all_chars)])
    n_token = len(all_chars)

    max_encoder_seq_length = max([len(txt) for txt in input_texts]) if input_texts else 0
    max_decoder_seq_length = max([len(txt) for txt in target_texts]) if target_texts else 0

    return char_to_token, token_to_char, n_token, max_encoder_seq_length, max_decoder_seq_length


def prepare_data(problems, answers, char_to_token, max_encoder_seq_length, max_decoder_seq_length, n_token):
    if not _tensorflow_is_available:
        print("Cannot prepare data: TensorFlow not available.")
        return np.array([]), np.array([]), np.array([])
    encoder_input_data = np.zeros(
        (len(problems), max_encoder_seq_length), dtype='float32')
    decoder_input_data = np.zeros(
        (len(problems), max_decoder_seq_length), dtype='float32')
    decoder_target_data = np.zeros(
        (len(problems), max_decoder_seq_length, n_token), dtype='float32')

    for i, (problem_item, answer_item) in enumerate(zip(problems, answers)):
        problem_str = problem_item['problem']
        answer_str = answer_item['answer']

        for t, char in enumerate(problem_str):
            if char in char_to_token:
                encoder_input_data[i, t] = char_to_token[char]
            else:
                encoder_input_data[i, t] = char_to_token['UNK']

        target_text_processed = '\t' + answer_str + '\n'
        for t, char in enumerate(target_text_processed):
            if char in char_to_token:
                decoder_input_data[i, t] = char_to_token[char]
                if t > 0:
                    decoder_target_data[i, t - 1, char_to_token[char]] = 1.
            else:
                decoder_input_data[i, t] = char_to_token['UNK']
                if t > 0:
                    decoder_target_data[i, t - 1, char_to_token['UNK']] = 1.

    return encoder_input_data, decoder_input_data, decoder_target_data


if __name__ == '__main__':
    print("--- ArithmeticSeq2Seq Model Structure Test ---")
    if _tensorflow_is_available:
        print("TensorFlow imported successfully.")

        dummy_problems = [{'problem': '1+1'}, {'problem': '10*2'}]
        dummy_answers = [{'answer': '2'}, {'answer': '20'}]

        char_map, token_map, n_tok, max_enc_len, max_dec_len = get_char_token_maps(dummy_problems, dummy_answers)

        print(f"Num tokens: {n_tok}")
        print(f"Max encoder sequence length: {max_enc_len}")
        print(f"Max decoder sequence length: {max_dec_len}")

        arith_model = ArithmeticSeq2Seq(char_map, token_map, max_enc_len, max_dec_len, n_tok)
        
        # The model is built lazily, so we call a method that triggers it.
        print("\nTesting prediction (on untrained model)...")
        test_problem = "5+5"
        predicted_answer = arith_model.predict_sequence(test_problem)
        print(f"Problem: {test_problem}")
        print(f"Predicted Answer: {predicted_answer}")

        print("\nModel.py basic structure test complete.")

    else:
        print("TensorFlow not available. Skipping model functionality tests.")