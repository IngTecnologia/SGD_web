# Sistema de Gestión Documental Web

Sistema web para gestión de documentos con integración Microsoft 365, códigos QR y almacenamiento OneDrive.

## 🚀 Características

- Autenticación con Microsoft 365
- Generación de documentos con códigos QR
- Registro y clasificación de documentos
- Búsqueda avanzada
- Gestión de tipos de documento configurable
- Sincronización automática con OneDrive

## 🏗️ Arquitectura

- **Backend**: FastAPI + PostgreSQL
- **Frontend**: React + TypeScript
- **Autenticación**: Microsoft Graph API
- **Almacenamiento**: OneDrive Business

## 📦 Instalación

### Prerrequisitos
- Docker y Docker Compose
- Cuenta Microsoft 365 Business
- OneDrive sincronizado en el servidor

### Desarrollo
`ash
# Clonar repositorio
git clone <repo-url>
cd sgd-web

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# Levantar servicios
docker-compose -f docker-compose.dev.yml up
`

### Producción
`ash
docker-compose up -d
`

## 📝 Configuración

1. Registrar aplicación en Azure AD
2. Configurar permisos para Microsoft Graph
3. Configurar OneDrive Business
4. Configurar variables de entorno

## 🔧 Desarrollo

Ver documentación detallada en /docs/

## 📄 Licencia

Propiedad de [Tu Empresa]
