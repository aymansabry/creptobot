FFROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt setup.py ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -e .

COPY . .

CMD ["python", "main.py"]
