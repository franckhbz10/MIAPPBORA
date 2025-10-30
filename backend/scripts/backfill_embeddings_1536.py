"""
Backfill embeddings a 1536 dims (OpenAI text-embedding-3-small) en Supabase.

Uso sugerido (PowerShell):

  $env:USE_EMBEDDING_API="true"
  $env:OPENAI_API_KEY="..."
  python backend/scripts/backfill_embeddings_1536.py --target phrases --batch 64 --limit 0
  python backend/scripts/backfill_embeddings_1536.py --target lexicon --batch 64 --limit 0

Notas:
- Requiere haber aplicado la migración SQL para agregar columnas embedding_1536.
- Por defecto procesa todos los registros (limit=0 = sin límite). Usa --limit para pruebas.
- Ajusta el "texto base" para embedding según tu caso.
"""
from __future__ import annotations
import argparse
import math
import sys
from pathlib import Path
from typing import List, Dict, Any

# Añadir backend al path para imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from adapters.huggingface_adapter import get_huggingface_adapter
from adapters.supabase_adapter import get_supabase_adapter


def chunks(lst: List[Any], size: int):
    for i in range(0, len(lst), size):
        yield lst[i:i+size]


def build_phrase_text(row: Dict[str, Any]) -> str:
    # Ajusta al formato que uses para embeddings de frases
    es = row.get('spanish_translation') or row.get('spanish_text') or ''
    bora = row.get('bora_text') or ''
    cat = row.get('category') or ''
    return f"{es} — Bora: {bora} — {cat}".strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', choices=['phrases', 'lexicon', 'bora_docs'], required=True,
                        help='Tabla destino para backfill: frases o lexicón')
    parser.add_argument('--batch', type=int, default=64, help='Tamaño de lote para embeddings')
    parser.add_argument('--limit', type=int, default=0, help='Límite de filas a procesar (0 = todas)')
    args = parser.parse_args()

    # Usar service_role para bypass RLS en escrituras
    from adapters.supabase_adapter import SupabaseAdapter
    supa = SupabaseAdapter(use_service_role=True)
    hf = get_huggingface_adapter()

    if not supa.is_connected():
        raise SystemExit('Supabase no está configurado.')

    total = 0

    if args.target == 'phrases':
        # 1) Obtener frases base
        # Nota: ajusta el select según tus columnas
        res = supa.client.table('bora_phrases').select(
            'id, bora_text, spanish_translation, category, difficulty_level'
        ).execute()
        rows = res.data or []
        if args.limit and args.limit > 0:
            rows = rows[:args.limit]

        # 2) Mapear a (phrase_id, texto)
        payload: List[Dict[str, Any]] = []
        for r in rows:
            payload.append({'phrase_id': r['id'], 'text': build_phrase_text(r)})

        # 3) Batch embeddings -> update phrase_embeddings.embedding_1536
        for part in chunks(payload, args.batch):
            texts = [p['text'] for p in part]
            try:
                vecs = hf.generate_embeddings_batch(texts)
            except Exception as e:
                print(f"Error generando embeddings batch: {e}")
                continue
            if not vecs:
                continue
            for p, vec in zip(part, vecs):
                try:
                    # update por phrase_id (sin upsert conflict, asumimos que ya existe el registro)
                    supa.client.table('phrase_embeddings').update({
                        'embedding_1536': vec,
                    }).eq('phrase_id', p['phrase_id']).execute()
                    total += 1
                    if total % 50 == 0:
                        print(f"  Procesados: {total}")
                except Exception as e:
                    print(f"Error actualizando phrase_id={p['phrase_id']}: {e}")

    elif args.target == 'lexicon':
        # 1) Obtener entradas del lexicón
        # Ajusta columnas reales (bora_text/spanish_text/category) según tu esquema
        res = supa.client.table('lexicon_entries').select(
            'id, bora_text, spanish_text, category'
        ).execute()
        rows = res.data or []
        if args.limit and args.limit > 0:
            rows = rows[:args.limit]

        payload: List[Dict[str, Any]] = []
        for r in rows:
            es = r.get('spanish_text') or ''
            bora = r.get('bora_text') or ''
            cat = r.get('category') or ''
            text = f"{es} — Bora: {bora} — {cat}".strip()
            payload.append({'entry_id': r['id'], 'text': text})

        # 2) Batch embeddings -> update lexicon_embeddings.embedding_1536
        for part in chunks(payload, args.batch):
            texts = [p['text'] for p in part]
            try:
                vecs = hf.generate_embeddings_batch(texts)
            except Exception as e:
                print(f"Error generando embeddings batch: {e}")
                continue
            if not vecs:
                continue
            for p, vec in zip(part, vecs):
                try:
                    supa.client.table('lexicon_embeddings').update({
                        'embedding_1536': vec,
                    }).eq('entry_id', p['entry_id']).execute()
                    total += 1
                    if total % 50 == 0:
                        print(f"  Procesados: {total}")
                except Exception as e:
                    print(f"Error actualizando entry_id={p['entry_id']}: {e}")

    elif args.target == 'bora_docs':
        # 1) Obtener documentos unificados (usaremos content como base de embedding)
        res = supa.client.table('bora_docs').select(
            'id, content'
        ).execute()
        rows = res.data or []
        if args.limit and args.limit > 0:
            rows = rows[:args.limit]

        payload = [{'id': r['id'], 'text': (r.get('content') or '').strip()} for r in rows]

        # 2) Batch embeddings -> update bora_docs.embedding_1536
        for part in chunks(payload, args.batch):
            texts = [p['text'] for p in part]
            try:
                vecs = hf.generate_embeddings_batch(texts)
            except Exception as e:
                print(f"Error generando embeddings batch: {e}")
                continue
            if not vecs:
                continue
            for p, vec in zip(part, vecs):
                try:
                    supa.client.table('bora_docs').update({
                        'embedding_1536': vec,
                    }).eq('id', p['id']).execute()
                    total += 1
                    if total % 100 == 0:
                        print(f"  Procesados: {total}")
                except Exception as e:
                    print(f"Error actualizando bora_docs id={p['id']}: {e}")

    print(f"Backfill completado. Registros procesados: {total}")


if __name__ == '__main__':
    main()
