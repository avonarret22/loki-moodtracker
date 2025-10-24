# Script para iniciar el servidor FastAPI con Claude integrado
Set-Location $PSScriptRoot
Write-Host "Iniciando servidor desde: $PSScriptRoot" -ForegroundColor Green
Write-Host "Cargando variables de entorno desde .env..." -ForegroundColor Cyan
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
