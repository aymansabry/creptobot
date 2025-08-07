from datetime import datetime, timedelta
from typing import List, Dict
from db.crud import get_user_trades
from notifications.telegram_notifier import send_notification
from utils.logger import logger

class TradeReporter:
    def __init__(self, bot, db_session):
        self.bot = bot
        self.db_session = db_session
    
    async def generate_daily_report(self, user_id: int):
        try:
            start_date = datetime.now() - timedelta(days=1)
            trades = await get_user_trades(self.db_session, user_id, start_date=start_date)
            
            if not trades:
                return await send_notification(
                    self.bot,
                    user_id,
                    "📊 تقريرك اليومي:\n\n"
                    "لم تنفذ أي صفقات اليوم."
                )
            
            total_profit = sum(t.profit for t in trades)
            total_commission = sum(t.commission for t in trades)
            successful_trades = sum(1 for t in trades if t.status == 'completed')
            failed_trades = len(trades) - successful_trades
            
            report = (
                "📊 تقريرك اليومي:\n\n"
                f"🔄 عدد الصفقات: {len(trades)}\n"
                f"✅ ناجحة: {successful_trades}\n"
                f"❌ فاشلة: {failed_trades}\n"
                f"💰 إجمالي الربح: {total_profit:.2f} USDT\n"
                f"⚖️ إجمالي العمولة: {total_commission:.2f} USDT\n\n"
                f"📈 أفضل صفقة: +{max(t.profit for t in trades if t.status == 'completed'):.2f} USDT\n"
                f"📉 أسوأ صفقة: {min(t.profit for t in trades if t.status == 'completed'):.2f} USDT"
            )
            
            await send_notification(self.bot, user_id, report)
        except Exception as e:
            logger.error(f"Failed to generate daily report: {str(e)}")
    
    async def generate_continuous_investment_report(self, user_id: int, investment_data: Dict):
        try:
            start_time = investment_data['start_time']
            end_time = datetime.now()
            duration = end_time - start_time
            
            report = (
                "🔄 تقرير الاستثمار المستمر:\n\n"
                f"⏳ المدة: {duration.days} يوم, {duration.seconds // 3600} ساعة\n"
                f"💸 المبلغ المستثمر: {investment_data['amount']} USDT\n"
                f"🔄 عدد الصفقات: {investment_data['trade_count']}\n"
                f"💰 إجمالي الربح: {investment_data['total_profit']:.2f} USDT\n"
                f"⚖️ إجمالي العمولة: {investment_data['total_commission']:.2f} USDT\n\n"
                f"📌 تم تحويل المبلغ الأصلي والأرباح إلى محفظتك."
            )
            
            await send_notification(self.bot, user_id, report)
        except Exception as e:
            logger.error(f"Failed to generate continuous investment report: {str(e)}")
    
    async def send_admin_report(self, admin_id: int):
        try:
            # إحصائيات النظام اليومية
            today = datetime.now().date()
            total_users = await self.db_session.execute(
                "SELECT COUNT(*) FROM users WHERE DATE(join_date) = :today",
                {'today': today}
            )
            total_trades = await self.db_session.execute(
                "SELECT COUNT(*) FROM trades WHERE DATE(created_at) = :today",
                {'today': today}
            )
            total_profit = await self.db_session.execute(
                "SELECT SUM(profit) FROM trades WHERE DATE(created_at) = :today AND status='completed'",
                {'today': today}
            )
            total_commission = await self.db_session.execute(
                "SELECT SUM(commission) FROM trades WHERE DATE(created_at) = :today",
                {'today': today}
            )
            
            report = (
                "📊 التقرير اليومي للمدير:\n\n"
                f"👥 مستخدمون جدد: {total_users.scalar() or 0}\n"
                f"🔄 صفقات اليوم: {total_trades.scalar() or 0}\n"
                f"💰 أرباح المستخدمين: {total_profit.scalar() or 0:.2f} USDT\n"
                f"⚖️ عمولة النظام: {total_commission.scalar() or 0:.2f} USDT"
            )
            
            await send_notification(self.bot, admin_id, report)
        except Exception as e:
            logger.error(f"Failed to send admin report: {str(e)}")
