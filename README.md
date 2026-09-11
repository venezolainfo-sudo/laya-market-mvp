# LAYA Market MVP

## Arranque recomendado en Windows

Desde la raíz del repositorio:

```powershell
git pull
powershell -ExecutionPolicy Bypass -File .\start-dev.ps1
```

El script:
- levanta PostgreSQL con Docker usando un puerto host disponible;
- crea/reutiliza `backend/.venv`;
- instala las dependencias del backend;
- ejecuta Alembic;
- aplica el seed demo de forma idempotente;
- inicia FastAPI en un puerto disponible;
- inicia los dashboards de comercio y administración con Vite, sin fijar 5173/5174/5175;
- conecta ambos dashboards al puerto real elegido por FastAPI.

La terminal principal mostrará la URL real de Swagger (`/docs`). Los dashboards imprimirán sus URLs en sus respectivas ventanas de PowerShell.

## Credenciales demo

- Admin: `admin@layamarket.local` / `Admin123!`
- Comercio: `comercio@layamarket.local` / `Comercio123!`
- Cliente: `cliente@layamarket.local` / `Cliente123!`

## App móvil

```powershell
cd .\laya-market-mvp\apps\mobile
npm install
npx expo start -c
```

Expo elegirá su puerto de desarrollo disponible.
