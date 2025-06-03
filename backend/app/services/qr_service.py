"""
Servicio de gestión de códigos QR
Lógica de negocio para operaciones CRUD y procesamiento de QR
"""
import logging
import os
import zipfile
import tempfile
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from fastapi import HTTPException, status, UploadFile

from ..models.qr_code import QRCode, QRCodeStatus
from ..models.document_type import DocumentType
from ..models.user import User
from ..models.document import Document
from ..schemas.qr_code import (
    QRCodeCreate,
    QRCodeBatchCreate,
    QRCodeUpdate,
    QRCodeFilter,
    QRCodeGenerationConfig,
    QRCodeValidation,
    QRCodeUse,
    QRCodeRevoke,
    QRCodeBulkAction
)
from ..config import get_settings
from ..utils.qr_processor import get_qr_processor, generate_unique_qr_id

# Configuración
settings = get_settings()
logger = logging.getLogger(__name__)


class QRService:
    """Servicio principal para gestión de códigos QR"""
    
    def __init__(self):
        """Inicializar el servicio de códigos QR"""
        self.qr_processor = get_qr_processor()
        
        logger.info("QRService inicializado")
    
    # === OPERACIONES CRUD ===
    
    def create_qr_code(
        self,
        qr_data: QRCodeCreate,
        user: User,
        db: Session
    ) -> QRCode:
        """
        Crear nuevo código QR
        
        Args:
            qr_data: Datos del código QR
            user: Usuario que crea el QR
            db: Sesión de base de datos
            
        Returns:
            QRCode: Código QR creado
        """
        try:
            logger.info(f"Creando código QR para tipo {qr_data.document_type_id} por usuario {user.id}")
            
            # Verificar tipo de documento
            document_type = db.query(DocumentType).filter(
                DocumentType.id == qr_data.document_type_id,
                DocumentType.is_active == True
            ).first()
            
            if not document_type:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Tipo de documento no encontrado o inactivo"
                )
            
            # Generar ID único si no se proporciona
            qr_id = qr_data.qr_id or generate_unique_qr_id()
            
            # Verificar que el QR ID no exista
            existing = db.query(QRCode).filter(QRCode.qr_id == qr_id).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya existe un código QR con ID: {qr_id}"
                )
            
            # Calcular fecha de expiración
            expires_at = None
            if qr_data.expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=qr_data.expires_in_days)
            
            # Crear código QR
            qr_code = QRCode(
                qr_id=qr_id,
                document_type_id=qr_data.document_type_id,
                generated_by=user.id,
                expires_at=expires_at,
                generation_config=qr_data.generation_config.dict() if qr_data.generation_config else {},
                notes=qr_data.notes
            )
            
            db.add(qr_code)
            db.commit()
            db.refresh(qr_code)
            
            # Actualizar estadísticas del tipo
            document_type.increment_qr_generated()
            user.increment_generations()
            db.commit()
            
            logger.info(f"Código QR creado: {qr_code.qr_id}")
            return qr_code
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creando código QR: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear código QR"
            )
    
    def create_qr_codes_batch(
        self,
        batch_data: QRCodeBatchCreate,
        user: User,
        db: Session
    ) -> List[QRCode]:
        """
        Crear múltiples códigos QR en lote
        
        Args:
            batch_data: Datos del lote
            user: Usuario que crea los QR
            db: Sesión de base de datos
            
        Returns:
            List[QRCode]: Lista de códigos QR creados
        """
        try:
            logger.info(f"Creando lote de {batch_data.quantity} códigos QR")
            
            # Verificar tipo de documento
            document_type = db.query(DocumentType).filter(
                DocumentType.id == batch_data.document_type_id,
                DocumentType.is_active == True
            ).first()
            
            if not document_type:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Tipo de documento no encontrado"
                )
            
            # Verificar límites
            if batch_data.quantity > 1000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Máximo 1000 códigos QR por lote"
                )
            
            # Calcular fecha de expiración
            expires_at = None
            if batch_data.expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=batch_data.expires_in_days)
            
            # Crear códigos QR
            created_qr_codes = []
            
            for i in range(batch_data.quantity):
                qr_id = generate_unique_qr_id()
                
                qr_code = QRCode(
                    qr_id=qr_id,
                    document_type_id=batch_data.document_type_id,
                    generated_by=user.id,
                    expires_at=expires_at,
                    generation_config=batch_data.generation_config.dict() if batch_data.generation_config else {},
                    notes=f"Lote #{i+1}" + (f" - {batch_data.notes}" if batch_data.notes else "")
                )
                
                db.add(qr_code)
                created_qr_codes.append(qr_code)
            
            # Commit en lote
            db.commit()
            
            # Actualizar estadísticas
            document_type.generated_count += batch_data.quantity
            user.increment_generations(batch_data.quantity)
            db.commit()
            
            logger.info(f"Lote de {len(created_qr_codes)} códigos QR creado")
            return created_qr_codes
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creando lote de QR: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear lote de códigos QR"
            )
    
    def get_qr_code_by_id(
        self,
        qr_id: str,
        user: User,
        db: Session
    ) -> QRCode:
        """
        Obtener código QR por ID
        
        Args:
            qr_id: ID del código QR
            user: Usuario que solicita
            db: Sesión de base de datos
            
        Returns:
            QRCode: Código QR encontrado
        """
        try:
            qr_code = db.query(QRCode).filter(QRCode.qr_id == qr_id).first()
            
            if not qr_code:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Código QR no encontrado"
                )
            
            # Verificar permisos de acceso
            if not self._check_qr_access(qr_code, user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tiene permisos para acceder a este código QR"
                )
            
            return qr_code
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo código QR: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error obteniendo código QR"
            )
    
    def update_qr_code(
        self,
        qr_id: str,
        update_data: QRCodeUpdate,
        user: User,
        db: Session
    ) -> QRCode:
        """
        Actualizar código QR
        
        Args:
            qr_id: ID del código QR
            update_data: Datos de actualización
            user: Usuario que actualiza
            db: Sesión de base de datos
            
        Returns:
            QRCode: Código QR actualizado
        """
        try:
            qr_code = self.get_qr_code_by_id(qr_id, user, db)
            
            # Verificar permisos de edición
            if not (user.is_admin or qr_code.generated_by == user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tiene permisos para editar este código QR"
                )
            
            # Solo permitir actualizar algunos campos
            if update_data.notes is not None:
                qr_code.notes = update_data.notes
            
            if update_data.expires_in_days is not None:
                if update_data.expires_in_days > 0:
                    qr_code.expires_at = datetime.utcnow() + timedelta(days=update_data.expires_in_days)
                else:
                    qr_code.expires_at = None
            
            if update_data.generation_config is not None:
                qr_code.generation_config = update_data.generation_config.dict()
            
            db.commit()
            db.refresh(qr_code)
            
            logger.info(f"Código QR actualizado: {qr_code.qr_id}")
            return qr_code
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error actualizando código QR: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar código QR"
            )
    
    def delete_qr_code(
        self,
        qr_id: str,
        user: User,
        db: Session,
        force: bool = False
    ) -> bool:
        """
        Eliminar código QR
        
        Args:
            qr_id: ID del código QR
            user: Usuario que elimina
            db: Sesión de base de datos
            force: Forzar eliminación
            
        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            qr_code = self.get_qr_code_by_id(qr_id, user, db)
            
            # Solo admins pueden eliminar
            if not user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo administradores pueden eliminar códigos QR"
                )
            
            # Verificar si está siendo usado
            if qr_code.is_used and not force:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se puede eliminar un código QR que ya fue usado"
                )
            
            # Verificar documentos asociados
            associated_docs = db.query(Document).filter(
                Document.qr_code_id == qr_code.qr_id
            ).count()
            
            if associated_docs > 0 and not force:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Hay {associated_docs} documentos asociados a este código QR"
                )
            
            db.delete(qr_code)
            db.commit()
            
            logger.info(f"Código QR eliminado: {qr_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error eliminando código QR: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar código QR"
            )
    
    # === BÚSQUEDA Y FILTROS ===
    
    def search_qr_codes(
        self,
        filters: QRCodeFilter,
        user: User,
        db: Session
    ) -> Tuple[List[QRCode], int]:
        """
        Buscar códigos QR con filtros
        
        Args:
            filters: Filtros de búsqueda
            user: Usuario que busca
            db: Sesión de base de datos
            
        Returns:
            Tuple[List[QRCode], int]: (códigos QR, total)
        """
        try:
            # Query base
            query = db.query(QRCode)
            
            # Filtrar por usuario si no es admin
            if not user.is_admin:
                query = query.filter(QRCode.generated_by == user.id)
            
            # Filtrar por tipo de documento si se especifica
            if document_type_id:
                query = query.filter(QRCode.document_type_id == document_type_id)
            
            # Estadísticas básicas
            total_generated = query.count()
            total_used = query.filter(QRCode.is_used == True).count()
            total_expired = query.filter(QRCode.is_expired == True).count()
            total_revoked = query.filter(QRCode.is_revoked == True).count()
            total_available = query.filter(
                and_(
                    QRCode.is_used == False,
                    QRCode.is_expired == False,
                    QRCode.is_revoked == False
                )
            ).count()
            
            # Calcular porcentajes
            usage_rate = (total_used / total_generated * 100) if total_generated > 0 else 0
            
            # Análisis temporal (últimos 30 días)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            generated_last_30_days = query.filter(QRCode.created_at >= thirty_days_ago).count()
            used_last_30_days = query.filter(
                and_(QRCode.is_used == True, QRCode.used_at >= thirty_days_ago)
            ).count()
            
            # Análisis por tipo de documento
            by_document_type = db.query(
                DocumentType.code,
                DocumentType.name,
                func.count(QRCode.id).label('total'),
                func.sum(func.case([(QRCode.is_used == True, 1)], else_=0)).label('used')
            ).join(QRCode).group_by(DocumentType.id, DocumentType.code, DocumentType.name).all()
            
            by_type_data = []
            for code, name, total, used in by_document_type:
                by_type_data.append({
                    "document_type_code": code,
                    "document_type_name": name,
                    "total_generated": total,
                    "total_used": used or 0,
                    "usage_rate": (used / total * 100) if total > 0 and used else 0
                })
            
            # QRs próximos a expirar (próximos 7 días)
            seven_days_ahead = datetime.utcnow() + timedelta(days=7)
            expiring_soon = query.filter(
                and_(
                    QRCode.expires_at.isnot(None),
                    QRCode.expires_at <= seven_days_ahead,
                    QRCode.is_used == False,
                    QRCode.is_revoked == False
                )
            ).count()
            
            return {
                "summary": {
                    "total_generated": total_generated,
                    "total_used": total_used,
                    "total_expired": total_expired,
                    "total_revoked": total_revoked,
                    "total_available": total_available,
                    "usage_rate": round(usage_rate, 2)
                },
                "status_distribution": {
                    "available": total_available,
                    "used": total_used,
                    "expired": total_expired,
                    "revoked": total_revoked
                },
                "temporal_analysis": {
                    "generated_last_30_days": generated_last_30_days,
                    "used_last_30_days": used_last_30_days,
                    "expiring_soon": expiring_soon
                },
                "by_document_type": by_type_data,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de QR: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener estadísticas de códigos QR"
            )
    
    # === LIMPIEZA Y MANTENIMIENTO ===
    
    def cleanup_expired_qr_codes(
        self,
        db: Session,
        auto_revoke: bool = True
    ) -> Dict[str, int]:
        """
        Limpiar códigos QR expirados
        
        Args:
            db: Sesión de base de datos
            auto_revoke: Revocar automáticamente los expirados
            
        Returns:
            dict: Resultado de la limpieza
        """
        try:
            current_time = datetime.utcnow()
            
            # Buscar QRs expirados que no estén marcados como expirados
            expired_qrs = db.query(QRCode).filter(
                and_(
                    QRCode.expires_at <= current_time,
                    QRCode.is_expired == False,
                    QRCode.is_used == False
                )
            ).all()
            
            expired_count = 0
            revoked_count = 0
            
            for qr_code in expired_qrs:
                # Marcar como expirado
                qr_code.is_expired = True
                expired_count += 1
                
                # Revocar si se especifica
                if auto_revoke and not qr_code.is_revoked:
                    qr_code.revoke("Expiración automática", None)
                    revoked_count += 1
            
            db.commit()
            
            logger.info(f"Limpieza completada: {expired_count} expirados, {revoked_count} revocados")
            
            return {
                "expired_count": expired_count,
                "revoked_count": revoked_count,
                "processed_at": current_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error en limpieza de QRs: {str(e)}")
            db.rollback()
            return {
                "expired_count": 0,
                "revoked_count": 0,
                "error": str(e)
            }
    
    def find_orphaned_qr_codes(self, db: Session) -> List[str]:
        """
        Encontrar códigos QR huérfanos (sin tipo de documento asociado válido)
        
        Args:
            db: Sesión de base de datos
            
        Returns:
            List[str]: Lista de IDs de QRs huérfanos
        """
        try:
            # Buscar QRs con tipos de documento inactivos o eliminados
            orphaned_qrs = db.query(QRCode.qr_id).outerjoin(DocumentType).filter(
                or_(
                    DocumentType.id.is_(None),
                    DocumentType.is_active == False
                )
            ).all()
            
            orphaned_ids = [qr_id[0] for qr_id in orphaned_qrs]
            
            logger.info(f"Encontrados {len(orphaned_ids)} códigos QR huérfanos")
            return orphaned_ids
            
        except Exception as e:
            logger.error(f"Error buscando QRs huérfanos: {str(e)}")
            return []
    
    # === MÉTODOS PRIVADOS ===
    
    def _check_qr_access(self, qr_code: QRCode, user: User) -> bool:
        """
        Verificar si el usuario puede acceder al código QR
        
        Args:
            qr_code: Código QR a verificar
            user: Usuario que solicita acceso
            
        Returns:
            bool: True si puede acceder
        """
        # Administradores tienen acceso a todo
        if user.is_admin:
            return True
        
        # El generador puede ver sus QRs
        if qr_code.generated_by == user.id:
            return True
        
        # Los operadores pueden ver QRs de su organización
        if user.is_operator:
            return True
        
        return False


# === INSTANCIA GLOBAL ===

# Instancia singleton del servicio
_qr_service = None

def get_qr_service() -> QRService:
    """
    Obtener instancia del servicio de códigos QR
    
    Returns:
        QRService: Instancia del servicio
    """
    global _qr_service
    if _qr_service is None:
        _qr_service = QRService()
    return _qr_service


# === FUNCIONES DE UTILIDAD ===

def validate_qr_id_format(qr_id: str) -> bool:
    """
    Validar formato de ID de código QR
    
    Args:
        qr_id: ID a validar
        
    Returns:
        bool: True si es válido
    """
    import re
    # QR ID debe ser UUID v4 o formato personalizado
    uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
    return bool(re.match(uuid_pattern, qr_id, re.IGNORECASE))


def generate_qr_data_structure(
    qr_id: str,
    document_type_code: str,
    additional_data: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generar estructura de datos estándar para QR
    
    Args:
        qr_id: ID del código QR
        document_type_code: Código del tipo de documento
        additional_data: Datos adicionales
        
    Returns:
        str: Datos estructurados como JSON
    """
    import json
    
    data_structure = {
        "qr_id": qr_id,
        "document_type": document_type_code,
        "version": "1.0",
        "generated_at": datetime.utcnow().isoformat(),
        "system": "SGD_Web"
    }
    
    if additional_data:
        data_structure.update(additional_data)
    
    return json.dumps(data_structure, ensure_ascii=False)


def parse_qr_data_structure(qr_content: str) -> Dict[str, Any]:
    """
    Parsear estructura de datos de QR
    
    Args:
        qr_content: Contenido del QR
        
    Returns:
        dict: Datos parseados
    """
    import json
    
    try:
        # Intentar parsear como JSON
        data = json.loads(qr_content)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    
    # Si no es JSON, asumir que es un ID simple
    return {
        "qr_id": qr_content,
        "version": "simple",
        "system": "unknown"
    }


async def batch_generate_qr_codes(
    document_type_id: int,
    quantity: int,
    user: User,
    db: Session,
    expires_in_days: Optional[int] = None,
    generation_config: Optional[QRCodeGenerationConfig] = None
) -> List[QRCode]:
    """
    Función de conveniencia para generación en lote
    
    Args:
        document_type_id: ID del tipo de documento
        quantity: Cantidad a generar
        user: Usuario que genera
        db: Sesión de base de datos
        expires_in_days: Días hasta expiración
        generation_config: Configuración de generación
        
    Returns:
        List[QRCode]: Códigos QR generados
    """
    qr_service = get_qr_service()
    
    batch_data = QRCodeBatchCreate(
        document_type_id=document_type_id,
        quantity=quantity,
        expires_in_days=expires_in_days,
        generation_config=generation_config
    )
    
    return qr_service.create_qr_codes_batch(batch_data, user, db)


def check_qr_codes_health(db: Session) -> Dict[str, Any]:
    """
    Verificar estado de salud de los códigos QR
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        dict: Reporte de salud
    """
    try:
        qr_service = get_qr_service()
        
        # Estadísticas básicas
        total_qrs = db.query(QRCode).count()
        active_qrs = db.query(QRCode).filter(
            and_(
                QRCode.is_used == False,
                QRCode.is_expired == False,
                QRCode.is_revoked == False
            )
        ).count()
        
        # Buscar problemas
        issues = []
        warnings = []
        
        # QRs huérfanos
        orphaned_qrs = qr_service.find_orphaned_qr_codes(db)
        if orphaned_qrs:
            issues.append(f"{len(orphaned_qrs)} códigos QR huérfanos encontrados")
        
        # QRs expirados no marcados
        current_time = datetime.utcnow()
        unmarked_expired = db.query(QRCode).filter(
            and_(
                QRCode.expires_at <= current_time,
                QRCode.is_expired == False
            )
        ).count()
        
        if unmarked_expired > 0:
            warnings.append(f"{unmarked_expired} códigos QR expirados no marcados")
        
        # QRs próximos a expirar
        seven_days_ahead = current_time + timedelta(days=7)
        expiring_soon = db.query(QRCode).filter(
            and_(
                QRCode.expires_at.isnot(None),
                QRCode.expires_at <= seven_days_ahead,
                QRCode.is_used == False,
                QRCode.is_revoked == False
            )
        ).count()
        
        if expiring_soon > 0:
            warnings.append(f"{expiring_soon} códigos QR expiran en los próximos 7 días")
        
        # Determinar estado general
        status = "healthy"
        if issues:
            status = "unhealthy"
        elif warnings:
            status = "warning"
        
        return {
            "status": status,
            "total_qr_codes": total_qrs,
            "active_qr_codes": active_qrs,
            "issues": issues,
            "warnings": warnings,
            "recommendations": [
                "Ejecutar limpieza de códigos QR expirados",
                "Revisar códigos QR huérfanos",
                "Monitorear códigos próximos a expirar"
            ] if issues or warnings else [],
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error verificando salud de QRs: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "checked_at": datetime.utcnow().isoformat()
        }


async def cleanup_qr_temp_files(max_age_hours: int = 24) -> Dict[str, Any]:
    """
    Limpiar archivos temporales de códigos QR
    
    Args:
        max_age_hours: Edad máxima en horas
        
    Returns:
        dict: Resultado de la limpieza
    """
    try:
        import glob
        from pathlib import Path
        
        temp_path = settings.TEMP_PATH
        current_time = datetime.now()
        deleted_count = 0
        total_size = 0
        
        # Buscar archivos QR temporales
        qr_patterns = [
            os.path.join(temp_path, "qr_*.png"),
            os.path.join(temp_path, "qr_*.jpg"),
            os.path.join(temp_path, "qr_*.jpeg"),
            os.path.join(temp_path, "qr_*.svg"),
            os.path.join(temp_path, "qr_batch_*.zip")
        ]
        
        for pattern in qr_patterns:
            for file_path in glob.glob(pattern):
                try:
                    file_stat = os.stat(file_path)
                    file_age = current_time - datetime.fromtimestamp(file_stat.st_mtime)
                    
                    if file_age.total_seconds() > (max_age_hours * 3600):
                        file_size = file_stat.st_size
                        os.remove(file_path)
                        deleted_count += 1
                        total_size += file_size
                        
                except Exception as e:
                    logger.warning(f"Error eliminando archivo temporal QR {file_path}: {str(e)}")
                    continue
        
        size_mb = round(total_size / (1024 * 1024), 2)
        
        logger.info(f"Limpieza de archivos QR temporales: {deleted_count} archivos ({size_mb} MB)")
        
        return {
            "deleted_files": deleted_count,
            "freed_size_mb": size_mb,
            "max_age_hours": max_age_hours,
            "cleaned_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error limpiando archivos temporales QR: {str(e)}")
        return {
            "deleted_files": 0,
            "freed_size_mb": 0,
            "error": str(e),
            "cleaned_at": datetime.utcnow().isoformat()
        }
            
        # Filtrar por usuario si no es admin
        if not user.is_admin:
            query = query.filter(QRCode.generated_by == user.id)
        
        # Aplicar filtros
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(QRCode.qr_id.ilike(search_term))
        
        if filters.document_type_id:
            query = query.filter(QRCode.document_type_id == filters.document_type_id)
        
        if filters.status:
            if filters.status == "available":
                query = query.filter(
                    and_(
                        QRCode.is_used == False,
                        QRCode.is_expired == False,
                        QRCode.is_revoked == False
                    )
                )
            elif filters.status == "used":
                query = query.filter(QRCode.is_used == True)
            elif filters.status == "expired":
                query = query.filter(QRCode.is_expired == True)
            elif filters.status == "revoked":
                query = query.filter(QRCode.is_revoked == True)
        
        if filters.is_valid is not None:
            if filters.is_valid:
                query = query.filter(
                    and_(
                        QRCode.is_used == False,
                        QRCode.is_expired == False,
                        QRCode.is_revoked == False
                    )
                )
            else:
                query = query.filter(
                    or_(
                        QRCode.is_used == True,
                        QRCode.is_expired == True,
                        QRCode.is_revoked == True
                    )
                )
        
        if filters.generated_by:
            query = query.filter(QRCode.generated_by == filters.generated_by)
        
        if filters.created_after:
            query = query.filter(QRCode.created_at >= filters.created_after)
        
        if filters.created_before:
            query = query.filter(QRCode.created_at <= filters.created_before)
        
        if filters.expires_before:
            query = query.filter(QRCode.expires_at <= filters.expires_before)
        
        # Contar total
        total = query.count()
        
        # Aplicar ordenamiento
        if filters.sort_by == "qr_id":
            order_column = QRCode.qr_id
        elif filters.sort_by == "used_at":
            order_column = QRCode.used_at
        elif filters.sort_by == "expires_at":
            order_column = QRCode.expires_at
        elif filters.sort_by == "usage_attempts":
            order_column = QRCode.usage_attempts
        else:  # created_at por defecto
            order_column = QRCode.created_at
        
        if filters.sort_order == "desc":
            order_column = desc(order_column)
        else:
            order_column = asc(order_column)
        
        query = query.order_by(order_column)
        
        # Aplicar paginación
        offset = (filters.page - 1) * filters.page_size
        qr_codes = query.offset(offset).limit(filters.page_size).all()
        
        return qr_codes, total
        
    except Exception as e:
        logger.error(f"Error buscando códigos QR: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en búsqueda de códigos QR"
        )

# === OPERACIONES DE QR ===

def validate_qr_code(
    self,
    validation_data: QRCodeValidation,
    user: User,
    db: Session
) -> Tuple[bool, List[str], Optional[QRCode]]:
    """
    Validar código QR
    
    Args:
        validation_data: Datos de validación
        user: Usuario que valida
        db: Sesión de base de datos
        
    Returns:
        Tuple[bool, List[str], Optional[QRCode]]: (es_válido, errores, qr_code)
    """
    try:
        # Buscar código QR
        qr_code = db.query(QRCode).filter(
            QRCode.qr_id == validation_data.qr_id
        ).first()
        
        if not qr_code:
            return False, ["Código QR no encontrado"], None
        
        # Verificar tipo de documento si se especifica
        if validation_data.document_type_id:
            if qr_code.document_type_id != validation_data.document_type_id:
                return False, ["Código QR no pertenece al tipo de documento especificado"], qr_code
        
        # Validar estado
        errors = []
        if qr_code.is_used:
            errors.append("Código QR ya utilizado")
        if qr_code.is_expired:
            errors.append("Código QR expirado")
        if qr_code.is_revoked:
            errors.append("Código QR revocado")
        if qr_code.expires_at and qr_code.expires_at <= datetime.utcnow():
            errors.append("Código QR ha expirado")
        
        # Registrar intento de validación
        qr_code.add_usage_log("validation_attempt", {
            "user_id": user.id,
            "document_type_id": validation_data.document_type_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        db.commit()
        
        is_valid = len(errors) == 0
        return is_valid, errors, qr_code
        
    except Exception as e:
        logger.error(f"Error validando código QR: {str(e)}")
        return False, [f"Error interno: {str(e)}"], None

def use_qr_code(
    self,
    use_data: QRCodeUse,
    user: User,
    db: Session
) -> QRCode:
    """
    Marcar código QR como usado
    
    Args:
        use_data: Datos de uso
        user: Usuario que usa el QR
        db: Sesión de base de datos
        
    Returns:
        QRCode: Código QR actualizado
    """
    try:
        qr_code = self.get_qr_code_by_id(use_data.qr_id, user, db)
        
        # Validar que esté disponible
        if not qr_code.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Código QR no válido: {qr_code.status}"
            )
        
        # Marcar como usado
        qr_code.mark_as_used(use_data.document_id, user.id)
        db.commit()
        db.refresh(qr_code)
        
        logger.info(f"Código QR usado: {qr_code.qr_id} para documento {use_data.document_id}")
        return qr_code
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error usando código QR: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al usar código QR"
        )

def revoke_qr_code(
    self,
    revoke_data: QRCodeRevoke,
    user: User,
    db: Session
) -> QRCode:
    """
    Revocar código QR
    
    Args:
        revoke_data: Datos de revocación
        user: Usuario que revoca
        db: Sesión de base de datos
        
    Returns:
        QRCode: Código QR revocado
    """
    try:
        qr_code = self.get_qr_code_by_id(revoke_data.qr_id, user, db)
        
        # Solo admins y operadores pueden revocar
        if not user.is_operator:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para revocar códigos QR"
            )
        
        # Revocar código
        qr_code.revoke(revoke_data.reason, user.id)
        db.commit()
        db.refresh(qr_code)
        
        logger.info(f"Código QR revocado: {qr_code.qr_id} por {revoke_data.reason}")
        return qr_code
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revocando código QR: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al revocar código QR"
        )

# === OPERACIONES EN LOTE ===

def bulk_action_qr_codes(
    self,
    action_data: QRCodeBulkAction,
    user: User,
    db: Session
) -> Dict[str, Any]:
    """
    Ejecutar acción en lote sobre códigos QR
    
    Args:
        action_data: Datos de la acción en lote
        user: Usuario que ejecuta la acción
        db: Sesión de base de datos
        
    Returns:
        dict: Resultado de la operación
    """
    try:
        if not user.is_operator:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para operaciones en lote"
            )
        
        # Obtener códigos QR
        qr_codes = db.query(QRCode).filter(
            QRCode.qr_id.in_(action_data.qr_ids)
        ).all()
        
        success_count = 0
        error_count = 0
        errors = []
        
        for qr_code in qr_codes:
            try:
                if action_data.action == "revoke":
                    qr_code.revoke(action_data.reason or "Revocación en lote", user.id)
                    success_count += 1
                elif action_data.action == "delete":
                    if user.is_admin:
                        db.delete(qr_code)
                        success_count += 1
                    else:
                        errors.append({
                            "qr_id": qr_code.qr_id,
                            "error": "Sin permisos para eliminar"
                        })
                        error_count += 1
                elif action_data.action == "extend_expiry":
                    if action_data.days:
                        qr_code.expires_at = datetime.utcnow() + timedelta(days=action_data.days)
                        success_count += 1
                    else:
                        errors.append({
                            "qr_id": qr_code.qr_id,
                            "error": "Días de extensión no especificados"
                        })
                        error_count += 1
                else:
                    errors.append({
                        "qr_id": qr_code.qr_id,
                        "error": f"Acción no soportada: {action_data.action}"
                    })
                    error_count += 1
                    
            except Exception as e:
                errors.append({
                    "qr_id": qr_code.qr_id,
                    "error": str(e)
                })
                error_count += 1
        
        # Commit cambios
        if success_count > 0:
            db.commit()
        
        logger.info(f"Acción en lote '{action_data.action}': {success_count} exitosas, {error_count} errores")
        
        return {
            "action": action_data.action,
            "requested_count": len(action_data.qr_ids),
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en acción en lote: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error ejecutando acción en lote"
        )

# === GENERACIÓN DE ARCHIVOS ===

async def generate_qr_images(
    self,
    qr_ids: List[str],
    format: str = "PNG",
    config: Optional[QRCodeGenerationConfig] = None
) -> List[str]:
    """
    Generar imágenes de códigos QR
    
    Args:
        qr_ids: Lista de IDs de códigos QR
        format: Formato de imagen
        config: Configuración de generación
        
    Returns:
        List[str]: Lista de rutas de archivos generados
    """
    try:
        generated_files = []
        
        for qr_id in qr_ids:
            try:
                # Generar imagen
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = f"qr_{qr_id}_{timestamp}.{format.lower()}"
                output_path = os.path.join(settings.TEMP_PATH, filename)
                
                image_path = self.qr_processor.generate_qr_code(
                    data=qr_id,
                    config=config.dict() if config else None,
                    output_path=output_path,
                    format=format
                )
                
                generated_files.append(image_path)
                
            except Exception as e:
                logger.error(f"Error generando imagen para QR {qr_id}: {str(e)}")
                continue
        
        logger.info(f"Generadas {len(generated_files)} imágenes QR")
        return generated_files
        
    except Exception as e:
        logger.error(f"Error generando imágenes QR: {str(e)}")
        return []

async def create_qr_batch_zip(
    self,
    qr_ids: List[str],
    format: str = "PNG",
    config: Optional[QRCodeGenerationConfig] = None
) -> str:
    """
    Crear archivo ZIP con múltiples códigos QR
    
    Args:
        qr_ids: Lista de IDs de códigos QR
        format: Formato de las imágenes
        config: Configuración de generación
        
    Returns:
        str: Ruta del archivo ZIP
    """
    try:
        # Generar imágenes individuales
        image_files = await self.generate_qr_images(qr_ids, format, config)
        
        if not image_files:
            raise Exception("No se pudieron generar imágenes QR")
        
        # Crear archivo ZIP
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"qr_batch_{timestamp}.zip"
        zip_path = os.path.join(settings.TEMP_PATH, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for image_path in image_files:
                if os.path.exists(image_path):
                    # Agregar al ZIP con nombre limpio
                    filename = os.path.basename(image_path)
                    zipf.write(image_path, filename)
        
        # Limpiar archivos temporales
        for image_path in image_files:
            try:
                os.remove(image_path)
            except:
                pass
        
        logger.info(f"Archivo ZIP creado: {zip_path}")
        return zip_path
        
    except Exception as e:
        logger.error(f"Error creando ZIP de códigos QR: {str(e)}")
        raise

# === ESTADÍSTICAS ===

def get_qr_codes_stats(
        self,
        user: User,
        db: Session,
        document_type_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Obtener estadísticas de códigos QR
        
        Args:
            user: Usuario que solicita
            db: Sesión de base de datos
            document_type_id: Filtrar por tipo de documento
            
        Returns:
            dict: Estadísticas de códigos QR
        """
        try:
            # Query base
            query = db.query(QRCode)
            
            # Filtrar por usuario si no es admin
            if not user.is_admin:
                query = query.filter(QRCode.generated_by == user.id)
            
            # Filtrar por tipo de documento si se especifica
            if document_type_id:
                query = query.filter(QRCode.document_type_id == document_type_id)
            
            # Estadísticas básicas
            total_generated = query.count()
            total_used = query.filter(QRCode.is_used == True).count()
            total_expired = query.filter(QRCode.is_expired == True).count()
            total_revoked = query.filter(QRCode.is_revoked == True).count()
            total_available = query.filter(
                and_(
                    QRCode.is_used == False,
                    QRCode.is_expired == False,
                    QRCode.is_revoked == False
                )
            ).count()
            
            # Calcular porcentajes
            usage_rate = (total_used / total_generated * 100) if total_generated > 0 else 0
            
            # Análisis temporal (últimos 30 días)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            generated_last_30_days = query.filter(QRCode.created_at >= thirty_days_ago).count()
            used_last_30_days = query.filter(
                and_(QRCode.is_used == True, QRCode.used_at >= thirty_days_ago)
            ).count()
            
            # Análisis por tipo de documento
            by_document_type = db.query(
                DocumentType.code,
                DocumentType.name,
                func.count(QRCode.id).label('total'),
                func.sum(func.case([(QRCode.is_used == True, 1)], else_=0)).label('used')
            ).join(QRCode).group_by(DocumentType.id, DocumentType.code, DocumentType.name).all()
            
            by_type_data = []
            for code, name, total, used in by_document_type:
                by_type_data.append({
                    "document_type_code": code,
                    "document_type_name": name,
                    "total_generated": total,
                    "total_used": used or 0,
                    "usage_rate": (used / total * 100) if total > 0 and used else 0
                })
            
            # QRs próximos a expirar (próximos 7 días)
            seven_days_ahead = datetime.utcnow() + timedelta(days=7)
            expiring_soon = query.filter(
                and_(
                    QRCode.expires_at.isnot(None),
                    QRCode.expires_at <= seven_days_ahead,
                    QRCode.is_used == False,
                    QRCode.is_revoked == False
                )
            ).count()
            
            return {
                "summary": {
                    "total_generated": total_generated,
                    "total_used": total_used,
                    "total_expired": total_expired,
                    "total_revoked": total_revoked,
                    "total_available": total_available,
                    "usage_rate": round(usage_rate, 2)
                },
                "status_distribution": {
                    "available": total_available,
                    "used": total_used,
                    "expired": total_expired,
                    "revoked": total_revoked
                },
                "temporal_analysis": {
                    "generated_last_30_days": generated_last_30_days,
                    "used_last_30_days": used_last_30_days,
                    "expiring_soon": expiring_soon
                },
                "by_document_type": by_type_data,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de QR: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener estadísticas de códigos QR"
            )