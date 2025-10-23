"""
Script para listar modelos disponibles desde la API de OpenAI
Usa OPENAI_API_KEY y opcionalmente OPENAI_BASE_URL/OPENAI_ORG del .env
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from adapters.openai_adapter import get_openai_adapter
from config.settings import settings


async def main():
    print("=== Listando modelos de OpenAI ===")
    print(f"Base URL: {settings.OPENAI_BASE_URL or 'default'}")
    print(f"Organization: {settings.OPENAI_ORG or 'default'}")
    
    adapter = get_openai_adapter()
    try:
        result = await adapter.list_models()
        print(f"Total modelos: {result['count']}")
        # Mostrar solo los primeros 30 para no saturar
        for mid in result["models"][:30]:
            print(" -", mid)
        if result['count'] > 30:
            print(f"... y {result['count'] - 30} más")
    except Exception as e:
        print("Error listando modelos:", e)


if __name__ == "__main__":
    asyncio.run(main())
