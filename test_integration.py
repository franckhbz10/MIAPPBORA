"""
Test de integración completa: Backend → Microservicio LLM → Respuesta
Prueba el flujo end-to-end del RAG con el microservicio
"""
import httpx
import asyncio
import json
from datetime import datetime

# URLs
BACKEND_URL = "http://localhost:8000"
LLM_SERVICE_URL = "http://localhost:8001"

async def test_backend_health():
    """Test 1: Verificar que el backend está corriendo"""
    print("\n" + "="*70)
    print("🔍 TEST 1: Backend Health Check")
    print("="*70)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACKEND_URL}/health")
            result = response.json()
            print(f"✓ Status: {response.status_code}")
            print(f"✓ App: {result['app']}")
            print(f"✓ Version: {result['version']}")
            return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

async def test_llm_service_health():
    """Test 2: Verificar que el microservicio LLM está corriendo"""
    print("\n" + "="*70)
    print("🤖 TEST 2: Microservicio LLM Health Check")
    print("="*70)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{LLM_SERVICE_URL}/api/llm/health")
            result = response.json()
            print(f"✓ Status: {response.status_code}")
            print(f"✓ State: {result['status']}")
            print(f"✓ Model: {result['model']}")
            print(f"✓ Device: {result['device']}")
            print(f"✓ Embeddings: {result['embedding_model']}")
            return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

async def test_llm_service_direct():
    """Test 3: Llamada directa al microservicio LLM"""
    print("\n" + "="*70)
    print("💬 TEST 3: Generación de texto directo (microservicio)")
    print("="*70)
    
    messages = [
        {"role": "system", "content": "Eres un asistente útil."},
        {"role": "user", "content": "Di 'hola' en una frase corta"}
    ]
    
    print(f"\nMensaje: {messages[1]['content']}")
    print("Generando respuesta... (15-30 segundos)")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            start = datetime.now()
            response = await client.post(
                f"{LLM_SERVICE_URL}/api/llm/generate",
                json={"messages": messages, "max_new_tokens": 50}
            )
            duration = (datetime.now() - start).total_seconds()
            
            result = response.json()
            print(f"\n✓ Status: {response.status_code}")
            print(f"✓ Tiempo: {duration:.2f}s")
            print(f"✓ Tokens generados: {result['tokens_generated']}")
            print(f"✓ Device: {result['device']}")
            print(f"\n📝 Respuesta: {result['answer']}")
            return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

async def test_rag_query():
    """Test 4: Consulta RAG completa (Backend → Microservicio → Respuesta)"""
    print("\n" + "="*70)
    print("🎯 TEST 4: Consulta RAG End-to-End (con microservicio)")
    print("="*70)
    
    # Necesitaremos un token válido para consultar el RAG
    # Por ahora, probemos el endpoint público de lexicon si existe
    
    query = "saludo"
    
    print(f"\nConsulta: '{query}'")
    print("Procesando búsqueda semántica + generación LLM...")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            start = datetime.now()
            
            # Intentar endpoint de búsqueda de lexicon (sin auth)
            response = await client.post(
                f"{BACKEND_URL}/api/game/lexicon/search",
                json={
                    "query": query,
                    "top_k": 5,
                    "min_similarity": 0.6
                }
            )
            
            duration = (datetime.now() - start).total_seconds()
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✓ Status: {response.status_code}")
                print(f"✓ Tiempo: {duration:.2f}s")
                print(f"✓ Resultados encontrados: {len(result.get('results', []))}")
                
                if result.get('results'):
                    print(f"\n📊 Primeros resultados:")
                    for i, item in enumerate(result['results'][:3], 1):
                        print(f"  {i}. {item.get('lemma', 'N/A')} - {item.get('gloss_es', 'N/A')}")
                        print(f"     Similitud: {item.get('similarity', 0):.3f}")
                
                return True
            else:
                print(f"⚠️ Status: {response.status_code}")
                print(f"⚠️ El endpoint requiere autenticación o no está disponible")
                print(f"   Response: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

async def test_mentor_chat():
    """Test 5: Chat con mentor Bora (si está disponible sin auth)"""
    print("\n" + "="*70)
    print("💭 TEST 5: Chat con Mentor Bora (si disponible)")
    print("="*70)
    
    query = "¿Cómo se dice hola en bora?"
    
    print(f"\nPregunta: '{query}'")
    print("Buscando contexto + generando respuesta con microservicio...")
    
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            start = datetime.now()
            
            # Intentar endpoint de mentor/chat
            response = await client.post(
                f"{BACKEND_URL}/api/game/mentor/chat",
                json={"message": query}
            )
            
            duration = (datetime.now() - start).total_seconds()
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✓ Status: {response.status_code}")
                print(f"✓ Tiempo total: {duration:.2f}s")
                print(f"\n🤖 Respuesta del Mentor:")
                print(f"   {result.get('response', 'N/A')}")
                
                if result.get('sources'):
                    print(f"\n📚 Fuentes consultadas: {len(result['sources'])}")
                
                return True
            else:
                print(f"⚠️ Status: {response.status_code}")
                print(f"⚠️ El endpoint requiere autenticación")
                print(f"   Esto es normal - el mentor requiere login")
                return False
                
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

async def main():
    """Ejecutar todos los tests de integración"""
    print("\n" + "🧪"*35)
    print(" "*15 + "TEST DE INTEGRACIÓN COMPLETA")
    print(" "*10 + "Backend ↔ Microservicio LLM ↔ Usuario")
    print("🧪"*35)
    
    results = []
    
    # Test 1: Backend Health
    results.append(("Backend Health", await test_backend_health()))
    
    # Test 2: LLM Service Health
    results.append(("LLM Service Health", await test_llm_service_health()))
    
    # Test 3: LLM Direct Generation
    results.append(("LLM Direct Generation", await test_llm_service_direct()))
    
    # Test 4: RAG Query
    results.append(("RAG Query", await test_rag_query()))
    
    # Test 5: Mentor Chat
    results.append(("Mentor Chat", await test_mentor_chat()))
    
    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN DE TESTS")
    print("="*70)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:12} - {name}")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    
    print("\n" + "="*70)
    print(f"Resultado Final: {passed}/{total} tests pasados ({passed/total*100:.1f}%)")
    print("="*70)
    
    if passed == total:
        print("\n🎉 ¡TODOS LOS TESTS PASARON!")
        print("✅ El microservicio LLM está integrado correctamente")
    elif passed >= 3:
        print("\n✅ Tests críticos pasados")
        print("⚠️ Algunos endpoints requieren autenticación (esperado)")
    else:
        print("\n⚠️ Algunos tests fallaron - revisar configuración")
    
    print()

if __name__ == "__main__":
    asyncio.run(main())
