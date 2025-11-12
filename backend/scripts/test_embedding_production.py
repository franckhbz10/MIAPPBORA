"""
Test de embeddings en producción - Diagnóstico completo
Verifica HuggingFace adapter y búsqueda vectorial
"""
import asyncio
import sys
import os
from pathlib import Path

# Agregar backend al path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from adapters.huggingface_adapter_hybrid import HuggingFaceAdapterHybrid
from adapters.supabase_adapter import SupabaseAdapter
from config.settings import settings


async def test_embedding_pipeline():
    """Test completo del pipeline de embeddings"""
    
    print("=" * 80)
    print("🔍 TEST DE EMBEDDINGS EN PRODUCCIÓN")
    print("=" * 80)
    
    # 1. Verificar configuración
    print("\n📋 PASO 1: Verificar configuración")
    print(f"   HF_API_KEY configurado: {'✅' if settings.HF_API_KEY else '❌'}")
    print(f"   HF_API_KEY length: {len(settings.HF_API_KEY) if settings.HF_API_KEY else 0}")
    print(f"   OPENAI_API_KEY configurado: {'✅' if settings.OPENAI_API_KEY else '❌'}")
    print(f"   SUPABASE_URL: {settings.SUPABASE_URL[:30]}..." if settings.SUPABASE_URL else "❌")
    
    # 2. Inicializar adaptadores
    print("\n🔧 PASO 2: Inicializar adaptadores")
    try:
        hf_adapter = HuggingFaceAdapterHybrid()
        print("   ✅ HuggingFace adapter creado")
    except Exception as e:
        print(f"   ❌ Error creando HF adapter: {e}")
        return
    
    try:
        supabase_adapter = SupabaseAdapter()
        print("   ✅ Supabase adapter creado")
    except Exception as e:
        print(f"   ❌ Error creando Supabase adapter: {e}")
        return
    
    # 3. Test queries
    test_queries = [
        "abrazar",
        "cantar",
        "como se dice casa en bora",
        "que significa majtsíva"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"🧪 TEST {i}/4: '{query}'")
        print(f"{'=' * 80}")
        
        # 3.1 Generar embedding
        print(f"\n   📊 Generando embedding...")
        try:
            embedding = hf_adapter.generate_embedding(query)
            
            if embedding:
                print(f"   ✅ Embedding generado exitosamente")
                print(f"   📏 Dimensiones: {len(embedding)}")
                print(f"   🔢 Primeros 5 valores: {embedding[:5]}")
                print(f"   📈 Min: {min(embedding):.6f}, Max: {max(embedding):.6f}")
                
                # Verificar que no sean todos ceros
                non_zero = sum(1 for x in embedding if abs(x) > 0.0001)
                print(f"   🎯 Valores no-cero: {non_zero}/{len(embedding)} ({non_zero/len(embedding)*100:.1f}%)")
                
                if non_zero == 0:
                    print(f"   ⚠️  WARNING: Todos los valores son cero!")
                
            else:
                print(f"   ❌ Embedding es None o vacío")
                continue
                
        except Exception as e:
            print(f"   ❌ Error generando embedding: {e}")
            import traceback
            traceback.print_exc()
            continue
        
        # 3.2 Buscar en Supabase
        print(f"\n   🔍 Buscando en Supabase (top_k=5, threshold=0.0)...")
        try:
            results = await supabase_adapter.vector_search_bora_docs(
                query_embedding=embedding,
                top_k=5,
                kinds=None,
                pos_full=None,
                min_similarity=0.0,  # Sin filtro para ver todos los resultados
                direction=None,
            )
            
            if results:
                print(f"   ✅ Encontrados {len(results)} resultados")
                print(f"\n   📋 Top 5 resultados:")
                for j, hit in enumerate(results[:5], 1):
                    similarity = hit.get('similarity', 0)
                    lemma = hit.get('gloss_es', 'N/A')
                    lemma_bora = hit.get('gloss_bora', 'N/A')
                    direction = hit.get('direction', 'N/A')
                    kind = hit.get('kind', 'N/A')
                    
                    print(f"   {j}. Similarity: {similarity:.4f}")
                    print(f"      Lemma ES: {lemma}")
                    print(f"      Lemma Bora: {lemma_bora}")
                    print(f"      Direction: {direction}")
                    print(f"      Kind: {kind}")
                    print()
            else:
                print(f"   ⚠️  No se encontraron resultados")
                
        except Exception as e:
            print(f"   ❌ Error en búsqueda: {e}")
            import traceback
            traceback.print_exc()
    
    # 4. Test directo a la API de HuggingFace
    print(f"\n{'=' * 80}")
    print(f"🌐 TEST DIRECTO A HUGGINGFACE API")
    print(f"{'=' * 80}")
    
    try:
        import httpx
        
        api_url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        headers = {"Authorization": f"Bearer {settings.HF_API_KEY}"}
        
        test_text = "abrazar"
        print(f"\n   📤 Enviando request a HuggingFace API")
        print(f"   🔑 API Key (primeros 10 chars): {settings.HF_API_KEY[:10]}...")
        print(f"   📝 Texto: '{test_text}'")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                api_url,
                headers=headers,
                json={"inputs": test_text, "options": {"wait_for_model": True}}
            )
            
            print(f"\n   📥 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    embedding = data[0]
                    print(f"   ✅ Embedding recibido")
                    print(f"   📏 Dimensiones: {len(embedding)}")
                    print(f"   🔢 Primeros 5 valores: {embedding[:5]}")
                else:
                    print(f"   ⚠️  Formato inesperado: {type(data)}")
            else:
                print(f"   ❌ Error HTTP {response.status_code}")
                print(f"   📄 Response: {response.text[:500]}")
                
    except Exception as e:
        print(f"   ❌ Error en test directo: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'=' * 80}")
    print("✅ DIAGNÓSTICO COMPLETADO")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_embedding_pipeline())
