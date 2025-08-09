from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from telegram_bot.menus import main_menu, exchange_manage_kb, exchange_action_kb
from db.database import get_session
from db.models import User, Trade
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, update
from core.config import ADMIN_TELEGRAM_ID
from core.logger import get_logger
# from core.security import encrypt_text  # تم إزالة هذا السطر
from aiogram.filters import Command

logger = get_logger('telegram_handlers')

class AddApiKeys(StatesGroup):
    waiting_for_api_key = State()
    waiting_for_secret = State()

def setup_handlers(router):
    @router.message(Command('start'))
    async def start_cmd(message: Message, state: FSMContext, session: Session = next(get_session())):
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            role = 'admin' if message.from_user.id == ADMIN_TELEGRAM_ID else 'user'
            user = User(telegram_id=message.from_user.id, username=message.from_user.username, role=role)
            session.add(user)
            session.commit()
            await message.answer('تم إنشاء حسابك. اختر من القائمة:', reply_markup=main_menu(is_admin=(role=='admin'), mode=user.mode))
        else:
            await message.answer('مرحبًا — اختر وظيفة:', reply_markup=main_menu(is_admin=(user.role=='admin'), mode=user.mode))
        await state.clear()

    @router.callback_query(lambda c: True)
    async def all_callbacks(cb: CallbackQuery, state: FSMContext, session: Session = next(get_session())):
        data = cb.data
        user = session.query(User).filter_by(telegram_id=cb.from_user.id).first()
        if not user:
            await cb.answer('يرجى التسجيل أولاً باستخدام /start', show_alert=True)
            return

        if data == 'main':
            await cb.message.edit_text('القائمة الرئيسية:', reply_markup=main_menu(is_admin=(user.role=='admin'), mode=user.mode))
        
        elif data == 'toggle_mode':
            new_mode = 'live' if user.mode == 'simulate' else 'simulate'
            user.mode = new_mode
            session.commit()
            await cb.answer(f'تم تغيير الوضع إلى: {new_mode}')
            await cb.message.edit_text('تم تغيير الوضع. ارجع للقائمة الرئيسية.', reply_markup=main_menu(is_admin=(user.role=='admin'), mode=user.mode))
            
        elif data == 'manage_exchanges':
            await cb.message.edit_text('اختر منصة لإدارة مفاتيحها:', reply_markup=exchange_manage_kb(user.api_exchange))
        
        elif data.startswith('exchg_'):
            exchange_name = data.split('_')[1]
            await cb.message.edit_text(f'إدارة منصة **{exchange_name}**:', reply_markup=exchange_action_kb(exchange_name), parse_mode='Markdown')
        
        elif data.startswith('add_keys_'):
            exchange_name = data.split('_', 2)[2]
            await state.set_state(AddApiKeys.waiting_for_api_key)
            await state.update_data(exchange_name=exchange_name)
            await cb.message.answer(f'أرسل الآن مفتاح API الخاص بمنصة **{exchange_name}**.', parse_mode='Markdown')
            
        elif data.startswith('enable_'):
            exchange_name = data.split('_')[1]
            if user.api_exchange and exchange_name in user.api_exchange:
                user.api_exchange[exchange_name]['enabled'] = True
                session.commit()
                await cb.answer(f'تم تفعيل منصة {exchange_name}.')
            else:
                await cb.answer(f'لا توجد مفاتيح لهذه المنصة. يرجى إضافتها أولاً.', show_alert=True)
            await cb.message.edit_text('إدارة المنصات:', reply_markup=exchange_manage_kb(user.api_exchange))
            
        elif data.startswith('disable_'):
            exchange_name = data.split('_')[1]
            if user.api_exchange and exchange_name in user.api_exchange:
                user.api_exchange[exchange_name]['enabled'] = False
                session.commit()
                await cb.answer(f'تم تعطيل منصة {exchange_name}.')
            else:
                await cb.answer(f'لا توجد مفاتيح لهذه المنصة.', show_alert=True)
            await cb.message.edit_text('إدارة المنصات:', reply_markup=exchange_manage_kb(user.api_exchange))
            
        elif data == 'my_trades':
            trades = session.query(Trade).filter_by(user_id=user.id).order_by(Trade.created_at.desc()).limit(10).all()
            if not trades:
                await cb.message.answer('لا توجد صفقات بعد.')
            else:
                txt = '\n'.join([f"**{t.pair}**: ربح {t.net_profit:.2f} USDT | الحالة: {t.status}" for t in trades])
                await cb.message.answer(f"**آخر 10 صفقات:**\n{txt}", parse_mode='Markdown')
        else:
            await cb.answer()

    @router.message(AddApiKeys.waiting_for_api_key)
    async def process_api_key(message: Message, state: FSMContext):
        data = await state.get_data()
        exchange_name = data['exchange_name']
        await state.update_data(api_key=message.text)
        await state.set_state(AddApiKeys.waiting_for_secret)
        await message.answer(f'تم حفظ مفتاح API. الآن أرسل **المفتاح السري** لمنصة **{exchange_name}**.', parse_mode='Markdown')

    @router.message(AddApiKeys.waiting_for_secret)
    async def process_secret_key(message: Message, state: FSMContext, session: Session = next(get_session())):
        data = await state.get_data()
        exchange_name = data['exchange_name']
        api_key = data['api_key']
        secret = message.text

        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            await message.answer('حدث خطأ. يرجى البدء من جديد باستخدام /start.')
            await state.clear()
            return
        
        # تم إزالة أسطر التشفير
        # encrypted_api_key = encrypt_text(api_key)
        # encrypted_secret = encrypt_text(secret)
        
        if user.api_exchange is None:
            user.api_exchange = {}
        
        user.api_exchange[exchange_name] = {
            'apiKey': api_key,  # تم التعديل لتخزين المفتاح الخام
            'secret': secret,   # تم التعديل لتخزين المفتاح الخام
            'enabled': True
        }
        
        session.commit()
        
        await message.answer(f'تم حفظ مفاتيح API بنجاح لمنصة {exchange_name}.', reply_markup=main_menu(is_admin=(user.role=='admin'), mode=user.mode))
        await state.clear()
