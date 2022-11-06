FROM python:3.10-slim-bullseye

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl=7.74.0-1.3+deb11u3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt --upgrade pip

COPY main.py /app/

EXPOSE 5000

CMD ["python", "/app/main.py"]
