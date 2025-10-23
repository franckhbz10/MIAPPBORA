# Plan B: Microservicio LLM Independiente

## Problema identificado

La actualización de `transformers` >= 4.48.0 requiere `torch` >= 2.2.0, lo cual genera conflictos en cascada:
- **tokenizers 0.22.1** tiene incompatibilidades con módulos del sistema
- **torch 2.9.0** rompe compatibilidad con `torchvision` y otras librerías del backend
- **packaging 25.0** es incompatible con `langchain-core < 0.2`
- **Windows + OneDrive + archivos .pyd** generan locks frecuentes al actualizar

## Solución: Microservicio LLM aislado

Separar el LLM en su propio servicio FastAPI con entorno virtual independiente, comunicándose por HTTP con el backend principal.

---

## Arquitectura propuesta

```
miappbora/
├── backend/                        # Backend principal (actual)
│   ├── venv/                       # Python 3.10 + transformers 4.45.2 + torch 2.1.0
│   ├── main.py                     # Puerto 8000
│   ├── routers/
│   ├── services/
│   │   └── rag_service.py          # Llama a llm_service vía HTTP
│   └── requirements.txt            # Sin transformers/torch pesados
│
├── llm_service/                    # Microservicio LLM (nuevo) ⭐
│   ├── venv_llm/                   # Python 3.10+ con transformers >= 4.48, torch >= 2.2
│   ├── main.py                     # Puerto 8001
│   ├── config/
│   │   └── settings.py             # LLM_MODEL, device_map, etc.
│   ├── routers/
│   │   └── llm_router.py           # POST /generate, POST /embed
│   ├── services/
│   │   └── llm_service.py          # Carga modelo, generate, embeddings
│   └── requirements.txt            # transformers, accelerate, torch, sentence-transformers
│
├── frontend/
└── docs/
```

**Nota:** El microservicio se ubica en la **raíz del proyecto** (mismo nivel que `backend/`) para mantener independencia total. Ver `docs/ORGANIZACION_PROYECTO.md` para justificación detallada.

---

## Endpoints del microservicio LLM

### `POST /api/llm/generate`

Genera respuestas del modelo LLM (Qwen3).

**Request:**
```json
{
  "messages": [
    {"role": "system", "content": "Eres Mentor Bora..."},
    {"role": "user", "content": "¿Qué significa 'ímihí'?"}
  ],
  "max_new_tokens": 250,
  "temperature": 0.5,
  "top_p": 0.9
}
```

**Response:**
```json
{
  "answer": "...",
  "model": "Qwen/Qwen3-1.7B",
  "tokens_generated": 120
}
```

### `POST /api/llm/embed`

Genera embeddings para texto o lista de textos.

**Request:**
```json
{
  "texts": ["hola", "adiós"],
  "model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

**Response:**
```json
{
  "embeddings": [[0.123, -0.456, ...], [...]],
  "dim": 384,
  "model": "all-MiniLM-L6-v2"
}
```

---

## Flujo de llamada desde backend principal

```python
# backend/services/rag_service.py

import httpx

LLM_SERVICE_URL = "http://localhost:8001"

async def generate_response(self, query: str, context_docs: list):
    messages = self._build_messages(query, context_docs)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{LLM_SERVICE_URL}/api/llm/generate",
            json={
                "messages": messages,
                "max_new_tokens": 250,
                "temperature": 0.5,
                "top_p": 0.9
            },
            timeout=60.0
        )
        response.raise_for_status()
        result = response.json()
        return result["answer"]
```

---

## Ventajas

1. **Independencia de versiones:**
   - `backend_llm/venv_llm/` puede tener `transformers>=4.48`, `torch>=2.2`, etc.
   - `backend/venv/` mantiene versiones estables sin conflictos con LangChain/Supabase

2. **Escalabilidad:**
   - El LLM se puede escalar horizontalmente (N réplicas en puertos distintos con load balancer)
   - Se puede deployar en máquina con GPU mientras el backend principal queda en CPU

3. **Facilidad de actualización:**
   - Actualizar `transformers` o cambiar modelo solo afecta al microservicio LLM
   - No hay locks de archivos compartidos entre ambos venvs

4. **Resiliencia:**
   - Si el LLM crashea, el backend principal sigue funcionando (puede retornar fallback)
   - Fácil de reiniciar/reemplazar el microservicio sin tocar el backend principal

---

## Desventajas

1. **Latencia adicional:**
   - Overhead HTTP ~5-20ms por request (vs llamada local en-proceso)
   - Mitigable con keep-alive y HTTP/2

2. **Complejidad operacional:**
   - Dos procesos a arrancar y monitorizar (uvicorn en 8000 y 8001)
   - En producción, dos contenedores/servicios separados

3. **Debugging:**
   - Logs distribuidos; tracing más complejo

---

## Pasos de implementación (Plan B)

### 1. Crear estructura del microservicio

```powershell
# Desde raíz del proyecto
New-Item -ItemType Directory -Path llm_service
cd llm_service
python -m venv venv_llm
& .\venv_llm\Scripts\Activate.ps1
```

### 2. Instalar dependencias LLM

```powershell
# llm_service/requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
transformers>=4.48.0
accelerate>=0.34.2
torch>=2.2.0
sentence-transformers==2.2.2
huggingface-hub>=0.25.2
safetensors>=0.4.5
python-dotenv==1.0.0
httpx==0.24.1
```

```powershell
pip install -r requirements.txt
```

### 3. Implementar main.py y routers

**llm_service/main.py:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import llm_router

app = FastAPI(title="LLM Microservice")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(llm_router.router, prefix="/api/llm", tags=["LLM"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

**llm_service/routers/llm_router.py:**
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.llm_service import LLMService

router = APIRouter()
llm_service = LLMService()

class GenerateRequest(BaseModel):
    messages: list[dict]
    max_new_tokens: int = 250
    temperature: float = 0.5
    top_p: float = 0.9

@router.post("/generate")
async def generate(req: GenerateRequest):
    try:
        answer = llm_service.generate(req.messages, req.max_new_tokens, req.temperature, req.top_p)
        return {"answer": answer, "model": llm_service.model_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class EmbedRequest(BaseModel):
    texts: list[str]
    model: str = "sentence-transformers/all-MiniLM-L6-v2"

@router.post("/embed")
async def embed(req: EmbedRequest):
    embeddings = llm_service.embed(req.texts)
    return {"embeddings": embeddings, "dim": len(embeddings[0]), "model": req.model}
```

**llm_service/services/llm_service.py:**
```python
from transformers import AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer
import torch

class LLMService:
    def __init__(self):
        self.model_name = "Qwen/Qwen3-1.7B"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            device_map="auto",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
        self.embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def generate(self, messages, max_new_tokens, temperature, top_p):
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        generated_tokens = outputs[0][inputs["input_ids"].shape[1]:]
        answer = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
        return answer

    def embed(self, texts):
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
```

### 4. Adaptar backend principal

**backend/services/rag_service.py:**
```python
import httpx

LLM_SERVICE_URL = "http://localhost:8001"

async def generate_response(self, query: str, context_docs: list):
    messages = self._build_messages(query, context_docs)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{LLM_SERVICE_URL}/api/llm/generate",
                json={
                    "messages": messages,
                    "max_new_tokens": 250,
                    "temperature": 0.5,
                    "top_p": 0.9
                }
            )
            response.raise_for_status()
            result = response.json()
            return self._post_process_mentor_response(result["answer"])
        except httpx.HTTPError as e:
            # Fallback a Inference API o mensaje de error
            return f"Error al generar respuesta: {e}"
```

### 5. Arrancar ambos servicios

**Terminal 1 (backend principal):**
```powershell
cd backend
& .\venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8000
```

**Terminal 2 (LLM microservice):**
```powershell
cd llm_service
& .\venv_llm\Scripts\Activate.ps1
uvicorn main:app --reload --port 8001
```

---

## Producción (Docker Compose)

```yaml
version: "3.8"
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - LLM_SERVICE_URL=http://llm:8001
    depends_on:
      - llm

  llm:
    build: ./llm_service
    ports:
      - "8001:8001"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

---

## Conclusión

El **Plan B** (microservicio LLM separado) es la arquitectura recomendada si:
- Las actualizaciones de `transformers` generan conflictos frecuentes
- Se requiere flexibilidad para cambiar modelos sin tocar el backend principal
- Se planea escalar el LLM horizontalmente o deployarlo en GPU mientras el backend queda en CPU

Con este diseño, cada componente tiene su propio ciclo de vida, dependencias y recursos, minimizando acoplamientos y facilitando mantenimiento a largo plazo.
