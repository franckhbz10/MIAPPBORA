"""
Aplica archivos SQL contra la base de datos Postgres (Supabase).

Uso (PowerShell):

  # Establece la URL de conexión (elige una)
  # $env:DATABASE_URL = "postgresql://..."
  # $env:POSTGRES_URL = "postgresql://..."  # alias usado en settings

  # Ejecutar una o varias migraciones
  python backend/scripts/apply_sql.py --file docs/migrations/2025-10-30-embeddings-1536.sql \
                                      --file docs/migrations/2025-10-30-bora-docs-1536.sql

Requisitos:
- psycopg (v3) incluido en requirements
- Conexión con permisos suficientes para DDL y crear funciones
"""
from __future__ import annotations
import argparse
import os
import sys
from typing import List
from pathlib import Path

import psycopg
from dotenv import load_dotenv

# Cargar .env desde backend/ o raíz
env_paths = [
    Path(__file__).parent.parent / ".env",  # backend/.env
    Path(__file__).parent.parent.parent / ".env",  # raíz/.env
]
for p in env_paths:
    if p.exists():
        load_dotenv(p)
        break


def read_sql_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def apply_sql(conn_str: str, files: List[str]) -> None:
    # Autocommit recomendado para DDL múltiples
    with psycopg.connect(conn_str, autocommit=True) as conn:
        with conn.cursor() as cur:
            for path in files:
                sql = read_sql_file(path)
                print(f"\n-- Ejecutando: {path}")
                cur.execute(sql)
                print(f"OK: {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", dest="files", action="append", required=True,
                        help="Ruta de archivo .sql a ejecutar (puede repetirse)")
    args = parser.parse_args()

    conn_str = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if not conn_str:
        print("ERROR: Define DATABASE_URL o POSTGRES_URL en variables de entorno.", file=sys.stderr)
        sys.exit(1)

    try:
        apply_sql(conn_str, args.files)
        print("\nTodas las migraciones finalizaron correctamente.")
    except Exception as e:
        print(f"Error aplicando migraciones: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
