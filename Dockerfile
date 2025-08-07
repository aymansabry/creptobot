# استخدم صورة بايثون الرسمية
FROM python:3.11-slim

# تثبيت الحزم الأساسية المطلوبة للبناء
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# تعيين مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ ملفات المشروع إلى داخل الحاوية
COPY . .

# تثبيت المتطلبات
RUN pip install --no-cache-dir -r requirements.txt

# أمر التشغيل
CMD ["python", "bot.py"]
