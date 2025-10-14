# ============================================================================
# Script para ELIMINAR Port Forwarding de Windows a WSL2
# ============================================================================

# IMPORTANTE: Ejecutar como ADMINISTRADOR

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Eliminando Port Forwarding" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Eliminando reglas de port forwarding..." -ForegroundColor Yellow
netsh interface portproxy delete v4tov4 listenport=80 listenaddress=0.0.0.0
netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0
netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0
netsh interface portproxy delete v4tov4 listenport=5432 listenaddress=0.0.0.0

Write-Host ""
Write-Host "Eliminando reglas de firewall..." -ForegroundColor Yellow
Remove-NetFirewallRule -DisplayName "SGD-Nginx" -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName "SGD-Backend" -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName "SGD-Frontend" -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName "SGD-PostgreSQL" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Port forwarding eliminado correctamente!" -ForegroundColor Green
Write-Host ""

# Mostrar reglas restantes (debería estar vacío)
Write-Host "Reglas activas:" -ForegroundColor Cyan
netsh interface portproxy show all
Write-Host ""
