"""
Local Authentication Endpoints
Provides local login functionality when Microsoft 365 is not available
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Dict, Any

from app.db.database import get_db
from app.services.local_auth import local_auth_service
from app.core.config import settings
from app.models.user import UserRole

router = APIRouter()

class LocalLoginRequest(BaseModel):
    email: EmailStr
    password: str

class LocalRegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: UserRole = UserRole.viewer

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class LocalLoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: Dict[str, Any]

@router.post("/local/login", response_model=LocalLoginResponse)
async def local_login(
    login_data: LocalLoginRequest,
    db: Session = Depends(get_db)
):
    """Login with local credentials (email/password)"""
    
    if not settings.LOCAL_AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Local authentication is disabled"
        )
    
    # Authenticate user
    user = local_auth_service.authenticate_user(
        email=login_data.email,
        password=login_data.password,
        db=db
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Generate access token
    token_data = local_auth_service.generate_access_token(user)
    
    return LocalLoginResponse(**token_data)

@router.post("/local/login/form")
async def local_login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login with OAuth2 password form (for compatibility)"""
    
    if not settings.LOCAL_AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Local authentication is disabled"
        )
    
    # Authenticate user
    user = local_auth_service.authenticate_user(
        email=form_data.username,  # OAuth2 uses 'username' field
        password=form_data.password,
        db=db
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Generate access token
    token_data = local_auth_service.generate_access_token(user)
    
    return {
        "access_token": token_data["access_token"],
        "token_type": token_data["token_type"]
    }

@router.post("/local/register")
async def local_register(
    register_data: LocalRegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new local user"""
    
    if not settings.LOCAL_AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Local authentication is disabled"
        )
    
    # In demo mode, prevent creating new users
    if settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User registration is disabled in demo mode"
        )
    
    try:
        user = local_auth_service.create_local_user(
            email=register_data.email,
            name=register_data.name,
            password=register_data.password,
            role=register_data.role,
            db=db
        )
        
        return {
            "message": "User created successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role.value,
                "is_active": user.is_active
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

@router.post("/local/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    
    if not settings.LOCAL_AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Local authentication is disabled"
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == current_user["id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        local_auth_service.change_password(
            user=user,
            old_password=password_data.old_password,
            new_password=password_data.new_password,
            db=db
        )
        
        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error changing password: {str(e)}"
        )

@router.get("/local/demo-users")
async def get_demo_users():
    """Get information about available demo users (development only)"""
    
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo mode is not enabled"
        )
    
    return local_auth_service.get_demo_users_info()

@router.get("/local/status")
async def local_auth_status():
    """Get local authentication status"""
    
    return {
        "local_auth_enabled": settings.LOCAL_AUTH_ENABLED,
        "demo_mode": settings.DEMO_MODE,
        "microsoft_auth_available": bool(settings.MICROSOFT_CLIENT_ID and settings.MICROSOFT_CLIENT_SECRET),
        "available_auth_methods": []
    }

# Import get_current_user here to avoid circular imports
from app.core.deps import get_current_user