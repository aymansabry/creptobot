from aiogram import types
from aiogram.dispatcher import FSMContext
from db.crud import create_user_wallet
from core.config import SystemConfig, OperationMode
from templates.menu_templates import wallet_type_menu

async def request_wallet_type(message: types.Message):
    settings = await get_system_settings()
    if not settings.allow_simulation and not settings.real_trading_enabled:
        return await message.answer("النظام غير متاح حالياً")
    
    menu = await wallet_type_menu(settings)
    await message.answer("اختر نوع المحفظة:", reply_markup=menu)

async def handle_wallet_type_selection(callback: types.CallbackQuery, state: FSMContext):
    wallet_type = OperationMode(callback.data.split(":")[1])
    
    if wallet_type == OperationMode.REAL and not SystemConfig.CURRENT_MODE == OperationMode.REAL:
        return await callback.answer("التداول الحقيقي معطل حالياً")
    
    wallet = await create_user_wallet(
        user_id=callback.from_user.id,
        wallet_type=wallet_type
    )
    
    await callback.answer(f"تم إنشاء محفظة {wallet_type.value} بنجاح")
    await show_wallet_details(callback.message, wallet)
