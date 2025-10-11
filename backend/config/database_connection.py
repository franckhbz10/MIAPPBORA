"""
Configuración de conexión a base de datos
Maneja sesión de SQLAlchemy y dependency injection
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from config.settings import settings
from models.database import Base

logger = logging.getLogger(__name__)

# Crear engine de SQLAlchemy
# Para desarrollo usa SQLite, para producción PostgreSQL (Supabase)
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG  # Log de queries SQL en modo debug
)

# Crear session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Inicializa la base de datos
    Crea todas las tablas si no existen
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar base de datos: {e}")
        raise


def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obtener sesión de base de datos
    Se usa en endpoints de FastAPI con Depends(get_db)
    
    Ejemplo:
        @router.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
