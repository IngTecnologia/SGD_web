"""
Modelo de Tipo de Documento para SGD Web
Permite configurar diferentes tipos de documentos con sus respectivos requisitos
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any

from ..database import Base


class DocumentType(Base):
    """
    Modelo para tipos de documento configurables
    
    Permite definir diferentes tipos de documentos (GCO-REG-099, Facturas, Contratos, etc.)
    y especificar qué campos requieren y si necesitan códigos QR.
    """
    __tablename__ = "document_types"
    
    # === CAMPOS PRINCIPALES ===
    id = Column(Integer, primary_key=True, index=True)
    
    # Identificación del tipo
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # === CONFIGURACIÓN DE REQUISITOS ===
    # Campos obligatorios
    requires_qr = Column(Boolean, default=False, nullable=False)
    requires_cedula = Column(Boolean, default=True, nullable=False)
    requires_nombre = Column(Boolean, default=False, nullable=False)
    requires_telefono = Column(Boolean, default=False, nullable=False)
    requires_email = Column(Boolean, default=False, nullable=False)
    requires_direccion = Column(Boolean, default=False, nullable=False)
    
    # Validación de archivos
    allowed_file_types = Column(Text)  # JSON string con tipos MIME permitidos
    max_file_size_mb = Column(Integer, default=50)  # Tamaño máximo en MB
    allow_multiple_files = Column(Boolean, default=False)  # Permitir múltiples archivos
    
    # === CONFIGURACIÓN DE GENERACIÓN ===
    # Plantilla para generación de documentos
    template_path = Column(String(255))  # Ruta a plantilla Word
    
    # Configuración de QR en la plantilla
    qr_table_number = Column(Integer, default=1)  # Número de tabla donde insertar QR
    qr_row = Column(Integer, default=5)           # Fila para el QR
    qr_column = Column(Integer, default=0)        # Columna para el QR
    qr_width = Column(Integer, default=1)         # Ancho del QR en pulgadas
    qr_height = Column(Integer, default=1)        # Alto del QR en pulgadas
    
    # === CONFIGURACIÓN DE INTERFAZ ===
    # Apariencia en la interfaz
    color = Column(String(7), default="#007bff")  # Color en formato hex
    icon = Column(String(50), default="file")      # Icono para mostrar
    sort_order = Column(Integer, default=0)        # Orden de aparición
    
    # === CONFIGURACIÓN DE PROCESO ===
    # Workflow y aprobaciones
    requires_approval = Column(Boolean, default=False)
    auto_notify_email = Column(Boolean, default=False)
    notification_emails = Column(Text)  # JSON string con emails para notificar
    
    # Retención y archivo
    retention_days = Column(Integer)  # Días de retención (null = indefinido)
    auto_archive = Column(Boolean, default=False)
    
    # === CAMPOS DE ESTADO ===
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_system_type = Column(Boolean, default=False)  # Tipos del sistema no editables
    
    # === AUDITORÍA ===
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Estadísticas de uso
    documents_count = Column(Integer, default=0)  # Documentos registrados de este tipo
    generated_count = Column(Integer, default=0)  # Documentos generados de este tipo
    
    # === RELACIONES ===
    # Usuario que creó este tipo
    created_by_user = relationship("User", back_populates="created_document_types")
    
    # Documentos de este tipo
    documents = relationship("Document", back_populates="document_type")
    
    # QR codes generados para este tipo
    qr_codes = relationship("QRCode", back_populates="document_type")
    
    def __repr__(self):
        return f"<DocumentType(id={self.id}, code='{self.code}', name='{self.name}')>"
    
    # === MÉTODOS DE UTILIDAD ===
    
    @property
    def allowed_file_types_list(self) -> list:
        """Obtener lista de tipos de archivo permitidos"""
        if not self.allowed_file_types:
            return ["application/pdf", "image/jpeg", "image/png"]
        
        import json
        try:
            return json.loads(self.allowed_file_types)
        except:
            return ["application/pdf", "image/jpeg", "image/png"]
    
    @allowed_file_types_list.setter
    def allowed_file_types_list(self, value: list):
        """Establecer lista de tipos de archivo permitidos"""
        import json
        self.allowed_file_types = json.dumps(value)
    
    @property
    def notification_emails_list(self) -> list:
        """Obtener lista de emails para notificaciones"""
        if not self.notification_emails:
            return []
        
        import json
        try:
            return json.loads(self.notification_emails)
        except:
            return []
    
    @notification_emails_list.setter
    def notification_emails_list(self, value: list):
        """Establecer lista de emails para notificaciones"""
        import json
        self.notification_emails = json.dumps(value)
    
    @property
    def required_fields(self) -> list:
        """Obtener lista de campos requeridos"""
        fields = []
        if self.requires_cedula:
            fields.append("cedula")
        if self.requires_nombre:
            fields.append("nombre")
        if self.requires_telefono:
            fields.append("telefono")
        if self.requires_email:
            fields.append("email")
        if self.requires_direccion:
            fields.append("direccion")
        if self.requires_qr:
            fields.append("qr_code")
        return fields
    
    @property
    def has_template(self) -> bool:
        """Verificar si tiene plantilla configurada"""
        return bool(self.template_path)
    
    @property
    def can_generate(self) -> bool:
        """Verificar si se pueden generar documentos de este tipo"""
        return self.has_template and self.is_active
    
    def validate_file_type(self, mime_type: str) -> bool:
        """
        Validar si un tipo de archivo está permitido
        
        Args:
            mime_type: Tipo MIME del archivo
            
        Returns:
            bool: True si está permitido
        """
        return mime_type in self.allowed_file_types_list
    
    def validate_file_size(self, size_bytes: int) -> bool:
        """
        Validar tamaño de archivo
        
        Args:
            size_bytes: Tamaño del archivo en bytes
            
        Returns:
            bool: True si está dentro del límite
        """
        max_bytes = self.max_file_size_mb * 1024 * 1024
        return size_bytes <= max_bytes
    
    def validate_document_data(self, data: dict) -> tuple[bool, list]:
        """
        Validar datos de documento según los requisitos del tipo
        
        Args:
            data: Diccionario con datos del documento
            
        Returns:
            tuple: (is_valid, errors_list)
        """
        errors = []
        
        # Validar campos requeridos
        for field in self.required_fields:
            if field not in data or not data[field]:
                field_name = {
                    "cedula": "Cédula",
                    "nombre": "Nombre completo",
                    "telefono": "Teléfono",
                    "email": "Email",
                    "direccion": "Dirección",
                    "qr_code": "Código QR"
                }.get(field, field)
                errors.append(f"{field_name} es requerido")
        
        # Validar email si está presente
        if "email" in data and data["email"]:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, data["email"]):
                errors.append("Email no tiene formato válido")
        
        return len(errors) == 0, errors
    
    def increment_documents(self):
        """Incrementar contador de documentos registrados"""
        self.documents_count += 1
    
    def increment_generated(self):
        """Incrementar contador de documentos generados"""
        self.generated_count += 1
    
    def activate(self):
        """Activar tipo de documento"""
        self.is_active = True
    
    def deactivate(self):
        """Desactivar tipo de documento"""
        self.is_active = False
    
    def clone(self, new_code: str, new_name: str, created_by: int) -> 'DocumentType':
        """
        Crear una copia de este tipo de documento
        
        Args:
            new_code: Nuevo código para el tipo
            new_name: Nuevo nombre para el tipo
            created_by: ID del usuario que crea la copia
            
        Returns:
            DocumentType: Nueva instancia clonada
        """
        cloned = DocumentType(
            code=new_code,
            name=new_name,
            description=f"Copia de {self.name}",
            requires_qr=self.requires_qr,
            requires_cedula=self.requires_cedula,
            requires_nombre=self.requires_nombre,
            requires_telefono=self.requires_telefono,
            requires_email=self.requires_email,
            requires_direccion=self.requires_direccion,
            allowed_file_types=self.allowed_file_types,
            max_file_size_mb=self.max_file_size_mb,
            allow_multiple_files=self.allow_multiple_files,
            template_path=self.template_path,
            qr_table_number=self.qr_table_number,
            qr_row=self.qr_row,
            qr_column=self.qr_column,
            qr_width=self.qr_width,
            qr_height=self.qr_height,
            color=self.color,
            icon=self.icon,
            requires_approval=self.requires_approval,
            auto_notify_email=self.auto_notify_email,
            notification_emails=self.notification_emails,
            retention_days=self.retention_days,
            auto_archive=self.auto_archive,
            created_by=created_by
        )
        return cloned
    
    def to_dict(self) -> dict:
        """Convertir tipo de documento a diccionario para APIs"""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "requirements": {
                "requires_qr": self.requires_qr,
                "requires_cedula": self.requires_cedula,
                "requires_nombre": self.requires_nombre,
                "requires_telefono": self.requires_telefono,
                "requires_email": self.requires_email,
                "requires_direccion": self.requires_direccion,
                "required_fields": self.required_fields
            },
            "file_config": {
                "allowed_file_types": self.allowed_file_types_list,
                "max_file_size_mb": self.max_file_size_mb,
                "allow_multiple_files": self.allow_multiple_files
            },
            "template_config": {
                "template_path": self.template_path,
                "has_template": self.has_template,
                "can_generate": self.can_generate,
                "qr_config": {
                    "table_number": self.qr_table_number,
                    "row": self.qr_row,
                    "column": self.qr_column,
                    "width": self.qr_width,
                    "height": self.qr_height
                } if self.requires_qr else None
            },
            "ui_config": {
                "color": self.color,
                "icon": self.icon,
                "sort_order": self.sort_order
            },
            "workflow": {
                "requires_approval": self.requires_approval,
                "auto_notify_email": self.auto_notify_email,
                "notification_emails": self.notification_emails_list,
                "retention_days": self.retention_days,
                "auto_archive": self.auto_archive
            },
            "status": {
                "is_active": self.is_active,
                "is_system_type": self.is_system_type
            },
            "stats": {
                "documents_count": self.documents_count,
                "generated_count": self.generated_count
            },
            "audit": {
                "created_by": self.created_by,
                "created_at": self.created_at,
                "updated_at": self.updated_at
            }
        }