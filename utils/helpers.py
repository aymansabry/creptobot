from datetime import timedelta

def calculate_fees(amount: float, rate: float) -> float:
    return amount * rate

def format_duration(seconds: int) -> str:
    return str(timedelta(seconds=seconds))
