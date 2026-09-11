$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

Write-Host 'Starting PostgreSQL...'
docker compose up -d db | Out-Host

Write-Host 'Waiting for PostgreSQL health...'
for ($i = 0; $i -lt 30; $i++) {
    $state = docker inspect -f '{{.State.Health.Status}}' laya_market_postgres 2>$null
    if ($state -eq 'healthy') { break }
    Start-Sleep -Seconds 2
}

$portLine = docker compose port db 5432
if (-not $portLine) { throw 'Could not resolve PostgreSQL host port.' }
$dbPort = ($portLine -split ':')[-1].Trim()
Write-Host "PostgreSQL host port: $dbPort"

$backend = Join-Path $repoRoot 'laya-market-mvp\backend'
Set-Location $backend

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    Write-Host 'Creating virtual environment...'
    python -m venv .venv
}

$python = Join-Path $backend '.venv\Scripts\python.exe'

Write-Host 'Installing backend dependencies...'
& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt

$env:DATABASE_URL = "postgresql+psycopg://laya:laya_dev_password@127.0.0.1:$dbPort/laya_market"

Write-Host 'Running migrations...'
& $python -m alembic upgrade head

Write-Host 'Applying demo seed...'
& $python -m app.seed

Write-Host 'Starting FastAPI on an available port...'
& $python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 0
