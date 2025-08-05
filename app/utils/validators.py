# app/utils/validators.py
def is_valid_amount(amount: float) -> bool:
    return amount > 0

def is_valid_address(address: str) -> bool:
    return address.startswith("T") and len(address) == 34
