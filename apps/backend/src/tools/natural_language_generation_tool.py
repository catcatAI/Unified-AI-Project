# 添加兼容性导入
try:
    # 设置环境变量以解决Keras兼容性问题
    import os
    os.environ['TF_USE_LEGACY_KERAS'] = '1'
    
    # 使用我们的兼容性模块
    try:
        from apps.backend.src.compat.transformers_compat import import_transformers_pipeline
        pipeline, TRANSFORMERS_AVAILABLE = import_transformers_pipeline()
        if not TRANSFORMERS_AVAILABLE:
            print("Warning: Could not import transformers pipeline")
    except ImportError as e:
        print(f"Warning: Could not import transformers_compat: {e}")
        pipeline = None
        TRANSFORMERS_AVAILABLE = False
except Exception as e:
    print(f"Warning: Error during transformers import: {e}")
    pipeline = None
    TRANSFORMERS_AVAILABLE = False

def generate_text(prompt):
    """
    Generates text from a prompt.

    Args:
        prompt: The prompt to generate text from.

    Returns:
        The generated text.
    """
    generator = pipeline("text-generation")
    return generator(prompt)

def save_model(model, model_path):
    """
    Saves the model to a file.

    Args:
        model: The model to be saved.
        model_path: The path to the file where the model will be saved.
    """
    model.save_pretrained(model_path)

def load_model(model_path):
    """
    Loads the model from a file.

    Args:
        model_path: The path to the file where the model is saved.

    Returns:
        The loaded model.
    """
    return pipeline("text-generation", model=model_path)