# Math Model: Lightweight Arithmetic Calculation

## Overview

The `math_model` directory (`src/tools/math_model/`) contains components for a **lightweight sequence-to-sequence model designed to perform basic arithmetic calculations** (addition, subtraction, multiplication, and division). This capability allows the AI to directly solve numerical problems, enhancing its utility in data analysis, problem-solving, and interactive applications.

The model is implemented using TensorFlow/Keras and provides a neural network-based approach to arithmetic, complementing rule-based calculation tools.

## Key Components

1.  **`model.py`**: Defines the `ArithmeticSeq2Seq` neural network architecture. This is an LSTM-based encoder-decoder model designed to learn the mapping from arithmetic expressions to their results.

2.  **`data_generator.py`**: A script used to generate synthetic datasets of arithmetic problems and their corresponding answers. These datasets are crucial for training and evaluating the neural network model.

3.  **`train.py`**: The script responsible for training the `ArithmeticSeq2Seq` model using the generated datasets. It handles the training loop and saves the trained model weights (e.g., to `data/models/arithmetic_model.keras`) and the character mappings (to `data/models/arithmetic_char_maps.json`) essential for inference.

4.  **`evaluate.py`**: A script to assess the performance of a trained model on a test dataset. It reports accuracy and can show example predictions.

5.  **`math_tool.py`** (located in the parent `src/tools` directory): Provides a high-level interface to use the trained model for calculations. It includes basic parsing of natural language queries to extract arithmetic problems and then uses the loaded `ArithmeticSeq2Seq` model to find the answer. It is designed to be invoked by the main `ToolDispatcher`.

## Model Architecture (`model.py`)

The `ArithmeticSeq2Seq` class implements an LSTM-based encoder-decoder architecture:

-   **Encoder**: Processes the input arithmetic expression (sequence of character tokens) through an Embedding layer and an LSTM layer. The final hidden and cell states of the LSTM are passed to the decoder.
-   **Decoder**: Takes the encoder's final states and a start-of-sequence token. It generates the answer sequence one token at a time, using its own Embedding and LSTM layers, followed by a Dense layer with softmax activation to predict the next character.
-   **Inference Models**: Separate encoder and decoder models are constructed from the trained layers to facilitate efficient sequence generation during prediction.

## Character and Token Mapping

-   The `get_char_token_maps` function (used by `train.py`) creates mappings between characters (numbers, operators, special tokens) and integer tokens.
-   These maps are vital for converting problem/answer strings into a format suitable for the neural network and for converting the network's output back into readable strings.
-   The maps are saved and loaded by `evaluate.py` and `math_tool.py` to ensure consistent processing.

## Setup and Usage Workflow

1.  **Environment**: Ensure Python 3.x and TensorFlow are installed.
2.  **Data Generation**: Run `python src/tools/math_model/data_generator.py` to create datasets.
3.  **Model Training**: Run `python src/tools/math_model/train.py` to train the model.
4.  **Model Evaluation**: Run `python src/tools/math_model/evaluate.py` to assess performance.
5.  **Using the Tool**: The `math_tool.py` provides the primary interface, typically invoked via the `ToolDispatcher`.

## Future Enhancements

-   Support for more complex expressions (e.g., multiple operations, parentheses).
-   Handling of floating-point numbers with greater precision or specific formatting.
-   More sophisticated NLP for problem extraction in `math_tool.py`.
-   Optimization of the model architecture (e.g., adding attention, using different RNN types like GRU).
-   More comprehensive error analysis in `evaluate.py`.

## Current Status

Tests currently show failures indicating instability in core model components. Work is ongoing to improve reliability and functionality.

## Code Location

`src/tools/math_model/`
