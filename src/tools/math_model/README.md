# Lightweight Arithmetic Model

This directory contains a lightweight sequence-to-sequence model designed to perform basic arithmetic calculations (addition, subtraction, multiplication, and division).

## Overview

The model is implemented using TensorFlow/Keras and consists of the following main components:

-   `model.py`: Defines the `ArithmeticSeq2Seq` neural network architecture. It's an LSTM-based encoder-decoder model.
-   `data_generator.py`: A script to generate datasets of arithmetic problems and their answers in CSV or JSON format.
-   `train.py`: A script to train the model using a generated dataset. It saves the trained model weights and character mappings.
-   `evaluate.py`: A script to evaluate the performance of a trained model on a test dataset.
-   `math_tool.py` (located in the parent `tools` directory): Provides a high-level interface to use the trained model for calculations, including basic parsing of natural language queries to extract arithmetic problems.

## Setup

1.  **Environment**: Ensure you have Python 3.x and TensorFlow installed. Dependencies are typically managed at the project root level (e.g., via `requirements.txt`).
    ```bash
    pip install tensorflow numpy
    ```

## Usage Workflow

### 1. Data Generation

The `data_generator.py` script is used to create training and testing datasets.

-   **To generate default datasets (JSON for training, CSV for testing):**
    ```bash
    python src/tools/math_model/data_generator.py
    ```
    This will create:
    -   `data/raw_datasets/arithmetic_train_dataset.json` (10,000 samples)
    -   `data/raw_datasets/arithmetic_test_dataset.csv` (2,000 samples)

-   **Customization**: You can modify `data_generator.py` to change the number of samples, `max_digits` for numbers, output filenames, and formats.

### 2. Model Training

The `train.py` script is used to train the model.

-   **Prerequisites**: Ensure `arithmetic_train_dataset.json` exists in `data/raw_datasets/`.
-   **To start training:**
    ```bash
    python src/tools/math_model/train.py
    ```
-   **Outputs**:
    -   Trained model weights: `data/models/arithmetic_model.keras`
    -   Character maps: `data/models/arithmetic_char_maps.json` (essential for inference)
-   **Hyperparameters**: Training parameters like `BATCH_SIZE`, `EPOCHS`, `LATENT_DIM`, etc., can be adjusted within `train.py`.

### 3. Model Evaluation

The `evaluate.py` script is used to assess the trained model's performance.

-   **Prerequisites**:
    -   Trained model (`arithmetic_model.keras`) and character maps (`arithmetic_char_maps.json`) must exist in `data/models/`.
    -   Test dataset (`arithmetic_test_dataset.csv`) must exist in `data/raw_datasets/`.
-   **To evaluate:**
    ```bash
    python src/tools/math_model/evaluate.py
    ```
-   **Output**: The script will print the accuracy of the model on the test set and show some example predictions.

### 4. Using the Model for Predictions (via `math_tool.py`)

The `math_tool.py` script (located in `src/tools/`) provides the primary interface for making predictions with the trained model. It's designed to be used by the `ToolDispatcher`.

-   **How it works**:
    1.  `math_tool.py` loads the trained model and character maps once.
    2.  The `calculate(query_string)` function extracts an arithmetic problem (e.g., "10 + 5") from the input string.
    3.  It then uses the model's `predict_sequence()` method to get the answer.
-   **Example (direct use of `math_tool.py` for testing):**
    ```bash
    python src/tools/math_tool.py
    ```
    This will run the `if __name__ == '__main__':` block in `math_tool.py`, demonstrating its usage.

## Model Architecture (`model.py`)

The `ArithmeticSeq2Seq` class implements an LSTM-based encoder-decoder architecture:

-   **Encoder**: Takes a sequence of character tokens representing the arithmetic problem and processes it through an Embedding layer and an LSTM layer. The final LSTM states (hidden state and cell state) are used to initialize the decoder.
-   **Decoder**: Takes the encoder's final states and a start-of-sequence token. It generates the answer sequence one token at a time, using its own Embedding and LSTM layers, followed by a Dense layer with softmax activation to predict the next character.
-   **Inference Models**: Separate encoder and decoder models are constructed from the trained layers to facilitate sequence generation during prediction.

## Character and Token Mapping

-   The `get_char_token_maps` function (in `model.py`, used by `train.py`) creates mappings between characters in the dataset (numbers, operators, start/end tokens) and integer tokens.
-   These maps are crucial for converting problem/answer strings into a format suitable for the neural network and for converting the network's output back into readable strings.
-   The maps are saved by `train.py` to `arithmetic_char_maps.json` and loaded by `evaluate.py` and `math_tool.py` for consistent processing.

## Future Enhancements

-   Support for more complex expressions (e.g., multiple operations, parentheses).
-   Handling of floating-point numbers with greater precision or specific formatting.
-   More sophisticated NLP for problem extraction in `math_tool.py`.
-   Optimization of the model architecture (e.g., adding attention, using different RNN types like GRU).
-   More comprehensive error analysis in `evaluate.py`.
