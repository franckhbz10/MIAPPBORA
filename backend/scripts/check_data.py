import sys
from pathlib import Path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from adapters.supabase_adapter import get_supabase_adapter

s = get_supabase_adapter()

# Check bora_phrases (source)
r = s.client.table('bora_phrases').select('id').limit(5).execute()
print(f"bora_phrases: {len(r.data)} filas")

# Check phrase_embeddings
r = s.client.table('phrase_embeddings').select('id,phrase_id,embedding_1536').limit(10).execute()
print(f"phrase_embeddings: {len(r.data)} filas")
if r.data:
    for d in r.data[:3]:
        print(f"  id={d['id']}, phrase_id={d['phrase_id']}, has_1536={d['embedding_1536'] is not None}")

# Check bora_docs
r = s.client.table('bora_docs').select('id,kind,embedding_1536').limit(10).execute()
print(f"\nbora_docs: {len(r.data)} filas")
if r.data:
    for d in r.data[:3]:
        has_vec = d['embedding_1536'] is not None
        print(f"  id={d['id']}, kind={d['kind']}, has_1536={has_vec}")

# Check lexicon_entries
r = s.client.table('lexicon_entries').select('id').limit(5).execute()
print(f"\nlexicon_entries: {len(r.data)} filas")

# Check lexicon_embeddings
r = s.client.table('lexicon_embeddings').select('id,entry_id,embedding_1536').limit(10).execute()
print(f"lexicon_embeddings: {len(r.data)} filas")
if r.data:
    for d in r.data[:3]:
        has_vec = d['embedding_1536'] is not None
        print(f"  id={d['id']}, entry_id={d['entry_id']}, has_1536={has_vec}")
