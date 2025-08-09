import asyncio
from services.other_exchanges import ExchangeAPIManager
from core.config import MIN_INVESTMENT_USDT
from utils.notifications import NotificationService

notification_service = NotificationService()

class ArbitrageTrader:
    def __init__(self, config):
        self.exchange_manager = ExchangeAPIManager(config)
        self.active = True

    async def start(self, user):
        if user.investment_amount < MIN_INVESTMENT_USDT:
            await notification_service.send_notification(
                int(user.telegram_id),
                f"المبلغ أقل من الحد الأدنى: {MIN_INVESTMENT_USDT} USDT."
            )
            return

        while self.active and user.active:
            active_exchanges = self.exchange_manager.list_active_exchanges()
            # TODO: منطق المراجحة هنا

            await asyncio.sleep(10)

    def stop(self):
        self.active = False
