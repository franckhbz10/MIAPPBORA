"""
Ingesta de salida.json al nuevo esquema unificado (lexicon_lemmas, lexicon_subentries, lexicon_examples, bora_docs).

Uso típico:
  python backend/scripts/ingest_bora_docs.py --path ../salida.json --batch-size 400 --embed-batch-size 64 --reset

Requisitos:
  - .env con SUPABASE_URL, SUPABASE_SERVICE_KEY (se usa service_role para escritura bajo RLS)
  - Embeddings locales con sentence-transformers/all-MiniLM-L6-v2 (384)
"""
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import logging
import sys

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from adapters.supabase_adapter import SupabaseAdapter
from adapters.huggingface_adapter_hybrid import get_huggingface_hybrid_adapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def awaitable(fn):
    import asyncio, inspect

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


def parse_json(path: Path, limit: Optional[int]) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(limit, int) and limit > 0:
        data = data[:limit]
    return data


def build_lemmas(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen: set[Tuple[str, str]] = set()
    for e in data:
        lemma = e.get('lemma')
        gloss = e.get('gloss_es') or e.get('gloss') or e.get('glossEs')
        if not lemma or not gloss:
            # gloss_es debe existir en lemma (restricción dada)
            continue
        key = (lemma, 'salida.json')
        if key in seen:
            continue
        seen.add(key)
        out.append({
            'lemma': lemma,
            'gloss_es': gloss,
            'pos': e.get('pos'),
            'pos_full': e.get('pos_full') or e.get('pos'),
            'page': e.get('page'),
            'variants': e.get('variants'),
            'synonyms': None,  # fuera de alcance del sprint
            'raw': e.get('raw'),
            'source': 'salida.json',
        })
    return out


def build_subentries(data: List[Dict[str, Any]], lemma_index: Dict[str, int]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen: set[Tuple[int, str, str]] = set()
    for e in data:
        lemma = e.get('lemma')
        lemma_id = lemma_index.get(lemma)
        if not lemma_id:
            continue
        for sub in e.get('subentries', []) or []:
            gloss = sub.get('gloss_es') or sub.get('glossEs') or sub.get('gloss')
            if not gloss:
                # gloss_es obligatorio en subentrada
                continue
            sublemma = sub.get('sublemma') or sub.get('bora') or ''
            key = (lemma_id, sublemma, gloss)
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                'lemma_id': lemma_id,
                'sublemma': sublemma or None,
                'gloss_es': gloss,
                'pos': sub.get('pos'),
                'pos_full': sub.get('pos_full') or sub.get('pos'),
                'page': sub.get('page') or e.get('page'),
                'variants': sub.get('variants'),
                'synonyms': None,
                'raw': sub.get('raw'),
            })
    return rows


def build_examples(data: List[Dict[str, Any]], lemma_index: Dict[str, int], sub_idx_by_key: Dict[Tuple[int, str, str], int]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen: set[Tuple[int, Optional[int], str, str, str]] = set()
    for e in data:
        lemma = e.get('lemma')
        lemma_id = lemma_index.get(lemma)
        if not lemma_id:
            continue
        # ejemplos al nivel de lemma
        for ex in e.get('examples', []) or []:
            bora = (ex.get('bora') or '').strip()
            es = (ex.get('es') or '').strip()
            if bora and es:
                key = (lemma_id, None, bora, es, 'salida.json')
                if key in seen:
                    continue
                seen.add(key)
                rows.append({
                    'lemma_id': lemma_id,
                    'subentry_id': None,
                    'bora_text': bora,
                    'spanish_text': es,
                    'category': e.get('pos_full') or e.get('pos') or 'Diccionario',
                    'page': e.get('page'),
                    'source': 'salida.json',
                })
        # ejemplos por subentrada
        for sub in e.get('subentries', []) or []:
            gloss = sub.get('gloss_es') or sub.get('glossEs') or sub.get('gloss')
            if not gloss:
                continue
            sublemma = sub.get('sublemma') or sub.get('bora') or ''
            key = (lemma_id, sublemma, gloss)
            subentry_id = sub_idx_by_key.get(key)
            for ex in sub.get('examples', []) or []:
                bora = (ex.get('bora') or '').strip()
                es = (ex.get('es') or '').strip()
                if bora and es:
                    k = (lemma_id, subentry_id, bora, es, 'salida.json')
                    if k in seen:
                        continue
                    seen.add(k)
                    rows.append({
                        'lemma_id': lemma_id,
                        'subentry_id': subentry_id,
                        'bora_text': bora,
                        'spanish_text': es,
                        'category': sub.get('pos_full') or sub.get('pos') or e.get('pos_full') or e.get('pos') or 'Diccionario',
                        'page': sub.get('page') or e.get('page'),
                        'source': 'salida.json',
                    })
    return rows


def build_bora_docs_texts_for_kind(
    kind: str,
    items: List[Dict[str, Any]],
    lemma_meta: Dict[int, Dict[str, Any]],
) -> Tuple[List[str], List[Dict[str, Any]]]:
    texts: List[str] = []
    records: List[Dict[str, Any]] = []
    if kind == 'lemma':
        for it in items:
            lemma_id = it['id']
            meta = lemma_meta[lemma_id]
            content = f"[LEMMA] {meta.get('lemma')} | DEF_ES: {meta.get('gloss_es')} | POS: {meta.get('pos_full') or meta.get('pos')} | PAG: {meta.get('page')}"
            texts.append(content)
            records.append({
                'kind': 'lemma',
                'parent_lemma_id': lemma_id,
                'subentry_id': None,
                'example_id': None,
                'content': content,
                'metadata': {
                    'source': 'salida.json',
                    'lemma': meta.get('lemma'),
                    'gloss_es': meta.get('gloss_es'),
                    'pos': meta.get('pos'),
                    'pos_full': meta.get('pos_full'),
                    'page': meta.get('page'),
                }
            })
    elif kind == 'subentry':
        for it in items:
            lemma_id = it['lemma_id']
            content = f"[SUBLEMMA] {it.get('sublemma')} | DEF_ES: {it.get('gloss_es')} | POS: {it.get('pos_full') or it.get('pos')} | PAG: {it.get('page')}"
            texts.append(content)
            records.append({
                'kind': 'subentry',
                'parent_lemma_id': lemma_id,
                'subentry_id': it['id'],
                'example_id': None,
                'content': content,
                'metadata': {
                    'source': 'salida.json',
                    'lemma': lemma_meta[lemma_id].get('lemma'),
                    'sublemma': it.get('sublemma'),
                    'gloss_es': it.get('gloss_es'),
                    'pos': it.get('pos'),
                    'pos_full': it.get('pos_full') or it.get('pos'),
                    'page': it.get('page'),
                }
            })
    elif kind == 'example':
        for it in items:
            lemma_id = it['lemma_id']
            meta = lemma_meta[lemma_id]
            content = f"BORA: {it['bora_text']} [SEP] ES: {it['spanish_text']} [SEP] LEMMA: {meta.get('lemma')} POS: {meta.get('pos_full') or meta.get('pos')}"
            texts.append(content)
            records.append({
                'kind': 'example',
                'parent_lemma_id': lemma_id,
                'subentry_id': it.get('subentry_id'),
                'example_id': it['id'],
                'content': content,
                'metadata': {
                    'source': 'salida.json',
                    'lemma': meta.get('lemma'),
                    'gloss_es': meta.get('gloss_es'),
                    'pos': meta.get('pos'),
                    'pos_full': meta.get('pos_full') or meta.get('pos'),
                    'page': it.get('page'),
                    'bora_text': it['bora_text'],
                    'spanish_text': it['spanish_text'],
                }
            })
    return texts, records


def main(path: Path, reset: bool, limit: Optional[int], batch_size: int, embed_batch_size: int) -> int:
    logger.info(f"📄 Cargando JSON: {path}")
    if not path.exists():
        logger.error(f"No se encontró el archivo: {path}")
        return 1

    data = parse_json(path, limit)
    logger.info(f"🔎 Entradas en JSON: {len(data)}")

    supa = SupabaseAdapter(use_service_role=True)
    if not supa.is_connected():
        logger.error("Supabase no configurado (revisa SUPABASE_URL y SUPABASE_SERVICE_KEY en .env)")
        return 1
    hf = get_huggingface_hybrid_adapter()

    # Reset opcional (borra lemmas por source y CASCADE el resto)
    if reset:
        try:
            from supabase import Client  # solo para tipado/confirmación
            # Eliminar desde lemmas para cascada en subentries, examples y bora_docs
            supa.client.table('lexicon_lemmas').delete().eq('source', 'salida.json').execute()
            logger.info("🧹 Reset ejecutado (lemmas por source)")
        except Exception as e:
            logger.warning(f"No se pudo ejecutar reset vía API: {e}")

    # 1) Lemmas
    lemmas = build_lemmas(data)
    # Upsert lemmas en batches
    saved_lemmas: List[Dict[str, Any]] = []
    for i in range(0, len(lemmas), batch_size):
        chunk = lemmas[i:i+batch_size]
        part = awaitable(supa.upsert_lemmas_bulk)(chunk)
        if part:
            saved_lemmas.extend(part)
        logger.info(f"🧩 Lemmas upsert: {len(saved_lemmas)}/{len(lemmas)}")
    if not saved_lemmas:
        logger.error("No se pudieron insertar/upsert lemmas")
        return 1
    lemma_index: Dict[str, int] = {r['lemma']: r['id'] for r in saved_lemmas if r.get('lemma') and r.get('id')}
    lemma_meta: Dict[int, Dict[str, Any]] = {r['id']: r for r in saved_lemmas if r.get('id')}
    logger.info(f"✅ Lemmas procesados: {len(lemma_index)}")

    # 2) Subentries
    subs = build_subentries(data, lemma_index)
    # Insert subentries en batches
    saved_subs: List[Dict[str, Any]] = []
    for i in range(0, len(subs), batch_size):
        chunk = subs[i:i+batch_size]
        part = awaitable(supa.insert_subentries_bulk)(chunk)
        if part:
            saved_subs.extend(part)
        logger.info(f"🧩 Subentradas insert: {len(saved_subs)}/{len(subs)}")
    # Índice de subentry para ejemplos por clave
    sub_idx_by_key: Dict[Tuple[int, str, str], int] = {}
    for s in saved_subs or []:
        key = (s.get('lemma_id'), s.get('sublemma') or '', s.get('gloss_es') or '')
        if s.get('id'):
            sub_idx_by_key[key] = s['id']
    logger.info(f"✅ Subentradas procesadas: {len(saved_subs or [])}")

    # 3) Examples
    examples = build_examples(data, lemma_index, sub_idx_by_key)
    # Insert examples en batches
    saved_examples: List[Dict[str, Any]] = []
    for i in range(0, len(examples), batch_size):
        chunk = examples[i:i+batch_size]
        part = awaitable(supa.insert_examples_bulk)(chunk)
        if part:
            saved_examples.extend(part)
        logger.info(f"🧩 Ejemplos insert: {len(saved_examples)}/{len(examples)}")
    # Reindex examples by a simple tuple
    # Nota: la API retorna filas insertadas; asumimos únicas por restricción
    ex_idx_by_fields: Dict[Tuple[int, Optional[int], str, str], int] = {}
    for ex in saved_examples or []:
        key = (ex.get('lemma_id'), ex.get('subentry_id'), ex.get('bora_text'), ex.get('spanish_text'))
        if ex.get('id') is not None:
            ex_idx_by_fields[key] = ex['id']
    logger.info(f"✅ Ejemplos procesados: {len(saved_examples or [])}")

    # 4) Embeddings y bora_docs
    inserted_docs = 0

    # 4a) Lemmas -> bora_docs(kind='lemma')
    texts, records = build_bora_docs_texts_for_kind('lemma', saved_lemmas or [], lemma_meta)
    if texts:
        embs = hf.generate_embeddings_batch(texts, batch_size=embed_batch_size, show_progress=False)
        docs = []
        for rec, emb in zip(records, embs):
            if emb:
                docs.append({**rec, 'embedding': emb})
        # Insert docs en batches
        for j in range(0, len(docs), batch_size):
            part = docs[j:j+batch_size]
            inserted_docs += awaitable(supa.insert_bora_docs_bulk)(part)
        logger.info(f"📦 bora_docs (lemma): +{len(docs)}")

    # 4b) Subentries -> bora_docs(kind='subentry')
    texts, records = build_bora_docs_texts_for_kind('subentry', saved_subs or [], lemma_meta)
    if texts:
        embs = hf.generate_embeddings_batch(texts, batch_size=embed_batch_size, show_progress=False)
        docs = []
        for rec, emb in zip(records, embs):
            if emb:
                docs.append({**rec, 'embedding': emb})
        for j in range(0, len(docs), batch_size):
            part = docs[j:j+batch_size]
            inserted_docs += awaitable(supa.insert_bora_docs_bulk)(part)
        logger.info(f"📦 bora_docs (subentry): +{len(docs)}")

    # 4c) Examples -> bora_docs(kind='example')
    # Reconstruir items con IDs de example
    example_items: List[Dict[str, Any]] = []
    for ex in saved_examples or []:
        if ex.get('id') is None:
            # Si el proveedor no devolvió ids, intentamos mapear
            key = (ex.get('lemma_id'), ex.get('subentry_id'), ex.get('bora_text'), ex.get('spanish_text'))
            ex_id = ex_idx_by_fields.get(key)
        else:
            ex_id = ex['id']
        if ex_id is None:
            continue
        example_items.append(ex | {'id': ex_id})
    texts, records = build_bora_docs_texts_for_kind('example', example_items, lemma_meta)
    if texts:
        embs = hf.generate_embeddings_batch(texts, batch_size=embed_batch_size, show_progress=False)
        docs = []
        for rec, emb in zip(records, embs):
            if emb:
                docs.append({**rec, 'embedding': emb})
        for j in range(0, len(docs), batch_size):
            part = docs[j:j+batch_size]
            inserted_docs += awaitable(supa.insert_bora_docs_bulk)(part)
        logger.info(f"📦 bora_docs (example): +{len(docs)}")

    logger.info(f"✅ Finalizado. Documentos vectoriales insertados: {inserted_docs}")
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    default_path = str(Path(__file__).parents[2] / 'salida.json')
    parser.add_argument('--path', type=str, default=default_path)
    parser.add_argument('--reset', action='store_true')
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--batch-size', type=int, default=400)
    parser.add_argument('--embed-batch-size', type=int, default=64)
    args = parser.parse_args()
    raise SystemExit(main(Path(args.path), reset=args.reset, limit=args.limit, batch_size=args.batch_size, embed_batch_size=args.embed_batch_size))
