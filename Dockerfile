# استخدم صورة Python خفيفة ومحدثة
FROM python:3.11-slim

# إعدادات البيئة
ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# تثبيت مكتبات النظام المطلوبة للبناء والمكتبات المشفرة
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    python3-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# إنشاء virtual environment
RUN python -m venv $VIRTUAL_ENV

# نسخ ملفات المشروع
WORKDIR /app
COPY . /app

# ترقية pip وتثبيت المكتبات من requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# تحديد الأمر الافتراضي لتشغيل البوت
CMD ["python", "main.py"]
