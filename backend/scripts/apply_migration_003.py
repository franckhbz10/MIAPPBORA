"""
Ejecuta migración: permitir NULL en bora_docs.embedding
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

print("🔧 Conectando a Supabase...")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# SQL de la migración
sql = """
ALTER TABLE bora_docs
  ALTER COLUMN embedding DROP NOT NULL;
"""

print("📝 Ejecutando migración:")
print("=" * 80)
print(sql)
print("=" * 80)

try:
    # Intentar ejecutar directamente
    response = supabase.table('bora_docs').select('id').limit(1).execute()
    print(f"✅ Conexión establecida (encontrados {len(response.data)} registros de prueba)")
    
    # Ejecutar SQL via RPC
    print("\n🔄 Ejecutando ALTER TABLE...")
    
    # Usar postgrest para ejecutar SQL crudo
    from httpx import Client as HttpClient
    
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }
    
    http_client = HttpClient()
    
    # Ejecutar SQL
    url = f"{SUPABASE_URL}/rest/v1/rpc/exec"
    
    # Si no existe exec, mostrar instrucciones
    print("\n⚠️  Supabase no permite ALTER TABLE via API REST")
    print("\n📋 INSTRUCCIONES MANUALES:")
    print("=" * 80)
    print("1. Ve a: https://supabase.com/dashboard/project/bsetkzhqjehhoaoietbq/sql")
    print("\n2. Ejecuta este SQL:")
    print("\nALTER TABLE bora_docs")
    print("  ALTER COLUMN embedding DROP NOT NULL;")
    print("\n3. Presiona 'Run' (F5)")
    print("=" * 80)
    print("\n✅ Una vez ejecutado, continúa con la ingesta.\n")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n📋 Ejecuta manualmente en Supabase Dashboard:")
    print("https://supabase.com/dashboard/project/bsetkzhqjehhoaoietbq/sql")
    print("\nSQL:")
    print(sql)
    exit(1)
