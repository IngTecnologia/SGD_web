"""
Servicio de autenticación y autorización
Gestión de tokens, permisos y seguridad
"""
import logging
import secrets
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models.user import User, UserRole, UserStatus
from ..schemas.user import UserCreate, UserMicrosoftData

# Configuración
settings = get_settings()
logger = logging.getLogger(__name__)

# Contexto para hashing de passwords (aunque usamos Microsoft OAuth)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthenticationError(Exception):
    """Excepción para errores de autenticación"""
    pass


class AuthorizationError(Exception):
    """Excepción para errores de autorización"""
    pass


class AuthService:
    """
    Servicio principal de autenticación y autorización
    """
    
    def __init__(self):
        """Inicializar el servicio de autenticación"""
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        
        # Cache de tokens revocados (en producción usar Redis)
        self._revoked_tokens = set()
        
        logger.info("AuthService inicializado")
    
    # === GESTIÓN DE TOKENS JWT ===
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Crear token JWT de acceso
        
        Args:
            data: Datos a incluir en el token (típicamente user_id)
            expires_delta: Tiempo de expiración personalizado
            
        Returns:
            str: Token JWT codificado
        """
        try:
            to_encode = data.copy()
            
            # Configurar expiración
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            
            # Agregar claims estándar
            to_encode.update({
                "exp": expire,
                "iat": datetime.utcnow(),
                "type": "access_token",
                "jti": secrets.token_urlsafe(16)  # JWT ID único
            })
            
            # Codificar token
            encoded_jwt = jwt.encode(
                to_encode, 
                self.secret_key, 
                algorithm=self.algorithm
            )
            
            logger.debug(f"Token de acceso creado para datos: {data}")
            return encoded_jwt
            
        except Exception as e:
            logger.error(f"Error creando token de acceso: {str(e)}")
            raise AuthenticationError(f"Error creando token: {str(e)}")
    
    def create_refresh_token(
        self, 
        user_id: int, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Crear token de refresh (para renovar access tokens)
        
        Args:
            user_id: ID del usuario
            expires_delta: Tiempo de expiración (por defecto 7 días)
            
        Returns:
            str: Token de refresh
        """
        try:
            if not expires_delta:
                expires_delta = timedelta(days=7)
            
            expire = datetime.utcnow() + expires_delta
            
            to_encode = {
                "sub": user_id,
                "exp": expire,
                "iat": datetime.utcnow(),
                "type": "refresh_token",
                "jti": secrets.token_urlsafe(16)
            }
            
            encoded_jwt = jwt.encode(
                to_encode,
                self.secret_key,
                algorithm=self.algorithm
            )
            
            logger.debug(f"Token de refresh creado para usuario: {user_id}")
            return encoded_jwt
            
        except Exception as e:
            logger.error(f"Error creando refresh token: {str(e)}")
            raise AuthenticationError(f"Error creando refresh token: {str(e)}")
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verificar y decodificar token JWT
        
        Args:
            token: Token JWT a verificar
            
        Returns:
            dict: Payload del token decodificado
            
        Raises:
            AuthenticationError: Si el token es inválido
        """
        try:
            # Verificar si el token está revocado
            if token in self._revoked_tokens:
                raise AuthenticationError("Token revocado")
            
            # Decodificar token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Verificar expiración
            exp = payload.get("exp")
            if exp is None:
                raise AuthenticationError("Token sin fecha de expiración")
            
            if datetime.utcnow().timestamp() > exp:
                raise AuthenticationError("Token expirado")
            
            # Verificar tipo de token
            token_type = payload.get("type")
            if token_type not in ["access_token", "refresh_token"]:
                raise AuthenticationError("Tipo de token inválido")
            
            return payload
            
        except JWTError as e:
            logger.warning(f"Error decodificando token: {str(e)}")
            raise AuthenticationError("Token inválido")
        except Exception as e:
            logger.error(f"Error verificando token: {str(e)}")
            raise AuthenticationError(f"Error verificando token: {str(e)}")
    
    def revoke_token(self, token: str) -> bool:
        """
        Revocar token (agregar a lista negra)
        
        Args:
            token: Token a revocar
            
        Returns:
            bool: True si se revocó exitosamente
        """
        try:
            # Verificar que el token sea válido antes de revocarlo
            payload = self.verify_token(token)
            
            # Agregar a lista de tokens revocados
            self._revoked_tokens.add(token)
            
            jti = payload.get("jti")
            logger.info(f"Token revocado: {jti}")
            
            return True
            
        except AuthenticationError:
            # Token ya inválido, no es necesario revocarlo
            return True
        except Exception as e:
            logger.error(f"Error revocando token: {str(e)}")
            return False
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """
        Renovar access token usando refresh token
        
        Args:
            refresh_token: Token de refresh válido
            
        Returns:
            str: Nuevo access token
            
        Raises:
            AuthenticationError: Si el refresh token es inválido
        """
        try:
            # Verificar refresh token
            payload = self.verify_token(refresh_token)
            
            if payload.get("type") != "refresh_token":
                raise AuthenticationError("Token no es de tipo refresh")
            
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationError("Refresh token sin ID de usuario")
            
            # Crear nuevo access token
            new_access_token = self.create_access_token({"sub": user_id})
            
            logger.info(f"Access token renovado para usuario: {user_id}")
            return new_access_token
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Error renovando access token: {str(e)}")
            raise AuthenticationError(f"Error renovando token: {str(e)}")
    
    # === GESTIÓN DE USUARIOS ===
    
    def create_user_from_microsoft(
        self, 
        microsoft_data: UserMicrosoftData, 
        db: Session
    ) -> User:
        """
        Crear usuario desde datos de Microsoft 365
        
        Args:
            microsoft_data: Datos del usuario desde Microsoft Graph
            db: Sesión de base de datos
            
        Returns:
            User: Usuario creado
        """
        try:
            # Determinar email principal
            email = microsoft_data.mail or microsoft_data.userPrincipalName
            
            # Verificar si el usuario ya existe
            existing_user = db.query(User).filter(
                (User.azure_id == microsoft_data.id) | 
                (User.email == email)
            ).first()
            
            if existing_user:
                # Actualizar datos existentes
                existing_user.update_from_microsoft(microsoft_data.dict())
                db.commit()
                db.refresh(existing_user)
                logger.info(f"Usuario actualizado desde Microsoft: {email}")
                return existing_user
            
            # Determinar rol inicial
            initial_role = self._determine_initial_role(email)
            
            # Crear nuevo usuario
            user_data = UserCreate(
                azure_id=microsoft_data.id,
                email=email,
                name=microsoft_data.displayName,
                given_name=microsoft_data.givenName,
                surname=microsoft_data.surname,
                display_name=microsoft_data.displayName,
                department=microsoft_data.department,
                job_title=microsoft_data.jobTitle,
                office_location=microsoft_data.officeLocation,
                company_name=microsoft_data.companyName,
                phone=microsoft_data.businessPhones[0] if microsoft_data.businessPhones else None,
                mobile_phone=microsoft_data.mobilePhone,
                role=initial_role
            )
            
            new_user = User(**user_data.dict())
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            logger.info(f"Usuario creado desde Microsoft: {email} con rol {initial_role.value}")
            return new_user
            
        except Exception as e:
            logger.error(f"Error creando usuario desde Microsoft: {str(e)}")
            db.rollback()
            raise AuthenticationError(f"Error creando usuario: {str(e)}")
    
    def _determine_initial_role(self, email: str) -> UserRole:
        """
        Determinar rol inicial del usuario basado en configuración
        
        Args:
            email: Email del usuario
            
        Returns:
            UserRole: Rol asignado
        """
        try:
            # Verificar si está en la lista de administradores
            admin_emails = [admin.lower() for admin in settings.ADMIN_EMAILS]
            if email.lower() in admin_emails:
                return UserRole.ADMIN
            
            # Rol por defecto
            return UserRole.VIEWER
            
        except Exception as e:
            logger.warning(f"Error determinando rol inicial: {str(e)}")
            return UserRole.VIEWER
    
    # === AUTORIZACIÓN Y PERMISOS ===
    
    def check_permission(self, user: User, permission: str) -> bool:
        """
        Verificar si un usuario tiene un permiso específico
        
        Args:
            user: Usuario a verificar
            permission: Permiso a verificar
            
        Returns:
            bool: True si tiene el permiso
        """
        try:
            if not user.is_active:
                return False
            
            if user.status == UserStatus.SUSPENDED:
                return False
            
            # Mapeo de permisos
            permission_map = {
                "can_upload": user.can_upload,
                "can_generate": user.can_generate,
                "can_manage_types": user.can_manage_types,
                "can_manage_users": user.can_manage_users,
                "is_admin": user.is_admin,
                "is_operator": user.is_operator
            }
            
            return permission_map.get(permission, False)
            
        except Exception as e:
            logger.error(f"Error verificando permiso {permission}: {str(e)}")
            return False
    
    def require_permission(self, user: User, permission: str) -> None:
        """
        Requerir que un usuario tenga un permiso específico
        
        Args:
            user: Usuario a verificar
            permission: Permiso requerido
            
        Raises:
            AuthorizationError: Si no tiene el permiso
        """
        if not self.check_permission(user, permission):
            raise AuthorizationError(f"Permiso '{permission}' requerido")
    
    def check_document_access(self, user: User, document) -> bool:
        """
        Verificar si un usuario puede acceder a un documento
        
        Args:
            user: Usuario que solicita acceso
            document: Documento a verificar
            
        Returns:
            bool: True si puede acceder
        """
        try:
            # Administradores tienen acceso a todo
            if user.is_admin:
                return True
            
            # Documentos eliminados solo para admins
            if document.status == "deleted":
                return False
            
            # Propietario siempre tiene acceso
            if document.uploaded_by == user.id:
                return True
            
            # Documentos confidenciales solo para propietario y admins
            if document.is_confidential:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verificando acceso a documento: {str(e)}")
            return False
    
    def check_qr_code_access(self, user: User, qr_code) -> bool:
        """
        Verificar si un usuario puede acceder a un código QR
        
        Args:
            user: Usuario que solicita acceso
            qr_code: Código QR a verificar
            
        Returns:
            bool: True si puede acceder
        """
        try:
            # Administradores tienen acceso a todo
            if user.is_admin:
                return True
            
            # Solo el generador puede ver el QR
            if qr_code.generated_by == user.id:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verificando acceso a QR: {str(e)}")
            return False
    
    # === VALIDACIÓN Y SEGURIDAD ===
    
    def validate_email_domain(self, email: str) -> bool:
        """
        Validar que el email pertenezca a un dominio permitido
        
        Args:
            email: Email a validar
            
        Returns:
            bool: True si el dominio está permitido
        """
        try:
            if not settings.ALLOWED_DOMAINS:
                return True  # No hay restricciones de dominio
            
            domain = email.split('@')[1].lower()
            allowed_domains = [d.lower() for d in settings.ALLOWED_DOMAINS]
            
            return domain in allowed_domains
            
        except Exception as e:
            logger.error(f"Error validando dominio de email: {str(e)}")
            return False
    
    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generar token seguro aleatorio
        
        Args:
            length: Longitud del token
            
        Returns:
            str: Token seguro
        """
        return secrets.token_urlsafe(length)
    
    def hash_password(self, password: str) -> str:
        """
        Hash de contraseña (para uso futuro si se implementa auth local)
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            str: Hash de la contraseña
        """
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verificar contraseña contra hash
        
        Args:
            plain_password: Contraseña en texto plano
            hashed_password: Hash almacenado
            
        Returns:
            bool: True si coinciden
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    # === GESTIÓN DE SESIONES ===
    
    def create_session(self, user: User) -> Dict[str, Any]:
        """
        Crear sesión completa para usuario
        
        Args:
            user: Usuario para crear sesión
            
        Returns:
            dict: Datos de la sesión (tokens, expiración, etc.)
        """
        try:
            # Crear tokens
            access_token = self.create_access_token({"sub": user.id})
            refresh_token = self.create_refresh_token(user.id)
            
            # Información de la sesión
            session_data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.full_name,
                    "role": user.role.value,
                    "permissions": {
                        "can_upload": user.can_upload,
                        "can_generate": user.can_generate,
                        "can_manage_types": user.can_manage_types,
                        "can_manage_users": user.can_manage_users
                    }
                },
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Actualizar último token emitido
            user.last_token_issued = datetime.utcnow()
            
            logger.info(f"Sesión creada para usuario: {user.email}")
            return session_data
            
        except Exception as e:
            logger.error(f"Error creando sesión: {str(e)}")
            raise AuthenticationError(f"Error creando sesión: {str(e)}")
    
    def invalidate_session(self, access_token: str, refresh_token: str = None) -> bool:
        """
        Invalidar sesión revocando tokens
        
        Args:
            access_token: Token de acceso a revocar
            refresh_token: Token de refresh a revocar (opcional)
            
        Returns:
            bool: True si se invalidó exitosamente
        """
        try:
            success = True
            
            # Revocar access token
            if not self.revoke_token(access_token):
                success = False
            
            # Revocar refresh token si se proporciona
            if refresh_token and not self.revoke_token(refresh_token):
                success = False
            
            if success:
                logger.info("Sesión invalidada exitosamente")
            
            return success
            
        except Exception as e:
            logger.error(f"Error invalidando sesión: {str(e)}")
            return False
    
    # === UTILIDADES ===
    
    def cleanup_revoked_tokens(self):
        """
        Limpiar tokens revocados expirados del cache
        En producción esto debería ejecutarse periódicamente
        """
        try:
            # En una implementación real con Redis, aquí se limpiarían
            # los tokens expirados automáticamente
            
            # Por ahora solo log
            logger.info(f"Limpieza de tokens: {len(self._revoked_tokens)} tokens revocados en cache")
            
        except Exception as e:
            logger.error(f"Error limpiando tokens revocados: {str(e)}")
    
    def get_auth_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de autenticación
        
        Returns:
            dict: Estadísticas del servicio
        """
        try:
            return {
                "revoked_tokens_count": len(self._revoked_tokens),
                "token_expire_minutes": self.access_token_expire_minutes,
                "algorithm": self.algorithm,
                "has_domain_restrictions": bool(settings.ALLOWED_DOMAINS),
                "allowed_domains": settings.ALLOWED_DOMAINS or [],
                "admin_emails_configured": len(settings.ADMIN_EMAILS),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de auth: {str(e)}")
            return {"error": str(e)}


# === INSTANCIA GLOBAL ===

# Instancia singleton del servicio
_auth_service = None

def get_auth_service() -> AuthService:
    """
    Obtener instancia del servicio de autenticación
    
    Returns:
        AuthService: Instancia del servicio
    """
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


# === FUNCIONES DE UTILIDAD ===

def create_access_token(data: Dict[str, Any]) -> str:
    """
    Función de conveniencia para crear access token
    
    Args:
        data: Datos del token
        
    Returns:
        str: Token JWT
    """
    auth_service = get_auth_service()
    return auth_service.create_access_token(data)


def verify_token(token: str) -> Dict[str, Any]:
    """
    Función de conveniencia para verificar token
    
    Args:
        token: Token a verificar
        
    Returns:
        dict: Payload del token
    """
    auth_service = get_auth_service()
    return auth_service.verify_token(token)


def check_user_permission(user: User, permission: str) -> bool:
    """
    Función de conveniencia para verificar permisos
    
    Args:
        user: Usuario
        permission: Permiso a verificar
        
    Returns:
        bool: True si tiene el permiso
    """
    auth_service = get_auth_service()
    return auth_service.check_permission(user, permission)


async def authenticate_microsoft_user(
    microsoft_data: UserMicrosoftData,
    db: Session
) -> Dict[str, Any]:
    """
    Autenticar usuario con datos de Microsoft y crear sesión
    
    Args:
        microsoft_data: Datos de Microsoft Graph
        db: Sesión de base de datos
        
    Returns:
        dict: Datos de la sesión creada
    """
    try:
        auth_service = get_auth_service()
        
        # Validar dominio si está configurado
        email = microsoft_data.mail or microsoft_data.userPrincipalName
        if not auth_service.validate_email_domain(email):
            raise AuthenticationError("Dominio de email no permitido")
        
        # Crear o actualizar usuario
        user = auth_service.create_user_from_microsoft(microsoft_data, db)
        
        # Verificar que el usuario esté activo
        if not user.is_active:
            raise AuthenticationError("Usuario desactivado")
        
        if user.status == UserStatus.SUSPENDED:
            raise AuthenticationError("Usuario suspendido")
        
        # Crear sesión
        session_data = auth_service.create_session(user)
        
        # Actualizar último login
        user.update_last_login()
        db.commit()
        
        logger.info(f"Autenticación exitosa para: {email}")
        return session_data
        
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"Error autenticando usuario de Microsoft: {str(e)}")
        raise AuthenticationError(f"Error en autenticación: {str(e)}")


def validate_auth_setup() -> Dict[str, Any]:
    """
    Validar configuración de autenticación
    
    Returns:
        dict: Estado de la configuración
    """
    try:
        issues = []
        warnings = []
        
        # Verificar configuración básica
        if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
            issues.append("SECRET_KEY debe tener al menos 32 caracteres")
        
        if not settings.MICROSOFT_CLIENT_ID:
            issues.append("MICROSOFT_CLIENT_ID no configurado")
        
        if not settings.MICROSOFT_CLIENT_SECRET:
            issues.append("MICROSOFT_CLIENT_SECRET no configurado")
        
        if not settings.MICROSOFT_TENANT_ID:
            issues.append("MICROSOFT_TENANT_ID no configurado")
        
        # Verificar configuración opcional
        if not settings.ADMIN_EMAILS:
            warnings.append("No hay emails de administrador configurados")
        
        if not settings.ALLOWED_DOMAINS:
            warnings.append("No hay restricciones de dominio configuradas")
        
        status = "healthy" if len(issues) == 0 else "unhealthy"
        
        return {
            "status": status,
            "issues": issues,
            "warnings": warnings,
            "microsoft_configured": bool(
                settings.MICROSOFT_CLIENT_ID and 
                settings.MICROSOFT_CLIENT_SECRET and 
                settings.MICROSOFT_TENANT_ID
            ),
            "domain_restrictions": bool(settings.ALLOWED_DOMAINS),
            "admin_emails_count": len(settings.ADMIN_EMAILS),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error validando configuración de auth: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }