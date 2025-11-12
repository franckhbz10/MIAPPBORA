"""
Test del flujo completo: Embedding → Vector Search → Contexto LLM
Simula exactamente lo que pasa en producción
"""
import asyncio
import sys
from pathlib import Path

# Agregar backend al path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services.rag_service import RAGService
from config.settings import settings

async def test_llm_embedding_flow():
    """
    Test completo del flujo de embeddings en el RAG
    """
    
    print("=" * 100)
    print("🔍 TEST FLUJO COMPLETO: EMBEDDING → VECTOR SEARCH → CONTEXTO LLM")
    print("=" * 100)
    
    # Inicializar RAG service
    print("\n🔧 PASO 1: Inicializar RAG Service")
    try:
        rag_service = RAGService()
        print("   ✅ RAG Service inicializado")
        print(f"   📊 HF Adapter tipo: {type(rag_service.hf_adapter).__name__}")
        print(f"   📊 Supabase Adapter presente: {rag_service.supabase_adapter is not None}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test queries
    test_queries = [
        "abrazar",
        "cantar",
        "como se dice casa en bora",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 100}")
        print(f"🧪 TEST {i}/{len(test_queries)}: '{query}'")
        print(f"{'=' * 100}")
        
        # PASO 1: Generar embedding
        print(f"\n   📊 PASO 1: Generar embedding para '{query}'")
        try:
            embedding = rag_service.hf_adapter.generate_embedding(query)
            
            if embedding:
                print(f"      ✅ Embedding generado")
                print(f"      📏 Dimensiones: {len(embedding)}")
                print(f"      🔢 Primeros 3: {[f'{x:.6f}' for x in embedding[:3]]}")
                print(f"      📈 Min: {min(embedding):.6f}, Max: {max(embedding):.6f}")
                
                # Verificar no-ceros
                non_zero = sum(1 for x in embedding if abs(x) > 0.0001)
                pct = non_zero/len(embedding)*100
                print(f"      ✓ Valores no-cero: {non_zero}/{len(embedding)} ({pct:.1f}%)")
                
                if non_zero == 0:
                    print(f"      ⚠️  PROBLEMA: Todos los valores son CERO!")
                    continue
            else:
                print(f"      ❌ Embedding es None")
                continue
                
        except Exception as e:
            print(f"      ❌ Error generando embedding: {e}")
            import traceback
            traceback.print_exc()
            continue
        
        # PASO 2: Vector Search en Supabase
        print(f"\n   🔍 PASO 2: Vector Search en Supabase (top_k=5, threshold=0.0)")
        try:
            results = await rag_service.supabase_adapter.vector_search_bora_docs(
                query_embedding=embedding,
                top_k=5,
                kinds=None,
                pos_full=None,
                min_similarity=0.0,  # Sin filtro
                direction=None,  # Ambas direcciones
            )
            
            if results:
                print(f"      ✅ Encontrados {len(results)} resultados")
                
                # Mostrar top 5
                for j, hit in enumerate(results[:5], 1):
                    similarity = hit.get('similarity', 0)
                    gloss_es = hit.get('gloss_es', 'N/A')
                    gloss_bora = hit.get('gloss_bora', 'N/A')
                    direction = hit.get('direction', 'N/A')
                    kind = hit.get('kind', 'N/A')
                    
                    print(f"\n      #{j} - Similarity: {similarity:.4f}")
                    print(f"          ES: {gloss_es}")
                    print(f"          Bora: {gloss_bora}")
                    print(f"          Direction: {direction}")
                    print(f"          Kind: {kind}")
            else:
                print(f"      ⚠️  Sin resultados")
                continue
                
        except Exception as e:
            print(f"      ❌ Error en vector search: {e}")
            import traceback
            traceback.print_exc()
            continue
        
        # PASO 3: Simular flujo completo del RAG (search_lexicon)
        print(f"\n   🎯 PASO 3: Flujo completo search_lexicon()")
        try:
            lexicon_results = await rag_service.search_lexicon(
                query=query,
                top_k=5,
                min_similarity=0.0,
                category=None,
                direction=None,
            )
            
            if lexicon_results:
                print(f"      ✅ search_lexicon retornó {len(lexicon_results)} resultados")
                
                for j, result in enumerate(lexicon_results[:3], 1):
                    print(f"\n      #{j}")
                    print(f"          Similarity: {result.get('similarity', 'N/A'):.4f}")
                    print(f"          ES: {result.get('gloss_es', 'N/A')}")
                    print(f"          Bora: {result.get('gloss_bora', 'N/A')}")
                    print(f"          Direction: {result.get('direction', 'N/A')}")
            else:
                print(f"      ⚠️  search_lexicon retornó lista vacía")
                
        except Exception as e:
            print(f"      ❌ Error en search_lexicon: {e}")
            import traceback
            traceback.print_exc()
        
        # PASO 4: Simular answer_with_lexicon (sin llamar al LLM, solo ver el contexto)
        print(f"\n   📝 PASO 4: Generar contexto para LLM (sin llamar al LLM)")
        try:
            # Usar método privado para generar embedding y buscar
            cleaned_query = query  # Simplificado
            emb = rag_service.hf_adapter.generate_embedding(cleaned_query)
            
            if emb:
                hits = await rag_service.supabase_adapter.vector_search_bora_docs(
                    query_embedding=emb,
                    top_k=5,
                    kinds=None,
                    pos_full=None,
                    min_similarity=0.7,  # Threshold de producción
                    direction=None,
                )
                
                print(f"      📊 Hits con threshold 0.7: {len(hits) if hits else 0}")
                
                if hits and len(hits) > 0:
                    print(f"\n      📋 CONTEXTO QUE RECIBIRÍA EL LLM:")
                    print(f"      " + "-" * 90)
                    
                    # Simular formato de contexto
                    for idx, hit in enumerate(hits[:3], 1):
                        gloss_es = hit.get('gloss_es', '')
                        gloss_bora = hit.get('gloss_bora', '')
                        direction = hit.get('direction', '')
                        similarity = hit.get('similarity', 0)
                        
                        if direction == 'es_bora':
                            print(f"      {idx}. Definición: Español: {gloss_es}, Bora: {gloss_bora}")
                        else:
                            print(f"      {idx}. Definición: Bora: {gloss_es}, Español: {gloss_bora}")
                        
                        print(f"         (Similarity: {similarity:.4f})")
                    
                    print(f"      " + "-" * 90)
                else:
                    print(f"      ⚠️  Sin hits con threshold 0.7")
                    
        except Exception as e:
            print(f"      ❌ Error simulando contexto: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'=' * 100}")
    print("✅ TEST COMPLETADO")
    print("=" * 100)


if __name__ == "__main__":
    asyncio.run(test_llm_embedding_flow())
