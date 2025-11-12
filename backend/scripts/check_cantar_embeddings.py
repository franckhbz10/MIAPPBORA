"""Verificar si 'cantar' tiene embeddings en bora_docs"""
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')
)

# 1. Buscar lemma "cantar" en lexicon_lemmas
print("=" * 80)
print("1️⃣ Buscando lemma 'cantar' en lexicon_lemmas")
print("=" * 80)

lemma_result = supabase.table('lexicon_lemmas')\
    .select('*')\
    .eq('lemma', 'cantar')\
    .execute()

if lemma_result.data:
    lemma = lemma_result.data[0]
    print(f"✅ Encontrado:")
    print(f"   ID: {lemma['id']}")
    print(f"   Lemma: {lemma['lemma']}")
    print(f"   Gloss ES: {lemma.get('gloss_es', 'N/A')}")
    print(f"   Gloss Bora: {lemma.get('gloss_bora', 'N/A')}")
    print(f"   Direction: {lemma.get('direction', 'N/A')}")
    print(f"   POS: {lemma.get('pos_full', 'N/A')}")
    
    lemma_id = lemma['id']
    
    # 2. Buscar documentos en bora_docs con ese parent_lemma_id
    print(f"\n2️⃣ Buscando documentos en bora_docs con parent_lemma_id={lemma_id}")
    print("=" * 80)
    
    docs_result = supabase.table('bora_docs')\
        .select('*')\
        .eq('parent_lemma_id', lemma_id)\
        .execute()
    
    print(f"✅ Documentos encontrados: {len(docs_result.data)}\n")
    
    for i, doc in enumerate(docs_result.data, 1):
        has_emb = doc.get('embedding_1536') is not None
        print(f"{i}. ID: {doc['id']}")
        print(f"   Kind: {doc['kind']}")
        print(f"   Has embedding_1536: {'✅' if has_emb else '❌'}")
        print(f"   Content: {doc['content'][:200]}")
        print()
else:
    print("❌ NO se encontró lemma 'cantar' en lexicon_lemmas")
