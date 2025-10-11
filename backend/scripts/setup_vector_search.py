"""
Crea la función match_phrases en Supabase
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import logging
from adapters.supabase_adapter import SupabaseAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_match_function():
    """Crea función SQL de búsqueda vectorial en Supabase"""
    logger.info("🔧 Creando función match_phrases en Supabase...")
    logger.info("=" * 60)
    
    supabase = SupabaseAdapter()
    
    # SQL para crear la función
    sql = """
-- Habilitar pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Crear función de búsqueda
CREATE OR REPLACE FUNCTION match_phrases (
  query_embedding vector(384),
  match_threshold float DEFAULT 0.5,
  match_count int DEFAULT 5,
  category_filter text DEFAULT NULL
)
RETURNS TABLE (
  id int,
  phrase_id int,
  bora_text text,
  spanish_text text,
  category text,
  difficulty int,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    pe.id,
    pe.phrase_id,
    bp.bora_text,
    bp.spanish_text,
    bp.category,
    bp.difficulty,
    1 - (pe.embedding <=> query_embedding) AS similarity
  FROM phrase_embeddings pe
  INNER JOIN bora_phrases bp ON pe.phrase_id = bp.id
  WHERE 
    (category_filter IS NULL OR bp.category = category_filter)
    AND (1 - (pe.embedding <=> query_embedding)) > match_threshold
  ORDER BY pe.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Crear índice HNSW
CREATE INDEX IF NOT EXISTS phrase_embeddings_embedding_idx 
ON phrase_embeddings 
USING hnsw (embedding vector_cosine_ops);
"""
    
    try:
        # Ejecutar SQL usando el cliente de Supabase
        result = supabase.client.rpc('exec_sql', {'query': sql}).execute()
        logger.info("✅ Función match_phrases creada exitosamente")
        logger.info("=" * 60)
        return True
    except Exception as e:
        # Si no existe exec_sql, mostrar instrucciones manuales
        logger.warning(f"⚠️ No se pudo ejecutar automáticamente: {e}")
        logger.info("\n" + "=" * 60)
        logger.info("📋 INSTRUCCIONES MANUALES:")
        logger.info("=" * 60)
        logger.info("1. Ve a Supabase Dashboard")
        logger.info("2. Abre el SQL Editor")
        logger.info("3. Copia y ejecuta el contenido de:")
        logger.info("   backend/sql/create_match_phrases_function.sql")
        logger.info("=" * 60)
        return False


if __name__ == "__main__":
    create_match_function()
