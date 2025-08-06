FROM python:3.10-slim

WORKDIR /app

# تثبيت تبعيات النظام
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# نسخ الملفات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# التأكد من تشغيل عملية وحيدة
CMD ["python", "main.py"]
