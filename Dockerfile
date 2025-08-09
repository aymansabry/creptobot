FROM python:3.11-slim
WORKDIR /app
COPY . /app
# تثبيت حزم النظام المطلوبة للتجميع والربط (linking)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
# تثبيت حزم بايثون
RUN pip install --upgrade pip && pip install -r requirements.txt
CMD ["python", "main.py"]
