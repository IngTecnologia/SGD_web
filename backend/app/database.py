"""
Configuración de base de datos para SGD Web
"""
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from .config import get_settings

# Obtener configuración
settings = get_settings()

# Configurar logging
logger = logging.getLogger(__name__)

# Crear engine de SQLAlchemy
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verificar conexiones antes de usarlas
    pool_recycle=300,    # Reciclar conexiones cada 5 minutos
    pool_size=5,         # Pool de 5 conexiones
    max_overflow=0,      # No permitir conexiones adicionales
    echo=settings.DEBUG, # Mostrar SQL queries en desarrollo
)

# Crear SessionLocal para transacciones
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base para modelos
Base = declarative_base()

# Metadata para migraciones
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obtener sesión de base de datos.
    Se usa en FastAPI como dependencia.
    
    Yields:
        Session: Sesión de SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Error en sesión de base de datos: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """
    Crear todas las tablas en la base de datos.
    Solo para desarrollo/testing. En producción usar Alembic.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas creadas exitosamente")
    except Exception as e:
        logger.error(f"Error creando tablas: {e}")
        raise


def drop_tables():
    """
    Eliminar todas las tablas.
    ¡CUIDADO! Solo para desarrollo/testing.
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("Todas las tablas han sido eliminadas")
    except Exception as e:
        logger.error(f"Error eliminando tablas: {e}")
        raise


def check_database_connection() -> bool:
    """
    Verificar conexión a la base de datos.

    Returns:
        bool: True si la conexión es exitosa
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Conexión a base de datos exitosa")
        return True
    except Exception as e:
        logger.error(f"Error conectando a base de datos: {e}")
        return False


class DatabaseManager:
    """Clase para gestionar operaciones de base de datos"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def get_session(self) -> Session:
        """Obtener nueva sesión de base de datos"""
        return self.SessionLocal()
    
    def create_all_tables(self):
        """Crear todas las tablas"""
        create_tables()
    
    def drop_all_tables(self):
        """Eliminar todas las tablas"""
        drop_tables()
    
    def check_connection(self) -> bool:
        """Verificar conexión"""
        return check_database_connection()
    
    def execute_sql(self, query: str, params: dict = None):
        """
        Ejecutar query SQL directamente.

        Args:
            query: Query SQL a ejecutar
            params: Parámetros para el query
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query), params or {})
                return result
        except Exception as e:
            logger.error(f"Error ejecutando SQL: {e}")
            raise
    
    def backup_database(self, backup_path: str):
        """
        Crear backup de base de datos.
        Implementación básica - en producción usar herramientas específicas.
        
        Args:
            backup_path: Ruta donde guardar el backup
        """
        import subprocess
        import os
        
        try:
            # Construir comando pg_dump
            cmd = [
                'pg_dump',
                f'--host={settings.POSTGRES_SERVER}',
                f'--port={settings.POSTGRES_PORT}',
                f'--username={settings.POSTGRES_USER}',
                f'--dbname={settings.POSTGRES_DB}',
                f'--file={backup_path}',
                '--verbose',
                '--no-password'
            ]
            
            # Configurar variable de entorno para contraseña
            env = os.environ.copy()
            env['PGPASSWORD'] = settings.POSTGRES_PASSWORD
            
            # Ejecutar backup
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Backup creado exitosamente en: {backup_path}")
                return True
            else:
                logger.error(f"Error en backup: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            return False


# Instancia global del manager
db_manager = DatabaseManager()


# Decorador para transacciones
def transactional(func):
    """
    Decorador para envolver funciones en transacciones.
    
    Usage:
        @transactional
        def my_function(db: Session):
            # código que modifica la BD
            pass
    """
    def wrapper(*args, **kwargs):
        db = SessionLocal()
        try:
            result = func(db, *args, **kwargs)
            db.commit()
            return result
        except Exception as e:
            db.rollback()
            logger.error(f"Error en transacción: {e}")
            raise
        finally:
            db.close()
    return wrapper


# Funciones de utilidad para testing
def create_test_database():
    """Crear base de datos de pruebas"""
    if settings.ENVIRONMENT == "testing":
        create_tables()
        logger.info("Base de datos de pruebas creada")
    else:
        logger.warning("create_test_database solo debe usarse en testing")


def cleanup_test_database():
    """Limpiar base de datos de pruebas"""
    if settings.ENVIRONMENT == "testing":
        drop_tables()
        logger.info("Base de datos de pruebas limpiada")
    else:
        logger.warning("cleanup_test_database solo debe usarse en testing")


# Health check para la base de datos
async def database_health_check() -> dict:
    """
    Verificar estado de la base de datos para health checks.
    
    Returns:
        dict: Estado de la base de datos
    """
    try:
        is_connected = check_database_connection()
        
        # Obtener información adicional si está conectado
        if is_connected:
            with engine.connect() as connection:
                # Verificar número de conexiones activas
                result = connection.execute(
                    text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
                )
                active_connections = result.scalar()
                
                return {
                    "status": "healthy",
                    "connected": True,
                    "active_connections": active_connections,
                    "database": settings.POSTGRES_DB,
                    "server": settings.POSTGRES_SERVER
                }
        else:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": "No se pudo conectar a la base de datos"
            }
            
    except Exception as e:
        logger.error(f"Error en health check de base de datos: {e}")
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }