"""
Servicio de gestión de documentos
Lógica de negocio para operaciones CRUD de documentos
"""
import logging
import os
import asyncio
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from fastapi import HTTPException, status, UploadFile

from ..models.document import Document, DocumentStatus, ApprovalStatus, AccessLevel
from ..models.document_type import DocumentType
from ..models.user import User
from ..models.qr_code import QRCode
from ..schemas.document import (
    DocumentCreate, DocumentUpdate, DocumentFilter, DocumentSummary,
    Document as DocumentSchema, DocumentDetailed
)
from ..utils.qr_processor import get_qr_processor, extract_qr_from_file
from ..utils.file_handler import get_file_handler, validate_and_save_file
from ..services.microsoft_service import (
    get_microsoft_service,
    MicrosoftGraphError,
)
from ..database import SessionLocal
from ..config import get_settings

# Configuración
settings = get_settings()
logger = logging.getLogger(__name__)


class DocumentService:
    """Servicio principal para gestión de documentos"""
    
    def __init__(self):
        """Inicializar el servicio de documentos"""
        self.qr_processor = get_qr_processor()
        self.file_handler = get_file_handler()
        self.microsoft_service = get_microsoft_service()
        
        logger.info("DocumentService inicializado")
    
    # === OPERACIONES CRUD ===
    
    async def create_document(
        self,
        document_data: DocumentCreate,
        file: UploadFile,
        user: User,
        db: Session
    ) -> Document:
        """
        Crear nuevo documento
        
        Args:
            document_data: Datos del documento
            file: Archivo subido
            user: Usuario que crea el documento
            db: Sesión de base de datos
            
        Returns:
            Document: Documento creado
        """
        try:
            logger.info(f"Creando documento tipo {document_data.document_type_id} por usuario {user.id}")
            
            # Obtener tipo de documento
            document_type = db.query(DocumentType).filter(
                DocumentType.id == document_data.document_type_id,
                DocumentType.is_active == True
            ).first()
            
            if not document_type:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Tipo de documento no encontrado o inactivo"
                )
            
            # Validar permisos del usuario
            if not user.can_upload:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Usuario no tiene permisos para subir documentos"
                )
            
            # Procesar archivo
            file_result = await validate_and_save_file(
                file=file,
                document_type_id=document_data.document_type_id,
                user_id=user.id,
                allowed_types=document_type.allowed_file_types_list
            )
            
            # Extraer QR si el tipo lo requiere
            qr_content = None
            qr_extraction_success = False
            qr_extraction_error = None
            
            if document_type.requires_qr:
                try:
                    qr_content = extract_qr_from_file(file_result["full_path"])
                    if qr_content:
                        qr_extraction_success = True
                        logger.info(f"QR extraído exitosamente: {qr_content[:20]}...")
                    else:
                        qr_extraction_error = "No se encontró código QR en el archivo"
                        logger.warning(f"No se pudo extraer QR del archivo: {file.filename}")
                except Exception as e:
                    qr_extraction_error = str(e)
                    logger.error(f"Error extrayendo QR: {str(e)}")
            
            # Validar datos según requisitos del tipo
            validation_data = {
                "cedula": document_data.cedula,
                "nombre_completo": document_data.nombre_completo,
                "telefono": document_data.telefono,
                "email": document_data.email,
                "direccion": document_data.direccion,
            }
            
            if document_type.requires_qr and qr_content:
                validation_data["qr_code"] = qr_content
            
            is_valid, validation_errors = document_type.validate_document_data(validation_data)
            
            if not is_valid:
                # Limpiar archivo subido si la validación falla
                try:
                    os.remove(file_result["full_path"])
                except:
                    pass
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Datos inválidos: {', '.join(validation_errors)}"
                )
            
            # Crear documento
            document = Document(
                # Información del tipo
                document_type_id=document_data.document_type_id,
                
                # Información de la persona
                cedula=document_data.cedula,
                nombre_completo=document_data.nombre_completo,
                telefono=document_data.telefono,
                email=document_data.email,
                direccion=document_data.direccion,
                
                # Información del archivo
                file_name=file_result["file_info"].file_name,
                file_path=file_result["storage_path"],
                file_size=file_result["file_info"].file_size,
                mime_type=file_result["file_info"].mime_type,
                file_hash=file_result["file_info"].file_hash,
                
                # QR
                qr_code_id=qr_content if qr_content else None,
                qr_extraction_success=qr_extraction_success,
                qr_extraction_error=qr_extraction_error,
                
                # Metadatos
                tags=document_data.metadata.tags,
                category=document_data.metadata.category,
                priority=document_data.metadata.priority,
                is_confidential=document_data.metadata.is_confidential,
                access_level=document_data.metadata.access_level,
                
                # Estado
                status=DocumentStatus.PENDING_APPROVAL if document_type.requires_approval else DocumentStatus.ACTIVE,
                approval_status=ApprovalStatus.PENDING if document_type.requires_approval else ApprovalStatus.AUTO_APPROVED,
                
                # Auditoría
                uploaded_by=user.id,
                version=1
            )
            
            # Calcular fecha de retención
            document.calculate_retention_date()
            
            # Guardar en base de datos
            db.add(document)
            db.commit()
            db.refresh(document)
            
            # Actualizar estadísticas del tipo
            document_type.increment_documents()
            user.increment_uploads()
            db.commit()
            
            # Log de creación
            document.add_change_log("created", {
                "file_name": document.file_name,
                "file_size": document.file_size,
                "qr_extracted": qr_extraction_success
            }, user.id)
            db.commit()
            
            # Subir a OneDrive en background
            asyncio.create_task(self._upload_to_onedrive(document, user))
            
            logger.info(f"Documento creado: ID {document.id}")
            return document
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creando documento: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al crear documento"
            )
    
    def get_document_by_id(
        self,
        document_id: int,
        user: User,
        db: Session,
        include_sensitive: bool = False
    ) -> Document:
        """
        Obtener documento por ID con verificación de acceso
        
        Args:
            document_id: ID del documento
            user: Usuario que solicita
            db: Sesión de base de datos
            include_sensitive: Incluir información sensible
            
        Returns:
            Document: Documento encontrado
        """
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Documento no encontrado"
                )
            
            # Verificar acceso
            if not self._check_document_access(document, user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tiene permisos para acceder a este documento"
                )
            
            # Marcar como visto
            document.mark_as_viewed(user.id)
            db.commit()
            
            return document
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo documento: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error obteniendo documento"
            )
    
    def update_document(
        self,
        document_id: int,
        update_data: DocumentUpdate,
        user: User,
        db: Session
    ) -> Document:
        """
        Actualizar documento
        
        Args:
            document_id: ID del documento
            update_data: Datos de actualización
            user: Usuario que actualiza
            db: Sesión de base de datos
            
        Returns:
            Document: Documento actualizado
        """
        try:
            document = self.get_document_by_id(document_id, user, db)
            
            # Verificar permisos de edición
            if not (user.is_admin or document.uploaded_by == user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tiene permisos para editar este documento"
                )
            
            # Guardar valores originales para log
            original_values = {}
            
            # Actualizar información de persona
            if update_data.person_info:
                person_info = update_data.person_info
                if person_info.cedula is not None:
                    original_values["cedula"] = document.cedula
                    document.cedula = person_info.cedula
                if person_info.nombre_completo is not None:
                    original_values["nombre_completo"] = document.nombre_completo
                    document.nombre_completo = person_info.nombre_completo
                if person_info.telefono is not None:
                    original_values["telefono"] = document.telefono
                    document.telefono = person_info.telefono
                if person_info.email is not None:
                    original_values["email"] = document.email
                    document.email = person_info.email
                if person_info.direccion is not None:
                    original_values["direccion"] = document.direccion
                    document.direccion = person_info.direccion
            
            # Actualizar metadatos
            if update_data.metadata:
                metadata = update_data.metadata
                if metadata.tags is not None:
                    original_values["tags"] = document.tags_list
                    document.tags_list = metadata.tags
                if metadata.category is not None:
                    original_values["category"] = document.category
                    document.category = metadata.category
                if metadata.priority is not None:
                    original_values["priority"] = document.priority
                    document.priority = metadata.priority
                if metadata.is_confidential is not None:
                    original_values["is_confidential"] = document.is_confidential
                    document.is_confidential = metadata.is_confidential
                if metadata.access_level is not None:
                    original_values["access_level"] = document.access_level
                    document.access_level = metadata.access_level
            
            # Actualizar archivos adicionales
            if update_data.additional_files is not None:
                original_values["additional_files"] = document.additional_files_list
                document.additional_files_list = update_data.additional_files
            
            # Incrementar versión y agregar log
            document.update_version(user.id, "Documento actualizado")
            document.add_change_log("updated", {
                "changes": original_values
            }, user.id)
            
            db.commit()
            db.refresh(document)
            
            logger.info(f"Documento {document.id} actualizado por usuario {user.id}")
            return document
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error actualizando documento: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error actualizando documento"
            )
    
    def delete_document(
        self,
        document_id: int,
        user: User,
        db: Session,
        hard_delete: bool = False
    ) -> bool:
        """
        Eliminar documento (soft delete por defecto)
        
        Args:
            document_id: ID del documento
            user: Usuario que elimina
            db: Sesión de base de datos
            hard_delete: Eliminación permanente
            
        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            document = self.get_document_by_id(document_id, user, db)
            
            # Solo admins pueden hacer hard delete
            if hard_delete and not user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo administradores pueden eliminar permanentemente"
                )
            
            # Verificar permisos
            if not (user.is_admin or document.uploaded_by == user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tiene permisos para eliminar este documento"
                )
            
            if hard_delete:
                # Eliminación permanente
                # Eliminar archivo físico
                try:
                    full_path = os.path.join(settings.DOCUMENTS_PATH, document.file_path)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                except Exception as e:
                    logger.warning(f"Error eliminando archivo físico: {str(e)}")
                
                db.delete(document)
                logger.info(f"Documento {document.id} eliminado permanentemente")
            else:
                # Soft delete
                document.soft_delete(user.id, "Eliminado por usuario")
                logger.info(f"Documento {document.id} marcado como eliminado")
            
            db.commit()
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error eliminando documento: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error eliminando documento"
            )
    
    # === BÚSQUEDA Y FILTROS ===
    
    def search_documents(
        self,
        filters: DocumentFilter,
        user: User,
        db: Session
    ) -> Tuple[List[Document], int]:
        """
        Buscar documentos con filtros
        
        Args:
            filters: Filtros de búsqueda
            user: Usuario que busca
            db: Sesión de base de datos
            
        Returns:
            Tuple[List[Document], int]: (documentos, total)
        """
        try:
            # Query base
            query = db.query(Document)
            
            # Aplicar filtros de acceso por usuario
            if not user.is_admin:
                query = query.filter(
                    or_(
                        Document.uploaded_by == user.id,
                        and_(
                            Document.is_confidential == False,
                            Document.status != DocumentStatus.DELETED
                        )
                    )
                )
            
            # Filtro de búsqueda general
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Document.file_name.ilike(search_term),
                        Document.cedula.ilike(search_term),
                        Document.nombre_completo.ilike(search_term),
                        Document.category.ilike(search_term)
                    )
                )
            
            # Filtros específicos
            if filters.document_type_id:
                query = query.filter(Document.document_type_id == filters.document_type_id)
            
            if filters.cedula:
                query = query.filter(Document.cedula.ilike(f"%{filters.cedula}%"))
            
            if filters.nombre_completo:
                query = query.filter(Document.nombre_completo.ilike(f"%{filters.nombre_completo}%"))
            
            if filters.status:
                query = query.filter(Document.status == filters.status)
            
            if filters.approval_status:
                query = query.filter(Document.approval_status == filters.approval_status)
            
            # Filtros de fecha
            if filters.created_after:
                query = query.filter(Document.created_at >= filters.created_after)
            
            if filters.created_before:
                query = query.filter(Document.created_at <= filters.created_before)
            
            if filters.updated_after:
                query = query.filter(Document.updated_at >= filters.updated_after)
            
            if filters.updated_before:
                query = query.filter(Document.updated_at <= filters.updated_before)
            
            # Filtros de metadatos
            if filters.tags:
                for tag in filters.tags:
                    query = query.filter(Document.tags.contains([tag]))
            
            if filters.category:
                query = query.filter(Document.category == filters.category)
            
            if filters.priority:
                query = query.filter(Document.priority == filters.priority)
            
            if filters.is_confidential is not None:
                query = query.filter(Document.is_confidential == filters.is_confidential)
            
            if filters.access_level:
                query = query.filter(Document.access_level == filters.access_level)
            
            # Filtros de archivo
            if filters.file_type:
                query = query.filter(Document.mime_type.ilike(f"%{filters.file_type}%"))
            
            if filters.min_file_size:
                query = query.filter(Document.file_size >= filters.min_file_size)
            
            if filters.max_file_size:
                query = query.filter(Document.file_size <= filters.max_file_size)
            
            # Filtros de QR
            if filters.has_qr is not None:
                if filters.has_qr:
                    query = query.filter(Document.qr_code_id.isnot(None))
                else:
                    query = query.filter(Document.qr_code_id.is_(None))
            
            if filters.qr_extraction_success is not None:
                query = query.filter(Document.qr_extraction_success == filters.qr_extraction_success)
            
            # Filtros de usuario
            if filters.uploaded_by:
                query = query.filter(Document.uploaded_by == filters.uploaded_by)
            
            if filters.approved_by:
                query = query.filter(Document.approved_by == filters.approved_by)
            
            # Contar total antes de paginación
            total = query.count()
            
            # Aplicar ordenamiento
            if filters.sort_by == "file_name":
                order_column = Document.file_name
            elif filters.sort_by == "file_size":
                order_column = Document.file_size
            elif filters.sort_by == "cedula":
                order_column = Document.cedula
            elif filters.sort_by == "nombre_completo":
                order_column = Document.nombre_completo
            elif filters.sort_by == "status":
                order_column = Document.status
            elif filters.sort_by == "approval_status":
                order_column = Document.approval_status
            elif filters.sort_by == "view_count":
                order_column = Document.view_count
            elif filters.sort_by == "updated_at":
                order_column = Document.updated_at
            else:  # created_at por defecto
                order_column = Document.created_at
            
            if filters.sort_order == "desc":
                order_column = desc(order_column)
            else:
                order_column = asc(order_column)
            
            query = query.order_by(order_column)
            
            # Aplicar paginación
            offset = (filters.page - 1) * filters.page_size
            documents = query.offset(offset).limit(filters.page_size).all()
            
            return documents, total
            
        except Exception as e:
            logger.error(f"Error buscando documentos: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error en búsqueda de documentos"
            )
    
    # === OPERACIONES DE APROBACIÓN ===
    
    def approve_document(
        self,
        document_id: int,
        user: User,
        db: Session,
        notes: str = None
    ) -> Document:
        """
        Aprobar documento
        
        Args:
            document_id: ID del documento
            user: Usuario que aprueba
            db: Sesión de base de datos
            notes: Notas de aprobación
            
        Returns:
            Document: Documento aprobado
        """
        try:
            if not user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo administradores pueden aprobar documentos"
                )
            
            document = self.get_document_by_id(document_id, user, db)
            
            if document.approval_status != ApprovalStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Documento no está pendiente de aprobación"
                )
            
            # Aprobar documento
            document.approve(user.id, notes)
            document.status = DocumentStatus.ACTIVE
            
            db.commit()
            db.refresh(document)
            
            logger.info(f"Documento {document.id} aprobado por {user.email}")
            return document
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error aprobando documento: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error aprobando documento"
            )
    
    def reject_document(
        self,
        document_id: int,
        user: User,
        db: Session,
        reason: str
    ) -> Document:
        """
        Rechazar documento
        
        Args:
            document_id: ID del documento
            user: Usuario que rechaza
            db: Sesión de base de datos
            reason: Razón del rechazo
            
        Returns:
            Document: Documento rechazado
        """
        try:
            if not user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo administradores pueden rechazar documentos"
                )
            
            if not reason or len(reason.strip()) < 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Debe proporcionar una razón válida para el rechazo"
                )
            
            document = self.get_document_by_id(document_id, user, db)
            
            # Rechazar documento
            document.reject(user.id, reason)
            
            db.commit()
            db.refresh(document)
            
            logger.info(f"Documento {document.id} rechazado por {user.email}")
            return document
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error rechazando documento: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error rechazando documento"
            )
    
    # === MÉTODOS PRIVADOS ===
    
    def _check_document_access(self, document: Document, user: User) -> bool:
        """
        Verificar si el usuario tiene acceso al documento
        
        Args:
            document: Documento a verificar
            user: Usuario que solicita acceso
            
        Returns:
            bool: True si tiene acceso
        """
        # Administradores tienen acceso a todo
        if user.is_admin:
            return True
        
        # Documentos eliminados solo para admins
        if document.status == DocumentStatus.DELETED:
            return False
        
        # Propietario siempre tiene acceso
        if document.uploaded_by == user.id:
            return True
        
        # Documentos confidenciales solo para propietario y admins
        if document.is_confidential:
            return False
        
        return True
    
    async def _upload_to_onedrive(self, document: Document, user: User):
        """
        Subir documento a OneDrive en background
        
        Args:
            document: Documento a subir
            user: Usuario propietario
        """
        try:
            logger.info(
                f"Iniciando subida a OneDrive para documento {document.id}"
            )

            # Verificar token de Microsoft en el usuario
            access_token = getattr(user, "microsoft_access_token", None)
            if not access_token:
                logger.warning(
                    "Usuario no tiene token de Microsoft, omitiendo subida a OneDrive"
                )
                return

            # Verificar existencia del archivo local
            local_path = os.path.join(settings.DOCUMENTS_PATH, document.file_path)
            if not os.path.exists(local_path):
                logger.error(
                    f"Archivo local no encontrado para subir: {document.file_path}"
                )
                return

            # Leer contenido
            with open(local_path, "rb") as f:
                file_content = f.read()

            folder_path = f"root:/{settings.ONEDRIVE_ROOT_FOLDER}"
            if document.document_type:
                folder_path = f"{folder_path}/{document.document_type.code}"

            def generate_name(doc: Document) -> str:
                base_name, ext = os.path.splitext(doc.file_name)
                safe_name = "".join(c for c in base_name if c.isalnum() or c in "._-")
                timestamp = doc.created_at.strftime("%Y%m%d_%H%M%S")
                return f"{doc.id}_{timestamp}_{safe_name}{ext}"

            file_name = generate_name(document)

            retries = 3
            for attempt in range(1, retries + 1):
                try:
                    upload_result = await self.microsoft_service.upload_file_to_onedrive(
                        access_token,
                        file_name,
                        file_content,
                        folder_path,
                    )

                    onedrive_url = upload_result.get("webUrl")
                    onedrive_id = upload_result.get("id")

                    # Actualizar registro en BD
                    db = SessionLocal()
                    try:
                        doc = db.query(Document).get(document.id)
                        if doc:
                            doc.onedrive_url = onedrive_url
                            doc.onedrive_file_id = onedrive_id
                            doc.add_change_log(
                                "onedrive_upload",
                                {
                                    "onedrive_file_id": onedrive_id,
                                    "onedrive_url": onedrive_url,
                                },
                                user.id,
                            )
                            db.commit()
                    finally:
                        db.close()

                    logger.info(
                        f"Documento {document.id} subido a OneDrive: {onedrive_url}"
                    )
                    return
                except MicrosoftGraphError as e:
                    logger.warning(
                        f"Intento {attempt} fallido subiendo a OneDrive: {e.message}"
                    )
                    if attempt < retries:
                        await asyncio.sleep(2**attempt)
                        continue
                    raise
            
        except Exception as e:
            logger.error(f"Error subiendo a OneDrive: {str(e)}")
            db = SessionLocal()
            try:
                doc = db.query(Document).get(document.id)
                if doc:
                    doc.add_change_log(
                        "onedrive_upload_failed", {"error": str(e)}, user.id
                    )
                    db.commit()
            finally:
                db.close()


# === INSTANCIA GLOBAL ===

# Instancia singleton del servicio
_document_service = None

def get_document_service() -> DocumentService:
    """
    Obtener instancia del servicio de documentos
    
    Returns:
        DocumentService: Instancia del servicio
    """
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service