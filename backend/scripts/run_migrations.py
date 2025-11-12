"""
Ejecutor de migraciones SQL para schema bidireccional

Ejecuta en orden:
1. 001_bidirectional_schema.sql - Agrega columnas direction y gloss_bora
2. 002_match_bora_docs_v2_bidirectional.sql - Actualiza función RPC

Uso:
    python backend/scripts/run_migrations.py
"""
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from adapters.supabase_adapter import SupabaseAdapter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_sql_file(path: Path) -> str:
    """Lee archivo SQL y retorna contenido"""
    if not path.exists():
        raise FileNotFoundError(f"No se encontró: {path}")
    return path.read_text(encoding='utf-8')


def execute_sql(supa: SupabaseAdapter, sql: str, description: str) -> bool:
    """
    Ejecuta SQL en Supabase
    
    Nota: Supabase Python client no tiene método directo para ejecutar SQL arbitrario.
    Las migraciones deben ejecutarse manualmente en el SQL Editor de Supabase.
    
    Este script solo MUESTRA el SQL que debe ejecutarse.
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"📄 {description}")
    logger.info(f"{'='*80}\n")
    logger.info(sql)
    logger.info(f"\n{'='*80}\n")
    return True


def main():
    logger.info("🚀 Ejecutor de Migraciones SQL - Schema Bidireccional")
    logger.info("="*80)
    
    # Verificar conexión
    supa = SupabaseAdapter(use_service_role=True)
    if not supa.is_connected():
        logger.error("❌ Supabase no configurado. Verifica SUPABASE_URL y SUPABASE_SERVICE_KEY en .env")
        return 1
    
    logger.info("✅ Conexión a Supabase establecida\n")
    
    # Rutas de migraciones
    migrations_dir = BACKEND_ROOT.parent / 'docs' / 'migrations'
    migration_001 = migrations_dir / '001_bidirectional_schema.sql'
    migration_002 = migrations_dir / '002_match_bora_docs_v2_bidirectional.sql'
    
    logger.info("📋 INSTRUCCIONES:")
    logger.info("="*80)
    logger.info("El cliente Python de Supabase no permite ejecutar SQL arbitrario.")
    logger.info("Debes copiar y ejecutar el SQL manualmente en Supabase SQL Editor:")
    logger.info("")
    logger.info("1. Abre: https://supabase.com/dashboard/project/_/sql")
    logger.info("2. Crea una nueva query")
    logger.info("3. Copia y pega el SQL de cada migración (mostrado abajo)")
    logger.info("4. Ejecuta con 'Run' o Ctrl+Enter")
    logger.info("="*80)
    
    input("\n⏸️  Presiona ENTER para ver la MIGRACIÓN 001...")
    
    try:
        # Migración 001
        sql_001 = read_sql_file(migration_001)
        execute_sql(supa, sql_001, "MIGRACIÓN 001: Schema Bidireccional")
        
        response = input("\n✅ ¿Ejecutaste la migración 001 en Supabase? (s/n): ")
        if response.lower() != 's':
            logger.warning("⚠️  Abortando. Ejecuta la migración 001 antes de continuar.")
            return 1
        
        # Migración 002
        sql_002 = read_sql_file(migration_002)
        execute_sql(supa, sql_002, "MIGRACIÓN 002: match_bora_docs_v2 Bidireccional")
        
        response = input("\n✅ ¿Ejecutaste la migración 002 en Supabase? (s/n): ")
        if response.lower() != 's':
            logger.warning("⚠️  Abortando. Ejecuta la migración 002 antes de continuar.")
            return 1
        
        logger.info("\n" + "="*80)
        logger.info("🎉 MIGRACIONES COMPLETADAS")
        logger.info("="*80)
        logger.info("\n📝 Próximos pasos:")
        logger.info("1. Verificar que columnas existen:")
        logger.info("   SELECT column_name FROM information_schema.columns")
        logger.info("   WHERE table_name='lexicon_lemmas' AND column_name IN ('direction','gloss_bora');")
        logger.info("")
        logger.info("2. Verificar datos existentes marcados como 'bora_es':")
        logger.info("   SELECT direction, COUNT(*) FROM lexicon_lemmas GROUP BY direction;")
        logger.info("")
        logger.info("3. Ejecutar test con subset:")
        logger.info("   python backend/scripts/ingest_es_bora_docs.py --path ../salida_es_bora_final.json --limit 100 --reset")
        logger.info("="*80)
        
    except FileNotFoundError as e:
        logger.error(f"❌ Error: {e}")
        return 1
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
