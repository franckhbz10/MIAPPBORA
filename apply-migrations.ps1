# Script PowerShell para aplicar migraciones SQL a Supabase
# Usa psql o ejecuta mediante Python con psycopg

# Cargar variables de entorno desde .env
if (Test-Path "backend\.env") {
    Get-Content "backend\.env" | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim().Trim('"')
            [System.Environment]::SetEnvironmentVariable($key, $value, [System.EnvironmentVariableTarget]::Process)
        }
    }
}

$dbUrl = $env:POSTGRES_URL
if (-not $dbUrl) {
    $dbUrl = $env:DATABASE_URL
}

if (-not $dbUrl) {
    Write-Error "No se encontró DATABASE_URL o POSTGRES_URL en .env"
    exit 1
}

Write-Host "Aplicando migraciones SQL a Supabase..." -ForegroundColor Cyan

# Ejecutar migraciones con psql (si está disponible) o Python
$sqlFiles = @(
    "docs\migrations\2025-10-30-embeddings-1536.sql",
    "docs\migrations\2025-10-30-bora-docs-1536.sql"
)

# Intentar con psql primero
$psqlAvailable = Get-Command psql -ErrorAction SilentlyContinue
if ($psqlAvailable) {
    Write-Host "Usando psql..." -ForegroundColor Green
    foreach ($file in $sqlFiles) {
        Write-Host "Ejecutando: $file" -ForegroundColor Yellow
        psql $dbUrl -f $file
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Error ejecutando $file"
            exit 1
        }
    }
} else {
    # Fallback a Python con psycopg
    Write-Host "psql no disponible, usando Python..." -ForegroundColor Yellow
    python backend/scripts/apply_sql.py --file $sqlFiles[0] --file $sqlFiles[1]
}

Write-Host "`nMigraciones aplicadas correctamente!" -ForegroundColor Green
