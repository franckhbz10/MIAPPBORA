"""
Prueba de búsqueda semántica con pgvector
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import asyncio
import logging
from adapters.supabase_adapter import SupabaseAdapter
from adapters.huggingface_adapter_hybrid import HuggingFaceHybridAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_search():
    """Prueba búsquedas semánticas"""
    logger.info("🔍 PRUEBA DE BÚSQUEDA SEMÁNTICA")
    logger.info("=" * 60)
    
    # Initialize adapters
    supabase = SupabaseAdapter()
    hf_adapter = HuggingFaceHybridAdapter()
    
    # Test queries
    queries = [
        "¿Cómo saludo a alguien?",
        "¿Cómo pregunto el nombre?",
        "¿Qué digo cuando tengo miedo?",
        "Necesito ayuda médica",
        "¿Cómo digo gracias?",
    ]
    
    for query in queries:
        logger.info(f"\n📝 Consulta: '{query}'")
        logger.info("-" * 60)
        
        # Generate embedding for query (synchronous method)
        query_embedding = hf_adapter.generate_embedding(query)
        
        # Search similar phrases using RPC directly with lower threshold
        results = supabase.client.rpc('match_phrases', {
            'query_embedding': query_embedding,
            'match_threshold': 0.3,  # Umbral más bajo (30% similaridad)
            'match_count': 3
        }).execute().data
        
        if results:
            logger.info(f"✅ Encontrados {len(results)} resultados:")
            for i, result in enumerate(results, 1):
                similarity = result.get('similarity', 0)
                bora_text = result.get('bora_text', '')
                spanish_translation = result.get('spanish_translation', '')
                logger.info(
                    f"  {i}. [{similarity:.2%}] {bora_text} → {spanish_translation}"
                )
        else:
            logger.info("❌ No se encontraron resultados")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Prueba completada")


if __name__ == "__main__":
    asyncio.run(test_search())
