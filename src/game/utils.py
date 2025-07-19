import random
import string

def generate_uid(length=16):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
