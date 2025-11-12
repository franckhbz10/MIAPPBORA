"""
Ingesta de salida_es_bora_final.json (Diccionario Español→Bora) al esquema bidireccional.

Diferencias clave vs ingest_bora_docs.py (Bora→ES):
1. gloss_bora en vez de gloss_es
2. Split de gloss_bora por ";" para múltiples traducciones
3. direction='es_bora' en todos los registros
4. Formato de documentos: [LEMMA_ES] en vez de [LEMMA]

Uso típico:
  python backend/scripts/ingest_es_bora_docs.py --path ../salida_es_bora_final.json --batch-size 400 --embed-batch-size 64 --limit 100
  python backend/scripts/ingest_es_bora_docs.py --path ../salida_es_bora_final.json --batch-size 400 --embed-batch-size 64 --reset

Requisitos:
  - .env con SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY
  - Schema bidireccional aplicado (001_bidirectional_schema.sql)
  - USE_EMBEDDING_API=true, USE_VECTOR_1536=true (configuración de producción)
  - Genera embeddings de 1536 dims con OpenAI (compatible con producción Railway)
"""
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import logging
import sys
import os

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Cargar variables de entorno desde .env si existe
try:
    from dotenv import load_dotenv
    env_path = BACKEND_ROOT / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    # python-dotenv no instalado, confiar en variables de entorno del sistema
    pass

from adapters.supabase_adapter import SupabaseAdapter
from openai import OpenAI

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


def build_lemmas_es_bora(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Construye lemmas desde salida_es_bora_final.json
    
    DIFERENCIA CLAVE vs build_lemmas():
    - Usa gloss_bora en vez de gloss_es
    - Split de gloss_bora por ";" para múltiples traducciones
    - direction='es_bora'
    """
    out: List[Dict[str, Any]] = []
    seen: set[Tuple[str, str, str]] = set()
    
    for e in data:
        lemma_es = e.get('lemma')  # Palabra en español
        gloss_bora = e.get('gloss_bora', '')  # Traducción(es) al Bora
        
        if not lemma_es or not gloss_bora:
            continue
        
        # Split por ";" para manejar múltiples traducciones
        # Ej: "ri; vu" → ["ri", "vu"]
        translations = [t.strip() for t in gloss_bora.split(';') if t.strip()]
        
        for translation in translations:
            # Key única: (lemma_español, traducción_bora, source)
            # NOTA: source incluye dirección para evitar conflictos con Bora→ES
            source_key = 'salida_es_bora_final.json'
            key = (lemma_es, translation, source_key)
            if key in seen:
                continue
            seen.add(key)
            
            out.append({
                'lemma': lemma_es,               # Palabra en español
                'gloss_bora': translation,        # UNA traducción al Bora
                'gloss_es': None,                 # NULL para ES→Bora
                'direction': 'es_bora',           # Marcador de dirección
                'pos': e.get('pos'),
                'pos_full': e.get('pos_full'),
                'page': e.get('page'),
                'variants': e.get('variants'),
                'synonyms': e.get('synonyms'),   # Campo presente en ES→Bora
                'raw': None,                      # No disponible en ES→Bora
                'source': source_key,
            })
    
    logger.info(f"📝 Lemmas ES→Bora construidos: {len(out)} (desde {len(data)} entradas)")
    return out


def build_subentries_es_bora(
    data: List[Dict[str, Any]], 
    lemma_index: Dict[str, int]
) -> List[Dict[str, Any]]:
    """
    Construye subentries desde salida_es_bora_final.json
    
    DIFERENCIA CLAVE:
    - Usa gloss_bora en vez de gloss_es
    - direction='es_bora'
    """
    rows: List[Dict[str, Any]] = []
    seen: set[Tuple[int, str, str]] = set()
    
    for e in data:
        lemma_es = e.get('lemma')
        lemma_id = lemma_index.get(lemma_es)
        if not lemma_id:
            continue
        
        for sub in e.get('subentries', []) or []:
            gloss_bora = sub.get('gloss_bora', '')
            if not gloss_bora:
                continue
            
            # sublemma es la frase en español (ej: "a cambio")
            sublemma_es = sub.get('lemma') or sub.get('sublemma') or ''
            
            # Split de traducciones múltiples
            translations = [t.strip() for t in gloss_bora.split(';') if t.strip()]
            
            for translation in translations:
                key = (lemma_id, sublemma_es, translation)
                if key in seen:
                    continue
                seen.add(key)
                
                rows.append({
                    'lemma_id': lemma_id,
                    'sublemma': sublemma_es or None,
                    'gloss_bora': translation,
                    'gloss_es': None,
                    'direction': 'es_bora',
                    'pos': sub.get('pos'),
                    'pos_full': sub.get('pos_full') or sub.get('pos'),
                    'page': sub.get('page') or e.get('page'),
                    'variants': sub.get('variants'),
                    'synonyms': sub.get('synonyms'),
                    'raw': None,
                })
    
    logger.info(f"📑 Subentries ES→Bora construidos: {len(rows)}")
    return rows


def build_examples_es_bora(
    data: List[Dict[str, Any]], 
    lemma_index: Dict[str, int], 
    sub_idx_by_key: Dict[Tuple[int, str, str], int]
) -> List[Dict[str, Any]]:
    """
    Construye examples desde salida_es_bora_final.json
    
    NOTA: El formato de examples es el MISMO para ambas direcciones
    (siempre tiene 'bora' y 'es'), solo cambia el source
    """
    rows: List[Dict[str, Any]] = []
    seen: set[Tuple[int, Optional[int], str, str, str]] = set()
    
    for e in data:
        lemma_es = e.get('lemma')
        lemma_id = lemma_index.get(lemma_es)
        if not lemma_id:
            continue
        
        # Ejemplos al nivel de lemma principal
        for ex in e.get('examples', []) or []:
            bora = (ex.get('bora') or '').strip()
            es = (ex.get('es') or '').strip()
            if bora and es:
                key = (lemma_id, None, bora, es, 'salida_es_bora_final.json')
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
                    'source': 'salida_es_bora_final.json',
                })
        
        # Ejemplos por subentrada
        for sub in e.get('subentries', []) or []:
            gloss_bora = sub.get('gloss_bora', '')
            if not gloss_bora:
                continue
            
            sublemma_es = sub.get('lemma') or sub.get('sublemma') or ''
            translations = [t.strip() for t in gloss_bora.split(';') if t.strip()]
            
            # Buscar subentry_id para cada traducción
            for translation in translations:
                key = (lemma_id, sublemma_es, translation)
                subentry_id = sub_idx_by_key.get(key)
                
                for ex in sub.get('examples', []) or []:
                    bora = (ex.get('bora') or '').strip()
                    es = (ex.get('es') or '').strip()
                    if bora and es:
                        k = (lemma_id, subentry_id, bora, es, 'salida_es_bora_final.json')
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
                            'source': 'salida_es_bora_final.json',
                        })
    
    logger.info(f"💬 Examples ES→Bora construidos: {len(rows)}")
    return rows


def build_bora_docs_texts_es_bora(
    kind: str,
    items: List[Dict[str, Any]],
    lemma_meta: Dict[int, Dict[str, Any]],
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Genera textos para vectorización (ES→Bora)
    
    DIFERENCIA CLAVE:
    - Formato [LEMMA_ES] en vez de [LEMMA]
    - Usa gloss_bora en metadata
    """
    texts: List[str] = []
    records: List[Dict[str, Any]] = []
    
    if kind == 'lemma':
        for it in items:
            lemma_id = it['id']
            meta = lemma_meta[lemma_id]
            
            # Formato: [LEMMA_ES] palabra_español | DEF_BORA: traducción_bora | POS: categoría
            content = f"[LEMMA_ES] {meta.get('lemma')} | DEF_BORA: {meta.get('gloss_bora')} | POS: {meta.get('pos_full') or meta.get('pos')} | PAG: {meta.get('page')}"
            
            texts.append(content)
            records.append({
                'kind': 'lemma',
                'parent_lemma_id': lemma_id,
                'subentry_id': None,
                'example_id': None,
                'content': content,
                'metadata': {
                    'source': 'salida_es_bora_final.json',
                    'direction': 'es_bora',
                    'lemma': meta.get('lemma'),
                    'gloss_bora': meta.get('gloss_bora'),
                    'pos': meta.get('pos'),
                    'pos_full': meta.get('pos_full'),
                    'page': meta.get('page'),
                }
            })
    
    elif kind == 'subentry':
        for it in items:
            lemma_id = it['lemma_id']
            content = f"[SUBLEMMA_ES] {it.get('sublemma')} | DEF_BORA: {it.get('gloss_bora')} | POS: {it.get('pos_full') or it.get('pos')} | PAG: {it.get('page')}"
            texts.append(content)
            records.append({
                'kind': 'subentry',
                'parent_lemma_id': lemma_id,
                'subentry_id': it['id'],
                'example_id': None,
                'content': content,
                'metadata': {
                    'source': 'salida_es_bora_final.json',
                    'direction': 'es_bora',
                    'lemma': lemma_meta[lemma_id].get('lemma'),
                    'sublemma': it.get('sublemma'),
                    'gloss_bora': it.get('gloss_bora'),
                    'pos': it.get('pos'),
                    'pos_full': it.get('pos_full') or it.get('pos'),
                    'page': it.get('page'),
                }
            })
    
    elif kind == 'example':
        # MISMO formato que Bora→ES (bidireccional)
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
                    'source': 'salida_es_bora_final.json',
                    'direction': 'es_bora',
                    'lemma': meta.get('lemma'),
                    'gloss_bora': meta.get('gloss_bora'),
                    'pos': meta.get('pos'),
                    'pos_full': meta.get('pos_full') or meta.get('pos'),
                    'page': it.get('page'),
                    'bora_text': it['bora_text'],
                    'spanish_text': it['spanish_text'],
                }
            })
    
    return texts, records


def main(path: Path, reset: bool, limit: Optional[int], batch_size: int, embed_batch_size: int) -> int:
    logger.info(f"📄 Cargando JSON ES→Bora: {path}")
    if not path.exists():
        logger.error(f"No se encontró el archivo: {path}")
        return 1

    data = parse_json(path, limit)
    logger.info(f"🔎 Entradas en JSON: {len(data)}")

    supa = SupabaseAdapter(use_service_role=True)
    if not supa.is_connected():
        logger.error("Supabase no configurado (revisa SUPABASE_URL y SUPABASE_SERVICE_KEY en .env)")
        return 1
    
    # Inicializar cliente OpenAI para embeddings (1536 dims, compatible con producción)
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    if not openai_api_key:
        logger.error("OPENAI_API_KEY no configurada en .env")
        return 1
    
    openai_client = OpenAI(api_key=openai_api_key)
    logger.info("✅ Cliente OpenAI inicializado para embeddings (text-embedding-3-small, 1536 dims)")


    # Reset opcional (borra lemmas ES→Bora por source Y direction)
    if reset:
        try:
            logger.info("🧹 Ejecutando reset (eliminando registros ES→Bora previos)...")
            # Borrar en orden inverso por foreign keys: bora_docs -> examples -> subentries -> lemmas
            supa.client.table('bora_docs').delete().eq('metadata->>source', 'salida_es_bora_final.json').execute()
            supa.client.table('lexicon_examples').delete().eq('source', 'salida_es_bora_final.json').execute()
            supa.client.table('lexicon_subentries').delete().eq('direction', 'es_bora').execute()
            supa.client.table('lexicon_lemmas').delete().eq('direction', 'es_bora').execute()
            logger.info("✅ Reset completado")
        except Exception as e:
            logger.warning(f"Error en reset: {e}")
            # Intentar borrar solo lemmas como fallback
            try:
                supa.client.table('lexicon_lemmas').delete().eq('source', 'salida_es_bora_final.json').eq('direction', 'es_bora').execute()
            except:
                pass

    # 1) Lemmas
    lemmas = build_lemmas_es_bora(data)
    
    logger.info(f"💾 Insertando {len(lemmas)} lemmas ES→Bora...")
    # Insertar uno por uno para evitar conflictos de duplicados en el mismo batch
    inserted_count = 0
    skipped_count = 0
    for lemma in lemmas:
        try:
            resp = supa.client.table('lexicon_lemmas').insert(lemma).execute()
            inserted_count += 1
            if inserted_count % 50 == 0:
                logger.info(f"  ✓ {inserted_count}/{len(lemmas)} insertados, {skipped_count} duplicados")
        except Exception as e:
            # Si ya existe, ignorar silenciosamente
            if '23505' in str(e) or 'duplicate key' in str(e).lower():
                skipped_count += 1
            else:
                logger.warning(f"  ⚠️  Error insertando lemma '{lemma.get('lemma')}': {e}")
    
    logger.info(f"  ✅ Total: {inserted_count} insertados, {skipped_count} duplicados")
    
    # Recuperar TODOS los lemmas ES→Bora de la BD para construir el index
    logger.info("📇 Recuperando lemmas ES→Bora de la base de datos...")
    all_lemmas_resp = supa.client.table('lexicon_lemmas').select('*').eq('direction', 'es_bora').execute()
    saved_lemmas = all_lemmas_resp.data or []
    logger.info(f"  ✓ {len(saved_lemmas)} lemmas ES→Bora en total")
    
    # Index lemmas por lemma_es
    lemma_index: Dict[str, int] = {l['lemma']: l['id'] for l in saved_lemmas}
    logger.info(f"📇 Índice de lemmas creado: {len(lemma_index)} entradas")

    # 2) Subentries
    subentries = build_subentries_es_bora(data, lemma_index)
    saved_subentries: List[Dict[str, Any]] = []
    
    if subentries:
        logger.info(f"💾 Insertando {len(subentries)} subentries ES→Bora...")
        for i in range(0, len(subentries), batch_size):
            chunk = subentries[i:i+batch_size]
            try:
                resp = supa.client.table('lexicon_subentries').insert(chunk).execute()
                saved_subentries.extend(resp.data)
                logger.info(f"  ✓ Batch {i//batch_size + 1}: {len(resp.data)} subentries insertados")
            except Exception as e:
                logger.error(f"Error insertando subentries batch {i//batch_size + 1}: {e}")
                return 1
    
    # Index subentries
    sub_idx_by_key: Dict[Tuple[int, str, str], int] = {
        (s['lemma_id'], s.get('sublemma') or '', s.get('gloss_bora') or ''): s['id']
        for s in saved_subentries
    }

    # 3) Examples
    examples = build_examples_es_bora(data, lemma_index, sub_idx_by_key)
    saved_examples: List[Dict[str, Any]] = []
    
    if examples:
        logger.info(f"💾 Insertando {len(examples)} examples ES→Bora...")
        # Insertar uno por uno para manejar duplicados
        inserted_ex = 0
        skipped_ex = 0
        for ex in examples:
            try:
                resp = supa.client.table('lexicon_examples').insert(ex).execute()
                saved_examples.extend(resp.data)
                inserted_ex += 1
                if inserted_ex % 50 == 0:
                    logger.info(f"  ✓ {inserted_ex}/{len(examples)} examples insertados, {skipped_ex} duplicados")
            except Exception as e:
                if '23505' in str(e) or 'duplicate key' in str(e).lower():
                    skipped_ex += 1
                else:
                    logger.error(f"Error insertando example: {e}")
                    return 1
        logger.info(f"  ✅ Total: {inserted_ex} insertados, {skipped_ex} duplicados")

    # 4) Metadata de lemmas para bora_docs
    lemma_meta: Dict[int, Dict[str, Any]] = {l['id']: l for l in saved_lemmas}

    # 5) bora_docs + embeddings
    logger.info("🎯 Generando textos para vectorización...")
    
    all_texts: List[str] = []
    all_records: List[Dict[str, Any]] = []
    
    # LEMMA documents
    texts_l, recs_l = build_bora_docs_texts_es_bora('lemma', saved_lemmas, lemma_meta)
    all_texts.extend(texts_l)
    all_records.extend(recs_l)
    logger.info(f"  ✓ {len(texts_l)} documentos LEMMA_ES")
    
    # SUBENTRY documents
    if saved_subentries:
        texts_s, recs_s = build_bora_docs_texts_es_bora('subentry', saved_subentries, lemma_meta)
        all_texts.extend(texts_s)
        all_records.extend(recs_s)
        logger.info(f"  ✓ {len(texts_s)} documentos SUBLEMMA_ES")
    
    # EXAMPLE documents
    if saved_examples:
        texts_e, recs_e = build_bora_docs_texts_es_bora('example', saved_examples, lemma_meta)
        all_texts.extend(texts_e)
        all_records.extend(recs_e)
        logger.info(f"  ✓ {len(texts_e)} documentos EXAMPLE")
    
    logger.info(f"📊 Total de documentos a vectorizar: {len(all_texts)}")

    # Generar embeddings usando OpenAI (1536 dims, compatible con producción)
    logger.info(f"🤖 Generando embeddings con OpenAI text-embedding-3-small (batches de {embed_batch_size})...")
    embeddings_1536: List[List[float]] = []
    
    for i in range(0, len(all_texts), embed_batch_size):
        chunk = all_texts[i:i+embed_batch_size]
        try:
            # Generar embeddings de 1536 dimensiones (OpenAI default)
            response = openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=chunk
            )
            embs = [item.embedding for item in response.data]
            
            if not embs or len(embs) != len(chunk):
                logger.error(f"Error generando embeddings batch {i//embed_batch_size + 1}")
                return 1
            
            embeddings_1536.extend(embs)
            logger.info(f"  ✓ Batch {i//embed_batch_size + 1}/{(len(all_texts)-1)//embed_batch_size + 1}: {len(embs)} embeddings (1536 dims)")
        except Exception as e:
            logger.error(f"Error en batch {i//embed_batch_size + 1}: {e}")
            return 1
    
    # Agregar embeddings a columna embedding_1536 (compatible con USE_VECTOR_1536=true en producción)
    # IMPORTANTE: Agregar embedding=None para compatibilidad con schema
    for rec, emb_1536 in zip(all_records, embeddings_1536):
        rec['embedding_1536'] = emb_1536
        rec['embedding'] = None  # NULL para columna de 384 dims (no usada en producción)

    # Insertar bora_docs
    logger.info(f"💾 Insertando {len(all_records)} documentos en bora_docs...")
    # Insertar uno por uno para manejar duplicados
    inserted_docs = 0
    skipped_docs = 0
    
    for i, doc in enumerate(all_records, 1):
        try:
            supa.client.table('bora_docs').insert(doc).execute()
            inserted_docs += 1
            if inserted_docs % 100 == 0:
                logger.info(f"  ✓ {inserted_docs}/{len(all_records)} insertados, {skipped_docs} duplicados")
        except Exception as e:
            # Error 409 = duplicado (constraint violation)
            if '409' in str(e) or '23505' in str(e) or 'duplicate key' in str(e).lower():
                skipped_docs += 1
                if skipped_docs % 100 == 0:
                    logger.info(f"  ⏭️  {inserted_docs} insertados, {skipped_docs} duplicados omitidos")
            else:
                logger.error(f"Error insertando bora_docs documento {i}: {e}")
                return 1
    
    logger.info(f"  ✅ Total: {inserted_docs} insertados, {skipped_docs} duplicados")

    logger.info("=" * 80)
    logger.info("✅ INGESTA COMPLETADA")
    logger.info(f"  Lemmas ES→Bora:   {len(saved_lemmas)}")
    logger.info(f"  Subentries:       {len(saved_subentries)}")
    logger.info(f"  Examples:         {len(saved_examples)}")
    logger.info(f"  Docs vectorizados: {inserted_docs} (de {len(all_records)} totales)")
    logger.info("=" * 80)
    
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ingesta de salida_es_bora_final.json (ES→Bora)')
    parser.add_argument('--path', type=str, required=True, help='Ruta al JSON')
    parser.add_argument('--reset', action='store_true', help='Borrar registros ES→Bora previos')
    parser.add_argument('--limit', type=int, default=None, help='Limitar entradas (para testing)')
    parser.add_argument('--batch-size', type=int, default=400, help='Tamaño de batch para inserts')
    parser.add_argument('--embed-batch-size', type=int, default=64, help='Tamaño de batch para embeddings')
    
    args = parser.parse_args()
    exit(main(Path(args.path), args.reset, args.limit, args.batch_size, args.embed_batch_size))
