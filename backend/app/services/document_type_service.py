"""
Servicio de gestión de tipos de documento
Lógica de negocio para operaciones CRUD y configuración de tipos
"""
import logging
import os
import shutil
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from fastapi import HTTPException, status, UploadFile

from ..models.document_type import DocumentType
from ..models.user import User
from ..models.document import Document
from ..models.qr_code import QRCode
from ..schemas.document_type import (
    DocumentTypeCreate,
    DocumentTypeUpdate,
    DocumentTypeAdminUpdate,
    DocumentTypeFilter,
    DocumentTypeClone,
    DocumentTypeRequirements,
    DocumentTypeFileConfig,
    DocumentTypeUIConfig,
    DocumentTypeWorkflow,
    DocumentTypeQRConfig
)
from ..config import get_settings
from ..utils.file_handler import get_file_handler

# Configuración
settings = get_settings()
logger = logging.getLogger(__name__)


class DocumentTypeService:
    """Servicio principal para gestión de tipos de documento"""
    
    def __init__(self):
        """Inicializar el servicio de tipos de documento"""
        self.file_handler = get_file_handler()
        
        logger.info("DocumentTypeService inicializado")
    
    # === OPERACIONES CRUD ===
    
    def create_document_type(
        self,
        type_data: DocumentTypeCreate,
        user: User,
        db: Session
    ) -> DocumentType:
        """
        Crear nuevo tipo de documento
        
        Args:
            type_data: Datos del tipo de documento
            user: Usuario que crea el tipo
            db: Sesión de base de datos
            
        Returns:
            DocumentType: Tipo de documento creado
        """
        try:
            logger.info(f"Creando tipo de documento {type_data.code} por usuario {user.id}")
            
            # Verificar que el código no exista
            existing = db.query(DocumentType).filter(
                DocumentType.code == type_data.code.upper()
            ).first()
            
            if existing:
                raise ValueError(f"Ya existe un tipo de documento con el código: {type_data.code}")
            
            # Validar configuraciones
            self._validate_type_configuration(type_data)
            
            # Crear tipo de documento
            document_type = DocumentType(
                code=type_data.code.upper(),
                name=type_data.name,
                description=type_data.description,
                
                # Requisitos
                requires_qr=type_data.requirements.requires_qr,
                requires_cedula=type_data.requirements.requires_cedula,
                requires_nombre=type_data.requirements.requires_nombre,
                requires_telefono=type_data.requirements.requires_telefono,
                requires_email=type_data.requirements.requires_email,
                requires_direccion=type_data.requirements.requires_direccion,
                
                # Configuración de archivos
                allowed_file_types=type_data.file_config.allowed_file_types,
                max_file_size_mb=type_data.file_config.max_file_size_mb,
                allow_multiple_files=type_data.file_config.allow_multiple_files,
                
                # Configuración de UI
                color=type_data.ui_config.color,
                icon=type_data.ui_config.icon,
                sort_order=type_data.ui_config.sort_order,
                
                # Configuración de workflow
                requires_approval=type_data.workflow.requires_approval,
                auto_notify_email=type_data.workflow.auto_notify_email,
                notification_emails=type_data.workflow.notification_emails,
                retention_days=type_data.workflow.retention_days,
                auto_archive=type_data.workflow.auto_archive,
                
                # Plantilla
                template_path=type_data.template_path,
                
                # Auditoría
                created_by=user.id
            )
            
            # Configuración de QR si se requiere
            if type_data.qr_config and type_data.requirements.requires_qr:
                document_type.qr_table_number = type_data.qr_config.qr_table_number
                document_type.qr_row = type_data.qr_config.qr_row
                document_type.qr_column = type_data.qr_config.qr_column
                document_type.qr_width = type_data.qr_config.qr_width
                document_type.qr_height = type_data.qr_config.qr_height
            
            db.add(document_type)
            db.commit()
            db.refresh(document_type)
            
            logger.info(f"Tipo de documento creado: {document_type.code}")
            return document_type
            
        except ValueError as e:
            logger.warning(f"Error de validación: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error creando tipo de documento: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear tipo de documento"
            )
    
    def get_document_type_by_id(
        self,
        type_id: int,
        user: User,
        db: Session,
        include_inactive: bool = False
    ) -> DocumentType:
        """
        Obtener tipo de documento por ID
        
        Args:
            type_id: ID del tipo de documento
            user: Usuario que solicita
            db: Sesión de base de datos
            include_inactive: Incluir tipos inactivos
            
        Returns:
            DocumentType: Tipo de documento encontrado
        """
        try:
            query = db.query(DocumentType).filter(DocumentType.id == type_id)
            
            # Filtrar por estado si no es admin
            if not include_inactive and not user.is_admin:
                query = query.filter(DocumentType.is_active == True)
            
            document_type = query.first()
            
            if not document_type:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Tipo de documento no encontrado"
                )
            
            return document_type
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo tipo de documento: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error obteniendo tipo de documento"
            )
    
    def get_document_type_by_code(
        self,
        type_code: str,
        user: User,
        db: Session,
        include_inactive: bool = False
    ) -> DocumentType:
        """
        Obtener tipo de documento por código
        
        Args:
            type_code: Código del tipo de documento
            user: Usuario que solicita
            db: Sesión de base de datos
            include_inactive: Incluir tipos inactivos
            
        Returns:
            DocumentType: Tipo de documento encontrado
        """
        try:
            query = db.query(DocumentType).filter(
                DocumentType.code == type_code.upper()
            )
            
            if not include_inactive and not user.is_admin:
                query = query.filter(DocumentType.is_active == True)
            
            document_type = query.first()
            
            if not document_type:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Tipo de documento no encontrado"
                )
            
            return document_type
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo tipo por código: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error obteniendo tipo de documento"
            )
    
    def update_document_type(
        self,
        type_id: int,
        update_data: DocumentTypeUpdate,
        user: User,
        db: Session
    ) -> DocumentType:
        """
        Actualizar tipo de documento
        
        Args:
            type_id: ID del tipo de documento
            update_data: Datos de actualización
            user: Usuario que actualiza
            db: Sesión de base de datos
            
        Returns:
            DocumentType: Tipo de documento actualizado
        """
        try:
            document_type = self.get_document_type_by_id(type_id, user, db, include_inactive=True)
            
            # Verificar permisos
            if document_type.is_system_type and not user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Los tipos de sistema solo pueden ser editados por administradores"
                )
            
            # Actualizar campos básicos
            if update_data.name is not None:
                document_type.name = update_data.name
            if update_data.description is not None:
                document_type.description = update_data.description
            if update_data.is_active is not None:
                document_type.is_active = update_data.is_active
            
            # Actualizar configuraciones si se proporcionan
            if update_data.requirements:
                self._update_requirements(document_type, update_data.requirements)
            
            if update_data.file_config:
                self._update_file_config(document_type, update_data.file_config)
            
            if update_data.ui_config:
                self._update_ui_config(document_type, update_data.ui_config)
            
            if update_data.workflow:
                self._update_workflow_config(document_type, update_data.workflow)
            
            if update_data.template_path is not None:
                document_type.template_path = update_data.template_path
            
            if update_data.qr_config:
                self._update_qr_config(document_type, update_data.qr_config)
            
            db.commit()
            db.refresh(document_type)
            
            logger.info(f"Tipo de documento actualizado: {document_type.code}")
            return document_type
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error actualizando tipo de documento: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar tipo de documento"
            )
    
    def delete_document_type(
        self,
        type_id: int,
        user: User,
        db: Session,
        force: bool = False
    ) -> bool:
        """
        Eliminar tipo de documento
        
        Args:
            type_id: ID del tipo de documento
            user: Usuario que elimina
            db: Sesión de base de datos
            force: Forzar eliminación incluso con documentos asociados
            
        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            document_type = self.get_document_type_by_id(type_id, user, db, include_inactive=True)
            
            # Solo administradores pueden eliminar
            if not user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo administradores pueden eliminar tipos de documento"
                )
            
            # Verificar si es tipo de sistema
            if document_type.is_system_type:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Los tipos de sistema no pueden ser eliminados"
                )
            
            # Verificar documentos asociados
            doc_count = db.query(Document).filter(
                Document.document_type_id == document_type.id
            ).count()
            
            qr_count = db.query(QRCode).filter(
                QRCode.document_type_id == document_type.id
            ).count()
            
            if (doc_count > 0 or qr_count > 0) and not force:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No se puede eliminar. Hay {doc_count} documentos y {qr_count} códigos QR asociados"
                )
            
            # Eliminar plantilla si existe
            if document_type.template_path:
                self._delete_template_file(document_type.template_path)
            
            # Eliminar tipo de documento
            db.delete(document_type)
            db.commit()
            
            logger.info(f"Tipo de documento eliminado: {document_type.code}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error eliminando tipo de documento: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar tipo de documento"
            )
    
    # === BÚSQUEDA Y FILTROS ===
    
    def search_document_types(
        self,
        filters: DocumentTypeFilter,
        user: User,
        db: Session
    ) -> Tuple[List[DocumentType], int]:
        """
        Buscar tipos de documento con filtros
        
        Args:
            filters: Filtros de búsqueda
            user: Usuario que busca
            db: Sesión de base de datos
            
        Returns:
            Tuple[List[DocumentType], int]: (tipos, total)
        """
        try:
            # Query base
            query = db.query(DocumentType)
            
            # Aplicar filtros
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        DocumentType.code.ilike(search_term),
                        DocumentType.name.ilike(search_term),
                        DocumentType.description.ilike(search_term)
                    )
                )
            
            if filters.is_active is not None:
                query = query.filter(DocumentType.is_active == filters.is_active)
            elif not user.is_admin:
                # No admins solo ven tipos activos
                query = query.filter(DocumentType.is_active == True)
            
            if filters.requires_qr is not None:
                query = query.filter(DocumentType.requires_qr == filters.requires_qr)
            
            if filters.can_generate is not None:
                if filters.can_generate:
                    query = query.filter(
                        and_(
                            DocumentType.template_path.isnot(None),
                            DocumentType.is_active == True
                        )
                    )
                else:
                    query = query.filter(
                        or_(
                            DocumentType.template_path.is_(None),
                            DocumentType.is_active == False
                        )
                    )
            
            if filters.created_by is not None:
                query = query.filter(DocumentType.created_by == filters.created_by)
            
            # Contar total
            total = query.count()
            
            # Aplicar ordenamiento
            if filters.sort_by == "name":
                order_column = DocumentType.name
            elif filters.sort_by == "code":
                order_column = DocumentType.code
            elif filters.sort_by == "created_at":
                order_column = DocumentType.created_at
            elif filters.sort_by == "updated_at":
                order_column = DocumentType.updated_at
            elif filters.sort_by == "documents_count":
                order_column = DocumentType.documents_count
            elif filters.sort_by == "sort_order":
                order_column = DocumentType.sort_order
            else:
                order_column = DocumentType.created_at
            
            if filters.sort_order == "desc":
                order_column = desc(order_column)
            else:
                order_column = asc(order_column)
            
            query = query.order_by(order_column)
            
            # Aplicar paginación
            offset = (filters.page - 1) * filters.page_size
            document_types = query.offset(offset).limit(filters.page_size).all()
            
            return document_types, total
            
        except Exception as e:
            logger.error(f"Error buscando tipos de documento: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error en búsqueda de tipos de documento"
            )
    
    # === OPERACIONES ESPECIALES ===
    
    def clone_document_type(
        self,
        clone_data: DocumentTypeClone,
        user: User,
        db: Session
    ) -> DocumentType:
        """
        Clonar tipo de documento existente
        
        Args:
            clone_data: Datos para la clonación
            user: Usuario que clona
            db: Sesión de base de datos
            
        Returns:
            DocumentType: Tipo de documento clonado
        """
        try:
            # Obtener tipo original
            source_type = self.get_document_type_by_id(
                clone_data.source_id, user, db, include_inactive=True
            )
            
            # Verificar que el nuevo código no exista
            existing = db.query(DocumentType).filter(
                DocumentType.code == clone_data.new_code.upper()
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya existe un tipo con el código: {clone_data.new_code}"
                )
            
            # Clonar usando el método del modelo
            cloned_type = source_type.clone(
                new_code=clone_data.new_code.upper(),
                new_name=clone_data.new_name,
                created_by=user.id
            )
            
            # Copiar plantilla si se solicita
            if clone_data.copy_template and source_type.template_path:
                try:
                    new_template_path = self._copy_template_file(
                        source_type.template_path,
                        clone_data.new_code.lower()
                    )
                    cloned_type.template_path = new_template_path
                except Exception as e:
                    logger.warning(f"Error copiando plantilla: {str(e)}")
            
            db.add(cloned_type)
            db.commit()
            db.refresh(cloned_type)
            
            logger.info(f"Tipo clonado: {source_type.code} -> {cloned_type.code}")
            return cloned_type
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error clonando tipo de documento: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al clonar tipo de documento"
            )
    
    def toggle_document_type_status(
        self,
        type_id: int,
        user: User,
        db: Session
    ) -> DocumentType:
        """
        Activar/desactivar tipo de documento
        
        Args:
            type_id: ID del tipo de documento
            user: Usuario que cambia el estado
            db: Sesión de base de datos
            
        Returns:
            DocumentType: Tipo actualizado
        """
        try:
            document_type = self.get_document_type_by_id(
                type_id, user, db, include_inactive=True
            )
            
            document_type.is_active = not document_type.is_active
            db.commit()
            db.refresh(document_type)
            
            action = "activado" if document_type.is_active else "desactivado"
            logger.info(f"Tipo de documento {action}: {document_type.code}")
            
            return document_type
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error cambiando estado: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al cambiar estado del tipo"
            )
    
    # === GESTIÓN DE PLANTILLAS ===
    
    async def upload_template(
        self,
        type_id: int,
        file: UploadFile,
        user: User,
        db: Session
    ) -> str:
        """
        Subir plantilla para tipo de documento
        
        Args:
            type_id: ID del tipo de documento
            file: Archivo de plantilla
            user: Usuario que sube la plantilla
            db: Sesión de base de datos
            
        Returns:
            str: Nombre del archivo de plantilla
        """
        try:
            document_type = self.get_document_type_by_id(type_id, user, db)
            
            # Validar archivo
            if not file.filename.endswith('.docx'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Solo se permiten archivos .docx"
                )
            
            # Crear nombre único para la plantilla
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_code = document_type.code.lower().replace('-', '_')
            new_filename = f"{safe_code}_template_{timestamp}.docx"
            
            # Guardar archivo
            template_path = os.path.join(settings.TEMPLATES_PATH, new_filename)
            
            with open(template_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Eliminar plantilla anterior si existe
            if document_type.template_path:
                self._delete_template_file(document_type.template_path)
            
            # Actualizar tipo de documento
            document_type.template_path = new_filename
            db.commit()
            
            logger.info(f"Plantilla subida para {document_type.code}: {new_filename}")
            return new_filename
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error subiendo plantilla: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al subir plantilla"
            )
    
    def delete_template(
        self,
        type_id: int,
        user: User,
        db: Session
    ) -> bool:
        """
        Eliminar plantilla del tipo de documento
        
        Args:
            type_id: ID del tipo de documento
            user: Usuario que elimina
            db: Sesión de base de datos
            
        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            document_type = self.get_document_type_by_id(type_id, user, db)
            
            if not document_type.template_path:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Este tipo de documento no tiene plantilla"
                )
            
            # Eliminar archivo físico
            self._delete_template_file(document_type.template_path)
            
            # Actualizar base de datos
            document_type.template_path = None
            db.commit()
            
            logger.info(f"Plantilla eliminada para {document_type.code}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error eliminando plantilla: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar plantilla"
            )
    
    # === VALIDACIÓN ===
    
    def validate_document_data(
        self,
        type_id: int,
        data: Dict[str, Any],
        user: User,
        db: Session
    ) -> Tuple[bool, List[str]]:
        """
        Validar datos de documento según tipo
        
        Args:
            type_id: ID del tipo de documento
            data: Datos a validar
            user: Usuario que valida
            db: Sesión de base de datos
            
        Returns:
            Tuple[bool, List[str]]: (es_válido, lista_errores)
        """
        try:
            document_type = self.get_document_type_by_id(type_id, user, db)
            return document_type.validate_document_data(data)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error validando datos: {str(e)}")
            return False, [f"Error en validación: {str(e)}"]
    
    # === ESTADÍSTICAS ===
    
    def get_document_types_stats(
        self,
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """
        Obtener estadísticas de tipos de documento
        
        Args:
            user: Usuario que solicita
            db: Sesión de base de datos
            
        Returns:
            dict: Estadísticas de tipos de documento
        """
        try:
            # Estadísticas básicas
            total_types = db.query(DocumentType).count()
            active_types = db.query(DocumentType).filter(
                DocumentType.is_active == True
            ).count()
            types_with_qr = db.query(DocumentType).filter(
                DocumentType.requires_qr == True
            ).count()
            types_with_templates = db.query(DocumentType).filter(
                DocumentType.template_path.isnot(None)
            ).count()
            
            # Tipos más usados (por documentos)
            top_types = db.query(
                DocumentType.code,
                DocumentType.name,
                func.count(Document.id).label('document_count')
            ).outerjoin(Document).group_by(
                DocumentType.id, DocumentType.code, DocumentType.name
            ).order_by(func.count(Document.id).desc()).limit(5).all()
            
            return {
                "summary": {
                    "total_types": total_types,
                    "active_types": active_types,
                    "inactive_types": total_types - active_types,
                    "with_qr": types_with_qr,
                    "with_templates": types_with_templates
                },
                "status_distribution": {
                    "active": active_types,
                    "inactive": total_types - active_types
                },
                "feature_distribution": {
                    "requires_qr": types_with_qr,
                    "has_template": types_with_templates,
                    "requires_approval": db.query(DocumentType).filter(
                        DocumentType.requires_approval == True
                    ).count()
                },
                "top_used_types": [
                    {
                        "code": code,
                        "name": name,
                        "document_count": count
                    }
                    for code, name, count in top_types
                ],
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener estadísticas"
            )
    
    # === MÉTODOS PRIVADOS ===
    
    def _validate_type_configuration(self, type_data: DocumentTypeCreate):
        """Validar configuración del tipo de documento"""
        # Validar que si requiere QR, tenga configuración de QR
        if type_data.requirements.requires_qr and not type_data.qr_config:
            raise ValueError("Configuración de QR es requerida cuando requires_qr es True")
        
        # Validar tipos de archivo
        if not type_data.file_config.allowed_file_types:
            raise ValueError("Debe especificar al menos un tipo de archivo permitido")
        
        # Validar tamaño de archivo
        if type_data.file_config.max_file_size_mb <= 0:
            raise ValueError("El tamaño máximo de archivo debe ser mayor a 0")
    
    def _update_requirements(self, document_type: DocumentType, requirements: DocumentTypeRequirements):
        """Actualizar configuración de requisitos"""
        document_type.requires_qr = requirements.requires_qr
        document_type.requires_cedula = requirements.requires_cedula
        document_type.requires_nombre = requirements.requires_nombre
        document_type.requires_telefono = requirements.requires_telefono
        document_type.requires_email = requirements.requires_email
        document_type.requires_direccion = requirements.requires_direccion
    
    def _update_file_config(self, document_type: DocumentType, file_config: DocumentTypeFileConfig):
        """Actualizar configuración de archivos"""
        document_type.allowed_file_types_list = file_config.allowed_file_types
        document_type.max_file_size_mb = file_config.max_file_size_mb
        document_type.allow_multiple_files = file_config.allow_multiple_files
    
    def _update_ui_config(self, document_type: DocumentType, ui_config: DocumentTypeUIConfig):
        """Actualizar configuración de UI"""
        document_type.color = ui_config.color
        document_type.icon = ui_config.icon
        document_type.sort_order = ui_config.sort_order
    
    def _update_workflow_config(self, document_type: DocumentType, workflow: DocumentTypeWorkflow):
        """Actualizar configuración de workflow"""
        document_type.requires_approval = workflow.requires_approval
        document_type.auto_notify_email = workflow.auto_notify_email
        document_type.notification_emails_list = workflow.notification_emails
        document_type.retention_days = workflow.retention_days
        document_type.auto_archive = workflow.auto_archive
    
    def _update_qr_config(self, document_type: DocumentType, qr_config: DocumentTypeQRConfig):
        """Actualizar configuración de QR"""
        document_type.qr_table_number = qr_config.qr_table_number
        document_type.qr_row = qr_config.qr_row
        document_type.qr_column = qr_config.qr_column
        document_type.qr_width = qr_config.qr_width
        document_type.qr_height = qr_config.qr_height
    
    def _delete_template_file(self, template_path: str):
        """Eliminar archivo de plantilla físicamente"""
        try:
            full_path = os.path.join(settings.TEMPLATES_PATH, template_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                logger.info(f"Archivo de plantilla eliminado: {template_path}")
        except Exception as e:
            logger.warning(f"Error eliminando archivo de plantilla: {str(e)}")
    
    def _copy_template_file(self, source_template: str, new_code: str) -> str:
        """Copiar archivo de plantilla para clonación"""
        try:
            source_path = os.path.join(settings.TEMPLATES_PATH, source_template)
            
            if not os.path.exists(source_path):
                raise FileNotFoundError(f"Plantilla fuente no encontrada: {source_template}")
            
            # Generar nuevo nombre
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{new_code}_template_{timestamp}.docx"
            dest_path = os.path.join(settings.TEMPLATES_PATH, new_filename)
            
            # Copiar archivo
            shutil.copy2(source_path, dest_path)
            
            logger.info(f"Plantilla copiada: {source_template} -> {new_filename}")
            return new_filename
            
        except Exception as e:
            logger.error(f"Error copiando plantilla: {str(e)}")
            raise


# === INSTANCIA GLOBAL ===

# Instancia singleton del servicio
_document_type_service = None

def get_document_type_service() -> DocumentTypeService:
    """
    Obtener instancia del servicio de tipos de documento
    
    Returns:
        DocumentTypeService: Instancia del servicio
    """
    global _document_type_service
    if _document_type_service is None:
        _document_type_service = DocumentTypeService()
    return _document_type_service


# === FUNCIONES DE UTILIDAD ===

def validate_document_type_code(code: str) -> bool:
    """
    Validar formato de código de tipo de documento
    
    Args:
        code: Código a validar
        
    Returns:
        bool: True si es válido
    """
    import re
    # Código debe ser alfanumérico, guiones y guiones bajos, 2-20 caracteres
    pattern = r'^[A-Z0-9_-]{2,20}'
    return bool(re.match(pattern, code.upper()))


def get_default_file_types() -> List[str]:
    """
    Obtener lista de tipos de archivo por defecto
    
    Returns:
        List[str]: Tipos MIME por defecto
    """
    return [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword"
    ]


def get_available_icons() -> List[str]:
    """
    Obtener lista de iconos disponibles para tipos de documento
    
    Returns:
        List[str]: Nombres de iconos
    """
    return [
        "document-text",
        "folder",
        "identification",
        "academic-cap",
        "briefcase",
        "clipboard-document-list",
        "shield-check",
        "user-circle",
        "building-office",
        "document-chart-bar",
        "document-duplicate",
        "document-magnifying-glass",
        "paper-clip",
        "archive-box",
        "qr-code"
    ]


def get_available_colors() -> List[str]:
    """
    Obtener lista de colores disponibles para tipos de documento
    
    Returns:
        List[str]: Códigos de color hex
    """
    return [
        "#3B82F6",  # blue
        "#10B981",  # emerald
        "#F59E0B",  # amber
        "#EF4444",  # red
        "#8B5CF6",  # violet
        "#06B6D4",  # cyan
        "#84CC16",  # lime
        "#F97316",  # orange
        "#EC4899",  # pink
        "#6B7280",  # gray
        "#14B8A6",  # teal
        "#A855F7",  # purple
        "#22C55E",  # green
        "#DC2626",  # red-600
        "#7C3AED"   # violet-600
    ]


async def initialize_default_document_types(db: Session, admin_user: User) -> List[DocumentType]:
    """
    Inicializar tipos de documento por defecto
    
    Args:
        db: Sesión de base de datos
        admin_user: Usuario administrador
        
    Returns:
        List[DocumentType]: Tipos creados
    """
    try:
        service = get_document_type_service()
        
        # Verificar si ya existen tipos
        existing_count = db.query(DocumentType).count()
        if existing_count > 0:
            logger.info("Ya existen tipos de documento, omitiendo inicialización")
            return []
        
        default_types = [
            {
                "code": "DNI",
                "name": "Documento Nacional de Identidad",
                "description": "Cédula de ciudadanía o documento de identificación",
                "requires_qr": True,
                "color": "#3B82F6",
                "icon": "identification"
            },
            {
                "code": "PASSPORT",
                "name": "Pasaporte",
                "description": "Documento de viaje internacional",
                "requires_qr": False,
                "color": "#10B981",
                "icon": "document-text"
            },
            {
                "code": "LICENSE",
                "name": "Licencia de Conducir",
                "description": "Licencia para conducir vehículos",
                "requires_qr": True,
                "color": "#F59E0B",
                "icon": "shield-check"
            },
            {
                "code": "CERTIFICATE",
                "name": "Certificado",
                "description": "Certificados académicos o profesionales",
                "requires_qr": False,
                "color": "#8B5CF6",
                "icon": "academic-cap"
            },
            {
                "code": "CONTRACT",
                "name": "Contrato",
                "description": "Contratos laborales o comerciales",
                "requires_qr": False,
                "color": "#EC4899",
                "icon": "briefcase"
            }
        ]
        
        created_types = []
        
        for i, type_data in enumerate(default_types):
            try:
                # Crear configuraciones por defecto
                requirements = DocumentTypeRequirements(
                    requires_qr=type_data["requires_qr"],
                    requires_cedula=True,
                    requires_nombre=True,
                    requires_telefono=False,
                    requires_email=False,
                    requires_direccion=False
                )
                
                file_config = DocumentTypeFileConfig(
                    allowed_file_types=get_default_file_types(),
                    max_file_size_mb=50,
                    allow_multiple_files=False
                )
                
                ui_config = DocumentTypeUIConfig(
                    color=type_data["color"],
                    icon=type_data["icon"],
                    sort_order=i + 1
                )
                
                workflow = DocumentTypeWorkflow(
                    requires_approval=False,
                    auto_notify_email=False,
                    notification_emails=[],
                    retention_days=None,
                    auto_archive=False
                )
                
                qr_config = None
                if type_data["requires_qr"]:
                    qr_config = DocumentTypeQRConfig(
                        qr_table_number=1,
                        qr_row=0,
                        qr_column=0,
                        qr_width=1.0,
                        qr_height=1.0
                    )
                
                # Crear tipo de documento
                create_data = DocumentTypeCreate(
                    code=type_data["code"],
                    name=type_data["name"],
                    description=type_data["description"],
                    requirements=requirements,
                    file_config=file_config,
                    ui_config=ui_config,
                    workflow=workflow,
                    qr_config=qr_config,
                    template_path=None
                )
                
                document_type = service.create_document_type(create_data, admin_user, db)
                document_type.is_system_type = True  # Marcar como tipo de sistema
                created_types.append(document_type)
                
            except Exception as e:
                logger.error(f"Error creando tipo por defecto {type_data['code']}: {str(e)}")
                continue
        
        db.commit()
        
        logger.info(f"Inicializados {len(created_types)} tipos de documento por defecto")
        return created_types
        
    except Exception as e:
        logger.error(f"Error inicializando tipos por defecto: {str(e)}")
        db.rollback()
        return []


def check_document_type_integrity(db: Session) -> Dict[str, Any]:
    """
    Verificar integridad de los tipos de documento
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        dict: Reporte de integridad
    """
    try:
        issues = []
        warnings = []
        
        # Verificar tipos sin plantilla pero que pueden generar
        types_without_template = db.query(DocumentType).filter(
            and_(
                DocumentType.template_path.is_(None),
                DocumentType.is_active == True
            )
        ).count()
        
        if types_without_template > 0:
            warnings.append(f"{types_without_template} tipos activos sin plantilla")
        
        # Verificar plantillas físicas
        types_with_template = db.query(DocumentType).filter(
            DocumentType.template_path.isnot(None)
        ).all()
        
        missing_templates = []
        for doc_type in types_with_template:
            template_path = os.path.join(settings.TEMPLATES_PATH, doc_type.template_path)
            if not os.path.exists(template_path):
                missing_templates.append(doc_type.code)
        
        if missing_templates:
            issues.append(f"Plantillas faltantes para tipos: {', '.join(missing_templates)}")
        
        # Verificar códigos duplicados
        duplicates = db.query(
            DocumentType.code,
            func.count(DocumentType.id).label('count')
        ).group_by(DocumentType.code).having(
            func.count(DocumentType.id) > 1
        ).all()
        
        if duplicates:
            issues.append(f"Códigos duplicados: {[code for code, count in duplicates]}")
        
        # Verificar configuraciones de QR
        qr_issues = []
        qr_types = db.query(DocumentType).filter(
            DocumentType.requires_qr == True
        ).all()
        
        for doc_type in qr_types:
            if not doc_type.qr_table_number:
                qr_issues.append(f"{doc_type.code}: falta configuración de tabla QR")
        
        if qr_issues:
            warnings.extend(qr_issues)
        
        status = "healthy" if len(issues) == 0 else "unhealthy"
        
        return {
            "status": status,
            "total_types": db.query(DocumentType).count(),
            "active_types": db.query(DocumentType).filter(DocumentType.is_active == True).count(),
            "issues": issues,
            "warnings": warnings,
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error verificando integridad: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "checked_at": datetime.utcnow().isoformat()
        }