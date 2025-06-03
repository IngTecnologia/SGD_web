"""
Modelos de SGD Web

Este módulo importa y expone todos los modelos de la aplicación,
facilitando las importaciones y asegurando que SQLAlchemy los registre correctamente.
"""

# Importar la base para SQLAlchemy
from ..database import Base

# Importar todos los modelos
from .user import User, UserRole, UserStatus
from .document_type import DocumentType
from .qr_code import QRCode
from .document import Document

# Lista de todos los modelos para facilitar importaciones
__all__ = [
    # Base
    "Base",
    
    # Modelos principales
    "User",
    "DocumentType", 
    "QRCode",
    "Document",
    
    # Enums
    "UserRole",
    "UserStatus",
]

# Diccionario para mapeo dinámico de modelos
MODEL_REGISTRY = {
    "user": User,
    "document_type": DocumentType,
    "qr_code": QRCode,
    "document": Document,
}

# Información de versión de los modelos
MODEL_VERSION = "1.0.0"

def get_model(model_name: str):
    """
    Obtener modelo por nombre
    
    Args:
        model_name: Nombre del modelo en minúsculas
        
    Returns:
        Clase del modelo o None si no existe
    """
    return MODEL_REGISTRY.get(model_name.lower())

def get_all_models():
    """
    Obtener lista de todas las clases de modelo
    
    Returns:
        List: Lista de clases de modelo
    """
    return list(MODEL_REGISTRY.values())

def get_model_names():
    """
    Obtener lista de nombres de modelos
    
    Returns:
        List: Lista de nombres de modelos
    """
    return list(MODEL_REGISTRY.keys())

# Verificar que todos los modelos estén registrados correctamente
def validate_models():
    """
    Validar que todos los modelos estén correctamente configurados
    
    Returns:
        bool: True si todos los modelos son válidos
    """
    issues = []
    
    for name, model_class in MODEL_REGISTRY.items():
        # Verificar que tenga __tablename__
        if not hasattr(model_class, '__tablename__'):
            issues.append(f"Modelo {name} no tiene __tablename__")
        
        # Verificar que herede de Base
        if not issubclass(model_class, Base):
            issues.append(f"Modelo {name} no hereda de Base")
        
        # Verificar que tenga primary key
        if not hasattr(model_class, 'id'):
            issues.append(f"Modelo {name} no tiene campo 'id'")
    
    if issues:
        print("Problemas encontrados en modelos:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    return True

# Información sobre las relaciones entre modelos
MODEL_RELATIONSHIPS = {
    "User": {
        "uploaded_documents": "Document.uploaded_by",
        "generated_qr_codes": "QRCode.generated_by", 
        "created_document_types": "DocumentType.created_by"
    },
    "DocumentType": {
        "documents": "Document.document_type_id",
        "qr_codes": "QRCode.document_type_id",
        "created_by_user": "User.id"
    },
    "QRCode": {
        "document_type": "DocumentType.id",
        "generated_by_user": "User.id",
        "associated_document": "Document.qr_code_id"
    },
    "Document": {
        "document_type": "DocumentType.id",
        "uploaded_by_user": "User.id",
        "qr_code": "QRCode.qr_id",
        "approved_by_user": "User.id",
        "last_viewed_by_user": "User.id"
    }
}

def get_model_relationships(model_name: str = None):
    """
    Obtener información sobre relaciones de modelos
    
    Args:
        model_name: Nombre del modelo específico (opcional)
        
    Returns:
        dict: Información de relaciones
    """
    if model_name:
        return MODEL_RELATIONSHIPS.get(model_name, {})
    return MODEL_RELATIONSHIPS

# Configuración de metadatos de tablas
TABLE_COMMENTS = {
    "users": "Usuarios del sistema integrados con Microsoft 365",
    "document_types": "Tipos de documento configurables con requisitos específicos",
    "qr_codes": "Códigos QR generados y su ciclo de vida",
    "documents": "Documentos registrados en el sistema con metadata completa"
}

def get_table_comment(table_name: str):
    """
    Obtener comentario de tabla
    
    Args:
        table_name: Nombre de la tabla
        
    Returns:
        str: Comentario de la tabla
    """
    return TABLE_COMMENTS.get(table_name, "")

# Índices recomendados para optimización
RECOMMENDED_INDEXES = {
    "users": [
        "azure_id",
        "email", 
        "role",
        "status",
        "is_active"
    ],
    "document_types": [
        "code",
        "is_active"
    ],
    "qr_codes": [
        "qr_id",
        "document_type_id",
        "is_used",
        "is_expired",
        "is_revoked",
        "used_in_document_id"
    ],
    "documents": [
        "document_type_id",
        "qr_code_id",
        "cedula",
        "status",
        "uploaded_by",
        "created_at",
        "is_confidential"
    ]
}

def get_recommended_indexes(table_name: str = None):
    """
    Obtener índices recomendados
    
    Args:
        table_name: Nombre de tabla específica (opcional)
        
    Returns:
        dict o list: Índices recomendados
    """
    if table_name:
        return RECOMMENDED_INDEXES.get(table_name, [])
    return RECOMMENDED_INDEXES

# Validaciones de integridad referencial
def check_referential_integrity():
    """
    Verificar integridad referencial entre modelos
    
    Returns:
        dict: Resultado de verificaciones
    """
    # Esta función se puede expandir para verificar:
    # - Foreign keys válidas
    # - Relaciones bidireccionales
    # - Constraints de integridad
    
    return {
        "status": "pending_implementation",
        "checks": [
            "foreign_key_constraints",
            "relationship_consistency", 
            "cascade_rules"
        ]
    }

# Funciones de utilidad para migraciones
def get_migration_order():
    """
    Obtener orden recomendado para migraciones
    
    Returns:
        list: Lista de modelos en orden de dependencia
    """
    # Orden basado en dependencias de foreign keys
    return [
        "User",           # Sin dependencias
        "DocumentType",   # Depende de User
        "QRCode",        # Depende de DocumentType y User
        "Document"       # Depende de DocumentType, User y QRCode
    ]

def get_model_dependencies():
    """
    Obtener mapa de dependencias entre modelos
    
    Returns:
        dict: Mapa de dependencias
    """
    return {
        "User": [],
        "DocumentType": ["User"],
        "QRCode": ["DocumentType", "User"],
        "Document": ["DocumentType", "User", "QRCode"]
    }

# Configuración para testing
TEST_DATA_REQUIREMENTS = {
    "User": {
        "required_fields": ["azure_id", "email", "name"],
        "optional_fields": ["department", "job_title", "role"]
    },
    "DocumentType": {
        "required_fields": ["code", "name", "created_by"],
        "optional_fields": ["description", "requires_qr", "template_path"]
    },
    "QRCode": {
        "required_fields": ["qr_id", "document_type_id", "generated_by"],
        "optional_fields": ["expires_at", "qr_data"]
    },
    "Document": {
        "required_fields": ["file_name", "file_path", "document_type_id", "uploaded_by"],
        "optional_fields": ["cedula", "nombre_completo", "qr_code_id"]
    }
}

def get_test_data_requirements(model_name: str = None):
    """
    Obtener requisitos para datos de testing
    
    Args:
        model_name: Nombre del modelo específico
        
    Returns:
        dict: Requisitos de datos de testing
    """
    if model_name:
        return TEST_DATA_REQUIREMENTS.get(model_name, {})
    return TEST_DATA_REQUIREMENTS

# Inicialización de modelos
def initialize_models():
    """
    Inicializar configuración de modelos
    
    Returns:
        bool: True si la inicialización fue exitosa
    """
    try:
        # Validar modelos
        if not validate_models():
            return False
        
        # Aquí se pueden agregar más verificaciones
        # como validación de relaciones, constraints, etc.
        
        print(f"Modelos inicializados correctamente (v{MODEL_VERSION})")
        print(f"Modelos registrados: {', '.join(get_model_names())}")
        
        return True
        
    except Exception as e:
        print(f"Error inicializando modelos: {e}")
        return False

# Auto-ejecutar validación al importar
if __name__ != "__main__":
    # Solo ejecutar en importación normal, no en testing
    initialize_models()