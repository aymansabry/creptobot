FROM python:3.11-slim

WORKDIR /app
COPY . /app

# أضف الأدوات المطلوبة للبناء
RUN apt-get update && apt-get install -y build-essential libssl-dev libffi-dev python3-dev

# ثم ثبّت المكتبات
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]
