
"""
Modelo de Usuario para SGD Web
Integrado con Microsoft 365 / Azure AD
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
import bcrypt

from ..database import Base


class UserRole(PyEnum):
    """Roles disponibles en el sistema"""
    ADMIN = "admin"           # Acceso completo al sistema
    OPERATOR = "operator"     # Puede generar, registrar y buscar documentos
    VIEWER = "viewer"         # Solo puede buscar y ver documentos
    

class UserStatus(PyEnum):
    """Estados del usuario"""
    ACTIVE = "active"         # Usuario activo
    INACTIVE = "inactive"     # Usuario desactivado
    PENDING = "pending"       # Primer acceso pendiente
    SUSPENDED = "suspended"   # Usuario suspendido temporalmente


class User(Base):
    """
    Modelo de Usuario integrado con Microsoft 365
    
    Los usuarios se autentican únicamente con sus cuentas corporativas de M365.
    No se almacenan contraseñas locales.
    """
    __tablename__ = "users"
    
    # === CAMPOS PRINCIPALES ===
    id = Column(Integer, primary_key=True, index=True)
    
    # Identificación de Microsoft
    azure_id = Column(String(255), unique=True, nullable=True, index=True)  # Nullable para usuarios locales
    email = Column(String(100), unique=True, nullable=False, index=True)

    # Autenticación local (opcional, para modo demo/desarrollo)
    password_hash = Column(String(255), nullable=True)  # Solo para usuarios locales
    is_local_user = Column(Boolean, default=False)  # Distinguir usuarios locales de M365
    
    # Información del usuario (sincronizada desde M365)
    name = Column(String(200), nullable=False)
    given_name = Column(String(100))  # Nombre
    surname = Column(String(100))     # Apellido
    display_name = Column(String(200))
    
    # Información organizacional
    department = Column(String(100))
    job_title = Column(String(100))
    office_location = Column(String(100))
    company_name = Column(String(100))
    
    # === CONFIGURACIÓN DEL SISTEMA ===
    role = Column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.VIEWER,
        index=True
    )

    status = Column(
        Enum(UserStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserStatus.PENDING,
        index=True
    )
    
    # === PREFERENCIAS Y CONFIGURACIÓN ===
    # Idioma preferido
    preferred_language = Column(String(10), default="es")
    
    # Zona horaria
    timezone = Column(String(50), default="America/Bogota")
    
    # Preferencias de notificaciones
    email_notifications = Column(Boolean, default=True)
    
    # Configuración de la interfaz
    theme_preference = Column(String(20), default="light")  # light, dark, auto
    
    # === CAMPOS DE AUDITORÍA ===
    # Fechas importantes
    first_login = Column(DateTime)
    last_login = Column(DateTime)
    last_activity = Column(DateTime)
    
    # Token info (para invalidar sesiones)
    last_token_issued = Column(DateTime)
    
    # Estadísticas de uso
    login_count = Column(Integer, default=0)
    documents_uploaded = Column(Integer, default=0)
    documents_generated = Column(Integer, default=0)
    
    # === CAMPOS DE SISTEMA ===
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps automáticos
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # === INFORMACIÓN ADICIONAL ===
    # Notas del administrador
    admin_notes = Column(Text)
    
    # Información de contacto adicional
    phone = Column(String(20))
    mobile_phone = Column(String(20))
    
    # === RELACIONES ===
    # Documentos subidos por este usuario
    uploaded_documents = relationship(
        "Document", 
        back_populates="uploaded_by_user",
        foreign_keys="Document.uploaded_by"
    )
    
    # QR codes generados por este usuario
    generated_qr_codes = relationship(
        "QRCode",
        back_populates="generated_by_user"
    )
    
    # Tipos de documento creados (solo admins)
    created_document_types = relationship(
        "DocumentType",
        back_populates="created_by_user"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}')>"
    
    # === MÉTODOS DE UTILIDAD ===
    
    @property
    def full_name(self) -> str:
        """Obtener nombre completo del usuario"""
        if self.given_name and self.surname:
            return f"{self.given_name} {self.surname}"
        return self.name or self.display_name or self.email
    
    @property
    def initials(self) -> str:
        """Obtener iniciales del usuario"""
        if self.given_name and self.surname:
            return f"{self.given_name[0]}{self.surname[0]}".upper()
        elif self.name:
            parts = self.name.split()
            if len(parts) >= 2:
                return f"{parts[0][0]}{parts[1][0]}".upper()
            return self.name[0].upper()
        return self.email[0].upper()
    
    @property
    def is_admin(self) -> bool:
        """Verificar si el usuario es administrador"""
        return self.role == UserRole.ADMIN
    
    @property
    def is_operator(self) -> bool:
        """Verificar si el usuario es operador o superior"""
        return self.role in [UserRole.ADMIN, UserRole.OPERATOR]
    
    @property
    def can_upload(self) -> bool:
        """Verificar si puede subir documentos"""
        return self.role in [UserRole.ADMIN, UserRole.OPERATOR]
    
    @property
    def can_generate(self) -> bool:
        """Verificar si puede generar documentos"""
        return self.role in [UserRole.ADMIN, UserRole.OPERATOR]
    
    @property
    def can_manage_types(self) -> bool:
        """Verificar si puede gestionar tipos de documento"""
        return self.role == UserRole.ADMIN
    
    @property
    def can_manage_users(self) -> bool:
        """Verificar si puede gestionar usuarios"""
        return self.role == UserRole.ADMIN

    @property
    def permissions(self) -> dict:
        """Obtener permisos del usuario como diccionario"""
        return {
            "can_upload": self.can_upload,
            "can_generate": self.can_generate,
            "can_manage_types": self.can_manage_types,
            "can_manage_users": self.can_manage_users
        }

    @property
    def stats(self) -> dict:
        """Obtener estadísticas del usuario como diccionario"""
        return {
            "login_count": self.login_count or 0,
            "documents_uploaded": self.documents_uploaded or 0,
            "documents_generated": self.documents_generated or 0,
            "last_login": self.last_login,
            "last_activity": self.last_activity
        }

    def update_last_login(self):
        """Actualizar timestamp de último login"""
        now = datetime.utcnow()
        if not self.first_login:
            self.first_login = now
            self.status = UserStatus.ACTIVE
        self.last_login = now
        self.last_activity = now
        self.login_count += 1
    
    def update_activity(self):
        """Actualizar timestamp de última actividad"""
        self.last_activity = datetime.utcnow()
    
    def increment_uploads(self):
        """Incrementar contador de documentos subidos"""
        self.documents_uploaded += 1
        self.update_activity()
    
    def increment_generations(self):
        """Incrementar contador de documentos generados"""
        self.documents_generated += 1
        self.update_activity()
    
    def update_from_microsoft(self, microsoft_user_data: dict):
        """
        Actualizar información del usuario desde Microsoft Graph API
        
        Args:
            microsoft_user_data: Datos del usuario desde Microsoft Graph
        """
        # Información básica
        self.name = microsoft_user_data.get("displayName", self.name)
        self.display_name = microsoft_user_data.get("displayName", self.display_name)
        self.given_name = microsoft_user_data.get("givenName", self.given_name)
        self.surname = microsoft_user_data.get("surname", self.surname)
        
        # Información organizacional
        self.department = microsoft_user_data.get("department", self.department)
        self.job_title = microsoft_user_data.get("jobTitle", self.job_title)
        self.office_location = microsoft_user_data.get("officeLocation", self.office_location)
        self.company_name = microsoft_user_data.get("companyName", self.company_name)
        
        # Información de contacto
        self.phone = microsoft_user_data.get("businessPhones", [None])[0] or self.phone
        self.mobile_phone = microsoft_user_data.get("mobilePhone", self.mobile_phone)
        
        # Preferencias
        preferred_lang = microsoft_user_data.get("preferredLanguage")
        if preferred_lang:
            self.preferred_language = preferred_lang[:2].lower()  # Solo código de idioma
    
    def deactivate(self, reason: str = None):
        """
        Desactivar usuario
        
        Args:
            reason: Razón de la desactivación
        """
        self.is_active = False
        self.status = UserStatus.INACTIVE
        if reason:
            self.admin_notes = f"{self.admin_notes or ''}\n[{datetime.utcnow()}] Desactivado: {reason}".strip()
    
    def reactivate(self):
        """Reactivar usuario"""
        self.is_active = True
        self.status = UserStatus.ACTIVE
        self.admin_notes = f"{self.admin_notes or ''}\n[{datetime.utcnow()}] Reactivado".strip()
    
    def suspend(self, reason: str = None):
        """
        Suspender usuario temporalmente

        Args:
            reason: Razón de la suspensión
        """
        self.status = UserStatus.SUSPENDED
        if reason:
            self.admin_notes = f"{self.admin_notes or ''}\n[{datetime.utcnow()}] Suspendido: {reason}".strip()

    def set_password(self, password: str):
        """
        Establecer contraseña para usuario local

        Args:
            password: Contraseña en texto plano
        """
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.is_local_user = True

    def verify_password(self, password: str) -> bool:
        """
        Verificar contraseña para usuario local

        Args:
            password: Contraseña en texto plano a verificar

        Returns:
            bool: True si la contraseña es correcta
        """
        if not self.password_hash or not self.is_local_user:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def to_dict(self) -> dict:
        """Convertir usuario a diccionario para APIs"""
        return {
            "id": self.id,
            "azure_id": self.azure_id,
            "email": self.email,
            "name": self.full_name,
            "given_name": self.given_name,
            "surname": self.surname,
            "department": self.department,
            "job_title": self.job_title,
            "role": self.role.value,
            "status": self.status.value,
            "is_active": self.is_active,
            "initials": self.initials,
            "last_login": self.last_login,
            "created_at": self.created_at,
            "permissions": {
                "can_upload": self.can_upload,
                "can_generate": self.can_generate,
                "can_manage_types": self.can_manage_types,
                "can_manage_users": self.can_manage_users,
            }
        }