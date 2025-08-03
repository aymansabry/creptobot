import random

async def suggest_trades(user_id: int) -> str:
    suggestions = []
    for i in range(3):
        profit = round(random.uniform(6.0, 18.0), 2)
        duration = random.randint(5, 20)
        suggestions.append(f"صفقة #{i+1}: ربح متوقع {profit}% خلال {duration} دقيقة.")

    suggestions.sort(key=lambda x: float(x.split(" ")[2][:-1]), reverse=True)
    return "\n\n".join(suggestions)

async def run_simulated_trade(user_id: int) -> str:
    profit = round(random.uniform(6.0, 15.0), 2)
    return f"تم تنفيذ صفقة وهمية بنجاح. الربح: {profit}%"
