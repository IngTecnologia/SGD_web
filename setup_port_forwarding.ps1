# ============================================================================
# Script para configurar Port Forwarding de Windows a WSL2
# Permite acceder a los contenedores Docker de WSL2 desde Windows usando localhost
# ============================================================================

# IMPORTANTE: Ejecutar como ADMINISTRADOR

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SGD Web - Port Forwarding Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Obtener la IP de WSL2
Write-Host "Obteniendo IP de WSL2..." -ForegroundColor Yellow
$wslIP = wsl hostname -I
$wslIP = $wslIP.Trim().Split()[0]

if (-not $wslIP) {
    Write-Host "ERROR: No se pudo obtener la IP de WSL2" -ForegroundColor Red
    Write-Host "Asegurate de que WSL2 este corriendo" -ForegroundColor Red
    exit 1
}

Write-Host "IP de WSL2 detectada: $wslIP" -ForegroundColor Green
Write-Host ""

# Verificar si ya existen reglas
Write-Host "Limpiando reglas anteriores (si existen)..." -ForegroundColor Yellow
netsh interface portproxy delete v4tov4 listenport=80 listenaddress=0.0.0.0 2>$null
netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0 2>$null
netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0 2>$null
netsh interface portproxy delete v4tov4 listenport=5432 listenaddress=0.0.0.0 2>$null
Write-Host "Listo" -ForegroundColor Green
Write-Host ""

# Crear port forwarding
Write-Host "Configurando port forwarding..." -ForegroundColor Yellow
Write-Host "  - Puerto 80 (Nginx) -> $wslIP`:80"
netsh interface portproxy add v4tov4 listenport=80 listenaddress=0.0.0.0 connectport=80 connectaddress=$wslIP

Write-Host "  - Puerto 8000 (Backend) -> $wslIP`:8000"
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$wslIP

Write-Host "  - Puerto 3000 (Frontend) -> $wslIP`:3000"
netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=$wslIP

Write-Host "  - Puerto 5432 (PostgreSQL) -> $wslIP`:5432"
netsh interface portproxy add v4tov4 listenport=5432 listenaddress=0.0.0.0 connectport=5432 connectaddress=$wslIP

Write-Host ""
Write-Host "Port forwarding configurado correctamente!" -ForegroundColor Green
Write-Host ""

# Mostrar reglas activas
Write-Host "Reglas activas:" -ForegroundColor Cyan
netsh interface portproxy show all
Write-Host ""

# Configurar firewall (opcional pero recomendado)
Write-Host "Configurando reglas de firewall..." -ForegroundColor Yellow
$firewallRules = @(
    @{Name="SGD-Nginx"; Port=80},
    @{Name="SGD-Backend"; Port=8000},
    @{Name="SGD-Frontend"; Port=3000},
    @{Name="SGD-PostgreSQL"; Port=5432}
)

foreach ($rule in $firewallRules) {
    # Eliminar regla si existe
    Remove-NetFirewallRule -DisplayName $rule.Name -ErrorAction SilentlyContinue

    # Crear nueva regla
    New-NetFirewallRule -DisplayName $rule.Name `
                       -Direction Inbound `
                       -LocalPort $rule.Port `
                       -Protocol TCP `
                       -Action Allow `
                       -Profile Any `
                       -ErrorAction SilentlyContinue | Out-Null

    Write-Host "  - Regla de firewall creada: $($rule.Name) (Puerto $($rule.Port))" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  CONFIGURACION COMPLETADA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Ahora puedes acceder a SGD Web usando:" -ForegroundColor Cyan
Write-Host "  http://localhost/" -ForegroundColor Yellow
Write-Host ""
Write-Host "Credenciales:" -ForegroundColor Cyan
Write-Host "  Email: admin@sgd-web.local" -ForegroundColor Yellow
Write-Host "  Password: admin123" -ForegroundColor Yellow
Write-Host ""
Write-Host "NOTA: Si reinicias Windows o WSL2, ejecuta este script nuevamente" -ForegroundColor Yellow
Write-Host "      ya que la IP de WSL2 puede cambiar." -ForegroundColor Yellow
Write-Host ""

# Preguntar si quiere abrir el navegador
$response = Read-Host "Deseas abrir SGD Web en el navegador ahora? (S/N)"
if ($response -eq "S" -or $response -eq "s") {
    Start-Process "http://localhost/"
}
