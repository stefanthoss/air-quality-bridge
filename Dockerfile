FROM python:3.8-slim-buster

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --upgrade pip

COPY main.py /app/

# CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
CMD ["python", "/app/main.py"]
