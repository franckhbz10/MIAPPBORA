"""
Script simplificado para generar embeddings
Inserta directamente en Supabase sin dependencias complejas
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import os
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client
from adapters.huggingface_adapter_hybrid import get_huggingface_hybrid_adapter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conexión Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_embeddings():
    """Genera embeddings para todas las frases"""
    
    logger.info("🤖 Iniciando generación de embeddings...")
    logger.info("="*60)
    
    # 1. Obtener todas las frases
    logger.info("📚 Obteniendo frases de Supabase...")
    response = supabase.table("bora_phrases").select("*").execute()
    frases = response.data
    
    logger.info(f"✅ Encontradas {len(frases)} frases")
    logger.info("")
    
    # 2. Inicializar modelo HuggingFace
    hf = get_huggingface_hybrid_adapter()
    logger.info("✅ Modelo de embeddings cargado")
    logger.info("")
    
    # 3. Generar y guardar embeddings
    success = 0
    errors = 0
    
    for i, frase in enumerate(frases, 1):
        try:
            # Texto combinado
            texto = f"{frase['bora_text']} {frase['spanish_translation']}"
            
            # Generar embedding
            embedding = hf.generate_embedding(texto)
            
            if not embedding:
                logger.error(f"❌ [{i}/{len(frases)}] Error al generar embedding")
                errors += 1
                continue
            
            # Guardar en Supabase
            supabase.table("phrase_embeddings").insert({
                "phrase_id": frase['id'],
                "embedding": embedding,
                "model_version": "sentence-transformers/all-MiniLM-L6-v2"
            }).execute()
            
            success += 1
            logger.info(
                f"✓ [{i}/{len(frases)}] "
                f"{frase['bora_text'][:30]}... → Embedding {len(embedding)}d"
            )
            
        except Exception as e:
            errors += 1
            logger.error(f"❌ [{i}/{len(frases)}] Error: {e}")
    
    # Resumen
    logger.info("")
    logger.info("="*60)
    logger.info("📊 RESUMEN")
    logger.info("="*60)
    logger.info(f"✅ Exitosos: {success}")
    logger.info(f"❌ Errores: {errors}")
    logger.info(f"📈 Total: {success + errors}/{len(frases)}")
    logger.info("="*60)
    
    return success > 0


if __name__ == "__main__":
    try:
        success = generate_embeddings()
        
        if success:
            logger.info("\n🎉 ¡Embeddings generados exitosamente!")
            logger.info("🎯 Ahora puedes probar la búsqueda semántica")
        else:
            logger.error("\n❌ No se generaron embeddings")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
