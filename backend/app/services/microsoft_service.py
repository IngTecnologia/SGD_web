
"""
Servicio de integración con Microsoft 365
Centraliza toda la lógica de interacción con Microsoft Graph API
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from msal import ConfidentialClientApplication
from sqlalchemy.orm import Session

from ..config import get_settings
from ..schemas.user import UserMicrosoftData

# Configuración
settings = get_settings()
logger = logging.getLogger(__name__)


class MicrosoftGraphError(Exception):
    """Excepción personalizada para errores de Microsoft Graph"""
    def __init__(self, message: str, status_code: int = None, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class MicrosoftService:
    """
    Servicio principal para interactuar con Microsoft 365 y Graph API
    """
    
    def __init__(self):
        """Inicializar el servicio de Microsoft"""
        self.client_id = settings.MICROSOFT_CLIENT_ID
        self.client_secret = settings.MICROSOFT_CLIENT_SECRET
        self.tenant_id = settings.MICROSOFT_TENANT_ID
        self.redirect_uri = settings.MICROSOFT_REDIRECT_URI
        self.scopes = settings.MICROSOFT_SCOPES
        
        # URLs base
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.graph_base_url = "https://graph.microsoft.com/v1.0"
        
        # Cliente MSAL para autenticación
        self.msal_app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority
        )
        
        # Cache de tokens en memoria (en producción usar Redis)
        self._token_cache = {}
        
        logger.info("MicrosoftService inicializado correctamente")
    
    # === AUTENTICACIÓN Y TOKENS ===
    
    def get_authorization_url(self, state: str = None) -> str:
        """
        Generar URL de autorización para OAuth2 flow
        
        Args:
            state: Estado para el callback (opcional)
            
        Returns:
            str: URL de autorización
        """
        try:
            auth_params = {
                "client_id": self.client_id,
                "response_type": "code",
                "redirect_uri": self.redirect_uri,
                "scope": " ".join(self.scopes),
                "response_mode": "query",
                "state": state or "default"
            }
            
            auth_url = f"{self.authority}/oauth2/v2.0/authorize?{urlencode(auth_params)}"
            
            logger.debug(f"URL de autorización generada para state: {state}")
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generando URL de autorización: {str(e)}")
            raise MicrosoftGraphError(f"Error generando URL de autorización: {str(e)}")
    
    async def exchange_code_for_tokens(self, authorization_code: str) -> Dict[str, Any]:
        """
        Intercambiar código de autorización por tokens
        
        Args:
            authorization_code: Código de autorización de Microsoft
            
        Returns:
            dict: Tokens (access_token, refresh_token, etc.)
            
        Raises:
            MicrosoftGraphError: Si el intercambio falla
        """
        try:
            logger.info("Intercambiando código por tokens")
            
            # Usar MSAL para obtener tokens
            result = self.msal_app.acquire_token_by_authorization_code(
                authorization_code,
                scopes=self.scopes,
                redirect_uri=self.redirect_uri
            )
            
            if "error" in result:
                error_msg = f"Error de MSAL: {result.get('error_description', result.get('error'))}"
                logger.error(error_msg)
                raise MicrosoftGraphError(error_msg, error_code=result.get('error'))
            
            # Extraer información relevante
            tokens = {
                "access_token": result["access_token"],
                "refresh_token": result.get("refresh_token"),
                "expires_in": result.get("expires_in", 3600),
                "token_type": result.get("token_type", "Bearer"),
                "scope": result.get("scope", " ".join(self.scopes)),
                "expires_at": datetime.utcnow() + timedelta(seconds=result.get("expires_in", 3600))
            }
            
            logger.info("Tokens obtenidos exitosamente")
            return tokens
            
        except MicrosoftGraphError:
            raise
        except Exception as e:
            logger.error(f"Error intercambiando código: {str(e)}")
            raise MicrosoftGraphError(f"Error intercambiando código por tokens: {str(e)}")
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Renovar token de acceso usando refresh token
        
        Args:
            refresh_token: Token de renovación
            
        Returns:
            dict: Nuevos tokens
            
        Raises:
            MicrosoftGraphError: Si la renovación falla
        """
        try:
            logger.info("Renovando token de acceso")
            
            result = self.msal_app.acquire_token_by_refresh_token(
                refresh_token,
                scopes=self.scopes
            )
            
            if "error" in result:
                error_msg = f"Error renovando token: {result.get('error_description', result.get('error'))}"
                logger.error(error_msg)
                raise MicrosoftGraphError(error_msg, error_code=result.get('error'))
            
            tokens = {
                "access_token": result["access_token"],
                "refresh_token": result.get("refresh_token", refresh_token),
                "expires_in": result.get("expires_in", 3600),
                "expires_at": datetime.utcnow() + timedelta(seconds=result.get("expires_in", 3600))
            }
            
            logger.info("Token renovado exitosamente")
            return tokens
            
        except MicrosoftGraphError:
            raise
        except Exception as e:
            logger.error(f"Error renovando token: {str(e)}")
            raise MicrosoftGraphError(f"Error renovando token: {str(e)}")
    
    def get_app_only_token(self) -> str:
        """
        Obtener token de solo aplicación para operaciones administrativas
        
        Returns:
            str: Token de acceso de aplicación
            
        Raises:
            MicrosoftGraphError: Si no se puede obtener el token
        """
        try:
            # Verificar si tenemos un token en cache válido
            cache_key = "app_only_token"
            if cache_key in self._token_cache:
                cached_token = self._token_cache[cache_key]
                if cached_token["expires_at"] > datetime.utcnow():
                    return cached_token["access_token"]
            
            logger.info("Obteniendo token de aplicación")
            
            # Obtener nuevo token
            result = self.msal_app.acquire_token_for_client(
                scopes=["https://graph.microsoft.com/.default"]
            )
            
            if "error" in result:
                error_msg = f"Error obteniendo token de app: {result.get('error_description', result.get('error'))}"
                logger.error(error_msg)
                raise MicrosoftGraphError(error_msg, error_code=result.get('error'))
            
            # Cachear token
            token_info = {
                "access_token": result["access_token"],
                "expires_at": datetime.utcnow() + timedelta(seconds=result.get("expires_in", 3600))
            }
            self._token_cache[cache_key] = token_info
            
            logger.info("Token de aplicación obtenido exitosamente")
            return result["access_token"]
            
        except MicrosoftGraphError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo token de aplicación: {str(e)}")
            raise MicrosoftGraphError(f"Error obteniendo token de aplicación: {str(e)}")
    
    # === OPERACIONES DE GRAPH API ===
    
    async def make_graph_request(
        self, 
        method: str, 
        endpoint: str, 
        access_token: str,
        data: Dict = None,
        params: Dict = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Realizar request a Microsoft Graph API
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint de Graph API (sin URL base)
            access_token: Token de acceso
            data: Datos para request POST/PUT
            params: Parámetros de query
            timeout: Timeout en segundos
            
        Returns:
            dict: Respuesta de Graph API
            
        Raises:
            MicrosoftGraphError: Si la request falla
        """
        try:
            url = f"{self.graph_base_url}/{endpoint.lstrip('/')}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            logger.debug(f"Graph API request: {method} {url}")
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=data, params=params)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=headers, json=data, params=params)
                elif method.upper() == "PATCH":
                    response = await client.patch(url, headers=headers, json=data, params=params)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers, params=params)
                else:
                    raise ValueError(f"Método HTTP no soportado: {method}")
            
            # Manejar respuesta
            if response.status_code == 204:  # No Content
                return {}
            
            if not response.is_success:
                error_detail = "Error desconocido"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("error", {}).get("message", str(error_data))
                except:
                    error_detail = response.text
                
                logger.error(f"Graph API error: {response.status_code} - {error_detail}")
                raise MicrosoftGraphError(
                    f"Error de Graph API: {error_detail}",
                    status_code=response.status_code
                )
            
            try:
                return response.json()
            except:
                return {"status": "success"}
                
        except MicrosoftGraphError:
            raise
        except httpx.TimeoutException:
            logger.error(f"Timeout en request a Graph API: {endpoint}")
            raise MicrosoftGraphError("Timeout en request a Microsoft Graph")
        except Exception as e:
            logger.error(f"Error en request a Graph API: {str(e)}")
            raise MicrosoftGraphError(f"Error en request a Graph API: {str(e)}")
    
    # === GESTIÓN DE USUARIOS ===
    
    async def get_user_info(self, access_token: str, user_id: str = "me") -> UserMicrosoftData:
        """
        Obtener información de usuario desde Graph API
        
        Args:
            access_token: Token de acceso del usuario
            user_id: ID del usuario o "me" para usuario actual
            
        Returns:
            UserMicrosoftData: Información del usuario
            
        Raises:
            MicrosoftGraphError: Si no se puede obtener la información
        """
        try:
            logger.info(f"Obteniendo información de usuario: {user_id}")
            
            endpoint = f"users/{user_id}" if user_id != "me" else "me"
            
            # Campos específicos que necesitamos
            select_fields = [
                "id", "displayName", "givenName", "surname", "mail", "userPrincipalName",
                "department", "jobTitle", "officeLocation", "companyName",
                "businessPhones", "mobilePhone", "preferredLanguage"
            ]
            
            params = {
                "$select": ",".join(select_fields)
            }
            
            user_data = await self.make_graph_request(
                method="GET",
                endpoint=endpoint,
                access_token=access_token,
                params=params
            )
            
            # Validar y convertir a nuestro schema
            microsoft_user = UserMicrosoftData(**user_data)
            
            logger.info(f"Información de usuario obtenida: {microsoft_user.userPrincipalName}")
            return microsoft_user
            
        except Exception as e:
            logger.error(f"Error obteniendo información de usuario: {str(e)}")
            raise MicrosoftGraphError(f"Error obteniendo información de usuario: {str(e)}")
    
    async def list_organization_users(
        self, 
        app_token: str = None,
        filter_query: str = None,
        top: int = 100
    ) -> List[UserMicrosoftData]:
        """
        Listar usuarios de la organización (requiere permisos administrativos)
        
        Args:
            app_token: Token de aplicación (se obtiene automáticamente si no se proporciona)
            filter_query: Filtro OData para usuarios
            top: Número máximo de usuarios a retornar
            
        Returns:
            List[UserMicrosoftData]: Lista de usuarios
            
        Raises:
            MicrosoftGraphError: Si no se pueden obtener los usuarios
        """
        try:
            logger.info("Listando usuarios de la organización")
            
            if not app_token:
                app_token = self.get_app_only_token()
            
            params = {
                "$top": min(top, 999),  # Máximo de Graph API
                "$select": "id,displayName,givenName,surname,mail,userPrincipalName,department,jobTitle"
            }
            
            if filter_query:
                params["$filter"] = filter_query
            
            response = await self.make_graph_request(
                method="GET",
                endpoint="users",
                access_token=app_token,
                params=params
            )
            
            users_data = response.get("value", [])
            users = []
            
            for user_data in users_data:
                try:
                    user = UserMicrosoftData(**user_data)
                    users.append(user)
                except Exception as e:
                    logger.warning(f"Error procesando usuario {user_data.get('id', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(f"Obtenidos {len(users)} usuarios de la organización")
            return users
            
        except Exception as e:
            logger.error(f"Error listando usuarios: {str(e)}")
            raise MicrosoftGraphError(f"Error listando usuarios de la organización: {str(e)}")
    
    async def get_user_photo(self, access_token: str, user_id: str = "me", size: str = "48x48") -> Optional[bytes]:
        """
        Obtener foto de perfil del usuario
        
        Args:
            access_token: Token de acceso
            user_id: ID del usuario o "me"
            size: Tamaño de la foto (48x48, 64x64, 96x96, 120x120, 240x240, 360x360, 432x432, 504x504, 648x648)
            
        Returns:
            Optional[bytes]: Datos binarios de la foto o None si no existe
        """
        try:
            endpoint = f"users/{user_id}/photos/{size}/$value" if user_id != "me" else f"me/photos/{size}/$value"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.graph_base_url}/{endpoint}",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
            
            if response.status_code == 404:
                return None
            elif response.is_success:
                return response.content
            else:
                logger.warning(f"Error obteniendo foto de usuario: {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"Error obteniendo foto de usuario: {str(e)}")
            return None
    
    # === GESTIÓN DE ARCHIVOS (OneDrive) ===
    
    async def get_onedrive_info(self, access_token: str) -> Dict[str, Any]:
        """
        Obtener información del OneDrive del usuario
        
        Args:
            access_token: Token de acceso del usuario
            
        Returns:
            dict: Información del OneDrive
        """
        try:
            logger.info("Obteniendo información de OneDrive")
            
            drive_info = await self.make_graph_request(
                method="GET",
                endpoint="me/drive",
                access_token=access_token
            )
            
            return {
                "id": drive_info.get("id"),
                "name": drive_info.get("name"),
                "drive_type": drive_info.get("driveType"),
                "quota": drive_info.get("quota", {}),
                "owner": drive_info.get("owner", {})
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo info de OneDrive: {str(e)}")
            raise MicrosoftGraphError(f"Error obteniendo información de OneDrive: {str(e)}")
    
    async def create_onedrive_folder(
        self, 
        access_token: str, 
        folder_name: str, 
        parent_path: str = "root"
    ) -> Dict[str, Any]:
        """
        Crear carpeta en OneDrive
        
        Args:
            access_token: Token de acceso
            folder_name: Nombre de la carpeta
            parent_path: Ruta de la carpeta padre
            
        Returns:
            dict: Información de la carpeta creada
        """
        try:
            logger.info(f"Creando carpeta en OneDrive: {folder_name}")
            
            data = {
                "name": folder_name,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "rename"
            }
            
            endpoint = f"me/drive/{parent_path}/children"
            
            folder_info = await self.make_graph_request(
                method="POST",
                endpoint=endpoint,
                access_token=access_token,
                data=data
            )
            
            logger.info(f"Carpeta creada: {folder_info.get('name')} (ID: {folder_info.get('id')})")
            return folder_info
            
        except Exception as e:
            logger.error(f"Error creando carpeta: {str(e)}")
            raise MicrosoftGraphError(f"Error creando carpeta en OneDrive: {str(e)}")
    
    async def upload_file_to_onedrive(
        self,
        access_token: str,
        file_path: str,
        file_content: bytes,
        folder_path: str = "root"
    ) -> Dict[str, Any]:
        """
        Subir archivo a OneDrive
        
        Args:
            access_token: Token de acceso
            file_path: Nombre del archivo en OneDrive
            file_content: Contenido del archivo en bytes
            folder_path: Ruta de la carpeta de destino
            
        Returns:
            dict: Información del archivo subido
        """
        try:
            logger.info(f"Subiendo archivo a OneDrive: {file_path}")
            
            # Para archivos pequeños (< 4MB) usar upload simple
            if len(file_content) < 4 * 1024 * 1024:
                url = f"{self.graph_base_url}/me/drive/{folder_path}:/{file_path}:/content"
                
                async with httpx.AsyncClient() as client:
                    response = await client.put(
                        url,
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Content-Type": "application/octet-stream"
                        },
                        content=file_content
                    )
                
                if not response.is_success:
                    raise MicrosoftGraphError(
                        f"Error subiendo archivo: {response.status_code}",
                        status_code=response.status_code
                    )
                
                file_info = response.json()
                logger.info(f"Archivo subido: {file_info.get('name')} (ID: {file_info.get('id')})")
                return file_info
            else:
                # Para archivos grandes usar upload session
                return await self._upload_large_file(access_token, file_path, file_content, folder_path)
                
        except Exception as e:
            logger.error(f"Error subiendo archivo: {str(e)}")
            raise MicrosoftGraphError(f"Error subiendo archivo a OneDrive: {str(e)}")
    
    async def _upload_large_file(
        self,
        access_token: str,
        file_path: str,
        file_content: bytes,
        folder_path: str
    ) -> Dict[str, Any]:
        """
        Subir archivo grande usando upload session
        
        Args:
            access_token: Token de acceso
            file_path: Nombre del archivo
            file_content: Contenido del archivo
            folder_path: Carpeta de destino
            
        Returns:
            dict: Información del archivo subido
        """
        try:
            logger.info(f"Iniciando upload session para archivo grande: {file_path}")
            
            # Crear upload session
            session_data = {
                "item": {
                    "@microsoft.graph.conflictBehavior": "rename",
                    "name": file_path
                }
            }
            
            session_response = await self.make_graph_request(
                method="POST",
                endpoint=f"me/drive/{folder_path}:/{file_path}:/createUploadSession",
                access_token=access_token,
                data=session_data
            )
            
            upload_url = session_response["uploadUrl"]
            
            # Subir en chunks de 320KB (recomendado por Microsoft)
            chunk_size = 320 * 1024
            total_size = len(file_content)
            
            async with httpx.AsyncClient() as client:
                for i in range(0, total_size, chunk_size):
                    chunk = file_content[i:i + chunk_size]
                    chunk_start = i
                    chunk_end = min(i + chunk_size - 1, total_size - 1)
                    
                    headers = {
                        "Content-Range": f"bytes {chunk_start}-{chunk_end}/{total_size}",
                        "Content-Length": str(len(chunk))
                    }
                    
                    response = await client.put(upload_url, headers=headers, content=chunk)
                    
                    if response.status_code == 201:  # Upload completo
                        file_info = response.json()
                        logger.info(f"Archivo grande subido: {file_info.get('name')}")
                        return file_info
                    elif response.status_code != 202:  # 202 = continuar
                        raise MicrosoftGraphError(
                            f"Error en upload session: {response.status_code}",
                            status_code=response.status_code
                        )
            
            raise MicrosoftGraphError("Upload session completado pero sin respuesta final")
            
        except Exception as e:
            logger.error(f"Error en upload de archivo grande: {str(e)}")
            raise MicrosoftGraphError(f"Error subiendo archivo grande: {str(e)}")
    
    # === NOTIFICACIONES Y EMAIL ===
    
    async def send_email(
        self,
        access_token: str,
        to_addresses: List[str],
        subject: str,
        body: str,
        is_html: bool = True,
        cc_addresses: List[str] = None,
        attachments: List[Dict] = None
    ) -> bool:
        """
        Enviar email usando Graph API
        
        Args:
            access_token: Token de acceso
            to_addresses: Lista de destinatarios
            subject: Asunto del email
            body: Cuerpo del email
            is_html: Si el cuerpo es HTML
            cc_addresses: Lista de CCs
            attachments: Lista de adjuntos
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            logger.info(f"Enviando email a {len(to_addresses)} destinatarios")
            
            # Construir mensaje
            message = {
                "subject": subject,
                "body": {
                    "contentType": "HTML" if is_html else "Text",
                    "content": body
                },
                "toRecipients": [
                    {"emailAddress": {"address": addr}} for addr in to_addresses
                ]
            }
            
            if cc_addresses:
                message["ccRecipients"] = [
                    {"emailAddress": {"address": addr}} for addr in cc_addresses
                ]
            
            if attachments:
                message["attachments"] = attachments
            
            await self.make_graph_request(
                method="POST",
                endpoint="me/sendMail",
                access_token=access_token,
                data={"message": message}
            )
            
            logger.info("Email enviado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email: {str(e)}")
            return False
    
    # === UTILIDADES ===
    
    def validate_token(self, access_token: str) -> bool:
        """
        Validar si un token de acceso es válido
        
        Args:
            access_token: Token a validar
            
        Returns:
            bool: True si el token es válido
        """
        try:
            # Hacer una request simple para validar
            asyncio.run(
                self.make_graph_request(
                    method="GET",
                    endpoint="me",
                    access_token=access_token,
                    params={"$select": "id"}
                )
            )
            return True
        except:
            return False
    
    async def get_tenant_info(self) -> Dict[str, Any]:
        """
        Obtener información del tenant de Azure AD
        
        Returns:
            dict: Información del tenant
        """
        try:
            app_token = self.get_app_only_token()
            
            tenant_info = await self.make_graph_request(
                method="GET",
                endpoint="organization",
                access_token=app_token,
                params={"$select": "id,displayName,verifiedDomains,country,countryLetterCode"}
            )
            
            return tenant_info.get("value", [{}])[0]
            
        except Exception as e:
            logger.error(f"Error obteniendo info del tenant: {str(e)}")
            raise MicrosoftGraphError(f"Error obteniendo información del tenant: {str(e)}")
    
    def clear_token_cache(self):
        """Limpiar cache de tokens"""
        self._token_cache.clear()
        logger.info("Cache de tokens limpiado")


# === INSTANCIA GLOBAL ===

# Instancia singleton del servicio
_microsoft_service = None

def get_microsoft_service() -> MicrosoftService:
    """
    Obtener instancia del servicio de Microsoft
    
    Returns:
        MicrosoftService: Instancia del servicio
    """
    global _microsoft_service
    if _microsoft_service is None:
        _microsoft_service = MicrosoftService()
    return _microsoft_service


# === FUNCIONES DE UTILIDAD ===

async def verify_microsoft_integration() -> Dict[str, Any]:
    """
    Verificar que la integración con Microsoft esté funcionando
    
    Returns:
        dict: Estado de la integración
    """
    try:
        service = get_microsoft_service()
        
        # Verificar configuración
        config_status = {
            "client_id_configured": bool(service.client_id),
            "client_secret_configured": bool(service.client_secret),
            "tenant_id_configured": bool(service.tenant_id),
            "redirect_uri_configured": bool(service.redirect_uri)
        }
        
        # Intentar obtener token de aplicación
        app_token_status = False
        tenant_info = None
        
        try:
            app_token = service.get_app_only_token()
            app_token_status = bool(app_token)
            
            if app_token_status:
                tenant_info = await service.get_tenant_info()
        except Exception as e:
            logger.warning(f"No se pudo obtener token de aplicación: {str(e)}")
        
        return {
            "status": "healthy" if all(config_status.values()) and app_token_status else "unhealthy",
            "configuration": config_status,
            "app_token_working": app_token_status,
            "tenant_info": tenant_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error verificando integración de Microsoft: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }