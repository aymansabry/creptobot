# استخدم صورة Python الرسمية
FROM python:3.11-slim

# إعداد مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ ملفات المشروع
COPY . /app

# تثبيت الاعتماديات
RUN pip install --no-cache-dir -r requirements.txt

# ضبط الأمر الرئيسي لتشغيل البوت
CMD ["python", "bot.py"]
