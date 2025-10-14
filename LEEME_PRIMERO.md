# 🚀 SGD Web - Guía de Acceso desde Windows

## ✅ El sistema está FUNCIONANDO

Todos los contenedores están corriendo correctamente:
- ✅ PostgreSQL (Base de datos)
- ✅ Backend (API FastAPI)
- ✅ Frontend (React)
- ✅ Nginx (Reverse proxy)
- ✅ Redis (Cache)

## 🎯 Problema: Windows + WSL2 + Docker

Docker está corriendo en WSL2, lo que crea una red virtual separada de Windows.
Por eso **`localhost` no funciona desde Windows**.

## 🔧 Solución 1: Usar la IP de WSL2 (Rápido)

**Accede directamente usando la IP de WSL2:**

### 🌐 URL de Acceso: http://172.23.175.109

**Credenciales:**
```
Email: admin@sgd-web.local
Password: admin123
```

### ⚠️ IMPORTANTE
Esta IP puede cambiar cuando reinicias tu PC. Para obtener la IP actual:
```bash
# En WSL2, ejecuta:
hostname -I
```

## 🔧 Solución 2: Port Forwarding (Recomendado)

Esta solución te permite usar `http://localhost` desde Windows.

### Paso 1: Abrir PowerShell como ADMINISTRADOR

1. Presiona `Win + X`
2. Selecciona "Windows PowerShell (Administrador)" o "Terminal (Administrador)"

### Paso 2: Ejecutar el script de configuración

```powershell
# Navega al directorio del proyecto
cd \\wsl$\Ubuntu\home\jesus\SGD\SGD_web

# Ejecuta el script
.\setup_port_forwarding.ps1
```

El script:
- ✅ Detecta automáticamente la IP de WSL2
- ✅ Configura port forwarding para todos los puertos
- ✅ Configura reglas de firewall necesarias
- ✅ Te pregunta si quieres abrir el navegador

### Después de ejecutar el script

Podrás acceder en: **http://localhost/**

### Para deshacer los cambios

```powershell
.\remove_port_forwarding.ps1
```

## 🔧 Solución 3: Configurar WSL2 con Networking Mirrored (Más permanente)

### Paso 1: Crear archivo de configuración

Crea el archivo `C:\Users\TU_USUARIO\.wslconfig` con este contenido:

```ini
[wsl2]
networkingMode=mirrored
```

### Paso 2: Reiniciar WSL2

En PowerShell (como administrador):
```powershell
wsl --shutdown
```

Luego vuelve a abrir WSL2.

Con esta configuración, WSL2 compartirá la misma red que Windows y `localhost` funcionará automáticamente.

## 📋 Archivos Útiles en este Directorio

- **`test_login_wsl_ip.html`** - Test de conectividad usando la IP de WSL2
- **`test_login.html`** - Test de conectividad usando localhost (requiere port forwarding)
- **`setup_port_forwarding.ps1`** - Script para configurar port forwarding
- **`remove_port_forwarding.ps1`** - Script para eliminar port forwarding
- **`ACCESO_WINDOWS.md`** - Documentación detallada

## 🎨 Usuarios Demo Disponibles

El sistema viene con 3 usuarios de prueba:

### 1. Administrador (Acceso completo)
```
Email: admin@sgd-web.local
Password: admin123
```

### 2. Operador (Puede crear y editar documentos)
```
Email: operator@sgd-web.local
Password: operator123
```

### 3. Viewer (Solo lectura)
```
Email: viewer@sgd-web.local
Password: viewer123
```

## ✅ Verificar que todo funciona

### Opción 1: Test con la IP de WSL2
Abre en tu navegador: `\\wsl$\Ubuntu\home\jesus\SGD\SGD_web\test_login_wsl_ip.html`

### Opción 2: Test con localhost (después de configurar port forwarding)
Abre en tu navegador: `\\wsl$\Ubuntu\home\jesus\SGD\SGD_web\test_login.html`

## 🆘 Solución de Problemas

### La IP de WSL2 cambió después de reiniciar

1. Obtén la nueva IP:
   ```bash
   hostname -I
   ```

2. Si configuraste port forwarding, ejecuta nuevamente:
   ```powershell
   .\setup_port_forwarding.ps1
   ```

### Los contenedores no están corriendo

```bash
# Verificar estado
docker ps

# Iniciar contenedores
docker-compose up -d

# Ver logs si hay problemas
docker-compose logs -f
```

### El frontend no se conecta al backend

Verifica que el frontend tenga la configuración correcta:
```bash
# Ver configuración actual
docker exec sgd-frontend env | grep REACT_APP_API_URL

# Debería mostrar: REACT_APP_API_URL=http://172.23.175.109
```

## 📞 Siguiente Paso

**Elige una de las soluciones y prueba acceder a la aplicación:**

- 🚀 **Más rápido:** Abre http://172.23.175.109 en tu navegador
- 🎯 **Más conveniente:** Ejecuta `setup_port_forwarding.ps1` y usa http://localhost

---

**¡Todo está listo! El sistema está desplegado y funcionando.** 🎉
