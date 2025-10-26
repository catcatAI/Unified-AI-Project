# TODO: Fix import - module 'random' not found
from tools.scripts.check_ai_docstrings import

def generate_uid(length = 16):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k = length))
