"""
Servicio de gestión de almacenamiento
Manejo de archivos locales, OneDrive y operaciones de almacenamiento
"""
import logging
import os
import shutil
import hashlib
import mimetypes
from typing import List, Optional, Dict, Any, Tuple, BinaryIO
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import zipfile
import json

from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile

from ..config import get_settings
from ..models.user import User
from ..models.document import Document
from ..utils.file_handler import get_file_handler
from ..services.microsoft_service import get_microsoft_service

# Configuración
settings = get_settings()
logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Excepción personalizada para errores de almacenamiento"""
    pass


class StorageService:
    """Servicio principal para gestión de almacenamiento"""
    
    def __init__(self):
        """Inicializar el servicio de almacenamiento"""
        self.documents_path = settings.DOCUMENTS_PATH
        self.temp_path = settings.TEMP_PATH
        self.templates_path = settings.TEMPLATES_PATH
        self.file_handler = get_file_handler()
        self.microsoft_service = get_microsoft_service()
        
        # Asegurar que existan los directorios
        self._ensure_directories()
        
        logger.info("StorageService inicializado")
    
    def _ensure_directories(self):
        """Asegurar que existan todos los directorios necesarios"""
        directories = [
            self.documents_path,
            self.temp_path,
            self.templates_path,
            os.path.join(self.documents_path, "archived"),
            os.path.join(self.temp_path, "uploads"),
            os.path.join(self.temp_path, "exports"),
            os.path.join(self.temp_path, "qr"),
            os.path.join(self.temp_path, "generated")
        ]
        
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                logger.debug(f"Directorio verificado: {directory}")
            except Exception as e:
                logger.error(f"Error creando directorio {directory}: {str(e)}")
                raise StorageError(f"No se pudo crear directorio: {directory}")
    
    # === OPERACIONES DE ARCHIVOS ===
    
    async def store_file(
        self,
        file: UploadFile,
        storage_path: str,
        calculate_hash: bool = True
    ) -> Dict[str, Any]:
        """
        Almacenar archivo en el sistema
        
        Args:
            file: Archivo a almacenar
            storage_path: Ruta relativa donde almacenar
            calculate_hash: Calcular hash del archivo
            
        Returns:
            dict: Información del archivo almacenado
        """
        try:
            # Ruta completa
            full_path = os.path.join(self.documents_path, storage_path)
            
            # Asegurar que existe el directorio padre
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Leer contenido del archivo
            content = await file.read()
            file_size = len(content)
            
            # Detectar tipo MIME
            mime_type, _ = mimetypes.guess_type(file.filename or "")
            if not mime_type:
                mime_type = "application/octet-stream"
            
            # Calcular hash si se solicita
            file_hash = None
            if calculate_hash:
                file_hash = hashlib.sha256(content).hexdigest()
            
            # Guardar archivo
            with open(full_path, 'wb') as f:
                f.write(content)
            
            # Verificar que se guardó correctamente
            if not os.path.exists(full_path):
                raise StorageError("El archivo no se guardó correctamente")
            
            actual_size = os.path.getsize(full_path)
            if actual_size != file_size:
                raise StorageError("El tamaño del archivo no coincide")
            
            logger.info(f"Archivo almacenado: {storage_path} ({file_size} bytes)")
            
            return {
                "storage_path": storage_path,
                "full_path": full_path,
                "file_size": file_size,
                "mime_type": mime_type,
                "file_hash": file_hash,
                "stored_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error almacenando archivo: {str(e)}")
            # Limpiar archivo parcial si existe
            try:
                if 'full_path' in locals() and os.path.exists(full_path):
                    os.remove(full_path)
            except:
                pass
            raise StorageError(f"Error almacenando archivo: {str(e)}")
    
    def get_file_info(self, storage_path: str) -> Dict[str, Any]:
        """
        Obtener información de archivo almacenado
        
        Args:
            storage_path: Ruta relativa del archivo
            
        Returns:
            dict: Información del archivo
        """
        try:
            full_path = os.path.join(self.documents_path, storage_path)
            
            if not os.path.exists(full_path):
                raise StorageError(f"Archivo no encontrado: {storage_path}")
            
            stat = os.stat(full_path)
            
            return {
                "storage_path": storage_path,
                "full_path": full_path,
                "exists": True,
                "size": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "is_readable": os.access(full_path, os.R_OK),
                "is_writable": os.access(full_path, os.W_OK),
                "mime_type": mimetypes.guess_type(full_path)[0]
            }
            
        except StorageError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo info de archivo: {str(e)}")
            raise StorageError(f"Error obteniendo información: {str(e)}")
    
    def move_file(self, source_path: str, dest_path: str) -> bool:
        """
        Mover archivo dentro del almacenamiento
        
        Args:
            source_path: Ruta origen relativa
            dest_path: Ruta destino relativa
            
        Returns:
            bool: True si se movió exitosamente
        """
        try:
            source_full = os.path.join(self.documents_path, source_path)
            dest_full = os.path.join(self.documents_path, dest_path)
            
            if not os.path.exists(source_full):
                raise StorageError(f"Archivo origen no existe: {source_path}")
            
            # Crear directorio destino si no existe
            os.makedirs(os.path.dirname(dest_full), exist_ok=True)
            
            # Mover archivo
            shutil.move(source_full, dest_full)
            
            logger.info(f"Archivo movido: {source_path} -> {dest_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error moviendo archivo: {str(e)}")
            raise StorageError(f"Error moviendo archivo: {str(e)}")
    
    def copy_file(self, source_path: str, dest_path: str) -> bool:
        """
        Copiar archivo dentro del almacenamiento
        
        Args:
            source_path: Ruta origen relativa
            dest_path: Ruta destino relativa
            
        Returns:
            bool: True si se copió exitosamente
        """
        try:
            source_full = os.path.join(self.documents_path, source_path)
            dest_full = os.path.join(self.documents_path, dest_path)
            
            if not os.path.exists(source_full):
                raise StorageError(f"Archivo origen no existe: {source_path}")
            
            # Crear directorio destino si no existe
            os.makedirs(os.path.dirname(dest_full), exist_ok=True)
            
            # Copiar archivo
            shutil.copy2(source_full, dest_full)
            
            logger.info(f"Archivo copiado: {source_path} -> {dest_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error copiando archivo: {str(e)}")
            raise StorageError(f"Error copiando archivo: {str(e)}")
    
    def delete_file(self, storage_path: str, force: bool = False) -> bool:
        """
        Eliminar archivo del almacenamiento
        
        Args:
            storage_path: Ruta relativa del archivo
            force: Forzar eliminación sin mover a papelera
            
        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            full_path = os.path.join(self.documents_path, storage_path)
            
            if not os.path.exists(full_path):
                logger.warning(f"Archivo no existe para eliminar: {storage_path}")
                return True
            
            if force:
                # Eliminación permanente
                os.remove(full_path)
                logger.info(f"Archivo eliminado permanentemente: {storage_path}")
            else:
                # Mover a papelera (carpeta archived)
                archived_path = os.path.join(
                    self.documents_path, 
                    "archived", 
                    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(storage_path)}"
                )
                shutil.move(full_path, archived_path)
                logger.info(f"Archivo archivado: {storage_path} -> archived/")
            
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando archivo: {str(e)}")
            raise StorageError(f"Error eliminando archivo: {str(e)}")
    
    def read_file(self, storage_path: str) -> bytes:
        """
        Leer contenido de archivo almacenado
        
        Args:
            storage_path: Ruta relativa del archivo
            
        Returns:
            bytes: Contenido del archivo
        """
        try:
            full_path = os.path.join(self.documents_path, storage_path)
            
            if not os.path.exists(full_path):
                raise StorageError(f"Archivo no encontrado: {storage_path}")
            
            with open(full_path, 'rb') as f:
                content = f.read()
            
            logger.debug(f"Archivo leído: {storage_path} ({len(content)} bytes)")
            return content
            
        except StorageError:
            raise
        except Exception as e:
            logger.error(f"Error leyendo archivo: {str(e)}")
            raise StorageError(f"Error leyendo archivo: {str(e)}")
    
    # === OPERACIONES DE DIRECTORIO ===
    
    def create_directory(self, dir_path: str) -> bool:
        """
        Crear directorio en el almacenamiento
        
        Args:
            dir_path: Ruta relativa del directorio
            
        Returns:
            bool: True si se creó exitosamente
        """
        try:
            full_path = os.path.join(self.documents_path, dir_path)
            os.makedirs(full_path, exist_ok=True)
            
            logger.info(f"Directorio creado: {dir_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creando directorio: {str(e)}")
            raise StorageError(f"Error creando directorio: {str(e)}")
    
    def list_directory(self, dir_path: str = "") -> List[Dict[str, Any]]:
        """
        Listar contenido de directorio
        
        Args:
            dir_path: Ruta relativa del directorio
            
        Returns:
            List[dict]: Lista de archivos y directorios
        """
        try:
            full_path = os.path.join(self.documents_path, dir_path)
            
            if not os.path.exists(full_path):
                raise StorageError(f"Directorio no encontrado: {dir_path}")
            
            items = []
            
            for item_name in os.listdir(full_path):
                item_path = os.path.join(full_path, item_name)
                item_stat = os.stat(item_path)
                
                item_info = {
                    "name": item_name,
                    "path": os.path.join(dir_path, item_name).replace("\\", "/"),
                    "is_file": os.path.isfile(item_path),
                    "is_directory": os.path.isdir(item_path),
                    "size": item_stat.st_size,
                    "modified": datetime.fromtimestamp(item_stat.st_mtime).isoformat(),
                    "mime_type": mimetypes.guess_type(item_path)[0] if os.path.isfile(item_path) else None
                }
                
                items.append(item_info)
            
            # Ordenar por tipo (directorios primero) y luego por nombre
            items.sort(key=lambda x: (not x["is_directory"], x["name"].lower()))
            
            return items
            
        except StorageError:
            raise
        except Exception as e:
            logger.error(f"Error listando directorio: {str(e)}")
            raise StorageError(f"Error listando directorio: {str(e)}")
    
    def get_directory_stats(self, dir_path: str = "") -> Dict[str, Any]:
        """
        Obtener estadísticas de directorio
        
        Args:
            dir_path: Ruta relativa del directorio
            
        Returns:
            dict: Estadísticas del directorio
        """
        try:
            full_path = os.path.join(self.documents_path, dir_path)
            
            if not os.path.exists(full_path):
                raise StorageError(f"Directorio no encontrado: {dir_path}")
            
            total_files = 0
            total_directories = 0
            total_size = 0
            file_types = {}
            
            for root, dirs, files in os.walk(full_path):
                total_directories += len(dirs)
                
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    file_size = os.path.getsize(file_path)
                    
                    total_files += 1
                    total_size += file_size
                    
                    # Contar tipos de archivo
                    _, ext = os.path.splitext(file_name)
                    ext = ext.lower()
                    file_types[ext] = file_types.get(ext, 0) + 1
            
            return {
                "path": dir_path,
                "total_files": total_files,
                "total_directories": total_directories,
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "total_size_gb": round(total_size / (1024 * 1024 * 1024), 2),
                "file_types": file_types,
                "calculated_at": datetime.utcnow().isoformat()
            }
            
        except StorageError:
            raise
        except Exception as e:
            logger.error(f"Error calculando estadísticas: {str(e)}")
            raise StorageError(f"Error calculando estadísticas: {str(e)}")
    
    # === OPERACIONES DE BACKUP ===
    
    def create_backup(
        self,
        backup_name: Optional[str] = None,
        include_archived: bool = False
    ) -> str:
        """
        Crear backup del almacenamiento
        
        Args:
            backup_name: Nombre del backup (se genera automáticamente si no se proporciona)
            include_archived: Incluir archivos archivados
            
        Returns:
            str: Ruta del archivo de backup
        """
        try:
            if not backup_name:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_path = os.path.join(self.temp_path, f"{backup_name}.zip")
            
            logger.info(f"Creando backup: {backup_name}")
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.documents_path):
                    # Excluir carpeta archived si no se solicita
                    if not include_archived and "archived" in dirs:
                        dirs.remove("archived")
                    
                    for file_name in files:
                        file_path = os.path.join(root, file_name)
                        arcname = os.path.relpath(file_path, self.documents_path)
                        zipf.write(file_path, arcname)
            
            backup_size = os.path.getsize(backup_path)
            logger.info(f"Backup creado: {backup_path} ({backup_size} bytes)")
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Error creando backup: {str(e)}")
            raise StorageError(f"Error creando backup: {str(e)}")
    
    def restore_backup(self, backup_path: str, overwrite: bool = False) -> bool:
        """
        Restaurar desde backup
        
        Args:
            backup_path: Ruta del archivo de backup
            overwrite: Sobrescribir archivos existentes
            
        Returns:
            bool: True si se restauró exitosamente
        """
        try:
            if not os.path.exists(backup_path):
                raise StorageError(f"Archivo de backup no encontrado: {backup_path}")
            
            logger.info(f"Restaurando desde backup: {backup_path}")
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                for member in zipf.infolist():
                    extract_path = os.path.join(self.documents_path, member.filename)
                    
                    # Verificar si el archivo ya existe
                    if os.path.exists(extract_path) and not overwrite:
                        logger.warning(f"Archivo ya existe, omitiendo: {member.filename}")
                        continue
                    
                    # Crear directorio padre si no existe
                    os.makedirs(os.path.dirname(extract_path), exist_ok=True)
                    
                    # Extraer archivo
                    zipf.extract(member, self.documents_path)
            
            logger.info("Backup restaurado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error restaurando backup: {str(e)}")
            raise StorageError(f"Error restaurando backup: {str(e)}")
    
    # === LIMPIEZA Y MANTENIMIENTO ===
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Limpiar archivos temporales antiguos
        
        Args:
            max_age_hours: Edad máxima en horas
            
        Returns:
            dict: Resultado de la limpieza
        """
        try:
            logger.info(f"Limpiando archivos temporales mayores a {max_age_hours} horas")
            
            current_time = datetime.now()
            deleted_count = 0
            total_size = 0
            errors = []
            
            for root, dirs, files in os.walk(self.temp_path):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    
                    try:
                        file_stat = os.stat(file_path)
                        file_age = current_time - datetime.fromtimestamp(file_stat.st_mtime)
                        
                        if file_age.total_seconds() > (max_age_hours * 3600):
                            file_size = file_stat.st_size
                            os.remove(file_path)
                            deleted_count += 1
                            total_size += file_size
                            
                    except Exception as e:
                        errors.append(f"Error procesando {file_path}: {str(e)}")
            
            # Limpiar directorios vacíos
            for root, dirs, files in os.walk(self.temp_path, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        if not os.listdir(dir_path):  # Directorio vacío
                            os.rmdir(dir_path)
                    except:
                        pass
            
            size_mb = round(total_size / (1024 * 1024), 2)
            
            result = {
                "deleted_files": deleted_count,
                "freed_size_mb": size_mb,
                "errors": errors,
                "cleaned_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Limpieza completada: {deleted_count} archivos eliminados ({size_mb} MB)")
            return result
            
        except Exception as e:
            logger.error(f"Error en limpieza: {str(e)}")
            return {
                "deleted_files": 0,
                "freed_size_mb": 0,
                "errors": [str(e)],
                "cleaned_at": datetime.utcnow().isoformat()
            }
    
    def cleanup_archived_files(self, max_age_days: int = 90) -> Dict[str, Any]:
        """
        Limpiar archivos archivados antiguos
        
        Args:
            max_age_days: Edad máxima en días
            
        Returns:
            dict: Resultado de la limpieza
        """
        try:
            archived_path = os.path.join(self.documents_path, "archived")
            
            if not os.path.exists(archived_path):
                return {
                    "deleted_files": 0,
                    "freed_size_mb": 0,
                    "message": "No existe carpeta de archivos archivados"
                }
            
            logger.info(f"Limpiando archivos archivados mayores a {max_age_days} días")
            
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(days=max_age_days)
            
            deleted_count = 0
            total_size = 0
            
            for file_name in os.listdir(archived_path):
                file_path = os.path.join(archived_path, file_name)
                
                if os.path.isfile(file_path):
                    file_stat = os.stat(file_path)
                    file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
                    
                    if file_mtime < cutoff_time:
                        file_size = file_stat.st_size
                        os.remove(file_path)
                        deleted_count += 1
                        total_size += file_size
            
            size_mb = round(total_size / (1024 * 1024), 2)
            
            result = {
                "deleted_files": deleted_count,
                "freed_size_mb": size_mb,
                "max_age_days": max_age_days,
                "cleaned_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Archivos antiguos eliminados: {deleted_count} archivos ({size_mb} MB)")
            return result
            
        except Exception as e:
            logger.error(f"Error limpiando archivos archivados: {str(e)}")
            return {
                "deleted_files": 0,
                "freed_size_mb": 0,
                "error": str(e)
            }
    
    def verify_storage_integrity(self, fix_issues: bool = False) -> Dict[str, Any]:
        """
        Verificar integridad del almacenamiento
        
        Args:
            fix_issues: Intentar corregir problemas encontrados
            
        Returns:
            dict: Reporte de integridad
        """
        try:
            logger.info("Verificando integridad del almacenamiento")
            
            issues = []
            warnings = []
            fixed = []
            
            # Verificar estructura de directorios
            required_dirs = [
                self.documents_path,
                self.temp_path,
                self.templates_path,
                os.path.join(self.documents_path, "archived")
            ]
            
            for directory in required_dirs:
                if not os.path.exists(directory):
                    issues.append(f"Directorio faltante: {directory}")
                    if fix_issues:
                        try:
                            os.makedirs(directory, exist_ok=True)
                            fixed.append(f"Directorio creado: {directory}")
                        except Exception as e:
                            issues.append(f"No se pudo crear {directory}: {str(e)}")
                elif not os.access(directory, os.W_OK):
                    issues.append(f"Directorio sin permisos de escritura: {directory}")
            
            # Verificar espacio en disco
            disk_usage = shutil.disk_usage(self.documents_path)
            free_space_gb = disk_usage.free / (1024**3)
            
            if free_space_gb < 1:  # Menos de 1GB libre
                issues.append(f"Poco espacio en disco: {free_space_gb:.2f} GB libres")
            elif free_space_gb < 5:  # Menos de 5GB libre
                warnings.append(f"Espacio en disco limitado: {free_space_gb:.2f} GB libres")
            
            # Verificar archivos huérfanos en temp
            temp_files = 0
            for root, dirs, files in os.walk(self.temp_path):
                temp_files += len(files)
            
            if temp_files > 1000:
                warnings.append(f"Muchos archivos temporales: {temp_files}")
            
            # Determinar estado general
            status = "healthy"
            if issues:
                status = "unhealthy"
            elif warnings:
                status = "warning"
            
            result = {
                "status": status,
                "issues": issues,
                "warnings": warnings,
                "fixed": fixed if fix_issues else [],
                "disk_space": {
                    "total_gb": round(disk_usage.total / (1024**3), 2),
                    "used_gb": round(disk_usage.used / (1024**3), 2),
                    "free_gb": round(free_space_gb, 2),
                    "used_percent": round((disk_usage.used / disk_usage.total) * 100, 1)
                },
                "temp_files_count": temp_files,
                "checked_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Verificación completada: status={status}, issues={len(issues)}, warnings={len(warnings)}")
            return result
            
        except Exception as e:
            logger.error(f"Error verificando integridad: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "checked_at": datetime.utcnow().isoformat()
            }
    
    # === INTEGRACIÓN CON ONEDRIVE ===
    
    async def sync_to_onedrive(
        self,
        storage_path: str,
        user_access_token: str,
        onedrive_folder: str = "SGD_Documents"
    ) -> Dict[str, Any]:
        """
        Sincronizar archivo con OneDrive
        
        Args:
            storage_path: Ruta relativa del archivo
            user_access_token: Token de acceso del usuario
            onedrive_folder: Carpeta en OneDrive
            
        Returns:
            dict: Resultado de la sincronización
        """
        try:
            # Verificar que existe el archivo
            full_path = os.path.join(self.documents_path, storage_path)
            if not os.path.exists(full_path):
                raise StorageError(f"Archivo no encontrado: {storage_path}")
            
            # Leer contenido del archivo
            with open(full_path, 'rb') as f:
                file_content = f.read()
            
            # Crear carpeta en OneDrive si no existe
            try:
                await self.microsoft_service.create_onedrive_folder(
                    user_access_token, onedrive_folder
                )
            except:
                pass  # La carpeta ya puede existir
            
            # Subir archivo a OneDrive
            file_name = os.path.basename(storage_path)
            upload_result = await self.microsoft_service.upload_file_to_onedrive(
                user_access_token,
                file_name,
                file_content,
                f"root:/{onedrive_folder}"
            )
            
            logger.info(f"Archivo sincronizado con OneDrive: {storage_path}")
            
            return {
                "success": True,
                "onedrive_id": upload_result.get("id"),
                "onedrive_url": upload_result.get("webUrl"),
                "file_size": len(file_content),
                "synced_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sincronizando con OneDrive: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "attempted_at": datetime.utcnow().isoformat()
            }
    
    # === BÚSQUEDA DE ARCHIVOS ===
    
    def search_files(
        self,
        query: str,
        file_types: Optional[List[str]] = None,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Buscar archivos en el almacenamiento
        
        Args:
            query: Término de búsqueda
            file_types: Tipos de archivo a incluir
            max_results: Número máximo de resultados
            
        Returns:
            List[dict]: Lista de archivos encontrados
        """
        try:
            logger.info(f"Buscando archivos: '{query}'")
            
            results = []
            query_lower = query.lower()
            
            for root, dirs, files in os.walk(self.documents_path):
                # Excluir carpeta archived
                if "archived" in dirs:
                    dirs.remove("archived")
                
                for file_name in files:
                    if len(results) >= max_results:
                        break
                    
                    # Buscar en nombre de archivo
                    if query_lower in file_name.lower():
                        file_path = os.path.join(root, file_name)
                        relative_path = os.path.relpath(file_path, self.documents_path)
                        
                        # Filtrar por tipo de archivo si se especifica
                        if file_types:
                            _, ext = os.path.splitext(file_name)
                            if ext.lower() not in file_types:
                                continue
                        
                        file_stat = os.stat(file_path)
                        
                        result = {
                            "name": file_name,
                            "path": relative_path.replace("\\", "/"),
                            "size": file_stat.st_size,
                            "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                            "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                            "mime_type": mimetypes.guess_type(file_path)[0],
                            "directory": os.path.dirname(relative_path).replace("\\", "/")
                        }
                        
                        results.append(result)
            
            logger.info(f"Búsqueda completada: {len(results)} archivos encontrados")
            return results
            
        except Exception as e:
            logger.error(f"Error buscando archivos: {str(e)}")
            return []
    
    # === ESTADÍSTICAS GENERALES ===
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas generales del almacenamiento
        
        Returns:
            dict: Estadísticas del almacenamiento
        """
        try:
            # Estadísticas de documentos
            docs_stats = self.get_directory_stats("")
            
            # Estadísticas de archivos temporales
            temp_stats = self.get_directory_stats(os.path.relpath(self.temp_path, self.documents_path))
            
            # Estadísticas de plantillas
            templates_stats = self.get_directory_stats(os.path.relpath(self.templates_path, self.documents_path))
            
            # Espacio en disco
            disk_usage = shutil.disk_usage(self.documents_path)
            
            # Archivos por tipo
            file_types = {}
            for root, dirs, files in os.walk(self.documents_path):
                if "archived" in dirs:
                    dirs.remove("archived")
                
                for file_name in files:
                    _, ext = os.path.splitext(file_name)
                    ext = ext.lower() or "sin_extension"
                    file_types[ext] = file_types.get(ext, 0) + 1
            
            # Top 10 tipos de archivo
            top_file_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "summary": {
                    "total_files": docs_stats["total_files"],
                    "total_size_gb": docs_stats["total_size_gb"],
                    "temp_files": temp_stats.get("total_files", 0),
                    "templates": templates_stats.get("total_files", 0)
                },
                "disk_usage": {
                    "total_gb": round(disk_usage.total / (1024**3), 2),
                    "used_gb": round(disk_usage.used / (1024**3), 2),
                    "free_gb": round(disk_usage.free / (1024**3), 2),
                    "used_percent": round((disk_usage.used / disk_usage.total) * 100, 1)
                },
                "by_directory": {
                    "documents": docs_stats,
                    "temp": temp_stats,
                    "templates": templates_stats
                },
                "file_types": dict(top_file_types),
                "paths": {
                    "documents": self.documents_path,
                    "temp": self.temp_path,
                    "templates": self.templates_path
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }


# === INSTANCIA GLOBAL ===

# Instancia singleton del servicio
_storage_service = None

def get_storage_service() -> StorageService:
    """
    Obtener instancia del servicio de almacenamiento
    
    Returns:
        StorageService: Instancia del servicio
    """
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service


# === FUNCIONES DE UTILIDAD ===

def generate_storage_path(
    document_type_code: str,
    user_id: int,
    filename: str,
    date: Optional[datetime] = None
) -> str:
    """
    Generar ruta de almacenamiento para documento
    
    Args:
        document_type_code: Código del tipo de documento
        user_id: ID del usuario
        filename: Nombre del archivo
        date: Fecha (usa actual si no se especifica)
        
    Returns:
        str: Ruta relativa de almacenamiento
    """
    if not date:
        date = datetime.now()
    
    # Limpiar nombre de archivo
    safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
    
    # Crear estructura de carpetas por fecha y tipo
    date_path = date.strftime("%Y/%m/%d")
    storage_path = f"{document_type_code.lower()}/{date_path}/{user_id}_{safe_filename}"
    
    return storage_path


def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> Optional[str]:
    """
    Calcular hash de archivo
    
    Args:
        file_path: Ruta del archivo
        algorithm: Algoritmo de hash (md5, sha1, sha256)
        
    Returns:
        Optional[str]: Hash del archivo o None si hay error
    """
    try:
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
        
    except Exception as e:
        logger.error(f"Error calculando hash: {str(e)}")
        return None


def validate_storage_path(storage_path: str) -> bool:
    """
    Validar que la ruta de almacenamiento sea segura
    
    Args:
        storage_path: Ruta a validar
        
    Returns:
        bool: True si es válida
    """
    # Verificar que no haya secuencias peligrosas
    dangerous_patterns = ["../", "..\\", "/.", "\\."]
    
    for pattern in dangerous_patterns:
        if pattern in storage_path:
            return False
    
    # Verificar que sea una ruta relativa
    if os.path.isabs(storage_path):
        return False
    
    return True


def get_file_extension(filename: str) -> str:
    """
    Obtener extensión de archivo de forma segura
    
    Args:
        filename: Nombre del archivo
        
    Returns:
        str: Extensión en minúsculas
    """
    _, ext = os.path.splitext(filename)
    return ext.lower()


def format_file_size(size_bytes: int) -> str:
    """
    Formatear tamaño de archivo de forma legible
    
    Args:
        size_bytes: Tamaño en bytes
        
    Returns:
        str: Tamaño formateado
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/(1024**2):.1f} MB"
    else:
        return f"{size_bytes/(1024**3):.1f} GB"


def is_safe_filename(filename: str) -> bool:
    """
    Verificar que el nombre de archivo sea seguro
    
    Args:
        filename: Nombre a verificar
        
    Returns:
        bool: True si es seguro
    """
    # Caracteres prohibidos
    forbidden_chars = '<>:"/\\|?*'
    
    # Verificar caracteres prohibidos
    for char in forbidden_chars:
        if char in filename:
            return False
    
    # Verificar nombres reservados en Windows
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    
    name_without_ext = os.path.splitext(filename)[0].upper()
    if name_without_ext in reserved_names:
        return False
    
    # Verificar longitud
    if len(filename) > 255:
        return False
    
    return True


async def create_storage_backup(
    include_archived: bool = False,
    backup_name: Optional[str] = None
) -> str:
    """
    Función de conveniencia para crear backup del almacenamiento
    
    Args:
        include_archived: Incluir archivos archivados
        backup_name: Nombre del backup
        
    Returns:
        str: Ruta del archivo de backup
    """
    storage_service = get_storage_service()
    return storage_service.create_backup(backup_name, include_archived)


async def cleanup_storage(
    temp_hours: int = 24,
    archived_days: int = 90
) -> Dict[str, Any]:
    """
    Función de conveniencia para limpieza completa del almacenamiento
    
    Args:
        temp_hours: Horas para archivos temporales
        archived_days: Días para archivos archivados
        
    Returns:
        dict: Resultado de la limpieza
    """
    storage_service = get_storage_service()
    
    # Limpiar archivos temporales
    temp_result = storage_service.cleanup_temp_files(temp_hours)
    
    # Limpiar archivos archivados
    archived_result = storage_service.cleanup_archived_files(archived_days)
    
    return {
        "temp_cleanup": temp_result,
        "archived_cleanup": archived_result,
        "total_freed_mb": temp_result.get("freed_size_mb", 0) + archived_result.get("freed_size_mb", 0),
        "completed_at": datetime.utcnow().isoformat()
    }


def check_storage_health() -> Dict[str, Any]:
    """
    Verificar estado de salud del almacenamiento
    
    Returns:
        dict: Reporte de salud
    """
    try:
        storage_service = get_storage_service()
        return storage_service.verify_storage_integrity(fix_issues=False)
    except Exception as e:
        logger.error(f"Error verificando salud del almacenamiento: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "checked_at": datetime.utcnow().isoformat()
        }


def get_storage_recommendations() -> List[str]:
    """
    Obtener recomendaciones para el almacenamiento
    
    Returns:
        List[str]: Lista de recomendaciones
    """
    recommendations = []
    
    try:
        storage_service = get_storage_service()
        
        # Verificar espacio en disco
        disk_usage = shutil.disk_usage(storage_service.documents_path)
        free_space_gb = disk_usage.free / (1024**3)
        
        if free_space_gb < 1:
            recommendations.append("URGENTE: Liberar espacio en disco (menos de 1GB libre)")
        elif free_space_gb < 5:
            recommendations.append("Considerar liberar espacio en disco (menos de 5GB libre)")
        
        # Verificar archivos temporales
        temp_files = 0
        for root, dirs, files in os.walk(storage_service.temp_path):
            temp_files += len(files)
        
        if temp_files > 1000:
            recommendations.append("Ejecutar limpieza de archivos temporales")
        
        # Verificar archivos archivados
        archived_path = os.path.join(storage_service.documents_path, "archived")
        if os.path.exists(archived_path):
            archived_files = len(os.listdir(archived_path))
            if archived_files > 100:
                recommendations.append("Revisar y limpiar archivos archivados antiguos")
        
        # Backup
        recommendations.append("Crear backup periódico del almacenamiento")
        recommendations.append("Verificar integridad del almacenamiento regularmente")
        
        if not recommendations:
            recommendations.append("El almacenamiento está en buen estado")
        
    except Exception as e:
        recommendations.append(f"Error obteniendo recomendaciones: {str(e)}")
    
    return recommendations