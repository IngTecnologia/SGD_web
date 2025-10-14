"""
Script para inicializar usuarios demo en modo desarrollo
"""
import logging
from sqlalchemy.orm import Session

from .models.user import User, UserRole, UserStatus
from .database import SessionLocal, engine
from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def create_demo_users(db: Session):
    """
    Crear usuarios demo si no existen

    Args:
        db: Sesión de base de datos
    """
    if not settings.DEMO_MODE:
        logger.info("Modo demo deshabilitado, no se crearán usuarios demo")
        return

    demo_users = [
        {
            "email": settings.DEMO_ADMIN_EMAIL,
            "name": settings.DEMO_ADMIN_NAME,
            "password": settings.DEMO_ADMIN_PASSWORD,
            "role": UserRole.ADMIN,
        },
        {
            "email": settings.DEMO_OPERATOR_EMAIL,
            "name": settings.DEMO_OPERATOR_NAME,
            "password": settings.DEMO_OPERATOR_PASSWORD,
            "role": UserRole.OPERATOR,
        },
        {
            "email": settings.DEMO_VIEWER_EMAIL,
            "name": settings.DEMO_VIEWER_NAME,
            "password": settings.DEMO_VIEWER_PASSWORD,
            "role": UserRole.VIEWER,
        },
    ]

    for user_data in demo_users:
        try:
            # Verificar si el usuario ya existe
            existing_user = db.query(User).filter(
                User.email == user_data["email"]
            ).first()

            if existing_user:
                logger.info(f"Usuario demo ya existe: {user_data['email']}")
                # Actualizar contraseña si cambió
                if not existing_user.verify_password(user_data["password"]):
                    existing_user.set_password(user_data["password"])
                    db.commit()
                    logger.info(f"Contraseña actualizada para: {user_data['email']}")
                continue

            # Crear nuevo usuario demo
            new_user = User(
                email=user_data["email"],
                name=user_data["name"],
                role=user_data["role"],
                status=UserStatus.ACTIVE,
                is_active=True,
                is_local_user=True,
                azure_id=f"demo-{user_data['email']}"  # Azure ID dummy para usuarios demo
            )
            new_user.set_password(user_data["password"])

            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            logger.info(f"Usuario demo creado: {user_data['email']} (rol: {user_data['role'].value})")

        except Exception as e:
            logger.error(f"Error creando usuario demo {user_data['email']}: {str(e)}")
            db.rollback()


def init_demo_data():
    """
    Inicializar todos los datos demo
    """
    try:
        db = SessionLocal()

        logger.info("Iniciando creación de usuarios demo...")
        create_demo_users(db)
        logger.info("Usuarios demo inicializados correctamente")

        db.close()

    except Exception as e:
        logger.error(f"Error inicializando datos demo: {str(e)}")
        raise


if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    init_demo_data()
