FROM python:3.8-slim-buster

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --upgrade pip

COPY main.py /app/

CMD ["python", "/app/main.py"]
