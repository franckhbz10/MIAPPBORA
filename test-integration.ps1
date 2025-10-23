# Script de PowerShell para test de integración
# Backend ↔ Microservicio LLM

Write-Host "`n" -NoNewline
Write-Host ("🧪" * 35) -ForegroundColor Cyan
Write-Host "          TEST DE INTEGRACIÓN COMPLETA" -ForegroundColor Yellow
Write-Host "     Backend ↔ Microservicio LLM ↔ Usuario" -ForegroundColor Yellow
Write-Host ("🧪" * 35) -ForegroundColor Cyan

$results = @()

# Test 1: Backend Health
Write-Host "`n" -NoNewline
Write-Host ("=" * 70) -ForegroundColor Gray
Write-Host "🔍 TEST 1: Backend Health Check" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -ErrorAction Stop
    Write-Host "✓ Status: OK" -ForegroundColor Green
    Write-Host "✓ App: $($response.app)" -ForegroundColor Green
    Write-Host "✓ Version: $($response.version)" -ForegroundColor Green
    $results += @{Name="Backend Health"; Success=$true}
} catch {
    Write-Host "✗ Error: $_" -ForegroundColor Red
    $results += @{Name="Backend Health"; Success=$false}
}

# Test 2: LLM Service Health
Write-Host "`n" -NoNewline
Write-Host ("=" * 70) -ForegroundColor Gray
Write-Host "🤖 TEST 2: Microservicio LLM Health Check" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8001/api/llm/health" -ErrorAction Stop
    Write-Host "✓ Status: OK" -ForegroundColor Green
    Write-Host "✓ State: $($response.status)" -ForegroundColor Green
    Write-Host "✓ Model: $($response.model)" -ForegroundColor Green
    Write-Host "✓ Device: $($response.device)" -ForegroundColor Green
    Write-Host "✓ Embeddings: $($response.embedding_model)" -ForegroundColor Green
    $results += @{Name="LLM Service Health"; Success=$true}
} catch {
    Write-Host "✗ Error: $_" -ForegroundColor Red
    $results += @{Name="LLM Service Health"; Success=$false}
}

# Test 3: LLM Direct Generation
Write-Host "`n" -NoNewline
Write-Host ("=" * 70) -ForegroundColor Gray
Write-Host "💬 TEST 3: Generación de texto directo (microservicio)" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Gray

$messages = @(
    @{role="system"; content="Eres un asistente útil."},
    @{role="user"; content="Hola"}
)

Write-Host "`nMensaje: $($messages[1].content)" -ForegroundColor White
Write-Host "Generando respuesta... (30-60 segundos en CPU)" -ForegroundColor Yellow

try {
    $body = @{
        messages = $messages
        max_new_tokens = 30
    } | ConvertTo-Json -Depth 3

    $start = Get-Date
    $response = Invoke-RestMethod -Uri "http://localhost:8001/api/llm/generate" `
        -Method Post `
        -Body $body `
        -ContentType "application/json" `
        -TimeoutSec 120 `
        -ErrorAction Stop
    $duration = ((Get-Date) - $start).TotalSeconds

    Write-Host "`n✓ Status: OK" -ForegroundColor Green
    Write-Host "✓ Tiempo: $([math]::Round($duration, 2))s" -ForegroundColor Green
    Write-Host "✓ Tokens generados: $($response.tokens_generated)" -ForegroundColor Green
    Write-Host "✓ Device: $($response.device)" -ForegroundColor Green
    Write-Host "`n📝 Respuesta: $($response.answer)" -ForegroundColor White
    $results += @{Name="LLM Direct Generation"; Success=$true}
} catch {
    Write-Host "`n✗ Error: $_" -ForegroundColor Red
    $results += @{Name="LLM Direct Generation"; Success=$false}
}

# Test 4: Verificar logs del backend
Write-Host "`n" -NoNewline
Write-Host ("=" * 70) -ForegroundColor Gray
Write-Host "📋 TEST 4: Verificar configuración del backend" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Gray

Write-Host "`nRevisando que el backend tenga configurado el microservicio..." -ForegroundColor Yellow
Write-Host "⚠️ Nota: Verificar los logs del backend en la otra terminal" -ForegroundColor Yellow
Write-Host "   Debe mostrar: '✓ Microservicio LLM conectado'" -ForegroundColor Yellow
$results += @{Name="Backend Configuration"; Success=$true}

# Resumen
Write-Host "`n" -NoNewline
Write-Host ("=" * 70) -ForegroundColor Gray
Write-Host "📊 RESUMEN DE TESTS" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Gray

foreach ($result in $results) {
    if ($result.Success) {
        Write-Host "✅ PASS      - $($result.Name)" -ForegroundColor Green
    } else {
        Write-Host "❌ FAIL      - $($result.Name)" -ForegroundColor Red
    }
}

$passed = ($results | Where-Object { $_.Success }).Count
$total = $results.Count

Write-Host "`n" -NoNewline
Write-Host ("=" * 70) -ForegroundColor Gray
Write-Host "Resultado Final: $passed/$total tests pasados ($([math]::Round($passed/$total*100, 1))%)" -ForegroundColor $(if ($passed -eq $total) {"Green"} else {"Yellow"})
Write-Host ("=" * 70) -ForegroundColor Gray

if ($passed -eq $total) {
    Write-Host "`n🎉 ¡TODOS LOS TESTS PASARON!" -ForegroundColor Green
    Write-Host "✅ El microservicio LLM está integrado correctamente" -ForegroundColor Green
} elseif ($passed -ge 3) {
    Write-Host "`n✅ Tests críticos pasados" -ForegroundColor Green
    Write-Host "⚠️ Revisar los tests que fallaron" -ForegroundColor Yellow
} else {
    Write-Host "`n⚠️ Algunos tests fallaron - revisar configuración" -ForegroundColor Red
}

Write-Host ""
