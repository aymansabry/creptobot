FROM python:3.11-slim

WORKDIR /app
COPY . /app

# تثبيت المتطلبات للنظام
RUN apt-get update && apt-get install -y gcc libpq-dev

# تثبيت البايثون باكدجات
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]
