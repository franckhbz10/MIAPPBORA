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
    
    # Verificar OpenAI (si está habilitado)
    if settings.OPENAI_ENABLED:
        try:
            from adapters.openai_adapter import get_openai_adapter
            openai_adapter = get_openai_adapter()
            health = await openai_adapter.health_check()
            if health.get("status") == "healthy":
                logger.info(f"✓ OpenAI disponible ({health.get('model', 'unknown')})")
            else:
                logger.warning(f"⚠️ OpenAI no disponible: {health.get('error', 'unknown')}")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo verificar OpenAI: {e}")
    else:
        logger.info("OpenAI deshabilitado por configuración")
    
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

# Añadir dominio de producción (Vercel) dinámicamente desde variable de entorno
import os
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    # Normalizar URL (quitar trailing slash)
    frontend_url = frontend_url.rstrip('/')
    # Soportar variantes con/sin www
    frontend_variants = [
        frontend_url,
        frontend_url.replace('https://', 'https://www.'),
        frontend_url.replace('https://www.', 'https://')
    ]
    for variant in frontend_variants:
        if variant not in allowed_origins and variant != frontend_url:
            allowed_origins.append(variant)
    if frontend_url not in allowed_origins:
        allowed_origins.append(frontend_url)
    logger.info(f"✓ Frontend de producción configurado: {frontend_url}")

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
try:
    from routers import lexicon_router
    app.include_router(lexicon_router.router)
    logger.info("✓ Router de lexicón cargado")
except Exception as e:
    logger.warning(f"✗ Router lexicón: {e}")

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
