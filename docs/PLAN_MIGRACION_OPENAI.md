# Plan de Trabajo: Migración a OpenAI API

## 📋 Objetivo
Eliminar el microservicio LLM local (que consume muchos recursos) y migrar a **OpenAI API** usando **GPT-4** o **GPT-3.5-turbo** para generar respuestas del mentor Bora.

---

## 🎯 Ventajas de la Migración

✅ **Menor consumo de recursos:** No necesita cargar modelos locales (4GB+ RAM)  
✅ **Mejor calidad:** GPT-4 es más potente que Qwen3-1.7B  
✅ **Más rápido:** Sin overhead de carga de modelo  
✅ **Menor latencia:** API optimizada en la nube  
✅ **Escalable:** Sin límites de hardware local  
✅ **Mantenimiento:** Sin preocupaciones por actualizaciones de transformers/torch  

---

## 📝 Fases del Plan

### ✅ **Fase 1: Preparación (10 min)**
**Objetivo:** Obtener API key de OpenAI y verificar acceso

**Tareas:**
1. ✅ Crear cuenta en [OpenAI Platform](https://platform.openai.com/)
2. ✅ Generar API key en [API Keys](https://platform.openai.com/api-keys)
3. ✅ Verificar créditos disponibles (o configurar billing)
4. ✅ Probar API key con un request simple

**Archivos a modificar:** Ninguno aún

---

### ✅ **Fase 2: Crear adaptador OpenAI (20 min)**
**Objetivo:** Implementar nuevo adaptador que reemplace al microservicio LLM

**Tareas:**
1. ✅ Crear `backend/adapters/openai_adapter.py`
2. ✅ Instalar `openai` library: `pip install openai`
3. ✅ Implementar clase `OpenAIAdapter` con:
   - `chat_completion()` - Generar respuesta usando GPT-4/3.5-turbo
   - `generate_embedding()` - Usar OpenAI embeddings (opcional)
4. ✅ Añadir configuración al `.env`:
   ```properties
   OPENAI_API_KEY=sk-...
   OPENAI_MODEL=gpt-4  # o gpt-3.5-turbo
   OPENAI_TEMPERATURE=0.7
   OPENAI_MAX_TOKENS=500
   ```
5. ✅ Actualizar `backend/config/settings.py` con nuevas variables

**Archivos a crear/modificar:**
- `backend/adapters/openai_adapter.py` (NUEVO)
- `backend/.env` (añadir OPENAI_API_KEY)
- `backend/config/settings.py` (añadir settings de OpenAI)
- `backend/requirements.txt` (añadir openai)

---

### ✅ **Fase 3: Modificar RAG Service (15 min)**
**Objetivo:** Actualizar `rag_service.py` para usar OpenAI en lugar del microservicio

**Tareas:**
1. ✅ Modificar `backend/services/rag_service.py`:
   - Remover import de `llm_service_adapter`
   - Añadir import de `openai_adapter`
   - Actualizar `__init__` para usar OpenAI adapter
   - Modificar `generate_response()` para llamar a OpenAI
   - Mantener fallback a HuggingFace local si OpenAI falla

**Flujo actualizado:**
```
1. Intentar OpenAI API (GPT-4/3.5-turbo)
   ├─ Éxito → Retornar respuesta
   └─ Fallo → Log warning + continuar con fallback

2. Fallback a HuggingFace local (Qwen3-1.7B)
   ├─ Éxito → Retornar respuesta
   └─ Fallo → Respuesta básica desde contexto
```

**Archivos a modificar:**
- `backend/services/rag_service.py`

---

### ✅ **Fase 4: Actualizar configuración (10 min)**
**Objetivo:** Deshabilitar microservicio LLM y configurar OpenAI

**Tareas:**
1. ✅ Modificar `backend/.env`:
   ```properties
   # Deshabilitar microservicio LLM
   LLM_SERVICE_ENABLED=false
   
   # Habilitar OpenAI
   OPENAI_ENABLED=true
   OPENAI_API_KEY=sk-...
   OPENAI_MODEL=gpt-4
   ```

2. ✅ Actualizar `backend/config/settings.py`:
   ```python
   OPENAI_ENABLED: bool = False
   OPENAI_API_KEY: Optional[str] = None
   OPENAI_MODEL: str = "gpt-4"  # o "gpt-3.5-turbo"
   OPENAI_TEMPERATURE: float = 0.7
   OPENAI_MAX_TOKENS: int = 500
   ```

3. ✅ Modificar `backend/main.py` (startup):
   - Remover health check del microservicio LLM
   - Añadir verificación de OpenAI API key

**Archivos a modificar:**
- `backend/.env`
- `backend/config/settings.py`
- `backend/main.py`

---

### ✅ **Fase 5: Testing (15 min)**
**Objetivo:** Validar que OpenAI funciona correctamente

**Tareas:**
1. ✅ Crear `backend/test_openai.py`:
   ```python
   # Test simple de OpenAI API
   from adapters.openai_adapter import get_openai_adapter
   
   adapter = get_openai_adapter()
   response = adapter.chat_completion([
       {"role": "user", "content": "¿Qué es Bora?"}
   ])
   print(response)
   ```

2. ✅ Arrancar backend: `uvicorn main:app --reload`
3. ✅ Probar endpoint del mentor: `POST /api/rag/query`
4. ✅ Verificar logs que muestran uso de OpenAI
5. ✅ Probar fallback desactivando OpenAI temporalmente

**Archivos a crear:**
- `backend/test_openai.py` (temporal, para validar)

---

### ✅ **Fase 6: Limpieza (10 min)**
**Objetivo:** Eliminar microservicio LLM y archivos innecesarios

**Tareas:**
1. ✅ Detener proceso del microservicio LLM (puerto 8001)
2. ✅ Eliminar carpeta completa: `llm_service/`
3. ✅ Remover archivos de adaptador LLM:
   - `backend/adapters/llm_service_adapter.py`
4. ✅ Limpiar imports innecesarios en el código
5. ✅ Actualizar `.gitignore` si es necesario

**Comandos:**
```powershell
# Detener microservicio (si está corriendo)
Get-Process -Name python | Where-Object {$_.Path -like "*llm_service*"} | Stop-Process

# Eliminar carpeta
Remove-Item -Recurse -Force llm_service

# Eliminar adaptador viejo
Remove-Item backend/adapters/llm_service_adapter.py
```

**Archivos a eliminar:**
- `llm_service/` (carpeta completa)
- `backend/adapters/llm_service_adapter.py`

---

### ✅ **Fase 7: Documentación (10 min)**
**Objetivo:** Actualizar documentación del proyecto

**Tareas:**
1. ✅ Actualizar `README.md`:
   - Indicar que usa OpenAI API
   - Explicar cómo obtener API key
   - Documentar variables de entorno

2. ✅ Crear `docs/SETUP_OPENAI.md`:
   - Guía paso a paso para configurar OpenAI
   - Estimación de costos
   - Modelos disponibles (GPT-4, GPT-3.5-turbo)

3. ✅ Actualizar `docs/GUIA_INSTALACION.md`:
   - Remover sección de microservicio LLM
   - Añadir sección de OpenAI

4. ✅ Archivar documentación vieja:
   - Mover `docs/LLM_MICROSERVICE.md` a `docs/archive/`
   - Mover `docs/PLAN_IMPLEMENTACION_LLM.md` a `docs/archive/`

**Archivos a modificar/crear:**
- `README.md`
- `docs/SETUP_OPENAI.md` (NUEVO)
- `docs/GUIA_INSTALACION.md`
- `docs/archive/` (carpeta para docs viejos)

---

### ✅ **Fase 8: Optimización (Opcional - 15 min)**
**Objetivo:** Optimizar uso de OpenAI para reducir costos

**Tareas:**
1. ⏳ Implementar caché de respuestas frecuentes
2. ⏳ Usar `gpt-3.5-turbo` para consultas simples
3. ⏳ Implementar rate limiting
4. ⏳ Añadir métricas de uso (tokens consumidos)
5. ⏳ Configurar timeout adecuado

**Archivos a modificar:**
- `backend/adapters/openai_adapter.py`
- `backend/services/rag_service.py`

---

## ⏱️ Cronograma Estimado

| Fase | Duración | Acumulado |
|------|----------|-----------|
| 1. Preparación | 10 min | 0:10 |
| 2. Crear adaptador OpenAI | 20 min | 0:30 |
| 3. Modificar RAG Service | 15 min | 0:45 |
| 4. Actualizar configuración | 10 min | 0:55 |
| 5. Testing | 15 min | 1:10 |
| 6. Limpieza | 10 min | 1:20 |
| 7. Documentación | 10 min | 1:30 |
| 8. Optimización (opcional) | 15 min | 1:45 |

**Tiempo total estimado: 1.5 - 2 horas**

---

## 💰 Estimación de Costos OpenAI

### Modelos Recomendados

#### GPT-4 Turbo (Recomendado para producción)
- **Input:** $0.01 / 1K tokens
- **Output:** $0.03 / 1K tokens
- **Contexto:** 128K tokens
- **Calidad:** Excelente

#### GPT-3.5 Turbo (Recomendado para desarrollo)
- **Input:** $0.0005 / 1K tokens  
- **Output:** $0.0015 / 1K tokens
- **Contexto:** 16K tokens
- **Calidad:** Muy buena

### Ejemplo de Uso
**Supuestos:**
- 100 consultas/día
- ~500 tokens promedio por consulta (input + output)

**Costo mensual (30 días):**
- GPT-4 Turbo: ~$45/mes
- GPT-3.5 Turbo: ~$2.25/mes

**Recomendación:** Comenzar con **GPT-3.5-turbo** para desarrollo y testing, migrar a **GPT-4** si necesitas mejor calidad.

---

## 🔧 Código de Ejemplo

### OpenAI Adapter
```python
# backend/adapters/openai_adapter.py
import openai
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class OpenAIAdapter:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.enabled = settings.OPENAI_ENABLED
        openai.api_key = self.api_key
        logger.info(f"OpenAIAdapter inicializado: {self.model}")
    
    def chat_completion(self, messages, max_tokens=None, temperature=None):
        if not self.enabled or not self.api_key:
            raise Exception("OpenAI no configurado")
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens or settings.OPENAI_MAX_TOKENS,
                temperature=temperature or settings.OPENAI_TEMPERATURE
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error llamando a OpenAI: {e}")
            raise

_openai_adapter = None

def get_openai_adapter():
    global _openai_adapter
    if _openai_adapter is None:
        _openai_adapter = OpenAIAdapter()
    return _openai_adapter
```

### RAG Service (actualizado)
```python
# backend/services/rag_service.py
from adapters.openai_adapter import get_openai_adapter

class RAGService:
    def __init__(self):
        self.openai_adapter = get_openai_adapter() if settings.OPENAI_ENABLED else None
        self.hf_adapter = get_huggingface_adapter()  # Fallback
        # ...
    
    async def generate_response(self, query, context, conversation_history=None):
        messages = self._build_messages(query, context, conversation_history)
        
        # Intentar OpenAI primero
        if self.openai_adapter:
            try:
                logger.info("🤖 Generando respuesta con OpenAI...")
                response = self.openai_adapter.chat_completion(messages)
                logger.info("✓ Respuesta generada con OpenAI")
                return self._post_process_mentor_response(response)
            except Exception as e:
                logger.warning(f"⚠️ OpenAI falló: {e}, usando fallback local")
        
        # Fallback a HuggingFace local
        logger.info("🔧 Generando respuesta con HuggingFace local...")
        response = self.hf_adapter.chat_completion(messages)
        return self._post_process_mentor_response(response)
```

---

## 🎯 Resultado Final

### Antes (Microservicio LLM)
```
Usuario → Backend → Microservicio:8001 → Qwen3-1.7B → Respuesta
          (8000)    (HTTP)              (4GB RAM)
```

### Después (OpenAI API)
```
Usuario → Backend → OpenAI API → GPT-4 → Respuesta
          (8000)    (HTTPS)     (Cloud)
```

### Beneficios
- ✅ **-4GB RAM** (no carga modelo local)
- ✅ **-1 servicio** (elimina microservicio)
- ✅ **+Calidad** (GPT-4 > Qwen3-1.7B)
- ✅ **+Velocidad** (API optimizada)
- ✅ **+Estabilidad** (sin problemas de device_map, torch, etc.)

---

## ✅ Checklist de Ejecución

### Preparación
- [ ] Crear cuenta en OpenAI
- [ ] Obtener API key
- [ ] Verificar créditos/billing
- [ ] Probar API key con curl

### Implementación
- [ ] Instalar `openai` library
- [ ] Crear `openai_adapter.py`
- [ ] Añadir variables al `.env`
- [ ] Actualizar `settings.py`
- [ ] Modificar `rag_service.py`
- [ ] Actualizar `main.py` (startup)

### Testing
- [ ] Probar OpenAI adapter aislado
- [ ] Arrancar backend y probar endpoint
- [ ] Verificar logs de uso de OpenAI
- [ ] Probar fallback

### Limpieza
- [ ] Detener microservicio LLM
- [ ] Eliminar carpeta `llm_service/`
- [ ] Eliminar `llm_service_adapter.py`
- [ ] Limpiar imports

### Documentación
- [ ] Actualizar README.md
- [ ] Crear SETUP_OPENAI.md
- [ ] Actualizar GUIA_INSTALACION.md
- [ ] Archivar docs viejos

---

## 🚀 Comando de Inicio

```powershell
# Comenzar con Fase 1
# 1. Ir a https://platform.openai.com/api-keys
# 2. Crear API key
# 3. Ejecutar: pip install openai
# 4. Crear backend/adapters/openai_adapter.py
```

---

**¿Listo para comenzar con la Fase 1?**
