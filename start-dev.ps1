# MIAPPBORA - Script de inicio para desarrollo local
# Ejecuta backend principal y frontend (y opcionalmente microservicio LLM)

Write-Host "🌿 MIAPPBORA - Iniciando servicios de desarrollo..." -ForegroundColor Green
Write-Host ""

# Verificar que estamos en la raíz del proyecto
if (-not (Test-Path "backend\main.py") -or -not (Test-Path "frontend\package.json")) {
    Write-Host "❌ Error: Este script debe ejecutarse desde la raíz del proyecto MIAPPBORA" -ForegroundColor Red
    exit 1
}

# Preguntar qué servicios arrancar
Write-Host "Selecciona los servicios a arrancar:" -ForegroundColor Cyan
Write-Host "  1) Backend principal (puerto 8000) + Frontend (puerto 3000)"
Write-Host "  2) Backend principal + Frontend + Microservicio LLM (puerto 8001)"
Write-Host ""
$opcion = Read-Host "Opción [1/2]"

if ($opcion -eq "" -or $opcion -eq "1") {
    Write-Host ""
    Write-Host "🚀 Arrancando Backend + Frontend..." -ForegroundColor Yellow
    Write-Host ""
    
    # Backend
    Write-Host "📦 Backend principal → http://localhost:8000" -ForegroundColor Magenta
    Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd backend; & .\venv\Scripts\Activate.ps1; uvicorn main:app --reload"
    
    Start-Sleep -Seconds 2
    
    # Frontend
    Write-Host "🎨 Frontend → http://localhost:3000" -ForegroundColor Magenta
    Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"
    
    Write-Host ""
    Write-Host "✅ Servicios arrancados en terminales separadas" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔗 URLs:" -ForegroundColor Cyan
    Write-Host "   Frontend:  http://localhost:3000"
    Write-Host "   Backend:   http://localhost:8000"
    Write-Host "   API Docs:  http://localhost:8000/docs"
    
} elseif ($opcion -eq "2") {
    # Verificar que existe el microservicio LLM
    if (-not (Test-Path "llm_service\main.py")) {
        Write-Host ""
        Write-Host "⚠️  El microservicio LLM no está implementado aún." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Para implementarlo, consulta:" -ForegroundColor Cyan
        Write-Host "  - docs/LLM_MICROSERVICE.md" -ForegroundColor White
        Write-Host "  - docs/ORGANIZACION_PROYECTO.md" -ForegroundColor White
        Write-Host ""
        Write-Host "¿Arrancar solo Backend + Frontend por ahora? [S/n]" -ForegroundColor Yellow
        $continuar = Read-Host
        
        if ($continuar -eq "" -or $continuar -eq "S" -or $continuar -eq "s") {
            # Arrancar solo backend + frontend
            Write-Host ""
            Write-Host "🚀 Arrancando Backend + Frontend..." -ForegroundColor Yellow
            Write-Host ""
            
            Write-Host "📦 Backend principal → http://localhost:8000" -ForegroundColor Magenta
            Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd backend; & .\venv\Scripts\Activate.ps1; uvicorn main:app --reload"
            
            Start-Sleep -Seconds 2
            
            Write-Host "🎨 Frontend → http://localhost:3000" -ForegroundColor Magenta
            Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"
            
            Write-Host ""
            Write-Host "✅ Servicios arrancados" -ForegroundColor Green
        } else {
            Write-Host "❌ Operación cancelada" -ForegroundColor Red
            exit 0
        }
    } else {
        Write-Host ""
        Write-Host "🚀 Arrancando Backend + Frontend + Microservicio LLM..." -ForegroundColor Yellow
        Write-Host ""
        
        # Backend principal
        Write-Host "📦 Backend principal → http://localhost:8000" -ForegroundColor Magenta
        Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd backend; & .\venv\Scripts\Activate.ps1; uvicorn main:app --reload --port 8000"
        
        Start-Sleep -Seconds 2
        
        # Microservicio LLM
        Write-Host "🤖 Microservicio LLM → http://localhost:8001" -ForegroundColor Magenta
        Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd llm_service; & .\venv_llm\Scripts\Activate.ps1; uvicorn main:app --reload --port 8001"
        
        Start-Sleep -Seconds 2
        
        # Frontend
        Write-Host "🎨 Frontend → http://localhost:3000" -ForegroundColor Magenta
        Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"
        
        Write-Host ""
        Write-Host "✅ Servicios arrancados en terminales separadas" -ForegroundColor Green
        Write-Host ""
        Write-Host "🔗 URLs:" -ForegroundColor Cyan
        Write-Host "   Frontend:      http://localhost:3000"
        Write-Host "   Backend:       http://localhost:8000"
        Write-Host "   LLM Service:   http://localhost:8001"
        Write-Host "   Backend Docs:  http://localhost:8000/docs"
        Write-Host "   LLM Docs:      http://localhost:8001/docs"
    }
}

Write-Host ""
Write-Host "💡 Tip: Cierra las terminales individuales para detener los servicios" -ForegroundColor Gray
Write-Host ""
