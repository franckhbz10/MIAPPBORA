"""
Ingesta de salida.json (Diccionario Bora→Español) al esquema bidireccional.

LIMPIEZA Y VALIDACIÓN:
- Valida y limpia datos malformados (texto truncado, "None" strings, etc.)
- Elimina datos históricos corruptos con --reset
- Genera embeddings OpenAI 1536 dims directamente (sin embedding de 384 dims)
- Metadata completa con direction='bora_es'

Diferencias vs ingest_es_bora_docs.py:
1. gloss_es en vez de gloss_bora
2. direction='bora_es'
3. Formato de documentos: [LEMMA] en vez de [LEMMA_ES]
4. VALIDACIÓN EXTRA: limpia datos corruptos del diccionario original

Uso típico:
  # Test con 100 entradas
  python backend/scripts/ingest_bora_es_docs.py --path salida.json --limit 100 --reset
  
  # Ingesta completa (limpia datos viejos corruptos)
  python backend/scripts/ingest_bora_es_docs.py --path salida.json --batch-size 50 --embed-batch-size 64 --reset

Requisitos:
  - .env con SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY
  - Schema bidireccional aplicado (001_bidirectional_schema.sql)
  - USE_EMBEDDING_API=true, USE_VECTOR_1536=true
"""
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import logging
import sys
import os
import re

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Cargar variables de entorno
try:
    from dotenv import load_dotenv
    env_path = BACKEND_ROOT / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
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


def clean_text(text: str) -> Optional[str]:
    """
    Limpia y valida texto, eliminando datos corruptos.
    
    Retorna None si el texto está corrupto o es inválido.
    """
    if not text:
        return None
    
    text = text.strip()
    
    # Rechazar strings que son literalmente "None" o "null"
    if text.lower() in ('none', 'null', 'n/a'):
        return None
    
    # Rechazar textos muy cortos que parecen truncados
    if len(text) < 2:
        return None
    
    # Rechazar si contiene muchos caracteres raros consecutivos
    if re.search(r'[^\w\s\-áéíóúÁÉÍÓÚñÑüÜɨʉ]{5,}', text):
        logger.warning(f"⚠️ Texto con caracteres raros rechazado: '{text[:50]}...'")
        return None
    
    # Advertir si parece truncado (termina con paréntesis abierto, punto suspensivo, etc.)
    if re.search(r'\($|\.\.\.$|…$', text):
        logger.warning(f"⚠️ Texto parece truncado: '{text}'")
        # Aún así lo permitimos, pero advertimos
    
    return text


def validate_lemma(lemma: str, gloss_es: str) -> bool:
    """
    Valida que un lemma sea válido y no esté corrupto.
    
    Retorna False si debe ser rechazado.
    """
    clean_lemma = clean_text(lemma)
    clean_gloss = clean_text(gloss_es)
    
    if not clean_lemma or not clean_gloss:
        logger.warning(f"❌ Lemma rechazado: lemma='{lemma}' gloss_es='{gloss_es}'")
        return False
    
    # Rechazar lemmas que parecen corruptos (ej: "fermedad que no nos respeta). ('")
    if ')' in clean_lemma or '(' in clean_lemma[-3:]:
        logger.warning(f"❌ Lemma corrupto rechazado: '{lemma}'")
        return False
    
    return True


def parse_json(path: Path, limit: Optional[int]) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(limit, int) and limit > 0:
        data = data[:limit]
    return data


def build_lemmas_bora_es(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Construye lemmas desde salida.json (Bora→ES)
    
    CON VALIDACIÓN Y LIMPIEZA:
    - Elimina datos corruptos
    - Valida gloss_es no sea "None" string
    - direction='bora_es'
    """
    out: List[Dict[str, Any]] = []
    seen: set[Tuple[str, str, str]] = set()
    rejected_count = 0
    
    for e in data:
        lemma_bora = e.get('lemma')  # Palabra en Bora
        gloss_es = e.get('gloss_es', '')  # Traducción al español
        
        if not lemma_bora or not gloss_es:
            rejected_count += 1
            continue
        
        # VALIDACIÓN: rechazar datos corruptos
        if not validate_lemma(lemma_bora, gloss_es):
            rejected_count += 1
            continue
        
        # Limpiar textos
        lemma_bora = clean_text(lemma_bora)
        gloss_es = clean_text(gloss_es)
        
        if not lemma_bora or not gloss_es:
            rejected_count += 1
            continue
        
        pos = e.get('pos', '')
        pos_full = e.get('pos_full', '')
        page = e.get('page')
        
        # Evitar duplicados exactos
        key = (lemma_bora, pos, gloss_es)
        if key in seen:
            continue
        seen.add(key)
        
        out.append({
            'lemma': lemma_bora,
            'pos': pos,
            'pos_full': pos_full,
            'gloss_es': gloss_es,
            'gloss_bora': None,  # NULL para Bora→ES
            'direction': 'bora_es',
            'page': page,
        })
    
    if rejected_count > 0:
        logger.info(f"ℹ️ {rejected_count} lemmas rechazados por datos corruptos/inválidos")
    
    logger.info(f"📝 Lemmas Bora→ES construidos: {len(out)} (desde {len(data)} entradas)")
    return out


def build_subentries_bora_es(data: List[Dict[str, Any]], lemma_id_map: Dict[Tuple[str, str, str], int]) -> List[Dict[str, Any]]:
    """Construye subentradas desde salida.json"""
    out: List[Dict[str, Any]] = []
    
    for e in data:
        lemma_bora = e.get('lemma')
        if not lemma_bora:
            continue
        
        lemma_bora = clean_text(lemma_bora)
        if not lemma_bora:
            continue
        
        pos = e.get('pos', '')
        gloss_es = e.get('gloss_es', '')
        
        # Buscar lemma_id
        key = (lemma_bora, pos, gloss_es)
        parent_id = lemma_id_map.get(key)
        if not parent_id:
            continue
        
        for sub in e.get('subentries', []):
            sub_lemma = clean_text(sub.get('lemma', ''))
            sub_gloss = clean_text(sub.get('gloss_es', ''))
            
            if not sub_lemma or not sub_gloss:
                continue
            
            out.append({
                'lemma_id': parent_id,
                'sublemma': sub_lemma,  # ✅ Correcto: sublemma, no lemma
                'pos': sub.get('pos', ''),
                'pos_full': sub.get('pos_full', ''),
                'gloss_es': sub_gloss,
                'gloss_bora': None,
                'page': sub.get('page'),
            })
    
    logger.info(f"📝 Subentradas Bora→ES construidas: {len(out)}")
    return out


def build_examples_bora_es(data: List[Dict[str, Any]], lemma_id_map: Dict[Tuple[str, str, str], int]) -> List[Dict[str, Any]]:
    """Construye ejemplos desde salida.json"""
    out: List[Dict[str, Any]] = []
    
    for e in data:
        lemma_bora = clean_text(e.get('lemma'))
        if not lemma_bora:
            continue
        
        pos = e.get('pos', '')
        gloss_es = e.get('gloss_es', '')
        
        key = (lemma_bora, pos, gloss_es)
        parent_id = lemma_id_map.get(key)
        if not parent_id:
            continue
        
        # Ejemplos directos del lemma
        for ex in e.get('examples', []):
            bora = clean_text(ex.get('bora', ''))
            es = clean_text(ex.get('es', ''))
            
            if bora and es:
                out.append({
                    'lemma_id': parent_id,
                    'subentry_id': None,
                    'bora_text': bora,
                    'spanish_text': es,
                    'page': ex.get('page'),
                })
        
        # Ejemplos de subentradas
        for sub in e.get('subentries', []):
            for ex in sub.get('examples', []):
                bora = clean_text(ex.get('bora', ''))
                es = clean_text(ex.get('es', ''))
                
                if bora and es:
                    out.append({
                        'lemma_id': parent_id,
                        'subentry_id': None,
                        'bora_text': bora,
                        'spanish_text': es,
                        'page': ex.get('page'),
                    })
    
    logger.info(f"📝 Ejemplos Bora→ES construidos: {len(out)}")
    return out


def build_bora_docs_bora_es(
    lemmas: List[Dict],
    subentries: List[Dict],
    examples: List[Dict],
    lemma_id_map: Dict,
    subentry_id_map: Dict,
) -> List[Dict[str, Any]]:
    """
    Construye documentos para bora_docs (Bora→ES)
    
    Formato: [LEMMA] gloss_es. POS: pos_full | Source: salida.json
    """
    docs: List[Dict[str, Any]] = []
    
    # Documentos de lemmas
    for lem in lemmas:
        lemma_bora = lem['lemma']
        gloss_es = lem.get('gloss_es', '')
        pos_full = lem.get('pos_full', '')
        
        content = f"[{lemma_bora}] {gloss_es}"
        if pos_full:
            content += f". POS: {pos_full}"
        content += f" | Source: salida.json"
        
        key = (lemma_bora, lem.get('pos', ''), gloss_es)
        parent_id = lemma_id_map.get(key)
        
        if parent_id:
            docs.append({
                'kind': 'lemma',
                'parent_lemma_id': parent_id,
                'subentry_id': None,
                'example_id': None,
                'content': content,
                'metadata': {
                    'direction': 'bora_es',
                    'source': 'salida.json',
                    'page': lem.get('page'),
                },
            })
    
    # Documentos de subentradas
    for sub in subentries:
        sub_lemma = sub['sublemma']  # ✅ Correcto: sublemma
        sub_gloss = sub.get('gloss_es', '')
        pos_full = sub.get('pos_full', '')
        
        content = f"[{sub_lemma}] {sub_gloss}"
        if pos_full:
            content += f". POS: {pos_full}"
        content += f" | Source: salida.json (subentry)"
        
        sub_id = subentry_id_map.get(sub.get('id'))
        parent_id = sub.get('lemma_id')
        
        if sub_id and parent_id:
            docs.append({
                'kind': 'subentry',
                'parent_lemma_id': parent_id,
                'subentry_id': sub_id,
                'example_id': None,
                'content': content,
                'metadata': {
                    'direction': 'bora_es',
                    'source': 'salida.json',
                    'page': sub.get('page'),
                },
            })
    
    # Documentos de ejemplos
    for ex in examples:
        bora = ex.get('bora_text', '')
        es = ex.get('spanish_text', '')
        
        content = f"BORA: {bora} | ES: {es} | Source: salida.json (example)"
        
        ex_id = ex.get('id')
        parent_id = ex.get('lemma_id')
        
        if ex_id and parent_id:
            docs.append({
                'kind': 'example',
                'parent_lemma_id': parent_id,
                'subentry_id': ex.get('subentry_id'),
                'example_id': ex_id,
                'content': content,
                'metadata': {
                    'direction': 'bora_es',
                    'source': 'salida.json',
                    'page': ex.get('page'),
                },
            })
    
    logger.info(f"📝 Documentos bora_docs construidos: {len(docs)} (lemmas: {len(lemmas)}, subentries: {len(subentries)}, examples: {len(examples)})")
    return docs


def chunks(lst: List, n: int):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


@awaitable
async def main():
    parser = argparse.ArgumentParser(description='Ingesta Bora→ES con limpieza de datos corruptos')
    parser.add_argument('--path', type=str, default='salida.json', help='Ruta a salida.json')
    parser.add_argument('--limit', type=int, default=None, help='Límite de entradas para test')
    parser.add_argument('--batch-size', type=int, default=50, help='Tamaño de batch para inserts')
    parser.add_argument('--embed-batch-size', type=int, default=64, help='Batch para embeddings OpenAI')
    parser.add_argument('--reset', action='store_true', help='Eliminar datos Bora→ES previos')
    args = parser.parse_args()
    
    path = Path(args.path)
    if not path.exists():
        logger.error(f"❌ Archivo no encontrado: {path}")
        return
    
    # Verificar OpenAI API Key
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        logger.error("❌ OPENAI_API_KEY no configurada")
        return
    
    logger.info(f"📄 Cargando JSON Bora→ES: {path}")
    data = parse_json(path, args.limit)
    logger.info(f"🔎 Entradas en JSON: {len(data)}")
    
    # Inicializar OpenAI
    openai_client = OpenAI(api_key=openai_key)
    logger.info("✅ Cliente OpenAI inicializado (text-embedding-3-small, 1536 dims)")
    
    # Conectar Supabase con SERVICE_ROLE para bypass RLS
    supabase = SupabaseAdapter(use_service_role=True)
    if not supabase.is_connected():
        logger.error("❌ No se pudo conectar a Supabase")
        return
    
    # Reset opcional (eliminar datos Bora→ES viejos corruptos)
    if args.reset:
        logger.info("🧹 Ejecutando reset (eliminando registros Bora→ES previos)...")
        try:
            # 1. Eliminar bora_docs con direction='bora_es'
            res1 = supabase.client.table('bora_docs').delete().eq('metadata->>direction', 'bora_es').execute()
            logger.info(f"  ✓ bora_docs eliminados: {len(res1.data) if res1.data else 0}")
            
            # 2. Eliminar bora_docs con source='salida.json' (datos viejos sin direction)
            res2 = supabase.client.table('bora_docs').delete().eq('metadata->>source', 'salida.json').execute()
            logger.info(f"  ✓ bora_docs (salida.json) eliminados: {len(res2.data) if res2.data else 0}")
            
            # 3. Obtener IDs de lemmas Bora→ES
            res_lemmas = supabase.client.table('lexicon_lemmas').select('id').eq('direction', 'bora_es').execute()
            lemma_ids = [row['id'] for row in (res_lemmas.data or [])]
            
            if lemma_ids:
                # 4. Eliminar ejemplos de esos lemmas
                supabase.client.table('lexicon_examples').delete().in_('lemma_id', lemma_ids).execute()
                logger.info(f"  ✓ lexicon_examples eliminados para {len(lemma_ids)} lemmas")
                
                # 5. Eliminar subentradas de esos lemmas
                supabase.client.table('lexicon_subentries').delete().in_('lemma_id', lemma_ids).execute()
                logger.info(f"  ✓ lexicon_subentries eliminados")
                
                # 6. Eliminar los lemmas
                supabase.client.table('lexicon_lemmas').delete().eq('direction', 'bora_es').execute()
                logger.info(f"  ✓ lexicon_lemmas eliminados: {len(lemma_ids)}")
            
            logger.info("✅ Reset completado")
        except Exception as e:
            logger.warning(f"⚠️ Reset parcial o error: {e}")
    
    # 1. Construir lemmas
    lemmas = build_lemmas_bora_es(data)
    logger.info(f"📝 Lemmas Bora→ES construidos: {len(lemmas)} (desde {len(data)} entradas)")
    
    # 2. Insertar lemmas
    logger.info(f"💾 Insertando {len(lemmas)} lemmas Bora→ES...")
    lemma_id_map: Dict[Tuple[str, str, str], int] = {}
    inserted = 0
    duplicates = 0
    
    for batch in chunks(lemmas, args.batch_size):
        try:
            res = supabase.client.table('lexicon_lemmas').insert(batch).execute()
            for row in res.data:
                key = (row['lemma'], row.get('pos', ''), row.get('gloss_es', ''))
                lemma_id_map[key] = row['id']
            inserted += len(batch)
            logger.info(f"  ✓ {inserted}/{len(lemmas)} insertados, {duplicates} duplicados")
        except Exception as e:
            if '23505' in str(e) or 'duplicate' in str(e).lower():
                duplicates += len(batch)
                logger.warning(f"  ⚠️ Batch duplicado ({len(batch)} lemmas)")
            else:
                logger.error(f"  ❌ Error insertando lemmas: {e}")
                raise
    
    logger.info(f"✅ Lemmas insertados: {inserted}, duplicados: {duplicates}")
    
    # 3. Construir e insertar subentradas
    subentries = build_subentries_bora_es(data, lemma_id_map)
    subentry_id_map: Dict[int, int] = {}
    
    if subentries:
        logger.info(f"💾 Insertando {len(subentries)} subentradas...")
        for batch in chunks(subentries, args.batch_size):
            try:
                res = supabase.client.table('lexicon_subentries').insert(batch).execute()
                for row in res.data:
                    subentry_id_map[row['id']] = row['id']
            except Exception as e:
                logger.error(f"  ❌ Error insertando subentradas: {e}")
    
    # 4. Construir e insertar ejemplos
    examples = build_examples_bora_es(data, lemma_id_map)
    
    if examples:
        logger.info(f"💾 Insertando {len(examples)} ejemplos...")
        for batch in chunks(examples, args.batch_size):
            try:
                res = supabase.client.table('lexicon_examples').insert(batch).execute()
                for i, row in enumerate(res.data):
                    examples[i]['id'] = row['id']
            except Exception as e:
                logger.error(f"  ❌ Error insertando ejemplos: {e}")
    
    # 5. Construir documentos bora_docs
    all_docs = build_bora_docs_bora_es(lemmas, subentries, examples, lemma_id_map, subentry_id_map)
    
    # 6. Generar embeddings con OpenAI
    logger.info(f"🔮 Generando embeddings OpenAI (1536 dims) para {len(all_docs)} documentos...")
    all_texts = [doc['content'] for doc in all_docs]
    embeddings_1536 = []
    
    for i, batch in enumerate(chunks(all_texts, args.embed_batch_size), 1):
        try:
            response = openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=batch,
                dimensions=1536,
            )
            batch_embeddings = [item.embedding for item in response.data]
            embeddings_1536.extend(batch_embeddings)
            logger.info(f"  ✓ Batch {i}/{(len(all_texts) + args.embed_batch_size - 1) // args.embed_batch_size}: {len(batch_embeddings)} embeddings (1536 dims)")
        except Exception as e:
            logger.error(f"  ❌ Error generando embeddings: {e}")
            raise
    
    # 7. Agregar embeddings a documentos
    for doc, emb_1536 in zip(all_docs, embeddings_1536):
        doc['embedding_1536'] = emb_1536
        doc['embedding'] = None  # NULL para columna de 384 dims
    
    # 8. Insertar documentos en bora_docs
    logger.info(f"💾 Insertando {len(all_docs)} documentos en bora_docs...")
    inserted_docs = 0
    
    for i, batch in enumerate(chunks(all_docs, args.batch_size), 1):
        try:
            res = supabase.client.table('bora_docs').insert(batch).execute()
            inserted_docs += len(batch)
            logger.info(f"  ✓ Batch {i}/{(len(all_docs) + args.batch_size - 1) // args.batch_size}: {len(batch)} docs insertados")
        except Exception as e:
            logger.error(f"  ❌ Error insertando bora_docs: {e}")
            raise
    
    # Resumen final
    logger.info("=" * 80)
    logger.info("✅ INGESTA COMPLETADA")
    logger.info(f"  Lemmas Bora→ES:   {len(lemmas)}")
    logger.info(f"  Subentries:       {len(subentries)}")
    logger.info(f"  Examples:         {len(examples)}")
    logger.info(f"  Docs vectorizados: {len(all_docs)}")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
