import os
from dotenv import load_dotenv

load_dotenv()

class ConfigLoader:
    def __init__(self):
        pass

    def get(self, key: str, default=None):
        parts = key.split(".")
        if len(parts) == 2:
            prefix, field = parts
            env_key = f"{prefix.upper()}_{field.upper()}"
        else:
            env_key = key.upper()
        return os.getenv(env_key, default)