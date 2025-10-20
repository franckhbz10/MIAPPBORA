"""
Crea tablas lexicon_* y función match_lexicon en Supabase.
Si la ejecución RPC no está disponible, imprime instrucciones para ejecutar el SQL manualmente.
"""
from pathlib import Path
import logging
import sys

# Ensure backend root is on sys.path so `adapters` imports work when running as a script
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from adapters.supabase_adapter import SupabaseAdapter
from config.settings import settings

try:
    import psycopg2  # psycopg2-binary
except Exception:
    psycopg2 = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_lexicon():
    supa = SupabaseAdapter()
    if not supa.is_connected():
        logger.error("Supabase no configurado. Define SUPABASE_URL y SUPABASE_ANON_KEY en .env")
        return False

    sql_path = Path(__file__).parents[2] / 'docs' / 'create_lexicon_tables_and_match.sql'
    sql = sql_path.read_text(encoding='utf-8')

    # Intento 1: RPC personalizada (si existiese)
    try:
        supa.client.rpc('exec_sql', {'query': sql}).execute()
        logger.info("✅ Tablas lexicon_* y función match_lexicon creadas (RPC)")
        return True
    except Exception as e:
        logger.warning(f"⚠️ RPC exec_sql no disponible: {e}")

    # Intento 2: conexión directa a Postgres si POSTGRES_URL/DATABASE_URL está disponible
    pg_url = settings.POSTGRES_URL or settings.DATABASE_URL
    if pg_url and psycopg2 is not None:
        try:
            logger.info("🔌 Ejecutando SQL directamente vía psycopg2")
            conn = psycopg2.connect(pg_url)
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.close()
            logger.info("✅ Tablas lexicon_* y función match_lexicon creadas (psycopg2)")
            return True
        except Exception as e:
            logger.error(f"❌ Error ejecutando SQL por psycopg2: {e}")

    # Fallback: instrucciones manuales
    logger.info("➡️ Ejecuta manualmente el SQL en Supabase Dashboard:")
    logger.info(f"   {sql_path}")
    return False


if __name__ == '__main__':
    setup_lexicon()
