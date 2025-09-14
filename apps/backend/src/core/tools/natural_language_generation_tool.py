from transformers import pipeline

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
