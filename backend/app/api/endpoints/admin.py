"""
Endpoints de administración
Gestión de estadísticas y estado del sistema
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ...database import get_db
from ...api.deps import get_current_user, require_admin
from ...models.user import User
from ...models.document import Document
from ...models.document_type import DocumentType
from ...models.qr_code import QRCode

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status", summary="Estado del sistema (Admin)")
async def get_admin_status(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Obtener estado general del sistema para el panel de administración
    Requiere rol de administrador
    """
    try:
        # Contar usuarios activos
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()

        # Contar documentos
        total_documents = db.query(Document).count()

        # Contar tipos de documento
        total_document_types = db.query(DocumentType).count()

        # Contar QR codes
        total_qr_codes = db.query(QRCode).count()
        used_qr_codes = db.query(QRCode).filter(QRCode.is_used == True).count()

        # Estado general
        return {
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "healthy": True,
                "version": "1.0.0",
                "environment": "production"
            },
            "counts": {
                "users": {
                    "total": total_users,
                    "active": active_users,
                    "inactive": total_users - active_users
                },
                "documents": {
                    "total": total_documents
                },
                "document_types": {
                    "total": total_document_types
                },
                "qr_codes": {
                    "total": total_qr_codes,
                    "used": used_qr_codes,
                    "available": total_qr_codes - used_qr_codes
                }
            }
        }

    except Exception as e:
        logger.error(f"Error obteniendo estado del sistema: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener estado del sistema"
        )


@router.get("/stats", summary="Estadísticas del sistema (Admin)")
async def get_admin_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Obtener estadísticas detalladas del sistema
    Requiere rol de administrador
    """
    try:
        # Estadísticas de documentos por mes (últimos 6 meses)
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        documents_by_month = db.query(
            func.date_trunc('month', Document.created_at).label('month'),
            func.count(Document.id).label('count')
        ).filter(
            Document.created_at >= six_months_ago
        ).group_by(
            func.date_trunc('month', Document.created_at)
        ).all()

        # Documentos por tipo
        documents_by_type = db.query(
            DocumentType.name,
            func.count(Document.id).label('count')
        ).join(
            Document, Document.document_type_id == DocumentType.id
        ).group_by(
            DocumentType.name
        ).all()

        # Usuarios por rol
        users_by_role = db.query(
            User.role,
            func.count(User.id).label('count')
        ).group_by(
            User.role
        ).all()

        # Actividad reciente (últimos 30 días)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_documents = db.query(Document).filter(
            Document.created_at >= thirty_days_ago
        ).count()

        recent_users = db.query(User).filter(
            User.created_at >= thirty_days_ago
        ).count()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "period": {
                "start": six_months_ago.isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "documents": {
                "by_month": [
                    {
                        "month": row.month.isoformat() if row.month else None,
                        "count": row.count
                    }
                    for row in documents_by_month
                ],
                "by_type": [
                    {
                        "type": row.name,
                        "count": row.count
                    }
                    for row in documents_by_type
                ],
                "recent_30_days": recent_documents
            },
            "users": {
                "by_role": [
                    {
                        "role": row.role,
                        "count": row.count
                    }
                    for row in users_by_role
                ],
                "recent_30_days": recent_users
            }
        }

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas del sistema: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener estadísticas del sistema"
        )
