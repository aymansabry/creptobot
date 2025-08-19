# استخدم صورة Python الرسمية
FROM python:3.11-slim

# تعيين مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ ملفات المشروع إلى الحاوية
COPY . .

# تثبيت المتطلبات
RUN pip install --no-cache-dir -r requirements.txt

# تعيين متغيرات البيئة (يمكن تعديلها من لوحة التحكم في Railway)
ENV PYTHONUNBUFFERED=1

# تشغيل البوت
CMD ["python", "main.py"]