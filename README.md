# warehouse_mro
Sistema Almacén MRO

## Ejecución online y multiplataforma
Estas instrucciones funcionan en Linux, macOS y Windows (PowerShell/WSL) y te permiten exponer la app en tu red local o un proveedor PaaS.

### 1) Requisitos previos
- **Python 3.11+** y `pip` (para ejecución directa).
- **Docker/Docker Desktop** (para contenedor multiplataforma, recomendado en Windows/macOS).

### 2) Configurar variables de entorno
1. Copia el archivo `.env.example` a `.env` y ajusta los valores:
   ```bash
   cp .env.example .env
   ```
2. Cambia `SECRET_KEY` por un valor seguro. Si usarás una base de datos gestionada, rellena `DATABASE_URL`; de lo contrario, se usará SQLite local.

### 3) Ejecución directa con Python (red local)
Funciona igual en Linux/macOS y en Windows PowerShell (en Windows puedes usar WSL para evitar problemas de dependencias).
```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\\Scripts\\activate
pip install -r warehouse_mro/requirements.txt
export FLASK_RUN_HOST=0.0.0.0
export FLASK_RUN_PORT=5000
python -m warehouse_mro.app
```
La app quedará accesible en `http://<tu_ip_en_la_red>:5000` desde otros dispositivos (PC o móvil) conectados a la misma red.

### 4) Ejecución con Docker (multiplataforma recomendada)
Docker abstrae las dependencias; solo necesitas Docker Desktop (Windows/macOS) o Docker Engine (Linux).

**Opción A: Docker directo**
```bash
docker build -t warehouse_mro .
docker run -p 8000:8000 --env-file .env -v $(pwd)/warehouse_mro/uploads:/app/warehouse_mro/uploads warehouse_mro
```
La app quedará en `http://localhost:8000` (mapea ese puerto en tu firewall si la expones).

**Opción B: Docker Compose (más simple y portable)**
```bash
docker compose up --build
```
- Usa `docker-compose` en entornos más antiguos.
- El servicio publica `8000:8000`, carga `.env` y persiste subidas en `warehouse_mro/uploads`.

### 5) Producción y despliegue PaaS
- Define `SECRET_KEY` y `DATABASE_URL` en tu proveedor (Heroku, Render, Railway, etc.).
- El contenedor usa Gunicorn en `0.0.0.0:8000`, listo para balanceadores o Ingress.
- Mapea almacenamiento persistente para `warehouse_mro/uploads` si necesitas conservar archivos.

Estas rutas te permiten ejecutar la aplicación online y acceder a ella desde otros equipos o móviles dentro de la misma red o a través de un proveedor en la nube.
