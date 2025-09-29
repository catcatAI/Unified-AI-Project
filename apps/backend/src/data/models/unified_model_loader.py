import os
import json
import sys

# Add src directory to sys.path to allow imports from sibling directories
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Global instances for models and their errors
_loaded_models = 
_model_load_errors = 

def _get_project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def load_math_model():
    """Loads the arithmetic model, handling potential TensorFlow import errors."""
    model_name = "math_model"
    if model_name in _loaded_models or model_name in _model_load_errors:
        return _loaded_models.get(model_name)

    MODEL_WEIGHTS_PATH = os.path.join(_get_project_root, "data/models/arithmetic_model.keras")
    CHAR_MAPS_PATH = os.path.join(_get_project_root, "data/models/arithmetic_char_maps.json")

    try:
        # 修复导入路径
        from ...tools.math_model.model import ArithmeticSeq2Seq
        print("Loading arithmetic model for the first time...")
        if not os.path.exists(MODEL_WEIGHTS_PATH) or not os.path.exists(CHAR_MAPS_PATH):
            raise FileNotFoundError("Math model or char map file not found.")

        model_instance = ArithmeticSeq2Seq.load_for_inference(
            MODEL_WEIGHTS_PATH, CHAR_MAPS_PATH
        )
        _loaded_models[model_name] = model_instance
        print("Arithmetic model loaded successfully.")

    except ImportError as e:
        print(f"CRITICAL: TensorFlow could not be imported for math model. NN features will be disabled. Error: {e}")
        _model_load_errors[model_name] = str(e)
    except FileNotFoundError as e:
        print(f"Warning: Math model files not found. NN features will be disabled. Error: {e}")
        _model_load_errors[model_name] = str(e)
    except Exception as e:
        print(f"An unexpected error occurred while loading the math model: {e}")
        _model_load_errors[model_name] = str(e)
        
    return _loaded_models.get(model_name)

def load_logic_nn_model():
    """Loads the LogicNNModel, handling potential TensorFlow import errors."""
    model_name = "logic_nn_model"
    if model_name in _loaded_models or model_name in _model_load_errors:
        return _loaded_models.get(model_name), _loaded_models.get("logic_nn_char_to_token")

    MODEL_LOAD_PATH = os.path.join(_get_project_root, "data/models/logic_model_nn.keras")
    CHAR_MAP_LOAD_PATH = os.path.join(_get_project_root, "data/models/logic_model_char_maps.json")

    try:
        # Assuming dependency_manager is available globally or passed in if needed
        # from dependency_manager import is_dependency_available
        # if not is_dependency_available('tensorflow'):
        #     raise ImportError("TensorFlow not available through dependency manager")

        # 修复导入路径
        from ...tools.logic_model.logic_model_nn import LogicNNModel
        print("Loading LogicNNModel for the first time...")
        if not os.path.exists(MODEL_LOAD_PATH) or not os.path.exists(CHAR_MAP_LOAD_PATH):
            raise FileNotFoundError("Logic NN Model or Char Map not found.")

        with open(CHAR_MAP_LOAD_PATH, 'r', encoding='utf-8') as f:
            char_to_token = json.load(f)

        model_instance = LogicNNModel.load_model(MODEL_LOAD_PATH)
        _loaded_models[model_name] = model_instance
        _loaded_models["logic_nn_char_to_token"] = char_to_token
        print("LogicNNModel loaded successfully.")

    except ImportError as e:
        print(f"CRITICAL: TensorFlow could not be imported for logic model. NN features will be disabled. Error: {e}")
        _model_load_errors[model_name] = str(e)
    except FileNotFoundError as e:
        print(f"Warning: Logic NN Model files not found. NN features will be disabled. Error: {e}")
        _model_load_errors[model_name] = str(e)
    except Exception as e:
        print(f"An unexpected error occurred while loading the logic NN model: {e}")
        _model_load_errors[model_name] = str(e)

    return _loaded_models.get(model_name), _loaded_models.get("logic_nn_char_to_token")

def get_model_load_error(model_name: str):
    """Returns the error message if a model failed to load."""
    return _model_load_errors.get(model_name)

# You can add more model loading functions here as needed