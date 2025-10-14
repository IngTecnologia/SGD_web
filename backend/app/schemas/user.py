"""
Esquemas Pydantic para Usuario
Validación y serialización de datos de usuario con integración Microsoft 365
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from ..models.user import UserRole, UserStatus


# === ESQUEMAS BASE ===

class UserBase(BaseModel):
    """Esquema base para usuario"""
    email: str = Field(..., description="Email corporativo del usuario")
    name: str = Field(..., min_length=2, max_length=200, description="Nombre completo")
    given_name: Optional[str] = Field(None, max_length=100, description="Nombre")
    surname: Optional[str] = Field(None, max_length=100, description="Apellido")
    display_name: Optional[str] = Field(None, max_length=200, description="Nombre para mostrar")

    # Información organizacional
    department: Optional[str] = Field(None, max_length=100, description="Departamento")
    job_title: Optional[str] = Field(None, max_length=100, description="Cargo")
    office_location: Optional[str] = Field(None, max_length=100, description="Ubicación de oficina")
    company_name: Optional[str] = Field(None, max_length=100, description="Nombre de empresa")

    # Información de contacto adicional
    phone: Optional[str] = Field(None, max_length=20, description="Teléfono de oficina")
    mobile_phone: Optional[str] = Field(None, max_length=20, description="Teléfono móvil")

    @validator('email')
    def validate_email_domain(cls, v):
        """Validar email permitiendo dominios .local para desarrollo"""
        if v:
            v = v.lower().strip()
            # Validación básica de formato email
            if '@' not in v or len(v.split('@')) != 2:
                raise ValueError('Email debe tener formato válido')
            local_part, domain = v.split('@')
            if not local_part or not domain:
                raise ValueError('Email debe tener formato válido')
        return v.lower() if v else v

    @validator('phone', 'mobile_phone')
    def validate_phone(cls, v):
        """Validar formato de teléfono básico"""
        if v:
            # Limpiar caracteres no numéricos excepto + y -
            import re
            cleaned = re.sub(r'[^\d\+\-\s\(\)]', '', v)
            if len(cleaned.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) < 7:
                raise ValueError('Teléfono debe tener al menos 7 dígitos')
            return cleaned
        return v


class UserCreate(UserBase):
    """Esquema para crear usuario"""
    azure_id: str = Field(..., description="ID único de Azure AD")
    role: UserRole = Field(default=UserRole.VIEWER, description="Rol del usuario")
    
    # Preferencias iniciales
    preferred_language: str = Field(default="es", max_length=10, description="Idioma preferido")
    timezone: str = Field(default="America/Bogota", max_length=50, description="Zona horaria")
    
    @validator('azure_id')
    def validate_azure_id(cls, v):
        """Validar formato del Azure ID"""
        if not v or len(v) < 10:
            raise ValueError('Azure ID debe ser válido')
        return v


class UserUpdate(BaseModel):
    """Esquema para actualizar usuario"""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    given_name: Optional[str] = Field(None, max_length=100)
    surname: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    
    # Información organizacional (actualizable por sync de M365)
    department: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    office_location: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, max_length=100)
    
    # Información de contacto
    phone: Optional[str] = Field(None, max_length=20)
    mobile_phone: Optional[str] = Field(None, max_length=20)
    
    # Preferencias (actualizables por el usuario)
    preferred_language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    email_notifications: Optional[bool] = Field(None)
    theme_preference: Optional[str] = Field(None, max_length=20)
    
    @validator('theme_preference')
    def validate_theme(cls, v):
        """Validar tema"""
        if v and v not in ['light', 'dark', 'auto']:
            raise ValueError('Tema debe ser: light, dark o auto')
        return v

    @validator('preferred_language')
    def validate_language(cls, v):
        """Validar código de idioma"""
        if v:
            valid_langs = ['es', 'en', 'fr', 'pt']  # Expandir según necesidades
            if v.lower() not in valid_langs:
                raise ValueError(f'Idioma debe ser uno de: {", ".join(valid_langs)}')
            return v.lower()
        return v


class UserAdminUpdate(UserUpdate):
    """Esquema para actualización por administrador"""
    role: Optional[UserRole] = Field(None, description="Rol del usuario")
    status: Optional[UserStatus] = Field(None, description="Estado del usuario")
    is_active: Optional[bool] = Field(None, description="Usuario activo")
    admin_notes: Optional[str] = Field(None, description="Notas del administrador")


# === ESQUEMAS DE RESPUESTA ===

class UserPermissions(BaseModel):
    """Esquema para permisos del usuario"""
    can_upload: bool = Field(description="Puede subir documentos")
    can_generate: bool = Field(description="Puede generar documentos")
    can_manage_types: bool = Field(description="Puede gestionar tipos de documento")
    can_manage_users: bool = Field(description="Puede gestionar usuarios")


class UserStats(BaseModel):
    """Esquema para estadísticas del usuario"""
    login_count: int = Field(default=0, description="Número de logins")
    documents_uploaded: int = Field(default=0, description="Documentos subidos")
    documents_generated: int = Field(default=0, description="Documentos generados")
    last_login: Optional[datetime] = Field(None, description="Último login")
    last_activity: Optional[datetime] = Field(None, description="Última actividad")


class User(UserBase):
    """Esquema completo de usuario para respuestas"""
    id: int = Field(description="ID único del usuario")
    azure_id: str = Field(description="ID de Azure AD")
    role: UserRole = Field(description="Rol del usuario")
    status: UserStatus = Field(description="Estado del usuario")
    is_active: bool = Field(description="Usuario activo")
    
    # Campos calculados
    full_name: str = Field(description="Nombre completo")
    initials: str = Field(description="Iniciales")
    
    # Preferencias
    preferred_language: str = Field(description="Idioma preferido")
    timezone: str = Field(description="Zona horaria")
    email_notifications: bool = Field(description="Notificaciones por email")
    theme_preference: str = Field(description="Tema preferido")
    
    # Permisos
    permissions: UserPermissions = Field(description="Permisos del usuario")
    
    # Estadísticas
    stats: UserStats = Field(description="Estadísticas del usuario")
    
    # Fechas
    first_login: Optional[datetime] = Field(None, description="Primer login")
    created_at: datetime = Field(description="Fecha de creación")
    updated_at: datetime = Field(description="Fecha de actualización")

    class Config:
        from_attributes = True


class UserSummary(BaseModel):
    """Esquema resumido de usuario para listas"""
    id: int
    email: str
    full_name: str
    initials: str
    role: UserRole
    status: UserStatus
    is_active: bool
    department: Optional[str] = None
    job_title: Optional[str] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserDetailed(User):
    """Esquema detallado para administradores"""
    admin_notes: Optional[str] = Field(None, description="Notas del administrador")
    
    # Información técnica
    last_token_issued: Optional[datetime] = Field(None, description="Último token emitido")
    
    class Config:
        from_attributes = True


# === ESQUEMAS PARA AUTENTICACIÓN ===

class UserLogin(BaseModel):
    """Esquema para datos de login"""
    email: EmailStr = Field(description="Email del usuario")
    microsoft_token: str = Field(description="Token de Microsoft")


class UserLocalLogin(BaseModel):
    """Esquema para login local (demo/desarrollo)"""
    email: str = Field(description="Email del usuario")
    password: str = Field(min_length=6, description="Contraseña del usuario")

    @validator('email')
    def validate_email(cls, v):
        """Validar email permitiendo dominios .local para desarrollo"""
        v = v.lower().strip()
        # Validación básica de formato email
        if '@' not in v or len(v.split('@')) != 2:
            raise ValueError('Email debe tener formato válido')
        local_part, domain = v.split('@')
        if not local_part or not domain:
            raise ValueError('Email debe tener formato válido')
        return v


class UserLoginResponse(BaseModel):
    """Esquema para respuesta de login"""
    user: User = Field(description="Datos del usuario")
    access_token: str = Field(description="Token de acceso")
    token_type: str = Field(default="bearer", description="Tipo de token")
    expires_in: int = Field(description="Expiración en segundos")


class UserMicrosoftData(BaseModel):
    """Esquema para datos de Microsoft Graph"""
    id: str = Field(description="ID de Azure AD")
    displayName: str = Field(description="Nombre para mostrar")
    givenName: Optional[str] = Field(None, description="Nombre")
    surname: Optional[str] = Field(None, description="Apellido")
    mail: Optional[str] = Field(None, description="Email principal")
    userPrincipalName: str = Field(description="UPN del usuario")
    
    # Información organizacional
    department: Optional[str] = Field(None, description="Departamento")
    jobTitle: Optional[str] = Field(None, description="Cargo")
    officeLocation: Optional[str] = Field(None, description="Ubicación")
    companyName: Optional[str] = Field(None, description="Empresa")
    
    # Información de contacto
    businessPhones: Optional[List[str]] = Field(None, description="Teléfonos de negocio")
    mobilePhone: Optional[str] = Field(None, description="Teléfono móvil")
    
    # Preferencias
    preferredLanguage: Optional[str] = Field(None, description="Idioma preferido")


# === ESQUEMAS PARA LISTADOS Y FILTROS ===

class UserFilter(BaseModel):
    """Esquema para filtros de búsqueda de usuarios"""
    search: Optional[str] = Field(None, description="Búsqueda por nombre o email")
    role: Optional[UserRole] = Field(None, description="Filtrar por rol")
    status: Optional[UserStatus] = Field(None, description="Filtrar por estado")
    is_active: Optional[bool] = Field(None, description="Filtrar por activo/inactivo")
    department: Optional[str] = Field(None, description="Filtrar por departamento")
    
    # Paginación
    page: int = Field(default=1, ge=1, description="Número de página")
    page_size: int = Field(default=20, ge=1, le=100, description="Tamaño de página")
    
    # Ordenamiento
    sort_by: str = Field(default="name", description="Campo para ordenar")
    sort_order: str = Field(default="asc", description="Orden: asc o desc")
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        """Validar campo de ordenamiento"""
        valid_fields = ['name', 'email', 'role', 'status', 'department', 'created_at', 'last_login']
        if v not in valid_fields:
            raise ValueError(f'sort_by debe ser uno de: {", ".join(valid_fields)}')
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        """Validar orden de clasificación"""
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('sort_order debe ser "asc" o "desc"')
        return v.lower()


class UserListResponse(BaseModel):
    """Esquema para respuesta de lista de usuarios"""
    users: List[UserSummary] = Field(description="Lista de usuarios")
    total: int = Field(description="Total de usuarios")
    page: int = Field(description="Página actual")
    page_size: int = Field(description="Tamaño de página")
    total_pages: int = Field(description="Total de páginas")


# === ESQUEMAS PARA OPERACIONES ADMINISTRATIVAS ===

class UserBulkAction(BaseModel):
    """Esquema para acciones en lote"""
    user_ids: List[int] = Field(..., description="IDs de usuarios")
    action: str = Field(..., description="Acción a realizar")
    reason: Optional[str] = Field(None, description="Razón de la acción")
    
    @validator('action')
    def validate_action(cls, v):
        """Validar acción"""
        valid_actions = ['activate', 'deactivate', 'suspend', 'change_role']
        if v not in valid_actions:
            raise ValueError(f'Acción debe ser una de: {", ".join(valid_actions)}')
        return v


class UserBulkActionResponse(BaseModel):
    """Esquema para respuesta de acción en lote"""
    success_count: int = Field(description="Usuarios procesados exitosamente")
    error_count: int = Field(description="Usuarios con errores")
    errors: List[Dict[str, Any]] = Field(description="Detalles de errores")


class UserActivityLog(BaseModel):
    """Esquema para log de actividad del usuario"""
    timestamp: datetime = Field(description="Fecha y hora")
    action: str = Field(description="Acción realizada")
    details: Dict[str, Any] = Field(description="Detalles de la acción")
    ip_address: Optional[str] = Field(None, description="Dirección IP")
    user_agent: Optional[str] = Field(None, description="User agent")


# === ESQUEMAS PARA EXPORTACIÓN ===

class UserExport(BaseModel):
    """Esquema para exportación de usuarios"""
    id: int
    azure_id: str
    email: str
    name: str
    department: Optional[str] = None
    job_title: Optional[str] = None
    role: str
    status: str
    is_active: bool
    login_count: int
    documents_uploaded: int
    documents_generated: int
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True