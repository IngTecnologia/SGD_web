# Sistema de Gestión Documental Web (SGD Web)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![Microsoft 365](https://img.shields.io/badge/Microsoft_365-Integration-orange.svg)](https://docs.microsoft.com/en-us/graph/)

Sistema web empresarial para gestión documental con integración completa con Microsoft 365, generación automática de códigos QR, sincronización con OneDrive y flujos de trabajo configurables.

## 🌟 Características Principales

### 🔐 Autenticación y Seguridad
- **Autenticación única (SSO)** con Microsoft 365/Azure AD
- **Roles de usuario** configurables (Admin, Operador, Viewer)
- **Tokens JWT** seguros con renovación automática
- **Validación de dominios** corporativos
- **Auditoría completa** de acciones de usuario

### 📄 Gestión Documental Avanzada
- **Tipos de documento configurables** con validaciones específicas
- **Subida masiva** de archivos con validación automática
- **Extracción automática de códigos QR** de documentos
- **Metadatos enriquecidos** y clasificación automática
- **Control de versiones** y trazabilidad completa
- **Gestión de retención** y archivo automático

### 🔍 QR Codes Inteligentes
- **Generación automática** de códigos QR únicos
- **Inserción en plantillas Word** con posicionamiento configurable
- **Extracción automática** desde PDFs e imágenes
- **Ciclo de vida completo** (generación → uso → expiración)
- **Validación y verificación** de integridad
- **Análisis y estadísticas** de uso

### ☁️ Integración Microsoft 365
- **Sincronización automática** con OneDrive Business
- **Estructura de carpetas** organizadas por tipo de documento
- **Graph API** para acceso a datos corporativos
- **Respaldo automático** en la nube
- **Colaboración** y compartición segura

### 🔎 Búsqueda y Filtrado
- **Búsqueda full-text** en contenido y metadatos
- **Filtros avanzados** por fecha, tipo, estado, etc.
- **Exportación** de resultados en múltiples formatos
- **Búsqueda por QR** y validación rápida

## 🏗️ Arquitectura del Sistema

### Backend (Python/FastAPI)
```
backend/
├── app/
│   ├── main.py                 # Aplicación principal FastAPI
│   ├── config.py              # Configuración centralizada
│   ├── database.py            # Configuración PostgreSQL
│   ├── models/                # Modelos SQLAlchemy
│   │   ├── user.py           # Usuarios y roles
│   │   ├── document.py       # Documentos principales
│   │   ├── document_type.py  # Tipos configurables
│   │   └── qr_code.py        # Códigos QR y ciclo de vida
│   ├── schemas/              # Validación Pydantic
│   │   ├── __init__.py       # Esquemas centralizados
│   │   ├── user.py          # Validación de usuarios
│   │   ├── document.py      # Validación de documentos
│   │   └── document_type.py # Validación de tipos
│   ├── api/                 # Endpoints REST
│   │   ├── deps.py         # Dependencias compartidas
│   │   └── endpoints/      # Controladores por módulo
│   ├── services/           # Lógica de negocio
│   ├── utils/             # Utilidades especializadas
│   │   ├── qr_processor.py    # Procesamiento QR
│   │   ├── file_handler.py    # Gestión de archivos
│   │   └── onedrive_sync.py   # Sincronización OneDrive
│   └── tests/             # Tests automatizados
├── storage/               # Almacenamiento local
├── templates/            # Plantillas Word
└── requirements.txt      # Dependencias Python
```

### Frontend (React/TypeScript)
```
frontend/
├── src/
│   ├── components/          # Componentes reutilizables
│   │   ├── common/         # Componentes base
│   │   ├── generator/      # Generación de documentos
│   │   ├── register/       # Registro de documentos
│   │   ├── search/         # Búsqueda y filtros
│   │   └── admin/          # Administración
│   ├── pages/              # Páginas principales
│   ├── services/           # Clientes API
│   ├── hooks/              # Hooks personalizados
│   ├── context/            # Estado global
│   └── utils/              # Utilidades frontend
├── public/                 # Archivos estáticos
└── package.json           # Dependencias Node.js
```

### Base de Datos (PostgreSQL)
```sql
-- Esquema principal con 4 tablas relacionadas:
users              # Usuarios integrados con Azure AD
document_types     # Tipos configurables de documentos  
qr_codes          # Códigos QR con ciclo de vida
documents         # Documentos principales con metadatos
```

## 🚀 Instalación y Configuración

### Prerrequisitos

1. **Docker y Docker Compose** (recomendado)
2. **Cuenta Microsoft 365 Business** con permisos de administrador
3. **Aplicación registrada en Azure AD** con permisos de Microsoft Graph
4. **OneDrive Business** configurado

### 1. Configuración de Azure AD

1. Accede al [Portal de Azure](https://portal.azure.com)
2. Ve a **Azure Active Directory** → **App registrations** → **New registration**
3. Configura la aplicación:
   ```
   Name: SGD Web Application
   Supported account types: Accounts in this organizational directory only
   Redirect URI: http://localhost:8000/api/v1/auth/microsoft/callback
   ```
4. Anota: **Application (client) ID**, **Directory (tenant) ID**
5. Ve a **Certificates & secrets** → **New client secret**
6. Anota el **Client Secret** (solo se muestra una vez)
7. Ve a **API permissions** → **Add a permission** → **Microsoft Graph**
8. Agregar permisos delegados:
   ```
   User.Read
   User.ReadBasic.All  
   Files.ReadWrite
   Sites.ReadWrite.All
   ```
9. **Grant admin consent** para los permisos

### 2. Instalación con Docker (Recomendado)

```bash
# Clonar repositorio
git clone 
cd sgd-web

# Configurar variables de entorno
cp .env.example .env
nano .env  # Editar con tus valores de Azure

# Levantar todo el stack
docker-compose up -d

# Verificar estado
docker-compose ps
```

### 3. Configuración Manual (Desarrollo)

#### Backend
```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos
createdb sgd_db
alembic upgrade head

# Ejecutar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend

# Instalar dependencias
npm install

# Ejecutar servidor de desarrollo
npm start
```

### 4. Variables de Entorno

Crear archivo `.env` basado en `.env.example`:

```bash
# === MICROSOFT 365 ===
MICROSOFT_CLIENT_ID=tu_client_id_de_azure
MICROSOFT_CLIENT_SECRET=tu_client_secret_de_azure  
MICROSOFT_TENANT_ID=tu_tenant_id_de_azure
MICROSOFT_REDIRECT_URI=http://localhost:8000/api/v1/auth/microsoft/callback

# === BASE DE DATOS ===
POSTGRES_SERVER=localhost
POSTGRES_USER=sgd_user
POSTGRES_PASSWORD=password_seguro_aqui
POSTGRES_DB=sgd_db
POSTGRES_PORT=5432

# === APLICACIÓN ===
SECRET_KEY=clave_super_secreta_para_jwt_tokens
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ENVIRONMENT=development

# === ONEDRIVE ===
ONEDRIVE_SYNC_PATH=/app/storage/documents
ONEDRIVE_ROOT_FOLDER=SGD_Documents

# === SEGURIDAD ===
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
ALLOWED_DOMAINS=["tuempresa.com","tudominio.co"]  # Opcional
ADMIN_EMAILS=["admin@tuempresa.com"]  # Administradores iniciales

# === ARCHIVOS ===
MAX_FILE_SIZE=52428800  # 50MB en bytes
```

## 📋 Uso del Sistema

### 1. Primer Acceso (Administrador)

1. Acceder a `http://localhost:3000`
2. Click en **"Iniciar Sesión con Microsoft"**
3. Autenticarse con cuenta corporativa
4. El sistema detectará automáticamente si eres administrador (basado en `ADMIN_EMAILS`)

### 2. Configuración Inicial

Como administrador, configura:

#### Tipos de Documento
```
1. Ve a Admin → Tipos de Documento
2. Crear nuevo tipo:
   - Código: GCO-REG-099
   - Nombre: Registro de Empleados  
   - Requiere QR: ✓
   - Campos obligatorios: Cédula, Nombre
   - Plantilla: subir archivo .docx
3. Configurar posición del QR en la plantilla
```

#### Usuarios y Permisos
```
1. Admin → Gestión de Usuarios
2. Asignar roles:
   - Admin: Acceso completo
   - Operador: Generar y registrar documentos
   - Viewer: Solo consultar
```

### 3. Flujo de Trabajo Típico

#### Generación de Documentos
```
1. Generator → Seleccionar tipo de documento
2. Llenar formulario con datos requeridos
3. Sistema genera:
   - Documento Word con datos llenos
   - Código QR único insertado
   - Documento guardado en OneDrive
   - Registro en base de datos
```

#### Registro de Documentos Existentes
```
1. Register → Subir archivo
2. Sistema extrae automáticamente:
   - Código QR (si existe)
   - Metadatos del archivo
   - Texto por OCR (futuro)
3. Validar y completar información
4. Guardar y sincronizar con OneDrive
```

#### Búsqueda y Consulta
```
1. Search → Usar filtros:
   - Por tipo de documento
   - Por cédula/nombre
   - Por fecha de creación
   - Por estado del documento
2. Ver documento en línea
3. Descargar desde OneDrive
4. Exportar resultados
```

## 🔧 Configuración Avanzada

### Personalización de Tipos de Documento

Cada tipo puede configurar:

```javascript
{
  "code": "CONT-EMP-001",
  "name": "Contrato de Empleado",
  "requirements": {
    "requires_qr": true,
    "requires_cedula": true,
    "requires_nombre": true,
    "requires_telefono": false,
    "requires_email": true,
    "requires_direccion": false
  },
  "file_config": {
    "allowed_file_types": ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
    "max_file_size_mb": 10,
    "allow_multiple_files": false
  },
  "workflow": {
    "requires_approval": true,
    "auto_notify_email": true,
    "notification_emails": ["rrhh@empresa.com"],
    "retention_days": 2555  // 7 años
  },
  "qr_config": {
    "qr_table_number": 1,
    "qr_row": 5,
    "qr_column": 1,
    "qr_width": 2,
    "qr_height": 2
  }
}
```

### Plantillas Word

Las plantillas deben:
1. Tener **tablas** donde insertar el QR
2. Usar **marcadores** para datos dinámicos: `{nombre}`, `{cedula}`, `{fecha}`
3. Estar en formato **.docx** (no .doc)

Ejemplo de tabla para QR:
```
| Campo 1    | Campo 2     |
|------------|-------------|
| Valor 1    | Valor 2     |
| QR se      | Otros datos |
| inserta    |             |
| aquí →     |             |
```

### OneDrive - Estructura de Carpetas

El sistema crea automáticamente:
```
OneDrive/
└── SGD_Documents/           # Carpeta raíz
    ├── GCO-REG-099/        # Por tipo de documento
    ├── CONT-EMP-001/
    ├── Templates/          # Plantillas compartidas
    ├── Exports/           # Exportaciones
    └── Backups/          # Respaldos automáticos
```

## 🛠️ Desarrollo y Contribución

### Estructura de Commits
```
feat: nueva funcionalidad
fix: corrección de bug  
docs: actualización documentación
style: formato de código
refactor: refactorización
test: agregar tests
chore: tareas de mantenimiento
```

### Testing
```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend tests  
cd frontend
npm test

# Integration tests
docker-compose -f docker-compose.test.yml up
```

### Agregar Nuevo Endpoint
```python
# 1. Crear esquema en schemas/
class MiNuevoSchema(BaseModel):
    campo: str

# 2. Crear endpoint en api/endpoints/
@router.post("/mi-endpoint", response_model=MiNuevoSchema)
async def mi_endpoint(data: MiNuevoSchema):
    return {"campo": "valor"}

# 3. Agregar al router en __init__.py
```

## 📊 Monitoreo y Logs

### Health Checks
```bash
# Verificar estado del sistema
curl http://localhost:8000/health

# Respuesta esperada:
{
  "status": "healthy",
  "version": "1.0.0",
  "checks": {
    "database": {"status": "healthy"},
    "storage": {"status": "healthy"}
  }
}
```

### Logs Importantes
```bash
# Ver logs del backend
docker-compose logs -f backend

# Ver logs específicos
grep "ERROR" logs/sgd_web.log
grep "microsoft_auth" logs/sgd_web.log
```

### Métricas de Uso
- Documentos generados por tipo
- Usuarios activos por período  
- Errores de sincronización OneDrive
- Códigos QR creados vs utilizados

## 🔒 Seguridad

### Mejores Prácticas Implementadas
- ✅ Autenticación JWT con expiración
- ✅ Validación de entrada con Pydantic
- ✅ CORS configurado por ambiente
- ✅ Rate limiting en endpoints críticos
- ✅ Sanitización de nombres de archivo
- ✅ Validación de tipos MIME
- ✅ Headers de seguridad HTTP
- ✅ Auditoría de acciones de usuario

### Configuración de Producción
```bash
# Variables adicionales para producción
ENVIRONMENT=production
SECRET_KEY=clave_super_compleja_y_unica
DEBUG=false
ALLOWED_HOSTS=["tudominio.com"]
SSL_REDIRECT=true
```

## 🚨 Troubleshooting

### Problemas Comunes

#### Error de Autenticación Microsoft
```bash
# Verificar configuración
echo $MICROSOFT_CLIENT_ID
echo $MICROSOFT_TENANT_ID

# Verificar permisos en Azure AD
# Verificar URL de redirect
```

#### OneDrive No Sincroniza
```bash
# Verificar token
curl -H "Authorization: Bearer $TOKEN" https://graph.microsoft.com/v1.0/me

# Verificar permisos Files.ReadWrite
# Verificar estructura de carpetas
```

#### Base de Datos
```bash
# Conectar y verificar
psql -h localhost -U sgd_user -d sgd_db

# Verificar migraciones
alembic current
alembic upgrade head
```

#### Códigos QR No Se Extraen
```bash
# Verificar dependencias
pip list | grep -E "(pyzbar|opencv|pillow)"

# Verificar archivos de prueba
python -c "from app.utils.qr_processor import get_qr_processor; print('QR Processor OK')"
```

## 📞 Soporte

### Información del Sistema
- **Versión**: 1.0.0
- **Python**: 3.11+
- **FastAPI**: 0.104+
- **PostgreSQL**: 15+
- **React**: 18+

### Documentación Adicional
- [API Documentation](http://localhost:8000/docs) (Swagger UI)
- [Microsoft Graph API](https://docs.microsoft.com/en-us/graph/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)

### Logs y Debugging
```bash
# Habilitar debug completo
export LOG_LEVEL=DEBUG
export DEBUG=true

# Ver logs en tiempo real
tail -f logs/sgd_web.log | grep ERROR
```

## 📄 Licencia

Copyright (c) 2024 Tu Empresa. Todos los derechos reservados.

Este software es propiedad de [Tu Empresa] y está protegido por las leyes de derechos de autor. El uso, distribución o modificación sin autorización expresa está prohibido.

---

## 🤝 Contribuciones

Para contribuir al desarrollo:

1. Fork del repositorio
2. Crear branch de feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit changes (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push to branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

---

**Desarrollado con ❤️ para la transformación digital empresarial**