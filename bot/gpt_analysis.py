import random

async def get_profitable_deal(amount: float) -> dict:
    # توليد صفقة وهمية باستخدام تحليل الذكاء الاصطناعي لاحقًا
    fake_deals = [
        {"profit_percent": 14.0, "duration": 40},
        {"profit_percent": 11.0, "duration": 25},
        {"profit_percent": 9.5, "duration": 30},
        {"profit_percent": 7.0, "duration": 20},
        {"profit_percent": 5.5, "duration": 15},
    ]
    deal = random.choice(fake_deals)
    return deal
