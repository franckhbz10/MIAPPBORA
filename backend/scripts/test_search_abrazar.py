"""
Test de búsqueda: ¿Qué recupera el sistema con "abrazar"?
"""
import os
from supabase import create_client, Client
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# Cargar .env
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

print("TEST DE BUSQUEDA: 'abrazar'\n")
print("=" * 80)

# 1. Verificar si "abrazar" existe en lexicon_lemmas
print("\n1. Buscando 'abrazar' en lexicon_lemmas...")
print("-" * 80)

lemma_resp = supabase.table('lexicon_lemmas').select('*').eq('lemma', 'abrazar').execute()

if lemma_resp.data:
    for lemma in lemma_resp.data:
        print(f"\nOK Encontrado en lexicon_lemmas:")
        print(f"   ID: {lemma['id']}")
        print(f"   Lemma: {lemma['lemma']}")
        print(f"   Gloss ES: {lemma.get('gloss_es')}")
        print(f"   Gloss Bora: {lemma.get('gloss_bora')}")
        print(f"   Direction: {lemma.get('direction')}")
        print(f"   POS: {lemma.get('pos_full') or lemma.get('pos')}")
        print(f"   Source: {lemma.get('source')}")
        
        # Verificar si tiene documento en bora_docs
        doc_resp = supabase.table('bora_docs').select('*').eq('kind', 'lemma').eq('parent_lemma_id', lemma['id']).execute()
        
        if doc_resp.data:
            print(f"\n   OK Tiene {len(doc_resp.data)} documento(s) en bora_docs:")
            for doc in doc_resp.data:
                print(f"      - Content: {doc.get('content')[:80]}...")
                print(f"      - Has embedding_1536: {bool(doc.get('embedding_1536'))}")
                print(f"      - Metadata direction: {doc.get('metadata', {}).get('direction')}")
                print(f"      - Metadata source: {doc.get('metadata', {}).get('source')}")
        else:
            print(f"\n   ERROR NO tiene documento en bora_docs")
else:
    print("ERROR 'abrazar' NO encontrado en lexicon_lemmas")

# 2. Búsqueda vectorial con OpenAI
print("\n\n2. Busqueda vectorial con match_bora_docs_v2...")
print("-" * 80)

query = "abrazar"
print(f"Query: '{query}'")

# Generar embedding para la query
response = openai_client.embeddings.create(
    model="text-embedding-3-small",
    input=query
)
query_embedding = response.data[0].embedding

# Llamar a match_bora_docs_v2
result = supabase.rpc(
    'match_bora_docs_v2',
    {
        'query_embedding': query_embedding,
        'match_threshold': 0.0,  # Sin filtro para ver todos los resultados
        'match_count': 10
    }
).execute()

if result.data:
    print(f"\nOK Resultados encontrados: {len(result.data)}\n")
    
    for i, doc in enumerate(result.data, 1):
        similarity = doc.get('similarity', 0)
        
        print(f"{i}. Similarity: {similarity:.4f}")
        print(f"   Kind: {doc.get('kind')}")
        print(f"   Lemma: {doc.get('lemma', 'N/A')}")
        print(f"   Direction: {doc.get('direction', 'N/A')}")
        print(f"   Gloss ES: {doc.get('gloss_es', 'N/A')}")
        print(f"   Gloss Bora: {doc.get('gloss_bora', 'N/A')}")
        print(f"   POS: {doc.get('pos_full', 'N/A')}")
        print()
else:
    print("ERROR No se encontraron resultados")

# 3. Análisis de resultados
print("\n3. Analisis:")
print("-" * 80)

if result.data:
    # Verificar si "abrazar" está en los resultados
    abrazar_found = False
    for doc in result.data:
        if doc.get('lemma') == 'abrazar':
            abrazar_found = True
            print(f"OK 'abrazar' ENCONTRADO en los resultados (similarity: {doc.get('similarity'):.4f})")
            break
    
    if not abrazar_found:
        print("ERROR 'abrazar' NO esta en los top 10 resultados")
        print("   Posibles razones:")
        print("   - No existe documento vectorizado para 'abrazar'")
        print("   - La similaridad es muy baja")
        print("   - Existe pero quedo fuera del top 10")
    
    # Distribución por dirección
    directions = {}
    for doc in result.data:
        direction = doc.get('direction', 'unknown')
        directions[direction] = directions.get(direction, 0) + 1
    
    print(f"\nDistribucion por direccion en resultados:")
    for direction, count in directions.items():
        print(f"   {direction}: {count}")
else:
    print("ERROR No hubo resultados para analizar")

print("\n" + "=" * 80)
print("OK Test completado")
