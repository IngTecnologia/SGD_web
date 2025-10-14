# 🚀 Cómo acceder a SGD Web desde Windows

## El Problema

WSL2 usa una red virtual separada de Windows. Cuando los contenedores Docker corren en WSL2,
`localhost` desde Windows no siempre funciona correctamente.

## ✅ Solución 1: Usar la IP de WSL2 (RECOMENDADO)

Tu IP de WSL2 es: **172.23.175.109**

**Accede a la aplicación usando:**
```
http://172.23.175.109
```

**Credenciales:**
- Email: admin@sgd-web.local
- Contraseña: admin123

## ✅ Solución 2: Port Forwarding de Windows

Ejecuta este comando en PowerShell como ADMINISTRADOR (en Windows, no en WSL):

```powershell
netsh interface portproxy add v4tov4 listenport=80 listenaddress=0.0.0.0 connectport=80 connectaddress=172.23.175.109
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=172.23.175.109
netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=172.23.175.109
```

**IMPORTANTE:** La IP de WSL2 puede cambiar cada vez que reinicias. Si después de reiniciar
no funciona, ejecuta `hostname -I` en WSL y actualiza los comandos con la nueva IP.

### Para verificar el port forwarding:
```powershell
netsh interface portproxy show all
```

### Para eliminar el port forwarding:
```powershell
netsh interface portproxy delete v4tov4 listenport=80 listenaddress=0.0.0.0
netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0
netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0
```

## ✅ Solución 3: Configurar WSL2 con IP estática

Crea o edita el archivo `C:\Users\TU_USUARIO\.wslconfig` en Windows:

```ini
[wsl2]
networkingMode=mirrored
```

Luego reinicia WSL2 desde PowerShell (como administrador):
```powershell
wsl --shutdown
```

Y vuelve a iniciar WSL2.

## 🔍 Verificar que todo funciona

1. Abre tu navegador en Windows
2. Ve a: `http://172.23.175.109/api/health`
3. Deberías ver un JSON con `"status": "healthy"`

Si ves eso, entonces accede a: `http://172.23.175.109`

## 📝 URLs importantes

- **Aplicación:** http://172.23.175.109/
- **API Health:** http://172.23.175.109/api/health
- **Backend directo:** http://172.23.175.109:8000/health
- **Frontend directo:** http://172.23.175.109:3000/

## ⚠️ Nota sobre la IP de WSL2

La IP `172.23.175.109` puede cambiar cuando reinicias tu PC o WSL2.

Para obtener la IP actual, ejecuta en WSL:
```bash
hostname -I
```

La primera IP que aparece es la que necesitas usar.

## 🛠️ Alternativa: Docker Desktop para Windows

Si instalas Docker Desktop para Windows (en lugar de usar Docker en WSL2),
los contenedores serán automáticamente accesibles en `localhost` desde Windows.

Descarga: https://www.docker.com/products/docker-desktop/
