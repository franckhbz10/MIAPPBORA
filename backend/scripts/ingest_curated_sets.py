"""
Ingesta de los conjuntos curados:
- vocabulario_v1.json (parejas palabra Bora ↔ traducción español)
- frases_v1.json (frases completas con categoría, dificultad y contexto)

El objetivo es poblar las tablas lexicon_lemmas, lexicon_examples y bora_docs
para que ambos datasets estén disponibles en la búsqueda semántica del mentor.

Uso típico:
    python backend/scripts/ingest_curated_sets.py \
            --vocab-path ../vocabulario_v1.json \
            --phrases-path ../frases_v1.json \
            --batch-size 400 --embed-batch-size 64 --reset

Flags útiles:
    --dry-run           Solo muestra estadísticas de parsing y termina.
    --limit-vocab N     Limita los registros del vocabulario para pruebas.
    --limit-phrases N   Limita los registros de frases para pruebas.
    --reset             Limpia todas las filas previas de ambos sources
                                            (lexicon_lemmas, lexicon_examples, bora_docs).

Requisitos:
        - SUPABASE_URL y SUPABASE_SERVICE_KEY en .env (usa service_role)
        - OPENAI_API_KEY disponible para `text-embedding-3-small`
        - Tabla `bora_docs` con columna `embedding_1536` (VECTOR(1536)) y `USE_VECTOR_1536=true`
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent

import sys

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Cargar variables desde backend/.env si existe
try:
    from dotenv import load_dotenv  # type: ignore

    env_path = BACKEND_ROOT / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except Exception:
    pass

from adapters.supabase_adapter import SupabaseAdapter
from config.settings import settings
from openai import OpenAI


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


VOCAB_SOURCE = "vocabulario_v1.json"
PHRASES_SOURCE = "frases_v1.json"


def awaitable(fn):
    import asyncio
    import inspect

    def wrapper(*args, **kwargs):
        result = fn(*args, **kwargs)
        if inspect.iscoroutine(result):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    new_loop = asyncio.new_event_loop()
                    try:
                        return new_loop.run_until_complete(result)
                    finally:
                        new_loop.close()
                else:
                    return loop.run_until_complete(result)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                try:
                    return loop.run_until_complete(result)
                finally:
                    loop.close()
        return result

    return wrapper


def load_json(path: Optional[Path], limit: Optional[int]) -> List[Dict[str, Any]]:
    if not path:
        return []
    if not path.exists():
        logger.warning("⚠️ No se encontró %s, se omite", path)
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(limit, int) and limit > 0:
        data = data[:limit]
    return data


def normalize_text(value: str) -> str:
    return " ".join(value.split()).strip()


def chunked(items: Iterable[Any], size: int) -> Iterable[List[Any]]:
    batch: List[Any] = []
    for item in items:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def insert_lemmas_direct(supa: SupabaseAdapter, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not rows or not supa.client:
        return []
    try:
        response = supa.client.table("lexicon_lemmas").insert(rows).execute()
        return response.data or []
    except Exception as exc:  # pragma: no cover
        logger.error("Error insert lemmas (fallback): %s", exc)
        return []


def build_vocab_lemmas(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    lemmas: List[Dict[str, Any]] = []
    counters = {"total": len(records), "deduped": 0, "skipped": 0}
    aggregated: Dict[str, Dict[str, Any]] = {}

    for entry in records:
        bora = normalize_text(entry.get("bora_text", ""))
        spanish = normalize_text(entry.get("spanish_text", ""))
        if not bora or not spanish:
            counters["skipped"] += 1
            continue
        key = bora.lower()
        target = aggregated.setdefault(
            key,
            {
                "lemma": bora,
                "direction": entry.get("direction") or "bora_es",
                "translations": set(),
                "raw_entries": [],
            },
        )
        target["translations"].add(spanish)
        target["raw_entries"].append(entry)

    for agg in aggregated.values():
        counters["deduped"] += 1
        gloss = "; ".join(sorted(agg["translations"]))
        lemmas.append(
            {
                "lemma": agg["lemma"],
                "gloss_es": gloss,
                "gloss_bora": None,
                "direction": agg["direction"],
                "pos": "voc",
                "pos_full": "vocabulario",
                "page": None,
                "variants": None,
                "synonyms": None,
                "raw": json.dumps(agg["raw_entries"], ensure_ascii=False),
                "source": VOCAB_SOURCE,
            }
        )

    return lemmas, counters


def build_phrase_category_lemmas(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    lemmas: List[Dict[str, Any]] = []
    index: Dict[str, Dict[str, Any]] = {}
    for entry in records:
        category = entry.get("category") or "General"
        category = normalize_text(category) or "General"
        if category in index:
            continue
        lemma_name = f"Frases · {category}"
        lemma_payload = {
            "lemma": lemma_name,
            "gloss_es": f"Frases de {category.lower()}" if category != "General" else "Frases de uso general",
            "gloss_bora": None,
            "direction": entry.get("direction") or "bora_es",
            "pos": "fr",
            "pos_full": "frase",
            "page": None,
            "variants": None,
            "synonyms": None,
            "raw": json.dumps({"category": category}, ensure_ascii=False),
            "source": PHRASES_SOURCE,
        }
        lemmas.append(lemma_payload)
        index[category] = lemma_payload
    return lemmas, index


def build_phrase_examples(
    records: List[Dict[str, Any]],
    category_to_lemma_id: Dict[str, int],
) -> Tuple[List[Dict[str, Any]], Dict[str, int], Dict[Tuple[int, str, str], Dict[str, Any]]]:
    examples: List[Dict[str, Any]] = []
    stats = {"total": len(records), "skipped": 0, "deduped": 0}
    seen_pairs: set[Tuple[int, str, str]] = set()
    metadata_lookup: Dict[Tuple[int, str, str], Dict[str, Any]] = {}

    for entry in records:
        category = normalize_text(entry.get("category") or "General") or "General"
        lemma_id = category_to_lemma_id.get(category)
        if not lemma_id:
            stats["skipped"] += 1
            continue

        bora = normalize_text(entry.get("bora_text", ""))
        spanish = normalize_text(entry.get("spanish_text", ""))
        if not bora or not spanish:
            stats["skipped"] += 1
            continue

        pair_key = (lemma_id, bora.lower(), spanish.lower())
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)
        stats["deduped"] += 1

        try:
            difficulty = int(entry.get("difficulty_level") or 1)
        except (TypeError, ValueError):
            difficulty = 1

        payload = {
            "lemma_id": lemma_id,
            "subentry_id": None,
            "bora_text": entry.get("bora_text", "").strip(),
            "spanish_text": entry.get("spanish_text", "").strip(),
            "category": category,
            "page": difficulty,
            "source": PHRASES_SOURCE,
        }
        examples.append(payload)
        metadata_lookup[(lemma_id, payload["bora_text"], payload["spanish_text"])] = {
            "usage_context": entry.get("usage_context"),
            "direction": entry.get("direction") or "bora_es",
        }

    return examples, stats, metadata_lookup


def build_lemma_docs(rows: List[Dict[str, Any]], extra_meta: Optional[Dict[str, Any]] = None) -> Tuple[List[str], List[Dict[str, Any]]]:
    texts: List[str] = []
    docs: List[Dict[str, Any]] = []
    for row in rows:
        lemma_id = row.get("id")
        if not lemma_id:
            continue
        lemma = row.get("lemma")
        gloss = row.get("gloss_es") or row.get("gloss_bora") or "—"
        pos = row.get("pos_full") or row.get("pos") or "lexema"
        content = f"[LEMMA] {lemma} | DEF: {gloss} | POS: {pos}"
        texts.append(content)
        metadata = {
            "source": row.get("source"),
            "direction": row.get("direction"),
            "pos": row.get("pos"),
            "pos_full": row.get("pos_full"),
        }
        if extra_meta:
            metadata.update(extra_meta)
        docs.append(
            {
                "kind": "lemma",
                "parent_lemma_id": lemma_id,
                "subentry_id": None,
                "example_id": None,
                "content": content,
                "metadata": metadata,
            }
        )
    return texts, docs


def build_phrase_example_docs(
    examples: List[Dict[str, Any]],
    lemma_lookup: Dict[int, Dict[str, Any]],
    metadata_lookup: Dict[Tuple[int, str, str], Dict[str, Any]],
) -> Tuple[List[str], List[Dict[str, Any]]]:
    texts: List[str] = []
    docs: List[Dict[str, Any]] = []
    for ex in examples:
        example_id = ex.get("id")
        lemma_id = ex.get("lemma_id")
        if not example_id or not lemma_id:
            continue
        lemma_meta = lemma_lookup.get(lemma_id) or {}
        category = ex.get("category")
        difficulty = ex.get("page")
        meta_key = (lemma_id, ex.get("bora_text"), ex.get("spanish_text"))
        extra_meta = metadata_lookup.get(meta_key) or {}
        content = (
            f"BORA: {ex.get('bora_text')} [SEP] ES: {ex.get('spanish_text')} "
            f"[SEP] CATEGORY: {category} DIFFICULTY: {difficulty}"
        )
        texts.append(content)
        docs.append(
            {
                "kind": "example",
                "parent_lemma_id": lemma_id,
                "subentry_id": None,
                "example_id": example_id,
                "content": content,
                "metadata": {
                    "source": PHRASES_SOURCE,
                    "direction": extra_meta.get("direction") or lemma_meta.get("direction"),
                    "category": category,
                    "difficulty_level": difficulty,
                    "usage_context": extra_meta.get("usage_context"),
                    "lemma": lemma_meta.get("lemma"),
                },
            }
        )
    return texts, docs


def purge_sources(supa: SupabaseAdapter, reset: bool) -> None:
    """Borra datos previos según el modo reset."""
    client = supa.client
    if not client:
        return

    sources = [VOCAB_SOURCE, PHRASES_SOURCE]

    if reset:
        for src in sources:
            logger.info("🧹 Reset: eliminando lemmas/source=%s (cascade)", src)
            client.table("lexicon_lemmas").delete().eq("source", src).execute()
        return

    # Sin reset: borrar solo dependencias directas para permitir reinserción idempotente
    logger.info("🧼 Limpieza ligera: eliminando bora_docs y ejemplos previos por source…")
    for src in sources:
        client.table("bora_docs").delete().eq("metadata->>source", src).execute()
    client.table("lexicon_examples").delete().eq("source", PHRASES_SOURCE).execute()


def main(args: argparse.Namespace) -> int:
    vocab_path = Path(args.vocab_path).resolve() if args.vocab_path else None
    phrases_path = Path(args.phrases_path).resolve() if args.phrases_path else None

    vocab_data = load_json(vocab_path, args.limit_vocab)
    phrases_data = load_json(phrases_path, args.limit_phrases)

    logger.info("📄 Registros vocabulario: %s", len(vocab_data))
    logger.info("📄 Registros frases: %s", len(phrases_data))

    vocab_lemmas, vocab_stats = build_vocab_lemmas(vocab_data)
    phrase_lemmas, category_index = build_phrase_category_lemmas(phrases_data)

    logger.info(
        "🧮 Vocabulario → total=%s dedup=%s skipped=%s",
        vocab_stats["total"],
        vocab_stats["deduped"],
        vocab_stats["skipped"],
    )
    logger.info("🧮 Categorías detectadas: %s", len(category_index))

    if args.dry_run:
        logger.info("✅ Dry-run: no se realizarán escrituras en Supabase")
        return 0

    supa = SupabaseAdapter(use_service_role=True)
    if not supa.is_connected():
        logger.error("Supabase no configurado. Revisa SUPABASE_URL/SUPABASE_SERVICE_KEY")
        return 1

    openai_api_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY no configurada; requerimos OpenAI para embeddings de 1536 dims.")
        return 1

    embedding_model = settings.EMBEDDING_API_MODEL or "text-embedding-3-small"
    openai_client = OpenAI(api_key=openai_api_key)
    logger.info("🤖 OpenAI embeddings habilitados (%s, 1536 dims)", embedding_model)

    purge_sources(supa, reset=args.reset)

    # 1) Upsert de lemmas (vocabulario + categorías)
    all_lemmas = vocab_lemmas + phrase_lemmas
    saved_lemmas: List[Dict[str, Any]] = []
    for chunk in chunked(all_lemmas, args.batch_size):
        result = awaitable(supa.upsert_lemmas_bulk)(chunk)
        rows = result or []
        if not rows:
            rows = insert_lemmas_direct(supa, chunk)
        saved_lemmas.extend(rows)
        logger.info("💾 Lemmas upsert acumulados: %s/%s", len(saved_lemmas), len(all_lemmas))

    if not saved_lemmas:
        logger.error("No se insertaron lemmas; abortando")
        return 1

    lemma_meta_by_id = {row["id"]: row for row in saved_lemmas if row.get("id")}
    lemma_meta_by_name = {row["lemma"]: row for row in saved_lemmas if row.get("lemma")}

    # Mapear categorías a IDs reales
    category_to_id: Dict[str, int] = {}
    for category, lemma_payload in category_index.items():
        saved = lemma_meta_by_name.get(lemma_payload["lemma"])
        if saved and saved.get("id"):
            category_to_id[category] = saved["id"]

    # 2) Insertar ejemplos de frases (si aplica)
    phrase_examples: List[Dict[str, Any]] = []
    example_inserted: List[Dict[str, Any]] = []
    example_meta_lookup: Dict[Tuple[int, str, str], Dict[str, Any]] = {}
    if phrases_data:
        phrase_examples, phrase_stats, example_meta_lookup = build_phrase_examples(phrases_data, category_to_id)
        logger.info(
            "🧮 Frases → total=%s dedup=%s skipped=%s",
            phrase_stats["total"],
            phrase_stats["deduped"],
            phrase_stats["skipped"],
        )
        for chunk in chunked(phrase_examples, args.batch_size):
            inserted = awaitable(supa.insert_examples_bulk)(chunk)
            example_inserted.extend(inserted or [])
        logger.info("💾 Ejemplos insertados: %s", len(example_inserted))

    # 3) Preparar documentos para embeddings
    vocab_lemma_rows = [row for row in saved_lemmas if row.get("source") == VOCAB_SOURCE]
    phrase_lemma_rows = [row for row in saved_lemmas if row.get("source") == PHRASES_SOURCE]

    docs_to_embed: List[Dict[str, Any]] = []
    texts_to_embed: List[str] = []

    for rows in (vocab_lemma_rows, phrase_lemma_rows):
        if not rows:
            continue
        texts, docs = build_lemma_docs(rows)
        texts_to_embed.extend(texts)
        docs_to_embed.extend(docs)

    if example_inserted:
        texts, docs = build_phrase_example_docs(example_inserted, lemma_meta_by_id, example_meta_lookup)
        texts_to_embed.extend(texts)
        docs_to_embed.extend(docs)

    if not texts_to_embed:
        logger.warning("No hay documentos para vectorizar")
        return 0

    logger.info(
        "🧠 Generando %s embeddings con OpenAI %s (1536 dims, batch=%s)",
        len(texts_to_embed),
        embedding_model,
        args.embed_batch_size,
    )

    embeddings_1536: List[List[float]] = []
    total_batches = (len(texts_to_embed) - 1) // args.embed_batch_size + 1
    for batch_idx in range(0, len(texts_to_embed), args.embed_batch_size):
        chunk = texts_to_embed[batch_idx : batch_idx + args.embed_batch_size]
        try:
            response = openai_client.embeddings.create(
                model=embedding_model,
                input=chunk,
            )
        except Exception as exc:
            logger.error("Error generando embeddings en batch %s/%s: %s", (batch_idx // args.embed_batch_size) + 1, total_batches, exc)
            return 1

        chunk_embeddings = [item.embedding for item in response.data]
        if len(chunk_embeddings) != len(chunk):
            logger.error(
                "OpenAI retornó %s embeddings para un batch de %s textos",
                len(chunk_embeddings),
                len(chunk),
            )
            return 1
        embeddings_1536.extend(chunk_embeddings)
        logger.info(
            "  ✓ Batch %s/%s listo",
            (batch_idx // args.embed_batch_size) + 1,
            total_batches,
        )

    if len(embeddings_1536) != len(docs_to_embed):
        logger.error(
            "Desfase entre textos (%s) y embeddings (%s)",
            len(docs_to_embed),
            len(embeddings_1536),
        )
        return 1

    docs_with_embeddings: List[Dict[str, Any]] = []
    for doc, emb in zip(docs_to_embed, embeddings_1536):
        doc_with_emb = dict(doc)
        doc_with_emb["embedding_1536"] = emb
        doc_with_emb["embedding"] = None
        docs_with_embeddings.append(doc_with_emb)

    docs_batch_size = getattr(args, "docs_batch_size", None) or min(args.batch_size, 100)
    if docs_batch_size != args.batch_size:
        logger.info(
            "⚙️  Ajustando batch de bora_docs a %s para evitar timeouts (batch original=%s)",
            docs_batch_size,
            args.batch_size,
        )

    total_docs = 0
    for chunk in chunked(docs_with_embeddings, docs_batch_size):
        inserted = awaitable(supa.insert_bora_docs_bulk)(chunk)
        total_docs += inserted
        logger.info(
            "📦 bora_docs insertados (acumulado): %s/%s (último batch=%s)",
            total_docs,
            len(docs_with_embeddings),
            inserted,
        )

    logger.info("✅ Ingesta completada | lemmas=%s | ejemplos=%s | docs=%s", len(saved_lemmas), len(example_inserted), total_docs)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingesta de vocabulario y frases curadas")
    default_vocab = str(BACKEND_ROOT.parent / "vocabulario_v1.json")
    default_phrases = str(BACKEND_ROOT.parent / "frases_v1.json")
    parser.add_argument("--vocab-path", type=str, default=default_vocab)
    parser.add_argument("--phrases-path", type=str, default=default_phrases)
    parser.add_argument("--limit-vocab", type=int, default=None)
    parser.add_argument("--limit-phrases", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=400)
    parser.add_argument("--embed-batch-size", type=int, default=64)
    parser.add_argument("--docs-batch-size", type=int, default=100)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    raise SystemExit(main(args))