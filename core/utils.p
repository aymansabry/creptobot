import random
import string

def generate_tx_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
