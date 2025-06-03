"""
Endpoints de la API SGD Web
Centraliza todos los routers de endpoints
"""

from .auth import router as auth_router
from .documents import router as documents_router
from .document_types import router as document_types_router
from .generator import router as generator_router
from .search import router as search_router
from .qr_codes import router as qr_codes_router
from .users import router as users_router

# Lista de todos los routers disponibles
__all__ = [
    "auth_router",
    "documents_router", 
    "document_types_router",
    "generator_router",
    "search_router",
    "qr_codes_router",
    "users_router"
]

# Configuración de routers con sus prefijos y tags
ROUTER_CONFIG = {
    "auth": {
        "router": auth_router,
        "prefix": "/auth",
        "tags": ["Autenticación"],
        "include_in_schema": True
    },
    "documents": {
        "router": documents_router,
        "prefix": "/documents", 
        "tags": ["Documentos"],
        "include_in_schema": True
    },
    "document_types": {
        "router": document_types_router,
        "prefix": "/document-types",
        "tags": ["Tipos de Documento"],
        "include_in_schema": True
    },
    "generator": {
        "router": generator_router,
        "prefix": "/generator",
        "tags": ["Generador"],
        "include_in_schema": True
    },
    "search": {
        "router": search_router,
        "prefix": "/search",
        "tags": ["Búsqueda"],
        "include_in_schema": True
    },
    "qr_codes": {
        "router": qr_codes_router,
        "prefix": "/qr-codes",
        "tags": ["Códigos QR"],
        "include_in_schema": True
    },
    "users": {
        "router": users_router,
        "prefix": "/users",
        "tags": ["Usuarios"],
        "include_in_schema": True
    }
}

def get_router_config():
    """Obtener configuración de routers"""
    return ROUTER_CONFIG

def get_all_routers():
    """Obtener todos los routers configurados"""
    return [config["router"] for config in ROUTER_CONFIG.values()]