"""
Dependencias compartidas para FastAPI
Usadas en múltiples routers
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Annotated

from config.database_connection import get_db
from services.auth_service import AuthService
from models.database import User

# OAuth2 scheme para autenticación con token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency para obtener usuario actual desde token JWT
    Se usa en endpoints protegidos que requieren autenticación
    
    Args:
        token: Token JWT extraído del header Authorization
        db: Sesión de base de datos
    
    Returns:
        Usuario autenticado
    
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    try:
        user = await AuthService.get_current_user(db, token)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error al validar token: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Para ver en logs del servidor
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
