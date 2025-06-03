
"""
Esquemas Pydantic para Documentos
Validación y serialización del modelo principal de documentos
"""
from pydantic import BaseModel, EmailStr, Field, validator, root_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import re


# === ENUMS ===

class DocumentStatus(str, Enum):
    """Estados posibles del documento"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    PENDING_APPROVAL = "pending_approval"
    REJECTED = "rejected"


class ApprovalStatus(str, Enum):
    """Estados de aprobación"""
    AUTO_APPROVED = "auto_approved"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AccessLevel(str, Enum):
    """Niveles de acceso"""
    NORMAL = "normal"
    RESTRICTED = "restricted"
    CONFIDENTIAL = "confidential"


class DocumentPriority(int, Enum):
    """Niveles de prioridad"""
    LOW = -1
    NORMAL = 0
    HIGH = 1
    URGENT = 2


# === ESQUEMAS BASE ===

class DocumentBase(BaseModel):
    """Esquema base para documento"""
    document_type_id: int = Field(..., description="ID del tipo de documento")
    
    # Información de la persona (campos principales)
    cedula: Optional[str] = Field(None, max_length=20, description="Número de identificación")
    nombre_completo: Optional[str] = Field(None, max_length=200, description="Nombre completo")
    
    # Información de contacto (opcional según tipo)
    telefono: Optional[str] = Field(None, max_length=20, description="Teléfono")
    email: Optional[EmailStr] = Field(None, description="Email de contacto")
    direccion: Optional[str] = Field(None, max_length=500, description="Dirección")
    
    @validator('cedula')
    def validate_cedula(cls, v):
        """Validar formato de cédula"""
        if v:
            # Limpiar caracteres no numéricos
            cleaned = re.sub(r'[^\d]', '', v)
            if len(cleaned) < 6 or len(cleaned) > 15:
                raise ValueError('Cédula debe tener entre 6 y 15 dígitos')
            return cleaned
        return v
    
    @validator('telefono')
    def validate_telefono(cls, v):
        """Validar formato de teléfono"""
        if v:
            # Permitir números, espacios, guiones, paréntesis y +
            cleaned = re.sub(r'[^\d\+\-\s\(\)]', '', v)
            digits_only = re.sub(r'[^\d]', '', cleaned)
            if len(digits_only) < 7:
                raise ValueError('Teléfono debe tener al menos 7 dígitos')
            return cleaned.strip()
        return v


class DocumentPersonInfo(BaseModel):
    """Esquema para información de la persona"""
    cedula: Optional[str] = Field(None, max_length=20)
    nombre_completo: Optional[str] = Field(None, max_length=200)
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    direccion: Optional[str] = Field(None, max_length=500)
    
    # Datos adicionales dinámicos según el tipo de documento
    additional_data: Dict[str, Any] = Field(default_factory=dict, description="Datos adicionales")


class DocumentFileInfo(BaseModel):
    """Esquema para información del archivo"""
    file_name: str = Field(..., min_length=1, max_length=255, description="Nombre del archivo")
    file_size: Optional[int] = Field(None, ge=0, description="Tamaño en bytes")
    mime_type: Optional[str] = Field(None, max_length=100, description="Tipo MIME")
    file_hash: Optional[str] = Field(None, max_length=64, description="Hash SHA-256")
    
    @validator('file_name')
    def validate_file_name(cls, v):
        """Validar nombre de archivo"""
        # Eliminar caracteres peligrosos
        if not v or v.strip() == '':
            raise ValueError('Nombre de archivo no puede estar vacío')
        
        # Verificar caracteres prohibidos
        prohibited_chars = r'[<>:"/\\|?*]'
        if re.search(prohibited_chars, v):
            raise ValueError('Nombre de archivo contiene caracteres prohibidos')
        
        return v.strip()
    
    @validator('mime_type')
    def validate_mime_type(cls, v):
        """Validar tipo MIME"""
        if v:
            valid_types = [
                'application/pdf',
                'image/jpeg', 'image/png', 'image/jpg', 'image/gif',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/msword',
                'text/plain'
            ]
            if v not in valid_types:
                raise ValueError(f'Tipo MIME no permitido: {v}')
        return v


class DocumentMetadata(BaseModel):
    """Esquema para metadatos del documento"""
    tags: List[str] = Field(default_factory=list, description="Tags para clasificación")
    category: Optional[str] = Field(None, max_length=100, description="Categoría")
    priority: DocumentPriority = Field(default=DocumentPriority.NORMAL, description="Prioridad")
    
    # Agrupación y secuencia
    group_id: Optional[str] = Field(None, max_length=50, description="ID de grupo")
    sequence_number: int = Field(default=1, ge=1, description="Número en secuencia")
    
    # Configuración de acceso
    is_confidential: bool = Field(default=False, description="Documento confidencial")
    access_level: AccessLevel = Field(default=AccessLevel.NORMAL, description="Nivel de acceso")
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validar tags"""
        if v:
            # Limpiar y normalizar tags
            clean_tags = []
            for tag in v:
                if isinstance(tag, str) and tag.strip():
                    clean_tag = tag.strip().lower()
                    if len(clean_tag) <= 50 and clean_tag not in clean_tags:
                        clean_tags.append(clean_tag)
            return clean_tags[:10]  # Máximo 10 tags
        return []


# === ESQUEMAS PARA CREACIÓN ===

class DocumentCreate(DocumentBase):
    """Esquema para crear documento"""
    # Información del archivo (requerida)
    file_info: DocumentFileInfo = Field(..., description="Información del archivo")
    
    # QR code (opcional, se puede extraer automáticamente)
    qr_code_id: Optional[str] = Field(None, description="ID del código QR asociado")
    
    # Metadatos opcionales
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata, description="Metadatos")
    
    @root_validator
    def validate_document_requirements(cls, values):
        """Validar que se cumplan los requisitos del tipo de documento"""
        # Esta validación se complementará con la lógica del tipo de documento
        # en el servicio correspondiente
        return values


class DocumentUpload(BaseModel):
    """Esquema para subida de archivo con datos mínimos"""
    document_type_id: int = Field(..., description="ID del tipo de documento")
    
    # Datos básicos que se pueden extraer automáticamente
    cedula: Optional[str] = Field(None, description="Cédula (si no se extrae del QR)")
    nombre_completo: Optional[str] = Field(None, description="Nombre (opcional)")
    
    # Metadatos básicos
    tags: List[str] = Field(default_factory=list, description="Tags iniciales")
    is_confidential: bool = Field(default=False, description="Marcar como confidencial")
    
    # El archivo se maneja por separado en multipart/form-data


class DocumentBatchUpload(BaseModel):
    """Esquema para subida en lote"""
    document_type_id: int = Field(..., description="ID del tipo de documento")
    
    # Configuración del lote
    auto_extract_qr: bool = Field(default=True, description="Extraer QR automáticamente")
    auto_categorize: bool = Field(default=True, description="Categorizar automáticamente")
    
    # Metadatos comunes para el lote
    common_tags: List[str] = Field(default_factory=list, description="Tags comunes")
    batch_id: Optional[str] = Field(None, description="ID del lote")


# === ESQUEMAS PARA ACTUALIZACIÓN ===

class DocumentUpdate(BaseModel):
    """Esquema para actualizar documento"""
    # Información de la persona (actualizable)
    person_info: Optional[DocumentPersonInfo] = Field(None, description="Información de la persona")
    
    # Metadatos actualizables
    metadata: Optional[DocumentMetadata] = Field(None, description="Metadatos")
    
    # Archivos adicionales
    additional_files: Optional[List[Dict[str, Any]]] = Field(None, description="Archivos adicionales")


class DocumentAdminUpdate(DocumentUpdate):
    """Esquema para actualización por administrador"""
    status: Optional[DocumentStatus] = Field(None, description="Estado del documento")
    approval_status: Optional[ApprovalStatus] = Field(None, description="Estado de aprobación")
    approval_notes: Optional[str] = Field(None, max_length=1000, description="Notas de aprobación")
    
    # Campos técnicos
    qr_code_id: Optional[str] = Field(None, description="Asociar/desasociar QR")
    file_path: Optional[str] = Field(None, description="Actualizar ruta de archivo")
    onedrive_url: Optional[str] = Field(None, description="URL de OneDrive")


# === ESQUEMAS DE RESPUESTA ===

class DocumentFileResponse(BaseModel):
    """Esquema para información de archivo en respuestas"""
    name: str = Field(description="Nombre del archivo")
    size: Optional[int] = Field(None, description="Tamaño en bytes")
    size_mb: Optional[float] = Field(None, description="Tamaño en MB")
    mime_type: Optional[str] = Field(None, description="Tipo MIME")
    extension: Optional[str] = Field(None, description="Extensión del archivo")
    
    # Información de tipo
    is_image: bool = Field(description="Es una imagen")
    is_pdf: bool = Field(description="Es un PDF")
    is_word: bool = Field(description="Es un documento Word")
    
    # URLs de acceso (solo para usuarios autorizados)
    download_url: Optional[str] = Field(None, description="URL de descarga")
    preview_url: Optional[str] = Field(None, description="URL de vista previa")


class DocumentTypeInfo(BaseModel):
    """Esquema para información del tipo de documento"""
    id: int = Field(description="ID del tipo")
    code: str = Field(description="Código del tipo")
    name: str = Field(description="Nombre del tipo")
    color: str = Field(description="Color para UI")
    icon: str = Field(description="Icono para UI")


class DocumentQRInfo(BaseModel):
    """Esquema para información del QR"""
    has_qr: bool = Field(description="Tiene código QR asociado")
    qr_code_id: Optional[str] = Field(None, description="ID del código QR")
    qr_extraction_success: bool = Field(description="Extracción de QR exitosa")
    qr_extraction_error: Optional[str] = Field(None, description="Error de extracción")


class DocumentUsageInfo(BaseModel):
    """Esquema para información de uso"""
    view_count: int = Field(default=0, description="Número de visualizaciones")
    last_viewed_at: Optional[datetime] = Field(None, description="Última visualización")
    last_viewed_by: Optional[int] = Field(None, description="Último usuario que lo vio")


class DocumentAuditInfo(BaseModel):
    """Esquema para información de auditoría"""
    version: int = Field(description="Versión actual")
    uploaded_by: int = Field(description="Usuario que subió")
    created_at: datetime = Field(description="Fecha de creación")
    updated_at: datetime = Field(description="Fecha de actualización")
    
    # Información de aprobación
    approval_status: ApprovalStatus = Field(description="Estado de aprobación")
    approved_by: Optional[int] = Field(None, description="Usuario que aprobó")
    approved_at: Optional[datetime] = Field(None, description="Fecha de aprobación")
    
    # Retención
    retention_date: Optional[datetime] = Field(None, description="Fecha de retención")
    is_permanent: bool = Field(description="Retención permanente")


class Document(DocumentBase):
    """Esquema completo de documento para respuestas"""
    id: int = Field(description="ID único del documento")
    
    # Información del tipo
    document_type: DocumentTypeInfo = Field(description="Información del tipo")
    
    # Información del archivo
    file_info: DocumentFileResponse = Field(description="Información del archivo")
    
    # Información de la persona
    person_info: DocumentPersonInfo = Field(description="Información de la persona")
    
    # Metadatos
    metadata: DocumentMetadata = Field(description="Metadatos del documento")
    
    # Estado
    status: DocumentStatus = Field(description="Estado del documento")
    
    # Información del QR
    qr_info: DocumentQRInfo = Field(description="Información del QR")
    
    # Uso y auditoría
    usage_info: DocumentUsageInfo = Field(description="Información de uso")
    audit_info: DocumentAuditInfo = Field(description="Información de auditoría")
    
    class Config:
        from_attributes = True


class DocumentSummary(BaseModel):
    """Esquema resumido para listas"""
    id: int
    document_type: DocumentTypeInfo
    file_name: str
    file_size_mb: Optional[float] = None
    cedula: Optional[str] = None
    nombre_completo: Optional[str] = None
    status: DocumentStatus
    approval_status: ApprovalStatus
    has_qr: bool
    created_at: datetime
    uploaded_by: int
    
    class Config:
        from_attributes = True


class DocumentDetailed(Document):
    """Esquema detallado para administradores"""
    # Información técnica adicional
    file_path: str = Field(description="Ruta del archivo")
    file_hash: Optional[str] = Field(None, description="Hash del archivo")
    onedrive_url: Optional[str] = Field(None, description="URL de OneDrive")
    onedrive_file_id: Optional[str] = Field(None, description="ID en OneDrive")
    
    # Archivos adicionales
    additional_files: List[Dict[str, Any]] = Field(description="Archivos adicionales")
    
    # Log de cambios
    change_log: List[Dict[str, Any]] = Field(description="Historial de cambios")
    
    # Datos de procesamiento
    qr_extraction_data: Optional[Dict[str, Any]] = Field(None, description="Datos del QR extraído")
    ocr_text: Optional[str] = Field(None, description="Texto extraído por OCR")
    
    class Config:
        from_attributes = True


# === ESQUEMAS PARA BÚSQUEDA Y FILTROS ===

class DocumentFilter(BaseModel):
    """Esquema para filtros de búsqueda"""
    # Búsqueda general
    search: Optional[str] = Field(None, description="Búsqueda en texto completo")
    
    # Filtros específicos
    document_type_id: Optional[int] = Field(None, description="Filtrar por tipo")
    cedula: Optional[str] = Field(None, description="Filtrar por cédula")
    nombre_completo: Optional[str] = Field(None, description="Filtrar por nombre")
    status: Optional[DocumentStatus] = Field(None, description="Filtrar por estado")
    approval_status: Optional[ApprovalStatus] = Field(None, description="Filtrar por aprobación")
    
    # Filtros de fecha
    created_after: Optional[datetime] = Field(None, description="Creados después de")
    created_before: Optional[datetime] = Field(None, description="Creados antes de")
    updated_after: Optional[datetime] = Field(None, description="Actualizados después de")
    updated_before: Optional[datetime] = Field(None, description="Actualizados antes de")
    
    # Filtros de metadatos
    tags: Optional[List[str]] = Field(None, description="Filtrar por tags")
    category: Optional[str] = Field(None, description="Filtrar por categoría")
    priority: Optional[DocumentPriority] = Field(None, description="Filtrar por prioridad")
    is_confidential: Optional[bool] = Field(None, description="Filtrar por confidencial")
    access_level: Optional[AccessLevel] = Field(None, description="Filtrar por nivel de acceso")
    
    # Filtros de archivo
    file_type: Optional[str] = Field(None, description="Filtrar por tipo de archivo")
    min_file_size: Optional[int] = Field(None, description="Tamaño mínimo en bytes")
    max_file_size: Optional[int] = Field(None, description="Tamaño máximo en bytes")
    
    # Filtros de QR
    has_qr: Optional[bool] = Field(None, description="Filtrar por QR")
    qr_extraction_success: Optional[bool] = Field(None, description="Filtrar por extracción QR exitosa")
    
    # Filtros de usuario
    uploaded_by: Optional[int] = Field(None, description="Filtrar por usuario que subió")
    approved_by: Optional[int] = Field(None, description="Filtrar por usuario que aprobó")
    
    # Paginación
    page: int = Field(default=1, ge=1, description="Número de página")
    page_size: int = Field(default=20, ge=1, le=100, description="Tamaño de página")
    
    # Ordenamiento
    sort_by: str = Field(default="created_at", description="Campo para ordenar")
    sort_order: str = Field(default="desc", description="Orden: asc o desc")
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        """Validar campo de ordenamiento"""
        valid_fields = [
            'created_at', 'updated_at', 'file_name', 'file_size', 'cedula',
            'nombre_completo', 'status', 'approval_status', 'view_count'
        ]
        if v not in valid_fields:
            raise ValueError(f'sort_by debe ser uno de: {", ".join(valid_fields)}')
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        """Validar orden"""
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('sort_order debe ser "asc" o "desc"')
        return v.lower()


class DocumentListResponse(BaseModel):
    """Esquema para respuesta de lista"""
    documents: List[DocumentSummary] = Field(description="Lista de documentos")
    total: int = Field(description="Total de documentos")
    page: int = Field(description="Página actual")
    page_size: int = Field(description="Tamaño de página")
    total_pages: int = Field(description="Total de páginas")
    
    # Estadísticas de la búsqueda
    filter_stats: Dict[str, Any] = Field(description="Estadísticas por filtros")


# === ESQUEMAS PARA OPERACIONES ESPECIALES ===

class DocumentApproval(BaseModel):
    """Esquema para aprobación de documento"""
    approval_status: ApprovalStatus = Field(..., description="Nuevo estado de aprobación")
    notes: Optional[str] = Field(None, max_length=1000, description="Notas de aprobación/rechazo")


class DocumentBulkAction(BaseModel):
    """Esquema para acciones en lote"""
    document_ids: List[int] = Field(..., min_items=1, max_items=100, description="IDs de documentos")
    action: str = Field(..., description="Acción a realizar")
    reason: Optional[str] = Field(None, description="Razón de la acción")
    
    @validator('action')
    def validate_action(cls, v):
        """Validar acción"""
        valid_actions = [
            'approve', 'reject', 'archive', 'restore', 'delete',
            'add_tags', 'remove_tags', 'change_category', 'change_access_level'
        ]
        if v not in valid_actions:
            raise ValueError(f'Acción debe ser una de: {", ".join(valid_actions)}')
        return v


class DocumentBulkActionResponse(BaseModel):
    """Esquema para respuesta de acción en lote"""
    success_count: int = Field(description="Documentos procesados exitosamente")
    error_count: int = Field(description="Documentos con errores")
    errors: List[Dict[str, Any]] = Field(description="Detalles de errores")
    results: List[Dict[str, Any]] = Field(description="Resultados detallados")


class DocumentExport(BaseModel):
    """Esquema para exportación de documentos"""
    id: int
    document_type_code: str
    file_name: str
    file_size_mb: Optional[float] = None
    cedula: Optional[str] = None
    nombre_completo: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    status: str
    approval_status: str
    has_qr: bool
    tags: str  # Tags como string separado por comas
    created_at: datetime
    uploaded_by: int
    
    class Config:
        from_attributes = True


# === ESQUEMAS PARA ANÁLISIS ===

class DocumentAnalytics(BaseModel):
    """Esquema para análisis de documentos"""
    total_documents: int = Field(description="Total de documentos")
    by_status: Dict[str, int] = Field(description="Documentos por estado")
    by_type: List[Dict[str, Any]] = Field(description="Documentos por tipo")
    by_approval_status: Dict[str, int] = Field(description="Documentos por estado de aprobación")
    
    # Análisis temporal
    uploaded_last_30_days: int = Field(description="Subidos últimos 30 días")
    approved_last_30_days: int = Field(description="Aprobados últimos 30 días")
    
    # Análisis de archivos
    total_size_gb: float = Field(description="Tamaño total en GB")
    avg_file_size_mb: float = Field(description="Tamaño promedio en MB")
    file_types_distribution: Dict[str, int] = Field(description="Distribución por tipo de archivo")
    
    # Análisis de QR
    documents_with_qr: int = Field(description="Documentos con QR")
    qr_extraction_success_rate: float = Field(description="Tasa de éxito extracción QR")


class DocumentProcessingStatus(BaseModel):
    """Esquema para estado de procesamiento"""
    document_id: int = Field(description="ID del documento")
    status: str = Field(description="Estado del procesamiento")
    progress: int = Field(ge=0, le=100, description="Progreso en porcentaje")
    message: Optional[str] = Field(None, description="Mensaje de estado")
    errors: List[str] = Field(default_factory=list, description="Errores encontrados")
    
    # Etapas del procesamiento
    stages: Dict[str, bool] = Field(description="Etapas completadas")
    current_stage: Optional[str] = Field(None, description="Etapa actual")