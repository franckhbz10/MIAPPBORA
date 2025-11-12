-- =============================================================================
-- MIAPPBORA — Permitir NULL en bora_docs.embedding (384 dims)
-- Permite insertar documentos solo con embedding_1536 sin necesidad de generar embedding de 384 dims
-- =============================================================================

-- Quitar constraint NOT NULL de embedding (384 dims)
-- Esto permite usar solo embedding_1536 en producción
ALTER TABLE bora_docs
  ALTER COLUMN embedding DROP NOT NULL;

-- Comentario explicativo
COMMENT ON COLUMN bora_docs.embedding IS 
  'Embedding de 384 dimensiones (HuggingFace local). Nullable para permitir uso exclusivo de embedding_1536 (OpenAI) en producción.';

COMMENT ON COLUMN bora_docs.embedding_1536 IS 
  'Embedding de 1536 dimensiones (OpenAI text-embedding-3-small). Usado en producción cuando USE_VECTOR_1536=true.';
