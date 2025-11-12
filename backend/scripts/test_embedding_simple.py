"""
Test simple de generación de embeddings
Verifica si el adapter está funcionando
"""
import sys
from pathlib import Path

# Agregar backend al path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from adapters.huggingface_adapter import get_huggingface_adapter
from config.settings import settings

print("=" * 80)
print("🔍 TEST SIMPLE DE EMBEDDINGS")
print("=" * 80)

print("\n📋 CONFIGURACIÓN:")
print(f"   USE_EMBEDDING_API: {settings.USE_EMBEDDING_API}")
print(f"   EMBEDDING_API_MODEL: {settings.EMBEDDING_API_MODEL}")
print(f"   OPENAI_API_KEY: {'✅ Configurado' if settings.OPENAI_API_KEY else '❌ No configurado'}")
print(f"   EMBEDDING_MODEL (local): {settings.EMBEDDING_MODEL}")
print(f"   EMBEDDING_DIMENSION: {settings.EMBEDDING_DIMENSION}")

print("\n🔧 INICIALIZANDO ADAPTER...")
try:
    adapter = get_huggingface_adapter()
    print("   ✅ Adapter inicializado")
    print(f"   Tipo: {type(adapter).__name__}")
    print(f"   Tiene _openai_client: {hasattr(adapter, '_openai_client') and adapter._openai_client is not None}")
    print(f"   Tiene embedding_model: {hasattr(adapter, 'embedding_model') and adapter.embedding_model is not None}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n🧪 TEST DE EMBEDDING:")
test_text = "abrazar"
print(f"   Texto: '{test_text}'")

try:
    print("   Generando embedding...")
    embedding = adapter.generate_embedding(test_text)
    
    if embedding:
        print(f"   ✅ Embedding generado")
        print(f"   📏 Longitud: {len(embedding)}")
        print(f"   🔢 Primeros 5 valores: {embedding[:5]}")
        print(f"   📊 Min: {min(embedding):.6f}, Max: {max(embedding):.6f}")
        
        # Verificar no-ceros
        non_zero = sum(1 for x in embedding if abs(x) > 0.0001)
        print(f"   ✓ Valores no-cero: {non_zero}/{len(embedding)} ({non_zero/len(embedding)*100:.1f}%)")
        
        if non_zero == 0:
            print("   ⚠️  PROBLEMA: Todos los valores son cero!")
        
    else:
        print(f"   ❌ Embedding es None")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
