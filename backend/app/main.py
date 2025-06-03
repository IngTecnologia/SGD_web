"""
Aplicación principal de SGD Web
FastAPI con integración Microsoft 365 y gestión documental
"""
import os
import sys
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

import uvicorn
from sqlalchemy.exc import SQLAlchemyError

# Importaciones locales
from .config import get_settings, is_development, is_production
from .database import get_db, check_database_connection, database_health_check
from .models import initialize_models

# Importar routers de endpoints
from .api.endpoints import (
    auth as auth_router,
    documents as documents_router,
    document_types as document_types_router,
    generator as generator_router,
    search as search_router,
)

# Configuración
settings = get_settings()

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format=settings.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/sgd_web.log') if os.path.exists('logs') else logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida de la aplicación
    Se ejecuta al iniciar y cerrar la aplicación
    """
    # === STARTUP ===
    logger.info("🚀 Iniciando SGD Web...")
    
    try:
        # Verificar conexión a base de datos
        logger.info("📊 Verificando conexión a base de datos...")
        if not check_database_connection():
            logger.error("❌ No se pudo conectar a la base de datos")
            raise Exception("Error de conexión a base de datos")
        logger.info("✅ Conexión a base de datos exitosa")
        
        # Inicializar modelos
        logger.info("📋 Inicializando modelos...")
        if not initialize_models():
            logger.error("❌ Error inicializando modelos")
            raise Exception("Error inicializando modelos")
        logger.info("✅ Modelos inicializados correctamente")
        
        # Verificar estructura de carpetas
        logger.info("📁 Verificando estructura de almacenamiento...")
        os.makedirs(settings.DOCUMENTS_PATH, exist_ok=True)
        os.makedirs(settings.TEMP_PATH, exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        logger.info("✅ Estructura de carpetas verificada")
        
        # Configurar aplicación
        app.state.startup_time = datetime.utcnow()
        app.state.version = settings.VERSION
        app.state.environment = settings.ENVIRONMENT
        
        logger.info(f"🎉 SGD Web v{settings.VERSION} iniciado exitosamente")
        logger.info(f"🌍 Ambiente: {settings.ENVIRONMENT}")
        logger.info(f"🏠 Host: {settings.HOST}:{settings.PORT}")
        
    except Exception as e:
        logger.error(f"💥 Error durante el startup: {str(e)}")
        raise
    
    yield
    
    # === SHUTDOWN ===
    logger.info("🛑 Cerrando SGD Web...")
    logger.info("✅ SGD Web cerrado correctamente")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    openapi_url="/api/v1/openapi.json" if is_development() else None,
    docs_url=None,  # Configuraremos documentación personalizada
    redoc_url=None,
    lifespan=lifespan,
)

# === MIDDLEWARES ===

# CORS - Configurar según ambiente
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page-Count"],
)

# Compresión GZIP
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted hosts (solo en producción)
if is_production():
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]  # Configurar según dominio
    )


# === MIDDLEWARE PERSONALIZADO ===

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Agregar headers de seguridad"""
    response = await call_next(request)
    
    # Headers de seguridad
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    if is_production():
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Logging de requests"""
    start_time = datetime.utcnow()
    
    # Log del request
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    logger.info(
        f"📥 {request.method} {request.url.path} - "
        f"IP: {client_ip} - UA: {user_agent[:50]}..."
    )
    
    try:
        response = await call_next(request)
        
        # Calcular tiempo de procesamiento
        process_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Agregar header de tiempo de respuesta
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log de respuesta
        logger.info(
            f"📤 {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Time: {process_time:.3f}s"
        )
        
        return response
        
    except Exception as e:
        process_time = (datetime.utcnow() - start_time).total_seconds()
        logger.error(
            f"💥 {request.method} {request.url.path} - "
            f"Error: {str(e)} - Time: {process_time:.3f}s"
        )
        raise


@app.middleware("http")
async def database_session_middleware(request: Request, call_next):
    """Middleware para manejo de sesiones de base de datos"""
    response = Response("Internal server error", status_code=500)
    
    try:
        response = await call_next(request)
    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos: {str(e)}")
        response = JSONResponse(
            status_code=500,
            content={"detail": "Error de base de datos"}
        )
    except Exception as e:
        logger.error(f"Error no manejado: {str(e)}")
        response = JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor"}
        )
    
    return response


# === RUTAS PRINCIPALES ===

@app.get("/", include_in_schema=False)
async def root():
    """Redirigir a documentación en desarrollo"""
    if is_development():
        return RedirectResponse(url="/docs")
    return {
        "message": f"SGD Web API v{settings.VERSION}",
        "environment": settings.ENVIRONMENT,
        "status": "running"
    }


@app.get("/health", tags=["Sistema"])
async def health_check():
    """
    Health check de la aplicación
    Verifica estado de base de datos y servicios críticos
    """
    try:
        # Verificar base de datos
        db_health = await database_health_check()
        
        # Verificar almacenamiento
        storage_health = {
            "documents_path_exists": os.path.exists(settings.DOCUMENTS_PATH),
            "temp_path_exists": os.path.exists(settings.TEMP_PATH),
            "documents_path_writable": os.access(settings.DOCUMENTS_PATH, os.W_OK),
            "temp_path_writable": os.access(settings.TEMP_PATH, os.W_OK),
        }
        
        # Estado general
        overall_status = (
            db_health["status"] == "healthy" and
            all(storage_health.values())
        )
        
        return {
            "status": "healthy" if overall_status else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "uptime_seconds": (datetime.utcnow() - app.state.startup_time).total_seconds(),
            "checks": {
                "database": db_health,
                "storage": storage_health,
            }
        }
        
    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )


@app.get("/info", tags=["Sistema"])
async def app_info():
    """
    Información de la aplicación
    """
    return {
        "name": settings.PROJECT_NAME,
        "description": settings.DESCRIPTION,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "startup_time": app.state.startup_time.isoformat(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "features": {
            "microsoft_365_integration": True,
            "qr_code_processing": True,
            "document_generation": True,
            "onedrive_sync": True,
            "batch_operations": True,
        },
        "api": {
            "docs_url": "/docs" if is_development() else None,
            "openapi_url": "/api/v1/openapi.json" if is_development() else None,
        }
    }


# === DOCUMENTACIÓN PERSONALIZADA ===

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Documentación Swagger personalizada"""
    if not is_development():
        raise HTTPException(status_code=404, detail="Not found")
    
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Documentación",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """Documentación ReDoc personalizada"""
    if not is_development():
        raise HTTPException(status_code=404, detail="Not found")
    
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Documentación",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js",
        redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )


def custom_openapi():
    """OpenAPI schema personalizado"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Personalizar schema
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    # Agregar información de seguridad
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Token JWT obtenido del login con Microsoft 365"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# === INCLUIR ROUTERS ===

# Prefijo base para API
API_V1_PREFIX = "/api/v1"

# Autenticación (sin prefijo adicional)
app.include_router(
    auth_router.router,
    prefix=f"{API_V1_PREFIX}/auth",
    tags=["Autenticación"],
)

# Gestión de documentos
app.include_router(
    documents_router.router,
    prefix=f"{API_V1_PREFIX}/documents",
    tags=["Documentos"],
)

# Tipos de documento
app.include_router(
    document_types_router.router,
    prefix=f"{API_V1_PREFIX}/document-types",
    tags=["Tipos de Documento"],
)

# Generador de documentos
app.include_router(
    generator_router.router,
    prefix=f"{API_V1_PREFIX}/generator",
    tags=["Generador"],
)

# Búsqueda de documentos
app.include_router(
    search_router.router,
    prefix=f"{API_V1_PREFIX}/search",
    tags=["Búsqueda"],
)


# === ARCHIVOS ESTÁTICOS ===

# Servir archivos estáticos en desarrollo
if is_development():
    if os.path.exists("static"):
        app.mount("/static", StaticFiles(directory="static"), name="static")


# === MANEJO DE ERRORES GLOBAL ===

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Manejo personalizado de 404"""
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Recurso no encontrado",
            "path": str(request.url.path),
            "method": request.method,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Manejo personalizado de errores internos"""
    logger.error(f"Error interno: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Error interno del servidor",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request.headers.get("X-Request-ID", "unknown")
        }
    )


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, exc: SQLAlchemyError):
    """Manejo de errores de base de datos"""
    logger.error(f"Error de base de datos: {str(exc)}")
    
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Error de base de datos - Servicio temporalmente no disponible",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# === FUNCIONES DE UTILIDAD ===

def create_app() -> FastAPI:
    """
    Factory function para crear la aplicación
    Útil para testing y deployments
    """
    return app


def get_application() -> FastAPI:
    """
    Obtener la instancia de la aplicación
    """
    return app


# === FUNCIÓN PRINCIPAL ===

def main():
    """Función principal para ejecutar la aplicación"""
    try:
        # Configuración según ambiente
        if is_development():
            # Desarrollo con recarga automática
            uvicorn.run(
                "app.main:app",
                host=settings.HOST,
                port=settings.PORT,
                reload=True,
                reload_dirs=["app"],
                log_level=settings.LOG_LEVEL.lower(),
                access_log=True,
            )
        else:
            # Producción
            uvicorn.run(
                app,
                host=settings.HOST,
                port=settings.PORT,
                log_level=settings.LOG_LEVEL.lower(),
                access_log=True,
                workers=1,  # Para producción usar Gunicorn
            )
            
    except KeyboardInterrupt:
        logger.info("🛑 Aplicación interrumpida por el usuario")
    except Exception as e:
        logger.error(f"💥 Error fatal: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()