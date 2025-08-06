FROM python:3.10-slim

# تثبيت أدوات البناء الأساسية
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# تثبيت المتطلبات مع تحديث pip أولاً
RUN pip install --upgrade pip && \
    pip install -r requirements.txt --no-cache-dir

CMD ["gunicorn", "main:bot", "--bind", "0.0.0.0:$PORT", "--worker-class", "uvicorn.workers.UvicornWorker"]
