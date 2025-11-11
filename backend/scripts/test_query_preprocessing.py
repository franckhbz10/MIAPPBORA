"""
Script de prueba para validar el preprocesamiento de queries con gpt-4o-mini

Este script prueba la nueva funcionalidad de extracción de keywords/frases
antes de la búsqueda vectorial.

Uso:
    python -m scripts.test_query_preprocessing
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio backend al path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services.rag_service import RAGService
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Casos de prueba
TEST_QUERIES = [
    # Queries con ruido conversacional
    "hola soy pablito, estoy estudiando y no se como saludar en la lengua bora",
    "oye amigo, necesito saber como se dice casa en bora",
    "estoy en clase y me preguntaron como se dice buenos dias en bora",
    "hola, una consulta, como digo yo soy estudiante en el idioma bora",
    
    # Queries inversas (Bora -> Español)
    "que significa áábukɨ en español",
    "no entiendo que quiere decir tsaallé en bora",
    
    # Queries con frases complejas
    "necesito ayuda para traducir la frase me gusta aprender idiomas",
    "como se dice en bora tengo hambre y sed",
    
    # Queries cortas/directas (deberían pasar casi sin cambios)
    "casa",
    "saludar",
    "buenos dias",
]


async def test_keyword_extraction():
    """
    Prueba la extracción de keywords con diferentes tipos de queries
    """
    print("=" * 80)
    print("🔍 Test de Preprocesamiento de Queries")
    print("=" * 80)
    print()
    
    # Inicializar servicio RAG
    rag_service = RAGService()
    
    # Verificar que OpenAI está disponible
    if not rag_service.openai_adapter:
        print("❌ ERROR: OpenAI adapter no está disponible.")
        print("Verifica que OPENAI_ENABLED=true y OPENAI_API_KEY esté configurada en .env")
        return
    
    print(f"✅ OpenAI adapter disponible (modelo: {rag_service.openai_adapter.model})")
    print()
    
    # Probar cada query
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"Test {i}/{len(TEST_QUERIES)}")
        print(f"  📝 Original: {query}")
        
        try:
            cleaned = await rag_service._extract_search_keywords(query)
            print(f"  ✨ Limpia:   {cleaned}")
            
            # Calcular reducción de longitud
            reduction = (1 - len(cleaned) / len(query)) * 100 if len(query) > 0 else 0
            print(f"  📊 Reducción: {reduction:.1f}%")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print()
    
    print("=" * 80)
    print("✅ Test completado")
    print("=" * 80)


async def test_full_rag_pipeline():
    """
    Prueba el pipeline RAG completo con preprocesamiento
    """
    print()
    print("=" * 80)
    print("🚀 Test de Pipeline RAG Completo (con preprocesamiento)")
    print("=" * 80)
    print()
    
    rag_service = RAGService()
    
    # Query de prueba con mucho ruido
    test_query = "hola, estoy estudiando bora y no se como se dice saludar, me puedes ayudar?"
    
    print(f"Query: {test_query}")
    print()
    
    try:
        result = await rag_service.answer_with_lexicon(
            query=test_query,
            top_k=5,
            min_similarity=0.3,
        )
        
        print("📊 Timings:")
        for key, value in result.get("timings", {}).items():
            print(f"  - {key}: {value:.2f}ms")
        
        print()
        print("📊 Counters:")
        for key, value in result.get("counters", {}).items():
            print(f"  - {key}: {value}")
        
        print()
        print(f"💬 Respuesta ({len(result['answer'])} chars):")
        print(f"{result['answer'][:300]}...")
        
        print()
        print("🔍 Top 3 resultados:")
        for i, hit in enumerate(result.get("results", [])[:3], 1):
            print(f"  {i}. [{hit['kind']}] {hit.get('lemma', 'N/A')} - sim: {hit.get('similarity', 0):.3f}")
        
    except Exception as e:
        print(f"❌ Error en pipeline RAG: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    # Ejecutar tests
    asyncio.run(test_keyword_extraction())
    asyncio.run(test_full_rag_pipeline())
