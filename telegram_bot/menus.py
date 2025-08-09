from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu(is_admin=False, mode='simulate'):
    kb = InlineKeyboardMarkup(row_width=2)
    mode_text = '🟢 حي' if mode == 'live' else '⚪️ محاكاة'
    kb.add(InlineKeyboardButton(f'💰 الوضع: {mode_text}', callback_data='toggle_mode'))
    kb.add(InlineKeyboardButton('⚙️ إعدادات الحساب', callback_data='settings'))
    kb.add(InlineKeyboardButton('🔐 إدارة المنصات', callback_data='manage_exchanges'))
    kb.add(InlineKeyboardButton('📊 صفقاتك', callback_data='my_trades'))
    kb.add(InlineKeyboardButton('🧾 سداد أرباح البوت', callback_data='pay_admin'))
    if is_admin:
        kb.add(InlineKeyboardButton('🔒 إدارة المستخدمين', callback_data='admin_users'))
    return kb

def exchange_manage_kb(user_exchanges):
    kb = InlineKeyboardMarkup(row_width=2)
    all_exchanges = ['binance', 'kucoin', 'kraken', 'okx', 'huobi', 'gate']
    
    for ex in all_exchanges:
        status = '✅' if user_exchanges.get(ex, {}).get('enabled') else '❌'
        kb.insert(InlineKeyboardButton(f'{ex} {status}', callback_data=f'exchg_{ex}'))
    
    kb.add(InlineKeyboardButton('⬅️ رجوع', callback_data='main'))
    return kb

def exchange_action_kb(exchange_name):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton('➕ إضافة/تعديل مفاتيح', callback_data=f'add_keys_{exchange_name}'))
    kb.add(InlineKeyboardButton('🟢 تفعيل', callback_data=f'enable_{exchange_name}'))
    kb.add(InlineKeyboardButton('❌ تعطيل', callback_data=f'disable_{exchange_name}'))
    kb.add(InlineKeyboardButton('⬅️ رجوع', callback_data='manage_exchanges'))
    return kb
