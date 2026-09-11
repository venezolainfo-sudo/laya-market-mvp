# LAYA Market MVP

## Arranque recomendado en Windows

Si descargaste el proyecto como ZIP desde GitHub, abre PowerShell dentro de la carpeta raíz `laya-market-mvp` y ejecuta:

```powershell
powershell -ExecutionPolicy Bypass -File .\start-dev.ps1
```

Si trabajas con Git clone, primero puedes actualizar con `git pull` y luego ejecutar el mismo script.

El script:
- levanta PostgreSQL con Docker usando un puerto host disponible;
- crea/reutiliza `backend/.venv`;
- instala las dependencias Python del backend;
- ejecuta Alembic;
- aplica el seed demo de forma idempotente;
- inicia FastAPI en un puerto disponible;
- ejecuta `npm install` para los dashboards de comercio y administración;
- inicia ambos dashboards con Vite sin fijar 5173/5174/5175;
- conecta ambos dashboards al puerto real elegido por FastAPI.

La terminal principal mostrará la URL real del backend y Swagger (`/docs`). Los dashboards imprimirán sus URLs en sus respectivas ventanas de PowerShell.

## Requisitos locales

- Docker Desktop abierto y funcionando.
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
