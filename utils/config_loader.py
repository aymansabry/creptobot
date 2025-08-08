# utils/config_loader.py
import os

class ConfigLoader:
    def get(self, key: str, default=None):
        env_key = key.upper().replace('.', '_')
        return os.environ.get(env_key, default)