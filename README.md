# warehouse_mro
Sistema Almacén MRO

## Ejecución online y multiplataforma

### 1) Configuración por variables de entorno
1. Copia el archivo `.env.example` a `.env` y ajusta los valores:
   ```bash
   cp .env.example .env
   ```
2. Personaliza `SECRET_KEY` y, si lo necesitas, `DATABASE_URL` para usar PostgreSQL/MySQL. Por defecto se usa SQLite en local.
3. Inicia el servidor en modo accesible desde otras máquinas:
   ```bash
   export FLASK_RUN_HOST=0.0.0.0
   export FLASK_RUN_PORT=5000
   pip install -r warehouse_mro/requirements.txt
   python -m warehouse_mro.app
   ```
   Con `FLASK_RUN_HOST=0.0.0.0` la app queda disponible en la red (p. ej. `http://<tu_ip>:5000`).

### 2) Despliegue contenedorizado (Docker)
1. Construye la imagen:
   ```bash
   docker build -t warehouse_mro .
   ```
2. Arranca el contenedor publicando el puerto:
   ```bash
   docker run -p 8000:8000 --env-file .env warehouse_mro
   ```
   El contenedor ejecuta Gunicorn en `0.0.0.0:8000`, listo para balanceadores o plataformas tipo AWS, Azure o GCP.

### 3) Producción y despliegues PaaS
- Usa `DATABASE_URL` apuntando a tu base de datos gestionada.
- Establece `SECRET_KEY` con un valor seguro en el proveedor (Heroku, Render, Railway, etc.).
- Mapea un volumen o servicio de archivos para las subidas en `warehouse_mro/uploads` si necesitas persistencia.

Estas opciones permiten exponer la aplicación de forma online y accesible desde escritorio o móvil.
