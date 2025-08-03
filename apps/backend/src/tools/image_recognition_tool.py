from skimage import data
from skimage.feature import match_template
import numpy as np

def recognize_image(image, template):
    """
    Recognizes an image using template matching.

    Args:
        image: The image to be recognized.
        template: The template to be matched.

    Returns:
        A tuple containing the x and y coordinates of the best match.
    """
    result = match_template(image, template)
    ij = np.unravel_index(np.argmax(result), result.shape)
    x, y = ij[::-1]
    return x, y

def save_model(model, model_path):
    """
    Saves the model to a file.

    Args:
        model: The model to be saved.
        model_path: The path to the file where the model will be saved.
    """
    np.save(model_path, model)

def load_model(model_path):
    """
    Loads the model from a file.

    Args:
        model_path: The path to the file where the model is saved.

    Returns:
        The loaded model.
    """
    return np.load(model_path)
