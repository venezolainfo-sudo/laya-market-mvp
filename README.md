# LAYA Market MVP

## Arranque recomendado en Windows

LAYA Market usa el PostgreSQL local instalado en Windows. Docker no forma parte del arranque del proyecto.

Desde la carpeta raíz del proyecto ejecuta:

```powershell
powershell -ExecutionPolicy Bypass -File .\start-dev.ps1
```

En la primera ejecución, si `backend/.env` todavía no existe, el script pide una sola vez los datos de tu PostgreSQL local (host, puerto, usuario y contraseña), guarda la conexión y crea automáticamente la base `laya_market` si aún no existe.

Después de esa primera configuración, el script:
- reutiliza `backend/.venv` o lo crea si falta;
- instala las dependencias Python del backend;
- verifica PostgreSQL local;
- crea la base `laya_market` si hace falta;
- ejecuta Alembic;
- aplica el seed demo de forma idempotente;
- inicia FastAPI en un puerto disponible;
- ejecuta `npm install` para los dashboards de comercio y administración;
- inicia ambos dashboards con Vite en puertos disponibles;
- conecta ambos dashboards al puerto real elegido por FastAPI.

La terminal principal mostrará la URL real del backend y Swagger (`/docs`). Los dashboards imprimirán sus URLs en sus respectivas ventanas de PowerShell.

## Requisitos locales

- PostgreSQL instalado y con su servicio iniciado.
- Python instalado y disponible como comando `python`.
- Node.js y npm instalados.

## Credenciales demo

- Admin: `admin@layamarket.local` / `Admin123!`
- Comercio: `comercio@layamarket.local` / `Comercio123!`
- Cliente: `cliente@layamarket.local` / `Cliente123!`

## App móvil

La app móvil no se inicia automáticamente con `start-dev.ps1`. Para instalarla y ejecutarla:

```powershell
cd .\apps\mobile
npm install
npx expo start -c
```

Expo elegirá un puerto de desarrollo disponible.
