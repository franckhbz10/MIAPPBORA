"""
Script simple para verificar campos vacíos en bora_docs (sin dependencias complejas)
"""
import os
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

# Cargar .env desde backend/
backend_dir = Path(__file__).parent.parent
env_path = backend_dir / '.env'
load_dotenv(env_path)

# Usar las variables de entorno directamente
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')

if not SUPABASE_KEY:
    print("❌ Error: SUPABASE_KEY no configurada en variables de entorno")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("🔍 Verificando frases con campos vacíos en bora_docs...\n")

# 1. Buscar documentos con content vacío o NULL
print("1️⃣ Documentos con content vacío/NULL:")
print("-" * 80)
try:
    res = supabase.table('bora_docs').select(
        'id, kind, lemma, content, gloss_es, gloss_bora, bora_text, spanish_text'
    ).or_('content.is.null,content.eq.').limit(20).execute()
    
    empty_docs = res.data or []
    if empty_docs:
        print(f"   ⚠️ Encontrados: {len(empty_docs)} documentos con content vacío/NULL\n")
        for doc in empty_docs[:10]:
            print(f"   ID: {doc['id']} | Kind: {doc['kind']}")
            print(f"   - Lemma: {doc.get('lemma', 'N/A')}")
            print(f"   - Content: '{doc.get('content', 'NULL')}'")
            print(f"   - gloss_es: {doc.get('gloss_es', 'NULL')}")
            print(f"   - gloss_bora: {doc.get('gloss_bora', 'NULL')}")
            if doc['kind'] == 'example':
                print(f"   - bora_text: {doc.get('bora_text', 'NULL')}")
                print(f"   - spanish_text: {doc.get('spanish_text', 'NULL')}")
            print()
    else:
        print("   ✅ No se encontraron documentos con content vacío\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# 2. Verificar lemmas específicamente
print("2️⃣ Muestreo de lemmas (primeros 5):")
print("-" * 80)
try:
    res = supabase.table('bora_docs').select(
        'id, kind, lemma, content, gloss_es, gloss_bora, metadata'
    ).eq('kind', 'lemma').limit(5).execute()
    
    lemmas = res.data or []
    for lemma in lemmas:
        direction = lemma.get('metadata', {}).get('direction', 'N/A')
        print(f"\n   Lemma: '{lemma.get('lemma', 'NULL')}' | Direction: {direction}")
        
        content = lemma.get('content', '')
        content_preview = content[:100] if content else 'NULL'
        print(f"   - Content: '{content_preview}{'...' if len(content) > 100 else ''}'")
        print(f"   - gloss_es: {lemma.get('gloss_es', 'NULL')}")
        print(f"   - gloss_bora: {lemma.get('gloss_bora', 'NULL')}")
        
        # Marcar campos problemáticos
        issues = []
        if not lemma.get('lemma'):
            issues.append('lemma vacío')
        if not lemma.get('content'):
            issues.append('content vacío')
        if not lemma.get('gloss_es') and direction != 'es_bora':
            issues.append('gloss_es vacío (Bora→ES)')
        if not lemma.get('gloss_bora') and direction == 'es_bora':
            issues.append('gloss_bora vacío (ES→Bora)')
        
        if issues:
            print(f"   ⚠️ PROBLEMAS: {', '.join(issues)}")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# 3. Verificar ejemplos con campos vacíos
print("\n3️⃣ Ejemplos con bora_text o spanish_text vacíos:")
print("-" * 80)
try:
    res = supabase.table('bora_docs').select(
        'id, kind, lemma, bora_text, spanish_text, content'
    ).eq('kind', 'example').or_(
        'bora_text.is.null,bora_text.eq.,spanish_text.is.null,spanish_text.eq.'
    ).limit(10).execute()
    
    empty_examples = res.data or []
    if empty_examples:
        print(f"   ⚠️ Encontrados: {len(empty_examples)} ejemplos con campos vacíos\n")
        for ex in empty_examples[:5]:
            print(f"   ID: {ex['id']} | Lemma: {ex.get('lemma', 'N/A')}")
            print(f"   - bora_text: '{ex.get('bora_text', 'NULL')}'")
            print(f"   - spanish_text: '{ex.get('spanish_text', 'NULL')}'")
            print(f"   - content: '{ex.get('content', 'NULL')[:50]}...'")
            print()
    else:
        print("   ✅ Todos los ejemplos tienen bora_text y spanish_text\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# 4. Contar por tipo
print("4️⃣ Resumen de documentos por tipo:")
print("-" * 80)
try:
    for kind in ['lemma', 'subentry', 'example']:
        res = supabase.table('bora_docs').select('id', count='exact').eq('kind', kind).execute()
        total = res.count
        
        # Contar con content vacío
        res_empty = supabase.table('bora_docs').select('id', count='exact').eq('kind', kind).or_(
            'content.is.null,content.eq.'
        ).execute()
        empty_count = res_empty.count
        
        print(f"   {kind.capitalize()}: {total} total, {empty_count} con content vacío ({empty_count/total*100 if total > 0 else 0:.1f}%)")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

print("\n✅ Diagnóstico completado")
