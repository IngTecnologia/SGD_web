"""
Endpoints de autenticación con Microsoft 365
Manejo de login, logout y gestión de tokens JWT
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from jose import jwt
import httpx

from ...database import get_db
from ...config import get_settings
from ...models.user import User, UserRole, UserStatus
from ...schemas.user import (
    UserLoginResponse,
    User as UserSchema,
    UserMicrosoftData,
    UserCreate,
    UserLocalLogin
)
from ..deps import get_current_user, get_current_user_optional, get_request_logger

# Configuración
settings = get_settings()
logger = logging.getLogger(__name__)

# Router
router = APIRouter()


# === ENDPOINTS DE AUTENTICACIÓN ===

@router.get("/microsoft/login")
async def microsoft_login(
    request: Request,
    redirect_uri: Optional[str] = None
):
    """
    Iniciar proceso de autenticación con Microsoft 365
    Redirige al usuario a la página de login de Microsoft
    
    Args:
        request: Request object de FastAPI
        redirect_uri: URI de redirección después del login (opcional)
        
    Returns:
        RedirectResponse: Redirección a Microsoft login
    """
    try:
        # Construir URL de autorización de Microsoft
        auth_params = {
            "client_id": settings.MICROSOFT_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": settings.MICROSOFT_REDIRECT_URI,
            "scope": " ".join(settings.MICROSOFT_SCOPES),
            "response_mode": "query",
            "state": redirect_uri or "default"  # Usar para redirigir después del login
        }
        
        # URL base de Microsoft para autenticación
        microsoft_auth_url = (
            f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize"
        )
        
        # Construir URL completa
        auth_url = f"{microsoft_auth_url}?{urlencode(auth_params)}"
        
        logger.info(f"Redirigiendo usuario a Microsoft login desde IP: {request.client.host}")
        
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        logger.error(f"Error generando URL de Microsoft login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al iniciar proceso de autenticación"
        )


@router.get("/microsoft/callback")
async def microsoft_callback(
    request: Request,
    code: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
    log_action = Depends(get_request_logger)
):
    """
    Callback de Microsoft después de la autenticación
    Intercambia el código por tokens y crea/actualiza el usuario
    
    Args:
        request: Request object de FastAPI
        code: Código de autorización de Microsoft
        error: Error de Microsoft (si lo hay)
        error_description: Descripción del error
        state: Estado pasado en la request inicial
        db: Sesión de base de datos
        log_action: Logger de acciones
        
    Returns:
        RedirectResponse o JSONResponse: Redirige al frontend o devuelve error
    """
    try:
        # Verificar si hubo error en Microsoft
        if error:
            logger.warning(f"Error de Microsoft: {error} - {error_description}")
            log_action("microsoft_auth_error", {"error": error, "description": error_description})
            
            # Redirigir al frontend con error
            frontend_url = settings.BACKEND_CORS_ORIGINS[0] if settings.BACKEND_CORS_ORIGINS else "/"
            error_url = f"{frontend_url}/login?error={error}&description={error_description}"
            return RedirectResponse(url=error_url)
        
        # Verificar que tenemos código
        if not code:
            logger.warning("Callback de Microsoft sin código de autorización")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código de autorización requerido"
            )
        
        # Intercambiar código por token
        tokens = await exchange_code_for_tokens(code)
        
        # Obtener información del usuario desde Microsoft Graph
        user_info = await get_user_info_from_microsoft(tokens["access_token"])
        
        # Crear o actualizar usuario en nuestra base de datos
        user = await create_or_update_user(user_info, db)
        
        # Generar JWT para nuestra aplicación
        access_token = create_access_token({"sub": user.id})
        
        # Log de login exitoso
        log_action("successful_login", {
            "user_id": user.id,
            "email": user.email,
            "method": "microsoft_365"
        })
        
        # Actualizar último login del usuario
        user.update_last_login()
        db.commit()
        
        logger.info(f"Login exitoso para usuario: {user.email}")
        
        # Redirigir al frontend con token
        frontend_url = settings.BACKEND_CORS_ORIGINS[0] if settings.BACKEND_CORS_ORIGINS else "/"
        if state and state != "default":
            redirect_url = state
        else:
            redirect_url = f"{frontend_url}/dashboard"
        
        # Agregar token como parámetro o cookie según configuración
        token_url = f"{redirect_url}?token={access_token}"
        
        return RedirectResponse(url=token_url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en callback de Microsoft: {str(e)}")
        log_action("microsoft_callback_error", {"error": str(e)}, "error")
        
        # Redirigir con error genérico
        frontend_url = settings.BACKEND_CORS_ORIGINS[0] if settings.BACKEND_CORS_ORIGINS else "/"
        error_url = f"{frontend_url}/login?error=callback_error"
        return RedirectResponse(url=error_url)


@router.post("/local/login", response_model=UserLoginResponse)
async def login_local(
    credentials: UserLocalLogin,
    db: Session = Depends(get_db),
    log_action = Depends(get_request_logger)
):
    """
    Login con usuario y contraseña local (modo demo/desarrollo)

    Args:
        credentials: Email y contraseña del usuario
        db: Sesión de base de datos
        log_action: Logger de acciones

    Returns:
        UserLoginResponse: Información del usuario y token JWT
    """
    try:
        # Verificar si la autenticación local está habilitada
        if not settings.LOCAL_AUTH_ENABLED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Autenticación local no habilitada"
            )

        # Buscar usuario por email
        user = db.query(User).filter(
            User.email == credentials.email.lower(),
            User.is_local_user == True
        ).first()

        if not user or not user.verify_password(credentials.password):
            logger.warning(f"Intento de login fallido para: {credentials.email}")
            log_action("failed_local_login", {"email": credentials.email}, "warning")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos"
            )

        # Verificar que el usuario esté activo
        if not user.is_active or user.status == UserStatus.SUSPENDED:
            logger.warning(f"Intento de login de usuario inactivo: {credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo o suspendido"
            )

        # Generar JWT
        access_token = create_access_token({"sub": user.id})

        # Log de login exitoso
        log_action("successful_local_login", {
            "user_id": user.id,
            "email": user.email
        })

        # Actualizar último login
        user.update_last_login()
        db.commit()

        logger.info(f"Login local exitoso para usuario: {user.email}")

        return UserLoginResponse(
            user=UserSchema.from_orm(user),
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login local: {str(e)}")
        log_action("local_login_error", {"error": str(e)}, "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al procesar login"
        )


@router.post("/token", response_model=UserLoginResponse)
async def login_with_microsoft_token(
    microsoft_token: str,
    db: Session = Depends(get_db),
    log_action = Depends(get_request_logger)
):
    """
    Login directo con token de Microsoft (para aplicaciones SPA)
    
    Args:
        microsoft_token: Token de acceso de Microsoft Graph
        db: Sesión de base de datos
        log_action: Logger de acciones
        
    Returns:
        UserLoginResponse: Información del usuario y token JWT
    """
    try:
        # Obtener información del usuario desde Microsoft Graph
        user_info = await get_user_info_from_microsoft(microsoft_token)
        
        # Crear o actualizar usuario
        user = await create_or_update_user(user_info, db)
        
        # Generar JWT
        access_token = create_access_token({"sub": user.id})
        
        # Log de login
        log_action("token_login", {
            "user_id": user.id,
            "email": user.email
        })
        
        # Actualizar último login
        user.update_last_login()
        db.commit()
        
        return UserLoginResponse(
            user=UserSchema.from_orm(user),
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login con token: {str(e)}")
        log_action("token_login_error", {"error": str(e)}, "error")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error al autenticar con Microsoft"
        )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    log_action = Depends(get_request_logger)
):
    """
    Logout del usuario
    
    Args:
        current_user: Usuario actual autenticado
        log_action: Logger de acciones
        
    Returns:
        dict: Confirmación de logout
    """
    try:
        # Log de logout
        log_action("logout", {
            "user_id": current_user.id,
            "email": current_user.email
        })
        
        logger.info(f"Logout exitoso para usuario: {current_user.email}")
        
        return {
            "message": "Logout exitoso",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en logout: {str(e)}")
        log_action("logout_error", {"error": str(e)}, "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al cerrar sesión"
        )


@router.get("/me", response_model=UserSchema)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Obtener información del usuario actual
    
    Args:
        current_user: Usuario actual autenticado
        
    Returns:
        UserSchema: Información completa del usuario
    """
    return UserSchema.from_orm(current_user)


@router.post("/refresh")
async def refresh_token(
    current_user: User = Depends(get_current_user),
    log_action = Depends(get_request_logger)
):
    """
    Renovar token de acceso
    
    Args:
        current_user: Usuario actual autenticado
        log_action: Logger de acciones
        
    Returns:
        dict: Nuevo token de acceso
    """
    try:
        # Generar nuevo token
        access_token = create_access_token({"sub": current_user.id})
        
        # Log de refresh
        log_action("token_refresh", {
            "user_id": current_user.id,
            "email": current_user.email
        })
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except Exception as e:
        logger.error(f"Error renovando token: {str(e)}")
        log_action("token_refresh_error", {"error": str(e)}, "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al renovar token"
        )


@router.get("/status")
async def auth_status(
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Verificar estado de autenticación
    
    Args:
        current_user: Usuario actual (opcional)
        
    Returns:
        dict: Estado de autenticación
    """
    if current_user:
        return {
            "authenticated": True,
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "name": current_user.full_name,
                "role": current_user.role.value,
                "status": current_user.status.value
            },
            "permissions": {
                "can_upload": current_user.can_upload,
                "can_generate": current_user.can_generate,
                "can_manage_types": current_user.can_manage_types,
                "can_manage_users": current_user.can_manage_users
            }
        }
    else:
        return {
            "authenticated": False,
            "user": None,
            "permissions": {}
        }


# === FUNCIONES AUXILIARES ===

async def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    """
    Intercambiar código de autorización por tokens de Microsoft
    
    Args:
        code: Código de autorización
        
    Returns:
        dict: Tokens de Microsoft (access_token, refresh_token, etc.)
        
    Raises:
        HTTPException: Si el intercambio falla
    """
    try:
        token_url = f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/token"
        
        token_data = {
            "client_id": settings.MICROSOFT_CLIENT_ID,
            "client_secret": settings.MICROSOFT_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.MICROSOFT_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
        
        if response.status_code != 200:
            logger.error(f"Error obteniendo tokens de Microsoft: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Error al obtener tokens de Microsoft"
            )
        
        tokens = response.json()
        logger.info("Tokens de Microsoft obtenidos exitosamente")
        return tokens
        
    except httpx.RequestError as e:
        logger.error(f"Error de red al obtener tokens: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error de conexión con Microsoft"
        )


async def get_user_info_from_microsoft(access_token: str) -> UserMicrosoftData:
    """
    Obtener información del usuario desde Microsoft Graph API
    
    Args:
        access_token: Token de acceso de Microsoft
        
    Returns:
        UserMicrosoftData: Información del usuario desde Microsoft
        
    Raises:
        HTTPException: Si la consulta falla
    """
    try:
        graph_url = "https://graph.microsoft.com/v1.0/me"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(graph_url, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Error obteniendo info de usuario de Microsoft: {response.status_code}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Error al obtener información del usuario"
            )
        
        user_data = response.json()
        
        # Validar y parsear datos del usuario
        microsoft_user = UserMicrosoftData(**user_data)
        
        logger.info(f"Información de usuario obtenida: {microsoft_user.userPrincipalName}")
        return microsoft_user
        
    except httpx.RequestError as e:
        logger.error(f"Error de red al obtener info de usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error de conexión con Microsoft Graph"
        )


async def create_or_update_user(user_info: UserMicrosoftData, db: Session) -> User:
    """
    Crear o actualizar usuario en la base de datos local
    
    Args:
        user_info: Información del usuario desde Microsoft
        db: Sesión de base de datos
        
    Returns:
        User: Usuario creado o actualizado
        
    Raises:
        HTTPException: Si hay errores de validación o dominio
    """
    try:
        # Usar email principal o userPrincipalName
        email = user_info.mail or user_info.userPrincipalName
        
        # Validar dominio si está configurado
        if settings.ALLOWED_DOMAINS:
            domain = email.split('@')[1].lower()
            if domain not in [d.lower() for d in settings.ALLOWED_DOMAINS]:
                logger.warning(f"Intento de login desde dominio no permitido: {domain}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Dominio de email no permitido"
                )
        
        # Buscar usuario existente
        user = db.query(User).filter(
            (User.azure_id == user_info.id) | (User.email == email)
        ).first()
        
        if user:
            # Actualizar usuario existente con datos de Microsoft
            user.update_from_microsoft(user_info.dict())
            logger.info(f"Usuario actualizado: {email}")
        else:
            # Crear nuevo usuario
            # Determinar rol inicial
            initial_role = UserRole.ADMIN if email.lower() in [
                admin_email.lower() for admin_email in settings.ADMIN_EMAILS
            ] else UserRole.VIEWER
            
            user_create_data = UserCreate(
                azure_id=user_info.id,
                email=email,
                name=user_info.displayName,
                given_name=user_info.givenName,
                surname=user_info.surname,
                display_name=user_info.displayName,
                department=user_info.department,
                job_title=user_info.jobTitle,
                office_location=user_info.officeLocation,
                company_name=user_info.companyName,
                phone=user_info.businessPhones[0] if user_info.businessPhones else None,
                mobile_phone=user_info.mobilePhone,
                role=initial_role
            )
            
            user = User(**user_create_data.dict())
            db.add(user)
            logger.info(f"Usuario creado: {email} con rol {initial_role.value}")
        
        db.commit()
        db.refresh(user)
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando/actualizando usuario: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al procesar información del usuario"
        )


def create_access_token(data: dict) -> str:
    """
    Crear token JWT de acceso

    Args:
        data: Datos a incluir en el token

    Returns:
        str: Token JWT codificado
    """
    to_encode = data.copy()

    # Asegurar que 'sub' sea string (requisito de JWT)
    if 'sub' in to_encode:
        to_encode['sub'] = str(to_encode['sub'])

    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


# === ENDPOINTS ADMINISTRATIVOS ===

@router.get("/users/sync")
async def sync_users_with_microsoft(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    log_action = Depends(get_request_logger)
):
    """
    Sincronizar usuarios con Microsoft Graph (solo administradores)
    
    Args:
        current_user: Usuario actual
        db: Sesión de base de datos
        log_action: Logger de acciones
        
    Returns:
        dict: Resultado de la sincronización
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden sincronizar usuarios"
        )
    
    try:
        # Esta funcionalidad requeriría permisos adicionales de Microsoft Graph
        # para listar usuarios del tenant. Por ahora solo log la acción.
        
        log_action("user_sync_attempted", {
            "admin_user_id": current_user.id
        })
        
        return {
            "message": "Sincronización de usuarios programada",
            "status": "pending_implementation"
        }
        
    except Exception as e:
        logger.error(f"Error en sincronización de usuarios: {str(e)}")
        log_action("user_sync_error", {"error": str(e)}, "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al sincronizar usuarios"
        )