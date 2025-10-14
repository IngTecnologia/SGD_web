#!/usr/bin/env python3
"""
Script para cambiar las contraseñas de los usuarios demo
"""
import sys
sys.path.insert(0, '/app')

import bcrypt
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User

# Nuevas contraseñas seguras
NEW_PASSWORDS = {
    "admin@sgd-web.local": "SGD_Admin#2024Secure!",
    "operator@sgd-web.local": "SGD_Oper@tor2024Safe!",
    "viewer@sgd-web.local": "SGD_View3r2024#Safe!"
}

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def cambiar_passwords():
    """Cambiar contraseñas de usuarios demo"""
    db: Session = SessionLocal()

    try:
        print("=" * 70)
        print("CAMBIANDO CONTRASEÑAS DE USUARIOS DEMO")
        print("=" * 70)
        print()

        for email, nueva_password in NEW_PASSWORDS.items():
            user = db.query(User).filter(User.email == email).first()

            if user:
                # Usar el método set_password del modelo User
                user.set_password(nueva_password)
                db.commit()

                print(f"✅ Contraseña actualizada para: {email}")
                print(f"   Nueva contraseña: {nueva_password}")
                print()
            else:
                print(f"⚠️  Usuario no encontrado: {email}")
                print()

        print("=" * 70)
        print("✅ CONTRASEÑAS ACTUALIZADAS CORRECTAMENTE")
        print("=" * 70)
        print()
        print("🔐 NUEVAS CREDENCIALES DE ACCESO:")
        print()
        print("┌─ ADMINISTRADOR ─────────────────────────────────────────┐")
        print(f"│  Email:    admin@sgd-web.local                          │")
        print(f"│  Password: {NEW_PASSWORDS['admin@sgd-web.local']:<44}│")
        print("└─────────────────────────────────────────────────────────┘")
        print()
        print("┌─ OPERADOR ──────────────────────────────────────────────┐")
        print(f"│  Email:    operator@sgd-web.local                       │")
        print(f"│  Password: {NEW_PASSWORDS['operator@sgd-web.local']:<44}│")
        print("└─────────────────────────────────────────────────────────┘")
        print()
        print("┌─ VIEWER ────────────────────────────────────────────────┐")
        print(f"│  Email:    viewer@sgd-web.local                         │")
        print(f"│  Password: {NEW_PASSWORDS['viewer@sgd-web.local']:<44}│")
        print("└─────────────────────────────────────────────────────────┘")
        print()

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    cambiar_passwords()
