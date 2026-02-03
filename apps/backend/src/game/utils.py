import random
import string

def generate_uid(length: int = 16) -> str:
    """Generates a random unique ID of a given length."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))