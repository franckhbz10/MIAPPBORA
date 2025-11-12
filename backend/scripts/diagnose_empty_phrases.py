"""
Script simple para diagnosticar frases vacías en el sistema
"""
import os
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

# Cargar .env
backend_dir = Path(__file__).parent.parent
load_dotenv(backend_dir / '.env')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("🔍 Diagnóstico de frases vacías en el sistema\n")
print("=" * 80)

# 1. Verificar bora_docs (sin JOINS) - solo content
print("\n1️⃣ Verificando content en bora_docs:")
print("-" * 80)
res = supabase.table('bora_docs').select('id, kind, parent_lemma_id, content').limit(5).execute()
for doc in res.data:
    content_preview = (doc.get('content') or '')[:80]
    print(f"ID {doc['id']} | Kind: {doc['kind']:<10} | Content: '{content_preview}...'")

# 2. Verificar si parent_lemma_id corresponde a registros existentes
print("\n2️⃣ Verificando integridad de parent_lemma_id:")
print("-" * 80)
res_docs = supabase.table('bora_docs').select('id, parent_lemma_id').limit(10).execute()
doc_ids = [d['parent_lemma_id'] for d in res_docs.data]

res_lemmas = supabase.table('lexicon_lemmas').select('id, lemma, gloss_es, gloss_bora, direction').in_('id', doc_ids).execute()
existing_ids = {l['id'] for l in res_lemmas.data}

print(f"bora_docs analizados: {len(doc_ids)}")
print(f"lexicon_lemmas encontrados: {len(existing_ids)}")

missing_ids = [did for did in doc_ids if did not in existing_ids]
if missing_ids:
    print(f"⚠️ PROBLEMA: {len(missing_ids)} parent_lemma_id sin registro en lexicon_lemmas:")
    print(f"   IDs faltantes: {missing_ids}")
else:
    print("✅ Todos los parent_lemma_id existen en lexicon_lemmas")

# 3. Verificar ejemplos con example_id pero sin registro
print("\n3️⃣ Verificando integridad de example_id:")
print("-" * 80)
res_examples = supabase.table('bora_docs').select('id, kind, example_id').eq('kind', 'example').not_.is_('example_id', 'null').limit(10).execute()

if res_examples.data:
    example_ids = [e['example_id'] for e in res_examples.data]
    res_lex_ex = supabase.table('lexicon_examples').select('id, bora_text, spanish_text').in_('id', example_ids).execute()
    existing_ex_ids = {e['id'] for e in res_lex_ex.data}
    
    print(f"bora_docs (kind=example) analizados: {len(example_ids)}")
    print(f"lexicon_examples encontrados: {len(existing_ex_ids)}")
    
    missing_ex = [eid for eid in example_ids if eid not in existing_ex_ids]
    if missing_ex:
        print(f"⚠️ PROBLEMA: {len(missing_ex)} example_id sin registro en lexicon_examples:")
        print(f"   IDs faltantes: {missing_ex[:5]}")
    else:
        print("✅ Todos los example_id existen en lexicon_examples")
    
    # Mostrar ejemplos de registros completos
    print("\n   Ejemplos de lexicon_examples:")
    for ex in res_lex_ex.data[:3]:
        print(f"   - ID {ex['id']}: bora='{ex.get('bora_text', 'NULL')}' | es='{ex.get('spanish_text', 'NULL')}'")
else:
    print("No se encontraron bora_docs con kind=example")

# 4. Simular la query de match_bora_docs_v2 manualmente
print("\n4️⃣ Simulando JOIN de match_bora_docs_v2:")
print("-" * 80)

# Tomar un bora_doc de ejemplo
res_sample = supabase.table('bora_docs').select('id, kind, parent_lemma_id, subentry_id, example_id').limit(3).execute()

for doc in res_sample.data:
    print(f"\nbora_doc ID {doc['id']} (kind={doc['kind']}):")
    
    # JOIN con lexicon_lemmas
    res_lemma = supabase.table('lexicon_lemmas').select('lemma, gloss_es, gloss_bora, direction').eq('id', doc['parent_lemma_id']).execute()
    if res_lemma.data:
        lemma_data = res_lemma.data[0]
        print(f"  ✅ lexicon_lemmas: lemma='{lemma_data.get('lemma')}' gloss_es='{lemma_data.get('gloss_es')}' gloss_bora='{lemma_data.get('gloss_bora')}' direction='{lemma_data.get('direction')}'")
    else:
        print(f"  ❌ lexicon_lemmas: NO ENCONTRADO (parent_lemma_id={doc['parent_lemma_id']})")
    
    # LEFT JOIN con lexicon_examples
    if doc.get('example_id'):
        res_ex = supabase.table('lexicon_examples').select('bora_text, spanish_text').eq('id', doc['example_id']).execute()
        if res_ex.data:
            ex_data = res_ex.data[0]
            print(f"  ✅ lexicon_examples: bora='{ex_data.get('bora_text')}' es='{ex_data.get('spanish_text')}'")
        else:
            print(f"  ❌ lexicon_examples: NO ENCONTRADO (example_id={doc['example_id']})")
    
    # LEFT JOIN con lexicon_subentries
    if doc.get('subentry_id'):
        res_sub = supabase.table('lexicon_subentries').select('gloss_es, gloss_bora').eq('id', doc['subentry_id']).execute()
        if res_sub.data:
            sub_data = res_sub.data[0]
            print(f"  ✅ lexicon_subentries: gloss_es='{sub_data.get('gloss_es')}' gloss_bora='{sub_data.get('gloss_bora')}'")
        else:
            print(f"  ❌ lexicon_subentries: NO ENCONTRADO (subentry_id={doc['subentry_id']})")

print("\n" + "=" * 80)
print("✅ Diagnóstico completado\n")
