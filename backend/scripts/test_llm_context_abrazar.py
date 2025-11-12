"""
Test completo: Simular exactamente lo que recibe el LLM cuando busca "abrazar"
"""
import os
import sys
from pathlib import Path
from supabase import create_client, Client
from openai import OpenAI
from dotenv import load_dotenv

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
sys.path.insert(0, str(BACKEND_ROOT))

# Cargar .env
env_path = BACKEND_ROOT / '.env'
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

print("="*80)
print("TEST COMPLETO: Como se dice 'abrazar' en bora?")
print("="*80)

# PASO 1: Verificar datos en bora_docs directamente
print("\n[PASO 1] Verificar datos RAW en bora_docs")
print("-"*80)

# Buscar lemma "abrazar" en lexicon_lemmas
lemma_resp = supabase.table('lexicon_lemmas').select('*').eq('lemma', 'abrazar').eq('direction', 'es_bora').execute()

if lemma_resp.data:
    abrazar_lemma = lemma_resp.data[0]
    lemma_id = abrazar_lemma['id']
    
    print(f"OK Lemma encontrado en lexicon_lemmas:")
    print(f"   ID: {lemma_id}")
    print(f"   lemma: {abrazar_lemma['lemma']}")
    print(f"   gloss_bora: {abrazar_lemma['gloss_bora']}")
    print(f"   direction: {abrazar_lemma['direction']}")
    
    # Buscar documento en bora_docs
    doc_resp = supabase.table('bora_docs').select('*').eq('parent_lemma_id', lemma_id).eq('kind', 'lemma').execute()
    
    if doc_resp.data:
        doc = doc_resp.data[0]
        print(f"\nOK Documento encontrado en bora_docs:")
        print(f"   id: {doc['id']}")
        print(f"   kind: {doc['kind']}")
        print(f"   parent_lemma_id: {doc['parent_lemma_id']}")
        print(f"   content: {doc['content']}")
        print(f"   metadata:")
        for key, value in doc.get('metadata', {}).items():
            print(f"      {key}: {value}")
        print(f"   has embedding_1536: {bool(doc.get('embedding_1536'))}")
    else:
        print("\nERROR: No se encontro documento en bora_docs")
        sys.exit(1)
else:
    print("ERROR: Lemma 'abrazar' no encontrado en lexicon_lemmas")
    sys.exit(1)

# PASO 2: Verificar que retorna match_bora_docs_v2 (RAW SQL)
print("\n\n[PASO 2] Verificar respuesta de match_bora_docs_v2 (SQL)")
print("-"*80)

query = "abrazar"
print(f"Query: '{query}'")

# Generar embedding
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
        'match_threshold': 0.6,  # Threshold alto para solo "abrazar"
        'match_count': 1
    }
).execute()

if result.data and len(result.data) > 0:
    doc = result.data[0]
    print(f"\nOK match_bora_docs_v2 retorno 1 resultado:")
    print(f"\nTODOS LOS CAMPOS RETORNADOS:")
    for key, value in doc.items():
        print(f"   {key}: {value}")
else:
    print("\nERROR: match_bora_docs_v2 no retorno resultados")
    sys.exit(1)

# PASO 3: Simular formato que recibe el LLM (RAG service)
print("\n\n[PASO 3] Simular formato RAG que recibe el LLM")
print("-"*80)

# Este es el formato que usa backend/services/rag_service.py
def format_for_llm(docs):
    """Simula el formateo que hace RAG service"""
    formatted = []
    
    for doc in docs:
        kind = doc.get('kind')
        
        if kind == 'lemma':
            # Formato para lemma
            lemma = doc.get('lemma', 'N/A')
            gloss_es = doc.get('gloss_es')
            gloss_bora = doc.get('gloss_bora')
            direction = doc.get('direction', 'N/A')
            pos = doc.get('pos_full', 'N/A')
            
            # Determinar gloss segun direccion
            if direction == 'bora_es':
                definition = f"Bora: {lemma}, Espanol: {gloss_es}"
            elif direction == 'es_bora':
                definition = f"Espanol: {lemma}, Bora: {gloss_bora}"
            else:
                definition = f"Lemma: {lemma}, ES: {gloss_es}, Bora: {gloss_bora}"
            
            formatted.append({
                'tipo': 'Lemma',
                'definicion': definition,
                'categoria': pos,
                'raw_data': {
                    'lemma': lemma,
                    'gloss_es': gloss_es,
                    'gloss_bora': gloss_bora,
                    'direction': direction,
                    'pos': pos
                }
            })
        
        elif kind == 'example':
            bora_text = doc.get('bora_text', 'N/A')
            spanish_text = doc.get('spanish_text', 'N/A')
            formatted.append({
                'tipo': 'Ejemplo',
                'bora': bora_text,
                'espanol': spanish_text
            })
    
    return formatted

formatted_results = format_for_llm(result.data)

print(f"Resultados formateados para LLM ({len(formatted_results)} items):\n")
for i, item in enumerate(formatted_results, 1):
    print(f"{i}. Tipo: {item.get('tipo')}")
    if item.get('tipo') == 'Lemma':
        print(f"   Definicion: {item['definicion']}")
        print(f"   Categoria: {item['categoria']}")
        print(f"   Raw data:")
        for key, value in item['raw_data'].items():
            print(f"      {key}: {value}")
    else:
        print(f"   Bora: {item.get('bora')}")
        print(f"   Espanol: {item.get('espanol')}")

# PASO 4: Verificar estructura de la funcion SQL
print("\n\n[PASO 4] Diagnostico del problema")
print("-"*80)

# Verificar si gloss_bora esta NULL
if result.data[0].get('gloss_bora') is None:
    print("ERROR ENCONTRADO:")
    print("   match_bora_docs_v2 retorna gloss_bora=NULL")
    print("\nPosibles causas:")
    print("   1. La funcion SQL NO incluye gloss_bora en el SELECT")
    print("   2. El JOIN con lexicon_lemmas esta mal")
    print("   3. El COALESCE esta fallando")
    print("\nVerificando datos en lexicon_lemmas directamente:")
    
    # Re-verificar lemma
    lemma_check = supabase.table('lexicon_lemmas').select('id, lemma, gloss_bora, direction').eq('id', result.data[0]['parent_lemma_id']).execute()
    
    if lemma_check.data:
        lem = lemma_check.data[0]
        print(f"   ID {lem['id']}: lemma='{lem['lemma']}', gloss_bora='{lem['gloss_bora']}', direction='{lem['direction']}'")
        print("\nCONCLUSION: Los datos EXISTEN en lexicon_lemmas pero match_bora_docs_v2 NO los retorna")
        print("SOLUCION: Actualizar la funcion SQL match_bora_docs_v2 en Supabase")
    else:
        print("   ERROR: No se encontro el lemma en verificacion")
else:
    print("OK gloss_bora SI esta presente en el resultado")
    print(f"   Valor: {result.data[0].get('gloss_bora')}")

# PASO 5: Simular respuesta del LLM
print("\n\n[PASO 5] Como responderia el LLM con estos datos")
print("-"*80)

if formatted_results:
    first_result = formatted_results[0]
    if first_result.get('tipo') == 'Lemma':
        raw = first_result['raw_data']
        
        print("Pregunta del usuario: 'Como se dice abrazar en bora?'")
        print("\nDatos disponibles para el LLM:")
        print(f"   lemma: {raw['lemma']}")
        print(f"   gloss_bora: {raw['gloss_bora']}")
        print(f"   direction: {raw['direction']}")
        
        if raw['gloss_bora'] and raw['gloss_bora'] != 'N/A':
            print(f"\nRespuesta esperada del LLM:")
            print(f"   'En bora, \"abrazar\" se dice \"{raw['gloss_bora']}\"'")
        else:
            print(f"\nRespuesta INCORRECTA del LLM (sin gloss_bora):")
            print(f"   'No encontre la traduccion de \"abrazar\" al bora'")
            print("\n   PROBLEMA: El LLM NO puede responder correctamente sin gloss_bora!")

print("\n" + "="*80)
print("FIN DEL TEST")
print("="*80)
