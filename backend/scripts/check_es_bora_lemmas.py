"""
Verifica cuántos documentos de tipo LEMMA ES→Bora existen en bora_docs
"""
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from adapters.supabase_adapter import SupabaseAdapter

def main():
    supa = SupabaseAdapter(use_service_role=True)
    
    print("📊 Analizando documentos LEMMA ES→Bora en bora_docs...\n")
    
    # 1. Total de lemmas ES→Bora en bora_docs
    resp = supa.client.table('bora_docs').select('id, parent_lemma_id, content, metadata', count='exact').eq('kind', 'lemma').execute()
    
    all_lemma_docs = resp.data or []
    total_count = resp.count
    
    print(f"1️⃣ Total de documentos LEMMA en bora_docs: {total_count}")
    
    # 2. Contar por dirección
    es_bora_count = 0
    bora_es_count = 0
    no_direction = 0
    
    for doc in all_lemma_docs:
        metadata = doc.get('metadata', {})
        direction = metadata.get('direction')
        
        if direction == 'es_bora':
            es_bora_count += 1
        elif direction == 'bora_es':
            bora_es_count += 1
        else:
            no_direction += 1
    
    print(f"\n2️⃣ Distribución por dirección (muestra de {len(all_lemma_docs)}):")
    print(f"  ES→Bora (es_bora):  {es_bora_count}")
    print(f"  Bora→ES (bora_es):  {bora_es_count}")
    print(f"  Sin dirección:      {no_direction}")
    
    # 3. Buscar "cantar" específicamente
    print(f"\n3️⃣ Buscando lemma 'cantar'...")
    
    # Primero buscar el ID de "cantar" en lexicon_lemmas
    lemma_resp = supa.client.table('lexicon_lemmas').select('id, lemma, gloss_bora, direction').eq('lemma', 'cantar').eq('direction', 'es_bora').execute()
    
    if lemma_resp.data:
        cantar_lemma = lemma_resp.data[0]
        cantar_id = cantar_lemma['id']
        
        print(f"  ✅ Lemma 'cantar' en lexicon_lemmas:")
        print(f"     ID: {cantar_id}")
        print(f"     Gloss Bora: {cantar_lemma.get('gloss_bora')}")
        
        # Buscar documento en bora_docs
        doc_resp = supa.client.table('bora_docs').select('*').eq('kind', 'lemma').eq('parent_lemma_id', cantar_id).execute()
        
        if doc_resp.data:
            cantar_doc = doc_resp.data[0]
            print(f"\n  ✅ Documento en bora_docs:")
            print(f"     Content: {cantar_doc.get('content')[:100]}...")
            print(f"     Has embedding_1536: {bool(cantar_doc.get('embedding_1536'))}")
        else:
            print(f"\n  ❌ NO se encontró documento en bora_docs para lemma_id={cantar_id}")
    else:
        print(f"  ❌ Lemma 'cantar' NO encontrado en lexicon_lemmas")
    
    print("\n✅ Análisis completado")

if __name__ == '__main__':
    main()
