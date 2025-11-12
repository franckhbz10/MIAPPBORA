"""Verificar cuántos documentos ES→Bora hay en bora_docs"""
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')
)

# 1. Contar lemmas ES→Bora en lexicon_lemmas
lemmas_result = supabase.table('lexicon_lemmas')\
    .select('*', count='exact')\
    .eq('direction', 'es_bora')\
    .execute()

print(f"📊 Lemmas ES→Bora en lexicon_lemmas: {lemmas_result.count}")

# 2. Contar documentos ES→Bora en bora_docs
# Necesitamos hacer un JOIN con lexicon_lemmas para obtener la dirección
docs_result = supabase.rpc('count_docs_by_direction', {
    'dir': 'es_bora'
}).execute()

print(f"\n📊 Intentando contar docs ES→Bora en bora_docs...")

# Alternativa: Seleccionar muestra y contar manualmente
sample = supabase.table('bora_docs')\
    .select('id, kind, parent_lemma_id')\
    .limit(1000)\
    .execute()

# Para cada doc, verificar si su parent_lemma tiene direction='es_bora'
es_bora_count = 0
bora_es_count = 0

for doc in sample.data:
    lemma_id = doc['parent_lemma_id']
    lemma = supabase.table('lexicon_lemmas')\
        .select('direction')\
        .eq('id', lemma_id)\
        .single()\
        .execute()
    
    if lemma.data and lemma.data.get('direction') == 'es_bora':
        es_bora_count += 1
    else:
        bora_es_count += 1

print(f"\n📊 Muestra de 1000 docs en bora_docs:")
print(f"   ES→Bora: {es_bora_count}")
print(f"   Bora→ES: {bora_es_count}")
print(f"   Proporción ES→Bora: {es_bora_count/10:.1f}%")
