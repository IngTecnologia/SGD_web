"""
Esquemas Pydantic para SGD Web

Este módulo centraliza todos los esquemas de validación y serialización
para facilitar las importaciones y mantener la consistencia.
"""

# === IMPORTACIONES DE USER ===
from .user import (
    # Esquemas base
    UserBase,
    UserCreate,
    UserUpdate,
    UserAdminUpdate,
    
    # Esquemas de respuesta
    User,
    UserSummary,
    UserDetailed,
    UserPermissions,
    UserStats,
    
    # Esquemas de autenticación
    UserLogin,
    UserLoginResponse,
    UserMicrosoftData,
    
    # Esquemas de filtros y listas
    UserFilter,
    UserListResponse,
    
    # Esquemas para operaciones
    UserBulkAction,
    UserBulkActionResponse,
    UserActivityLog,
    UserExport,
    
    # Enums
    UserRole,
    UserStatus,
)

# === IMPORTACIONES DE DOCUMENT_TYPE ===
from .document_type import (
    # Esquemas base
    DocumentTypeBase,
    DocumentTypeCreate,
    DocumentTypeUpdate,
    DocumentTypeAdminUpdate,
    
    # Esquemas de configuración
    DocumentTypeRequirements,
    DocumentTypeFileConfig,
    DocumentTypeQRConfig,
    DocumentTypeUIConfig,
    DocumentTypeWorkflow,
    
    # Esquemas de respuesta
    DocumentType,
    DocumentTypeSummary,
    DocumentTypeStats,
    
    # Esquemas de validación
    DocumentTypeValidation,
    DocumentTypeValidationResponse,
    
    # Esquemas de filtros y listas
    DocumentTypeFilter,
    DocumentTypeListResponse,
    
    # Esquemas para operaciones especiales
    DocumentTypeClone,
    DocumentTypeBulkAction,
    DocumentTypeBulkActionResponse,
    DocumentTypeTemplate,
    DocumentTypeTemplateUpload,
    DocumentTypeExport,
)

# === IMPORTACIONES DE QR_CODE ===
from .qr_code import (
    # Esquemas base
    QRCodeBase,
    QRCodeCreate,
    QRCodeBatchCreate,
    QRCodeUpdate,
    QRCodeRevoke,
    QRCodeUse,
    
    # Esquemas de configuración
    QRGenerationConfig,
    QRData,
    
    # Esquemas de respuesta
    QRCode,
    QRCodeSummary,
    QRCodeStats,
    QRCodeUsageLog,
    
    # Esquemas de validación
    QRCodeValidation,
    QRCodeValidationResponse,
    
    # Esquemas de filtros y listas
    QRCodeFilter,
    QRCodeListResponse,
    
    # Esquemas para operaciones
    QRCodeBulkAction,
    QRCodeBulkActionResponse,
    QRCodeGenerationRequest,
    QRCodeGenerationResponse,
    QRCodeAnalytics,
    QRCodeExport,
    
    # Enums
    QRStatus,
    QRErrorCorrectionLevel,
)

# === IMPORTACIONES DE DOCUMENT ===
from .document import (
    # Esquemas base
    DocumentBase,
    DocumentCreate,
    DocumentUpload,
    DocumentBatchUpload,
    DocumentUpdate,
    DocumentAdminUpdate,
    
    # Esquemas de información
    DocumentPersonInfo,
    DocumentFileInfo,
    DocumentMetadata,
    
    # Esquemas de respuesta
    Document,
    DocumentSummary,
    DocumentDetailed,
    DocumentFileResponse,
    DocumentTypeInfo,
    DocumentQRInfo,
    DocumentUsageInfo,
    DocumentAuditInfo,
    
    # Esquemas de filtros y listas
    DocumentFilter,
    DocumentListResponse,
    
    # Esquemas para operaciones
    DocumentApproval,
    DocumentBulkAction,
    DocumentBulkActionResponse,
    DocumentAnalytics,
    DocumentProcessingStatus,
    DocumentExport,
    
    # Enums
    DocumentStatus,
    ApprovalStatus,
    AccessLevel,
    DocumentPriority,
)

# === LISTA DE EXPORTACIONES ===
__all__ = [
    # === USER SCHEMAS ===
    "UserBase", "UserCreate", "UserUpdate", "UserAdminUpdate",
    "User", "UserSummary", "UserDetailed", "UserPermissions", "UserStats",
    "UserLogin", "UserLoginResponse", "UserMicrosoftData",
    "UserFilter", "UserListResponse",
    "UserBulkAction", "UserBulkActionResponse", "UserActivityLog", "UserExport",
    "UserRole", "UserStatus",
    
    # === DOCUMENT_TYPE SCHEMAS ===
    "DocumentTypeBase", "DocumentTypeCreate", "DocumentTypeUpdate", "DocumentTypeAdminUpdate",
    "DocumentTypeRequirements", "DocumentTypeFileConfig", "DocumentTypeQRConfig",
    "DocumentTypeUIConfig", "DocumentTypeWorkflow",
    "DocumentType", "DocumentTypeSummary", "DocumentTypeStats",
    "DocumentTypeValidation", "DocumentTypeValidationResponse",
    "DocumentTypeFilter", "DocumentTypeListResponse",
    "DocumentTypeClone", "DocumentTypeBulkAction", "DocumentTypeBulkActionResponse",
    "DocumentTypeTemplate", "DocumentTypeTemplateUpload", "DocumentTypeExport",
    
    # === QR_CODE SCHEMAS ===
    "QRCodeBase", "QRCodeCreate", "QRCodeBatchCreate", "QRCodeUpdate", "QRCodeRevoke", "QRCodeUse",
    "QRGenerationConfig", "QRData",
    "QRCode", "QRCodeSummary", "QRCodeStats", "QRCodeUsageLog",
    "QRCodeValidation", "QRCodeValidationResponse",
    "QRCodeFilter", "QRCodeListResponse",
    "QRCodeBulkAction", "QRCodeBulkActionResponse",
    "QRCodeGenerationRequest", "QRCodeGenerationResponse", "QRCodeAnalytics", "QRCodeExport",
    "QRStatus", "QRErrorCorrectionLevel",
    
    # === DOCUMENT SCHEMAS ===
    "DocumentBase", "DocumentCreate", "DocumentUpload", "DocumentBatchUpload",
    "DocumentUpdate", "DocumentAdminUpdate",
    "DocumentPersonInfo", "DocumentFileInfo", "DocumentMetadata",
    "Document", "DocumentSummary", "DocumentDetailed",
    "DocumentFileResponse", "DocumentTypeInfo", "DocumentQRInfo",
    "DocumentUsageInfo", "DocumentAuditInfo",
    "DocumentFilter", "DocumentListResponse",
    "DocumentApproval", "DocumentBulkAction", "DocumentBulkActionResponse",
    "DocumentAnalytics", "DocumentProcessingStatus", "DocumentExport",
    "DocumentStatus", "ApprovalStatus", "AccessLevel", "DocumentPriority",
]

# === REGISTROS POR CATEGORÍA ===
USER_SCHEMAS = {
    "base": [UserBase, UserCreate, UserUpdate, UserAdminUpdate],
    "response": [User, UserSummary, UserDetailed, UserPermissions, UserStats],
    "auth": [UserLogin, UserLoginResponse, UserMicrosoftData],
    "operations": [UserFilter, UserListResponse, UserBulkAction, UserBulkActionResponse],
    "enums": [UserRole, UserStatus],
}

DOCUMENT_TYPE_SCHEMAS = {
    "base": [DocumentTypeBase, DocumentTypeCreate, DocumentTypeUpdate, DocumentTypeAdminUpdate],
    "config": [DocumentTypeRequirements, DocumentTypeFileConfig, DocumentTypeQRConfig, 
               DocumentTypeUIConfig, DocumentTypeWorkflow],
    "response": [DocumentType, DocumentTypeSummary, DocumentTypeStats],
    "validation": [DocumentTypeValidation, DocumentTypeValidationResponse],
    "operations": [DocumentTypeFilter, DocumentTypeListResponse, DocumentTypeClone,
                   DocumentTypeBulkAction, DocumentTypeBulkActionResponse],
}

QR_CODE_SCHEMAS = {
    "base": [QRCodeBase, QRCodeCreate, QRCodeBatchCreate, QRCodeUpdate, QRCodeRevoke, QRCodeUse],
    "config": [QRGenerationConfig, QRData],
    "response": [QRCode, QRCodeSummary, QRCodeStats, QRCodeUsageLog],
    "validation": [QRCodeValidation, QRCodeValidationResponse],
    "operations": [QRCodeFilter, QRCodeListResponse, QRCodeBulkAction, QRCodeBulkActionResponse,
                   QRCodeGenerationRequest, QRCodeGenerationResponse, QRCodeAnalytics],
    "enums": [QRStatus, QRErrorCorrectionLevel],
}

DOCUMENT_SCHEMAS = {
    "base": [DocumentBase, DocumentCreate, DocumentUpload, DocumentBatchUpload,
             DocumentUpdate, DocumentAdminUpdate],
    "info": [DocumentPersonInfo, DocumentFileInfo, DocumentMetadata],
    "response": [Document, DocumentSummary, DocumentDetailed, DocumentFileResponse,
                 DocumentTypeInfo, DocumentQRInfo, DocumentUsageInfo, DocumentAuditInfo],
    "operations": [DocumentFilter, DocumentListResponse, DocumentApproval,
                   DocumentBulkAction, DocumentBulkActionResponse, DocumentAnalytics],
    "enums": [DocumentStatus, ApprovalStatus, AccessLevel, DocumentPriority],
}

# === FUNCIONES DE UTILIDAD ===

def get_schemas_by_category(category: str) -> dict:
    """
    Obtener esquemas por categoría
    
    Args:
        category: Categoría de esquemas (user, document_type, qr_code, document)
        
    Returns:
        dict: Diccionario con esquemas de la categoría
    """
    schemas_map = {
        "user": USER_SCHEMAS,
        "document_type": DOCUMENT_TYPE_SCHEMAS,
        "qr_code": QR_CODE_SCHEMAS,
        "document": DOCUMENT_SCHEMAS,
    }
    return schemas_map.get(category, {})


def get_all_schemas() -> dict:
    """
    Obtener todos los esquemas organizados por categoría
    
    Returns:
        dict: Todos los esquemas organizados
    """
    return {
        "user": USER_SCHEMAS,
        "document_type": DOCUMENT_TYPE_SCHEMAS,
        "qr_code": QR_CODE_SCHEMAS,
        "document": DOCUMENT_SCHEMAS,
    }


def get_schema_info(schema_name: str) -> dict:
    """
    Obtener información sobre un esquema específico
    
    Args:
        schema_name: Nombre del esquema
        
    Returns:
        dict: Información del esquema
    """
    # Buscar en todos los esquemas
    all_schemas = globals()
    
    if schema_name in all_schemas:
        schema_class = all_schemas[schema_name]
        
        # Verificar que sea una clase Pydantic
        if hasattr(schema_class, '__fields__'):
            return {
                "name": schema_name,
                "fields": list(schema_class.__fields__.keys()),
                "field_count": len(schema_class.__fields__),
                "docstring": schema_class.__doc__,
                "module": schema_class.__module__,
            }
    
    return {"error": f"Esquema '{schema_name}' no encontrado"}


def validate_schema_consistency():
    """
    Validar consistencia entre esquemas relacionados
    
    Returns:
        dict: Resultado de validaciones
    """
    issues = []
    warnings = []
    
    # Verificar que esquemas de creación y actualización sean consistentes
    creation_update_pairs = [
        (UserCreate, UserUpdate),
        (DocumentTypeCreate, DocumentTypeUpdate),
        (QRCodeCreate, QRCodeUpdate),
        (DocumentCreate, DocumentUpdate),
    ]
    
    for create_schema, update_schema in creation_update_pairs:
        create_fields = set(create_schema.__fields__.keys())
        update_fields = set(update_schema.__fields__.keys())
        
        # Los campos de actualización deberían ser subconjunto de creación
        extra_update_fields = update_fields - create_fields
        if extra_update_fields:
            warnings.append(
                f"{update_schema.__name__} tiene campos no presentes en {create_schema.__name__}: "
                f"{', '.join(extra_update_fields)}"
            )
    
    # Verificar que los enums estén siendo usados consistentemente
    enum_usage = {
        "UserRole": [User, UserCreate, UserUpdate, UserFilter],
        "UserStatus": [User, UserCreate, UserUpdate, UserFilter],
        "QRStatus": [QRCode, QRCodeSummary, QRCodeFilter],
        "DocumentStatus": [Document, DocumentSummary, DocumentFilter],
        "ApprovalStatus": [Document, DocumentSummary, DocumentFilter],
    }
    
    for enum_name, schemas_using in enum_usage.items():
        # Verificar que los esquemas estén usando el enum
        for schema in schemas_using:
            schema_fields = schema.__fields__
            # Esta validación se puede expandir según necesidades específicas
    
    return {
        "status": "validated",
        "issues": issues,
        "warnings": warnings,
        "total_schemas": len(__all__),
        "categories": ["user", "document_type", "qr_code", "document"]
    }


def get_schema_dependencies() -> dict:
    """
    Obtener dependencias entre esquemas
    
    Returns:
        dict: Mapa de dependencias
    """
    return {
        "Document": ["DocumentType", "User", "QRCode"],
        "QRCode": ["DocumentType", "User"],
        "DocumentType": ["User"],
        "User": [],  # Sin dependencias
    }


def get_validation_schemas() -> list:
    """
    Obtener lista de esquemas que incluyen validaciones personalizadas
    
    Returns:
        list: Esquemas con validaciones
    """
    validation_schemas = []
    
    for schema_name in __all__:
        schema_class = globals().get(schema_name)
        if schema_class and hasattr(schema_class, '__validators__'):
            if schema_class.__validators__:
                validation_schemas.append(schema_name)
    
    return validation_schemas


def get_enum_schemas() -> list:
    """
    Obtener lista de enums definidos
    
    Returns:
        list: Lista de enums
    """
    return [
        "UserRole", "UserStatus", "QRStatus", "QRErrorCorrectionLevel",
        "DocumentStatus", "ApprovalStatus", "AccessLevel", "DocumentPriority"
    ]


# === CONFIGURACIÓN DE ESQUEMAS ===
SCHEMA_VERSION = "1.0.0"

SCHEMA_METADATA = {
    "version": SCHEMA_VERSION,
    "total_schemas": len(__all__),
    "categories": {
        "user": len(USER_SCHEMAS.get("base", [])) + len(USER_SCHEMAS.get("response", [])) + 
                len(USER_SCHEMAS.get("operations", [])),
        "document_type": len(DOCUMENT_TYPE_SCHEMAS.get("base", [])) + 
                        len(DOCUMENT_TYPE_SCHEMAS.get("response", [])),
        "qr_code": len(QR_CODE_SCHEMAS.get("base", [])) + len(QR_CODE_SCHEMAS.get("response", [])),
        "document": len(DOCUMENT_SCHEMAS.get("base", [])) + len(DOCUMENT_SCHEMAS.get("response", [])),
    },
    "enums": len(get_enum_schemas()),
    "with_validators": len(get_validation_schemas()),
}


def get_schema_metadata() -> dict:
    """
    Obtener metadatos de los esquemas
    
    Returns:
        dict: Metadatos completos
    """
    return SCHEMA_METADATA


# === INICIALIZACIÓN ===
def initialize_schemas():
    """
    Inicializar y validar esquemas
    
    Returns:
        bool: True si la inicialización fue exitosa
    """
    try:
        validation_result = validate_schema_consistency()
        
        if validation_result.get("issues"):
            print("Problemas encontrados en esquemas:")
            for issue in validation_result["issues"]:
                print(f"  - ERROR: {issue}")
            return False
        
        if validation_result.get("warnings"):
            print("Advertencias en esquemas:")
            for warning in validation_result["warnings"]:
                print(f"  - WARNING: {warning}")
        
        print(f"Esquemas inicializados correctamente (v{SCHEMA_VERSION})")
        print(f"Total de esquemas: {SCHEMA_METADATA['total_schemas']}")
        print(f"Esquemas con validadores: {SCHEMA_METADATA['with_validators']}")
        print(f"Enums definidos: {SCHEMA_METADATA['enums']}")
        
        return True
        
    except Exception as e:
        print(f"Error inicializando esquemas: {e}")
        return False


# Auto-ejecutar inicialización al importar
if __name__ != "__main__":
    initialize_schemas()