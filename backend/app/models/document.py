"""
Modelo de Documento para SGD Web
Modelo principal que representa los documentos registrados en el sistema
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import os
import json

from ..database import Base


class Document(Base):
    """
    Modelo principal para documentos registrados
    
    Representa cada documento físico o digital que ha sido registrado
    en el sistema, con toda su metadata y referencias.
    """
    __tablename__ = "documents"
    
    # === CAMPOS PRINCIPALES ===
    id = Column(Integer, primary_key=True, index=True)
    
    # === IDENTIFICACIÓN ===
    # Código QR asociado (si aplica)
    qr_code_id = Column(String(255), ForeignKey("qr_codes.qr_id"), nullable=True, index=True)
    
    # Tipo de documento
    document_type_id = Column(Integer, ForeignKey("document_types.id"), nullable=False, index=True)
    
    # === INFORMACIÓN DE LA PERSONA ===
    # Campos principales
    cedula = Column(String(20), index=True)  # Número de identificación
    nombre_completo = Column(String(200))    # Nombre completo de la persona
    
    # Campos adicionales (según configuración del tipo)
    telefono = Column(String(20))
    email = Column(String(100))
    direccion = Column(Text)
    
    # Información adicional en formato JSON
    additional_data = Column(JSON)  # Campos dinámicos según el tipo de documento
    
    # === INFORMACIÓN DEL ARCHIVO ===
    # Archivo principal
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Ruta local
    file_size = Column(BigInteger)  # Tamaño en bytes
    mime_type = Column(String(100))
    file_hash = Column(String(64))  # SHA-256 del archivo para integridad
    
    # URLs de acceso
    onedrive_url = Column(String(500))      # URL de OneDrive
    onedrive_file_id = Column(String(255))  # ID del archivo en OneDrive
    
    # Archivos adicionales (si el tipo lo permite)
    additional_files = Column(JSON)  # Lista de archivos adicionales
    
    # === PROCESAMIENTO Y ANÁLISIS ===
    # Información extraída del QR
    tiene_qr = Column(Boolean, default=False, nullable=False)  # Si el documento físico tiene QR
    qr_extraction_success = Column(Boolean, default=False, nullable=False)
    qr_extraction_data = Column(JSON)  # Datos extraídos del QR
    qr_extraction_error = Column(Text)  # Error en extracción si aplica
    
    # Análisis OCR (futuro)
    ocr_processed = Column(Boolean, default=False)
    ocr_text = Column(Text)  # Texto extraído por OCR
    ocr_confidence = Column(Integer)  # Confianza del OCR (0-100)
    
    # === ESTADO Y WORKFLOW ===
    status = Column(String(20), default="active", nullable=False, index=True)
    # Posibles valores: active, archived, deleted, pending_approval, rejected
    
    approval_status = Column(String(20), default="auto_approved")
    # Posibles valores: auto_approved, pending, approved, rejected
    
    approval_notes = Column(Text)  # Notas de aprobación/rechazo
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # === CLASIFICACIÓN Y ORGANIZACIÓN ===
    # Tags y categorización
    tags = Column(JSON)  # Lista de tags para búsqueda
    category = Column(String(100))  # Categoría adicional
    priority = Column(Integer, default=0)  # Prioridad (0=normal, 1=alta, -1=baja)
    
    # Agrupación (para documentos relacionados)
    group_id = Column(String(50))  # ID de grupo para documentos relacionados
    sequence_number = Column(Integer, default=1)  # Número en secuencia
    
    # === AUDITORÍA COMPLETA ===
    # Usuario que subió el documento
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Historial de cambios
    version = Column(Integer, default=1)  # Versión del documento
    change_log = Column(JSON)  # Log de cambios
    
    # === RETENCIÓN Y ARCHIVO ===
    # Fechas importantes
    retention_date = Column(DateTime)  # Fecha de retención calculada
    archive_date = Column(DateTime)    # Fecha de archivo
    
    # Control de retención
    is_permanent = Column(Boolean, default=False)  # Retención permanente
    
    # === ACCESO Y SEGURIDAD ===
    # Control de acceso
    is_confidential = Column(Boolean, default=False)
    access_level = Column(String(20), default="normal")  # normal, restricted, confidential
    
    # Registro de accesos
    view_count = Column(Integer, default=0)
    last_viewed_at = Column(DateTime)
    last_viewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # === RELACIONES ===
    # Tipo de documento
    document_type = relationship("DocumentType", back_populates="documents")
    
    # Usuario que subió
    uploaded_by_user = relationship(
        "User", 
        back_populates="uploaded_documents",
        foreign_keys=[uploaded_by]
    )
    
    # Usuario que aprobó
    approved_by_user = relationship(
        "User", 
        foreign_keys=[approved_by]
    )
    
    # Usuario que vio por última vez
    last_viewed_by_user = relationship(
        "User",
        foreign_keys=[last_viewed_by]
    )
    
    # Código QR asociado
    qr_code = relationship(
        "QRCode", 
        back_populates="associated_document",
        foreign_keys=[qr_code_id]
    )
    
    def __repr__(self):
        return f"<Document(id={self.id}, file_name='{self.file_name}', type='{self.document_type.code if self.document_type else 'N/A'}')>"
    
    # === MÉTODOS DE UTILIDAD ===
    
    @property
    def additional_data_dict(self) -> Dict[str, Any]:
        """Obtener datos adicionales como diccionario"""
        return self.additional_data or {}
    
    @additional_data_dict.setter
    def additional_data_dict(self, value: Dict[str, Any]):
        """Establecer datos adicionales"""
        self.additional_data = value
    
    @property
    def tags_list(self) -> List[str]:
        """Obtener lista de tags"""
        return self.tags or []
    
    @tags_list.setter
    def tags_list(self, value: List[str]):
        """Establecer lista de tags"""
        self.tags = value
    
    @property
    def additional_files_list(self) -> List[Dict[str, Any]]:
        """Obtener lista de archivos adicionales"""
        return self.additional_files or []
    
    @additional_files_list.setter
    def additional_files_list(self, value: List[Dict[str, Any]]):
        """Establecer lista de archivos adicionales"""
        self.additional_files = value
    
    @property
    def change_log_list(self) -> List[Dict[str, Any]]:
        """Obtener log de cambios"""
        return self.change_log or []
    
    @property
    def file_size_mb(self) -> float:
        """Obtener tamaño del archivo en MB"""
        if not self.file_size:
            return 0.0
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def file_extension(self) -> str:
        """Obtener extensión del archivo"""
        return os.path.splitext(self.file_name)[1].lower()
    
    @property
    def is_image(self) -> bool:
        """Verificar si es una imagen"""
        image_mimes = ["image/jpeg", "image/png", "image/jpg", "image/gif"]
        return self.mime_type in image_mimes
    
    @property
    def is_pdf(self) -> bool:
        """Verificar si es un PDF"""
        return self.mime_type == "application/pdf"
    
    @property
    def is_word_document(self) -> bool:
        """Verificar si es un documento Word"""
        word_mimes = [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword"
        ]
        return self.mime_type in word_mimes
    
    @property
    def is_expired(self) -> bool:
        """Verificar si el documento ha expirado según retención"""
        if not self.retention_date:
            return False
        return self.retention_date <= datetime.utcnow()
    
    @property
    def days_until_retention(self) -> Optional[int]:
        """Días hasta la fecha de retención"""
        if not self.retention_date:
            return None
        delta = self.retention_date - datetime.utcnow()
        return max(0, delta.days)
    
    def add_change_log(self, action: str, details: Dict[str, Any], user_id: int):
        """
        Agregar entrada al log de cambios
        
        Args:
            action: Acción realizada
            details: Detalles del cambio
            user_id: Usuario que realizó el cambio
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details,
            "user_id": user_id,
            "version": self.version
        }
        
        current_log = self.change_log_list
        current_log.append(log_entry)
        self.change_log = current_log
    
    def update_version(self, user_id: int, change_description: str = None):
        """
        Incrementar versión del documento
        
        Args:
            user_id: Usuario que actualiza
            change_description: Descripción del cambio
        """
        self.version += 1
        self.add_change_log("version_update", {
            "description": change_description,
            "new_version": self.version
        }, user_id)
    
    def calculate_retention_date(self):
        """Calcular fecha de retención basada en el tipo de documento"""
        if self.is_permanent or not self.document_type or not self.document_type.retention_days:
            self.retention_date = None
        else:
            self.retention_date = self.created_at + timedelta(days=self.document_type.retention_days)
    
    def mark_as_viewed(self, user_id: int):
        """
        Marcar documento como visto
        
        Args:
            user_id: ID del usuario que ve el documento
        """
        self.view_count += 1
        self.last_viewed_at = datetime.utcnow()
        self.last_viewed_by = user_id
    
    def add_tag(self, tag: str):
        """Agregar tag al documento"""
        current_tags = self.tags_list
        if tag not in current_tags:
            current_tags.append(tag.lower().strip())
            self.tags_list = current_tags
    
    def remove_tag(self, tag: str):
        """Remover tag del documento"""
        current_tags = self.tags_list
        if tag in current_tags:
            current_tags.remove(tag)
            self.tags_list = current_tags
    
    def add_additional_file(self, file_info: Dict[str, Any]):
        """
        Agregar archivo adicional
        
        Args:
            file_info: Información del archivo adicional
        """
        current_files = self.additional_files_list
        current_files.append(file_info)
        self.additional_files_list = current_files
    
    def approve(self, user_id: int, notes: str = None):
        """
        Aprobar documento
        
        Args:
            user_id: Usuario que aprueba
            notes: Notas de aprobación
        """
        self.approval_status = "approved"
        self.approved_by = user_id
        self.approved_at = datetime.utcnow()
        self.approval_notes = notes
        
        self.add_change_log("approved", {
            "notes": notes
        }, user_id)
    
    def reject(self, user_id: int, reason: str):
        """
        Rechazar documento
        
        Args:
            user_id: Usuario que rechaza
            reason: Razón del rechazo
        """
        self.approval_status = "rejected"
        self.approved_by = user_id
        self.approved_at = datetime.utcnow()
        self.approval_notes = reason
        self.status = "rejected"
        
        self.add_change_log("rejected", {
            "reason": reason
        }, user_id)
    
    def archive(self, user_id: int):
        """
        Archivar documento
        
        Args:
            user_id: Usuario que archiva
        """
        self.status = "archived"
        self.archive_date = datetime.utcnow()
        
        self.add_change_log("archived", {}, user_id)
    
    def soft_delete(self, user_id: int, reason: str = None):
        """
        Eliminación suave del documento
        
        Args:
            user_id: Usuario que elimina
            reason: Razón de eliminación
        """
        self.status = "deleted"
        
        self.add_change_log("deleted", {
            "reason": reason
        }, user_id)
    
    def restore(self, user_id: int):
        """
        Restaurar documento eliminado
        
        Args:
            user_id: Usuario que restaura
        """
        self.status = "active"
        
        self.add_change_log("restored", {}, user_id)
    
    def get_search_text(self) -> str:
        """Obtener texto para búsqueda completa"""
        search_parts = [
            self.file_name,
            self.cedula or "",
            self.nombre_completo or "",
            self.telefono or "",
            self.email or "",
            self.direccion or "",
            " ".join(self.tags_list),
            self.category or "",
            self.ocr_text or ""
        ]
        
        return " ".join(filter(None, search_parts)).lower()
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Convertir documento a diccionario para APIs
        
        Args:
            include_sensitive: Incluir información sensible
        """
        base_dict = {
            "id": self.id,
            "document_type": {
                "id": self.document_type_id,
                "code": self.document_type.code if self.document_type else None,
                "name": self.document_type.name if self.document_type else None
            },
            "file_info": {
                "name": self.file_name,
                "size": self.file_size,
                "size_mb": self.file_size_mb,
                "mime_type": self.mime_type,
                "extension": self.file_extension,
                "is_image": self.is_image,
                "is_pdf": self.is_pdf,
                "is_word": self.is_word_document
            },
            "person_info": {
                "cedula": self.cedula,
                "nombre_completo": self.nombre_completo,
                "telefono": self.telefono,
                "email": self.email
            },
            "status": {
                "status": self.status,
                "approval_status": self.approval_status,
                "is_confidential": self.is_confidential,
                "access_level": self.access_level
            },
            "metadata": {
                "tags": self.tags_list,
                "category": self.category,
                "priority": self.priority,
                "version": self.version,
                "group_id": self.group_id,
                "sequence_number": self.sequence_number
            },
            "dates": {
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "retention_date": self.retention_date,
                "archive_date": self.archive_date
            },
            "usage": {
                "view_count": self.view_count,
                "last_viewed_at": self.last_viewed_at
            },
            "qr_info": {
                "tiene_qr": self.tiene_qr,
                "has_qr_code": bool(self.qr_code_id),
                "qr_code_id": self.qr_code_id,
                "qr_extraction_success": self.qr_extraction_success
            }
        }
        
        if include_sensitive:
            base_dict.update({
                "file_paths": {
                    "local_path": self.file_path,
                    "onedrive_url": self.onedrive_url,
                    "onedrive_file_id": self.onedrive_file_id
                },
                "additional_data": self.additional_data_dict,
                "additional_files": self.additional_files_list,
                "change_log": self.change_log_list,
                "qr_extraction_data": self.qr_extraction_data,
                "ocr_text": self.ocr_text if self.ocr_processed else None
            })
        
        return base_dict