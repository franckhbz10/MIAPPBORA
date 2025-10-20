"""
Adaptador de HuggingFace para MIAPPBORA
Maneja embeddings y modelos de lenguaje desde HuggingFace
"""
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from huggingface_hub import InferenceClient
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from config.settings import settings
import logging
import numpy as np

logger = logging.getLogger(__name__)


class HuggingFaceAdapter:
    """
    Adaptador para servicios de HuggingFace
    
    Funcionalidades:
    - Generar embeddings de texto
    - Inferencia con LLMs
    - Caché de modelos
    """
    
    def __init__(self):
        self.embedding_model: Optional[SentenceTransformer] = None
        self.inference_client: Optional[InferenceClient] = None
        self.local_tokenizer: Optional[AutoTokenizer] = None
        self.local_model: Optional[AutoModelForCausalLM] = None
        self._llm_ready: bool = False
        self._initialize_models()
    
    def _initialize_models(self):
        """
        Inicializa modelos de HuggingFace
        
        IMPORTANTE: Para usar modelos privados o aumentar rate limits:
        1. Obtener token en https://huggingface.co/settings/tokens
        2. Configurar HUGGINGFACE_API_KEY en .env
        """
        try:
            # Inicializar modelo de embeddings
            logger.info(f"Cargando modelo de embeddings: {settings.EMBEDDING_MODEL}")
            self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Modelo de embeddings cargado correctamente")
            
            # Inicializar backend de LLM
            if getattr(settings, "LLM_BACKEND", "inference-api") == "transformers":
                # Lazy loading para evitar descargas en arranque
                logger.info(
                    f"LLM backend=transformers (lazy_load={'on'}). Modelo configurado: {settings.LLM_MODEL}"
                )
                # No cargamos aún; se cargará en la primera inferencia
                self._llm_ready = False
                try:
                    dtype = None
                    if settings.LLM_DTYPE.lower() in ("bfloat16", "bf16"):
                        dtype = torch.bfloat16
                    elif settings.LLM_DTYPE.lower() in ("float16", "fp16"):
                        dtype = torch.float16
                    elif settings.LLM_DTYPE.lower() in ("float32", "fp32"):
                        dtype = torch.float32

                    logger.info(f"Cargando LLM local con transformers: {settings.LLM_MODEL}")
                    self.local_tokenizer = AutoTokenizer.from_pretrained(settings.LLM_MODEL)
                    self.local_model = AutoModelForCausalLM.from_pretrained(
                        settings.LLM_MODEL,
                        torch_dtype=dtype or (torch.bfloat16 if torch.cuda.is_available() else torch.float32),
                        device_map=settings.LLM_DEVICE_MAP or "auto",
                    )
                    logger.info("LLM local cargado correctamente")
                except Exception as le:
                    logger.error(f"No se pudo cargar LLM local: {le}. Se intentará usar Inference API.")
                    # fallback a API de inferencia
                    self._init_inference_client()
            else:
                self._init_inference_client()
                
        except Exception as e:
            logger.error(f"Error al inicializar modelos de HuggingFace: {e}")

    def _ensure_local_llm(self) -> bool:
        """Carga perezosa del modelo local si aún no está listo."""
        if self._llm_ready and self.local_model and self.local_tokenizer:
            return True
        try:
            dtype = None
            if settings.LLM_DTYPE.lower() in ("bfloat16", "bf16"):
                dtype = torch.bfloat16
            elif settings.LLM_DTYPE.lower() in ("float16", "fp16"):
                dtype = torch.float16
            elif settings.LLM_DTYPE.lower() in ("float32", "fp32"):
                dtype = torch.float32

            logger.info(f"Cargando LLM local con transformers: {settings.LLM_MODEL}")
            self.local_tokenizer = AutoTokenizer.from_pretrained(settings.LLM_MODEL)
            self.local_model = AutoModelForCausalLM.from_pretrained(
                settings.LLM_MODEL,
                torch_dtype=dtype or (torch.bfloat16 if torch.cuda.is_available() else torch.float32),
                device_map=settings.LLM_DEVICE_MAP or "auto",
            )
            self._llm_ready = True
            logger.info("LLM local cargado correctamente")
            return True
        except Exception as le:
            logger.error(f"No se pudo cargar LLM local: {le}")
            self._llm_ready = False
            return False

    def _init_inference_client(self):
        try:
            if settings.HUGGINGFACE_API_KEY:
                self.inference_client = InferenceClient(token=settings.HUGGINGFACE_API_KEY)
                logger.info("Cliente de inferencia inicializado")
            else:
                logger.warning(
                    "No se configuró HUGGINGFACE_API_KEY. Usando API pública con límites de rate."
                )
                self.inference_client = InferenceClient()
        except Exception as e:
            logger.error(f"Error inicializando InferenceClient: {e}")
    
    # ==========================================
    # EMBEDDINGS
    # ==========================================
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Genera embedding para un texto
        
        Args:
            text: Texto a convertir en embedding
        
        Returns:
            Lista de floats representando el embedding o None si falla
        
        Ejemplo:
            >>> adapter = HuggingFaceAdapter()
            >>> embedding = adapter.generate_embedding("Hola, ¿cómo estás?")
            >>> len(embedding)  # Para all-MiniLM-L6-v2: 384
            384
        """
        if not self.embedding_model:
            logger.error("Modelo de embeddings no inicializado")
            return None
        
        try:
            # Generar embedding
            embedding = self.embedding_model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True  # Normalizar para similitud coseno
            )
            
            # Convertir a lista de Python
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error al generar embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """
        Genera embeddings para múltiples textos (más eficiente)
        
        Args:
            texts: Lista de textos
        
        Returns:
            Lista de embeddings o None si falla
        """
        if not self.embedding_model:
            logger.error("Modelo de embeddings no inicializado")
            return None
        
        try:
            embeddings = self.embedding_model.encode(
                texts,
                batch_size=32,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=len(texts) > 100
            )
            
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Error al generar embeddings batch: {e}")
            return None
    
    def compute_similarity(
        self, 
        embedding1: List[float], 
        embedding2: List[float]
    ) -> float:
        """
        Calcula similitud coseno entre dos embeddings
        
        Args:
            embedding1: Primer embedding
            embedding2: Segundo embedding
        
        Returns:
            Similitud entre -1 y 1 (1 = idéntico, -1 = opuesto)
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Similitud coseno
            similarity = np.dot(vec1, vec2) / (
                np.linalg.norm(vec1) * np.linalg.norm(vec2)
            )
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error al calcular similitud: {e}")
            return 0.0
    
    # ==========================================
    # INFERENCIA CON LLM
    # ==========================================
    
    def generate_text(
        self,
        prompt: str,
        max_length: int = 150,
        temperature: float = 0.7,
    ) -> Optional[str]:
        """
        Genera texto usando modelo de lenguaje
        
        Args:
            prompt: Texto de entrada
            max_length: Longitud máxima de respuesta
            temperature: Creatividad (0.0 = determinístico, 1.0 = creativo)
        
        Returns:
            Texto generado o None si falla
        
        NOTA: Para producción, considerar usar modelos más grandes
        o API de OpenAI para mejor calidad.
        
        Modelos recomendados para evaluación:
        - Embeddings: text-embedding-3-small (OpenAI), Sentence-BERT
        - LLM: Llama-3 8B Instruct, GPT-4o mini
        """
        # Ruta 1: modelo local con transformers
        if getattr(settings, "LLM_BACKEND", "inference-api") == "transformers":
            if self._ensure_local_llm() and self.local_model and self.local_tokenizer:
                try:
                    messages = [{"role": "user", "content": prompt}]
                    try:
                        text = self.local_tokenizer.apply_chat_template(
                            messages,
                            tokenize=False,
                            add_generation_prompt=True,
                            enable_thinking=getattr(settings, "LLM_ENABLE_THINKING", False),
                        )
                    except TypeError:
                        text = self.local_tokenizer.apply_chat_template(
                            messages,
                            tokenize=False,
                            add_generation_prompt=True,
                        )
                    inputs = self.local_tokenizer([text], return_tensors="pt").to(self.local_model.device)
                    with torch.no_grad():
                        generated = self.local_model.generate(
                            **inputs,
                            max_new_tokens=max_length or getattr(settings, "LLM_MAX_NEW_TOKENS", 256),
                            temperature=temperature,
                            top_p=getattr(settings, "LLM_TOP_P", 0.9),
                            do_sample=True,
                        )
                    output = self.local_tokenizer.decode(generated[0], skip_special_tokens=True)
                    return output
                except Exception as e:
                    logger.error(f"Error en generación local: {e}")
            # Si falla local, probamos Inference API si está disponible
        
        # Ruta 2: Hugging Face Inference API
        if not self.inference_client:
            logger.error("Cliente de inferencia no inicializado")
            return None
        try:
            response = self.inference_client.text_generation(
                prompt,
                model=settings.LLM_MODEL,
                max_new_tokens=max_length,
                temperature=temperature,
                return_full_text=False,
            )
            return response
        except Exception as e:
            logger.error(f"Error en generación de texto (Inference API): {e}")
            return None
    
    def chat_completion(
        self, 
        messages: List[dict],
        max_tokens: int = 150
    ) -> Optional[str]:
        """
        Completa conversación estilo chat
        
        Args:
            messages: Lista de mensajes [{"role": "user", "content": "..."}]
            max_tokens: Tokens máximos en respuesta
        
        Returns:
            Respuesta del asistente
        """
        # Ruta 1: modelo local con chat template
        if getattr(settings, "LLM_BACKEND", "inference-api") == "transformers":
            if self._ensure_local_llm() and self.local_model and self.local_tokenizer:
                try:
                    try:
                        text = self.local_tokenizer.apply_chat_template(
                            messages,
                            tokenize=False,
                            add_generation_prompt=True,
                            enable_thinking=getattr(settings, "LLM_ENABLE_THINKING", False),
                        )
                    except TypeError:
                        text = self.local_tokenizer.apply_chat_template(
                            messages,
                            tokenize=False,
                            add_generation_prompt=True,
                        )
                    inputs = self.local_tokenizer([text], return_tensors="pt").to(self.local_model.device)
                    with torch.no_grad():
                        generated = self.local_model.generate(
                            **inputs,
                            max_new_tokens=max_tokens or getattr(settings, "LLM_MAX_NEW_TOKENS", 256),
                            temperature=getattr(settings, "LLM_TEMPERATURE", 0.7),
                            top_p=getattr(settings, "LLM_TOP_P", 0.9),
                            do_sample=True,
                        )
                    output = self.local_tokenizer.decode(generated[0], skip_special_tokens=True)
                    return output
                except Exception as e:
                    logger.error(f"Error en chat completion local: {e}")

        # Ruta 2: construir prompt plano y usar generate_text con Inference API
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt += f"{role.capitalize()}: {content}\n"
        prompt += "Assistant:"
        return self.generate_text(prompt, max_length=max_tokens)


# Instancia global del adaptador
huggingface_adapter = HuggingFaceAdapter()


def get_huggingface_adapter() -> HuggingFaceAdapter:
    """Función helper para obtener el adaptador"""
    return huggingface_adapter
