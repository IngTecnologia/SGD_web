"""
Configuración de la aplicación SGD Web
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """Configuración principal de la aplicación"""
    
    # === CONFIGURACIÓN DE LA APLICACIÓN ===
    PROJECT_NAME: str = "SGD Web"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Sistema de Gestión Documental Web con Microsoft 365"
    
    # Configuración del servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # === CONFIGURACIÓN DE BASE DE DATOS ===
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "sgd_user"
    POSTGRES_PASSWORD: str = "sgd_password"
    POSTGRES_DB: str = "sgd_db"
    POSTGRES_PORT: int = 5432
    
    @property
    def DATABASE_URL(self) -> str:
        """URL de conexión a PostgreSQL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # === CONFIGURACIÓN DE MICROSOFT 365 ===
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_TENANT_ID: Optional[str] = None
    MICROSOFT_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/microsoft/callback"
    
    # Scopes requeridos para Microsoft Graph
    MICROSOFT_SCOPES: List[str] = [
        "User.Read",
        "User.ReadBasic.All",
        "Files.ReadWrite",
        "Sites.ReadWrite.All"
    ]
    
    # Dominio corporativo permitido (opcional, para restringir acceso)
    ALLOWED_DOMAINS: Optional[List[str]] = None
    
    @validator('ALLOWED_DOMAINS', pre=True)
    def parse_allowed_domains(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, str):
            domains = [domain.strip() for domain in v.split(',') if domain.strip()]
            return domains if domains else None
        return v
    
    # === CONFIGURACIÓN DE SEGURIDAD ===
    SECRET_KEY: str = "sgd-web-super-secret-key-change-in-production-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 horas
    
    # === CONFIGURACIÓN DE CORS ===
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
    ]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, str):
            # Try to parse as JSON first
            import json
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                pass
            # If not JSON, treat as comma-separated
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        raise ValueError(f"Invalid value for BACKEND_CORS_ORIGINS: {v}")
    
    # === CONFIGURACIÓN DE ALMACENAMIENTO ===
    # Carpeta local donde se almacenan los documentos
    STORAGE_PATH: str = "/app/storage"
    DOCUMENTS_PATH: str = "/app/storage/documents"
    TEMP_PATH: str = "/app/storage/temp"
    TEMPLATES_PATH: str = "/app/templates"
    
    # OneDrive configuración
    ONEDRIVE_SYNC_PATH: str = "/app/storage/documents"
    ONEDRIVE_ROOT_FOLDER: str = "SGD_Documents"
    
    # === CONFIGURACIÓN DE ARCHIVOS ===
    # Tamaño máximo de archivo en bytes (50MB por defecto)
    MAX_FILE_SIZE: int = 50 * 1024 * 1024
    
    # Tipos de archivo permitidos
    ALLOWED_FILE_TYPES: List[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/jpg",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
        "application/msword",  # .doc
    ]
    
    # Extensiones permitidas
    ALLOWED_FILE_EXTENSIONS: List[str] = [
        ".pdf", ".jpg", ".jpeg", ".png", ".docx", ".doc"
    ]
    
    # === CONFIGURACIÓN DE QR ===
    # Configuración para generación de códigos QR
    QR_VERSION: int = 1
    QR_ERROR_CORRECTION: str = "L"  # L, M, Q, H
    QR_BOX_SIZE: int = 10
    QR_BORDER: int = 4
    
    # === CONFIGURACIÓN DE LOGS ===
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # === CONFIGURACIÓN DE PAGINACIÓN ===
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # === CONFIGURACIÓN DE CACHE ===
    CACHE_TTL: int = 300  # 5 minutos en segundos
    
    # === CONFIGURACIÓN DE ROLES ===
    DEFAULT_USER_ROLE: str = "viewer"
    ADMIN_EMAILS_STR: Optional[str] = None  # Emails de admin separados por comas

    @property
    def ADMIN_EMAILS(self) -> List[str]:
        """Parse admin emails from comma-separated string"""
        if not self.ADMIN_EMAILS_STR or self.ADMIN_EMAILS_STR == "":
            return []
        if isinstance(self.ADMIN_EMAILS_STR, str):
            emails = [email.strip().lower() for email in self.ADMIN_EMAILS_STR.split(',') if email.strip()]
            return emails if emails else []
        return []
    
    # === CONFIGURACIÓN DE AUTENTICACIÓN LOCAL ===
    LOCAL_AUTH_ENABLED: bool = True
    DEMO_MODE: bool = True
    
    # Usuarios demo para desarrollo
    DEMO_ADMIN_EMAIL: str = "admin@sgd-web.local"
    DEMO_ADMIN_NAME: str = "Administrador SGD"
    DEMO_ADMIN_PASSWORD: str = "admin123"
    
    DEMO_OPERATOR_EMAIL: str = "operator@sgd-web.local"
    DEMO_OPERATOR_NAME: str = "Operador SGD"
    DEMO_OPERATOR_PASSWORD: str = "operator123"
    
    DEMO_VIEWER_EMAIL: str = "viewer@sgd-web.local"
    DEMO_VIEWER_NAME: str = "Visualizador SGD"
    DEMO_VIEWER_PASSWORD: str = "viewer123"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignorar variables de entorno que no están definidas en el modelo


# Instancia global de configuración
settings = Settings()


def get_settings() -> Settings:
    """Obtener la configuración de la aplicación"""
    return settings


# Configuraciones específicas por ambiente
def get_database_url() -> str:
    """Obtener URL de base de datos"""
    return settings.DATABASE_URL


def is_development() -> bool:
    """Verificar si estamos en desarrollo"""
    return settings.ENVIRONMENT.lower() == "development"


def is_production() -> bool:
    """Verificar si estamos en producción"""
    return settings.ENVIRONMENT.lower() == "production"


def get_cors_origins() -> List[str]:
    """Obtener orígenes permitidos para CORS"""
    return settings.BACKEND_CORS_ORIGINS