import openai
import asyncio
from core.config import OPENAI_API_KEY
from utils.notifications import NotificationService

openai.api_key = OPENAI_API_KEY
notification_service = NotificationService()

class AITrader:
    def __init__(self):
        self.active = True

    async def start(self, user):
        while self.active and user.active:
            prompt = "تحليل سوق العملات الرقمية واقتراح صفقة مراجحة آمنة."
            try:
                response = openai.Completion.create(
                    engine="text-davinci-003",
                    prompt=prompt,
                    max_tokens=150,
                    temperature=0.5
                )
                decision = response.choices[0].text.strip()
                await notification_service.send_notification(
                    int(user.telegram_id),
                    f"توصية تداول: {decision}"
                )
            except Exception as e:
                await notification_service.send_notification(
                    int(user.telegram_id),
                    f"خطأ في تحليل الذكاء الاصطناعي: {e}"
                )
            await asyncio.sleep(60)

    def stop(self):
        self.active = False
