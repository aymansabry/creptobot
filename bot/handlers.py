from aiogram import Router, types
from bot.wallet import get_user_wallet, create_virtual_wallet
from bot.trades import suggest_trades, execute_trade
from bot.utils import get_user_stats

router = Router()

async def start_handler(msg: types.Message):
    await msg.answer("مرحبًا بك في بوت التداول الذكي! أرسل /صفقة لبدء الاستثمار أو /تجربة لتجربة وهمية.")

async def trade_handler(msg: types.Message):
    wallet = await get_user_wallet(msg.from_user.id)
    if not wallet:
        await create_virtual_wallet(msg.from_user.id)
        await msg.answer("تم إنشاء محفظتك، أرسل /صفقة لبدء أول استثمار.")

    suggestions = await suggest_trades()
    if suggestions:
        text = "\n".join(f"⚡ صفقة بنسبة ربح {s['profit']}٪ في {s['duration']} دقيقة" for s in suggestions)
        await msg.answer(f"الصفقات المتاحة:\n\n{text}")
    else:
        await msg.answer("لا توجد صفقات مربحة حالياً، سيتم إعلامك عند توفرها.")

async def demo_handler(msg: types.Message):
    await msg.answer("هذه تجربة وهمية لمحاكاة الصفقة دون استخدام رصيد. 👍")

async def stats_handler(msg: types.Message):
    stats = await get_user_stats(msg.from_user.id)
    await msg.answer(stats)

def register_handlers(dp):
    dp.include_router(router)
    router.message.register(start_handler, commands={"start"})
    router.message.register(trade_handler, commands={"صفقة"})
    router.message.register(demo_handler, commands={"تجربة"})
    router.message.register(stats_handler, commands={"رصيدي"})
