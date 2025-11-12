"""
Verificar distribución de tipos y direcciones en bora_docs
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Cargar .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

print("📊 Analizando bora_docs...\n")

# 1. Totales por kind
print("1️⃣ Distribución por KIND:")
print("-" * 50)
for kind in ['lemma', 'subentry', 'example']:
    result = supabase.table('bora_docs').select('id', count='exact').eq('kind', kind).execute()
    print(f"  {kind:12} = {result.count:,} documentos")

# 2. Totales por dirección (metadata->>direction)
print("\n2️⃣ Distribución por DIRECCIÓN:")
print("-" * 50)

# Obtener muestra para analizar metadata
sample = supabase.table('bora_docs').select('id,kind,metadata').limit(100).execute()

bora_es_count = 0
es_bora_count = 0
no_direction = 0

for doc in sample.data:
    direction = doc.get('metadata', {}).get('direction')
    if direction == 'bora_es':
        bora_es_count += 1
    elif direction == 'es_bora':
        es_bora_count += 1
    else:
        no_direction += 1

print(f"  Muestra de 100 documentos:")
print(f"    Bora→ES (bora_es):  {bora_es_count}")
print(f"    ES→Bora (es_bora):  {es_bora_count}")
print(f"    Sin dirección:      {no_direction}")

# Mostrar ejemplos
print(f"\n  Ejemplos:")
for doc in sample.data[:5]:
    direction = doc.get('metadata', {}).get('direction', 'N/A')
    kind = doc.get('kind', 'N/A')
    source = doc.get('metadata', {}).get('source', 'N/A')
    print(f"    - kind={kind:10} direction={direction:10} source={source}")

# 3. Verificar embeddings
print("\n3️⃣ Estado de EMBEDDINGS:")
print("-" * 50)

# Con embedding_1536
result_1536 = supabase.table('bora_docs').select('id', count='exact').not_.is_('embedding_1536', 'null').execute()
print(f"  Con embedding_1536 (OpenAI):  {result_1536.count:,}")

# Con embedding (384)
result_384 = supabase.table('bora_docs').select('id', count='exact').not_.is_('embedding', 'null').execute()
print(f"  Con embedding (384 HF):       {result_384.count:,}")

# Sin ningún embedding
result_none = supabase.table('bora_docs').select('id', count='exact').is_('embedding_1536', 'null').is_('embedding', 'null').execute()
print(f"  Sin embeddings:               {result_none.count:,}")

# 4. Distribución por kind + embedding
print("\n4️⃣ Embeddings por KIND:")
print("-" * 50)
for kind in ['lemma', 'subentry', 'example']:
    with_emb = supabase.table('bora_docs').select('id', count='exact').eq('kind', kind).not_.is_('embedding_1536', 'null').execute()
    total = supabase.table('bora_docs').select('id', count='exact').eq('kind', kind).execute()
    print(f"  {kind:12} = {with_emb.count:,}/{total.count:,} con embedding_1536")

print("\n✅ Análisis completado")
