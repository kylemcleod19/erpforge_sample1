FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "\
  echo 'Starting backend...' && \
  python -c 'from app.main import app; print(\"Import OK\")' && \
  timeout 30 alembic upgrade head || echo 'WARNING: migrations failed or timed out' ; \
  echo 'Starting uvicorn...' && \
  exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} \
"]
