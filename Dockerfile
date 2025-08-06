FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt --no-cache-dir

CMD ["gunicorn", "--config", "gunicorn_config.py", "main:bot"]
