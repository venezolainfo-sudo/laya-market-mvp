$ErrorActionPreference = 'Stop'

function Get-FreeTcpPort {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
    $listener.Start()
    $port = ($listener.LocalEndpoint).Port
    $listener.Stop()
    return $port
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

Write-Host 'Starting PostgreSQL...'
docker compose up -d db | Out-Host

Write-Host 'Waiting for PostgreSQL health...'
$state = $null
for ($i = 0; $i -lt 30; $i++) {
    $state = docker inspect -f '{{.State.Health.Status}}' laya_market_postgres 2>$null
    if ($state -eq 'healthy') { break }
    Start-Sleep -Seconds 2
}
if ($state -ne 'healthy') { throw 'PostgreSQL did not become healthy.' }

$portLine = docker compose port db 5432
if (-not $portLine) { throw 'Could not resolve PostgreSQL host port.' }
$dbPort = ($portLine -split ':')[-1].Trim()
$backendPort = Get-FreeTcpPort
$apiBase = "http://127.0.0.1:$backendPort/api/v1"

$backend = Join-Path $repoRoot 'backend'
Set-Location $backend

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    Write-Host 'Creating backend virtual environment...'
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

$backendCommand = "$env:DATABASE_URL='$($env:DATABASE_URL)'; & '$python' -m uvicorn app.main:app --reload --host 127.0.0.1 --port $backendPort"
Start-Process powershell -ArgumentList '-NoExit','-Command',$backendCommand -WorkingDirectory $backend

$merchant = Join-Path $repoRoot 'apps\merchant-dashboard'
$merchantCommand = "$env:VITE_API_URL='$apiBase'; npm install; npm run dev"
Start-Process powershell -ArgumentList '-NoExit','-Command',$merchantCommand -WorkingDirectory $merchant

$admin = Join-Path $repoRoot 'apps\admin-dashboard'
$adminCommand = "$env:VITE_API_URL='$apiBase'; npm install; npm run dev"
Start-Process powershell -ArgumentList '-NoExit','-Command',$adminCommand -WorkingDirectory $admin

Write-Host ''
Write-Host 'LAYA Market development environment started.'
Write-Host "Backend: http://127.0.0.1:$backendPort"
Write-Host "Swagger: http://127.0.0.1:$backendPort/docs"
Write-Host 'Merchant and Admin dashboards will print their own available Vite URLs in their PowerShell windows.'
