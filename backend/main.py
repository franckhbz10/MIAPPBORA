"""
MIAPPBORA - Aplicación de Aprendizaje del Idioma Bora
Backend FastAPI

Aplicación para practicar y aprender frases cotidianas en Bora,
una lengua indígena de la Amazonía peruana.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config.settings import settings
from config.database_connection import init_db
from routers import health_router, auth_router, game_router, profile_router

# Configurar logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida de la aplicación
    Se ejecuta al inicio y al cierre
    """
    # Startup
    logger.info(f"Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Inicializar base de datos
    try:
        init_db()
        logger.info("Base de datos inicializada")
    except Exception as e:
        logger.error(f"Error al inicializar BD: {e}")
    
    # Verificar conexiones (sin interrumpir inicio)
    try:
        from adapters.supabase_adapter import get_supabase_adapter
        supabase = get_supabase_adapter()
        
        if supabase.is_connected():
            logger.info("✓ Supabase conectado")
        else:
            logger.warning("✗ Supabase no configurado - revisar .env")
            
    except ImportError:
        logger.warning("✗ Módulo supabase no instalado - ejecuta: pip install supabase")
    except Exception as e:
        logger.warning(f"✗ Supabase: {e}")
    
    try:
        from adapters.huggingface_adapter import get_huggingface_adapter
        hf = get_huggingface_adapter()
        
        if hf.embedding_model:
            logger.info("✓ Modelos de HuggingFace cargados")
        else:
            logger.warning("✗ Modelos de HuggingFace no disponibles")
            
    except ImportError:
        logger.warning("✗ Módulos ML no instalados - ejecuta: pip install sentence-transformers")
    except Exception as e:
        logger.warning(f"✗ HuggingFace: {e}")
    
    logger.info(f"Servidor listo en modo {'DEBUG' if settings.DEBUG else 'PRODUCCIÓN'}")
    
    yield
    
    # Shutdown
    logger.info("Cerrando aplicación...")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## MIAPPBORA - Aprende Bora 🌿
    
    Aplicación gamificada para aprender frases cotidianas en Bora,
    una lengua indígena amazónica de Perú.
    
    ### Características:
    
    * 🔐 **Autenticación**: Registro y login de usuarios
    * 💬 **Mentor Bora**: Asistente conversacional con IA
    * 🎮 **Minijuegos**: Práctica interactiva
    * 📊 **Progreso**: Sistema de gamificación
    * 🗣️ **Corpus**: +500 frases Bora-Español
    
    ### Categorías de Aprendizaje:
    
    1. Saludos y Presentaciones
    2. Conversación General
    3. Ubicación
    4. Relaciones Cotidianas
    5. Emergencias
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
# Configurar CORS
# Asegurar que incluimos todos los orígenes necesarios para desarrollo
allowed_origins = list(settings.CORS_ORIGINS)  # Convertir a lista mutable

# Añadir explícitamente orígenes comunes de desarrollo si no están
dev_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

for origin in dev_origins:
    if origin not in allowed_origins:
        allowed_origins.append(origin)
        logger.info(f"Añadiendo origen de desarrollo: {origin}")

logger.info(f"CORS configuración final - Orígenes permitidos: {allowed_origins}")
logger.info(f"CORS - allow_credentials: True")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(health_router.router)
app.include_router(auth_router.router)
app.include_router(game_router.router)
app.include_router(profile_router.router)

# Importar y registrar el nuevo router de autenticación
try:
    from api.auth import router as new_auth_router
    app.include_router(new_auth_router)
    logger.info("✓ Router de autenticación API cargado")
except Exception as e:
    logger.warning(f"✗ Router auth API: {e}")


@app.get("/")
async def root():
    """
    Endpoint raíz - Información básica de la API
    """
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health/connections",
        "message": "Bienvenido a MIAPPBORA - Aprende Bora 🌿"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
