import os
from dotenv import load_dotenv

load_dotenv()

class ConfigLoader:
    def __init__(self):
        pass

    def get(self, key: str, default=None):
        return os.getenv(key, default)