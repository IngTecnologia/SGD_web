"""
Local Authentication Service
Fallback authentication system when Microsoft 365 is not available
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.models.user import User, UserRole
from app.core.config import settings
from app.core.security import create_access_token

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LocalAuthService:
    """Local authentication service for demo/development mode"""
    
    def __init__(self):
        self.demo_users = self._get_demo_users()
    
    def _get_demo_users(self) -> Dict[str, Dict[str, Any]]:
        """Get demo users from environment configuration"""
        return {
            settings.DEMO_ADMIN_EMAIL: {
                "name": settings.DEMO_ADMIN_NAME,
                "email": settings.DEMO_ADMIN_EMAIL,
                "password": self._hash_password(settings.DEMO_ADMIN_PASSWORD),
                "role": UserRole.admin,
                "is_active": True,
            },
            settings.DEMO_OPERATOR_EMAIL: {
                "name": settings.DEMO_OPERATOR_NAME,
                "email": settings.DEMO_OPERATOR_EMAIL,
                "password": self._hash_password(settings.DEMO_OPERATOR_PASSWORD),
                "role": UserRole.operator,
                "is_active": True,
            },
            settings.DEMO_VIEWER_EMAIL: {
                "name": settings.DEMO_VIEWER_NAME,
                "email": settings.DEMO_VIEWER_EMAIL,
                "password": self._hash_password(settings.DEMO_VIEWER_PASSWORD),
                "role": UserRole.viewer,
                "is_active": True,
            }
        }
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def authenticate_user(self, email: str, password: str, db: Session) -> Optional[User]:
        """Authenticate a user with email and password"""
        
        # First, try to authenticate with demo users
        if settings.DEMO_MODE and email in self.demo_users:
            demo_user = self.demo_users[email]
            if self._verify_password(password, demo_user["password"]):
                # Get or create user in database
                user = self._get_or_create_demo_user(email, demo_user, db)
                return user
        
        # If not demo mode or not a demo user, check database
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        
        # Check if user has a local password (stored in profile_data)
        if not user.profile_data or "password_hash" not in user.profile_data:
            return None
        
        if not self._verify_password(password, user.profile_data["password_hash"]):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
    
    def _get_or_create_demo_user(self, email: str, demo_user_data: Dict[str, Any], db: Session) -> User:
        """Get or create a demo user in the database"""
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Create new demo user
            user = User(
                email=demo_user_data["email"],
                name=demo_user_data["name"],
                role=demo_user_data["role"],
                is_active=demo_user_data["is_active"],
                microsoft_id=None,  # Local user, no Microsoft ID
                profile_data={
                    "is_demo_user": True,
                    "auth_type": "local",
                    "password_hash": demo_user_data["password"]
                }
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update existing user
            user.name = demo_user_data["name"]
            user.role = demo_user_data["role"]
            user.is_active = demo_user_data["is_active"]
            user.last_login = datetime.utcnow()
            
            if not user.profile_data:
                user.profile_data = {}
            user.profile_data.update({
                "is_demo_user": True,
                "auth_type": "local",
                "password_hash": demo_user_data["password"]
            })
            db.commit()
        
        return user
    
    def create_local_user(
        self, 
        email: str, 
        name: str, 
        password: str, 
        role: UserRole = UserRole.viewer,
        db: Session = None
    ) -> User:
        """Create a new local user (non-demo)"""
        if not settings.LOCAL_AUTH_ENABLED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Local authentication is disabled"
            )
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create new user
        password_hash = self._hash_password(password)
        user = User(
            email=email,
            name=name,
            role=role,
            is_active=True,
            microsoft_id=None,
            profile_data={
                "is_demo_user": False,
                "auth_type": "local",
                "password_hash": password_hash
            }
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    def change_password(self, user: User, old_password: str, new_password: str, db: Session) -> bool:
        """Change user password"""
        if not user.profile_data or "password_hash" not in user.profile_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User does not have a local password"
            )
        
        # Verify old password
        if not self._verify_password(old_password, user.profile_data["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        new_password_hash = self._hash_password(new_password)
        user.profile_data["password_hash"] = new_password_hash
        user.updated_at = datetime.utcnow()
        
        db.commit()
        return True
    
    def generate_access_token(self, user: User) -> Dict[str, Any]:
        """Generate access token for authenticated user"""
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "auth_type": "local"
        }
        
        access_token = create_access_token(data=token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role.value,
                "is_active": user.is_active,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "auth_type": "local"
            }
        }
    
    def get_demo_users_info(self) -> Dict[str, Any]:
        """Get information about available demo users"""
        if not settings.DEMO_MODE:
            return {}
        
        return {
            "demo_mode": True,
            "available_users": [
                {
                    "email": settings.DEMO_ADMIN_EMAIL,
                    "name": settings.DEMO_ADMIN_NAME,
                    "role": "admin",
                    "password": settings.DEMO_ADMIN_PASSWORD
                },
                {
                    "email": settings.DEMO_OPERATOR_EMAIL,
                    "name": settings.DEMO_OPERATOR_NAME,
                    "role": "operator",
                    "password": settings.DEMO_OPERATOR_PASSWORD
                },
                {
                    "email": settings.DEMO_VIEWER_EMAIL,
                    "name": settings.DEMO_VIEWER_NAME,
                    "role": "viewer",
                    "password": settings.DEMO_VIEWER_PASSWORD
                }
            ]
        }

# Global instance
local_auth_service = LocalAuthService()