"""
Dependencias compartidas para endpoints de SGD Web
Autenticación, autorización y utilidades comunes
"""
import logging
from typing import Generator, Optional, List, Any
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status, Request, Query, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from ..database import get_db
from ..config import get_settings
from ..models.user import User, UserRole, UserStatus
from ..models.document_type import DocumentType
from ..models.document import Document
from ..models.qr_code import QRCode
from ..schemas.user import UserPermissions

# Configuración
settings = get_settings()
logger = logging.getLogger(__name__)

# Esquema de autenticación
security = HTTPBearer(auto_error=False)


# === DEPENDENCIAS DE BASE DE DATOS ===

def get_database() -> Generator[Session, None, None]:
    """
    Dependencia para obtener sesión de base de datos
    """
    yield from get_db()


# === DEPENDENCIAS DE AUTENTICACIÓN ===

def verify_token(token: str) -> dict:
    """
    Verificar y decodificar token JWT
    
    Args:
        token: Token JWT
        
    Returns:
        dict: Payload del token decodificado
        
    Raises:
        HTTPException: Si el token es inválido
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Verificar expiración
        exp = payload.get("exp")
        if exp is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token sin fecha de expiración",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar si ha expirado
        if datetime.utcnow().timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
        
    except JWTError as e:
        logger.warning(f"Error decodificando token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_database)
) -> User:
    """
    Obtener usuario actual desde token JWT
    
    Args:
        credentials: Credenciales del header Authorization
        db: Sesión de base de datos
        
    Returns:
        User: Usuario autenticado
        
    Raises:
        HTTPException: Si no hay token o el usuario no existe
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autorización requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar token
    payload = verify_token(credentials.credentials)
    
    # Obtener ID del usuario del payload
    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: ID de usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Buscar usuario en base de datos
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar que el usuario esté activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario desactivado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar estado del usuario
    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario suspendido",
        )
    
    # Actualizar última actividad
    user.update_activity()
    db.commit()
    
    return user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_database)
) -> Optional[User]:
    """
    Obtener usuario actual de manera opcional
    No falla si no hay token, útil para endpoints públicos con funcionalidad extra para usuarios autenticados
    
    Args:
        credentials: Credenciales del header Authorization
        db: Sesión de base de datos
        
    Returns:
        Optional[User]: Usuario autenticado o None
    """
    if not credentials:
        return None
    
    try:
        return get_current_user_from_token(credentials, db)
    except HTTPException:
        return None


# Alias para mayor claridad
get_current_user = get_current_user_from_token


# === DEPENDENCIAS DE AUTORIZACIÓN ===

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Requerir que el usuario sea administrador
    
    Args:
        current_user: Usuario actual
        
    Returns:
        User: Usuario administrador
        
    Raises:
        HTTPException: Si el usuario no es administrador
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permisos de administrador requeridos"
        )
    return current_user


def require_operator_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Requerir que el usuario sea operador o administrador
    
    Args:
        current_user: Usuario actual
        
    Returns:
        User: Usuario con permisos de operador o superior
        
    Raises:
        HTTPException: Si el usuario no tiene permisos suficientes
    """
    if not current_user.is_operator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permisos de operador o administrador requeridos"
        )
    return current_user


def check_permission(permission: str):
    """
    Factory para crear dependencias de permisos específicos
    
    Args:
        permission: Nombre del permiso a verificar
        
    Returns:
        function: Función de dependencia
    """
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        user_permissions = {
            "can_upload": current_user.can_upload,
            "can_generate": current_user.can_generate,
            "can_manage_types": current_user.can_manage_types,
            "can_manage_users": current_user.can_manage_users,
        }
        
        if not user_permissions.get(permission, False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso '{permission}' requerido"
            )
        return current_user
    
    return permission_checker


# Dependencias específicas
require_upload_permission = check_permission("can_upload")
require_generate_permission = check_permission("can_generate")
require_manage_types_permission = check_permission("can_manage_types")
require_manage_users_permission = check_permission("can_manage_users")


# === DEPENDENCIAS DE RECURSOS ===

def get_document_type_by_id(
    document_type_id: int = Path(..., description="ID del tipo de documento"),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
) -> DocumentType:
    """
    Obtener tipo de documento por ID
    
    Args:
        document_type_id: ID del tipo de documento
        db: Sesión de base de datos
        current_user: Usuario actual
        
    Returns:
        DocumentType: Tipo de documento encontrado
        
    Raises:
        HTTPException: Si el tipo no existe o no tiene acceso
    """
    document_type = db.query(DocumentType).filter(
        DocumentType.id == document_type_id
    ).first()
    
    if not document_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de documento no encontrado"
        )
    
    # Verificar si está activo (solo admins pueden ver inactivos)
    if not document_type.is_active and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de documento no encontrado"
        )
    
    return document_type


def get_document_by_id(
    document_id: int = Path(..., description="ID del documento"),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
) -> Document:
    """
    Obtener documento por ID con verificación de acceso
    
    Args:
        document_id: ID del documento
        db: Sesión de base de datos
        current_user: Usuario actual
        
    Returns:
        Document: Documento encontrado
        
    Raises:
        HTTPException: Si el documento no existe o no tiene acceso
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )
    
    # Verificar acceso según nivel de confidencialidad
    if document.is_confidential:
        # Solo admins y el usuario que subió el documento pueden ver confidenciales
        if not (current_user.is_admin or document.uploaded_by == current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para acceder a este documento"
            )
    
    # Verificar estado del documento
    if document.status == "deleted" and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )
    
    # Marcar como visto
    document.mark_as_viewed(current_user.id)
    db.commit()
    
    return document


def get_qr_code_by_id(
    qr_id: str = Path(..., description="ID del código QR"),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
) -> QRCode:
    """
    Obtener código QR por ID
    
    Args:
        qr_id: ID del código QR
        db: Sesión de base de datos
        current_user: Usuario actual
        
    Returns:
        QRCode: Código QR encontrado
        
    Raises:
        HTTPException: Si el QR no existe o no tiene acceso
    """
    qr_code = db.query(QRCode).filter(QRCode.qr_id == qr_id).first()
    
    if not qr_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código QR no encontrado"
        )
    
    # Solo admins y el usuario que generó el QR pueden verlo
    if not (current_user.is_admin or qr_code.generated_by == current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a este código QR"
        )
    
    return qr_code


def get_user_by_id(
    user_id: int = Path(..., description="ID del usuario"),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Obtener usuario por ID (solo para admins o el mismo usuario)
    
    Args:
        user_id: ID del usuario
        db: Sesión de base de datos
        current_user: Usuario actual
        
    Returns:
        User: Usuario encontrado
        
    Raises:
        HTTPException: Si el usuario no existe o no tiene acceso
    """
    # Solo admins pueden ver otros usuarios, o el usuario puede verse a sí mismo
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a la información de este usuario"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return user


# === DEPENDENCIAS DE PAGINACIÓN ===

class PaginationParams:
    """Parámetros de paginación comunes"""
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Número de página"),
        page_size: int = Query(20, ge=1, le=100, description="Elementos por página"),
        sort_by: str = Query("created_at", description="Campo para ordenar"),
        sort_order: str = Query("desc", regex="^(asc|desc)$", description="Orden de clasificación")
    ):
        self.page = page
        self.page_size = page_size
        self.sort_by = sort_by
        self.sort_order = sort_order
        
    @property
    def offset(self) -> int:
        """Calcular offset para la consulta"""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Límite para la consulta"""
        return self.page_size


def get_pagination_params() -> PaginationParams:
    """Dependencia para parámetros de paginación"""
    return Depends(PaginationParams)


# === DEPENDENCIAS DE FILTROS ===

class DateRangeFilter:
    """Filtro de rango de fechas"""
    def __init__(
        self,
        start_date: Optional[datetime] = Query(None, description="Fecha de inicio"),
        end_date: Optional[datetime] = Query(None, description="Fecha de fin")
    ):
        self.start_date = start_date
        self.end_date = end_date
        
        # Validar que start_date sea anterior a end_date
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha de inicio debe ser anterior a la fecha de fin"
            )


def get_date_range_filter() -> DateRangeFilter:
    """Dependencia para filtro de rango de fechas"""
    return Depends(DateRangeFilter)


# === DEPENDENCIAS DE VALIDACIÓN ===

def validate_file_upload():
    """
    Validador para subida de archivos
    """
    def validator(request: Request) -> dict:
        # Verificar Content-Type
        content_type = request.headers.get("content-type", "")
        if not content_type.startswith("multipart/form-data"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content-Type debe ser multipart/form-data"
            )
        
        # Verificar tamaño de la request
        content_length = request.headers.get("content-length")
        if content_length:
            size = int(content_length)
            max_size = settings.MAX_FILE_SIZE * 2  # Allowance for form data overhead
            if size > max_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Archivo demasiado grande. Máximo: {settings.MAX_FILE_SIZE // (1024*1024)}MB"
                )
        
        return {"validated": True}
    
    return validator


# === DEPENDENCIAS DE LOGGING ===

def get_request_logger(request: Request):
    """
    Dependencia para logging específico del request
    """
    def log_action(action: str, details: dict = None, level: str = "info"):
        """
        Log de acción del usuario
        
        Args:
            action: Acción realizada
            details: Detalles adicionales
            level: Nivel de log
        """
        log_data = {
            "action": action,
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "path": str(request.url.path),
            "method": request.method,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if details:
            log_data.update(details)
        
        log_method = getattr(logger, level, logger.info)
        log_method(f"User action: {action}", extra=log_data)
    
    return log_action


# === DEPENDENCIAS DE CACHE ===

def get_cache_key(prefix: str, *args) -> str:
    """
    Generar clave de cache
    
    Args:
        prefix: Prefijo de la clave
        *args: Argumentos adicionales para la clave
        
    Returns:
        str: Clave de cache
    """
    key_parts = [prefix] + [str(arg) for arg in args]
    return ":".join(key_parts)


# === DEPENDENCIAS DE RATE LIMITING ===

class RateLimiter:
    """Simple rate limiter en memoria"""
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """
        Verificar si la request está permitida
        
        Args:
            key: Clave única para el rate limiting
            limit: Número máximo de requests
            window: Ventana de tiempo en segundos
            
        Returns:
            bool: True si está permitida
        """
        now = datetime.utcnow()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Limpiar requests antiguas
        cutoff = now - timedelta(seconds=window)
        self.requests[key] = [
            req_time for req_time in self.requests[key] 
            if req_time > cutoff
        ]
        
        # Verificar límite
        if len(self.requests[key]) >= limit:
            return False
        
        # Agregar request actual
        self.requests[key].append(now)
        return True


# Instancia global del rate limiter
rate_limiter = RateLimiter()


def create_rate_limit_dependency(limit: int, window: int = 60):
    """
    Factory para crear dependencias de rate limiting
    
    Args:
        limit: Número máximo de requests
        window: Ventana de tiempo en segundos
        
    Returns:
        function: Función de dependencia
    """
    def rate_limit_checker(
        request: Request,
        current_user: User = Depends(get_current_user)
    ):
        # Usar IP + user ID como clave
        key = f"{request.client.host}:{current_user.id}"
        
        if not rate_limiter.is_allowed(key, limit, window):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Demasiadas requests. Límite: {limit} por {window} segundos"
            )
        
        return True
    
    return rate_limit_checker


# === DEPENDENCIAS ESPECÍFICAS DE ENDPOINTS ===

def verify_document_ownership_or_admin(
    document: Document = Depends(get_document_by_id),
    current_user: User = Depends(get_current_user)
) -> Document:
    """
    Verificar que el usuario sea dueño del documento o administrador
    
    Args:
        document: Documento a verificar
        current_user: Usuario actual
        
    Returns:
        Document: Documento verificado
        
    Raises:
        HTTPException: Si no tiene permisos
    """
    if not (current_user.is_admin or document.uploaded_by == current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para modificar este documento"
        )
    
    return document


def verify_qr_ownership_or_admin(
    qr_code: QRCode = Depends(get_qr_code_by_id),
    current_user: User = Depends(get_current_user)
) -> QRCode:
    """
    Verificar que el usuario sea dueño del QR o administrador
    
    Args:
        qr_code: Código QR a verificar
        current_user: Usuario actual
        
    Returns:
        QRCode: Código QR verificado
        
    Raises:
        HTTPException: Si no tiene permisos
    """
    if not (current_user.is_admin or qr_code.generated_by == current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para modificar este código QR"
        )
    
    return qr_code