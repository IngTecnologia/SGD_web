"""
Modelo de Código QR para SGD Web
Gestiona los códigos QR generados y su ciclo de vida
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid
import json

from ..database import Base


class QRCode(Base):
    """
    Modelo para códigos QR generados
    
    Rastrea todos los códigos QR creados, su estado, y su asociación
    con documentos cuando son utilizados.
    """
    __tablename__ = "qr_codes"
    
    # === CAMPOS PRINCIPALES ===
    id = Column(Integer, primary_key=True, index=True)
    
    # Identificador único del QR (UUID4)
    qr_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # === CONFIGURACIÓN Y CONTEXTO ===
    # Tipo de documento para el cual fue generado
    document_type_id = Column(Integer, ForeignKey("document_types.id"), nullable=False, index=True)
    
    # Información adicional del QR
    qr_data = Column(Text)  # Datos completos codificados en el QR (JSON)
    qr_version = Column(Integer, default=1)  # Versión del formato de QR
    
    # === ESTADO DEL QR ===
    is_used = Column(Boolean, default=False, nullable=False, index=True)
    is_expired = Column(Boolean, default=False, nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False, index=True)
    
    # === ASOCIACIONES ===
    # Documento al que está asociado (cuando se usa)
    used_in_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True, index=True)
    
    # === AUDITORÍA ===
    # Usuario que generó el QR
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Fechas importantes
    created_at = Column(DateTime, default=func.now(), nullable=False)
    used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # Fecha de expiración (opcional)
    revoked_at = Column(DateTime, nullable=True)
    
    # === INFORMACIÓN TÉCNICA ===
    # Configuración usada para generar el QR
    generation_config = Column(JSON)  # Configuración técnica del QR
    
    # Información del archivo donde se insertó (para generación)
    source_file_path = Column(String(500))  # Ruta del archivo generado
    source_file_name = Column(String(255))  # Nombre del archivo generado
    
    # === ESTADÍSTICAS Y LOGS ===
    # Número de veces que se ha intentado usar
    usage_attempts = Column(Integer, default=0)
    
    # Log de intentos de uso (JSON)
    usage_log = Column(JSON, default=list)
    
    # === RELACIONES ===
    # Tipo de documento
    document_type = relationship("DocumentType", back_populates="qr_codes")
    
    # Usuario que lo generó
    generated_by_user = relationship("User", back_populates="generated_qr_codes")
    
    # Documento asociado (si se ha usado)
    associated_document = relationship(
        "Document",
        foreign_keys=[used_in_document_id],
        uselist=False
    )
    
    def __repr__(self):
        return f"<QRCode(id={self.id}, qr_id='{self.qr_id[:8]}...', used={self.is_used})>"
    
    # === MÉTODOS DE UTILIDAD ===
    
    @classmethod
    def generate_qr_id(cls) -> str:
        """Generar un ID único para el QR"""
        return str(uuid.uuid4())
    
    @property
    def is_valid(self) -> bool:
        """Verificar si el QR es válido para uso"""
        return (
            not self.is_used and 
            not self.is_expired and 
            not self.is_revoked and
            (not self.expires_at or self.expires_at > datetime.utcnow())
        )
    
    @property
    def status(self) -> str:
        """Obtener estado actual del QR"""
        if self.is_revoked:
            return "revoked"
        elif self.is_expired or (self.expires_at and self.expires_at <= datetime.utcnow()):
            return "expired"
        elif self.is_used:
            return "used"
        else:
            return "available"
    
    @property
    def qr_data_dict(self) -> Dict[str, Any]:
        """Obtener datos del QR como diccionario"""
        if not self.qr_data:
            return {}
        
        try:
            return json.loads(self.qr_data)
        except:
            return {}
    
    @qr_data_dict.setter
    def qr_data_dict(self, value: Dict[str, Any]):
        """Establecer datos del QR desde diccionario"""
        self.qr_data = json.dumps(value, ensure_ascii=False)
    
    @property
    def generation_config_dict(self) -> Dict[str, Any]:
        """Obtener configuración de generación como diccionario"""
        return self.generation_config or {}
    
    @generation_config_dict.setter
    def generation_config_dict(self, value: Dict[str, Any]):
        """Establecer configuración de generación"""
        self.generation_config = value
    
    @property
    def usage_log_list(self) -> list:
        """Obtener log de uso como lista"""
        return self.usage_log or []
    
    def add_usage_log(self, event: str, details: Dict[str, Any] = None):
        """
        Agregar entrada al log de uso
        
        Args:
            event: Tipo de evento
            details: Detalles adicionales del evento
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "details": details or {}
        }
        
        current_log = self.usage_log_list
        current_log.append(log_entry)
        self.usage_log = current_log
        
        self.usage_attempts += 1
    
    def mark_as_used(self, document_id: int, user_id: int = None):
        """
        Marcar QR como usado y asociarlo a un documento
        
        Args:
            document_id: ID del documento al que se asocia
            user_id: ID del usuario que lo usó
        """
        if not self.is_valid:
            raise ValueError(f"QR no válido para uso: {self.status}")
        
        self.is_used = True
        self.used_at = datetime.utcnow()
        self.used_in_document_id = document_id
        
        self.add_usage_log("used", {
            "document_id": document_id,
            "user_id": user_id
        })
    
    def revoke(self, reason: str = None, user_id: int = None):
        """
        Revocar el QR
        
        Args:
            reason: Razón de la revocación
            user_id: Usuario que revoca
        """
        self.is_revoked = True
        self.revoked_at = datetime.utcnow()
        
        self.add_usage_log("revoked", {
            "reason": reason,
            "revoked_by": user_id
        })
    
    def set_expiration(self, days: int = None, expiration_date: datetime = None):
        """
        Establecer fecha de expiración
        
        Args:
            days: Número de días desde hoy para expiración
            expiration_date: Fecha específica de expiración
        """
        if expiration_date:
            self.expires_at = expiration_date
        elif days:
            self.expires_at = datetime.utcnow() + timedelta(days=days)
    
    def check_expiration(self):
        """Verificar y marcar como expirado si corresponde"""
        if self.expires_at and self.expires_at <= datetime.utcnow():
            if not self.is_expired:
                self.is_expired = True
                self.add_usage_log("expired", {
                    "expiration_date": self.expires_at.isoformat()
                })
    
    def validate_for_document_type(self, document_type_id: int) -> bool:
        """
        Validar que el QR puede usarse para un tipo de documento específico
        
        Args:
            document_type_id: ID del tipo de documento
            
        Returns:
            bool: True si es válido para el tipo
        """
        return self.document_type_id == document_type_id and self.is_valid
    
    def get_qr_content(self) -> str:
        """
        Obtener el contenido que debe codificarse en el QR
        
        Returns:
            str: Contenido del QR (generalmente el qr_id)
        """
        # Por defecto, el QR contiene solo el ID
        # Pero podría extenderse para incluir más información
        return self.qr_id
    
    def create_qr_data_structure(self, additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Crear estructura de datos completa para el QR
        
        Args:
            additional_data: Datos adicionales para incluir
            
        Returns:
            dict: Estructura completa de datos
        """
        base_data = {
            "qr_id": self.qr_id,
            "document_type": self.document_type.code if self.document_type else None,
            "version": self.qr_version,
            "generated_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }
        
        if additional_data:
            base_data.update(additional_data)
        
        return base_data
    
    def can_be_reused(self) -> bool:
        """
        Verificar si el QR puede ser reutilizado
        (Por defecto no, pero configurable por tipo de documento)
        
        Returns:
            bool: True si puede reutilizarse
        """
        # Por ahora, los QR son de un solo uso
        # Esto podría configurarse por tipo de documento en el futuro
        return False
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """
        Obtener resumen del uso del QR
        
        Returns:
            dict: Resumen de uso
        """
        return {
            "qr_id": self.qr_id,
            "status": self.status,
            "is_valid": self.is_valid,
            "document_type": self.document_type.code if self.document_type else None,
            "created_at": self.created_at,
            "used_at": self.used_at,
            "expires_at": self.expires_at,
            "usage_attempts": self.usage_attempts,
            "associated_document": self.used_in_document_id,
            "generated_by": self.generated_by
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir QR a diccionario para APIs"""
        return {
            "id": self.id,
            "qr_id": self.qr_id,
            "document_type_id": self.document_type_id,
            "document_type_code": self.document_type.code if self.document_type else None,
            "status": self.status,
            "is_valid": self.is_valid,
            "is_used": self.is_used,
            "is_expired": self.is_expired,
            "is_revoked": self.is_revoked,
            "qr_data": self.qr_data_dict,
            "generation_config": self.generation_config_dict,
            "source_file": {
                "path": self.source_file_path,
                "name": self.source_file_name
            },
            "usage": {
                "attempts": self.usage_attempts,
                "log": self.usage_log_list
            },
            "dates": {
                "created_at": self.created_at,
                "used_at": self.used_at,
                "expires_at": self.expires_at,
                "revoked_at": self.revoked_at
            },
            "associations": {
                "generated_by": self.generated_by,
                "used_in_document_id": self.used_in_document_id
            }
        }