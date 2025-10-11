"""
Servicio de Autenticación para MIAPPBORA
Maneja registro, login y gestión de tokens JWT
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from models.database import User
from schemas.schemas import UserRegister, UserResponse, Token
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Configuración de encriptación de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    Servicio de autenticación
    
    Responsabilidades:
    - Registro de usuarios
    - Login y generación de tokens
    - Verificación de contraseñas
    - Validación de tokens JWT
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Genera hash de contraseña usando bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica contraseña contra hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Crea token JWT
        
        Args:
            data: Datos a incluir en el token (típicamente user_id)
            expires_delta: Tiempo de expiración
        
        Returns:
            Token JWT codificado
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Optional[int]:
        """
        Decodifica y valida token JWT

        Args:
            token: Token JWT

        Returns:
            user_id (int) si el token es válido, None si no
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            user_id_str: str = payload.get("sub")
            if user_id_str is None:
                return None
            # Convertir de string a int
            user_id = int(user_id_str)
            return user_id
        except (JWTError, ValueError) as e:
            logger.error(f"Error al decodificar token: {e}")
            return None    @staticmethod
    async def register_user(
        db: Session,
        user_data: UserRegister
    ) -> User:
        """
        Registra nuevo usuario
        
        Args:
            db: Sesión de base de datos
            user_data: Datos del usuario
        
        Returns:
            Usuario creado
        
        Raises:
            ValueError: Si el email o username ya existen
        """
        # Verificar si el email ya existe
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise ValueError("El email ya está registrado")

        # Verificar si el username ya existe
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            raise ValueError("El nombre de usuario ya está en uso")

        # Verificar si el teléfono ya existe
        existing_phone = db.query(User).filter(User.phone == user_data.phone).first()
        if existing_phone:
            raise ValueError("El teléfono ya está registrado")

        # Crear nuevo usuario
        hashed_password = AuthService.hash_password(user_data.password)

        new_user = User(
            email=user_data.email,
            username=user_data.username,
            phone=user_data.phone,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            avatar_url='https://ui-avatars.com/api/?name=User',
            level=1,
            total_points=0,
            current_title='Principiante',
            is_active=True
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"Usuario registrado: {new_user.username} ({new_user.email})")
        return new_user

    @staticmethod
    async def authenticate_user(
        db: Session,
        email: str,
        password: str
    ) -> Optional[User]:
        """
        Autentica usuario por email y contraseña
        
        Args:
            db: Sesión de base de datos
            email: Email del usuario
            password: Contraseña en texto plano
        
        Returns:
            Usuario si la autenticación es exitosa, None si no
        """
        user = db.query(User).filter(User.email == email).first()

        if not user:
            return None

        if not AuthService.verify_password(password, user.hashed_password):
            return None

        # Actualizar último login
        user.last_login = datetime.utcnow()
        db.commit()

        return user

    @staticmethod
    async def get_current_user(db: Session, token: str) -> Optional[User]:
        """
        Obtiene usuario actual desde token JWT
        
        Args:
            db: Sesión de base de datos
            token: Token JWT
        
        Returns:
            Usuario si el token es válido, None si no
        """
        user_id = AuthService.decode_token(token)
        
        if not user_id:
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        return user


# Instancia global del servicio
auth_service = AuthService()


def get_auth_service() -> AuthService:
    """Función helper para obtener el servicio"""
    return auth_service
