"""
Ingesta de salida.json al lexicón (tablas lexicon_entries y lexicon_embeddings en Supabase).

Uso:
    - Por defecto busca el archivo en la raíz del proyecto: ../salida.json
    - --path "c:/ruta/salida.json" para personalizar la ruta
    - --reset para borrar previamente entradas con source=salida.json (CASCADE en embeddings)
    - --dry-run para simular sin escribir en la base de datos

Lee entradas del diccionario y para cada ejemplo crea una entrada en lexicon_entries
y genera su embedding en lexicon_embeddings. Si ya existe la entrada o el embedding, los omite.
"""
import argparse
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import logging
import sys

# Ensure backend root is on sys.path so `adapters` imports work when running as a script
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from adapters.huggingface_adapter_hybrid import get_huggingface_hybrid_adapter
from adapters.supabase_adapter import SupabaseAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def normalize_category(entry: Dict[str, Any]) -> str:
    # Categoría tentativa a partir de pos/pos_full; se puede mejorar luego
    return entry.get('pos_full') or entry.get('pos') or 'Diccionario'


def extract_examples(entry: Dict[str, Any]) -> List[Dict[str, str]]:
    examples = []
    # Ejemplos directos
    for ex in entry.get('examples', []) or []:
        bora = ex.get('bora') or ''
        es = ex.get('es') or ''
        if bora and es:
            examples.append({'bora': bora.strip(), 'es': es.strip()})
    # Subentradas con ejemplos
    for sub in entry.get('subentries', []) or []:
        for ex in sub.get('examples', []) or []:
            bora = ex.get('bora') or ''
            es = ex.get('es') or ''
            if bora and es:
                examples.append({'bora': bora.strip(), 'es': es.strip()})
    return examples


def build_phrase_rows(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    category = normalize_category(entry)
    rows: List[Dict[str, Any]] = []
    for ex in extract_examples(entry):
        rows.append({
            'bora_text': ex['bora'],
            'spanish_text': ex['es'],
            'category': category,
            'difficulty': 1,
            'usage_context': None,
            'pronunciation_guide': None,
        })
    return rows


def build_entry_row(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Construye una fila resumen para el lemma (vista 'entry')."""
    return {
        'bora_text': None,  # no aplica
        'spanish_text': None,  # no aplica
        'lemma': entry.get('lemma'),
        'pos': entry.get('pos'),
        'pos_full': entry.get('pos_full'),
        'category': entry.get('pos_full') or entry.get('pos') or 'Diccionario',
        'page': entry.get('page'),
        'variants': entry.get('variants'),
        'synonyms': entry.get('synonyms'),
        'raw': entry.get('raw'),
        'source': 'salida.json',
    }


def main(path: Path, reset: bool = False, dry_run: bool = False, limit: int | None = None, batch_size: int = 256, embed_batch_size: int = 32, sleep_between_batches: float = 0.0):
    logger.info(f"📄 Cargando JSON: {path}")
    if not path.exists():
        logger.error(f"No se encontró el archivo: {path}")
        return 1
    data = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(limit, int) and limit > 0:
        data = data[:limit]
    logger.info(f"🔎 Entradas: {len(data)}")

    # Para ingesta server-side usamos la service_role key (RLS: write permitido)
    supabase = SupabaseAdapter(use_service_role=True)
    if not supabase.is_connected() and not dry_run:
        logger.error("Supabase no configurado. Revisa SUPABASE_URL y SUPABASE_ANON_KEY en .env")
        return 1

    hf = None if dry_run else get_huggingface_hybrid_adapter()

    # Opcional: reset del corpus del lexicón por source
    if reset and not dry_run:
        logger.info("🧹 Reset por source=salida.json en lexicon_entries (CASCADE)")
        ok_reset = awaitable(supabase.reset_lexicon_source)('salida.json')
        if ok_reset:
            logger.info("Reset ejecutado correctamente")
        else:
            logger.warning("No se pudo ejecutar el reset (revisa logs de Supabase)")

    inserted = 0
    embedded = 0
    lemma_to_entry_id: Dict[str, int] = {}
    lemma_info: Dict[str, Dict[str, Any]] = {}

    # Preconstruir todas las filas del lexicón (pueden ser muchas, pero es lineal)
    all_rows: List[Dict[str, Any]] = []
    entry_rows: List[Dict[str, Any]] = []
    for entry in data:
        for row in build_phrase_rows(entry):
            all_rows.append({
                'bora_text': row['bora_text'],
                'spanish_text': row['spanish_text'],
                'lemma': entry.get('lemma'),
                'pos': entry.get('pos'),
                'pos_full': entry.get('pos_full'),
                'category': row.get('category') or entry.get('pos_full'),
                'page': entry.get('page'),
                'variants': entry.get('variants'),
                'synonyms': entry.get('synonyms'),
                'raw': entry.get('raw'),
                'source': 'salida.json',
            })
        # Agregar una fila por entrada (lemma) para vista 'entry'
        er = build_entry_row(entry)
        entry_rows.append(er)
        # Guardar info por lemma para construir texto/metadata luego
        if er.get('lemma'):
            lemma_info[er['lemma']] = er

    logger.info(f"🧮 Filas totales a upsert en lexicon_entries (examples): {len(all_rows)}")
    logger.info(f"🧮 Filas totales 'entry' (lemmas) a procesar: {len(entry_rows)}")

    # Procesar en batches
    for start in range(0, len(all_rows), batch_size):
        batch = all_rows[start:start+batch_size]

        # 1) Upsert de entradas (salteado en dry-run)
        if dry_run:
            batch_with_ids = [dict(row, id=-1) for row in batch]
        else:
            upserted = awaitable(supabase.upsert_lexicon_entries_bulk)(batch)
            # Mapear ids por (bora_text, spanish_text)
            index = {(r['bora_text'], r['spanish_text']): r['id'] for r in (upserted or []) if 'id' in r}
            # Completar IDs en orden del batch (si no está, requiere una consulta fallback)
            batch_with_ids = []
            for row in batch:
                key = (row['bora_text'], row['spanish_text'])
                entry_id = index.get(key)
                if entry_id is None:
                    # Fallback: lookup puntual (raro, pero por seguridad)
                    found = awaitable(supabase.find_lexicon_by_texts)(*key)
                    entry_id = found['id'] if found else None
                if entry_id is None:
                    # No se pudo insertar ni recuperar; saltar
                    continue
                # Mapear lemma -> entry_id si aplica (primera ocurrencia)
                lm = row.get('lemma')
                if lm and lm not in lemma_to_entry_id:
                    lemma_to_entry_id[lm] = entry_id
                batch_with_ids.append(dict(row, id=entry_id))

        inserted += len(batch_with_ids)

        # 2) Filtrar los que ya tienen embedding (kind='example') (salteado en dry-run)
        if dry_run:
            todo_for_embedding = batch_with_ids
        else:
            ids = [r['id'] for r in batch_with_ids]
            have = set(awaitable(supabase.get_existing_lexicon_embeddings_by_kind)(ids, 'example') or [])
            todo_for_embedding = [r for r in batch_with_ids if r['id'] not in have]

        # 3) Generar embeddings en batch (omitido en dry-run)
        if dry_run:
            embedded += len(todo_for_embedding)
        else:
            # Construcción del texto etiquetado (preserva tildes; no normalizar)
            texts = [
                f"BORA: {r['bora_text']} [SEP] ES: {r['spanish_text']} [SEP] LEMMA: {r.get('lemma')} POS: {r.get('pos_full') or r.get('pos')}"
                for r in todo_for_embedding
            ]
            embs = hf.generate_embeddings_batch(texts, batch_size=embed_batch_size, show_progress=False)
            rows_to_insert = []
            for r, emb in zip(todo_for_embedding, embs):
                if not emb:
                    continue
                rows_to_insert.append({
                    'entry_id': r['id'],
                    'embedding': emb,
                    'metadata': {
                        'kind': 'example',
                        'source': 'salida.json',
                        'category': r.get('category'),
                        'lemma': r.get('lemma'),
                        'page': r.get('page'),
                        'bora_text': r.get('bora_text'),
                        'spanish_text': r.get('spanish_text'),
                        'pos': r.get('pos'),
                        'pos_full': r.get('pos_full'),
                    }
                })
            if rows_to_insert:
                inserted_count = awaitable(supabase.insert_lexicon_embeddings_bulk)(rows_to_insert)
                embedded += inserted_count

        logger.info(f"Batch {start//batch_size + 1}: entradas procesadas {len(batch_with_ids)}, embeddings nuevos {embedded}")

        if sleep_between_batches > 0:
            import time
            time.sleep(sleep_between_batches)

    # === PROCESAR VISTA 'ENTRY' (lemmas) ===
    logger.info("🧠 Procesando embeddings de lemmas (kind='entry')...")
    if not dry_run:
        # Construir lista de pares (lemma, entry_id) únicos
        lemma_pairs: List[Tuple[str, int]] = [(lm, eid) for lm, eid in lemma_to_entry_id.items() if lm]
        if lemma_pairs:
            # Evitar duplicados por entry_id con kind='entry'
            entry_ids = [eid for _, eid in lemma_pairs]
            have_entry_kind = set(awaitable(supabase.get_existing_lexicon_embeddings_by_kind)(entry_ids, 'entry') or [])
            # Preparar textos y metadatos
            texts: List[str] = []
            target_rows: List[Dict[str, Any]] = []
            for lm, eid in lemma_pairs:
                if eid in have_entry_kind:
                    continue
                info = lemma_info.get(lm) or {}
                pos = info.get('pos')
                pos_full = info.get('pos_full') or pos
                # Plantilla 'entry': etiquetas explícitas, preservando tildes
                # Opcional: variantes/sinónimos si vienen limpios
                variants = info.get('variants')
                synonyms = info.get('synonyms')
                extra = []
                if variants:
                    try:
                        if isinstance(variants, list):
                            extra.append("VAR: " + ", ".join([str(v) for v in variants if v]))
                        else:
                            extra.append("VAR: " + str(variants))
                    except Exception:
                        pass
                if synonyms:
                    try:
                        if isinstance(synonyms, list):
                            extra.append("SIN: " + ", ".join([str(s) for s in synonyms if s]))
                        else:
                            extra.append("SIN: " + str(synonyms))
                    except Exception:
                        pass
                extra_text = (" | " + " | ".join(extra)) if extra else ""
                content = f"[LEMMA] {lm} | POS: {pos} ({pos_full}){extra_text}"
                texts.append(content)
                target_rows.append({
                    'entry_id': eid,
                    'metadata': {
                        'kind': 'entry',
                        'source': 'salida.json',
                        'lemma': lm,
                        'pos': pos,
                        'pos_full': pos_full,
                        'page': info.get('page'),
                    }
                })

            if texts:
                embs = hf.generate_embeddings_batch(texts, batch_size=embed_batch_size, show_progress=False)
                to_insert = []
                for meta_row, emb in zip(target_rows, embs):
                    if not emb:
                        continue
                    to_insert.append({
                        'entry_id': meta_row['entry_id'],
                        'embedding': emb,
                        'metadata': meta_row['metadata']
                    })
                if to_insert:
                    cnt = awaitable(supabase.insert_lexicon_embeddings_bulk)(to_insert)
                    embedded += cnt

    logger.info(f"✅ Terminado. Entradas procesadas: {inserted}, embeddings creados: {embedded}")
    return 0


def awaitable(fn):
    """Permite invocar funciones async desde un script sync.

    Si la función retorna una corrutina, la ejecuta en un event loop temporal.
    """
    import asyncio
    import inspect

    def wrapper(*args, **kwargs):
        result = fn(*args, **kwargs)
        if inspect.iscoroutine(result):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Crear un nuevo loop si ya hay uno corriendo
                    new_loop = asyncio.new_event_loop()
                    try:
                        return new_loop.run_until_complete(result)
                    finally:
                        new_loop.close()
                else:
                    return loop.run_until_complete(result)
            except RuntimeError:
                # No hay loop, crear uno nuevo
                loop = asyncio.new_event_loop()
                try:
                    return loop.run_until_complete(result)
                finally:
                    loop.close()
        return result

    return wrapper


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, default=str(Path(__file__).parents[2] / 'salida.json'))
    parser.add_argument('--reset', action='store_true', help='Borra datos previos del lexicón con source=salida.json')
    parser.add_argument('--dry-run', action='store_true', help='Simula sin escribir en la base de datos')
    parser.add_argument('--limit', type=int, default=None, help='Procesa solo las primeras N entradas del JSON')
    parser.add_argument('--batch-size', type=int, default=256, help='Tamaño del batch para upsert de entradas')
    parser.add_argument('--embed-batch-size', type=int, default=32, help='Tamaño del batch para generar embeddings locales')
    parser.add_argument('--sleep-between-batches', type=float, default=0.0, help='Pausa en segundos entre batches (0 para sin pausa)')
    args = parser.parse_args()
    exit(main(Path(args.path), reset=args.reset, dry_run=args.dry_run, limit=args.limit, batch_size=args.batch_size, embed_batch_size=args.embed_batch_size, sleep_between_batches=args.sleep_between_batches))
