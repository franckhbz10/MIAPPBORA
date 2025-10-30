"""
Script de verificación para RPCs v2 (1536 dims)
Consulta las tablas y llama a las RPCs v2 para validar que devuelven resultados.
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from adapters.supabase_adapter import get_supabase_adapter
from adapters.huggingface_adapter import get_huggingface_adapter

def main():
    supa = get_supabase_adapter()
    hf = get_huggingface_adapter()
    
    if not supa.is_connected():
        print("❌ Supabase no conectado")
        return
    
    print("✓ Supabase conectado\n")
    
    # 1) Verificar columnas embedding_1536
    print("📊 Verificando columnas embedding_1536...")
    
    # bora_docs
    res = supa.client.table('bora_docs').select('id, embedding_1536').not_.is_('embedding_1536', 'null').limit(3).execute()
    print(f"  bora_docs: {len(res.data or [])} filas con embedding_1536")
    
    # phrase_embeddings
    res = supa.client.table('phrase_embeddings').select('id, embedding_1536').not_.is_('embedding_1536', 'null').limit(3).execute()
    print(f"  phrase_embeddings: {len(res.data or [])} filas con embedding_1536")
    
    # lexicon_embeddings
    res = supa.client.table('lexicon_embeddings').select('id, embedding_1536').not_.is_('embedding_1536', 'null').limit(3).execute()
    print(f"  lexicon_embeddings: {len(res.data or [])} filas con embedding_1536")
    
    print("\n🔍 Probando RPCs v2 con un embedding de prueba...")
    
    # Generar embedding de prueba
    test_query = "Hola, ¿cómo estás?"
    test_vec = hf.generate_embedding(test_query)
    
    if not test_vec:
        print("❌ No se pudo generar embedding de prueba")
        return
    
    print(f"  Query: '{test_query}' -> vector de {len(test_vec)} dims\n")
    
    # Test match_bora_docs_v2
    try:
        res = supa.client.rpc('match_bora_docs_v2', {
            'query_embedding': test_vec,
            'match_threshold': 0.3,
            'match_count': 3,
        }).execute()
        print(f"  ✓ match_bora_docs_v2: {len(res.data or [])} resultados")
    except Exception as e:
        print(f"  ❌ match_bora_docs_v2 falló: {e}")
    
    # Test match_phrases_v2
    try:
        res = supa.client.rpc('match_phrases_v2', {
            'query_embedding': test_vec,
            'match_threshold': 0.3,
            'match_count': 3,
        }).execute()
        print(f"  ✓ match_phrases_v2: {len(res.data or [])} resultados")
    except Exception as e:
        print(f"  ❌ match_phrases_v2 falló: {e}")
    
    # Test match_lexicon_v2
    try:
        res = supa.client.rpc('match_lexicon_v2', {
            'query_embedding': test_vec,
            'match_threshold': 0.3,
            'match_count': 3,
        }).execute()
        print(f"  ✓ match_lexicon_v2: {len(res.data or [])} resultados")
    except Exception as e:
        print(f"  ❌ match_lexicon_v2 falló: {e}")
    
    print("\n✅ Verificación completada!")

if __name__ == '__main__':
    main()
