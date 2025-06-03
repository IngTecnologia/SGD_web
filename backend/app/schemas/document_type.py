"""
Esquemas Pydantic para Tipos de Documento
Validación y serialización de tipos de documento configurables
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# === ESQUEMAS BASE ===

class DocumentTypeBase(BaseModel):
    """Esquema base para tipo de documento"""
    code: str = Field(..., min_length=2, max_length=20, description="Código único del tipo")
    name: str = Field(..., min_length=3, max_length=100, description="Nombre descriptivo")
    description: Optional[str] = Field(None, max_length=1000, description="Descripción detallada")
    
    @validator('code')
    def validate_code(cls, v):
        """Validar formato del código"""
        import re
        # Permitir solo letras, números, guiones y guiones bajos
        if not re.match(r'^[A-Za-z0-9_-]+$', v):
            raise ValueError('Código solo puede contener letras, números, guiones y guiones bajos')
        return v.upper()  # Convertir a mayúsculas
    
    @validator('name')
    def validate_name(cls, v):
        """Validar nombre"""
        if v:
            v = v.strip()
            if len(v) < 3:
                raise ValueError('Nombre debe tener al menos 3 caracteres')
        return v


class DocumentTypeRequirements(BaseModel):
    """Esquema para configuración de requisitos"""
    requires_qr: bool = Field(default=False, description="Requiere código QR")
    requires_cedula: bool = Field(default=True, description="Requiere cédula/ID")
    requires_nombre: bool = Field(default=False, description="Requiere nombre completo")
    requires_telefono: bool = Field(default=False, description="Requiere teléfono")
    requires_email: bool = Field(default=False, description="Requiere email")
    requires_direccion: bool = Field(default=False, description="Requiere dirección")


class DocumentTypeFileConfig(BaseModel):
    """Esquema para configuración de archivos"""
    allowed_file_types: List[str] = Field(
        default=["application/pdf", "image/jpeg", "image/png"],
        description="Tipos MIME permitidos"
    )
    max_file_size_mb: int = Field(
        default=50, 
        ge=1, 
        le=500, 
        description="Tamaño máximo en MB"
    )
    allow_multiple_files: bool = Field(
        default=False, 
        description="Permitir múltiples archivos"
    )
    
    @validator('allowed_file_types')
    def validate_file_types(cls, v):
        """Validar tipos MIME"""
        valid_types = [
            "application/pdf",
            "image/jpeg", "image/jpg", "image/png", "image/gif",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
            "text/plain"
        ]
        
        for mime_type in v:
            if mime_type not in valid_types:
                raise ValueError(f'Tipo MIME no válido: {mime_type}')
        
        return v


class DocumentTypeQRConfig(BaseModel):
    """Esquema para configuración de QR en plantillas"""
    qr_table_number: int = Field(default=1, ge=1, description="Número de tabla para QR")
    qr_row: int = Field(default=5, ge=0, description="Fila para el QR")
    qr_column: int = Field(default=0, ge=0, description="Columna para el QR")
    qr_width: int = Field(default=1, ge=1, le=10, description="Ancho del QR en pulgadas")
    qr_height: int = Field(default=1, ge=1, le=10, description="Alto del QR en pulgadas")


class DocumentTypeUIConfig(BaseModel):
    """Esquema para configuración de interfaz"""
    color: str = Field(default="#007bff", description="Color en formato hex")
    icon: str = Field(default="file", max_length=50, description="Icono para mostrar")
    sort_order: int = Field(default=0, description="Orden de aparición")
    
    @validator('color')
    def validate_color(cls, v):
        """Validar formato hexadecimal"""
        import re
        if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError('Color debe estar en formato hexadecimal (#RRGGBB)')
        return v.upper()
    
    @validator('icon')
    def validate_icon(cls, v):
        """Validar nombre del icono"""
        # Lista de iconos válidos (expandir según librería de iconos usada)
        valid_icons = [
            'file', 'file-text', 'image', 'pdf', 'word', 'excel',
            'document', 'folder', 'archive', 'certificate', 'contract',
            'invoice', 'receipt', 'id-card', 'passport', 'license'
        ]
        
        if v not in valid_icons:
            # Solo advertencia, no error para permitir flexibilidad
            pass
        
        return v


class DocumentTypeWorkflow(BaseModel):
    """Esquema para configuración de workflow"""
    requires_approval: bool = Field(default=False, description="Requiere aprobación")
    auto_notify_email: bool = Field(default=False, description="Notificación automática por email")
    notification_emails: List[str] = Field(default=[], description="Emails para notificar")
    retention_days: Optional[int] = Field(None, ge=1, description="Días de retención")
    auto_archive: bool = Field(default=False, description="Archivo automático")
    
    @validator('notification_emails')
    def validate_emails(cls, v):
        """Validar emails de notificación"""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        for email in v:
            if not re.match(email_pattern, email):
                raise ValueError(f'Email no válido: {email}')
        
        return [email.lower() for email in v]


# === ESQUEMAS PARA CREACIÓN Y ACTUALIZACIÓN ===

class DocumentTypeCreate(DocumentTypeBase):
    """Esquema para crear tipo de documento"""
    # Configuraciones
    requirements: DocumentTypeRequirements = Field(default_factory=DocumentTypeRequirements)
    file_config: DocumentTypeFileConfig = Field(default_factory=DocumentTypeFileConfig)
    ui_config: DocumentTypeUIConfig = Field(default_factory=DocumentTypeUIConfig)
    workflow: DocumentTypeWorkflow = Field(default_factory=DocumentTypeWorkflow)
    
    # Configuración de plantilla
    template_path: Optional[str] = Field(None, max_length=255, description="Ruta a plantilla Word")
    qr_config: Optional[DocumentTypeQRConfig] = Field(None, description="Configuración de QR")
    
    @validator('qr_config')
    def validate_qr_config(cls, v, values):
        """Validar configuración de QR si se requiere QR"""
        requirements = values.get('requirements')
        if requirements and requirements.requires_qr and not v:
            raise ValueError('Configuración de QR es requerida cuando requires_qr es True')
        return v


class DocumentTypeUpdate(BaseModel):
    """Esquema para actualizar tipo de documento"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    
    # Configuraciones opcionales
    requirements: Optional[DocumentTypeRequirements] = None
    file_config: Optional[DocumentTypeFileConfig] = None
    ui_config: Optional[DocumentTypeUIConfig] = None
    workflow: Optional[DocumentTypeWorkflow] = None
    
    # Configuración de plantilla
    template_path: Optional[str] = Field(None, max_length=255)
    qr_config: Optional[DocumentTypeQRConfig] = None
    
    # Estado
    is_active: Optional[bool] = None


class DocumentTypeAdminUpdate(DocumentTypeUpdate):
    """Esquema para actualización por administrador"""
    code: Optional[str] = Field(None, min_length=2, max_length=20)
    is_system_type: Optional[bool] = Field(None, description="Tipo de sistema (no editable)")
    
    @validator('code')
    def validate_code(cls, v):
        """Validar formato del código"""
        if v:
            import re
            if not re.match(r'^[A-Za-z0-9_-]+$', v):
                raise ValueError('Código solo puede contener letras, números, guiones y guiones bajos')
            return v.upper()
        return v


# === ESQUEMAS DE RESPUESTA ===

class DocumentTypeStats(BaseModel):
    """Esquema para estadísticas del tipo de documento"""
    documents_count: int = Field(default=0, description="Documentos registrados")
    generated_count: int = Field(default=0, description="Documentos generados")
    
    # Estadísticas adicionales calculadas
    documents_last_month: Optional[int] = Field(None, description="Documentos del último mes")
    avg_documents_per_day: Optional[float] = Field(None, description="Promedio de documentos por día")


class DocumentType(DocumentTypeBase):
    """Esquema completo de tipo de documento para respuestas"""
    id: int = Field(description="ID único del tipo")
    
    # Configuraciones
    requirements: DocumentTypeRequirements = Field(description="Configuración de requisitos")
    file_config: DocumentTypeFileConfig = Field(description="Configuración de archivos")
    ui_config: DocumentTypeUIConfig = Field(description="Configuración de UI")
    workflow: DocumentTypeWorkflow = Field(description="Configuración de workflow")
    
    # Configuración de plantilla
    template_path: Optional[str] = Field(None, description="Ruta a plantilla")
    qr_config: Optional[DocumentTypeQRConfig] = Field(None, description="Configuración de QR")
    
    # Estado y flags
    is_active: bool = Field(description="Tipo activo")
    is_system_type: bool = Field(description="Tipo de sistema")
    
    # Capacidades calculadas
    has_template: bool = Field(description="Tiene plantilla configurada")
    can_generate: bool = Field(description="Puede generar documentos")
    required_fields: List[str] = Field(description="Campos requeridos")
    
    # Estadísticas
    stats: DocumentTypeStats = Field(description="Estadísticas del tipo")
    
    # Auditoría
    created_by: int = Field(description="Usuario que creó el tipo")
    created_at: datetime = Field(description="Fecha de creación")
    updated_at: datetime = Field(description="Fecha de actualización")
    
    class Config:
        from_attributes = True


class DocumentTypeSummary(BaseModel):
    """Esquema resumido para listas"""
    id: int
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool
    requires_qr: bool
    can_generate: bool
    documents_count: int
    color: str
    icon: str
    
    class Config:
        from_attributes = True


# === ESQUEMAS PARA VALIDACIÓN ===

class DocumentTypeValidation(BaseModel):
    """Esquema para validar datos de documento según tipo"""
    document_type_id: int = Field(description="ID del tipo de documento")
    data: Dict[str, Any] = Field(description="Datos del documento a validar")


class DocumentTypeValidationResponse(BaseModel):
    """Esquema para respuesta de validación"""
    is_valid: bool = Field(description="Datos son válidos")
    errors: List[str] = Field(default=[], description="Lista de errores")
    warnings: List[str] = Field(default=[], description="Lista de advertencias")
    required_fields: List[str] = Field(description="Campos requeridos")
    missing_fields: List[str] = Field(description="Campos faltantes")


# === ESQUEMAS PARA LISTADOS Y FILTROS ===

class DocumentTypeFilter(BaseModel):
    """Esquema para filtros de búsqueda"""
    search: Optional[str] = Field(None, description="Búsqueda por código o nombre")
    is_active: Optional[bool] = Field(None, description="Filtrar por activo")
    requires_qr: Optional[bool] = Field(None, description="Filtrar por requisito de QR")
    can_generate: Optional[bool] = Field(None, description="Filtrar por capacidad de generación")
    created_by: Optional[int] = Field(None, description="Filtrar por creador")
    
    # Paginación
    page: int = Field(default=1, ge=1, description="Número de página")
    page_size: int = Field(default=20, ge=1, le=100, description="Tamaño de página")
    
    # Ordenamiento
    sort_by: str = Field(default="name", description="Campo para ordenar")
    sort_order: str = Field(default="asc", description="Orden: asc o desc")
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        """Validar campo de ordenamiento"""
        valid_fields = ['code', 'name', 'created_at', 'updated_at', 'documents_count', 'sort_order']
        if v not in valid_fields:
            raise ValueError(f'sort_by debe ser uno de: {", ".join(valid_fields)}')
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        """Validar orden"""
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('sort_order debe ser "asc" o "desc"')
        return v.lower()


class DocumentTypeListResponse(BaseModel):
    """Esquema para respuesta de lista"""
    document_types: List[DocumentTypeSummary] = Field(description="Lista de tipos")
    total: int = Field(description="Total de tipos")
    page: int = Field(description="Página actual")
    page_size: int = Field(description="Tamaño de página")
    total_pages: int = Field(description="Total de páginas")


# === ESQUEMAS PARA OPERACIONES ESPECIALES ===

class DocumentTypeClone(BaseModel):
    """Esquema para clonar tipo de documento"""
    source_id: int = Field(description="ID del tipo a clonar")
    new_code: str = Field(..., min_length=2, max_length=20, description="Nuevo código")
    new_name: str = Field(..., min_length=3, max_length=100, description="Nuevo nombre")
    copy_template: bool = Field(default=False, description="Copiar plantilla también")
    
    @validator('new_code')
    def validate_new_code(cls, v):
        """Validar nuevo código"""
        import re
        if not re.match(r'^[A-Za-z0-9_-]+$', v):
            raise ValueError('Código solo puede contener letras, números, guiones y guiones bajos')
        return v.upper()


class DocumentTypeBulkAction(BaseModel):
    """Esquema para acciones en lote"""
    type_ids: List[int] = Field(..., description="IDs de tipos")
    action: str = Field(..., description="Acción a realizar")
    
    @validator('action')
    def validate_action(cls, v):
        """Validar acción"""
        valid_actions = ['activate', 'deactivate', 'delete']
        if v not in valid_actions:
            raise ValueError(f'Acción debe ser una de: {", ".join(valid_actions)}')
        return v


class DocumentTypeBulkActionResponse(BaseModel):
    """Esquema para respuesta de acción en lote"""
    success_count: int = Field(description="Tipos procesados exitosamente")
    error_count: int = Field(description="Tipos con errores")
    errors: List[Dict[str, Any]] = Field(description="Detalles de errores")


# === ESQUEMAS PARA PLANTILLAS ===

class DocumentTypeTemplate(BaseModel):
    """Esquema para información de plantilla"""
    has_template: bool = Field(description="Tiene plantilla")
    template_path: Optional[str] = Field(None, description="Ruta de plantilla")
    template_name: Optional[str] = Field(None, description="Nombre de plantilla")
    template_size: Optional[int] = Field(None, description="Tamaño de plantilla")
    last_modified: Optional[datetime] = Field(None, description="Última modificación")


class DocumentTypeTemplateUpload(BaseModel):
    """Esquema para subida de plantilla"""
    document_type_id: int = Field(description="ID del tipo de documento")
    # El archivo se maneja por separado en el endpoint multipart/form-data


# === ESQUEMAS PARA EXPORTACIÓN ===

class DocumentTypeExport(BaseModel):
    """Esquema para exportación de tipos"""
    id: int
    code: str
    name: str
    description: Optional[str] = None
    requires_qr: bool
    requires_cedula: bool
    requires_nombre: bool
    requires_telefono: bool
    requires_email: bool
    requires_direccion: bool
    max_file_size_mb: int
    is_active: bool
    documents_count: int
    generated_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True