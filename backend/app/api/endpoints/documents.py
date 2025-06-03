
"""
Endpoints para gestión de documentos
CRUD completo, subida de archivos y operaciones de documentos
"""
import logging
import os
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import (
    APIRouter, Depends, HTTPException, status, Query, UploadFile, 
    File, Form, BackgroundTasks
)
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc

from ...database import get_database
from ...config import get_settings
from ...models.user import User
from ...models.document import Document
from ...models.document_type import DocumentType
from ...schemas.document import (
    Document as DocumentSchema,
    DocumentSummary,
    DocumentDetailed,
    DocumentCreate,
    DocumentUpload,
    DocumentBatchUpload,
    DocumentUpdate,
    DocumentAdminUpdate,
    DocumentFilter,
    DocumentListResponse,
    DocumentApproval,
    DocumentBulkAction,
    DocumentBulkActionResponse,
    DocumentAnalytics,
    DocumentProcessingStatus,
    DocumentExport
)
from ..deps import (
    get_current_user,
    require_admin,
    require_upload_permission,
    get_document_by_id,
    verify_document_ownership_or_admin,
    PaginationParams,
    get_request_logger,
    create_rate_limit_dependency
)
from ...services.document_service import get_document_service
from ...utils.file_handler import get_file_handler, validate_and_save_file
from ...utils.qr_processor import extract_qr_from_file

# Configuración
settings = get_settings()
logger = logging.getLogger(__name__)

# Router
router = APIRouter()

# Rate limiting para subidas
upload_rate_limit = create_rate_limit_dependency(limit=10, window=60)


# === ENDPOINTS DE CONSULTA ===

@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    # Filtros de búsqueda
    search: Optional[str] = Query(None, description="Búsqueda en texto completo"),
    document_type_id: Optional[int] = Query(None, description="Filtrar por tipo"),
    cedula: Optional[str] = Query(None, description="Filtrar por cédula"),
    nombre_completo: Optional[str] = Query(None, description="Filtrar por nombre"),
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    approval_status: Optional[str] = Query(None, description="Filtrar por aprobación"),
    
    # Filtros de fecha
    created_after: Optional[datetime] = Query(None, description="Creados después de"),
    created_before: Optional[datetime] = Query(None, description="Creados antes de"),
    
    # Filtros de metadatos
    tags: Optional[List[str]] = Query(None, description="Filtrar por tags"),
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    is_confidential: Optional[bool] = Query(None, description="Filtrar por confidencial"),
    
    # Filtros de archivo
    file_type: Optional[str] = Query(None, description="Filtrar por tipo de archivo"),
    has_qr: Optional[bool] = Query(None, description="Filtrar por presencia de QR"),
    
    # Paginación
    pagination: PaginationParams = Depends(PaginationParams),
    
    # Dependencias
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """
    Listar documentos con filtros avanzados y paginación
    """
    try:
        document_service = get_document_service()
        
        # Crear filtros
        from ...schemas.document import DocumentFilter
        filters = DocumentFilter(
            search=search,
            document_type_id=document_type_id,
            cedula=cedula,
            nombre_completo=nombre_completo,
            status=status,
            approval_status=approval_status,
            created_after=created_after,
            created_before=created_before,
            tags=tags or [],
            category=category,
            is_confidential=is_confidential,
            file_type=file_type,
            has_qr=has_qr,
            page=pagination.page,
            page_size=pagination.page_size,
            sort_by=pagination.sort_by,
            sort_order=pagination.sort_order
        )
        
        # Buscar documentos
        documents, total = document_service.search_documents(filters, current_user, db)
        
        # Convertir a schemas de respuesta
        documents_summary = [DocumentSummary.from_orm(doc) for doc in documents]
        
        # Estadísticas de filtros
        filter_stats = {
            "by_status": {},
            "by_approval": {},
            "by_type": {},
            "with_qr": 0,
            "confidential": 0
        }
        
        # Calcular estadísticas básicas
        for doc in documents:
            # Por estado
            if doc.status not in filter_stats["by_status"]:
                filter_stats["by_status"][doc.status] = 0
            filter_stats["by_status"][doc.status] += 1
            
            # Por aprobación
            if doc.approval_status not in filter_stats["by_approval"]:
                filter_stats["by_approval"][doc.approval_status] = 0
            filter_stats["by_approval"][doc.approval_status] += 1
            
            # Otros
            if doc.qr_code_id:
                filter_stats["with_qr"] += 1
            if doc.is_confidential:
                filter_stats["confidential"] += 1
        
        return DocumentListResponse(
            documents=documents_summary,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=(total + pagination.page_size - 1) // pagination.page_size,
            filter_stats=filter_stats
        )
        
    except Exception as e:
        logger.error(f"Error listando documentos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener documentos"
        )


@router.get("/{document_id}", response_model=DocumentSchema)
async def get_document(
    document: Document = Depends(get_document_by_id)
):
    """
    Obtener un documento específico
    """
    return DocumentSchema.from_orm(document)


@router.get("/{document_id}/detailed", response_model=DocumentDetailed)
async def get_document_detailed(
    document: Document = Depends(get_document_by_id),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener información detallada del documento (para administradores)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden ver información detallada"
        )
    
    return DocumentDetailed.from_orm(document)


# === ENDPOINTS DE SUBIDA ===

@router.post("/upload", response_model=DocumentSchema)
async def upload_document(
    # Datos del formulario
    document_type_id: int = Form(..., description="ID del tipo de documento"),
    cedula: Optional[str] = Form(None, description="Cédula del titular"),
    nombre_completo: Optional[str] = Form(None, description="Nombre completo"),
    telefono: Optional[str] = Form(None, description="Teléfono"),
    email: Optional[str] = Form(None, description="Email"),
    direccion: Optional[str] = Form(None, description="Dirección"),
    
    # Metadatos opcionales
    tags: Optional[str] = Form(None, description="Tags separados por comas"),
    category: Optional[str] = Form(None, description="Categoría"),
    is_confidential: bool = Form(False, description="Documento confidencial"),
    
    # Archivo
    file: UploadFile = File(..., description="Archivo del documento"),
    
    # Dependencias
    db: Session = Depends(get_database),
    current_user: User = Depends(require_upload_permission),
    log_action = Depends(get_request_logger),
    _: bool = Depends(upload_rate_limit)
):
    """
    Subir un nuevo documento
    """
    try:
        document_service = get_document_service()
        
        # Parsear tags
        tags_list = []
        if tags:
            tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Crear datos del documento
        from ...schemas.document import DocumentPersonInfo, DocumentMetadata
        person_info = DocumentPersonInfo(
            cedula=cedula,
            nombre_completo=nombre_completo,
            telefono=telefono,
            email=email,
            direccion=direccion
        )
        
        metadata = DocumentMetadata(
            tags=tags_list,
            category=category,
            is_confidential=is_confidential
        )
        
        document_data = DocumentCreate(
            document_type_id=document_type_id,
            cedula=cedula,
            nombre_completo=nombre_completo,
            telefono=telefono,
            email=email,
            direccion=direccion,
            file_info=None,  # Se llenará en el servicio
            metadata=metadata
        )
        
        # Crear documento
        document = await document_service.create_document(
            document_data, file, current_user, db
        )
        
        # Log de subida
        log_action("document_uploaded", {
            "document_id": document.id,
            "document_type_id": document_type_id,
            "file_name": file.filename,
            "file_size": file.size if hasattr(file, 'size') else None
        })
        
        logger.info(f"Documento subido: ID {document.id} por usuario {current_user.email}")
        
        return DocumentSchema.from_orm(document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error subiendo documento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al subir documento"
        )


@router.post("/upload-batch", response_model=List[DocumentProcessingStatus])
async def upload_documents_batch(
    document_type_id: int = Form(...),
    auto_extract_qr: bool = Form(True),
    auto_categorize: bool = Form(True),
    common_tags: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    
    db: Session = Depends(get_database),
    current_user: User = Depends(require_upload_permission),
    log_action = Depends(get_request_logger),
    _: bool = Depends(upload_rate_limit)
):
    """
    Subir múltiples documentos en lote
    """
    try:
        if len(files) > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Máximo 20 archivos por lote"
            )
        
        # Verificar tipo de documento
        document_type = db.query(DocumentType).filter(
            DocumentType.id == document_type_id,
            DocumentType.is_active == True
        ).first()
        
        if not document_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tipo de documento no encontrado"
            )
        
        # Parsear tags comunes
        common_tags_list = []
        if common_tags:
            common_tags_list = [tag.strip() for tag in common_tags.split(',') if tag.strip()]
        
        # Procesar archivos
        file_handler = get_file_handler()
        processing_results = await file_handler.process_multiple_uploads(
            files, document_type_id, current_user.id
        )
        
        # Crear respuestas de estado
        statuses = []
        for i, result in enumerate(processing_results):
            if result["status"] == "success":
                status_item = DocumentProcessingStatus(
                    document_id=0,  # Se asignará cuando se cree
                    status="processed",
                    progress=100,
                    message="Archivo procesado exitosamente",
                    errors=[],
                    stages={
                        "file_validation": True,
                        "file_storage": True,
                        "qr_extraction": auto_extract_qr,
                        "metadata_extraction": True
                    },
                    current_stage="completed"
                )
            else:
                status_item = DocumentProcessingStatus(
                    document_id=0,
                    status="error",
                    progress=0,
                    message=f"Error procesando archivo: {result.get('error', 'Error desconocido')}",
                    errors=[result.get('error', 'Error desconocido')],
                    stages={
                        "file_validation": False,
                        "file_storage": False,
                        "qr_extraction": False,
                        "metadata_extraction": False
                    },
                    current_stage="file_validation"
                )
            
            statuses.append(status_item)
        
        # Log del lote
        successful_count = len([r for r in processing_results if r["status"] == "success"])
        log_action("batch_upload", {
            "total_files": len(files),
            "successful": successful_count,
            "failed": len(files) - successful_count,
            "document_type_id": document_type_id
        })
        
        return statuses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en subida por lotes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al procesar lote de documentos"
        )


# === ENDPOINTS DE ACTUALIZACIÓN ===

@router.put("/{document_id}", response_model=DocumentSchema)
async def update_document(
    update_data: DocumentUpdate,
    document: Document = Depends(verify_document_ownership_or_admin),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
    log_action = Depends(get_request_logger)
):
    """
    Actualizar documento
    """
    try:
        document_service = get_document_service()
        
        updated_document = document_service.update_document(
            document.id, update_data, current_user, db
        )
        
        log_action("document_updated", {
            "document_id": document.id,
            "changes": update_data.dict(exclude_unset=True)
        })
        
        return DocumentSchema.from_orm(updated_document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando documento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar documento"
        )


@router.patch("/{document_id}/admin", response_model=DocumentDetailed)
async def admin_update_document(
    update_data: DocumentAdminUpdate,
    document: Document = Depends(get_document_by_id),
    db: Session = Depends(get_database),
    current_user: User = Depends(require_admin),
    log_action = Depends(get_request_logger)
):
    """
    Actualización administrativa de documento
    """
    try:
        original_values = {}
        # Aplicar cambios administrativos
        if update_data.status is not None:
            original_values["status"] = document.status
            document.status = update_data.status
        if update_data.approval_status is not None:
            original_values["approval_status"] = document.approval_status
            document.approval_status = update_data.approval_status
        if update_data.approval_notes is not None:
            original_values["approval_notes"] = document.approval_notes
            document.approval_notes = update_data.approval_notes
        if update_data.qr_code_id is not None:
            original_values["qr_code_id"] = document.qr_code_id
            document.qr_code_id = update_data.qr_code_id
        if update_data.file_path is not None:
            original_values["file_path"] = document.file_path
            document.file_path = update_data.file_path
        if update_data.onedrive_url is not None:
            original_values["onedrive_url"] = document.onedrive_url
            document.onedrive_url = update_data.onedrive_url
        
        # Aplicar otros cambios si existen
        if update_data.person_info:
            # Aplicar cambios de persona
            info = DocumentPersonInfo(**update_data.person_info.dict(exclude_unset=True))
            if info.cedula is not None:
                original_values["cedula"] = document.cedula
                document.cedula = info.cedula
            if info.nombre_completo is not None:
                original_values["nombre_completo"] = document.nombre_completo
                document.nombre_completo = info.nombre_completo
            if info.telefono is not None:
                original_values["telefono"] = document.telefono
                document.telefono = info.telefono
            if info.email is not None:
                original_values["email"] = document.email
                document.email = info.email
            if info.direccion is not None:
                original_values["direccion"] = document.direccion
                document.direccion = info.direccion
            if info.additional_data:
                original_values["additional_data"] = document.additional_data_dict
                document.additional_data_dict = info.additional_data
        
        if update_data.metadata:
            # Aplicar cambios de metadatos
            meta = DocumentMetadata(**update_data.metadata.dict(exclude_unset=True))
            if meta.tags is not None:
                original_values["tags"] = document.tags_list
                document.tags_list = meta.tags
            if meta.category is not None:
                original_values["category"] = document.category
                document.category = meta.category
            if meta.priority is not None:
                original_values["priority"] = document.priority
                document.priority = meta.priority
            if meta.group_id is not None:
                original_values["group_id"] = document.group_id
                document.group_id = meta.group_id
            if meta.sequence_number is not None:
                original_values["sequence_number"] = document.sequence_number
                document.sequence_number = meta.sequence_number
            if meta.is_confidential is not None:
                original_values["is_confidential"] = document.is_confidential
                document.is_confidential = meta.is_confidential
            if meta.access_level is not None:
                original_values["access_level"] = document.access_level
                document.access_level = meta.access_level

        if update_data.additional_files is not None:
            original_values["additional_files"] = document.additional_files_list
            document.additional_files_list = update_data.additional_files
        
        document.update_version(current_user.id, "Actualización administrativa")
        document.add_change_log("admin_updated", {"changes": original_values}, current_user.id)
        db.commit()
        db.refresh(document)
        
        log_action(
            "document_admin_updated",
            {
                "document_id": document.id,
                "changes": {
                    key: {"from": original_values[key], "to": getattr(document, key)}
                    for key in original_values
                    if original_values[key] != getattr(document, key)
                },
            },
        )
        
        return DocumentDetailed.from_orm(document)
        
    except Exception as e:
        logger.error(f"Error en actualización administrativa: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar documento"
        )


# === ENDPOINTS DE APROBACIÓN ===

@router.post("/{document_id}/approve")
async def approve_document(
    approval_data: DocumentApproval,
    document: Document = Depends(get_document_by_id),
    db: Session = Depends(get_database),
    current_user: User = Depends(require_admin),
    log_action = Depends(get_request_logger)
):
    """
    Aprobar o rechazar documento
    """
    try:
        document_service = get_document_service()
        
        if approval_data.approval_status.value == "approved":
            updated_document = document_service.approve_document(
                document.id, current_user, db, approval_data.notes
            )
        elif approval_data.approval_status.value == "rejected":
            if not approval_data.notes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Las notas son requeridas para rechazar un documento"
                )
            updated_document = document_service.reject_document(
                document.id, current_user, db, approval_data.notes
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estado de aprobación inválido"
            )
        
        log_action("document_approval", {
            "document_id": document.id,
            "approval_status": approval_data.approval_status.value,
            "notes": approval_data.notes
        })
        
        return {
            "message": f"Documento {approval_data.approval_status.value}",
            "document_id": document.id,
            "approval_status": updated_document.approval_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en aprobación: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al procesar aprobación"
        )


# === ENDPOINTS DE DESCARGA ===

@router.get("/{document_id}/download")
async def download_document(
    document: Document = Depends(get_document_by_id),
    current_user: User = Depends(get_current_user),
    log_action = Depends(get_request_logger)
):
    """
    Descargar archivo del documento
    """
    try:
        # Construir ruta completa del archivo
        full_path = os.path.join(settings.DOCUMENTS_PATH, document.file_path)
        
        if not os.path.exists(full_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Archivo no encontrado"
            )
        
        # Log de descarga
        log_action("document_downloaded", {
            "document_id": document.id,
            "file_name": document.file_name
        })
        
        # Marcar como visto
        document.mark_as_viewed(current_user.id)
        
        return FileResponse(
            path=full_path,
            filename=document.file_name,
            media_type=document.mime_type or "application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error descargando documento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al descargar documento"
        )


# === ENDPOINTS DE ELIMINACIÓN ===

@router.delete("/{document_id}")
async def delete_document(
    force: bool = Query(False, description="Eliminación permanente"),
    document: Document = Depends(verify_document_ownership_or_admin),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
    log_action = Depends(get_request_logger)
):
    """
    Eliminar documento (soft delete por defecto)
    """
    try:
        document_service = get_document_service()
        
        # Solo admins pueden hacer eliminación permanente
        if force and not current_user.is_admin:
            force = False
        
        success = document_service.delete_document(
            document.id, current_user, db, force
        )
        
        if success:
            log_action("document_deleted", {
                "document_id": document.id,
                "file_name": document.file_name,
                "permanent": force
            })
            
            action = "eliminado permanentemente" if force else "marcado como eliminado"
            return {
                "message": f"Documento {action}",
                "document_id": document.id,
                "permanent": force,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar documento"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando documento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar documento"
        )


# === ENDPOINTS DE ESTADÍSTICAS ===

@router.get("/analytics", response_model=DocumentAnalytics)
async def get_documents_analytics(
    document_type_id: Optional[int] = Query(None),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener análisis de documentos
    """
    try:
        # Query base
        query = db.query(Document)
        
        # Filtrar por usuario si no es admin
        if not current_user.is_admin:
            query = query.filter(
                or_(
                    Document.uploaded_by == current_user.id,
                    Document.is_confidential == False
                )
            )
        
        # Filtrar por tipo si se especifica
        if document_type_id:
            query = query.filter(Document.document_type_id == document_type_id)
        
        # Estadísticas básicas
        total_documents = query.count()
        
        # Por estado
        by_status = {}
        for status_val in ["active", "archived", "deleted", "pending_approval", "rejected"]:
            count = query.filter(Document.status == status_val).count()
            by_status[status_val] = count
        
        # Por tipo de documento
        by_type = db.query(
            DocumentType.code,
            DocumentType.name,
            func.count(Document.id).label('count')
        ).join(Document).group_by(
            DocumentType.id, DocumentType.code, DocumentType.name
        ).all()
        
        by_type_data = [
            {"type_code": code, "type_name": name, "count": count}
            for code, name, count in by_type
        ]
        
        # Por estado de aprobación
        by_approval_status = {}
        for approval_val in ["auto_approved", "pending", "approved", "rejected"]:
            count = query.filter(Document.approval_status == approval_val).count()
            by_approval_status[approval_val] = count
        
        # Análisis temporal
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        uploaded_last_30_days = query.filter(Document.created_at >= thirty_days_ago).count()
        approved_last_30_days = query.filter(
            and_(
                Document.approval_status == "approved",
                Document.approved_at >= thirty_days_ago
            )
        ).count()
        
        # Análisis de archivos
        total_size_bytes = db.query(func.sum(Document.file_size)).scalar() or 0
        total_size_gb = round(total_size_bytes / (1024**3), 2)
        avg_file_size_mb = round((total_size_bytes / total_documents) / (1024**2), 2) if total_documents > 0 else 0
        
        # Distribución por tipo de archivo
        file_types = db.query(
            Document.mime_type,
            func.count(Document.id).label('count')
        ).group_by(Document.mime_type).all()
        
        file_types_distribution = {
            mime_type or "unknown": count for mime_type, count in file_types
        }
        
        # Análisis de QR
        documents_with_qr = query.filter(Document.qr_code_id.isnot(None)).count()
        qr_extraction_success = query.filter(Document.qr_extraction_success == True).count()
        qr_extraction_success_rate = (qr_extraction_success / documents_with_qr * 100) if documents_with_qr > 0 else 0
        
        return DocumentAnalytics(
            total_documents=total_documents,
            by_status=by_status,
            by_type=by_type_data,
            by_approval_status=by_approval_status,
            uploaded_last_30_days=uploaded_last_30_days,
            approved_last_30_days=approved_last_30_days,
            total_size_gb=total_size_gb,
            avg_file_size_mb=avg_file_size_mb,
            file_types_distribution=file_types_distribution,
            documents_with_qr=documents_with_qr,
            qr_extraction_success_rate=round(qr_extraction_success_rate, 2)
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo análisis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener análisis de documentos"
        )