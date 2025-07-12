import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, LSTM, Dense, Embedding
import json # Added for loading char_maps

class ArithmeticSeq2Seq:
    def __init__(self, char_to_token, token_to_char, max_encoder_seq_length, max_decoder_seq_length, n_token, latent_dim=256, embedding_dim=128):
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
        # Call build_model if parameters are sufficient, or it can be called separately
        if self.n_token > 0: # A basic check
             self._build_inference_models() # Renamed and made private convention

    def _build_inference_models(self):
        # This method sets up the model structure for training AND inference
        # Encoder
        encoder_inputs = Input(shape=(None,), name="encoder_inputs")
        encoder_embedding = Embedding(self.n_token, self.embedding_dim, name="encoder_embedding")(encoder_inputs)
        # Using name 'encoder_lstm_layer' for the layer itself to avoid conflict if self.encoder_lstm is an attribute
        encoder_lstm_layer = LSTM(self.latent_dim, return_state=True, name="encoder_lstm")
        _, state_h, state_c = encoder_lstm_layer(encoder_embedding)
        encoder_states = [state_h, state_c]

        # Decoder
        decoder_inputs = Input(shape=(None,), name="decoder_inputs")
        # Using name 'decoder_embedding_layer' for the layer itself
        decoder_embedding_layer_instance = Embedding(self.n_token, self.embedding_dim, name="decoder_embedding")
        decoder_embedding = decoder_embedding_layer_instance(decoder_inputs)
        # Using name 'decoder_lstm_layer'
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
        # print("Model structure (training and inference) built.")
        # self.model.summary() # Optional: print summary during build

    def _string_to_tokens(self, input_string, max_len, is_target=False): # Made private by convention
        tokens = np.zeros((1, max_len), dtype='float32')
        if is_target:
            processed_string = '\t' + input_string + '\n'
        else:
            processed_string = input_string

        for t, char in enumerate(processed_string):
            if t < max_len: # Ensure we don't go out of bounds for tokens array
                if char in self.char_to_token:
                    tokens[0, t] = self.char_to_token[char]
                else:
                    tokens[0, t] = self.char_to_token.get('UNK', 0) # Default to 0 if UNK also not found
            else:
                break
        return tokens

    def predict_sequence(self, input_seq_str: str) -> str:
        if not self.encoder_model or not self.decoder_model:
            # Attempt to build if not already built (e.g. when loaded from saved weights)
            if self.n_token > 0:
                self._build_inference_models()
                if not self.encoder_model or not self.decoder_model:
                     raise ValueError("Inference models are not built and could not be auto-built.")
            else:
                raise ValueError("Inference models are not built. Call build_model() or load_model_for_inference() first.")

        input_seq = self._string_to_tokens(input_seq_str, self.max_encoder_seq_length, is_target=False)
        states_value = self.encoder_model.predict(input_seq, verbose=0)

        target_seq = np.zeros((1, 1))

        if '\t' not in self.char_to_token:
            raise ValueError("Start token '\\t' not found in char_to_token map.")
        target_seq[0, 0] = self.char_to_token['\t']

        stop_condition = False
        decoded_sentence = ''

        for _ in range(self.max_decoder_seq_length + 1): # Max iterations to prevent infinite loop
            output_tokens, h, c = self.decoder_model.predict([target_seq] + states_value, verbose=0)

            sampled_token_index = np.argmax(output_tokens[0, -1, :])
            sampled_char = self.token_to_char.get(sampled_token_index, 'UNK')

            if sampled_char == '\n' or sampled_char == 'UNK' or len(decoded_sentence) >= self.max_decoder_seq_length:
                stop_condition = True
                break

            decoded_sentence += sampled_char

            target_seq = np.zeros((1, 1))
            target_seq[0, 0] = sampled_token_index
            states_value = [h, c]

        return decoded_sentence

    @classmethod
    def load_for_inference(cls, model_weights_path, char_maps_path): # Removed latent_dim, embedding_dim from args
        """Loads a trained model and its character maps for inference."""
        try:
            with open(char_maps_path, 'r', encoding='utf-8') as f:
                char_map_data = json.load(f)

            char_to_token = char_map_data['char_to_token']
            token_to_char = char_map_data['token_to_char']
            n_token = char_map_data['n_token']
            max_encoder_seq_length = char_map_data['max_encoder_seq_length']
            max_decoder_seq_length = char_map_data['max_decoder_seq_length']

            # Load latent_dim and embedding_dim from char_map_data
            # Provide defaults if not found, for backward compatibility or if file is old.
            latent_dim = char_map_data.get('latent_dim', 256)
            embedding_dim = char_map_data.get('embedding_dim', 128)

            instance = cls(char_to_token, token_to_char, max_encoder_seq_length,
                           max_decoder_seq_length, n_token, latent_dim, embedding_dim)

            # Build the model structure before loading weights
            instance._build_inference_models() # This also builds instance.model
            instance.model.load_weights(model_weights_path)
            # Inference models (encoder_model, decoder_model) share layers with model,
            # so their weights are updated when model.load_weights() is called.
            print(f"Model loaded successfully from {model_weights_path}")
            return instance

        except FileNotFoundError:
            raise FileNotFoundError(f"Error: Model or char map file not found. Searched: {model_weights_path}, {char_maps_path}")
        except Exception as e:
            raise Exception(f"Error loading model for inference: {e}")


# --- Helper functions for preparing data (can be moved to a utils.py or train.py) ---
def get_char_token_maps(problems, answers):
    input_texts = [p['problem'] for p in problems]
    target_texts = ['\t' + a['answer'] + '\n' for a in answers] # Add start/end tokens

    all_chars = set()
    for text in input_texts:
        for char in text:
            all_chars.add(char)
    for text in target_texts:
        for char in text:
            all_chars.add(char)

    all_chars = sorted(list(all_chars))
    all_chars.append('UNK') # For unknown characters

    char_to_token = dict([(char, i) for i, char in enumerate(all_chars)])
    token_to_char = dict([(i, char) for i, char in enumerate(all_chars)])
    n_token = len(all_chars)

    max_encoder_seq_length = max([len(txt) for txt in input_texts])
    max_decoder_seq_length = max([len(txt) for txt in target_texts])

    return char_to_token, token_to_char, n_token, max_encoder_seq_length, max_decoder_seq_length

def prepare_data(problems, answers, char_to_token, max_encoder_seq_length, max_decoder_seq_length, n_token):
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
                if t > 0: # decoder_target_data is one timestep ahead
                    decoder_target_data[i, t - 1, char_to_token[char]] = 1.
            else: # Handle UNK token
                decoder_input_data[i, t] = char_to_token['UNK']
                if t > 0:
                    decoder_target_data[i, t - 1, char_to_token['UNK']] = 1.


    return encoder_input_data, decoder_input_data, decoder_target_data


if __name__ == '__main__':
    # This is a placeholder for example usage or basic testing
    # Actual training and data loading will be in train.py

    # Dummy data for testing the class structure
    dummy_problems = [{'problem': '1+1'}, {'problem': '10*2'}]
    dummy_answers = [{'answer': '2'}, {'answer': '20'}]

    char_map, token_map, n_tok, max_enc_len, max_dec_len = get_char_token_maps(dummy_problems, dummy_answers)

    print(f"Num tokens: {n_tok}")
    print(f"Max encoder sequence length: {max_enc_len}")
    print(f"Max decoder sequence length: {max_dec_len}")
    print(f"Char to token map: {char_map}")

    # Test model build
    arith_model = ArithmeticSeq2Seq(char_map, token_map, max_enc_len, max_dec_len, n_tok)
    arith_model.build_model()

    # Test prediction (on a non-trained model, this will be gibberish)
    print("\nTesting prediction (on untrained model):")
    test_problem = "5+5"
    predicted_answer = arith_model.predict_sequence(test_problem)
    print(f"Problem: {test_problem}")
    print(f"Predicted Answer: {predicted_answer}")

    test_problem_2 = "123*2"
    predicted_answer_2 = arith_model.predict_sequence(test_problem_2)
    print(f"Problem: {test_problem_2}")
    print(f"Predicted Answer: {predicted_answer_2}")

    print("\nModel.py basic structure test complete.")
