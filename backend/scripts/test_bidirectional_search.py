"""
Test de búsqueda bidireccional con detección automática de dirección

Este script prueba:
1. Detección automática de dirección (ES→Bora vs Bora→ES)
2. Filtrado por dirección en búsqueda vectorial
3. Verificación de resultados correctos

Requisitos:
- Ejecutar migración: 003_match_bora_docs_v2_direction_filter.sql en Supabase
- Backend corriendo con variables de entorno configuradas
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv()

from services.rag_service import RAGService


async def test_direction_detection():
    """Test de detección de dirección del query"""
    rag = RAGService()
    
    print("=" * 80)
    print("TEST 1: Detección de Dirección del Query")
    print("=" * 80)
    
    test_cases = [
        ("como se dice cantar en bora", "es_bora", "Query explícito ES→Bora"),
        ("que significa majtsíva", "bora_es", "Query explícito Bora→ES"),
        ("cantar", None, "Query ambiguo (una palabra)"),
        ("como digo buenos dias en bora", "es_bora", "Frase ES→Bora"),
        ("traducir tsʉ́bɨ al español", "bora_es", "Frase Bora→ES"),
        ("áábukɨ", "bora_es", "Palabra Bora (caracteres especiales)"),
    ]
    
    for query, expected, description in test_cases:
        detected = await rag._detect_query_direction(query)
        status = "✅" if detected == expected else "❌"
        print(f"\n{status} {description}")
        print(f"   Query: '{query}'")
        print(f"   Esperado: {expected}")
        print(f"   Detectado: {detected}")


async def test_search_with_direction():
    """Test de búsqueda con filtrado por dirección"""
    rag = RAGService()
    
    print("\n" + "=" * 80)
    print("TEST 2: Búsqueda con Filtrado por Dirección")
    print("=" * 80)
    
    # Test 1: Buscar "cantar" en ES→Bora
    print("\n📍 Test 2.1: 'Como se dice cantar en bora' (debería buscar ES→Bora)")
    results = await rag.search_lexicon(
        query="como se dice cantar en bora",
        top_k=5,
        min_similarity=0.5,
    )
    
    print(f"   Resultados: {len(results)}")
    if results:
        for i, r in enumerate(results[:3], 1):
            direction = r.get('direction', 'N/A')
            lemma = r.get('lemma', 'N/A')
            gloss_bora = r.get('gloss_bora', 'N/A')
            gloss_es = r.get('gloss_es', 'N/A')
            similarity = r.get('similarity', 0.0)
            
            print(f"\n   {i}. Lemma: {lemma}")
            print(f"      Direction: {direction}")
            print(f"      Gloss ES: {gloss_es}")
            print(f"      Gloss Bora: {gloss_bora}")
            print(f"      Similarity: {similarity:.3f}")
            
            # Verificar que sea ES→Bora
            if direction == 'es_bora' and lemma.lower() == 'cantar':
                print(f"      ✅ CORRECTO: Encontró 'cantar' en ES→Bora")
                if gloss_bora and 'majtsí' in gloss_bora.lower():
                    print(f"      ✅ CORRECTO: Traducción contiene 'majtsí'")
            elif direction != 'es_bora':
                print(f"      ❌ ERROR: Dirección incorrecta, esperaba 'es_bora'")
    else:
        print("   ❌ ERROR: No se encontraron resultados")
    
    # Test 2: Buscar "majtsíva" en Bora→ES
    print("\n📍 Test 2.2: 'Que significa majtsíva' (debería buscar Bora→ES)")
    results = await rag.search_lexicon(
        query="que significa majtsíva",
        top_k=5,
        min_similarity=0.5,
    )
    
    print(f"   Resultados: {len(results)}")
    if results:
        for i, r in enumerate(results[:3], 1):
            direction = r.get('direction', 'N/A')
            lemma = r.get('lemma', 'N/A')
            gloss_bora = r.get('gloss_bora', 'N/A')
            gloss_es = r.get('gloss_es', 'N/A')
            similarity = r.get('similarity', 0.0)
            
            print(f"\n   {i}. Lemma: {lemma}")
            print(f"      Direction: {direction}")
            print(f"      Gloss ES: {gloss_es}")
            print(f"      Gloss Bora: {gloss_bora}")
            print(f"      Similarity: {similarity:.3f}")
            
            # Verificar que sea Bora→ES
            if direction == 'bora_es' and 'majtsí' in lemma.lower():
                print(f"      ✅ CORRECTO: Encontró palabra Bora en Bora→ES")
                if gloss_es:
                    print(f"      ✅ CORRECTO: Tiene traducción al español: {gloss_es}")
            elif direction != 'bora_es':
                print(f"      ❌ ERROR: Dirección incorrecta, esperaba 'bora_es'")
    else:
        print("   ❌ ERROR: No se encontraron resultados")


async def test_full_rag_pipeline():
    """Test del pipeline RAG completo con respuesta del LLM"""
    rag = RAGService()
    
    print("\n" + "=" * 80)
    print("TEST 3: Pipeline RAG Completo (con respuesta LLM)")
    print("=" * 80)
    
    # Test 1: Query ES→Bora
    print("\n📍 Test 3.1: 'Como se dice cantar en bora'")
    result = await rag.answer_with_lexicon(
        query="como se dice cantar en bora",
        top_k=5,
        min_similarity=0.5,
    )
    
    print(f"\n   Respuesta LLM:")
    print(f"   {result.get('answer', 'N/A')}")
    
    print(f"\n   Timings:")
    timings = result.get('timings', {})
    print(f"   - Direction detection: {timings.get('direction_detection_ms', 0):.2f} ms")
    print(f"   - Preprocessing: {timings.get('preprocessing_ms', 0):.2f} ms")
    print(f"   - Embedding: {timings.get('embedding_ms', 0):.2f} ms")
    print(f"   - Vector search: {timings.get('vector_search_ms', 0):.2f} ms")
    print(f"   - Total: {timings.get('total_ms', 0):.2f} ms")
    
    # Verificar que la respuesta mencione "majtsí"
    answer = result.get('answer', '').lower()
    if 'majtsí' in answer:
        print("\n   ✅ CORRECTO: Respuesta contiene 'majtsí'")
    else:
        print("\n   ❌ ADVERTENCIA: Respuesta no contiene 'majtsí'")
    
    # Test 2: Query Bora→ES
    print("\n📍 Test 3.2: 'Que significa majtsíva'")
    result = await rag.answer_with_lexicon(
        query="que significa majtsíva",
        top_k=5,
        min_similarity=0.5,
    )
    
    print(f"\n   Respuesta LLM:")
    print(f"   {result.get('answer', 'N/A')}")
    
    # Verificar que la respuesta esté relacionada con cantar/canción
    answer = result.get('answer', '').lower()
    if 'cantar' in answer or 'canción' in answer or 'canto' in answer:
        print("\n   ✅ CORRECTO: Respuesta relacionada con cantar/canción")
    else:
        print("\n   ❌ ADVERTENCIA: Respuesta no menciona cantar/canción")


async def main():
    """Ejecutar todos los tests"""
    print("\n🧪 TESTS DE BÚSQUEDA BIDIRECCIONAL\n")
    
    try:
        await test_direction_detection()
        await test_search_with_direction()
        await test_full_rag_pipeline()
        
        print("\n" + "=" * 80)
        print("✅ TODOS LOS TESTS COMPLETADOS")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERROR EN TESTS: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
