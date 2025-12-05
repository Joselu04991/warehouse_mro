# Usa Python oficial
FROM python:3.11-slim

# Crear carpeta
WORKDIR /app

# Copiar requerimientos
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el proyecto
COPY . .

# Exponer puerto (obligatorio para Koyeb)
EXPOSE 8080

# Ejecutar la app con Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
