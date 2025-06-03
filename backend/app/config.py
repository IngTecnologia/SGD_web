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
    MICROSOFT_CLIENT_ID: str
    MICROSOFT_CLIENT_SECRET: str
    MICROSOFT_TENANT_ID: str
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
        if isinstance(v, str):
            return [domain.strip() for domain in v.split(',') if domain.strip()]
        return v
    
    # === CONFIGURACIÓN DE SEGURIDAD ===
    SECRET_KEY: str
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
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
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
    ADMIN_EMAILS: List[str] = []  # Emails que tendrán rol de admin automáticamente
    
    @validator('ADMIN_EMAILS', pre=True)
    def parse_admin_emails(cls, v):
        if isinstance(v, str):
            return [email.strip().lower() for email in v.split(',') if email.strip()]
        return [email.lower() for email in v] if v else []
    
    class Config:
        env_file = ".env"
        case_sensitive = True


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