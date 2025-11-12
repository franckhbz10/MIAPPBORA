"""
Script de análisis exploratorio para salida_es_bora_final.json

Objetivo: Generar estadísticas detalladas del diccionario ES→Bora
para diseñar estrategia de ingesta óptima.

Uso:
    python backend/scripts/analyze_es_bora_json.py ../salida_es_bora_final.json
"""

import json
import sys
from pathlib import Path
from collections import Counter
from typing import Dict, List, Any

def analyze_json(file_path: Path) -> Dict[str, Any]:
    """Analiza estructura y contenido del JSON ES→Bora"""
    
    print(f"📄 Cargando {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ JSON cargado: {len(data)} entradas\n")
    
    stats = {
        'total_entries': len(data),
        'unique_lemmas': set(),
        'pos_distribution': Counter(),
        'subentries_count': 0,
        'examples_count': 0,
        'gloss_bora_splits': Counter(),  # Cuántas traducciones por lemma
        'empty_fields': {
            'variants': 0,
            'synonyms': 0,
            'gloss_bora': 0,
        },
        'subentries_with_examples': 0,
        'examples_missing_bora_or_es': 0,
    }
    
    for entry in data:
        # Lemmas únicos
        lemma = entry.get('lemma')
        if lemma:
            stats['unique_lemmas'].add(lemma)
        
        # POS distribution
        pos_full = entry.get('pos_full', 'unknown')
        stats['pos_distribution'][pos_full] += 1
        
        # gloss_bora analysis (múltiples traducciones)
        gloss_bora = entry.get('gloss_bora', '')
        if not gloss_bora:
            stats['empty_fields']['gloss_bora'] += 1
        else:
            # Contar cuántas traducciones (split por ";")
            translations = [t.strip() for t in gloss_bora.split(';') if t.strip()]
            stats['gloss_bora_splits'][len(translations)] += 1
        
        # Variants & Synonyms
        if not entry.get('variants'):
            stats['empty_fields']['variants'] += 1
        if not entry.get('synonyms'):
            stats['empty_fields']['synonyms'] += 1
        
        # Subentries
        subentries = entry.get('subentries', [])
        stats['subentries_count'] += len(subentries)
        
        for sub in subentries:
            # Examples en subentries
            sub_examples = sub.get('examples', [])
            if sub_examples:
                stats['subentries_with_examples'] += 1
            
            for ex in sub_examples:
                stats['examples_count'] += 1
                # Validar que tengan ambos campos
                if not ex.get('bora') or not ex.get('es'):
                    stats['examples_missing_bora_or_es'] += 1
        
        # Examples al nivel de entry principal
        main_examples = entry.get('examples', [])
        for ex in main_examples:
            stats['examples_count'] += 1
            if not ex.get('bora') or not ex.get('es'):
                stats['examples_missing_bora_or_es'] += 1
    
    stats['unique_lemmas'] = len(stats['unique_lemmas'])
    return stats


def print_report(stats: Dict[str, Any]):
    """Imprime reporte detallado de estadísticas"""
    
    print("=" * 80)
    print("📊 ANÁLISIS DE salida_es_bora_final.json (Diccionario ES→Bora)")
    print("=" * 80)
    print()
    
    print("📌 RESUMEN GENERAL")
    print(f"  Total de entradas:       {stats['total_entries']:,}")
    print(f"  Lemmas únicos (español): {stats['unique_lemmas']:,}")
    print(f"  Subentradas:             {stats['subentries_count']:,}")
    print(f"  Ejemplos totales:        {stats['examples_count']:,}")
    print()
    
    print("🔤 DISTRIBUCIÓN POR CATEGORÍA GRAMATICAL (Top 10)")
    for pos, count in stats['pos_distribution'].most_common(10):
        pct = (count / stats['total_entries']) * 100
        print(f"  {pos:30s} {count:6,} ({pct:5.1f}%)")
    print()
    
    print("🔀 MÚLTIPLES TRADUCCIONES EN gloss_bora")
    print("  (Distribución de cuántas traducciones tiene cada lemma)")
    for num_translations in sorted(stats['gloss_bora_splits'].keys()):
        count = stats['gloss_bora_splits'][num_translations]
        pct = (count / stats['total_entries']) * 100
        print(f"  {num_translations} traducción(es): {count:6,} lemmas ({pct:5.1f}%)")
    
    # Calcular documentos estimados por split
    total_docs_from_splits = sum(
        num * count for num, count in stats['gloss_bora_splits'].items()
    )
    print(f"\n  📊 Estimado de documentos LEMMA tras split: ~{total_docs_from_splits:,}")
    print()
    
    print("⚠️ CAMPOS VACÍOS")
    print(f"  gloss_bora vacío:  {stats['empty_fields']['gloss_bora']:,}")
    print(f"  variants vacío:    {stats['empty_fields']['variants']:,}")
    print(f"  synonyms vacío:    {stats['empty_fields']['synonyms']:,}")
    print()
    
    print("📝 EJEMPLOS")
    print(f"  Total de ejemplos:                 {stats['examples_count']:,}")
    print(f"  Subentradas con ejemplos:          {stats['subentries_with_examples']:,}")
    print(f"  Ejemplos incompletos (falta campo): {stats['examples_missing_bora_or_es']:,}")
    print()
    
    print("🎯 ESTIMACIÓN DE DOCUMENTOS VECTORIZADOS")
    docs_lemma = total_docs_from_splits
    docs_subentry = stats['subentries_count']
    docs_example = stats['examples_count'] - stats['examples_missing_bora_or_es']
    total_docs = docs_lemma + docs_subentry + docs_example
    
    print(f"  LEMMA (tras split):      ~{docs_lemma:,}")
    print(f"  SUBENTRY:                ~{docs_subentry:,}")
    print(f"  EXAMPLE (válidos):       ~{docs_example:,}")
    print(f"  {'─' * 40}")
    print(f"  TOTAL ESTIMADO:          ~{total_docs:,}")
    print()
    
    print("💰 COSTOS ESTIMADOS (OpenAI text-embedding-3-small)")
    cost_per_1k = 0.00002 * 1000  # $0.02 per 1M tokens, ~1 token/embedding
    total_cost = (total_docs / 1000) * cost_per_1k
    print(f"  Embeddings a generar: ~{total_docs:,}")
    print(f"  Costo estimado:       ${total_cost:.2f} USD")
    print()
    
    print("⏱️ TIEMPO ESTIMADO")
    batches = total_docs / 64  # OpenAI batch size
    time_minutes = (batches * 2) / 60  # ~2s por batch
    print(f"  Batches (64/batch):   ~{int(batches):,}")
    print(f"  Tiempo estimado:      ~{int(time_minutes)} minutos")
    print()
    
    print("=" * 80)
    print("✅ Análisis completado")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python analyze_es_bora_json.py <ruta_al_json>")
        print("Ejemplo: python analyze_es_bora_json.py ../salida_es_bora_final.json")
        sys.exit(1)
    
    json_path = Path(sys.argv[1])
    
    if not json_path.exists():
        print(f"❌ Error: Archivo no encontrado: {json_path}")
        sys.exit(1)
    
    stats = analyze_json(json_path)
    print_report(stats)
