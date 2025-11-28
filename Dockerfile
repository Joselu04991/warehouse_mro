FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY warehouse_mro/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY warehouse_mro /app/warehouse_mro

ENV FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=8000

EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "warehouse_mro.app:app"]
