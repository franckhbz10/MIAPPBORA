"""
Aplica el SQL de creación del nuevo esquema y RPC (bora_docs + match_bora_docs).
Intenta primero vía Supabase RPC genérico; si no existe, usa conexión directa a Postgres.
"""
import os
from pathlib import Path
import logging

SQL_FILE = Path(__file__).parents[2] / 'docs' / 'create_bora_docs_and_match.sql'
ENV_CANDIDATES = [
    Path(__file__).parents[1] / '.env',  # backend/.env
    Path(__file__).parents[2] / '.env',  # repo root .env
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def apply_via_direct_connection(sql_text: str) -> bool:
    # Cargar .env manualmente para asegurar variables
    try:
        from dotenv import load_dotenv
        for env_path in ENV_CANDIDATES:
            if env_path.exists():
                load_dotenv(dotenv_path=env_path, override=False)
    except Exception:
        pass

    dsn = os.getenv('POSTGRES_URL') or os.getenv('DATABASE_URL')
    if not dsn:
        logger.error('POSTGRES_URL/DATABASE_URL no configurado para conexión directa')
        return False
    try:
        import psycopg2
        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(sql_text)
        conn.close()
        logger.info('SQL aplicado vía conexión directa (psycopg2)')
        return True
    except Exception as e:
        logger.error(f'Error al aplicar SQL por conexión directa: {e}')
        return False


def main():
    if not SQL_FILE.exists():
        logger.error(f'No se encontró el archivo SQL: {SQL_FILE}')
        return 1
    sql_text = SQL_FILE.read_text(encoding='utf-8')

    # Intento directo (más fiable)
    ok = apply_via_direct_connection(sql_text)
    if ok:
        return 0

    # Como fallback, intentar vía Supabase RPC genérico si existiera (no implementado por defecto)
    try:
        from adapters.supabase_adapter import get_supabase_adapter
        supa = get_supabase_adapter()
        if not supa.is_connected():
            logger.error('Supabase no conectado y no hay conexión directa. No se puede aplicar SQL.')
            return 1
        # Si tienes un RPC exec_sql, descomenta y usa:
        # supa.client.rpc('exec_sql', {'sql': sql_text}).execute()
        logger.error('No hay RPC genérico para ejecutar SQL. Aplica manualmente en Supabase SQL Editor.')
        return 1
    except Exception as e:
        logger.error(f'Error en fallback Supabase: {e}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
