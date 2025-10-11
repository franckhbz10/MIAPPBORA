"""
Router de Autenticación para MIAPPBORA
Endpoints para registro, login y gestión de usuarios
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from schemas.schemas import (
    UserRegister, 
    UserLogin, 
    UserResponse, 
    LoginResponse,
    Token
)
from services.auth_service import AuthService, get_auth_service
from models.database import User
from config.database_connection import get_db
from dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])
@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo usuario

    - **email**: Email único del usuario
    - **username**: Nombre de usuario único (3-100 caracteres)
    - **phone**: Teléfono del usuario (9-20 caracteres)
    - **password**: Contraseña (mínimo 6 caracteres)
    - **full_name**: Nombre completo del usuario (opcional)
    """
    try:
        # Registrar usuario
        user = await AuthService.register_user(db, user_data)

        # Crear token de acceso (convertir id a string para JWT)
        access_token = AuthService.create_access_token(data={"sub": str(user.id)})
        
        return {
            "user": user,
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        error_detail = f"Error al registrar usuario: {str(e)}\\n{traceback.format_exc()}"
        print(error_detail)  # Para ver en logs del servidor
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Inicia sesión con email y contraseña

    - **email**: Email del usuario
    - **password**: Contraseña

    Retorna token JWT para autenticación
    """
    try:
        # Autenticar usuario
        user = await AuthService.authenticate_user(
            db, 
            credentials.email, 
            credentials.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Crear token de acceso (convertir id a string para JWT)
        access_token = AuthService.create_access_token(data={"sub": str(user.id)})

        return {
            "user": user,
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error al hacer login: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Para ver en logs del servidor
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Obtiene información del usuario actual
    
    Requiere autenticación con token JWT
    """
    return current_user


@router.post("/logout")
async def logout():
    """
    Cierra sesión del usuario
    
    Nota: En JWT stateless, el logout se maneja en el frontend
    eliminando el token. Este endpoint es informativo.
    """
    return {"message": "Sesión cerrada exitosamente"}
