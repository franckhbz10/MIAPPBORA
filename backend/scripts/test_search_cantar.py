"""
Script para diagnosticar por qué 'cantar' no encuentra 'majtsíva'
"""
import os
from dotenv import load_dotenv
from supabase import create_client
import json

# Cargar variables de entorno
load_dotenv()

# Conectar directamente a Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

def test_search():
    """Buscar 'cantar' en diferentes direcciones"""
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    print("🔍 DIAGNÓSTICO: Búsqueda de 'cantar'\n")
    print("=" * 60)
    
    # 1. Buscar directamente en lexicon_lemmas
    print("\n1️⃣ Buscando 'cantar' en lexicon_lemmas...")
    print("-" * 60)
    
    # ES→Bora (lemma debería ser 'cantar')
    res_es_bora = supabase.table('lexicon_lemmas')\
        .select('*')\
        .eq('direction', 'es_bora')\
        .ilike('lemma', '%cantar%')\
        .execute()
    
    print(f"✅ ES→Bora: {len(res_es_bora.data)} resultados")
    for item in res_es_bora.data[:3]:
        print(f"  - lemma='{item['lemma']}' gloss_bora='{item['gloss_bora']}' id={item['id']}")
    
    # Bora→ES (gloss_es debería contener 'cantar')
    res_bora_es = supabase.table('lexicon_lemmas')\
        .select('*')\
        .eq('direction', 'bora_es')\
        .ilike('gloss_es', '%cantar%')\
        .execute()
    
    print(f"✅ Bora→ES: {len(res_bora_es.data)} resultados")
    for item in res_bora_es.data[:3]:
        print(f"  - lemma='{item['lemma']}' gloss_es='{item['gloss_es']}' id={item['id']}")
    
    # 2. Buscar en bora_docs
    print("\n2️⃣ Buscando 'cantar' en bora_docs...")
    print("-" * 60)
    
    # ES→Bora
    res_docs_es_bora = supabase.table('bora_docs')\
        .select('*')\
        .eq('metadata->>direction', 'es_bora')\
        .ilike('content', '%cantar%')\
        .limit(5)\
        .execute()
    
    print(f"✅ ES→Bora docs: {len(res_docs_es_bora.data)} resultados")
    for doc in res_docs_es_bora.data[:3]:
        print(f"  - kind={doc['kind']} content='{doc['content'][:80]}...'")
    
    # Bora→ES
    res_docs_bora_es = supabase.table('bora_docs')\
        .select('*')\
        .eq('metadata->>direction', 'bora_es')\
        .ilike('content', '%cantar%')\
        .limit(5)\
        .execute()
    
    print(f"✅ Bora→ES docs: {len(res_docs_bora_es.data)} resultados")
    for doc in res_docs_bora_es.data[:3]:
        print(f"  - kind={doc['kind']} content='{doc['content'][:80]}...'")
    
    # 3. Verificar 'majtsíva' en la dirección opuesta
    print("\n3️⃣ Verificando 'majtsíva' en bora_docs...")
    print("-" * 60)
    
    res_majtsi = supabase.table('bora_docs')\
        .select('*')\
        .ilike('content', '%majtsí%')\
        .limit(5)\
        .execute()
    
    print(f"✅ Encontrados: {len(res_majtsi.data)} documentos con 'majtsí'")
    for doc in res_majtsi.data:
        direction = doc.get('metadata', {}).get('direction', 'N/A')
        print(f"  - kind={doc['kind']} direction={direction} content='{doc['content'][:100]}...'")
    
    # 4. Verificar el embedding de 'cantar'
    print("\n4️⃣ Verificando si 'cantar' tiene embedding...")
    print("-" * 60)
    
    if res_docs_es_bora.data:
        doc = res_docs_es_bora.data[0]
        has_emb = doc.get('embedding_1536') is not None
        print(f"✅ Primer documento 'cantar' tiene embedding_1536: {has_emb}")
    
    print("\n" + "=" * 60)
    print("✅ Diagnóstico completado\n")

if __name__ == '__main__':
    test_search()
