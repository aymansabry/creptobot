wallets = {}

async def process_wallet_setup(msg):
    user_id = msg.from_user.id
    if user_id not in wallets:
        wallets[user_id] = {"balance": 100.0}
        await msg.answer("تم إنشاء محفظتك برصيد ابتدائي 100 USDT.")
    else:
        await msg.answer("محفظتك مُسجلة بالفعل.")

async def get_balance(user_id: int) -> float:
    if user_id in wallets:
        return wallets[user_id]["balance"]
    return 0.0
