import re

def is_valid_exchange_name(name: str) -> bool:
    """A simple validator for exchange names."""
    return bool(re.match(r'^[a-zA-Z0-9_\-]+$', name))
