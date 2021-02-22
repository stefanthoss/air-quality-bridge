FROM tiangolo/uwsgi-nginx-flask:python3.8

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --upgrade pip

COPY main.py /app/
COPY main.cfg /app/
