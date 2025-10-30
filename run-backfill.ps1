# Script PowerShell para ejecutar backfill dentro del venv

$ErrorActionPreference = "Stop"

# Cargar variables del .env
if (Test-Path "backend\.env") {
    Get-Content "backend\.env" | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim().Trim('"')
            [System.Environment]::SetEnvironmentVariable($key, $value, [System.EnvironmentVariableTarget]::Process)
        }
    }
}

# Activar venv
& "backend\venv\Scripts\Activate.ps1"

# Sobreescribir flag de API
$env:USE_EMBEDDING_API = "true"

# Ejecutar backfill según argumentos
$target = $args[0]
$batch = if ($args[1]) { $args[1] } else { "32" }
$limit = if ($args[2]) { $args[2] } else { "0" }

Write-Host "Ejecutando backfill para $target (batch=$batch, limit=$limit)..." -ForegroundColor Cyan

python backend/scripts/backfill_embeddings_1536.py --target $target --batch $batch --limit $limit

if ($LASTEXITCODE -ne 0) {
    Write-Error "Backfill falló"
    exit 1
}

Write-Host "`n✅ Backfill completado" -ForegroundColor Green
