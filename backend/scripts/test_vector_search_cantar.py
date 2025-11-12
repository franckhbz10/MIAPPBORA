"""
Test de búsqueda vectorial REAL con embedding de "cantar"

Este script verifica:
1. Generar embedding de "cantar"
2. Buscar vectorialmente en bora_docs SIN filtros
3. Ver qué resultados trae la búsqueda
"""
import asyncio
import sys
import os
from pathlib import Path

backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv()

from adapters.huggingface_adapter import get_huggingface_adapter
from supabase import create_client


async def main():
    print("=" * 80)
    print("TEST: Búsqueda Vectorial Real de 'cantar'")
    print("=" * 80)
    
    # 1. Generar embedding de "cantar"
    print("\n1️⃣ Generando embedding de 'cantar'...")
    hf = get_huggingface_adapter()
    embedding = hf.generate_embedding("cantar")
    
    if not embedding:
        print("❌ Error: No se pudo generar embedding")
        return
    
    print(f"✅ Embedding generado: {len(embedding)} dimensiones")
    print(f"   Primeros 5 valores: {embedding[:5]}")
    
    # 2. Conectar a Supabase
    print("\n2️⃣ Conectando a Supabase...")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")  # Usar SUPABASE_SERVICE_KEY
    
    if not supabase_url or not supabase_key:
        print("❌ Error: Variables de entorno no configuradas")
        print(f"   SUPABASE_URL: {'✅' if supabase_url else '❌'}")
        print(f"   SUPABASE_SERVICE_KEY: {'✅' if supabase_key else '❌'}")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    print(f"✅ Conectado a Supabase")
    
    # 3. Búsqueda vectorial SIN filtros usando match_bora_docs_v2
    print("\n3️⃣ Búsqueda vectorial con match_bora_docs_v2...")
    print(f"   Parámetros:")
    print(f"   - match_threshold: 0.0 (SIN FILTRO)")
    print(f"   - match_count: 20")
    print(f"   - kind_filter: NULL (todos)")
    print(f"   - pos_filter: NULL")
    
    try:
        result = supabase.rpc('match_bora_docs_v2', {
            'query_embedding': embedding,
            'match_threshold': 0.0,  # ✅ SIN FILTRO para ver TODOS los resultados
            'match_count': 20,
            'kind_filter': None,
            'pos_filter': None,
        }).execute()
        
        docs = result.data or []
        print(f"\n✅ Búsqueda completada: {len(docs)} resultados")
        
        if not docs:
            print("\n❌ ERROR: No se encontraron resultados")
            print("   Esto es extraño porque sabemos que los datos existen")
            return
        
        # 4. Analizar resultados
        print("\n4️⃣ Analizando resultados...")
        print("=" * 80)
        
        found_cantar = False
        
        for i, doc in enumerate(docs, 1):
            lemma = doc.get('lemma', 'N/A')
            kind = doc.get('kind', 'N/A')
            direction = doc.get('direction', 'N/A')
            similarity = doc.get('similarity', 0.0)
            gloss_es = doc.get('gloss_es', 'N/A')
            gloss_bora = doc.get('gloss_bora', 'N/A')
            
            print(f"\n{i}. Lemma: {lemma}")
            print(f"   Kind: {kind}")
            print(f"   Direction: {direction}")
            print(f"   Similarity: {similarity:.4f}")
            print(f"   Gloss ES: {gloss_es}")
            print(f"   Gloss Bora: {gloss_bora}")
            
            # Verificar si es "cantar"
            if lemma.lower() == 'cantar':
                found_cantar = True
                print(f"   🎯 ¡ENCONTRADO 'cantar'!")
                
                if direction == 'es_bora' and gloss_bora and 'majtsí' in gloss_bora.lower():
                    print(f"   ✅ PERFECTO: ES→Bora con traducción 'majtsíva'")
                    print(f"   ✅ Posición: #{i} en el ranking")
        
        # 5. Conclusión
        print("\n" + "=" * 80)
        print("CONCLUSIÓN:")
        print("=" * 80)
        
        if found_cantar:
            print("✅ La búsqueda vectorial SÍ encuentra 'cantar'")
            print("✅ Los datos están correctos")
            print("✅ Los embeddings funcionan")
            print("\n🤔 Si el frontend no lo encuentra, el problema está en:")
            print("   - El preprocesamiento del query")
            print("   - El threshold de similitud")
            print("   - O la forma en que el frontend llama al backend")
        else:
            print("❌ La búsqueda vectorial NO encontró 'cantar' en top 20")
            print("❌ Posibles causas:")
            print("   1. El embedding de 'cantar' no es similar al documento")
            print("   2. El threshold (0.5) es muy alto")
            print("   3. Hay un problema con los embeddings en la BD")
        
    except Exception as e:
        print(f"\n❌ Error en búsqueda: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
