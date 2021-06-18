FROM python:3.8-slim-buster

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --upgrade pip

COPY main.py /app/

CMD ["python", "/app/main.py"]
