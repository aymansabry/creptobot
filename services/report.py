from database.models import get_user_trades, get_user_balance
from config import BOT_SHARE_PERCENT

def generate_report(user_id):
    trades = get_user_trades(user_id)
    balance = get_user_balance(user_id)

    total_profit = sum([t["profit"] for t in trades])
    bot_share = total_profit * BOT_SHARE_PERCENT / 100
    net_user_profit = total_profit - bot_share

    last_trade = trades[-1] if trades else None

    return {
        "total_profit": round(total_profit, 4),
        "bot_share": round(bot_share, 4),
        "net_user_profit": round(net_user_profit, 4),
        "trade_count": len(trades),
        "last_trade": {
            "path": last_trade["path"],
            "profit": round(last_trade["profit"], 4),
            "timestamp": last_trade["timestamp"]
        } if last_trade else None,
        "balance": round(balance, 4)
    }