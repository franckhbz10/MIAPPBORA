"""
Adaptador HÍBRIDO de HuggingFace para MIAPPBORA
Soporta embeddings en modo LOCAL y API

Configuración en .env:
    USE_EMBEDDING_API=true   # Usar API de HuggingFace
    USE_EMBEDDING_API=false  # Usar modelo local (por defecto)
"""
from typing import List, Optional, Dict, Any
import logging
import numpy as np
import requests
import time

from config.settings import settings

logger = logging.getLogger(__name__)

# Imports opcionales para modo local
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("⚠️ sentence-transformers no instalado. Solo modo API disponible.")


class HuggingFaceHybridAdapter:
    """
    Adaptador híbrido que soporta embeddings locales y vía API
    
    Modos de operación:
    - LOCAL: Descarga modelo y ejecuta localmente
    - API: Usa Inference API de HuggingFace
    
    El modo se configura con la variable USE_EMBEDDING_API en .env
    """
    
    # URLs de API para diferentes modelos
    API_ENDPOINTS = {
        "sentence-transformers/all-MiniLM-L6-v2": 
            "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2":
            "https://api-inference.huggingface.co/models/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "intfloat/multilingual-e5-small":
            "https://api-inference.huggingface.co/models/intfloat/multilingual-e5-small"
    }
    
    def __init__(self, use_api: Optional[bool] = None):
        """
        Inicializa el adaptador
        
        Args:
            use_api: True para API, False para local, None para usar settings
        """
        self.embedding_model: Optional[SentenceTransformer] = None
        self.use_api = use_api if use_api is not None else getattr(settings, 'USE_EMBEDDING_API', False)
        self.api_url = self.API_ENDPOINTS.get(settings.EMBEDDING_MODEL)
        self.api_headers = None
        
        if settings.HUGGINGFACE_API_KEY:
            self.api_headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}
        
        self._initialize()
    
    def _initialize(self):
        """Inicializa el modo apropiado (local o API)"""
        
        if self.use_api:
            logger.info("🌐 Modo: API de HuggingFace")
            self._initialize_api_mode()
        else:
            logger.info("💻 Modo: Embeddings locales")
            self._initialize_local_mode()
    
    def _initialize_local_mode(self):
        """Inicializa modelo local"""
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.error("❌ sentence-transformers no está instalado")
            logger.error("Instala con: pip install sentence-transformers")
            logger.info("💡 Alternativa: Usar modo API con USE_EMBEDDING_API=true")
            return
        
        try:
            logger.info(f"📦 Descargando/Cargando: {settings.EMBEDDING_MODEL}")
            logger.info("⏳ Primera descarga puede tomar 1-2 minutos...")
            
            self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            
            logger.info("✅ Modelo local cargado correctamente")
            logger.info(f"📏 Dimensión: {settings.EMBEDDING_DIMENSION}")
            
        except Exception as e:
            logger.error(f"❌ Error al cargar modelo local: {e}")
            logger.info("💡 Puedes usar modo API: SET USE_EMBEDDING_API=true en .env")
    
    def _initialize_api_mode(self):
        """Inicializa modo API"""
        
        if not self.api_url:
            logger.error(f"❌ No hay endpoint API para modelo: {settings.EMBEDDING_MODEL}")
            logger.info("Modelos soportados en API:")
            for model in self.API_ENDPOINTS.keys():
                logger.info(f"  • {model}")
            return
        
        if not self.api_headers:
            logger.warning("⚠️ No hay HUGGINGFACE_API_KEY configurada")
            logger.warning("Rate limits reducidos sin token")
            logger.info("Obtén token en: https://huggingface.co/settings/tokens")
        
        # Test de conexión
        try:
            logger.info("🔍 Verificando conexión con API...")
            test_response = self._call_api("test")
            
            if test_response:
                logger.info("✅ API conectada correctamente")
                logger.info(f"📏 Dimensión: {len(test_response)}")
            else:
                logger.warning("⚠️ API responde pero puede estar en cold start")
                
        except Exception as e:
            logger.error(f"❌ Error al conectar con API: {e}")
    
    # ==========================================
    # MÉTODO PRINCIPAL: GENERAR EMBEDDING
    # ==========================================
    
    def generate_embedding(self, text: str, retry_on_failure: bool = True) -> Optional[List[float]]:
        """
        Genera embedding usando el modo configurado (local o API)
        
        Args:
            text: Texto a convertir en embedding
            retry_on_failure: Si falla API, intentar con modo local
        
        Returns:
            Lista de floats (embedding) o None si falla
        """
        if not text or not text.strip():
            logger.warning("Texto vacío, retornando None")
            return None
        
        # Intentar con el modo configurado
        if self.use_api:
            embedding = self._generate_via_api(text)
            
            # Fallback a local si API falla y está disponible
            if embedding is None and retry_on_failure and self.embedding_model:
                logger.warning("API falló, intentando con modelo local...")
                embedding = self._generate_local(text)
        else:
            embedding = self._generate_local(text)
            
            # Fallback a API si local falla
            if embedding is None and retry_on_failure and self.api_url:
                logger.warning("Modelo local falló, intentando con API...")
                embedding = self._generate_via_api(text)
        
        return embedding
    
    # ==========================================
    # MODO LOCAL
    # ==========================================
    
    def _generate_local(self, text: str) -> Optional[List[float]]:
        """Genera embedding usando modelo local"""
        
        if not self.embedding_model:
            logger.error("Modelo local no inicializado")
            return None
        
        try:
            start_time = time.time()
            
            # Generar embedding
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            
            # Convertir a lista
            embedding_list = embedding.tolist()
            
            elapsed = (time.time() - start_time) * 1000
            logger.debug(f"⚡ Embedding local generado en {elapsed:.0f}ms")
            
            return embedding_list
            
        except Exception as e:
            logger.error(f"Error al generar embedding local: {e}")
            return None
    
    # ==========================================
    # MODO API
    # ==========================================
    
    def _generate_via_api(self, text: str) -> Optional[List[float]]:
        """Genera embedding usando API de HuggingFace"""
        
        if not self.api_url:
            logger.error("URL de API no configurada")
            return None
        
        try:
            embedding = self._call_api(text)
            return embedding
            
        except Exception as e:
            logger.error(f"Error al generar embedding vía API: {e}")
            return None
    
    def _call_api(self, text: str, max_retries: int = 3) -> Optional[List[float]]:
        """
        Llama a la API de HuggingFace con reintentos
        
        Args:
            text: Texto a procesar
            max_retries: Número máximo de reintentos
        
        Returns:
            Embedding como lista de floats
        """
        payload = {"inputs": text}
        
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                response = requests.post(
                    self.api_url,
                    headers=self.api_headers,
                    json=payload,
                    timeout=30
                )
                
                elapsed = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # La API puede retornar diferentes formatos
                    if isinstance(result, list):
                        if isinstance(result[0], list):
                            embedding = result[0]  # [[emb]] -> [emb]
                        else:
                            embedding = result
                    else:
                        logger.error(f"Formato inesperado de API: {type(result)}")
                        return None
                    
                    logger.debug(f"🌐 Embedding API generado en {elapsed:.0f}ms")
                    return embedding
                
                elif response.status_code == 503:
                    # Modelo en cold start
                    wait_time = 2 ** attempt  # Backoff exponencial
                    logger.warning(f"⏳ Modelo cargando... reintento en {wait_time}s")
                    time.sleep(wait_time)
                    continue
                
                elif response.status_code == 429:
                    logger.error("❌ Rate limit alcanzado")
                    logger.info("💡 Considera usar modelo local o esperar unos minutos")
                    return None
                
                else:
                    logger.error(f"❌ API error {response.status_code}: {response.text}")
                    return None
                    
            except requests.exceptions.Timeout:
                logger.warning(f"⏱️ Timeout en intento {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return None
                
            except Exception as e:
                logger.error(f"Error en llamada API: {e}")
                return None
        
        logger.error("❌ Máximo de reintentos alcanzado")
        return None
    
    # ==========================================
    # BATCH PROCESSING
    # ==========================================
    
    def generate_embeddings_batch(
        self, 
        texts: List[str], 
        batch_size: int = 32,
        show_progress: bool = True
    ) -> List[Optional[List[float]]]:
        """
        Genera embeddings para múltiples textos
        
        Args:
            texts: Lista de textos
            batch_size: Tamaño del batch (solo para local)
            show_progress: Mostrar progreso
        
        Returns:
            Lista de embeddings
        """
        if self.use_api:
            # API: procesar uno por uno (no soporta batch nativo)
            return self._batch_api(texts, show_progress)
        else:
            # Local: usar batch nativo de sentence-transformers
            return self._batch_local(texts, batch_size, show_progress)
    
    def _batch_local(
        self, 
        texts: List[str], 
        batch_size: int,
        show_progress: bool
    ) -> List[Optional[List[float]]]:
        """Procesar batch en modo local"""
        
        if not self.embedding_model:
            logger.error("Modelo local no inicializado")
            return [None] * len(texts)
        
        try:
            logger.info(f"📦 Procesando {len(texts)} textos en modo local...")
            
            embeddings = self.embedding_model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )
            
            # Convertir a lista de listas
            return [emb.tolist() for emb in embeddings]
            
        except Exception as e:
            logger.error(f"Error en batch local: {e}")
            return [None] * len(texts)
    
    def _batch_api(self, texts: List[str], show_progress: bool) -> List[Optional[List[float]]]:
        """Procesar batch en modo API (secuencial)"""
        
        logger.info(f"🌐 Procesando {len(texts)} textos vía API...")
        logger.warning("⚠️ Modo API procesa secuencialmente (puede ser lento)")
        
        embeddings = []
        for i, text in enumerate(texts):
            if show_progress and (i + 1) % 10 == 0:
                logger.info(f"Progreso: {i + 1}/{len(texts)}")
            
            emb = self.generate_embedding(text, retry_on_failure=False)
            embeddings.append(emb)
            
            # Rate limiting gentil
            time.sleep(0.1)
        
        return embeddings
    
    # ==========================================
    # UTILIDADES
    # ==========================================
    
    def get_info(self) -> Dict[str, Any]:
        """Retorna información sobre el adaptador"""
        
        return {
            "mode": "API" if self.use_api else "LOCAL",
            "model": settings.EMBEDDING_MODEL,
            "dimension": settings.EMBEDDING_DIMENSION,
            "api_available": self.api_url is not None,
            "local_available": self.embedding_model is not None,
            "has_api_key": self.api_headers is not None
        }


# ==========================================
# SINGLETON
# ==========================================

_adapter_instance: Optional[HuggingFaceHybridAdapter] = None

def get_huggingface_hybrid_adapter() -> HuggingFaceHybridAdapter:
    """Obtiene instancia singleton del adaptador híbrido"""
    global _adapter_instance
    
    if _adapter_instance is None:
        _adapter_instance = HuggingFaceHybridAdapter()
    
    return _adapter_instance
