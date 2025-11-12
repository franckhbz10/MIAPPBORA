"""
Script para verificar qué frases tienen campos vacíos en bora_docs
y entender por qué algunas frases aparecen vacías en el frontend
"""
import asyncio
import sys
from pathlib import Path

# Añadir el directorio backend al path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from adapters.supabase_adapter import get_supabase_adapter
from config.settings import settings

async def check_empty_phrases():
    supabase = get_supabase_adapter()
    
    print("🔍 Verificando frases con campos vacíos en bora_docs...\n")
    
    # 1. Buscar documentos con content vacío o NULL
    print("1️⃣ Documentos con content vacío/NULL:")
    print("-" * 50)
    try:
        # Verificar content vacío
        res_empty = supabase.client.table('bora_docs').select(
            'id, kind, lemma, content, metadata'
        ).or_('content.is.null,content.eq.').limit(20).execute()
        
        empty_docs = res_empty.data or []
        if empty_docs:
            print(f"   Encontrados: {len(empty_docs)} documentos con content vacío")
            for doc in empty_docs[:5]:  # Mostrar solo primeros 5
                print(f"   - ID: {doc['id']} | Kind: {doc['kind']} | Lemma: {doc.get('lemma', 'N/A')}")
                print(f"     Content: '{doc.get('content', '')}' | Metadata: {doc.get('metadata', {})}")
        else:
            print("   ✅ No se encontraron documentos con content vacío")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n2️⃣ Muestreo de lemmas y sus campos:")
    print("-" * 50)
    try:
        # Obtener muestra de lemmas
        res_lemmas = supabase.client.table('bora_docs').select(
            'id, kind, lemma, content, gloss_es, gloss_bora, metadata'
        ).eq('kind', 'lemma').limit(10).execute()
        
        lemmas = res_lemmas.data or []
        for lemma in lemmas:
            direction = lemma.get('metadata', {}).get('direction', 'N/A')
            print(f"\n   Lemma: {lemma.get('lemma', 'N/A')} | Direction: {direction}")
            print(f"   - Content: '{lemma.get('content', '')[:50]}...'")
            print(f"   - gloss_es: {lemma.get('gloss_es', 'N/A')}")
            print(f"   - gloss_bora: {lemma.get('gloss_bora', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n3️⃣ Verificar ejemplos con bora_text o spanish_text vacíos:")
    print("-" * 50)
    try:
        # Buscar ejemplos con campos vacíos
        res_examples = supabase.client.table('bora_docs').select(
            'id, kind, lemma, bora_text, spanish_text, content'
        ).eq('kind', 'example').or_(
            'bora_text.is.null,bora_text.eq.,spanish_text.is.null,spanish_text.eq.'
        ).limit(10).execute()
        
        empty_examples = res_examples.data or []
        if empty_examples:
            print(f"   Encontrados: {len(empty_examples)} ejemplos con campos vacíos")
            for ex in empty_examples[:5]:
                print(f"   - ID: {doc['id']} | Lemma: {ex.get('lemma', 'N/A')}")
                print(f"     bora_text: '{ex.get('bora_text', '')}' | spanish_text: '{ex.get('spanish_text', '')}'")
        else:
            print("   ✅ No se encontraron ejemplos con campos vacíos")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n4️⃣ Simulando búsqueda vectorial (como en el frontend):")
    print("-" * 50)
    try:
        # Generar embedding de prueba
        from adapters.huggingface_adapter import get_huggingface_adapter
        hf = get_huggingface_adapter()
        
        test_query = "casa"
        print(f"   Query de prueba: '{test_query}'")
        emb = hf.generate_embedding(test_query)
        
        if emb:
            # Llamar a la función RPC como lo hace el RAG
            rpc_name = 'match_bora_docs_v2' if settings.USE_VECTOR_1536 else 'match_bora_docs'
            print(f"   Usando RPC: {rpc_name}")
            
            res = supabase.client.rpc(rpc_name, {
                'query_embedding': emb,
                'match_threshold': 0.5,
                'match_count': 5,
                'kind_filter': None,
                'pos_filter': None,
            }).execute()
            
            hits = res.data or []
            print(f"\n   Resultados encontrados: {len(hits)}")
            for i, hit in enumerate(hits, 1):
                print(f"\n   {i}. Kind: {hit.get('kind')} | Similarity: {hit.get('similarity', 0):.3f}")
                print(f"      Lemma: {hit.get('lemma', 'N/A')}")
                print(f"      gloss_es: {hit.get('gloss_es', 'N/A')}")
                print(f"      gloss_bora: {hit.get('gloss_bora', 'N/A')}")
                print(f"      bora_text: {hit.get('bora_text', 'N/A')}")
                print(f"      spanish_text: {hit.get('spanish_text', 'N/A')}")
                print(f"      direction: {hit.get('direction', 'N/A')}")
                
                # DIAGNÓSTICO: ¿Qué campos están vacíos?
                empty_fields = []
                if not hit.get('lemma'):
                    empty_fields.append('lemma')
                if not hit.get('gloss_es'):
                    empty_fields.append('gloss_es')
                if not hit.get('gloss_bora'):
                    empty_fields.append('gloss_bora')
                if hit.get('kind') == 'example':
                    if not hit.get('bora_text'):
                        empty_fields.append('bora_text')
                    if not hit.get('spanish_text'):
                        empty_fields.append('spanish_text')
                
                if empty_fields:
                    print(f"      ⚠️ CAMPOS VACÍOS: {', '.join(empty_fields)}")
        else:
            print("   ❌ No se pudo generar embedding")
    except Exception as e:
        print(f"   ❌ Error en búsqueda: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(check_empty_phrases())
