FROM python:3.11-slim

WORKDIR /app

# تثبيت التبعيات النظامية
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# نسخ المتطلبات أولاً (لتحسين استخدام الطبقات)
COPY requirements.txt .

# تثبيت جميع الحزم
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# نسخ باقي الملفات
COPY . .

CMD ["python", "main.py"]
