# استخدم صورة بايثون الرسمية
FROM python:3.11-slim

# تثبيت أدوات النظام المطلوبة لبناء psycopg2
RUN apt-get update && apt-get install -y     gcc     libpq-dev     build-essential     && rm -rf /var/lib/apt/lists/*

# إعداد مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ الملفات إلى الحاوية
COPY . .

# تثبيت المتطلبات
RUN pip install --no-cache-dir -r requirements.txt

# أمر التشغيل
CMD ["python", "bot.py"]
