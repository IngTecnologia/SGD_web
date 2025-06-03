"""
Endpoints para búsqueda avanzada de documentos
Búsqueda por texto completo, filtros y análisis
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text

from ...database import get_database
from ...config import get_settings
from ...models.user import User
from ...models.document import Document
from ...models.document_type import DocumentType
from ...models.qr_code import QRCode
from ...schemas.document import (
    DocumentSummary,
    DocumentFilter,
    DocumentListResponse
)
from ..deps import (
    get_current_user,
    PaginationParams,
    get_request_logger
)

# Configuración
settings = get_settings()
logger = logging.getLogger(__name__)

# Router
router = APIRouter()


# === ESQUEMAS PARA BÚSQUEDA ===

class SearchRequest:
    """Esquema para solicitud de búsqueda"""
    def __init__(
        self,
        query: str,
        search_type: str = "all",
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "relevance",
        sort_order: str = "desc"
    ):
        self.query = query
        self.search_type = search_type  # all, documents, qr_codes, people
        self.filters = filters or {}
        self.sort_by = sort_by
        self.sort_order = sort_order


class SearchResult:
    """Esquema para resultado de búsqueda"""
    def __init__(
        self,
        type: str,
        id: int,
        title: str,
        description: str,
        relevance_score: float,
        metadata: Dict[str, Any],
        url: str
    ):
        self.type = type
        self.id = id
        self.title = title
        self.description = description
        self.relevance_score = relevance_score
        self.metadata = metadata
        self.url = url


class SearchResponse:
    """Esquema para respuesta de búsqueda"""
    def __init__(
        self,
        query: str,
        total_results: int,
        search_time_ms: int,
        results: List[SearchResult],
        facets: Dict[str, Any],
        suggestions: List[str]
    ):
        self.query = query
        self.total_results = total_results
        self.search_time_ms = search_time_ms
        self.results = results
        self.facets = facets
        self.suggestions = suggestions


# === ENDPOINTS DE BÚSQUEDA ===

@router.get("/")
async def search_all(
    # Parámetros de búsqueda
    q: str = Query(..., min_length=1, description="Término de búsqueda"),
    search_type: str = Query("all", regex="^(all|documents|qr_codes|people)$", description="Tipo de búsqueda"),
    
    # Filtros opcionales
    document_type_id: Optional[int] = Query(None, description="Filtrar por tipo de documento"),
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    created_after: Optional[datetime] = Query(None, description="Creados después de"),
    created_before: Optional[datetime] = Query(None, description="Creados antes de"),
    has_qr: Optional[bool] = Query(None, description="Con código QR"),
    is_confidential: Optional[bool] = Query(None, description="Documentos confidenciales"),
    
    # Paginación y ordenamiento
    pagination: PaginationParams = Depends(PaginationParams),
    
    # Dependencias
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
    log_action = Depends(get_request_logger)
):
    """
    Búsqueda general en todos los tipos de contenido
    """
    try:
        start_time = datetime.utcnow()
        
        logger.info(f"Búsqueda realizada por {current_user.email}: '{q}'")
        
        # Crear filtros base
        filters = DocumentFilter(
            search=q,
            document_type_id=document_type_id,
            status=status,
            created_after=created_after,
            created_before=created_before,
            has_qr=has_qr,
            is_confidential=is_confidential,
            page=pagination.page,
            page_size=pagination.page_size,
            sort_by=pagination.sort_by,
            sort_order=pagination.sort_order
        )
        
        # Realizar búsqueda según el tipo
        if search_type == "documents" or search_type == "all":
            documents, total_docs = await search_documents_advanced(filters, current_user, db)
        else:
            documents, total_docs = [], 0
        
        # Convertir resultados
        results = []
        for doc in documents:
            result = SearchResult(
                type="document",
                id=doc.id,
                title=doc.file_name,
                description=f"{doc.nombre_completo or 'Sin nombre'} - {doc.document_type.name if doc.document_type else 'Sin tipo'}",
                relevance_score=calculate_relevance_score(doc, q),
                metadata={
                    "document_type": doc.document_type.code if doc.document_type else None,
                    "status": doc.status,
                    "created_at": doc.created_at.isoformat(),
                    "file_size_mb": doc.file_size_mb,
                    "has_qr": bool(doc.qr_code_id)
                },
                url=f"/api/v1/documents/{doc.id}"
            )
            results.append(result)
        
        # Calcular tiempo de búsqueda
        search_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Generar facetas (agregaciones)
        facets = await generate_search_facets(filters, current_user, db)
        
        # Generar sugerencias
        suggestions = generate_search_suggestions(q, results)
        
        # Log de búsqueda
        log_action("search_performed", {
            "query": q,
            "search_type": search_type,
            "total_results": total_docs,
            "search_time_ms": int(search_time)
        })
        
        response = SearchResponse(
            query=q,
            total_results=total_docs,
            search_time_ms=int(search_time),
            results=results,
            facets=facets,
            suggestions=suggestions
        )
        
        return {
            "query": response.query,
            "total_results": response.total_results,
            "search_time_ms": response.search_time_ms,
            "results": [
                {
                    "type": r.type,
                    "id": r.id,
                    "title": r.title,
                    "description": r.description,
                    "relevance_score": r.relevance_score,
                    "metadata": r.metadata,
                    "url": r.url
                } for r in response.results
            ],
            "facets": response.facets,
            "suggestions": response.suggestions,
            "pagination": {
                "page": pagination.page,
                "page_size": pagination.page_size,
                "total_pages": (response.total_results + pagination.page_size - 1) // pagination.page_size
            }
        }
        
    except Exception as e:
        logger.error(f"Error en búsqueda: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al realizar búsqueda"
        )


@router.get("/documents")
async def search_documents_only(
    # Parámetros de búsqueda específicos para documentos
    q: str = Query(..., min_length=1, description="Término de búsqueda"),
    
    # Filtros específicos
    cedula: Optional[str] = Query(None, description="Buscar por cédula"),
    nombre: Optional[str] = Query(None, description="Buscar por nombre"),
    document_type_codes: Optional[List[str]] = Query(None, description="Códigos de tipos de documento"),
    tags: Optional[List[str]] = Query(None, description="Tags a buscar"),
    
    # Filtros de archivo
    file_type: Optional[str] = Query(None, description="Tipo de archivo"),
    min_size_mb: Optional[float] = Query(None, description="Tamaño mínimo en MB"),
    max_size_mb: Optional[float] = Query(None, description="Tamaño máximo en MB"),
    
    # Búsqueda en contenido (OCR)
    search_content: bool = Query(False, description="Buscar en contenido extraído"),
    
    # Paginación
    pagination: PaginationParams = Depends(PaginationParams),
    
    # Dependencias
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
    log_action = Depends(get_request_logger)
):
    """
    Búsqueda específica en documentos con filtros avanzados
    """
    try:
        logger.info(f"Búsqueda de documentos por {current_user.email}: '{q}'")
        
        # Query base
        query = db.query(Document).join(DocumentType)
        
        # Aplicar filtros de acceso
        if not current_user.is_admin:
            query = query.filter(
                or_(
                    Document.uploaded_by == current_user.id,
                    and_(
                        Document.is_confidential == False,
                        Document.status != "deleted"
                    )
                )
            )
        
        # Filtro principal de búsqueda
        if q:
            search_conditions = []
            search_term = f"%{q}%"
            
            # Buscar en campos principales
            search_conditions.extend([
                Document.file_name.ilike(search_term),
                Document.cedula.ilike(search_term),
                Document.nombre_completo.ilike(search_term),
                Document.category.ilike(search_term),
                DocumentType.name.ilike(search_term),
                DocumentType.code.ilike(search_term)
            ])
            
            # Buscar en tags (usando operador JSON)
            if hasattr(Document.tags, 'op'):
                search_conditions.append(
                    func.array_to_string(Document.tags, ',').ilike(search_term)
                )
            
            # Buscar en contenido OCR si está habilitado
            if search_content:
                search_conditions.append(
                    Document.ocr_text.ilike(search_term)
                )
            
            query = query.filter(or_(*search_conditions))
        
        # Filtros específicos
        if cedula:
            query = query.filter(Document.cedula.ilike(f"%{cedula}%"))
        
        if nombre:
            query = query.filter(Document.nombre_completo.ilike(f"%{nombre}%"))
        
        if document_type_codes:
            query = query.filter(DocumentType.code.in_(document_type_codes))
        
        if tags:
            for tag in tags:
                # Buscar documentos que contengan el tag
                query = query.filter(
                    func.json_extract_path_text(Document.tags, tag).isnot(None)
                )
        
        if file_type:
            query = query.filter(Document.mime_type.ilike(f"%{file_type}%"))
        
        if min_size_mb:
            min_bytes = min_size_mb * 1024 * 1024
            query = query.filter(Document.file_size >= min_bytes)
        
        if max_size_mb:
            max_bytes = max_size_mb * 1024 * 1024
            query = query.filter(Document.file_size <= max_bytes)
        
        # Contar total
        total = query.count()
        
        # Aplicar ordenamiento
        if pagination.sort_by == "relevance":
            # Ordenamiento por relevancia (simplificado)
            query = query.order_by(desc(Document.created_at))
        elif pagination.sort_by == "name":
            query = query.order_by(asc(Document.file_name))
        elif pagination.sort_by == "date":
            query = query.order_by(desc(Document.created_at))
        elif pagination.sort_by == "size":
            query = query.order_by(desc(Document.file_size))
        else:
            query = query.order_by(desc(Document.created_at))
        
        # Aplicar paginación
        documents = query.offset(pagination.offset).limit(pagination.limit).all()
        
        # Convertir a schemas
        documents_summary = [DocumentSummary.from_orm(doc) for doc in documents]
        
        # Log de búsqueda
        log_action("documents_search", {
            "query": q,
            "total_results": total,
            "filters_applied": {
                "cedula": bool(cedula),
                "nombre": bool(nombre),
                "document_types": len(document_type_codes) if document_type_codes else 0,
                "tags": len(tags) if tags else 0,
                "search_content": search_content
            }
        })
        
        return DocumentListResponse(
            documents=documents_summary,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=(total + pagination.page_size - 1) // pagination.page_size,
            filter_stats={}  # Se puede expandir con estadísticas específicas
        )
        
    except Exception as e:
        logger.error(f"Error en búsqueda de documentos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al buscar documentos"
        )


@router.get("/qr-codes")
async def search_qr_codes(
    q: str = Query(..., min_length=1, description="Término de búsqueda"),
    status: Optional[str] = Query(None, description="Estado del QR"),
    document_type_id: Optional[int] = Query(None, description="Tipo de documento"),
    
    pagination: PaginationParams = Depends(PaginationParams),
    
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user),
    log_action = Depends(get_request_logger)
):
    """
    Búsqueda específica en códigos QR
    """
    try:
        # Query base
        query = db.query(QRCode).join(DocumentType)
        
        # Filtrar por usuario si no es admin
        if not current_user.is_admin:
            query = query.filter(QRCode.generated_by == current_user.id)
        
        # Búsqueda principal
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                QRCode.qr_id.ilike(search_term),
                DocumentType.code.ilike(search_term),
                DocumentType.name.ilike(search_term)
            )
        )
        
        # Filtros adicionales
        if status:
            if status == "available":
                query = query.filter(
                    and_(
                        QRCode.is_used == False,
                        QRCode.is_expired == False,
                        QRCode.is_revoked == False
                    )
                )
            elif status == "used":
                query = query.filter(QRCode.is_used == True)
            elif status == "expired":
                query = query.filter(QRCode.is_expired == True)
            elif status == "revoked":
                query = query.filter(QRCode.is_revoked == True)
        
        if document_type_id:
            query = query.filter(QRCode.document_type_id == document_type_id)
        
        # Contar y paginar
        total = query.count()
        qr_codes = query.offset(pagination.offset).limit(pagination.limit).all()
        
        # Convertir resultados
        results = []
        for qr in qr_codes:
            results.append({
                "id": qr.id,
                "qr_id": qr.qr_id,
                "document_type": {
                    "id": qr.document_type.id,
                    "code": qr.document_type.code,
                    "name": qr.document_type.name
                },
                "status": qr.status,
                "is_valid": qr.is_valid,
                "created_at": qr.created_at,
                "used_at": qr.used_at,
                "expires_at": qr.expires_at
            })
        
        # Log
        log_action("qr_codes_search", {
            "query": q,
            "total_results": total
        })
        
        return {
            "qr_codes": results,
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "total_pages": (total + pagination.page_size - 1) // pagination.page_size
        }
        
    except Exception as e:
        logger.error(f"Error buscando códigos QR: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al buscar códigos QR"
        )


@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1, max_length=50, description="Término parcial"),
    limit: int = Query(10, ge=1, le=20, description="Número máximo de sugerencias"),
    
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener sugerencias de búsqueda basadas en contenido existente
    """
    try:
        suggestions = []
        search_term = f"%{q}%"
        
        # Sugerencias de nombres de archivo
        file_names = db.query(Document.file_name).filter(
            Document.file_name.ilike(search_term)
        ).distinct().limit(limit // 3).all()
        
        suggestions.extend([name[0] for name in file_names])
        
        # Sugerencias de nombres de personas
        person_names = db.query(Document.nombre_completo).filter(
            Document.nombre_completo.ilike(search_term),
            Document.nombre_completo.isnot(None)
        ).distinct().limit(limit // 3).all()
        
        suggestions.extend([name[0] for name in person_names])
        
        # Sugerencias de tipos de documento
        doc_types = db.query(DocumentType.name).filter(
            DocumentType.name.ilike(search_term),
            DocumentType.is_active == True
        ).distinct().limit(limit // 3).all()
        
        suggestions.extend([name[0] for name in doc_types])
        
        # Limitar y ordenar
        unique_suggestions = list(set(suggestions))[:limit]
        
        return {
            "query": q,
            "suggestions": unique_suggestions,
            "count": len(unique_suggestions)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo sugerencias: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener sugerencias"
        )


@router.get("/stats")
async def get_search_stats(
    days: int = Query(30, ge=1, le=365, description="Días para estadísticas"),
    
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener estadísticas de búsqueda y contenido
    """
    try:
        # Fecha de corte
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Estadísticas básicas de documentos
        total_documents = db.query(Document).count()
        recent_documents = db.query(Document).filter(
            Document.created_at >= since_date
        ).count()
        
        # Documentos por tipo
        docs_by_type = db.query(
            DocumentType.code,
            DocumentType.name,
            func.count(Document.id).label('count')
        ).join(Document).group_by(
            DocumentType.id, DocumentType.code, DocumentType.name
        ).all()
        
        # Estadísticas de códigos QR
        total_qr_codes = db.query(QRCode).count()
        active_qr_codes = db.query(QRCode).filter(
            QRCode.is_used == False,
            QRCode.is_expired == False,
            QRCode.is_revoked == False
        ).count()
        
        # Tamaño total de archivos
        total_size_bytes = db.query(func.sum(Document.file_size)).scalar() or 0
        total_size_gb = round(total_size_bytes / (1024**3), 2)
        
        return {
            "period_days": days,
            "documents": {
                "total": total_documents,
                "recent": recent_documents,
                "by_type": [
                    {"code": code, "name": name, "count": count}
                    for code, name, count in docs_by_type
                ]
            },
            "qr_codes": {
                "total": total_qr_codes,
                "active": active_qr_codes,
                "used": total_qr_codes - active_qr_codes
            },
            "storage": {
                "total_size_gb": total_size_gb,
                "avg_file_size_mb": round(
                    (total_size_bytes / total_documents) / (1024**2), 2
                ) if total_documents > 0 else 0
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener estadísticas"
        )


# === FUNCIONES AUXILIARES ===

async def search_documents_advanced(
    filters: DocumentFilter,
    current_user: User,
    db: Session
):
    """
    Búsqueda avanzada de documentos con filtros
    """
    try:
        from ...services.document_service import get_document_service
        document_service = get_document_service()
        
        return document_service.search_documents(filters, current_user, db)
        
    except Exception as e:
        logger.error(f"Error en búsqueda avanzada: {str(e)}")
        return [], 0


def calculate_relevance_score(document: Document, query: str) -> float:
    """
    Calcular puntuación de relevancia para un documento
    """
    try:
        score = 0.0
        query_lower = query.lower()
        
        # Puntuación por coincidencia en nombre de archivo
        if query_lower in document.file_name.lower():
            score += 0.3
        
        # Puntuación por coincidencia en nombre completo
        if document.nombre_completo and query_lower in document.nombre_completo.lower():
            score += 0.25
        
        # Puntuación por coincidencia en cédula
        if document.cedula and query_lower in document.cedula:
            score += 0.2
        
        # Puntuación por coincidencia en tipo de documento
        if document.document_type and query_lower in document.document_type.name.lower():
            score += 0.15
        
        # Puntuación por recencia (documentos más nuevos tienen mayor relevancia)
        days_old = (datetime.utcnow() - document.created_at).days
        recency_score = max(0, 0.1 - (days_old * 0.001))
        score += recency_score
        
        return min(1.0, score)
        
    except Exception as e:
        logger.warning(f"Error calculando relevancia: {str(e)}")
        return 0.5


async def generate_search_facets(
    filters: DocumentFilter,
    current_user: User,
    db: Session
) -> Dict[str, Any]:
    """
    Generar facetas (agregaciones) para la búsqueda
    """
    try:
        facets = {}
        
        # Faceta por tipo de documento
        doc_types = db.query(
            DocumentType.code,
            DocumentType.name,
            func.count(Document.id).label('count')
        ).join(Document).group_by(
            DocumentType.id, DocumentType.code, DocumentType.name
        ).all()
        
        facets["document_types"] = [
            {"code": code, "name": name, "count": count}
            for code, name, count in doc_types
        ]
        
        # Faceta por estado
        statuses = db.query(
            Document.status,
            func.count(Document.id).label('count')
        ).group_by(Document.status).all()
        
        facets["statuses"] = [
            {"status": status, "count": count}
            for status, count in statuses
        ]
        
        # Faceta por presencia de QR
        qr_facet = db.query(
            func.count(func.case([(Document.qr_code_id.isnot(None), 1)])).label('with_qr'),
            func.count(func.case([(Document.qr_code_id.is_(None), 1)])).label('without_qr')
        ).first()
        
        facets["qr_presence"] = {
            "with_qr": qr_facet.with_qr,
            "without_qr": qr_facet.without_qr
        }
        
        return facets
        
    except Exception as e:
        logger.warning(f"Error generando facetas: {str(e)}")
        return {}


def generate_search_suggestions(query: str, results: List[SearchResult]) -> List[str]:
    """
    Generar sugerencias basadas en la consulta y resultados
    """
    try:
        suggestions = []
        
        # Sugerencias básicas basadas en palabras clave comunes
        common_terms = {
            "cedula": ["número de identificación", "documento de identidad"],
            "nombre": ["nombre completo", "apellidos"],
            "telefono": ["número de teléfono", "celular", "contacto"],
            "email": ["correo electrónico", "e-mail"],
            "documento": ["archivo", "expediente", "registro"]
        }
        
        query_lower = query.lower()
        for key, terms in common_terms.items():
            if key in query_lower:
                suggestions.extend(terms)
        
        # Limitar sugerencias
        return suggestions[:5]
        
    except Exception as e:
        logger.warning(f"Error generando sugerencias: {str(e)}")
        return []