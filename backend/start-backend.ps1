# Script de inicio para MIAPPBORA Backend
# Ejecutar: .\start-backend.ps1

Write-Host "🌿 Iniciando MIAPPBORA Backend..." -ForegroundColor Green
Write-Host ""

# Verificar si estamos en el directorio correcto
if (!(Test-Path "main.py")) {
    Write-Host "❌ Error: Debes ejecutar este script desde la carpeta backend/" -ForegroundColor Red
    exit 1
}

# Instalar dependencias mínimas para health check
Write-Host "📦 Instalando dependencias básicas..." -ForegroundColor Cyan
pip install --quiet fastapi uvicorn[standard] sqlalchemy pydantic pydantic-settings python-jose[cryptography] passlib[bcrypt] python-multipart python-dotenv

Write-Host "✅ Dependencias básicas instaladas" -ForegroundColor Green
Write-Host ""

Write-Host "ℹ️ NOTA: Supabase y HuggingFace se instalarán cuando las necesites" -ForegroundColor Yellow
Write-Host "   Por ahora el servidor funcionará sin ellas para health check" -ForegroundColor Yellow
Write-Host ""

# Crear archivo .env si no existe
if (!(Test-Path ".env")) {
    Write-Host "📝 Creando archivo .env desde plantilla..." -ForegroundColor Cyan
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Archivo .env creado. Edítalo con tus credenciales." -ForegroundColor Green
    Write-Host ""
}

# Iniciar servidor
Write-Host "🚀 Iniciando servidor en http://localhost:8000..." -ForegroundColor Green
Write-Host "📖 Documentación disponible en http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Presiona Ctrl+C para detener el servidor" -ForegroundColor Yellow
Write-Host ""

python -m uvicorn main:app --reload --port 8000
