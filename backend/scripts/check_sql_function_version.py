"""
Verificar version actual de match_bora_docs_v2 en Supabase
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path

# Cargar .env
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

print("="*80)
print("VERIFICACION: Version de match_bora_docs_v2 en Supabase")
print("="*80)

# Query para obtener la definicion de la funcion
query = """
SELECT 
    p.proname as function_name,
    pg_get_function_result(p.oid) as return_type,
    pg_get_function_arguments(p.oid) as arguments,
    pg_get_functiondef(p.oid) as definition
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
  AND p.proname = 'match_bora_docs_v2';
"""

try:
    # Ejecutar query usando SQL directo
    result = supabase.rpc('exec_sql', {'query': query}).execute()
    print("\nERROR: exec_sql no esta disponible")
    print("Necesitamos verificar manualmente en Supabase SQL Editor")
except Exception as e:
    print("\nINFO: No podemos ejecutar SQL directo desde Python")
    print("Verificacion manual necesaria")

# Alternativa: Verificar campos retornados por la funcion
print("\n[VERIFICACION ALTERNATIVA] Campos retornados por match_bora_docs_v2:")
print("-"*80)

from openai import OpenAI

openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# Generar embedding de prueba
response = openai_client.embeddings.create(
    model="text-embedding-3-small",
    input="test"
)
test_embedding = response.data[0].embedding

# Llamar a la funcion
result = supabase.rpc(
    'match_bora_docs_v2',
    {
        'query_embedding': test_embedding,
        'match_threshold': 0.0,
        'match_count': 1
    }
).execute()

if result.data and len(result.data) > 0:
    doc = result.data[0]
    print("\nCampos retornados:")
    for key in sorted(doc.keys()):
        value = doc[key]
        # Truncar valores largos
        if isinstance(value, str) and len(value) > 50:
            value = value[:50] + "..."
        print(f"   {key}: {value}")
    
    print("\n[ANALISIS]")
    print("-"*80)
    
    # Verificar campos criticos
    required_fields = ['gloss_bora', 'direction']
    missing_fields = []
    
    for field in required_fields:
        if field not in doc:
            missing_fields.append(field)
            print(f"ERROR: Campo '{field}' NO existe en el schema de retorno")
        elif doc[field] is None:
            print(f"WARNING: Campo '{field}' existe pero es NULL")
            print(f"         Esto puede indicar que la funcion NO lo esta poblando")
        else:
            print(f"OK: Campo '{field}' existe y tiene valor")
    
    if missing_fields:
        print(f"\n[CONCLUSION]")
        print(f"La funcion match_bora_docs_v2 NO incluye estos campos: {', '.join(missing_fields)}")
        print(f"ACCION: Ejecutar migracion 002_match_bora_docs_v2_bidirectional.sql")
    elif doc.get('gloss_bora') is None and doc.get('direction') is None:
        print(f"\n[CONCLUSION]")
        print(f"La funcion incluye los campos pero NO los esta poblando correctamente")
        print(f"ACCION: Verificar el COALESCE y JOIN en la funcion SQL")
    else:
        print(f"\n[CONCLUSION]")
        print(f"La funcion parece estar correcta")

else:
    print("\nERROR: No se obtuvieron resultados")

print("\n" + "="*80)
print("SIGUIENTE PASO:")
print("  1. Abrir Supabase SQL Editor")
print("  2. Ejecutar: docs/migrations/002_match_bora_docs_v2_bidirectional.sql")
print("  3. Re-ejecutar test_llm_context_abrazar.py para verificar")
print("="*80)
