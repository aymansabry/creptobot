from telegram import Bot
from telegram.constants import ParseMode
from typing import Optional, Union, List
import asyncio
from utils.logger import logger

async def send_notification(
    bot: Union[Bot, int],
    chat_id: int,
    message: str,
    parse_mode: Optional[str] = ParseMode.MARKDOWN,
    reply_markup=None
):
    try:
        if isinstance(bot, int):
            # إذا كان bot هو معرف البوت، نحتاج إلى الحصول على كائن البوت من مكان آخر
            # هذا يعتمد على كيفية إعداد نظامك
            pass
        
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {str(e)}")

async def broadcast_message(
    bot: Bot,
    db_session,
    message: str,
    exclude_ids: Optional[List[int]] = None
):
    try:
        if exclude_ids is None:
            exclude_ids = []
        
        users = await db_session.execute("SELECT telegram_id FROM users")
        users = users.scalars().all()
        
        success = 0
        failed = 0
        
        for user_id in users:
            if user_id in exclude_ids:
                continue
                
            try:
                await send_notification(bot, user_id, message)
                success += 1
            except Exception as e:
                logger.error(f"Failed to send to user {user_id}: {str(e)}")
                failed += 1
            await asyncio.sleep(0.1)  # لتجنب حظر الرسائل السريعة
        
        return {
            'status': 'completed',
            'success': success,
            'failed': failed
        }
    except Exception as e:
        logger.error(f"Broadcast failed: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e)
        }

async def send_trade_report(
    bot: Bot,
    user_id: int,
    trade_data: dict,
    is_completed: bool = True
):
    try:
        emoji = "✅" if is_completed else "⚠️"
        status = "مكتملة" if is_completed else "فشلت"
        
        message = (
            f"{emoji} تقرير الصفقة {status}\n\n"
            f"🆔 رقم الصفقة: {trade_data.get('id', 'N/A')}\n"
            f"📊 الرمز: {trade_data.get('symbol', 'N/A')}\n"
            f"🛒 الشراء من: {trade_data.get('buy_exchange', 'N/A')}\n"
            f"💰 سعر الشراء: {trade_data.get('buy_price', 0):.6f}\n"
            f"🏪 البيع في: {trade_data.get('sell_exchange', 'N/A')}\n"
            f"💵 سعر البيع: {trade_data.get('sell_price', 0):.6f}\n"
        )
        
        if is_completed:
            message += (
                f"🎯 الربح: {trade_data.get('profit', 0):.2f} USDT\n"
                f"⚖️ العمولة: {trade_data.get('commission', 0):.2f} USDT\n"
                f"📅 وقت التنفيذ: {trade_data.get('executed_at', 'N/A')}\n"
            )
        else:
            message += f"❌ الخطأ: {trade_data.get('error', 'غير معروف')}\n"
        
        await send_notification(bot, user_id, message)
    except Exception as e:
        logger.error(f"Failed to send trade report: {str(e)}")
