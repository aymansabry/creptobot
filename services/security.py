def validate_api_format(api_key, secret, passphrase=None):
    if not api_key or not secret:
        return False
    if len(api_key) < 10 or len(secret) < 10:
        return False
    if passphrase and len(passphrase) < 4:
        return False
    return True