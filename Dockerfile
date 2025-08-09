FROM python:3.11-slim
WORKDIR /app
COPY . /app
# First, update apt and install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends build-essential python3-dev
# Then, clean up apt cache to reduce image size
RUN rm -rf /var/lib/apt/lists/*
# Finally, install Python packages
RUN pip install --upgrade pip && pip install -r requirements.txt
CMD ["python", "main.py"]
