"""
Script de prueba rápida para verificar conexión API de HuggingFace
Ejecutar: python scripts/test_hf_api.py
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import os
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Leer variables de entorno
from dotenv import load_dotenv
load_dotenv()

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


def test_api_connection():
    """Prueba la conexión con la API de HuggingFace"""
    
    logger.info("🧪 Probando conexión con API de HuggingFace...")
    logger.info("="*60)
    
    # Construir URL del endpoint (formato correcto)
    api_url = f"https://api-inference.huggingface.co/models/{EMBEDDING_MODEL}"
    
    logger.info(f"📡 Endpoint: {api_url}")
    logger.info(f"🔑 Token configurado: {'Sí' if HUGGINGFACE_API_KEY else 'No (usando público)'}")
    logger.info("")
    
    # Preparar headers
    headers = {}
    if HUGGINGFACE_API_KEY:
        headers["Authorization"] = f"Bearer {HUGGINGFACE_API_KEY}"
    
    # Texto de prueba
    test_text = "Hola, ¿cómo estás?"
    
    # Este modelo específico espera un array de textos
    payload = {"inputs": {"source_sentence": test_text, "sentences": [test_text]}}
    
    try:
        logger.info(f"📝 Texto de prueba: '{test_text}'")
        logger.info("⏳ Enviando request a HuggingFace...")
        
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        logger.info(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Extraer embedding
            if isinstance(result, list):
                if isinstance(result[0], list):
                    embedding = result[0]
                else:
                    embedding = result
            else:
                logger.error(f"❌ Formato inesperado: {type(result)}")
                return False
            
            logger.info("✅ API funcionando correctamente!")
            logger.info(f"📏 Dimensión del embedding: {len(embedding)}")
            logger.info(f"🔢 Primeros 5 valores: {embedding[:5]}")
            logger.info("")
            logger.info("="*60)
            logger.info("🎉 ¡Listo para generar embeddings!")
            logger.info("="*60)
            return True
            
        elif response.status_code == 503:
            logger.warning("⏳ Modelo está cargando (cold start)")
            logger.info("💡 Espera 10-20 segundos y vuelve a intentar")
            logger.info("O ejecuta: python scripts/generate_embeddings.py")
            logger.info("(El script reintentará automáticamente)")
            return False
            
        elif response.status_code == 429:
            logger.error("❌ Rate limit alcanzado")
            logger.info("💡 Soluciones:")
            logger.info("  1. Espera unos minutos")
            logger.info("  2. Verifica que HUGGINGFACE_API_KEY esté en .env")
            logger.info("  3. Considera usar modo LOCAL (más rápido)")
            return False
            
        elif response.status_code == 401:
            logger.error("❌ Token inválido o expirado")
            logger.info("💡 Verifica HUGGINGFACE_API_KEY en .env")
            logger.info("Genera nuevo token en: https://huggingface.co/settings/tokens")
            return False
            
        else:
            logger.error(f"❌ Error desconocido: {response.status_code}")
            logger.error(f"Respuesta: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("❌ Timeout: La API no respondió a tiempo")
        logger.info("💡 Intenta nuevamente o usa modo LOCAL")
        return False
        
    except requests.exceptions.ConnectionError:
        logger.error("❌ Error de conexión")
        logger.info("💡 Verifica tu conexión a internet")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_info():
    """Muestra información de configuración"""
    
    logger.info("\n📋 CONFIGURACIÓN ACTUAL")
    logger.info("="*60)
    logger.info(f"Modelo: {EMBEDDING_MODEL}")
    logger.info(f"Token HF: {'✅ Configurado' if HUGGINGFACE_API_KEY else '❌ No configurado'}")
    logger.info(f"USE_EMBEDDING_API: {os.getenv('USE_EMBEDDING_API', 'false')}")
    logger.info("="*60)
    logger.info("")


if __name__ == "__main__":
    show_info()
    
    success = test_api_connection()
    
    if success:
        logger.info("\n✅ Todo listo para generar embeddings!")
        logger.info("Ejecuta: python scripts/generate_embeddings.py")
    else:
        logger.error("\n❌ Hay problemas con la API")
        logger.info("\n📝 Opciones:")
        logger.info("  A) Espera y vuelve a intentar")
        logger.info("  B) Cambia a modo LOCAL:")
        logger.info("     - Edita .env: USE_EMBEDDING_API=false")
        logger.info("     - Instala: pip install sentence-transformers")
        logger.info("     - Ejecuta: python scripts/generate_embeddings.py")
        sys.exit(1)
