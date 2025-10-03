import os
import sys
_ = sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.tools.parameter_extractor import ParameterExtractor

def main() -> None:
    # 1. Initialize the ParameterExtractor
    extractor = ParameterExtractor(repo_id="bert-base-uncased")

    # 2. Download the model parameters
    _ = print("Downloading model parameters...")
    model_path = extractor.download_model_parameters(filename="pytorch_model.bin")
    _ = print(f"Model parameters downloaded to: {model_path}")

    # 3. Verify that the file was downloaded
    _ = assert os.path.exists(model_path)
    _ = print("File download verified successfully.")

if __name__ == "__main__":


    _ = main()
