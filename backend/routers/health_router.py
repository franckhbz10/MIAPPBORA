"""
Router de Salud y Diagnóstico para MIAPPBORA
Endpoints para verificar estado de servicios y conexiones
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

# Imports opcionales - tolerante a dependencias faltantes
try:
    from adapters.supabase_adapter import get_supabase_adapter
    SUPABASE_AVAILABLE = True
except ImportError as e:
    SUPABASE_AVAILABLE = False
    logging.warning(f"Supabase adapter no disponible: {e}")
    get_supabase_adapter = None

try:
    from adapters.huggingface_adapter import get_huggingface_adapter
    HUGGINGFACE_AVAILABLE = True
except ImportError as e:
    HUGGINGFACE_AVAILABLE = False
    logging.warning(f"HuggingFace adapter no disponible: {e}")
    get_huggingface_adapter = None

from config.settings import settings

router = APIRouter(prefix="/health", tags=["Health"])
logger = logging.getLogger(__name__)


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Endpoint básico de health check
    Verifica que el servidor esté funcionando
    """
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@router.get("/connections")
async def check_connections() -> Dict[str, Any]:
    """
    Verifica el estado de todas las conexiones externas
    
    Verifica:
    - Conexión a Supabase
    - Disponibilidad de modelos de HuggingFace
    - Configuración de variables de entorno
    
    Retorna estado detallado de cada servicio
    """
    status_report = {
        "app_info": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug_mode": settings.DEBUG
        },
        "services": {},
        "configuration": {},
        "overall_status": "ok"
    }
    
    issues = []
    
    # ==========================================
    # VERIFICAR SUPABASE
    # ==========================================
    if not SUPABASE_AVAILABLE:
        status_report["services"]["supabase"] = {
            "status": "unavailable",
            "message": "Módulo supabase no instalado. Ejecuta: pip install supabase",
            "instructions": "pip install supabase langchain langchain-community"
        }
        issues.append("Supabase: módulo no instalado")
    else:
        try:
            supabase_adapter = get_supabase_adapter()
            
            if supabase_adapter.is_connected():
                status_report["services"]["supabase"] = {
                    "status": "connected",
                    "url": settings.SUPABASE_URL if settings.SUPABASE_URL else "not_configured",
                    "message": "Conexión establecida correctamente"
                }
            else:
                status_report["services"]["supabase"] = {
                    "status": "disconnected",
                    "url": "not_configured",
                    "message": "Supabase no configurado. Revisa .env: SUPABASE_URL y SUPABASE_ANON_KEY"
                }
                issues.append("Supabase no configurado")
                
        except Exception as e:
            logger.error(f"Error al verificar Supabase: {e}")
            status_report["services"]["supabase"] = {
                "status": "error",
                "message": str(e)
            }
            issues.append(f"Error en Supabase: {str(e)}")
    
    # ==========================================
    # VERIFICAR HUGGINGFACE
    # ==========================================
    if not HUGGINGFACE_AVAILABLE:
        status_report["services"]["huggingface"] = {
            "status": "unavailable",
            "message": "Módulo sentence_transformers no instalado",
            "instructions": "pip install sentence-transformers transformers torch"
        }
        issues.append("HuggingFace: módulos no instalados")
    else:
        try:
            hf_adapter = get_huggingface_adapter()
            
            # Verificar si el modelo de embeddings está cargado
            if hf_adapter.embedding_model is not None:
                status_report["services"]["huggingface"] = {
                    "status": "connected",
                    "embedding_model": settings.EMBEDDING_MODEL,
                    "llm_model": settings.LLM_MODEL,
                    "api_key_configured": bool(settings.HUGGINGFACE_API_KEY),
                    "message": "Modelos cargados correctamente"
                }
                
                # Test rápido de embedding
                test_embedding = hf_adapter.generate_embedding("test")
                if test_embedding:
                    status_report["services"]["huggingface"]["embedding_dimension"] = len(test_embedding)
                    status_report["services"]["huggingface"]["test_embedding"] = "success"
                else:
                    status_report["services"]["huggingface"]["test_embedding"] = "failed"
                    issues.append("Test de embedding falló")
            else:
                status_report["services"]["huggingface"] = {
                    "status": "error",
                    "message": "Modelo de embeddings no cargado"
                }
                issues.append("HuggingFace: modelo no cargado")
                
        except Exception as e:
            logger.error(f"Error al verificar HuggingFace: {e}")
            status_report["services"]["huggingface"] = {
                "status": "error",
                "message": str(e)
            }
            issues.append(f"Error en HuggingFace: {str(e)}")
    
    # ==========================================
    # VERIFICAR CONFIGURACIÓN
    # ==========================================
    config_status = {
        "supabase_url": "configured" if settings.SUPABASE_URL else "missing",
        "supabase_key": "configured" if settings.SUPABASE_ANON_KEY else "missing",
        "huggingface_key": "configured" if settings.HUGGINGFACE_API_KEY else "missing",
        "embedding_model": settings.EMBEDDING_MODEL,
        "llm_model": settings.LLM_MODEL,
        "embedding_dimension": settings.EMBEDDING_DIMENSION
    }
    
    status_report["configuration"] = config_status
    
    # Verificar configuraciones críticas
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        issues.append("Configuración de Supabase incompleta")
    
    # ==========================================
    # ESTADO GENERAL
    # ==========================================
    if issues:
        status_report["overall_status"] = "degraded"
        status_report["issues"] = issues
        status_report["recommendations"] = [
            "1. Verificar archivo .env existe y tiene todas las variables",
            "2. Crear proyecto en Supabase: https://supabase.com",
            "3. Obtener token de HuggingFace: https://huggingface.co/settings/tokens",
            "4. Revisar logs del servidor para más detalles"
        ]
    
    return status_report


@router.get("/supabase")
async def check_supabase_only() -> Dict[str, Any]:
    """
    Verifica solo la conexión con Supabase
    Endpoint específico para debugging de Supabase
    """
    if not SUPABASE_AVAILABLE:
        return {
            "status": "unavailable",
            "message": "Módulo supabase no instalado",
            "instructions": {
                "step_1": "Instalar dependencias: pip install supabase langchain langchain-community",
                "step_2": "Crear proyecto en https://supabase.com",
                "step_3": "Ir a Settings → API",
                "step_4": "Copiar URL y anon key",
                "step_5": "Agregar a .env: SUPABASE_URL y SUPABASE_ANON_KEY"
            }
        }
    
    supabase_adapter = get_supabase_adapter()
    
    if not supabase_adapter.is_connected():
        return {
            "status": "disconnected",
            "message": "Supabase no configurado",
            "instructions": {
                "step_1": "Crear proyecto en https://supabase.com",
                "step_2": "Ir a Settings → API",
                "step_3": "Copiar URL y anon key",
                "step_4": "Agregar a .env: SUPABASE_URL y SUPABASE_ANON_KEY"
            },
            "env_status": {
                "SUPABASE_URL": "configured" if settings.SUPABASE_URL else "missing",
                "SUPABASE_ANON_KEY": "configured" if settings.SUPABASE_ANON_KEY else "missing"
            }
        }
    
    # Test de conexión real
    try:
        # Intentar una operación simple
        result = await supabase_adapter.get_phrases_by_category(
            category="Saludos y Presentaciones",
            limit=1
        )
        
        return {
            "status": "connected",
            "message": "Conexión exitosa con Supabase",
            "url": settings.SUPABASE_URL,
            "test_query": "success",
            "phrases_found": len(result)
        }
        
    except Exception as e:
        logger.error(f"Error en test de Supabase: {e}")
        return {
            "status": "error",
            "message": "Conexión establecida pero error en query",
            "error": str(e),
            "suggestion": "Verificar que las tablas estén creadas en Supabase"
        }


@router.get("/huggingface")
async def check_huggingface_only() -> Dict[str, Any]:
    """
    Verifica solo HuggingFace
    Endpoint específico para debugging de modelos
    """
    if not HUGGINGFACE_AVAILABLE:
        return {
            "status": "unavailable",
            "message": "Módulos de HuggingFace no instalados",
            "instructions": {
                "step_1": "Instalar: pip install sentence-transformers transformers torch",
                "step_2": "Obtener token de HuggingFace: https://huggingface.co/settings/tokens",
                "step_3": "Agregar a .env: HUGGINGFACE_API_KEY=tu_token"
            },
            "config": {
                "embedding_model": settings.EMBEDDING_MODEL,
                "llm_model": settings.LLM_MODEL
            }
        }
    
    hf_adapter = get_huggingface_adapter()
    
    if not hf_adapter.embedding_model:
        return {
            "status": "error",
            "message": "Modelo de embeddings no cargado",
            "config": {
                "embedding_model": settings.EMBEDDING_MODEL,
                "llm_model": settings.LLM_MODEL
            }
        }
    
    # Test de embedding
    try:
        test_text = "Hola, ¿cómo estás?"
        embedding = hf_adapter.generate_embedding(test_text)
        
        if embedding:
            return {
                "status": "ok",
                "message": "Modelo funcionando correctamente",
                "embedding_model": settings.EMBEDDING_MODEL,
                "embedding_dimension": len(embedding),
                "test_text": test_text,
                "test_result": "success"
            }
        else:
            return {
                "status": "error",
                "message": "No se pudo generar embedding"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": "Error al generar embedding",
            "error": str(e)
        }
