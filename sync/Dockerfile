FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt /app/sync/requirements.txt
RUN pip install --no-cache-dir -r /app/sync/requirements.txt
COPY . /app/sync/

CMD ["python", "-m", "sync.main"]
