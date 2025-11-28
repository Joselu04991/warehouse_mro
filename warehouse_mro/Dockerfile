FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r warehouse_mro/requirements.txt

EXPOSE 8000

CMD ["python", "warehouse_mro/app.py"]
