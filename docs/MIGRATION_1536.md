# Migración de embeddings a 1536 (text-embedding-3-small)

Este documento describe el proceso para migrar los vectores de 384 a 1536 dimensiones usando el API de OpenAI con batching. El plan minimiza downtime manteniendo columnas e índices en paralelo (v2) y permite rollback.

## 1) Preparar entorno

- Variables necesarias (PowerShell):
  - `OPENAI_API_KEY` (requerido)
  - `USE_EMBEDDING_API=true` (para usar API de OpenAI en la generación)
  - `DATABASE_URL` o `POSTGRES_URL` (cadena de conexión de Supabase Postgres)

## 2) Aplicar migraciones SQL

Ejecuta los SQL para agregar columnas `embedding_1536`, índices HNSW e implementar RPCs v2:

```pwsh
python backend/scripts/apply_sql.py --file docs/migrations/2025-10-30-embeddings-1536.sql \
                                   --file docs/migrations/2025-10-30-bora-docs-1536.sql
```

## 3) Backfill de embeddings (smoke test)

Corre un muestreo pequeño para validar que se escriben los `embedding_1536` correctamente:

```pwsh
# Bora docs
python backend/scripts/backfill_embeddings_1536.py --target bora_docs --batch 64 --limit 50

# Phrases
python backend/scripts/backfill_embeddings_1536.py --target phrases --batch 64 --limit 50

# Lexicon
python backend/scripts/backfill_embeddings_1536.py --target lexicon --batch 64 --limit 50
```

Verifica en Supabase que las columnas `embedding_1536` se estén llenando y que las RPC v2 devuelvan resultados.

## 4) Backfill completo

Cuando el smoke test pase, ejecuta sin límite (o con límites mayores) para completar el backfill:

```pwsh
python backend/scripts/backfill_embeddings_1536.py --target bora_docs --batch 64 --limit 0
python backend/scripts/backfill_embeddings_1536.py --target phrases   --batch 64 --limit 0
python backend/scripts/backfill_embeddings_1536.py --target lexicon   --batch 64 --limit 0
```

## 5) Activar 1536 en la app (staging)

Configura en el backend (variables de entorno):

- `USE_EMBEDDING_API=true`
- `USE_VECTOR_1536=true`

Reinicia el backend y prueba las rutas que usen vector search. Mide latencia y calidad; ajusta `SIMILARITY_THRESHOLD` si es necesario.

## 6) Producción y rollback

- Promociona a producción tras validar en staging.
- Mantén las columnas/índices de 384 durante una ventana de rollback. Si todo va bien, podrás eliminarlas en una limpieza posterior.

## Notas

- El archivo `backend/config/settings.py` ahora falla temprano si `LLM_PROVIDER=openai` y no hay `OPENAI_API_KEY` y `ALLOW_HF_LLM_FALLBACK=false`, cumpliendo la política de "OpenAI-only".
- El backfill usa llamados en batch al modelo `text-embedding-3-small` para eficiencia/costo.
