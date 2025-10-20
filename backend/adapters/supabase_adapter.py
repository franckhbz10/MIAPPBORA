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
    
    def __init__(self, use_service_role: bool = False):
        self.client: Optional[Client] = None
        self._initialize_client(use_service_role=use_service_role)
    
    def _initialize_client(self, use_service_role: bool = False):
        """
        Inicializa el cliente de Supabase
        
        IMPORTANTE: Antes de usar, configurar en .env:
        - SUPABASE_URL
        - SUPABASE_ANON_KEY o SUPABASE_SERVICE_KEY
        """
        # Elegir key según contexto
        supabase_key = None
        if use_service_role and settings.SUPABASE_SERVICE_KEY:
            supabase_key = settings.SUPABASE_SERVICE_KEY
        else:
            supabase_key = settings.SUPABASE_ANON_KEY

        if not settings.SUPABASE_URL or not supabase_key:
            logger.warning(
                "Supabase no configurado. "
                "Configura SUPABASE_URL y SUPABASE_ANON_KEY en .env"
            )
            return
        
        try:
            self.client = create_client(
                settings.SUPABASE_URL,
                supabase_key
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

    async def insert_phrases_bulk(self, phrases: List[Dict[str, Any]]) -> List[Dict]:
        """
        Inserta múltiples frases en una sola operación.
        """
        if not self.is_connected():
            return []
        if not phrases:
            return []
        try:
            result = self.client.table('bora_phrases').insert(phrases).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error en inserción bulk de frases: {e}")
            return []

    async def find_phrase_by_texts(self, bora_text: str, spanish_text: str) -> Optional[Dict]:
        """
        Busca una frase existente por texto en Bora y traducción en español.
        """
        if not self.is_connected():
            return None
        try:
            result = (
                self.client.table('bora_phrases')
                .select('*')
                .eq('bora_text', bora_text)
                .eq('spanish_text', spanish_text)
                .limit(1)
                .execute()
            )
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"Error buscando frase: {e}")
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

    async def has_embedding(self, phrase_id: int) -> bool:
        """Verifica si ya existe un embedding para la frase dada."""
        if not self.is_connected():
            return False
        try:
            result = (
                self.client.table('phrase_embeddings')
                .select('id')
                .eq('phrase_id', phrase_id)
                .limit(1)
                .execute()
            )
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error verificando embedding existente: {e}")
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
    # LEXICON: Operaciones separadas
    # ==========================================

    async def insert_lexicon_entry(self, entry: Dict[str, Any]) -> Optional[Dict]:
        if not self.is_connected():
            return None
        try:
            result = self.client.table('lexicon_entries').insert(entry).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            # Si es conflicto por UNIQUE, intentar recuperar existente
            logger.warning(f"Insert lexicon entry aviso: {e}")
            try:
                found = self.find_lexicon_by_texts(entry['bora_text'], entry['spanish_text'])
                return found
            except Exception:
                return None

    async def find_lexicon_by_texts(self, bora_text: str, spanish_text: str) -> Optional[Dict]:
        if not self.is_connected():
            return None
        try:
            result = (
                self.client.table('lexicon_entries')
                .select('*')
                .eq('bora_text', bora_text)
                .eq('spanish_text', spanish_text)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error buscando lexicon entry: {e}")
            return None

    async def has_lexicon_embedding(self, entry_id: int) -> bool:
        if not self.is_connected():
            return False
        try:
            result = (
                self.client.table('lexicon_embeddings')
                .select('id')
                .eq('entry_id', entry_id)
                .limit(1)
                .execute()
            )
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error verificando lexicon embedding: {e}")
            return False

    async def store_lexicon_embedding(self, entry_id: int, embedding: List[float], metadata: Optional[Dict] = None) -> bool:
        if not self.is_connected():
            return False
        try:
            payload = {'entry_id': entry_id, 'embedding': embedding, 'metadata': metadata or {}}
            result = self.client.table('lexicon_embeddings').insert(payload).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error guardando lexicon embedding: {e}")
            return False

    async def vector_search_lexicon(self, query_embedding: List[float], top_k: int = 5, category: Optional[str] = None, min_similarity: Optional[float] = None) -> List[Dict]:
        if not self.is_connected():
            return []
        try:
            threshold = settings.SIMILARITY_THRESHOLD if (min_similarity is None) else float(min_similarity)
            result = self.client.rpc(
                'match_lexicon',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': threshold,
                    'match_count': top_k,
                    'category_filter': category,
                },
            ).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error en match_lexicon: {e}")
            return []

    async def reset_lexicon_source(self, source: str = 'salida.json') -> bool:
        """Elimina entradas y embeddings asociados a un source del lexicón."""
        if not self.is_connected():
            return False
        try:
            # Borrar entradas por source; embeddings se eliminan por CASCADE
            self.client.table('lexicon_entries').delete().eq('source', source).execute()
            return True
        except Exception as e:
            logger.error(f"Error reseteando lexicon por source: {e}")
            return False

    # ==========================================
    # LEXICON: Bulk operations for performance
    # ==========================================

    async def upsert_lexicon_entries_bulk(self, entries: List[Dict[str, Any]], on_conflict: str = 'bora_text,spanish_text') -> List[Dict]:
        """Bulk upsert lexicon entries and return affected rows with IDs."""
        if not self.is_connected():
            return []
        if not entries:
            return []
        try:
            result = (
                self.client
                .table('lexicon_entries')
                .upsert(entries, on_conflict=on_conflict)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Error en upsert bulk de lexicon_entries: {e}")
            return []

    async def get_existing_lexicon_embeddings(self, entry_ids: List[int]) -> List[int]:
        """Return entry_ids that already have an embedding (batch)."""
        if not self.is_connected():
            return []
        if not entry_ids:
            return []
        try:
            result = (
                self.client
                .table('lexicon_embeddings')
                .select('entry_id')
                .in_('entry_id', entry_ids)
                .execute()
            )
            rows = result.data or []
            return [r.get('entry_id') for r in rows if r.get('entry_id') is not None]
        except Exception as e:
            logger.error(f"Error consultando embeddings existentes: {e}")
            return []

    async def get_existing_lexicon_embeddings_by_kind(self, entry_ids: List[int], kind: str) -> List[int]:
        """Return entry_ids that already have an embedding of the given kind in metadata.kind."""
        if not self.is_connected():
            return []
        if not entry_ids:
            return []
        try:
            # Supabase JS query style for JSON filter: metadata->>kind equals value
            # Python client supports .filter('metadata->>kind','eq',kind)
            result = (
                self.client
                .table('lexicon_embeddings')
                .select('entry_id, metadata')
                .in_('entry_id', entry_ids)
                .filter('metadata->>kind', 'eq', kind)
                .execute()
            )
            rows = result.data or []
            return [r.get('entry_id') for r in rows if r.get('entry_id') is not None]
        except Exception as e:
            logger.error(f"Error consultando embeddings por kind='{kind}': {e}")
            return []

    async def insert_lexicon_embeddings_bulk(self, rows: List[Dict[str, Any]]) -> int:
        """Bulk insert lexicon embeddings. Returns number of inserted rows."""
        if not self.is_connected():
            return 0
        if not rows:
            return 0
        try:
            result = (
                self.client
                .table('lexicon_embeddings')
                .insert(rows)
                .execute()
            )
            return len(result.data or [])
        except Exception as e:
            logger.error(f"Error en inserción bulk de lexicon_embeddings: {e}")
            return 0

    # ==========================================
    # BORA_DOCS: Nuevo esquema unificado
    # ==========================================

    async def upsert_lemmas_bulk(self, lemmas: List[Dict[str, Any]]) -> List[Dict]:
        if not self.is_connected():
            return []
        if not lemmas:
            return []
        try:
            result = (
                self.client
                .table('lexicon_lemmas')
                .upsert(lemmas, on_conflict='lemma,source')
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Error upsert lemmas: {e}")
            return []

    async def insert_subentries_bulk(self, subentries: List[Dict[str, Any]]) -> List[Dict]:
        if not self.is_connected():
            return []
        if not subentries:
            return []
        try:
            result = self.client.table('lexicon_subentries').insert(subentries).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error insert subentries: {e}")
            return []

    async def insert_examples_bulk(self, examples: List[Dict[str, Any]]) -> List[Dict]:
        if not self.is_connected():
            return []
        if not examples:
            return []
        try:
            result = self.client.table('lexicon_examples').insert(examples).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error insert examples: {e}")
            return []

    async def insert_bora_docs_bulk(self, docs: List[Dict[str, Any]]) -> int:
        if not self.is_connected():
            return 0
        if not docs:
            return 0
        try:
            result = self.client.table('bora_docs').insert(docs).execute()
            return len(result.data or [])
        except Exception as e:
            logger.error(f"Error insert bora_docs: {e}")
            return 0

    async def find_lemma_by_text(self, lemma: str) -> Optional[Dict[str, Any]]:
        """Busca un lemma exacto (case-sensitive por defecto)."""
        if not self.is_connected():
            return None
        try:
            res = (
                self.client
                .table('lexicon_lemmas')
                .select('id, lemma, gloss_es, pos, pos_full, page')
                .eq('lemma', lemma)
                .limit(1)
                .execute()
            )
            rows = res.data or []
            return rows[0] if rows else None
        except Exception as e:
            logger.error(f"Error buscando lemma='{lemma}': {e}")
            return None

    async def get_examples_by_lemma_id(self, lemma_id: int, limit: int = 3) -> List[Dict[str, Any]]:
        """Obtiene ejemplos (bora_text, spanish_text) de un lemma dado."""
        if not self.is_connected():
            return []
        try:
            res = (
                self.client
                .table('lexicon_examples')
                .select('id, bora_text, spanish_text, page')
                .eq('lemma_id', lemma_id)
                .limit(limit)
                .execute()
            )
            return res.data or []
        except Exception as e:
            logger.error(f"Error obteniendo ejemplos de lemma_id={lemma_id}: {e}")
            return []

    async def vector_search_bora_docs(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        kinds: Optional[List[str]] = None,
        pos_full: Optional[str] = None,
        min_similarity: Optional[float] = None,
    ) -> List[Dict]:
        if not self.is_connected():
            return []
        try:
            threshold = settings.SIMILARITY_THRESHOLD if (min_similarity is None) else float(min_similarity)
            params: Dict[str, Any] = {
                'query_embedding': query_embedding,
                'match_threshold': threshold,
                'match_count': top_k,
                'kind_filter': kinds if kinds else None,
                'pos_filter': pos_full if pos_full else None,
            }
            res = self.client.rpc('match_bora_docs', params).execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Error en match_bora_docs: {e}")
            return []
    
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
# Instancia por defecto para la app web (usa anon key y RLS de solo lectura)
supabase_adapter = SupabaseAdapter(use_service_role=False)


def get_supabase_adapter() -> SupabaseAdapter:
    """Función helper para obtener el adaptador"""
    return supabase_adapter
