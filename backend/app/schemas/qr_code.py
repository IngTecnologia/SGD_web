"""
Esquemas Pydantic para Códigos QR
Validación y serialización de códigos QR y su ciclo de vida
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
from enum import Enum


# === ENUMS ===

class QRStatus(str, Enum):
    """Estados posibles del código QR"""
    AVAILABLE = "available"
    USED = "used"
    EXPIRED = "expired"
    REVOKED = "revoked"


class QRErrorCorrectionLevel(str, Enum):
    """Niveles de corrección de errores para QR"""
    L = "L"  # ~7% de corrección
    M = "M"  # ~15% de corrección
    Q = "Q"  # ~25% de corrección
    H = "H"  # ~30% de corrección


# === ESQUEMAS BASE ===

class QRCodeBase(BaseModel):
    """Esquema base para código QR"""
    qr_id: str = Field(..., min_length=10, description="ID único del código QR")
    document_type_id: int = Field(..., description="ID del tipo de documento")
    
    @validator('qr_id')
    def validate_qr_id(cls, v):
        """Validar formato del QR ID"""
        import re
        # Validar que sea un UUID válido o formato personalizado
        uuid_pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
        if not re.match(uuid_pattern, v):
            # Si no es UUID, validar formato personalizado
            if len(v) < 10 or not v.replace('-', '').replace('_', '').isalnum():
                raise ValueError('QR ID debe ser un UUID válido o alfanumérico de al menos 10 caracteres')
        return v


class QRGenerationConfig(BaseModel):
    """Esquema para configuración de generación de QR"""
    version: int = Field(default=1, ge=1, le=40, description="Versión del QR (1-40)")
    error_correction: QRErrorCorrectionLevel = Field(
        default=QRErrorCorrectionLevel.L, 
        description="Nivel de corrección de errores"
    )
    box_size: int = Field(default=10, ge=1, le=50, description="Tamaño de cada caja en píxeles")
    border: int = Field(default=4, ge=0, le=20, description="Tamaño del borde")
    
    # Colores personalizados
    fill_color: str = Field(default="black", description="Color de relleno")
    back_color: str = Field(default="white", description="Color de fondo")
    
    @validator('fill_color', 'back_color')
    def validate_colors(cls, v):
        """Validar colores"""
        import re
        # Permitir nombres de color estándar o hex
        if v.lower() in ['black', 'white', 'red', 'blue', 'green', 'yellow', 'orange', 'purple']:
            return v.lower()
        elif re.match(r'^#[0-9A-Fa-f]{6}$', v):
            return v.upper()
        else:
            raise ValueError('Color debe ser un nombre estándar o formato hex (#RRGGBB)')


class QRData(BaseModel):
    """Esquema para datos adicionales del QR"""
    version: int = Field(default=1, description="Versión del formato de datos")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos adicionales")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Campos personalizados")
    
    @validator('metadata', 'custom_fields')
    def validate_json_serializable(cls, v):
        """Validar que los datos sean serializables a JSON"""
        import json
        try:
            json.dumps(v)
            return v
        except (TypeError, ValueError):
            raise ValueError('Los datos deben ser serializables a JSON')


# === ESQUEMAS PARA CREACIÓN ===

class QRCodeCreate(QRCodeBase):
    """Esquema para crear código QR"""
    qr_data: Optional[QRData] = Field(None, description="Datos adicionales del QR")
    generation_config: Optional[QRGenerationConfig] = Field(
        default_factory=QRGenerationConfig,
        description="Configuración de generación"
    )
    expires_at: Optional[datetime] = Field(None, description="Fecha de expiración")
    source_file_name: Optional[str] = Field(None, description="Nombre del archivo fuente")
    
    @validator('expires_at')
    def validate_expiration(cls, v):
        """Validar fecha de expiración"""
        if v and v <= datetime.utcnow():
            raise ValueError('Fecha de expiración debe ser futura')
        return v


class QRCodeBatchCreate(BaseModel):
    """Esquema para crear múltiples códigos QR"""
    document_type_id: int = Field(..., description="ID del tipo de documento")
    quantity: int = Field(..., ge=1, le=1000, description="Cantidad de QRs a generar")
    
    # Configuración común
    generation_config: Optional[QRGenerationConfig] = Field(
        default_factory=QRGenerationConfig,
        description="Configuración de generación"
    )
    expires_in_days: Optional[int] = Field(
        None, 
        ge=1, 
        le=3650, 
        description="Días hasta expiración"
    )
    
    # Configuración de archivos
    generate_files: bool = Field(default=True, description="Generar archivos de imagen")
    file_format: str = Field(default="PNG", description="Formato de archivo")
    
    @validator('file_format')
    def validate_file_format(cls, v):
        """Validar formato de archivo"""
        valid_formats = ['PNG', 'JPEG', 'SVG', 'PDF']
        if v.upper() not in valid_formats:
            raise ValueError(f'Formato debe ser uno de: {", ".join(valid_formats)}')
        return v.upper()


# === ESQUEMAS PARA ACTUALIZACIÓN ===

class QRCodeUpdate(BaseModel):
    """Esquema para actualizar código QR"""
    qr_data: Optional[QRData] = Field(None, description="Datos adicionales del QR")
    expires_at: Optional[datetime] = Field(None, description="Nueva fecha de expiración")
    
    @validator('expires_at')
    def validate_expiration(cls, v):
        """Validar fecha de expiración"""
        if v and v <= datetime.utcnow():
            raise ValueError('Fecha de expiración debe ser futura')
        return v


class QRCodeRevoke(BaseModel):
    """Esquema para revocar código QR"""
    reason: str = Field(..., min_length=3, max_length=500, description="Razón de revocación")


class QRCodeUse(BaseModel):
    """Esquema para marcar QR como usado"""
    document_id: int = Field(..., description="ID del documento asociado")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Datos adicionales del uso")


# === ESQUEMAS DE RESPUESTA ===

class QRCodeUsageLog(BaseModel):
    """Esquema para entrada de log de uso"""
    timestamp: datetime = Field(description="Fecha y hora del evento")
    event: str = Field(description="Tipo de evento")
    details: Dict[str, Any] = Field(description="Detalles del evento")
    
    class Config:
        from_attributes = True


class QRCodeStats(BaseModel):
    """Esquema para estadísticas del QR"""
    usage_attempts: int = Field(default=0, description="Intentos de uso")
    days_since_creation: int = Field(description="Días desde creación")
    days_until_expiration: Optional[int] = Field(None, description="Días hasta expiración")


class QRCode(QRCodeBase):
    """Esquema completo de código QR para respuestas"""
    id: int = Field(description="ID único del registro")
    
    # Estado
    status: QRStatus = Field(description="Estado actual del QR")
    is_valid: bool = Field(description="QR válido para uso")
    is_used: bool = Field(description="QR ya utilizado")
    is_expired: bool = Field(description="QR expirado")
    is_revoked: bool = Field(description="QR revocado")
    
    # Datos y configuración
    qr_data: Optional[QRData] = Field(None, description="Datos del QR")
    generation_config: Optional[QRGenerationConfig] = Field(None, description="Configuración de generación")
    qr_version: int = Field(description="Versión del formato QR")
    
    # Asociaciones
    used_in_document_id: Optional[int] = Field(None, description="ID del documento asociado")
    generated_by: int = Field(description="Usuario que lo generó")
    
    # Archivos
    source_file_path: Optional[str] = Field(None, description="Ruta del archivo fuente")
    source_file_name: Optional[str] = Field(None, description="Nombre del archivo fuente")
    
    # Estadísticas y logs
    stats: QRCodeStats = Field(description="Estadísticas del QR")
    usage_log: List[QRCodeUsageLog] = Field(description="Log de uso")
    
    # Fechas
    created_at: datetime = Field(description="Fecha de creación")
    used_at: Optional[datetime] = Field(None, description="Fecha de uso")
    expires_at: Optional[datetime] = Field(None, description="Fecha de expiración")
    revoked_at: Optional[datetime] = Field(None, description="Fecha de revocación")
    
    # Información del tipo de documento
    document_type_code: Optional[str] = Field(None, description="Código del tipo de documento")
    
    class Config:
        from_attributes = True


class QRCodeSummary(BaseModel):
    """Esquema resumido para listas"""
    id: int
    qr_id: str
    document_type_id: int
    document_type_code: Optional[str] = None
    status: QRStatus
    is_valid: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    used_at: Optional[datetime] = None
    usage_attempts: int
    
    class Config:
        from_attributes = True


# === ESQUEMAS PARA VALIDACIÓN ===

class QRCodeValidation(BaseModel):
    """Esquema para validar código QR"""
    qr_id: str = Field(..., description="ID del código QR")
    document_type_id: int = Field(..., description="ID del tipo de documento")


class QRCodeValidationResponse(BaseModel):
    """Esquema para respuesta de validación"""
    is_valid: bool = Field(description="QR es válido")
    status: QRStatus = Field(description="Estado del QR")
    errors: List[str] = Field(default=[], description="Errores de validación")
    qr_info: Optional[QRCodeSummary] = Field(None, description="Información del QR si es válido")


# === ESQUEMAS PARA BÚSQUEDA Y FILTROS ===

class QRCodeFilter(BaseModel):
    """Esquema para filtros de búsqueda"""
    search: Optional[str] = Field(None, description="Búsqueda por QR ID")
    document_type_id: Optional[int] = Field(None, description="Filtrar por tipo de documento")
    status: Optional[QRStatus] = Field(None, description="Filtrar por estado")
    is_valid: Optional[bool] = Field(None, description="Filtrar por validez")
    generated_by: Optional[int] = Field(None, description="Filtrar por generador")
    
    # Filtros de fecha
    created_after: Optional[datetime] = Field(None, description="Creados después de")
    created_before: Optional[datetime] = Field(None, description="Creados antes de")
    expires_after: Optional[datetime] = Field(None, description="Expiran después de")
    expires_before: Optional[datetime] = Field(None, description="Expiran antes de")
    
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
            'qr_id', 'created_at', 'used_at', 'expires_at', 'status', 
            'usage_attempts', 'document_type_id'
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


class QRCodeListResponse(BaseModel):
    """Esquema para respuesta de lista"""
    qr_codes: List[QRCodeSummary] = Field(description="Lista de códigos QR")
    total: int = Field(description="Total de códigos")
    page: int = Field(description="Página actual")
    page_size: int = Field(description="Tamaño de página")
    total_pages: int = Field(description="Total de páginas")
    
    # Estadísticas de la búsqueda
    filter_stats: Dict[str, int] = Field(description="Estadísticas por estado")


# === ESQUEMAS PARA OPERACIONES EN LOTE ===

class QRCodeBulkAction(BaseModel):
    """Esquema para acciones en lote"""
    qr_ids: List[str] = Field(..., min_items=1, max_items=100, description="IDs de códigos QR")
    action: str = Field(..., description="Acción a realizar")
    reason: Optional[str] = Field(None, description="Razón de la acción")
    
    @validator('action')
    def validate_action(cls, v):
        """Validar acción"""
        valid_actions = ['revoke', 'extend_expiration', 'delete']
        if v not in valid_actions:
            raise ValueError(f'Acción debe ser una de: {", ".join(valid_actions)}')
        return v


class QRCodeBulkActionResponse(BaseModel):
    """Esquema para respuesta de acción en lote"""
    success_count: int = Field(description="QRs procesados exitosamente")
    error_count: int = Field(description="QRs con errores")
    errors: List[Dict[str, Any]] = Field(description="Detalles de errores")
    results: List[Dict[str, Any]] = Field(description="Resultados detallados")


# === ESQUEMAS PARA GENERACIÓN ===

class QRCodeGenerationRequest(BaseModel):
    """Esquema para solicitud de generación"""
    document_type_id: int = Field(..., description="ID del tipo de documento")
    quantity: int = Field(default=1, ge=1, le=100, description="Cantidad a generar")
    format: str = Field(default="image", description="Formato de salida")
    
    # Configuración opcional
    generation_config: Optional[QRGenerationConfig] = None
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)
    
    @validator('format')
    def validate_format(cls, v):
        """Validar formato de salida"""
        valid_formats = ['image', 'pdf', 'json', 'zip']
        if v.lower() not in valid_formats:
            raise ValueError(f'Formato debe ser uno de: {", ".join(valid_formats)}')
        return v.lower()


class QRCodeGenerationResponse(BaseModel):
    """Esquema para respuesta de generación"""
    generated_count: int = Field(description="Códigos generados")
    qr_codes: List[QRCodeSummary] = Field(description="Códigos QR generados")
    file_urls: List[str] = Field(description="URLs de archivos generados")
    batch_id: str = Field(description="ID del lote de generación")


# === ESQUEMAS PARA ANÁLISIS ===

class QRCodeAnalytics(BaseModel):
    """Esquema para análisis de códigos QR"""
    total_generated: int = Field(description="Total generados")
    total_used: int = Field(description="Total utilizados")
    total_expired: int = Field(description="Total expirados")
    total_revoked: int = Field(description="Total revocados")
    usage_rate: float = Field(description="Tasa de uso (%)")
    
    # Análisis por período
    generated_last_30_days: int = Field(description="Generados últimos 30 días")
    used_last_30_days: int = Field(description="Usados últimos 30 días")
    
    # Análisis por tipo de documento
    by_document_type: List[Dict[str, Any]] = Field(description="Estadísticas por tipo")


class QRCodeExport(BaseModel):
    """Esquema para exportación de códigos QR"""
    id: int
    qr_id: str
    document_type_code: str
    status: str
    is_valid: bool
    created_at: datetime
    used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    usage_attempts: int
    generated_by: int
    
    class Config:
        from_attributes = True