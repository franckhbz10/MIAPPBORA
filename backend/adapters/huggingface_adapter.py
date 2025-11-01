"""
Adaptador de HuggingFace para MIAPPBORA
Maneja embeddings y modelos de lenguaje desde HuggingFace
"""
from typing import List, Optional, TYPE_CHECKING
from huggingface_hub import InferenceClient
from config.settings import settings
from openai import OpenAI
import logging
import numpy as np

# Import lazy de sentence_transformers (solo si se necesita)
if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

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
        self.embedding_model: Optional['SentenceTransformer'] = None
        self.inference_client: Optional[InferenceClient] = None
        self._openai_client: Optional[OpenAI] = None
        self._initialize_models()
    
    def _initialize_models(self):
        """
        Inicializa modelos de HuggingFace
        
        IMPORTANTE: Para usar modelos privados o aumentar rate limits:
        1. Obtener token en https://huggingface.co/settings/tokens
        2. Configurar HUGGINGFACE_API_KEY en .env
        """
        try:
            # Si usamos API para embeddings (OpenAI), no cargamos el modelo local
            if settings.USE_EMBEDDING_API and settings.OPENAI_API_KEY:
                logger.info(
                    f"Embeddings por API habilitado: OpenAI ({settings.EMBEDDING_API_MODEL}). No se cargará modelo local."
                )
                # Cliente OpenAI (sincrónico) para embeddings
                client_kwargs = {"api_key": settings.OPENAI_API_KEY}
                if settings.OPENAI_BASE_URL:
                    client_kwargs["base_url"] = settings.OPENAI_BASE_URL
                if settings.OPENAI_ORG:
                    client_kwargs["organization"] = settings.OPENAI_ORG
                self._openai_client = OpenAI(**client_kwargs)
            else:
                # Inicializar modelo de embeddings local (requiere sentence-transformers)
                try:
                    from sentence_transformers import SentenceTransformer
                    logger.info(f"Cargando modelo de embeddings local: {settings.EMBEDDING_MODEL}")
                    self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
                    logger.info("Modelo de embeddings local cargado correctamente")
                except ImportError:
                    logger.error(
                        "sentence-transformers no está instalado. "
                        "Para embeddings locales: pip install sentence-transformers"
                    )
                    raise RuntimeError(
                        "Embeddings locales requiere sentence-transformers. "
                        "Use USE_EMBEDDING_API=true o instale: pip install sentence-transformers"
                    )

            # Inicializar backend de LLM SOLO vía Inference API (sin carga local)
            self._init_inference_client()

        except Exception as e:
            logger.error(f"Error al inicializar adaptadores ML: {e}")

    # Se elimina soporte de carga local del LLM

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
        # Ruta OpenAI API
        if settings.USE_EMBEDDING_API and self._openai_client:
            try:
                resp = self._openai_client.embeddings.create(
                    model=settings.EMBEDDING_API_MODEL,
                    input=text,
                )
                vec = (resp.data[0].embedding if resp and resp.data else None)
                if vec is None:
                    return None
                return list(vec)
            except Exception as e:
                logger.error(f"Error al generar embedding (OpenAI API): {e}")
                return None

        # Ruta local (SentenceTransformer)
        if not self.embedding_model:
            logger.error("Modelo de embeddings local no inicializado")
            return None

        try:
            embedding = self.embedding_model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error al generar embedding local: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """
        Genera embeddings para múltiples textos (más eficiente)
        
        Args:
            texts: Lista de textos
        
        Returns:
            Lista de embeddings o None si falla
        """
        # Ruta OpenAI API (entrada como lista -> una sola llamada)
        if settings.USE_EMBEDDING_API and self._openai_client:
            try:
                resp = self._openai_client.embeddings.create(
                    model=settings.EMBEDDING_API_MODEL,
                    input=texts,
                )
                if not resp or not resp.data:
                    return None
                # Orden ya viene alineada con la entrada
                return [list(item.embedding) for item in resp.data]
            except Exception as e:
                logger.error(f"Error al generar embeddings batch (OpenAI API): {e}")
                return None

        # Ruta local (SentenceTransformer)
        if not self.embedding_model:
            logger.error("Modelo de embeddings local no inicializado")
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
            logger.error(f"Error al generar embeddings batch local: {e}")
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
        # Hugging Face Inference API
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
        # Construir prompt plano y usar generate_text con Inference API
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
