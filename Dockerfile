FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libffi-dev python3-dev libssl-dev default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --upgrade pip setuptools wheel && pip install -r requirements.txt

COPY . .

CMD ["python", "bot.py"]