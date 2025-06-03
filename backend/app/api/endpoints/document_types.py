
"""
Endpoints para gestión de tipos de documento
CRUD completo y operaciones administrativas
"""
import logging
import os
import shutil
from typing import List, Optional
from datetime import datetime

from fastapi import (
    APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ...database import get_database
from ...config import get_settings
from ...models.user import User
from ...models.document_type import DocumentType
from ...models.document import Document
from ...models.qr_code import QRCode
from ...schemas.document_type import (
    DocumentType as DocumentTypeSchema,
    DocumentTypeSummary,
    DocumentTypeCreate,
    DocumentTypeUpdate,
    DocumentTypeAdminUpdate,
    DocumentTypeFilter,
    DocumentTypeListResponse,
    DocumentTypeValidation,
    DocumentTypeValidationResponse,
    DocumentTypeClone,
    DocumentTypeBulkAction,
    DocumentTypeBulkActionResponse,
    DocumentTypeTemplate,
    DocumentTypeExport
)
from ..deps import (
    get_current_user,
    require_admin,
    require_manage_types_permission,
    get_document_type_by_id,
    PaginationParams,
    get_request_logger,
    create_rate_limit_dependency
)

# Configuración
settings = get_settings()
logger = logging.getLogger(__name__)

# Router
router = APIRouter()

# Rate limiting para operaciones sensibles
admin_rate_limit = create_rate_limit_dependency(limit=30, window=60)


# === ENDPOINTS DE CONSULTA ===

@router.get("/", response_model=DocumentTypeListResponse)
async def list_document_types(
    # Filtros
    search: Optional[str] = Query(None, description="Búsqueda por código o nombre"),
    is_active: Optional[bool] = Query(None, description="Filtrar por activo"),
    requires_qr: Optional[bool] = Query(None, description="Filtrar por requisito de QR"),
    can_generate: Optional[bool] = Query(None, description="Filtrar por capacidad de generación"),
    created_by: Optional[int] = Query(None, description="Filtrar por creador"),
    
    # Paginación
    pagination: PaginationParams = Depends(PaginationParams),
    
    # Dependencias
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """
    Listar tipos de documento con filtros y paginación
    
    Args:
        search: Término de búsqueda
        is_active: Filtrar por estado activo
        requires_qr: Filtrar por requisito de QR
        can_generate: Filtrar por capacidad de generación
        created_by: Filtrar por usuario creador
        pagination: Parámetros de paginación
        db: Sesión de base de datos
        current_user: Usuario actual
        
    Returns:
        DocumentTypeListResponse: Lista paginada de tipos de documento
    """
    try:
        # Query base
        query = db.query(DocumentType)
        
        # Aplicar filtros
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    DocumentType.code.ilike(search_term),
                    DocumentType.name.ilike(search_term),
                    DocumentType.description.ilike(search_term)
                )
            )
        
        if is_active is not None:
            query = query.filter(DocumentType.is_active == is_active)
        elif not current_user.is_admin:
            # No admins solo ven tipos activos
            query = query.filter(DocumentType.is_active == True)
        
        if requires_qr is not None:
            query = query.filter(DocumentType.requires_qr == requires_qr)
        
        if can_generate is not None:
            if can_generate:
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
        
        if created_by is not None:
            query = query.filter(DocumentType.created_by == created_by)
        
        # Contar total
        total = query.count()
        
        # Aplicar ordenamiento
        if pagination.sort_by == "name":
            order_column = DocumentType.name
        elif pagination.sort_by == "code":
            order_column = DocumentType.code
        elif pagination.sort_by == "created_at":
            order_column = DocumentType.created_at
        elif pagination.sort_by == "updated_at":
            order_column = DocumentType.updated_at
        elif pagination.sort_by == "documents_count":
            order_column = DocumentType.documents_count
        elif pagination.sort_by == "sort_order":
            order_column = DocumentType.sort_order
        else:
            order_column = DocumentType.created_at
        
        if pagination.sort_order == "desc":
            order_column = order_column.desc()
        
        query = query.order_by(order_column)
        
        # Aplicar paginación
        document_types = query.offset(pagination.offset).limit(pagination.limit).all()
        
        # Convertir a schemas de respuesta
        document_types_summary = [
            DocumentTypeSummary.from_orm(dt) for dt in document_types
        ]
        
        return DocumentTypeListResponse(
            document_types=document_types_summary,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=(total + pagination.page_size - 1) // pagination.page_size
        )
        
    except Exception as e:
        logger.error(f"Error listando tipos de documento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener tipos de documento"
        )


@router.get("/{document_type_id}", response_model=DocumentTypeSchema)
async def get_document_type(
    document_type: DocumentType = Depends(get_document_type_by_id)
):
    """
    Obtener un tipo de documento específico
    
    Args:
        document_type: Tipo de documento (inyectado por dependencia)
        
    Returns:
        DocumentTypeSchema: Tipo de documento completo
    """
    return DocumentTypeSchema.from_orm(document_type)


@router.get("/code/{type_code}", response_model=DocumentTypeSchema)
async def get_document_type_by_code(
    type_code: str,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener tipo de documento por código
    
    Args:
        type_code: Código del tipo de documento
        db: Sesión de base de datos
        current_user: Usuario actual
        
    Returns:
        DocumentTypeSchema: Tipo de documento encontrado
    """
    document_type = db.query(DocumentType).filter(
        DocumentType.code == type_code.upper()
    ).first()
    
    if not document_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de documento no encontrado"
        )
    
    # Verificar acceso
    if not document_type.is_active and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de documento no encontrado"
        )
    
    return DocumentTypeSchema.from_orm(document_type)


# === ENDPOINTS DE CREACIÓN Y MODIFICACIÓN ===

@router.post("/", response_model=DocumentTypeSchema, status_code=status.HTTP_201_CREATED)
async def create_document_type(
    document_type_data: DocumentTypeCreate,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_manage_types_permission),
    log_action = Depends(get_request_logger),
    _: bool = Depends(admin_rate_limit)
):
    """
    Crear nuevo tipo de documento
    
    Args:
        document_type_data: Datos del tipo de documento
        db: Sesión de base de datos
        current_user: Usuario actual (con permisos)
        log_action: Logger de acciones
        
    Returns:
        DocumentTypeSchema: Tipo de documento creado
    """
    try:
        # Verificar que el código no exista
        existing = db.query(DocumentType).filter(
            DocumentType.code == document_type_data.code.upper()
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un tipo de documento con el código: {document_type_data.code}"
            )
        
        # Crear tipo de documento
        document_type = DocumentType(
            code=document_type_data.code.upper(),
            name=document_type_data.name,
            description=document_type_data.description,
            
            # Requisitos
            requires_qr=document_type_data.requirements.requires_qr,
            requires_cedula=document_type_data.requirements.requires_cedula,
            requires_nombre=document_type_data.requirements.requires_nombre,
            requires_telefono=document_type_data.requirements.requires_telefono,
            requires_email=document_type_data.requirements.requires_email,
            requires_direccion=document_type_data.requirements.requires_direccion,
            
            # Configuración de archivos
            allowed_file_types=document_type_data.file_config.allowed_file_types,
            max_file_size_mb=document_type_data.file_config.max_file_size_mb,
            allow_multiple_files=document_type_data.file_config.allow_multiple_files,
            
            # Configuración de UI
            color=document_type_data.ui_config.color,
            icon=document_type_data.ui_config.icon,
            sort_order=document_type_data.ui_config.sort_order,
            
            # Configuración de workflow
            requires_approval=document_type_data.workflow.requires_approval,
            auto_notify_email=document_type_data.workflow.auto_notify_email,
            notification_emails=document_type_data.workflow.notification_emails,
            retention_days=document_type_data.workflow.retention_days,
            auto_archive=document_type_data.workflow.auto_archive,
            
            # Plantilla y QR
            template_path=document_type_data.template_path,
            
            # Auditoría
            created_by=current_user.id
        )
        
        # Configuración de QR si se requiere
        if document_type_data.qr_config:
            document_type.qr_table_number = document_type_data.qr_config.qr_table_number
            document_type.qr_row = document_type_data.qr_config.qr_row
            document_type.qr_column = document_type_data.qr_config.qr_column
            document_type.qr_width = document_type_data.qr_config.qr_width
            document_type.qr_height = document_type_data.qr_config.qr_height
        
        db.add(document_type)
        db.commit()
        db.refresh(document_type)
        
        # Log de creación
        log_action("document_type_created", {
            "document_type_id": document_type.id,
            "code": document_type.code,
            "name": document_type.name
        })
        
        logger.info(f"Tipo de documento creado: {document_type.code} por usuario {current_user.email}")
        
        return DocumentTypeSchema.from_orm(document_type)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando tipo de documento: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear tipo de documento"
        )


@router.put("/{document_type_id}", response_model=DocumentTypeSchema)
async def update_document_type(
    document_type_data: DocumentTypeUpdate,
    document_type: DocumentType = Depends(get_document_type_by_id),
    db: Session = Depends(get_database),
    current_user: User = Depends(require_manage_types_permission),
    log_action = Depends(get_request_logger)
):
    """
    Actualizar tipo de documento
    
    Args:
        document_type_data: Datos actualizados
        document_type: Tipo de documento existente
        db: Sesión de base de datos
        current_user: Usuario actual
        log_action: Logger de acciones
        
    Returns:
        DocumentTypeSchema: Tipo de documento actualizado
    """
    try:
        # Verificar si es tipo de sistema (no editable)
        if document_type.is_system_type and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los tipos de sistema solo pueden ser editados por administradores"
            )
        
        # Guardar valores originales para log
        original_values = {
            "name": document_type.name,
            "description": document_type.description,
            "is_active": document_type.is_active
        }
        
        # Actualizar campos básicos
        if document_type_data.name is not None:
            document_type.name = document_type_data.name
        if document_type_data.description is not None:
            document_type.description = document_type_data.description
        if document_type_data.is_active is not None:
            document_type.is_active = document_type_data.is_active
        
        # Actualizar configuraciones si se proporcionan
        if document_type_data.requirements:
            document_type.requires_qr = document_type_data.requirements.requires_qr
            document_type.requires_cedula = document_type_data.requirements.requires_cedula
            document_type.requires_nombre = document_type_data.requirements.requires_nombre
            document_type.requires_telefono = document_type_data.requirements.requires_telefono
            document_type.requires_email = document_type_data.requirements.requires_email
            document_type.requires_direccion = document_type_data.requirements.requires_direccion
        
        if document_type_data.file_config:
            document_type.allowed_file_types = document_type_data.file_config.allowed_file_types
            document_type.max_file_size_mb = document_type_data.file_config.max_file_size_mb
            document_type.allow_multiple_files = document_type_data.file_config.allow_multiple_files
        
        if document_type_data.ui_config:
            document_type.color = document_type_data.ui_config.color
            document_type.icon = document_type_data.ui_config.icon
            document_type.sort_order = document_type_data.ui_config.sort_order
        
        if document_type_data.workflow:
            document_type.requires_approval = document_type_data.workflow.requires_approval
            document_type.auto_notify_email = document_type_data.workflow.auto_notify_email
            document_type.notification_emails = document_type_data.workflow.notification_emails
            document_type.retention_days = document_type_data.workflow.retention_days
            document_type.auto_archive = document_type_data.workflow.auto_archive
        
        # Actualizar configuración de plantilla
        if document_type_data.template_path is not None:
            document_type.template_path = document_type_data.template_path
        
        # Actualizar configuración de QR
        if document_type_data.qr_config:
            document_type.qr_table_number = document_type_data.qr_config.qr_table_number
            document_type.qr_row = document_type_data.qr_config.qr_row
            document_type.qr_column = document_type_data.qr_config.qr_column
            document_type.qr_width = document_type_data.qr_config.qr_width
            document_type.qr_height = document_type_data.qr_config.qr_height
        
        db.commit()
        db.refresh(document_type)
        
        # Log de actualización
        log_action("document_type_updated", {
            "document_type_id": document_type.id,
            "code": document_type.code,
            "changes": {
                key: {"from": original_values[key], "to": getattr(document_type, key)}
                for key in original_values
                if original_values[key] != getattr(document_type, key)
            }
        })
        
        logger.info(f"Tipo de documento actualizado: {document_type.code}")
        
        return DocumentTypeSchema.from_orm(document_type)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando tipo de documento: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar tipo de documento"
        )


@router.patch("/{document_type_id}/admin", response_model=DocumentTypeSchema)
async def admin_update_document_type(
    document_type_data: DocumentTypeAdminUpdate,
    document_type: DocumentType = Depends(get_document_type_by_id),
    db: Session = Depends(get_database),
    current_user: User = Depends(require_admin),
    log_action = Depends(get_request_logger)
):
    """
    Actualización administrativa de tipo de documento (solo admins)
    
    Args:
        document_type_data: Datos de actualización administrativa
        document_type: Tipo de documento existente
        db: Sesión de base de datos
        current_user: Usuario administrador
        log_action: Logger de acciones
        
    Returns:
        DocumentTypeSchema: Tipo de documento actualizado
    """
    try:
        # Verificar cambio de código (solo admins)
        if document_type_data.code and document_type_data.code != document_type.code:
            # Verificar que el nuevo código no exista
            existing = db.query(DocumentType).filter(
                DocumentType.code == document_type_data.code.upper(),
                DocumentType.id != document_type.id
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya existe un tipo con el código: {document_type_data.code}"
                )
            
            old_code = document_type.code
            document_type.code = document_type_data.code.upper()
            
            log_action("document_type_code_changed", {
                "document_type_id": document_type.id,
                "old_code": old_code,
                "new_code": document_type.code
            })
        
        # Actualizar otros campos administrativos
        if document_type_data.is_system_type is not None:
            document_type.is_system_type = document_type_data.is_system_type
        
        # Aplicar otras actualizaciones usando el método padre
        # Convertir a DocumentTypeUpdate para reutilizar lógica
        regular_update = DocumentTypeUpdate(
            name=document_type_data.name,
            description=document_type_data.description,
            requirements=document_type_data.requirements,
            file_config=document_type_data.file_config,
            ui_config=document_type_data.ui_config,
            workflow=document_type_data.workflow,
            template_path=document_type_data.template_path,
            qr_config=document_type_data.qr_config,
            is_active=document_type_data.is_active
        )
        
        # Aplicar actualizaciones regulares
        if regular_update.name is not None:
            document_type.name = regular_update.name
        if regular_update.description is not None:
            document_type.description = regular_update.description
        if regular_update.is_active is not None:
            document_type.is_active = regular_update.is_active
        
        # ... (aplicar otras configuraciones igual que en update_document_type)
        
        db.commit()
        db.refresh(document_type)
        
        log_action("document_type_admin_updated", {
            "document_type_id": document_type.id,
            "code": document_type.code
        })
        
        return DocumentTypeSchema.from_orm(document_type)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en actualización administrativa: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar tipo de documento"
        )


# === ENDPOINTS DE VALIDACIÓN ===

@router.post("/validate", response_model=DocumentTypeValidationResponse)
async def validate_document_data(
    validation_data: DocumentTypeValidation,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """
    Validar datos de documento según tipo
    
    Args:
        validation_data: Datos a validar
        db: Sesión de base de datos
        current_user: Usuario actual
        
    Returns:
        DocumentTypeValidationResponse: Resultado de validación
    """
    try:
        # Obtener tipo de documento
        document_type = db.query(DocumentType).filter(
            DocumentType.id == validation_data.document_type_id
        ).first()
        
        if not document_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tipo de documento no encontrado"
            )
        
        # Validar datos usando el método del modelo
        is_valid, errors = document_type.validate_document_data(validation_data.data)
        
        # Obtener campos requeridos y faltantes
        required_fields = document_type.required_fields
        missing_fields = [
            field for field in required_fields
            if field not in validation_data.data or not validation_data.data[field]
        ]
        
        return DocumentTypeValidationResponse(
            is_valid=is_valid,
            errors=errors,
            warnings=[],  # Se pueden agregar warnings específicos
            required_fields=required_fields,
            missing_fields=missing_fields
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validando datos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al validar datos"
        )


# === ENDPOINTS DE OPERACIONES ESPECIALES ===

@router.post("/clone", response_model=DocumentTypeSchema)
async def clone_document_type(
    clone_data: DocumentTypeClone,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_manage_types_permission),
    log_action = Depends(get_request_logger),
    _: bool = Depends(admin_rate_limit)
):
    """
    Clonar tipo de documento existente
    
    Args:
        clone_data: Datos para la clonación
        db: Sesión de base de datos
        current_user: Usuario actual
        log_action: Logger de acciones
        
    Returns:
        DocumentTypeSchema: Tipo de documento clonado
    """
    try:
        # Obtener tipo original
        source_type = db.query(DocumentType).filter(
            DocumentType.id == clone_data.source_id
        ).first()
        
        if not source_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tipo de documento origen no encontrado"
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
            created_by=current_user.id
        )
        
        # Copiar plantilla si se solicita
        if clone_data.copy_template and source_type.template_path:
            try:
                # Implementar copia de plantilla
                source_path = os.path.join(settings.TEMPLATES_PATH, source_type.template_path)
                if os.path.exists(source_path):
                    new_template_name = f"{clone_data.new_code.lower()}_template.docx"
                    dest_path = os.path.join(settings.TEMPLATES_PATH, new_template_name)
                    shutil.copy2(source_path, dest_path)
                    cloned_type.template_path = new_template_name
            except Exception as e:
                logger.warning(f"Error copiando plantilla: {str(e)}")
        
        db.add(cloned_type)
        db.commit()
        db.refresh(cloned_type)
        
        # Log de clonación
        log_action("document_type_cloned", {
            "source_id": clone_data.source_id,
            "source_code": source_type.code,
            "new_id": cloned_type.id,
            "new_code": cloned_type.code,
            "template_copied": clone_data.copy_template
        })
        
        logger.info(f"Tipo clonado: {source_type.code} -> {cloned_type.code}")
        
        return DocumentTypeSchema.from_orm(cloned_type)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clonando tipo de documento: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al clonar tipo de documento"
        )


@router.patch("/{document_type_id}/toggle")
async def toggle_document_type_status(
    document_type: DocumentType = Depends(get_document_type_by_id),
    db: Session = Depends(get_database),
    current_user: User = Depends(require_manage_types_permission),
    log_action = Depends(get_request_logger)
):
    """
    Activar/desactivar tipo de documento
    
    Args:
        document_type: Tipo de documento
        db: Sesión de base de datos
        current_user: Usuario actual
        log_action: Logger de acciones
        
    Returns:
        dict: Estado actualizado
    """
    try:
        old_status = document_type.is_active
        document_type.is_active = not document_type.is_active
        
        db.commit()
        
        log_action("document_type_toggled", {
            "document_type_id": document_type.id,
            "code": document_type.code,
            "old_status": old_status,
            "new_status": document_type.is_active
        })
        
        action = "activado" if document_type.is_active else "desactivado"
        logger.info(f"Tipo de documento {action}: {document_type.code}")
        
        return {
            "message": f"Tipo de documento {action}",
            "is_active": document_type.is_active,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error cambiando estado: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al cambiar estado del tipo"
        )


@router.delete("/{document_type_id}")
async def delete_document_type(
    document_type: DocumentType = Depends(get_document_type_by_id),
    force: bool = Query(False, description="Forzar eliminación even with documents"),
    db: Session = Depends(get_database),
    current_user: User = Depends(require_admin),
    log_action = Depends(get_request_logger),
    _: bool = Depends(admin_rate_limit)
):
    """
    Eliminar tipo de documento (solo administradores)
    
    Args:
        document_type: Tipo de documento
        force: Forzar eliminación incluso con documentos asociados
        db: Sesión de base de datos
        current_user: Usuario administrador
        log_action: Logger de acciones
        
    Returns:
        dict: Confirmación de eliminación
    """
    try:
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
                detail=f"No se puede eliminar. Hay {doc_count} documentos y {qr_count} códigos QR asociados. Use force=true para forzar eliminación."
            )
        
        # Eliminar plantilla si existe
        if document_type.template_path:
            try:
                template_path = os.path.join(settings.TEMPLATES_PATH, document_type.template_path)
                if os.path.exists(template_path):
                    os.remove(template_path)
                    logger.info(f"Plantilla eliminada: {template_path}")
            except Exception as e:
                logger.warning(f"Error eliminando plantilla: {str(e)}")
        
        # Guardar información para log
        type_info = {
            "id": document_type.id,
            "code": document_type.code,
            "name": document_type.name,
            "documents_count": doc_count,
            "qr_count": qr_count
        }
        
        # Eliminar tipo de documento
        db.delete(document_type)
        db.commit()
        
        # Log de eliminación
        log_action("document_type_deleted", {
            **type_info,
            "forced": force
        })
        
        logger.info(f"Tipo de documento eliminado: {type_info['code']}")
        
        return {
            "message": "Tipo de documento eliminado",
            "deleted_type": type_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando tipo de documento: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar tipo de documento"
        )


# === ENDPOINTS DE OPERACIONES EN LOTE ===

@router.post("/bulk-action", response_model=DocumentTypeBulkActionResponse)
async def bulk_action_document_types(
    action_data: DocumentTypeBulkAction,
    db: Session = Depends(get_database),
    current_user: User = Depends(require_admin),
    log_action = Depends(get_request_logger),
    _: bool = Depends(admin_rate_limit)
):
    """
    Ejecutar acción en lote sobre tipos de documento
    
    Args:
        action_data: Datos de la acción en lote
        db: Sesión de base de datos
        current_user: Usuario administrador
        log_action: Logger de acciones
        
    Returns:
        DocumentTypeBulkActionResponse: Resultado de la operación
    """
    try:
        success_count = 0
        error_count = 0
        errors = []
        
        # Obtener tipos de documento
        document_types = db.query(DocumentType).filter(
            DocumentType.id.in_(action_data.type_ids)
        ).all()
        
        if len(document_types) != len(action_data.type_ids):
            found_ids = [dt.id for dt in document_types]
            missing_ids = [id for id in action_data.type_ids if id not in found_ids]
            errors.append({
                "error": "Algunos tipos no fueron encontrados",
                "missing_ids": missing_ids
            })
        
        for document_type in document_types:
            try:
                if action_data.action == "activate":
                    document_type.is_active = True
                    success_count += 1
                    
                elif action_data.action == "deactivate":
                    document_type.is_active = False
                    success_count += 1
                    
                elif action_data.action == "delete":
                    # Verificar que no sea tipo de sistema
                    if document_type.is_system_type:
                        errors.append({
                            "document_type_id": document_type.id,
                            "error": "Tipo de sistema no puede ser eliminado"
                        })
                        error_count += 1
                        continue
                    
                    # Verificar documentos asociados
                    doc_count = db.query(Document).filter(
                        Document.document_type_id == document_type.id
                    ).count()
                    
                    if doc_count > 0:
                        errors.append({
                            "document_type_id": document_type.id,
                            "error": f"Tiene {doc_count} documentos asociados"
                        })
                        error_count += 1
                        continue
                    
                    db.delete(document_type)
                    success_count += 1
                    
            except Exception as e:
                errors.append({
                    "document_type_id": document_type.id,
                    "error": str(e)
                })
                error_count += 1
        
        # Commit cambios
        if success_count > 0:
            db.commit()
        
        # Log de acción en lote
        log_action("document_types_bulk_action", {
            "action": action_data.action,
            "requested_count": len(action_data.type_ids),
            "success_count": success_count,
            "error_count": error_count
        })
        
        logger.info(
            f"Acción en lote '{action_data.action}': "
            f"{success_count} exitosas, {error_count} errores"
        )
        
        return DocumentTypeBulkActionResponse(
            success_count=success_count,
            error_count=error_count,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Error en acción en lote: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error ejecutando acción en lote"
        )


# === ENDPOINTS DE PLANTILLAS ===

@router.get("/{document_type_id}/template", response_model=DocumentTypeTemplate)
async def get_template_info(
    document_type: DocumentType = Depends(get_document_type_by_id)
):
    """
    Obtener información de la plantilla del tipo de documento
    
    Args:
        document_type: Tipo de documento
        
    Returns:
        DocumentTypeTemplate: Información de la plantilla
    """
    template_info = DocumentTypeTemplate(
        has_template=document_type.has_template,
        template_path=document_type.template_path,
        template_name=os.path.basename(document_type.template_path) if document_type.template_path else None
    )
    
    # Obtener información adicional del archivo si existe
    if document_type.template_path:
        try:
            full_path = os.path.join(settings.TEMPLATES_PATH, document_type.template_path)
            if os.path.exists(full_path):
                stat = os.stat(full_path)
                template_info.template_size = stat.st_size
                template_info.last_modified = datetime.fromtimestamp(stat.st_mtime)
        except Exception as e:
            logger.warning(f"Error obteniendo info de plantilla: {str(e)}")
    
    return template_info


@router.post("/{document_type_id}/template")
async def upload_template(
    document_type_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_database),
    current_user: User = Depends(require_manage_types_permission),
    log_action = Depends(get_request_logger)
):
    """
    Subir plantilla para tipo de documento
    
    Args:
        document_type_id: ID del tipo de documento
        file: Archivo de plantilla
        db: Sesión de base de datos
        current_user: Usuario actual
        log_action: Logger de acciones
        
    Returns:
        dict: Información de la plantilla subida
    """
    try:
        # Obtener tipo de documento
        document_type = db.query(DocumentType).filter(
            DocumentType.id == document_type_id
        ).first()
        
        if not document_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tipo de documento no encontrado"
            )
        
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
            old_path = os.path.join(settings.TEMPLATES_PATH, document_type.template_path)
            try:
                if os.path.exists(old_path):
                    os.remove(old_path)
            except Exception as e:
                logger.warning(f"Error eliminando plantilla anterior: {str(e)}")
        
        # Actualizar tipo de documento
        document_type.template_path = new_filename
        db.commit()
        
        # Log de subida
        log_action("template_uploaded", {
            "document_type_id": document_type.id,
            "code": document_type.code,
            "filename": new_filename,
            "file_size": len(content)
        })
        
        logger.info(f"Plantilla subida para {document_type.code}: {new_filename}")
        
        return {
            "message": "Plantilla subida exitosamente",
            "filename": new_filename,
            "size": len(content),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error subiendo plantilla: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al subir plantilla"
        )


@router.get("/{document_type_id}/template/download")
async def download_template(
    document_type: DocumentType = Depends(get_document_type_by_id),
    current_user: User = Depends(get_current_user),
    log_action = Depends(get_request_logger)
):
    """
    Descargar plantilla del tipo de documento
    
    Args:
        document_type: Tipo de documento
        current_user: Usuario actual
        log_action: Logger de acciones
        
    Returns:
        FileResponse: Archivo de plantilla
    """
    try:
        if not document_type.template_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Este tipo de documento no tiene plantilla"
            )
        
        template_path = os.path.join(settings.TEMPLATES_PATH, document_type.template_path)
        
        if not os.path.exists(template_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Archivo de plantilla no encontrado"
            )
        
        # Log de descarga
        log_action("template_downloaded", {
            "document_type_id": document_type.id,
            "code": document_type.code,
            "template_path": document_type.template_path
        })
        
        # Nombre de descarga amigable
        download_name = f"plantilla_{document_type.code.lower()}.docx"
        
        return FileResponse(
            path=template_path,
            filename=download_name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error descargando plantilla: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al descargar plantilla"
        )


@router.delete("/{document_type_id}/template")
async def delete_template(
    document_type: DocumentType = Depends(get_document_type_by_id),
    db: Session = Depends(get_database),
    current_user: User = Depends(require_manage_types_permission),
    log_action = Depends(get_request_logger)
):
    """
    Eliminar plantilla del tipo de documento
    
    Args:
        document_type: Tipo de documento
        db: Sesión de base de datos
        current_user: Usuario actual
        log_action: Logger de acciones
        
    Returns:
        dict: Confirmación de eliminación
    """
    try:
        if not document_type.template_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Este tipo de documento no tiene plantilla"
            )
        
        # Eliminar archivo físico
        template_path = os.path.join(settings.TEMPLATES_PATH, document_type.template_path)
        try:
            if os.path.exists(template_path):
                os.remove(template_path)
        except Exception as e:
            logger.warning(f"Error eliminando archivo de plantilla: {str(e)}")
        
        # Actualizar base de datos
        old_template = document_type.template_path
        document_type.template_path = None
        db.commit()
        
        # Log de eliminación
        log_action("template_deleted", {
            "document_type_id": document_type.id,
            "code": document_type.code,
            "deleted_template": old_template
        })
        
        logger.info(f"Plantilla eliminada para {document_type.code}")
        
        return {
            "message": "Plantilla eliminada exitosamente",
            "deleted_template": old_template,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando plantilla: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar plantilla"
        )


# === ENDPOINTS DE EXPORTACIÓN ===

@router.get("/export", response_model=List[DocumentTypeExport])
async def export_document_types(
    format: str = Query("json", regex="^(json|csv)$"),
    include_inactive: bool = Query(False),
    db: Session = Depends(get_database),
    current_user: User = Depends(require_admin),
    log_action = Depends(get_request_logger)
):
    """
    Exportar tipos de documento
    
    Args:
        format: Formato de exportación (json, csv)
        include_inactive: Incluir tipos inactivos
        db: Sesión de base de datos
        current_user: Usuario administrador
        log_action: Logger de acciones
        
    Returns:
        List[DocumentTypeExport]: Datos exportados
    """
    try:
        # Query base
        query = db.query(DocumentType)
        
        if not include_inactive:
            query = query.filter(DocumentType.is_active == True)
        
        document_types = query.all()
        
        # Convertir a formato de exportación
        export_data = [
            DocumentTypeExport.from_orm(dt) for dt in document_types
        ]
        
        # Log de exportación
        log_action("document_types_exported", {
            "format": format,
            "count": len(export_data),
            "include_inactive": include_inactive
        })
        
        logger.info(f"Exportados {len(export_data)} tipos de documento en formato {format}")
        
        return export_data
        
    except Exception as e:
        logger.error(f"Error exportando tipos de documento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al exportar tipos de documento"
        )


# === ENDPOINTS DE ESTADÍSTICAS ===

@router.get("/stats")
async def get_document_types_stats(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener estadísticas de tipos de documento
    
    Args:
        db: Sesión de base de datos
        current_user: Usuario actual
        
    Returns:
        dict: Estadísticas de tipos de documento
    """
    try:
        # Estadísticas básicas
        total_types = db.query(DocumentType).count()
        active_types = db.query(DocumentType).filter(DocumentType.is_active == True).count()
        types_with_qr = db.query(DocumentType).filter(DocumentType.requires_qr == True).count()
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
        
        # Distribución por estado
        status_distribution = {
            "active": active_types,
            "inactive": total_types - active_types
        }
        
        # Distribución por características
        feature_distribution = {
            "requires_qr": types_with_qr,
            "has_template": types_with_templates,
            "requires_approval": db.query(DocumentType).filter(
                DocumentType.requires_approval == True
            ).count()
        }
        
        return {
            "summary": {
                "total_types": total_types,
                "active_types": active_types,
                "inactive_types": total_types - active_types,
                "with_qr": types_with_qr,
                "with_templates": types_with_templates
            },
            "status_distribution": status_distribution,
            "feature_distribution": feature_distribution,
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