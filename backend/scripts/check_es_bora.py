import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv
load_dotenv(BACKEND_ROOT / '.env')

from adapters.supabase_adapter import SupabaseAdapter

supa = SupabaseAdapter(use_service_role=True)

# Verificar registros ES→Bora
result = supa.client.table('lexicon_lemmas').select('id,lemma,direction,source').eq('direction','es_bora').limit(10).execute()

print(f"\n📊 Registros con direction='es_bora': {len(result.data)}")
for r in result.data[:10]:
    print(f"  ID: {r['id']}, Lemma: '{r['lemma']}', Source: {r['source']}")

if len(result.data) == 0:
    print("\n✅ No hay registros ES→Bora (reset funcionó)")
else:
    print(f"\n⚠️  Hay {len(result.data)} registros ES→Bora (reset no completó)")
