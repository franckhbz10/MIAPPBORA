"""
Script para ejecutar migración: permitir NULL en bora_docs.embedding

Esta migración es necesaria porque:
1. El schema original tenía embedding VECTOR(384) NOT NULL
2. En producción usamos solo embedding_1536 (OpenAI, 1536 dims)
3. Necesitamos permitir embedding=NULL para insertar solo con embedding_1536
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Falta SUPABASE_URL o SUPABASE_SERVICE_KEY en .env")
    exit(1)

# Cliente de Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Leer migración
migration_path = Path(__file__).parent.parent / 'docs' / 'migrations' / '003_bora_docs_embedding_nullable.sql'
with open(migration_path, 'r', encoding='utf-8') as f:
    sql = f.read()

print(f"📄 Ejecutando migración: {migration_path.name}")
print("=" * 80)
print(sql)
print("=" * 80)

try:
    # Ejecutar SQL
    result = supabase.rpc('exec_sql', {'sql': sql}).execute()
    print("✅ Migración ejecutada exitosamente")
    print(f"Resultado: {result}")
except Exception as e:
    # Si exec_sql no existe, intentar con postgrest directamente
    print(f"⚠️  exec_sql no disponible, usando enfoque alternativo...")
    
    # Dividir en statements individuales
    statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
    
    for i, stmt in enumerate(statements, 1):
        if stmt:
            print(f"\n{i}. Ejecutando statement:")
            print(stmt[:100] + "..." if len(stmt) > 100 else stmt)
            try:
                supabase.postgrest.rpc('exec', {'query': stmt}).execute()
                print(f"   ✅ Statement {i} OK")
            except Exception as e2:
                print(f"   ❌ Error en statement {i}: {e2}")
                print(f"\n⚠️  Ejecuta manualmente en Supabase SQL Editor:")
                print(f"   {SUPABASE_URL.replace('https://', 'https://supabase.com/dashboard/project/')}/sql")
                print(f"\nSQL a ejecutar:")
                print("=" * 80)
                print(sql)
                print("=" * 80)
                exit(1)

print("\n✅ Migración completada. Ahora puedes ejecutar el script de ingesta nuevamente.")
