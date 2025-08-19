# services/profit_calculator.py
def calculate_profit(amount, type):
    if type == "fixed":
        return amount * 0.03  # 3% شهريًا
    elif type == "flex":
        return amount * 0.05  # 5% متغيرة
    elif type == "risk":
        return amount * 0.12  # مخاطرة عالية
    return 0.0