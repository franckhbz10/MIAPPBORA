# Plan de Trabajo: Implementación del Microservicio LLM

## Objetivo
Separar la funcionalidad LLM del backend principal en un microservicio independiente que:
- Corra en puerto 8001 con su propio venv y versiones actualizadas
- Se comunique con el backend principal (puerto 8000) vía HTTP
- Comparta configuración desde `.env` pero mantenga independencia operacional

---

## Fase 1: Preparación y estructura base (30 min)

### 1.1. Crear estructura del microservicio
```powershell
# Desde raíz del proyecto
New-Item -ItemType Directory -Path llm_service
cd llm_service
New-Item -ItemType Directory -Path config, routers, services
New-Item -ItemType File -Path .env.example
```

**Resultado esperado:**
```
llm_service/
├── config/
├── routers/
├── services/
└── .env.example
```

### 1.2. Crear entorno virtual independiente
```powershell
# Dentro de llm_service/
python -m venv venv_llm
& .\venv_llm\Scripts\Activate.ps1
```

### 1.3. Crear requirements.txt con versiones actualizadas
**Archivo:** `llm_service/requirements.txt`

```txt
# FastAPI core
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0

# LLM y embeddings (versiones actualizadas)
transformers>=4.48.0
accelerate>=0.34.2
torch>=2.2.0
tokenizers>=0.20.3
sentence-transformers==2.2.2

# HuggingFace
huggingface-hub>=0.25.2
safetensors>=0.4.5

# Utilidades
httpx==0.24.1
pydantic==2.5.0
```

### 1.4. Instalar dependencias
```powershell
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

**Checkpoint 1:** Verificar imports
```powershell
python -c "import transformers,torch,accelerate; print('transformers:', transformers.__version__); print('torch:', torch.__version__)"
```

---

## Fase 2: Configuración compartida (20 min)

### 2.1. Crear enlace simbólico al .env del backend
**Estrategia:** Usar el mismo `.env` del backend para compartir configuración

```powershell
# Desde llm_service/
# Windows (requiere permisos de admin) o copiar manualmente:
Copy-Item ..\backend\.env .\.env

# Alternativa: Crear .env propio y referenciar al del backend en código
```

### 2.2. Crear settings.py para el microservicio
**Archivo:** `llm_service/config/settings.py`

```python
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # App config
    app_name: str = "LLM Microservice"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # LLM config (desde .env del backend)
    llm_backend: str = "transformers"
    llm_model: str = "Qwen/Qwen3-1.7B"
    llm_device_map: str = "auto"
    llm_dtype: str = "auto"
    llm_max_new_tokens: int = 256
    llm_temperature: float = 0.35
    llm_top_p: float = 0.9
    llm_enable_thinking: bool = False
    
    # Embeddings config
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    
    # HuggingFace API
    huggingface_api_key: Optional[str] = None
    
    # CORS (permitir conexiones desde backend principal)
    cors_origins: list = ["http://localhost:8000", "http://127.0.0.1:8000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

**Checkpoint 2:** Probar carga de settings
```powershell
python -c "from config.settings import settings; print(f'Modelo: {settings.llm_model}'); print(f'Device: {settings.llm_device_map}')"
```

---

## Fase 3: Implementar servicio LLM (45 min)

### 3.1. Crear el servicio principal
**Archivo:** `llm_service/services/llm_service.py`

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer
import torch
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class LLMService:
    """Servicio para generación de texto y embeddings"""
    
    def __init__(self):
        self.model_name = settings.llm_model
        self.device = self._get_device()
        self.dtype = self._get_dtype()
        
        # Cargar tokenizer y modelo LLM
        logger.info(f"Cargando modelo LLM: {self.model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )
        
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            device_map=settings.llm_device_map,
            torch_dtype=self.dtype
        )
        logger.info(f"✓ Modelo cargado en {self.device}")
        
        # Cargar modelo de embeddings
        logger.info(f"Cargando modelo de embeddings: {settings.embedding_model}")
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        logger.info("✓ Modelo de embeddings cargado")
    
    def _get_device(self):
        """Determinar dispositivo (CPU/GPU)"""
        if settings.llm_device_map == "cpu":
            return "cpu"
        return "cuda" if torch.cuda.is_available() else "cpu"
    
    def _get_dtype(self):
        """Determinar tipo de datos según configuración"""
        if settings.llm_dtype == "float16":
            return torch.float16
        elif settings.llm_dtype == "bfloat16":
            return torch.bfloat16
        elif settings.llm_dtype == "auto":
            return torch.float16 if torch.cuda.is_available() else torch.float32
        return torch.float32
    
    def generate(
        self,
        messages: list[dict],
        max_new_tokens: int = None,
        temperature: float = None,
        top_p: float = None
    ) -> dict:
        """
        Generar respuesta del LLM
        
        Args:
            messages: Lista de mensajes en formato chat (system, user, assistant)
            max_new_tokens: Máximo de tokens a generar
            temperature: Temperatura de sampling
            top_p: Top-p para nucleus sampling
        
        Returns:
            Dict con la respuesta generada y metadatos
        """
        # Usar valores por defecto del settings si no se especifican
        max_new_tokens = max_new_tokens or settings.llm_max_new_tokens
        temperature = temperature or settings.llm_temperature
        top_p = top_p or settings.llm_top_p
        
        try:
            # Aplicar chat template
            prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            # Tokenizar
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            input_length = inputs["input_ids"].shape[1]
            
            # Generar
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decodificar solo los tokens nuevos
            generated_tokens = outputs[0][input_length:]
            answer = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
            
            return {
                "answer": answer.strip(),
                "model": self.model_name,
                "tokens_generated": len(generated_tokens),
                "device": str(self.device)
            }
            
        except Exception as e:
            logger.error(f"Error generando respuesta: {e}")
            raise
    
    def embed(self, texts: list[str]) -> dict:
        """
        Generar embeddings para textos
        
        Args:
            texts: Lista de textos a embedear
        
        Returns:
            Dict con embeddings y metadatos
        """
        try:
            embeddings = self.embedding_model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            return {
                "embeddings": embeddings.tolist(),
                "dim": embeddings.shape[1],
                "count": len(embeddings),
                "model": settings.embedding_model
            }
            
        except Exception as e:
            logger.error(f"Error generando embeddings: {e}")
            raise

# Instancia global (singleton)
_llm_service = None

def get_llm_service() -> LLMService:
    """Obtener instancia única del servicio LLM"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
```

**Checkpoint 3:** Probar carga del servicio
```powershell
python -c "from services.llm_service import get_llm_service; svc = get_llm_service(); print('✓ Servicio LLM cargado')"
```

---

## Fase 4: Crear API REST (30 min)

### 4.1. Crear router con endpoints
**Archivo:** `llm_service/routers/llm_router.py`

```python
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from services.llm_service import get_llm_service
from config.settings import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Schemas de request/response
class Message(BaseModel):
    role: str = Field(..., description="Rol del mensaje: system, user, assistant")
    content: str = Field(..., description="Contenido del mensaje")

class GenerateRequest(BaseModel):
    messages: list[Message] = Field(..., description="Lista de mensajes en formato chat")
    max_new_tokens: int | None = Field(None, description="Máximo de tokens a generar")
    temperature: float | None = Field(None, ge=0.0, le=2.0, description="Temperatura de sampling")
    top_p: float | None = Field(None, ge=0.0, le=1.0, description="Top-p para nucleus sampling")

class GenerateResponse(BaseModel):
    answer: str
    model: str
    tokens_generated: int
    device: str

class EmbedRequest(BaseModel):
    texts: list[str] = Field(..., description="Lista de textos a embedear")

class EmbedResponse(BaseModel):
    embeddings: list[list[float]]
    dim: int
    count: int
    model: str

# Endpoints
@router.post("/generate", response_model=GenerateResponse, summary="Generar respuesta del LLM")
async def generate_text(request: GenerateRequest):
    """
    Genera una respuesta del modelo LLM basado en los mensajes proporcionados.
    
    - **messages**: Lista de mensajes en formato chat [{"role": "user", "content": "..."}]
    - **max_new_tokens**: Límite de tokens a generar (default: desde settings)
    - **temperature**: Controla aleatoriedad (0.0 = determinista, 2.0 = muy aleatorio)
    - **top_p**: Nucleus sampling threshold
    """
    try:
        llm_service = get_llm_service()
        
        # Convertir Pydantic models a dicts
        messages_dict = [{"role": m.role, "content": m.content} for m in request.messages]
        
        result = llm_service.generate(
            messages=messages_dict,
            max_new_tokens=request.max_new_tokens,
            temperature=request.temperature,
            top_p=request.top_p
        )
        
        return GenerateResponse(**result)
        
    except Exception as e:
        logger.error(f"Error en /generate: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando respuesta: {str(e)}"
        )

@router.post("/embed", response_model=EmbedResponse, summary="Generar embeddings")
async def generate_embeddings(request: EmbedRequest):
    """
    Genera embeddings vectoriales para los textos proporcionados.
    
    - **texts**: Lista de strings a convertir en vectores
    
    Retorna embeddings de dimensión 384 (all-MiniLM-L6-v2)
    """
    try:
        if not request.texts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La lista de textos no puede estar vacía"
            )
        
        llm_service = get_llm_service()
        result = llm_service.embed(texts=request.texts)
        
        return EmbedResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en /embed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando embeddings: {str(e)}"
        )

@router.get("/health", summary="Health check del servicio LLM")
async def health_check():
    """Verifica que el servicio LLM esté operativo"""
    try:
        llm_service = get_llm_service()
        return {
            "status": "healthy",
            "model": llm_service.model_name,
            "device": str(llm_service.device),
            "embedding_model": settings.embedding_model
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

### 4.2. Crear aplicación FastAPI principal
**Archivo:** `llm_service/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from routers import llm_router
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Crear aplicación
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Microservicio LLM para generación de texto y embeddings",
    debug=settings.debug
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(llm_router.router, prefix="/api/llm", tags=["LLM"])

# Eventos de startup/shutdown
@app.on_event("startup")
async def startup_event():
    logger.info(f"🤖 {settings.app_name} v{settings.app_version} iniciando...")
    logger.info(f"   Modelo LLM: {settings.llm_model}")
    logger.info(f"   Embeddings: {settings.embedding_model}")
    logger.info(f"   Device map: {settings.llm_device_map}")
    
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Cerrando microservicio LLM...")

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.debug
    )
```

**Checkpoint 4:** Probar arranque del microservicio
```powershell
# Dentro de llm_service/ con venv_llm activado
uvicorn main:app --reload --port 8001
# Visitar: http://localhost:8001/docs
```

---

## Fase 5: Adaptar backend principal (30 min)

### 5.1. Actualizar backend/config/settings.py
Añadir configuración del microservicio LLM:

```python
# Backend principal: backend/config/settings.py
# Añadir al final de la clase Settings:

    # Microservicio LLM
    llm_service_url: str = "http://localhost:8001"
    llm_service_enabled: bool = True  # Flag para activar/desactivar
    llm_service_timeout: int = 60  # Timeout en segundos
```

### 5.2. Crear adaptador HTTP para el microservicio
**Archivo:** `backend/adapters/llm_service_adapter.py` (NUEVO)

```python
import httpx
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class LLMServiceAdapter:
    """Adaptador para comunicarse con el microservicio LLM"""
    
    def __init__(self):
        self.base_url = settings.llm_service_url
        self.timeout = settings.llm_service_timeout
        self.enabled = settings.llm_service_enabled
    
    async def generate(
        self,
        messages: list[dict],
        max_new_tokens: int = None,
        temperature: float = None,
        top_p: float = None
    ) -> str:
        """
        Generar respuesta del LLM vía microservicio
        
        Args:
            messages: Lista de mensajes [{"role": "user", "content": "..."}]
            max_new_tokens: Tokens máximos a generar
            temperature: Temperatura de sampling
            top_p: Top-p sampling
        
        Returns:
            String con la respuesta generada
        """
        if not self.enabled:
            raise Exception("Microservicio LLM deshabilitado en configuración")
        
        url = f"{self.base_url}/api/llm/generate"
        payload = {
            "messages": messages,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_p": top_p
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                return result["answer"]
                
        except httpx.TimeoutException:
            logger.error(f"Timeout llamando a microservicio LLM ({url})")
            raise Exception("Timeout generando respuesta del LLM")
        except httpx.HTTPError as e:
            logger.error(f"Error HTTP llamando a microservicio LLM: {e}")
            raise Exception(f"Error comunicándose con microservicio LLM: {e}")
    
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generar embeddings vía microservicio
        
        Args:
            texts: Lista de textos a embedear
        
        Returns:
            Lista de vectores de embeddings
        """
        if not self.enabled:
            raise Exception("Microservicio LLM deshabilitado en configuración")
        
        url = f"{self.base_url}/api/llm/embed"
        payload = {"texts": texts}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                return result["embeddings"]
                
        except httpx.TimeoutException:
            logger.error(f"Timeout generando embeddings ({url})")
            raise Exception("Timeout generando embeddings")
        except httpx.HTTPError as e:
            logger.error(f"Error HTTP generando embeddings: {e}")
            raise Exception(f"Error generando embeddings: {e}")
    
    async def health_check(self) -> dict:
        """Verificar salud del microservicio LLM"""
        url = f"{self.base_url}/api/llm/health"
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Health check falló: {e}")
            return {"status": "unreachable", "error": str(e)}

# Instancia global
_llm_adapter = None

def get_llm_service_adapter() -> LLMServiceAdapter:
    """Obtener instancia del adaptador"""
    global _llm_adapter
    if _llm_adapter is None:
        _llm_adapter = LLMServiceAdapter()
    return _llm_adapter
```

### 5.3. Actualizar backend/services/rag_service.py
Modificar para usar el microservicio cuando esté disponible:

```python
# backend/services/rag_service.py
# Importar el nuevo adaptador al inicio:
from adapters.llm_service_adapter import get_llm_service_adapter
from adapters.huggingface_adapter import HuggingFaceAdapter  # Fallback
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self, supabase_adapter, huggingface_adapter=None):
        self.supabase = supabase_adapter
        self.hf_adapter = huggingface_adapter or HuggingFaceAdapter()  # Fallback
        self.llm_adapter = get_llm_service_adapter() if settings.llm_service_enabled else None
    
    async def generate_response(self, query: str, context_docs: list):
        """Genera respuesta usando el microservicio LLM o fallback local"""
        messages = self._build_messages(query, context_docs)
        
        # Intentar microservicio primero
        if self.llm_adapter:
            try:
                logger.info("Generando respuesta con microservicio LLM...")
                answer = await self.llm_adapter.generate(
                    messages=messages,
                    max_new_tokens=settings.llm_max_new_tokens,
                    temperature=settings.llm_temperature,
                    top_p=settings.llm_top_p
                )
                return self._post_process_mentor_response(answer)
                
            except Exception as e:
                logger.warning(f"Microservicio LLM falló, usando fallback local: {e}")
                # Continuar con fallback
        
        # Fallback a adaptador local
        logger.info("Generando respuesta con adaptador local...")
        answer = self.hf_adapter.chat_completion(messages)
        return self._post_process_mentor_response(answer)
    
    # ... resto de métodos sin cambios
```

---

## Fase 6: Testing e integración (30 min)

### 6.1. Crear script de prueba
**Archivo:** `llm_service/test_service.py`

```python
"""Script de prueba para el microservicio LLM"""
import httpx
import asyncio

BASE_URL = "http://localhost:8001"

async def test_health():
    print("🔍 Probando health check...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/llm/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")

async def test_generate():
    print("\n🤖 Probando generación de texto...")
    messages = [
        {"role": "system", "content": "Eres un asistente útil."},
        {"role": "user", "content": "¿Qué es Python?"}
    ]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/llm/generate",
            json={"messages": messages, "max_new_tokens": 100}
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Modelo: {result['model']}")
        print(f"   Tokens: {result['tokens_generated']}")
        print(f"   Respuesta: {result['answer'][:200]}...")

async def test_embed():
    print("\n📊 Probando embeddings...")
    texts = ["Hola mundo", "Buenos días"]
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/llm/embed",
            json={"texts": texts}
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Dimensión: {result['dim']}")
        print(f"   Vectores generados: {result['count']}")

async def main():
    print("=" * 60)
    print("TEST DEL MICROSERVICIO LLM")
    print("=" * 60)
    
    try:
        await test_health()
        await test_generate()
        await test_embed()
        print("\n✅ Todas las pruebas pasaron")
    except Exception as e:
        print(f"\n❌ Error en las pruebas: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 6.2. Crear script de inicio combinado
**Archivo:** `start-llm-service.ps1` (raíz)

```powershell
# Script para arrancar el microservicio LLM
Write-Host "🤖 Arrancando microservicio LLM..." -ForegroundColor Green

# Verificar que existe
if (-not (Test-Path "llm_service\main.py")) {
    Write-Host "❌ Error: llm_service/ no encontrado" -ForegroundColor Red
    exit 1
}

# Activar venv y arrancar
cd llm_service
& .\venv_llm\Scripts\Activate.ps1
Write-Host "✓ Venv activado" -ForegroundColor Green

Write-Host "🚀 Iniciando servidor en puerto 8001..." -ForegroundColor Yellow
uvicorn main:app --reload --port 8001
```

### 6.3. Actualizar backend/.env
Añadir configuración del microservicio:

```properties
# ==============================================
# MICROSERVICIO LLM
# ==============================================
LLM_SERVICE_URL=http://localhost:8001
LLM_SERVICE_ENABLED=true
LLM_SERVICE_TIMEOUT=60
```

---

## Fase 7: Deployment y validación final (20 min)

### 7.1. Crear .gitignore para llm_service
**Archivo:** `llm_service/.gitignore`

```
venv_llm/
__pycache__/
*.pyc
.env
*.log
```

### 7.2. Checklist de validación

```
✅ Estructura creada (config/, routers/, services/)
✅ Venv independiente con transformers >= 4.48
✅ Settings.py lee configuración desde .env
✅ LLMService carga modelo correctamente
✅ Router expone /generate y /embed
✅ main.py arranca en puerto 8001
✅ Backend adaptado con LLMServiceAdapter
✅ RAGService usa microservicio con fallback
✅ Tests pasan (health, generate, embed)
✅ start-dev.ps1 actualizado para opción 2
```

### 7.3. Flujo de arranque completo

**Terminal 1: Microservicio LLM**
```powershell
cd llm_service
& .\venv_llm\Scripts\Activate.ps1
uvicorn main:app --reload --port 8001
```

**Terminal 2: Backend principal**
```powershell
cd backend
& .\venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8000
```

**Terminal 3: Frontend**
```powershell
cd frontend
npm run dev
```

**O usar el script automatizado:**
```powershell
.\start-dev.ps1
# Opción 2: Backend + Frontend + LLM
```

---

## Fase 8: Documentación y entrega (15 min)

### 8.1. Crear README del microservicio
**Archivo:** `llm_service/README.md`

```markdown
# Microservicio LLM - MIAPPBORA

Servicio independiente para generación de texto y embeddings.

## Inicio rápido

1. Crear venv:
   ```powershell
   python -m venv venv_llm
   & .\venv_llm\Scripts\Activate.ps1
   ```

2. Instalar dependencias:
   ```powershell
   pip install -r requirements.txt
   ```

3. Configurar .env (copiar desde ../backend/.env)

4. Arrancar servicio:
   ```powershell
   uvicorn main:app --reload --port 8001
   ```

5. Probar endpoints: http://localhost:8001/docs

## Endpoints

- `POST /api/llm/generate` - Generar respuesta
- `POST /api/llm/embed` - Generar embeddings
- `GET /api/llm/health` - Health check

## Variables de entorno

Ver `backend/.env` (compartido):
- `LLM_MODEL` - Modelo a usar (default: Qwen/Qwen3-1.7B)
- `LLM_DEVICE_MAP` - Device mapping (auto/cpu/cuda)
- `LLM_DTYPE` - Tipo de datos (auto/float16/float32)
- `LLM_MAX_NEW_TOKENS` - Tokens máximos (256)
- `LLM_TEMPERATURE` - Temperatura (0.35)
```

### 8.2. Actualizar docs/ORGANIZACION_PROYECTO.md
Marcar como implementado y añadir notas de deployment.

---

## Cronograma estimado

| Fase | Duración | Acumulado |
|------|----------|-----------|
| 1. Preparación y estructura base | 30 min | 0:30 |
| 2. Configuración compartida | 20 min | 0:50 |
| 3. Implementar servicio LLM | 45 min | 1:35 |
| 4. Crear API REST | 30 min | 2:05 |
| 5. Adaptar backend principal | 30 min | 2:35 |
| 6. Testing e integración | 30 min | 3:05 |
| 7. Deployment y validación | 20 min | 3:25 |
| 8. Documentación | 15 min | **3:40** |

**Total estimado: 3-4 horas** (con tiempo para debugging)

---

## Beneficios inmediatos

✅ **Independencia:** Actualizar transformers sin afectar al backend principal  
✅ **Escalabilidad:** Replicar solo el LLM (N instancias en 8001, 8002, ...)  
✅ **Mantenibilidad:** Cambiar modelo sin tocar lógica de negocio  
✅ **Performance:** Backend ligero en CPU, LLM en GPU si disponible  
✅ **Testabilidad:** Probar LLM aisladamente  

---

## Próximos pasos (post-implementación)

1. **Optimización:**
   - Implementar caché de respuestas frecuentes
   - Batch processing para múltiples requests simultáneos
   - Compresión de embeddings

2. **Monitoreo:**
   - Logs estructurados (ELK stack)
   - Métricas de latencia y throughput
   - Alertas de salud del servicio

3. **Producción:**
   - Dockerizar ambos servicios
   - Load balancer para LLM (nginx/traefik)
   - Deploy en cloud (backend en Cloud Run, LLM en VM con GPU)

---

## Rollback plan

Si algo falla durante la implementación:

1. **Parar microservicio LLM**
2. **En backend/.env:**
   ```properties
   LLM_SERVICE_ENABLED=false
   ```
3. **Reiniciar backend:** El RAGService usará automáticamente el adaptador local
4. **Todo sigue funcionando como antes**

No hay cambios destructivos, solo aditivos. El backend mantiene compatibilidad con ambos modos.
