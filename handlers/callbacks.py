from aiogram import types, Router
from aiogram.types import CallbackQuery
from keyboards.main import main_menu
from database.investments import create_investment_request
from utils.ai_engine import ask_ai

router = Router()

@router.callback_query(lambda c: c.data == "new_investment")
async def new_investment_handler(callback: CallbackQuery):
    await callback.message.edit_text("💵 من فضلك أدخل المبلغ الذي حولته USDT:")

@router.callback_query(lambda c: c.data == "my_investments")
async def my_investments_handler(callback: CallbackQuery):
    await callback.message.edit_text("📊 عرض استثماراتك قيد التطوير حالياً.")

@router.callback_query(lambda c: c.data == "analyze_trades")
async def analyze_trades_handler(callback: CallbackQuery):
    analysis = await ask_ai("قدم لي أفضل 3 فرص تداول للعملات الرقمية بفارق ربح لا يقل عن 3%.")
    await callback.message.edit_text(f"🤖 تحليل الصفقات:\n\n{analysis}")
