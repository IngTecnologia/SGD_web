"""
Utilidades para sincronización con OneDrive
Gestión de subida, descarga y sincronización automática de documentos
"""
import logging
import os
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import hashlib

from sqlalchemy.orm import Session

from ..config import get_settings
from ..models.user import User
from ..models.document import Document
from ..models.document_type import DocumentType
from ..services.microsoft_service import get_microsoft_service
from ..services.storage_service import get_storage_service

# Configuración
settings = get_settings()
logger = logging.getLogger(__name__)


class OneDriveSyncError(Exception):
    """Excepción personalizada para errores de sincronización"""
    pass


class OneDriveSync:
    """
    Clase principal para sincronización con OneDrive
    """
    
    def __init__(self):
        """Inicializar el sincronizador de OneDrive"""
        self.microsoft_service = get_microsoft_service()
        self.storage_service = get_storage_service()
        self.root_folder = settings.ONEDRIVE_ROOT_FOLDER
        
        # Cache de información de OneDrive
        self._folder_cache = {}
        self._sync_status_cache = {}
        
        logger.info("OneDriveSync inicializado")
    
    # === CONFIGURACIÓN DE CARPETAS ===
    
    async def setup_onedrive_structure(
        self,
        access_token: str,
        document_types: List[DocumentType]
    ) -> Dict[str, Any]:
        """
        Configurar estructura de carpetas en OneDrive
        
        Args:
            access_token: Token de acceso del usuario
            document_types: Lista de tipos de documento
            
        Returns:
            dict: Resultado de la configuración
        """
        try:
            logger.info("Configurando estructura de OneDrive")
            
            created_folders = []
            errors = []
            
            # Crear carpeta raíz
            try:
                root_info = await self.microsoft_service.create_onedrive_folder(
                    access_token, self.root_folder
                )
                created_folders.append(self.root_folder)
                logger.info(f"Carpeta raíz creada: {self.root_folder}")
            except Exception as e:
                if "already exists" not in str(e).lower():
                    errors.append(f"Error creando carpeta raíz: {str(e)}")
            
            # Crear carpetas por tipo de documento
            for doc_type in document_types:
                if doc_type.is_active:
                    folder_name = f"{self.root_folder}/{doc_type.code}"
                    try:
                        await self.microsoft_service.create_onedrive_folder(
                            access_token, doc_type.code, f"root:/{self.root_folder}"
                        )
                        created_folders.append(folder_name)
                        logger.info(f"Carpeta creada: {folder_name}")
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            errors.append(f"Error creando carpeta {doc_type.code}: {str(e)}")
            
            # Crear carpetas adicionales
            additional_folders = ["Templates", "Exports", "Backups"]
            for folder in additional_folders:
                try:
                    await self.microsoft_service.create_onedrive_folder(
                        access_token, folder, f"root:/{self.root_folder}"
                    )
                    created_folders.append(f"{self.root_folder}/{folder}")
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        errors.append(f"Error creando carpeta {folder}: {str(e)}")
            
            return {
                "success": len(errors) == 0,
                "created_folders": created_folders,
                "errors": errors,
                "configured_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error configurando OneDrive: {str(e)}")
            raise OneDriveSyncError(f"Error configurando estructura: {str(e)}")
    
    # === SINCRONIZACIÓN DE DOCUMENTOS ===
    
    async def sync_document_to_onedrive(
        self,
        document: Document,
        user_access_token: str,
        force_upload: bool = False
    ) -> Dict[str, Any]:
        """
        Sincronizar documento específico con OneDrive
        
        Args:
            document: Documento a sincronizar
            user_access_token: Token de acceso del usuario
            force_upload: Forzar subida aunque ya exista
            
        Returns:
            dict: Resultado de la sincronización
        """
        try:
            logger.info(f"Sincronizando documento {document.id} con OneDrive")
            
            # Verificar si el archivo existe localmente
            local_path = os.path.join(settings.DOCUMENTS_PATH, document.file_path)
            if not os.path.exists(local_path):
                raise OneDriveSyncError(f"Archivo local no encontrado: {document.file_path}")
            
            # Verificar si ya está sincronizado
            if document.onedrive_url and not force_upload:
                # Verificar si el archivo sigue existiendo en OneDrive
                if await self._verify_onedrive_file_exists(document.onedrive_url, user_access_token):
                    return {
                        "success": True,
                        "action": "already_synced",
                        "onedrive_url": document.onedrive_url,
                        "message": "Documento ya sincronizado"
                    }
            
            # Determinar carpeta de destino
            folder_path = f"root:/{self.root_folder}"
            if document.document_type:
                folder_path = f"root:/{self.root_folder}/{document.document_type.code}"
            
            # Leer archivo
            with open(local_path, 'rb') as f:
                file_content = f.read()
            
            # Generar nombre único para OneDrive
            onedrive_filename = self._generate_onedrive_filename(document)
            
            # Subir archivo
            upload_result = await self.microsoft_service.upload_file_to_onedrive(
                user_access_token,
                onedrive_filename,
                file_content,
                folder_path
            )
            
            # Actualizar documento con información de OneDrive
            sync_info = {
                "onedrive_id": upload_result.get("id"),
                "onedrive_url": upload_result.get("webUrl"),
                "onedrive_filename": onedrive_filename,
                "sync_date": datetime.utcnow().isoformat(),
                "file_size": len(file_content),
                "file_hash": hashlib.sha256(file_content).hexdigest()
            }
            
            document.onedrive_sync_info = sync_info
            document.onedrive_url = upload_result.get("webUrl")
            document.onedrive_synced_at = datetime.utcnow()
            
            logger.info(f"Documento sincronizado: {document.id} -> {onedrive_filename}")
            
            return {
                "success": True,
                "action": "uploaded",
                "onedrive_id": upload_result.get("id"),
                "onedrive_url": upload_result.get("webUrl"),
                "onedrive_filename": onedrive_filename,
                "file_size": len(file_content)
            }
            
        except Exception as e:
            logger.error(f"Error sincronizando documento {document.id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "attempted_at": datetime.utcnow().isoformat()
            }
    
    async def sync_documents_batch(
        self,
        documents: List[Document],
        user_access_token: str,
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """
        Sincronizar múltiples documentos en lote
        
        Args:
            documents: Lista de documentos a sincronizar
            user_access_token: Token de acceso del usuario
            max_concurrent: Máximo de subidas concurrentes
            
        Returns:
            dict: Resultado de la sincronización en lote
        """
        try:
            logger.info(f"Sincronizando {len(documents)} documentos en lote")
            
            # Crear semáforo para limitar concurrencia
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def sync_single_document(doc):
                async with semaphore:
                    return await self.sync_document_to_onedrive(doc, user_access_token)
            
            # Ejecutar sincronización concurrente
            tasks = [sync_single_document(doc) for doc in documents]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Procesar resultados
            successful = 0
            failed = 0
            errors = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed += 1
                    errors.append({
                        "document_id": documents[i].id,
                        "error": str(result)
                    })
                elif result.get("success"):
                    successful += 1
                else:
                    failed += 1
                    errors.append({
                        "document_id": documents[i].id,
                        "error": result.get("error", "Error desconocido")
                    })
            
            logger.info(f"Sincronización en lote completada: {successful} exitosas, {failed} fallidas")
            
            return {
                "total_documents": len(documents),
                "successful": successful,
                "failed": failed,
                "errors": errors,
                "completed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error en sincronización en lote: {str(e)}")
            return {
                "total_documents": len(documents),
                "successful": 0,
                "failed": len(documents),
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat()
            }
    
    # === DESCARGA DESDE ONEDRIVE ===
    
    async def download_from_onedrive(
        self,
        onedrive_file_id: str,
        user_access_token: str,
        local_path: str
    ) -> Dict[str, Any]:
        """
        Descargar archivo desde OneDrive
        
        Args:
            onedrive_file_id: ID del archivo en OneDrive
            user_access_token: Token de acceso del usuario
            local_path: Ruta local donde guardar
            
        Returns:
            dict: Resultado de la descarga
        """
        try:
            logger.info(f"Descargando archivo desde OneDrive: {onedrive_file_id}")
            
            # Obtener información del archivo
            file_info = await self.microsoft_service.make_graph_request(
                "GET",
                f"me/drive/items/{onedrive_file_id}",
                user_access_token
            )
            
            # Descargar contenido
            download_url = file_info.get("@microsoft.graph.downloadUrl")
            if not download_url:
                raise OneDriveSyncError("URL de descarga no disponible")
            
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(download_url)
                response.raise_for_status()
                file_content = response.content
            
            # Crear directorio local si no existe
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Guardar archivo
            with open(local_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"Archivo descargado: {onedrive_file_id} -> {local_path}")
            
            return {
                "success": True,
                "local_path": local_path,
                "file_size": len(file_content),
                "file_name": file_info.get("name"),
                "downloaded_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error descargando desde OneDrive: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "attempted_at": datetime.utcnow().isoformat()
            }
    
    # === SINCRONIZACIÓN AUTOMÁTICA ===
    
    async def auto_sync_pending_documents(
        self,
        user: User,
        db: Session,
        max_documents: int = 50
    ) -> Dict[str, Any]:
        """
        Sincronizar automáticamente documentos pendientes
        
        Args:
            user: Usuario para obtener token de acceso
            db: Sesión de base de datos
            max_documents: Máximo de documentos a sincronizar
            
        Returns:
            dict: Resultado de la sincronización automática
        """
        try:
            logger.info(f"Sincronización automática para usuario {user.id}")
            
            # Verificar que el usuario tenga token de Microsoft válido
            if not user.microsoft_refresh_token:
                return {
                    "success": False,
                    "error": "Usuario no tiene token de Microsoft válido",
                    "synced_count": 0
                }
            
            # Renovar token de acceso
            try:
                from ..services.auth_service import get_auth_service
                auth_service = get_auth_service()
                access_token = await auth_service.refresh_microsoft_token(user.microsoft_refresh_token)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Error renovando token: {str(e)}",
                    "synced_count": 0
                }
            
            # Buscar documentos pendientes de sincronización
            pending_docs = db.query(Document).filter(
                Document.uploaded_by == user.id,
                Document.onedrive_url.is_(None),
                Document.status == "active"
            ).limit(max_documents).all()
            
            if not pending_docs:
                return {
                    "success": True,
                    "message": "No hay documentos pendientes de sincronización",
                    "synced_count": 0
                }
            
            # Sincronizar documentos
            sync_result = await self.sync_documents_batch(pending_docs, access_token)
            
            # Guardar cambios en base de datos
            db.commit()
            
            logger.info(f"Sincronización automática completada: {sync_result['successful']} documentos")
            
            return {
                "success": True,
                "synced_count": sync_result["successful"],
                "failed_count": sync_result["failed"],
                "errors": sync_result["errors"],
                "completed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error en sincronización automática: {str(e)}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
                "synced_count": 0,
                "attempted_at": datetime.utcnow().isoformat()
            }
    
    # === VERIFICACIÓN Y VALIDACIÓN ===
    
    async def verify_sync_integrity(
        self,
        documents: List[Document],
        user_access_token: str
    ) -> Dict[str, Any]:
        """
        Verificar integridad de documentos sincronizados
        
        Args:
            documents: Lista de documentos a verificar
            user_access_token: Token de acceso del usuario
            
        Returns:
            dict: Resultado de la verificación
        """
        try:
            logger.info(f"Verificando integridad de {len(documents)} documentos")
            
            verified = 0
            missing = 0
            corrupted = 0
            errors = []
            
            for document in documents:
                if not document.onedrive_url:
                    continue
                
                try:
                    # Verificar que el archivo existe en OneDrive
                    exists = await self._verify_onedrive_file_exists(
                        document.onedrive_url, user_access_token
                    )
                    
                    if exists:
                        # Verificar integridad si tenemos hash
                        if document.onedrive_sync_info and document.onedrive_sync_info.get("file_hash"):
                            local_path = os.path.join(settings.DOCUMENTS_PATH, document.file_path)
                            if os.path.exists(local_path):
                                local_hash = self._calculate_file_hash(local_path)
                                stored_hash = document.onedrive_sync_info.get("file_hash")
                                
                                if local_hash == stored_hash:
                                    verified += 1
                                else:
                                    corrupted += 1
                                    errors.append({
                                        "document_id": document.id,
                                        "error": "Hash no coincide - archivo posiblemente corrupto"
                                    })
                            else:
                                errors.append({
                                    "document_id": document.id,
                                    "error": "Archivo local no encontrado"
                                })
                        else:
                            verified += 1
                    else:
                        missing += 1
                        errors.append({
                            "document_id": document.id,
                            "error": "Archivo no encontrado en OneDrive"
                        })
                        
                except Exception as e:
                    errors.append({
                        "document_id": document.id,
                        "error": f"Error verificando: {str(e)}"
                    })
            
            return {
                "total_checked": len(documents),
                "verified": verified,
                "missing": missing,
                "corrupted": corrupted,
                "errors": errors,
                "verified_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error verificando integridad: {str(e)}")
            return {
                "total_checked": len(documents),
                "verified": 0,
                "missing": 0,
                "corrupted": 0,
                "error": str(e),
                "verified_at": datetime.utcnow().isoformat()
            }
    
    # === GESTIÓN DE PLANTILLAS ===
    
    async def sync_template_to_onedrive(
        self,
        template_path: str,
        template_name: str,
        user_access_token: str
    ) -> Dict[str, Any]:
        """
        Sincronizar plantilla con OneDrive
        
        Args:
            template_path: Ruta local de la plantilla
            template_name: Nombre de la plantilla
            user_access_token: Token de acceso del usuario
            
        Returns:
            dict: Resultado de la sincronización
        """
        try:
            local_path = os.path.join(settings.TEMPLATES_PATH, template_path)
            
            if not os.path.exists(local_path):
                raise OneDriveSyncError(f"Plantilla no encontrada: {template_path}")
            
            # Leer plantilla
            with open(local_path, 'rb') as f:
                template_content = f.read()
            
            # Subir a carpeta de plantillas
            upload_result = await self.microsoft_service.upload_file_to_onedrive(
                user_access_token,
                template_name,
                template_content,
                f"root:/{self.root_folder}/Templates"
            )
            
            logger.info(f"Plantilla sincronizada: {template_name}")
            
            return {
                "success": True,
                "onedrive_id": upload_result.get("id"),
                "onedrive_url": upload_result.get("webUrl"),
                "template_name": template_name,
                "file_size": len(template_content)
            }
            
        except Exception as e:
            logger.error(f"Error sincronizando plantilla: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "template_name": template_name
            }
    
    # === EXPORTACIÓN Y BACKUP ===
    
    async def export_to_onedrive(
        self,
        export_data: bytes,
        export_filename: str,
        user_access_token: str,
        folder: str = "Exports"
    ) -> Dict[str, Any]:
        """
        Exportar datos a OneDrive
        
        Args:
            export_data: Datos a exportar
            export_filename: Nombre del archivo de exportación
            user_access_token: Token de acceso del usuario
            folder: Carpeta de destino
            
        Returns:
            dict: Resultado de la exportación
        """
        try:
            # Subir archivo de exportación
            upload_result = await self.microsoft_service.upload_file_to_onedrive(
                user_access_token,
                export_filename,
                export_data,
                f"root:/{self.root_folder}/{folder}"
            )
            
            logger.info(f"Exportación subida a OneDrive: {export_filename}")
            
            return {
                "success": True,
                "onedrive_id": upload_result.get("id"),
                "onedrive_url": upload_result.get("webUrl"),
                "filename": export_filename,
                "file_size": len(export_data),
                "exported_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error exportando a OneDrive: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "filename": export_filename
            }
    
    # === MÉTODOS PRIVADOS ===
    
    def _generate_onedrive_filename(self, document: Document) -> str:
        """
        Generar nombre único para archivo en OneDrive
        
        Args:
            document: Documento
            
        Returns:
            str: Nombre único para OneDrive
        """
        # Usar ID del documento + nombre original para garantizar unicidad
        base_name, ext = os.path.splitext(document.file_name)
        safe_name = "".join(c for c in base_name if c.isalnum() or c in "._-")
        
        timestamp = document.created_at.strftime("%Y%m%d_%H%M%S")
        return f"{document.id}_{timestamp}_{safe_name}{ext}"
    
    async def _verify_onedrive_file_exists(
        self,
        onedrive_url: str,
        user_access_token: str
    ) -> bool:
        """
        Verificar que un archivo existe en OneDrive
        
        Args:
            onedrive_url: URL del archivo en OneDrive
            user_access_token: Token de acceso del usuario
            
        Returns:
            bool: True si el archivo existe
        """
        try:
            # Extraer ID del archivo de la URL
            # Esto es una implementación simplificada
            # En una implementación real sería más robusta
            import re
            match = re.search(r'/items/([A-F0-9]+)', onedrive_url)
            if not match:
                return False
            
            file_id = match.group(1)
            
            # Verificar que el archivo existe
            await self.microsoft_service.make_graph_request(
                "GET",
                f"me/drive/items/{file_id}",
                user_access_token
            )
            
            return True
            
        except Exception:
            return False
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """
        Calcular hash SHA-256 de archivo
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            str: Hash del archivo
        """
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()


# === INSTANCIA GLOBAL ===

# Instancia singleton del sincronizador
_onedrive_sync = None

def get_onedrive_sync() -> OneDriveSync:
    """
    Obtener instancia del sincronizador de OneDrive
    
    Returns:
        OneDriveSync: Instancia del sincronizador
    """
    global _onedrive_sync
    if _onedrive_sync is None:
        _onedrive_sync = OneDriveSync()
    return _onedrive_sync


# === FUNCIONES DE UTILIDAD ===

async def setup_user_onedrive(
    user: User,
    document_types: List[DocumentType],
    db: Session
) -> Dict[str, Any]:
    """
    Configurar OneDrive para un usuario
    
    Args:
        user: Usuario a configurar
        document_types: Tipos de documento disponibles
        db: Sesión de base de datos
        
    Returns:
        dict: Resultado de la configuración
    """
    try:
        if not user.microsoft_access_token:
            return {
                "success": False,
                "error": "Usuario no tiene token de Microsoft válido"
            }
        
        sync = get_onedrive_sync()
        result = await sync.setup_onedrive_structure(
            user.microsoft_access_token,
            document_types
        )
        
        # Marcar usuario como configurado
        if result["success"]:
            user.onedrive_configured = True
            user.onedrive_configured_at = datetime.utcnow()
            db.commit()
        
        return result
        
    except Exception as e:
        logger.error(f"Error configurando OneDrive para usuario {user.id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def sync_document_if_needed(
    document: Document,
    user: User,
    force: bool = False
) -> Dict[str, Any]:
    """
    Sincronizar documento con OneDrive si es necesario
    
    Args:
        document: Documento a sincronizar
        user: Usuario propietario
        force: Forzar sincronización
        
    Returns:
        dict: Resultado de la sincronización
    """
    try:
        # Verificar si necesita sincronización
        if document.onedrive_url and not force:
            return {
                "success": True,
                "action": "already_synced",
                "message": "Documento ya sincronizado"
            }
        
        if not user.microsoft_access_token:
            return {
                "success": False,
                "error": "Usuario no tiene token de Microsoft válido"
            }
        
        sync = get_onedrive_sync()
        return await sync.sync_document_to_onedrive(
            document,
            user.microsoft_access_token,
            force
        )
        
    except Exception as e:
        logger.error(f"Error sincronizando documento {document.id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def get_sync_status(document: Document) -> str:
    """
    Obtener estado de sincronización de documento
    
    Args:
        document: Documento a verificar
        
    Returns:
        str: Estado de sincronización
    """
    if not document.onedrive_url:
        return "not_synced"
    
    if not document.onedrive_synced_at:
        return "pending"
    
    # Verificar si el archivo local es más nuevo
    if document.updated_at and document.onedrive_synced_at:
        if document.updated_at > document.onedrive_synced_at:
            return "out_of_sync"
    
    return "synced"


async def batch_sync_user_documents(
    user: User,
    db: Session,
    max_documents: int = 100
) -> Dict[str, Any]:
    """
    Sincronizar todos los documentos de un usuario
    
    Args:
        user: Usuario
        db: Sesión de base de datos
        max_documents: Máximo de documentos a procesar
        
    Returns:
        dict: Resultado de la sincronización
    """
    try:
        # Obtener documentos del usuario que no están sincronizados
        documents = db.query(Document).filter(
            Document.uploaded_by == user.id,
            Document.onedrive_url.is_(None),
            Document.status == "active"
        ).limit(max_documents).all()
        
        if not documents:
            return {
                "success": True,
                "message": "No hay documentos para sincronizar",
                "synced_count": 0
            }
        
        if not user.microsoft_access_token:
            return {
                "success": False,
                "error": "Usuario no tiene token de Microsoft válido",
                "synced_count": 0
            }
        
        sync = get_onedrive_sync()
        result = await sync.sync_documents_batch(
            documents,
            user.microsoft_access_token
        )
        
        # Guardar cambios
        db.commit()
        
        return result
        
    except Exception as e:
        logger.error(f"Error en sincronización masiva: {str(e)}")
        db.rollback()
        return {
            "success": False,
            "error": str(e),
            "synced_count": 0
        }


def check_onedrive_health(user: User) -> Dict[str, Any]:
    """
    Verificar estado de salud de OneDrive para usuario
    
    Args:
        user: Usuario a verificar
        
    Returns:
        dict: Estado de salud
    """
    try:
        issues = []
        warnings = []
        
        # Verificar configuración básica
        if not user.microsoft_access_token:
            issues.append("Usuario no tiene token de Microsoft")
        
        if not user.onedrive_configured:
            warnings.append("OneDrive no está configurado")
        
        # Verificar documentos no sincronizados
        # Esto requeriría una sesión de BD, simplificado por ahora
        
        status = "healthy"
        if issues:
            status = "unhealthy"
        elif warnings:
            status = "warning"
        
        return {
            "status": status,
            "user_id": user.id,
            "microsoft_token_valid": bool(user.microsoft_access_token),
            "onedrive_configured": user.onedrive_configured,
            "configured_at": user.onedrive_configured_at.isoformat() if user.onedrive_configured_at else None,
            "issues": issues,
            "warnings": warnings,
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error verificando salud de OneDrive: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "checked_at": datetime.utcnow().isoformat()
        }


async def cleanup_onedrive_orphaned_files(
    user_access_token: str,
    known_document_ids: List[int]
) -> Dict[str, Any]:
    """
    Limpiar archivos huérfanos en OneDrive
    
    Args:
        user_access_token: Token de acceso del usuario
        known_document_ids: IDs de documentos conocidos en el sistema
        
    Returns:
        dict: Resultado de la limpieza
    """
    try:
        logger.info("Limpiando archivos huérfanos en OneDrive")
        
        microsoft_service = get_microsoft_service()
        sync = get_onedrive_sync()
        
        # Listar archivos en la carpeta raíz de SGD
        folder_contents = await microsoft_service.make_graph_request(
            "GET",
            f"me/drive/root:/{sync.root_folder}:/children",
            user_access_token
        )
        
        orphaned_files = []
        deleted_count = 0
        
        for item in folder_contents.get("value", []):
            if item.get("file"):  # Es un archivo, no carpeta
                filename = item.get("name", "")
                
                # Extraer ID del documento del nombre del archivo
                import re
                match = re.match(r"^(\d+)_", filename)
                if match:
                    doc_id = int(match.group(1))
                    if doc_id not in known_document_ids:
                        orphaned_files.append({
                            "onedrive_id": item.get("id"),
                            "filename": filename,
                            "document_id": doc_id
                        })
        
        # Opcionalmente eliminar archivos huérfanos
        # Por seguridad, solo los reportamos por ahora
        
        return {
            "orphaned_files_found": len(orphaned_files),
            "deleted_count": deleted_count,
            "orphaned_files": orphaned_files,
            "cleaned_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error limpiando archivos huérfanos: {str(e)}")
        return {
            "orphaned_files_found": 0,
            "deleted_count": 0,
            "error": str(e),
            "cleaned_at": datetime.utcnow().isoformat()
        }


def get_onedrive_recommendations(user: User, document_count: int = 0) -> List[str]:
    """
    Obtener recomendaciones para OneDrive
    
    Args:
        user: Usuario
        document_count: Número de documentos no sincronizados
        
    Returns:
        List[str]: Lista de recomendaciones
    """
    recommendations = []
    
    try:
        if not user.microsoft_access_token:
            recommendations.append("Conectar con Microsoft 365 para habilitar sincronización")
            return recommendations
        
        if not user.onedrive_configured:
            recommendations.append("Configurar estructura de carpetas en OneDrive")
        
        if document_count > 0:
            recommendations.append(f"Sincronizar {document_count} documentos pendientes")
        
        if user.onedrive_configured_at:
            days_since_config = (datetime.utcnow() - user.onedrive_configured_at).days
            if days_since_config > 30:
                recommendations.append("Verificar integridad de archivos sincronizados")
        
        # Recomendaciones generales
        recommendations.extend([
            "Verificar periódicamente el estado de sincronización",
            "Mantener token de Microsoft actualizado",
            "Revisar archivos huérfanos en OneDrive"
        ])
        
        if not recommendations:
            recommendations.append("OneDrive está correctamente configurado y sincronizado")
        
    except Exception as e:
        recommendations.append(f"Error obteniendo recomendaciones: {str(e)}")
    
    return recommendations


# === CONFIGURACIÓN DE TAREAS AUTOMÁTICAS ===

async def schedule_auto_sync(
    user_id: int,
    db: Session,
    interval_hours: int = 24
) -> bool:
    """
    Programar sincronización automática para usuario
    
    Args:
        user_id: ID del usuario
        db: Sesión de base de datos
        interval_hours: Intervalo en horas
        
    Returns:
        bool: True si se programó exitosamente
    """
    try:
        # Esta función sería implementada con un sistema de tareas como Celery
        # Por ahora solo registramos la intención
        
        logger.info(f"Programando sync automático para usuario {user_id} cada {interval_hours} horas")
        
        # Aquí se agregaría la lógica para programar la tarea
        # Ejemplo con Celery:
        # from .tasks import auto_sync_user_documents
        # auto_sync_user_documents.apply_async(
        #     args=[user_id],
        #     countdown=interval_hours * 3600
        # )
        
        return True
        
    except Exception as e:
        logger.error(f"Error programando sync automático: {str(e)}")
        return False


async def get_sync_statistics(
    user_id: Optional[int] = None,
    db: Session = None
) -> Dict[str, Any]:
    """
    Obtener estadísticas de sincronización
    
    Args:
        user_id: ID del usuario (opcional, para estadísticas globales)
        db: Sesión de base de datos
        
    Returns:
        dict: Estadísticas de sincronización
    """
    try:
        if not db:
            return {"error": "Sesión de base de datos requerida"}
        
        # Query base
        query = db.query(Document)
        
        if user_id:
            query = query.filter(Document.uploaded_by == user_id)
        
        # Estadísticas básicas
        total_documents = query.count()
        synced_documents = query.filter(Document.onedrive_url.isnot(None)).count()
        pending_sync = total_documents - synced_documents
        
        # Documentos sincronizados en últimas 24 horas
        yesterday = datetime.utcnow() - timedelta(days=1)
        recently_synced = query.filter(
            Document.onedrive_synced_at >= yesterday
        ).count()
        
        # Calcular tasa de sincronización
        sync_rate = (synced_documents / total_documents * 100) if total_documents > 0 else 0
        
        return {
            "total_documents": total_documents,
            "synced_documents": synced_documents,
            "pending_sync": pending_sync,
            "sync_rate": round(sync_rate, 2),
            "recently_synced": recently_synced,
            "user_id": user_id,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        return {
            "error": str(e),
            "generated_at": datetime.utcnow().isoformat()
        }


# === FUNCIONES DE MIGRACIÓN ===

async def migrate_existing_documents_to_onedrive(
    user: User,
    db: Session,
    batch_size: int = 10
) -> Dict[str, Any]:
    """
    Migrar documentos existentes a OneDrive
    
    Args:
        user: Usuario propietario de los documentos
        db: Sesión de base de datos
        batch_size: Tamaño del lote para procesamiento
        
    Returns:
        dict: Resultado de la migración
    """
    try:
        logger.info(f"Iniciando migración de documentos a OneDrive para usuario {user.id}")
        
        if not user.microsoft_access_token:
            return {
                "success": False,
                "error": "Usuario no tiene token de Microsoft válido",
                "migrated_count": 0
            }
        
        # Configurar OneDrive si no está configurado
        if not user.onedrive_configured:
            document_types = db.query(DocumentType).filter(DocumentType.is_active == True).all()
            setup_result = await setup_user_onedrive(user, document_types, db)
            
            if not setup_result["success"]:
                return {
                    "success": False,
                    "error": f"Error configurando OneDrive: {setup_result.get('error')}",
                    "migrated_count": 0
                }
        
        # Obtener documentos no sincronizados
        documents = db.query(Document).filter(
            Document.uploaded_by == user.id,
            Document.onedrive_url.is_(None),
            Document.status == "active"
        ).all()
        
        if not documents:
            return {
                "success": True,
                "message": "No hay documentos para migrar",
                "migrated_count": 0
            }
        
        total_migrated = 0
        total_errors = 0
        errors = []
        
        # Procesar en lotes
        sync = get_onedrive_sync()
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            try:
                batch_result = await sync.sync_documents_batch(
                    batch,
                    user.microsoft_access_token
                )
                
                total_migrated += batch_result["successful"]
                total_errors += batch_result["failed"]
                errors.extend(batch_result["errors"])
                
                # Guardar progreso
                db.commit()
                
                # Pausa entre lotes para no sobrecargar la API
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error en lote de migración: {str(e)}")
                total_errors += len(batch)
                errors.append({
                    "batch": f"Lote {i//batch_size + 1}",
                    "error": str(e)
                })
        
        success_rate = (total_migrated / len(documents) * 100) if documents else 0
        
        logger.info(f"Migración completada: {total_migrated}/{len(documents)} documentos migrados")
        
        return {
            "success": total_errors == 0,
            "total_documents": len(documents),
            "migrated_count": total_migrated,
            "failed_count": total_errors,
            "success_rate": round(success_rate, 2),
            "errors": errors,
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en migración: {str(e)}")
        db.rollback()
        return {
            "success": False,
            "error": str(e),
            "migrated_count": 0,
            "attempted_at": datetime.utcnow().isoformat()
        }