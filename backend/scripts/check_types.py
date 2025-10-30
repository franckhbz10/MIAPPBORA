import sys
from pathlib import Path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from adapters.supabase_adapter import get_supabase_adapter

s = get_supabase_adapter()

# Check schema de bora_phrases
try:
    r = s.client.table('bora_phrases').select('id,difficulty_level').limit(3).execute()
    print(f"bora_phrases sample:")
    for row in r.data:
        print(f"  id={row['id']} (type: {type(row['id']).__name__}), difficulty_level={row.get('difficulty_level')} (type: {type(row.get('difficulty_level')).__name__})")
except Exception as e:
    print(f"Error: {e}")

# Check schema de phrase_embeddings
try:
    r = s.client.table('phrase_embeddings').select('id,phrase_id').limit(3).execute()
    print(f"\nphrase_embeddings sample:")
    for row in r.data:
        print(f"  id={row['id']} (type: {type(row['id']).__name__}), phrase_id={row['phrase_id']} (type: {type(row['phrase_id']).__name__})")
except Exception as e:
    print(f"Error: {e}")
