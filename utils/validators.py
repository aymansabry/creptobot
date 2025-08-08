def is_valid_amount(amount: str):
    try:
        value = float(amount)
        return value >= 1.0
    except ValueError:
        return False
