FROM python:3.11-slim

WORKDIR /app

COPY warehouse_mro/ ./warehouse_mro/
COPY requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "warehouse_mro.app:app"]
