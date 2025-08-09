import asyncio
import openai
from services.other_exchanges import ExchangeAPIManager
from core.config import OPENAI_API_KEY, MIN_INVESTMENT_USDT
from utils.notifications import NotificationService

openai.api_key = OPENAI_API_KEY
notification_service = NotificationService()

class AIAutomaticArbitrageTrader:
    def __init__(self, config):
        self.exchange_manager = ExchangeAPIManager(config)
        self.active = True

    async def fetch_prices(self):
        prices = {}
        for name in self.exchange_manager.list_active_exchanges():
            exchange = self.exchange_manager.get_exchange(name)
            try:
                account_info = exchange.get_account_info()
                prices[name] = account_info
            except Exception as e:
                await notification_service.send_notification(
                    chat_id=123456,
                    message=f"خطأ في جلب بيانات {name}: {str(e)}"
                )
        return prices

    async def analyze_and_trade(self, user):
        if user.investment_amount < MIN_INVESTMENT_USDT:
            await notification_service.send_notification(
                int(user.telegram_id),
                f"مبلغ الاستثمار أقل من الحد الأدنى: {MIN_INVESTMENT_USDT} USDT."
            )
            return

        while self.active and user.active:
            prices = await self.fetch_prices()

            prompt = f"""
            البيانات الحالية للأسعار: {prices}
            حدد لي أفضل فرصة مراجحة بين هذه المنصات، مع الخطوات التنفيذية بالترتيب.
            وكم يجب أن يكون حجم الصفقة بناء على مبلغ استثمار {user.investment_amount} USDT.
            """

            try:
                response = openai.Completion.create(
                    engine="text-davinci-003",
                    prompt=prompt,
                    max_tokens=300,
                    temperature=0.3
                )
                decision_text = response.choices[0].text.strip()

                await notification_service.send_notification(int(user.telegram_id), f"توصية تداول AI:\n{decision_text}")

                # TODO: تحليل decision_text وتحويله لأوامر تنفيذية API تلقائياً

            except Exception as e:
                await notification_service.send_notification(int(user.telegram_id), f"خطأ AI: {e}")

            await asyncio.sleep(30)

    def stop(self):
        self.active = False
