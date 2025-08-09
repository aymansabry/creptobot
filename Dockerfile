FROM python:3.11-slim
WORKDIR /app
COPY . /app

# تثبيت حزم النظام المطلوبة للتجميع والربط (linking)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# تثبيت حزم بايثون واحدة تلو الأخرى لتحديد أي حزمة تسبب المشكلة
RUN pip install --upgrade pip
RUN pip install aiogram==3.0.0
RUN pip install ccxt==4.0.0
RUN pip install sqlalchemy==2.0.22
RUN pip install psycopg2-binary
RUN pip install python-dotenv
RUN pip install cryptography
RUN pip install openai

CMD ["python", "main.py"]
