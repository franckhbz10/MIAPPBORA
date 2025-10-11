"""
Adaptador de Supabase para MIAPPBORA
Maneja la conexión con Supabase (PostgreSQL + pgvector)
"""
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class SupabaseAdapter:
    """
    Adaptador para interactuar con Supabase
    
    Funcionalidades:
    - Autenticación de usuarios
    - Operaciones CRUD en tablas
    - Búsqueda de vectores con pgvector
    - Almacenamiento de corpus
    """
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """
        Inicializa el cliente de Supabase
        
        IMPORTANTE: Antes de usar, configurar en .env:
        - SUPABASE_URL
        - SUPABASE_ANON_KEY o SUPABASE_SERVICE_KEY
        """
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            logger.warning(
                "Supabase no configurado. "
                "Configura SUPABASE_URL y SUPABASE_ANON_KEY en .env"
            )
            return
        
        try:
            self.client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY
            )
            logger.info("Cliente de Supabase inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar Supabase: {e}")
    
    def is_connected(self) -> bool:
        """Verifica si hay conexión con Supabase"""
        return self.client is not None
    
    # ==========================================
    # OPERACIONES DE CORPUS
    # ==========================================
    
    async def insert_phrase(self, phrase_data: Dict[str, Any]) -> Optional[Dict]:
        """
        Inserta una frase del corpus en Supabase
        
        Args:
            phrase_data: Diccionario con bora_text, spanish_text, category, etc.
        
        Returns:
            Frase insertada o None si falla
        """
        if not self.is_connected():
            return None
        
        try:
            result = self.client.table('bora_phrases').insert(phrase_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error al insertar frase: {e}")
            return None
    
    async def get_phrases_by_category(
        self, 
        category: str, 
        limit: int = 10
    ) -> List[Dict]:
        """
        Obtiene frases filtradas por categoría
        
        Categorías disponibles:
        - Saludos y Presentaciones
        - Conversación General
        - Ubicación
        - Relaciones Cotidianas
        - Emergencias
        """
        if not self.is_connected():
            return []
        
        try:
            result = self.client.table('bora_phrases')\
                .select('*')\
                .eq('category', category)\
                .limit(limit)\
                .execute()
            return result.data
        except Exception as e:
            logger.error(f"Error al obtener frases: {e}")
            return []
    
    # ==========================================
    # BÚSQUEDA VECTORIAL (pgvector)
    # ==========================================
    
    async def vector_search(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        category: Optional[str] = None
    ) -> List[Dict]:
        """
        Realiza búsqueda de similitud vectorial usando pgvector
        
        IMPORTANTE: Requiere pgvector habilitado en Supabase
        
        Pasos para habilitar pgvector en Supabase:
        1. Ir a SQL Editor en Supabase Dashboard
        2. Ejecutar: CREATE EXTENSION IF NOT EXISTS vector;
        3. Crear índice: 
           CREATE INDEX ON phrase_embeddings 
           USING ivfflat (embedding vector_cosine_ops);
        
        Args:
            query_embedding: Vector de embedding de la consulta
            top_k: Número de resultados a retornar
            category: Filtro opcional por categoría
        
        Returns:
            Lista de frases más similares
        """
        if not self.is_connected():
            return []
        
        try:
            # Construir query con búsqueda vectorial
            # Nota: La sintaxis exacta depende de la implementación en Supabase
            # Este es un ejemplo que deberás adaptar
            
            query = self.client.rpc(
                'match_phrases',  # Función almacenada en Supabase
                {
                    'query_embedding': query_embedding,
                    'match_threshold': settings.SIMILARITY_THRESHOLD,
                    'match_count': top_k,
                    'category_filter': category
                }
            )
            
            result = query.execute()
            return result.data
        except Exception as e:
            logger.error(f"Error en búsqueda vectorial: {e}")
            return []
    
    async def store_embedding(
        self, 
        phrase_id: int, 
        embedding: List[float],
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Almacena embedding de una frase en Supabase
        
        Args:
            phrase_id: ID de la frase en bora_phrases
            embedding: Vector de embedding
            metadata: Metadatos adicionales
        
        Returns:
            True si se almacenó correctamente
        """
        if not self.is_connected():
            return False
        
        try:
            data = {
                'phrase_id': phrase_id,
                'embedding': embedding,
                'metadata': metadata or {}
            }
            
            result = self.client.table('phrase_embeddings').insert(data).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error al almacenar embedding: {e}")
            return False
    
    # ==========================================
    # OPERACIONES DE USUARIO
    # ==========================================
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Obtiene usuario por email"""
        if not self.is_connected():
            return None
        
        try:
            result = self.client.table('users')\
                .select('*')\
                .eq('email', email)\
                .single()\
                .execute()
            return result.data
        except Exception as e:
            logger.error(f"Error al obtener usuario: {e}")
            return None
    
    async def update_user_points(self, user_id: str, points_to_add: int) -> bool:
        """Actualiza puntos del usuario"""
        if not self.is_connected():
            return False
        
        try:
            # Incrementar puntos atomicamente
            self.client.rpc(
                'increment_user_points',
                {'user_uuid': user_id, 'points': points_to_add}
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Error al actualizar puntos: {e}")
            return False


# Instancia global del adaptador
supabase_adapter = SupabaseAdapter()


def get_supabase_adapter() -> SupabaseAdapter:
    """Función helper para obtener el adaptador"""
    return supabase_adapter
