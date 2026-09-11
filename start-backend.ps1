$ErrorActionPreference = 'Stop'

function Get-FreeTcpPort {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
    $listener.Start()
    $port = ($listener.LocalEndpoint).Port
    $listener.Stop()
    return $port
}

function Initialize-BackendEnv {
    param([string]$BackendPath)

    $envFile = Join-Path $BackendPath '.env'
    if (Test-Path $envFile) { return }

    Write-Host ''
    Write-Host 'First local PostgreSQL setup for LAYA Market.'
    Write-Host 'This is a one-time configuration. Docker is not used.'

    $dbHost = Read-Host 'PostgreSQL host [127.0.0.1]'
    if ([string]::IsNullOrWhiteSpace($dbHost)) { $dbHost = '127.0.0.1' }

    $dbPort = Read-Host 'PostgreSQL port [5432]'
    if ([string]::IsNullOrWhiteSpace($dbPort)) { $dbPort = '5432' }

    $dbUser = Read-Host 'PostgreSQL user [postgres]'
    if ([string]::IsNullOrWhiteSpace($dbUser)) { $dbUser = 'postgres' }

    $securePassword = Read-Host "PostgreSQL password for '$dbUser'" -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
    try {
        $dbPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }

    $encodedUser = [Uri]::EscapeDataString($dbUser)
    $encodedPassword = [Uri]::EscapeDataString($dbPassword)
    $auth = $encodedUser
    if (-not [string]::IsNullOrEmpty($dbPassword)) { $auth = "$encodedUser`:$encodedPassword" }

    $databaseUrl = "postgresql+psycopg://$auth@$dbHost`:$dbPort/laya_market"

    @"
APP_NAME=LAYA Market API
ENV=development
DATABASE_URL=$databaseUrl
JWT_SECRET=change-me-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_MINUTES=1440
CORS_ORIGINS=
"@ | Set-Content -Path $envFile -Encoding UTF8

    Write-Host "Saved local database configuration in $envFile"
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $repoRoot 'backend'
Set-Location $backend

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    Write-Host 'Creating backend virtual environment...'
    python -m venv .venv
}

$python = Join-Path $backend '.venv\Scripts\python.exe'
Write-Host 'Installing backend dependencies...'
& $python -m pip install --disable-pip-version-check -r requirements.txt

Initialize-BackendEnv -BackendPath $backend

Write-Host 'Checking local PostgreSQL and LAYA Market database...'
& $python -m app.setup_db

Write-Host 'Running migrations...'
& $python -m alembic upgrade head

Write-Host 'Applying demo seed...'
& $python -m app.seed

$backendPort = Get-FreeTcpPort
Write-Host "Starting FastAPI on http://127.0.0.1:$backendPort"
Write-Host "Swagger: http://127.0.0.1:$backendPort/docs"
& $python -m uvicorn app.main:app --reload --host 127.0.0.1 --port $backendPort
