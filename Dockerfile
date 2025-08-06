FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt gunicorn uvicorn

CMD ["gunicorn", "main:bot", "--config", "gunicorn_config.py"]
