"""
Servicio RAG (Retrieval-Augmented Generation) para MIAPPBORA
Implementa el pipeline completo de RAG con Langchain
"""
from typing import List, Dict, Optional, Any, Tuple
import time
from pathlib import Path
from langchain.embeddings.base import Embeddings
from langchain.vectorstores import VectorStore
from langchain.chains import RetrievalQA
from langchain.llms.base import LLM
from langchain.prompts import PromptTemplate
from sqlalchemy.orm import Session

from models.database import BoraPhrase, PhraseEmbedding, ChatConversation, ChatMessage
from adapters.huggingface_adapter import get_huggingface_adapter
from adapters.supabase_adapter import get_supabase_adapter
from adapters.openai_adapter import get_openai_adapter
from config.settings import settings
import logging
import json

logger = logging.getLogger(__name__)

# Cache simple en memoria para resultados del lexicón
_CACHE_TTL_SECONDS = 120  # 2 minutos
_lexicon_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}

def _make_lexicon_cache_key(q: str, top_k: int, min_sim: float, category: Optional[str], fast: bool) -> str:
    cat = (category or '').strip().lower()
    return f"q={q.strip().lower()}|k={top_k}|min={min_sim:.2f}|cat={cat}|fast={int(fast)}"


class CustomHuggingFaceEmbeddings(Embeddings):
    """
    Wrapper de embeddings de HuggingFace para Langchain
    Adapta nuestro HuggingFaceAdapter a la interfaz de Langchain
    """
    
    def __init__(self):
        self.hf_adapter = get_huggingface_adapter()
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para múltiples documentos"""
        embeddings = self.hf_adapter.generate_embeddings_batch(texts)
        return embeddings if embeddings else []
    
    def embed_query(self, text: str) -> List[float]:
        """Genera embedding para una consulta"""
        embedding = self.hf_adapter.generate_embedding(text)
        return embedding if embedding else []


class RAGService:
    """
    Servicio de RAG para consultas sobre el idioma Bora
    
    Pipeline RAG:
    1. Usuario hace pregunta
    2. Convertir pregunta a embedding
    3. Buscar frases similares en vector store (pgvector)
    4. Construir contexto con frases relevantes
    5. Generar respuesta usando LLM + contexto
    6. Retornar respuesta con fuentes
    
    Características:
    - Búsqueda semántica en corpus Bora
    - Filtrado por categoría
    - Historial de conversaciones
    - Referencias a frases fuente
    """
    
    def __init__(self):
        self.hf_adapter = get_huggingface_adapter()  # Fallback local
        self.supabase_adapter = get_supabase_adapter()
        self.embeddings = CustomHuggingFaceEmbeddings()
        
        # Adaptador de OpenAI (si está habilitado)
        self.openai_adapter = get_openai_adapter() if settings.OPENAI_ENABLED else None
    
    # ==========================================
    # Helpers de conversación/persistencia
    # ==========================================

    def _conversation_title_from_query(self, query: str) -> str:
        """Genera título corto para la conversación."""
        if not query:
            return "Nueva conversación"
        normalized = query.strip()
        return normalized if len(normalized) <= 80 else f"{normalized[:77]}..."

    def _fetch_conversation_history_from_db(
        self,
        db: Optional[Session],
        conversation_id: Optional[int],
        limit: int = 6,
    ) -> List[Dict[str, Any]]:
        """Obtiene historial desde la DB para alimentar el prompt."""
        if not db or not conversation_id:
            return []

        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
        if not messages:
            return []

        # Solo últimos N para evitar prompts gigantes
        sliced = messages[-limit:]
        return [{"role": m.role, "content": m.content} for m in sliced]

    def _persist_chat_exchange(
        self,
        db: Optional[Session],
        user_id: Optional[int],
        query: str,
        answer: str,
        conversation_id: Optional[int],
    ) -> Optional[int]:
        """Guarda mensaje del usuario y respuesta del mentor."""
        if not db or not user_id:
            return conversation_id

        try:
            conversation = None
            if conversation_id:
                conversation = (
                    db.query(ChatConversation)
                    .filter(
                        ChatConversation.id == conversation_id,
                        ChatConversation.user_id == user_id,
                    )
                    .first()
                )

            if not conversation:
                conversation = ChatConversation(
                    user_id=user_id,
                    title=self._conversation_title_from_query(query),
                )
                db.add(conversation)
                db.flush()  # Necesitamos el ID para mensajes

            convo_id = conversation.id

            db.add(
                ChatMessage(
                    conversation_id=convo_id,
                    role="user",
                    content=query,
                )
            )
            db.add(
                ChatMessage(
                    conversation_id=convo_id,
                    role="assistant",
                    content=answer,
                )
            )

            db.commit()
            db.refresh(conversation)
            return convo_id
        except Exception:
            if db:
                db.rollback()
            logger.exception("Error al persistir conversación del mentor")
            return conversation_id

    async def _extract_search_keywords(self, query: str) -> str:
        """
        Extrae keywords/frases relevantes de la query del usuario usando gpt-4o-mini.
        
        Objetivo: Limpiar ruido conversacional para mejorar la búsqueda vectorial.
        
        Ejemplos:
        - Input: "hola soy pablito, estoy estudiando y no se como saludar en la lengua bora"
          Output: "como saludar"
        
        - Input: "oye amigo, necesito saber como se dice casa en bora"
          Output: "como se dice casa"
        
        - Input: "como se dice abrigar en bora"
          Output: "como se dice abrigar"
        
        Args:
            query: Query original del usuario con posible ruido conversacional
            
        Returns:
            String limpio con keywords/frases clave para búsqueda vectorial
        """
        # Si el preprocesamiento está deshabilitado, retornar query original
        if not settings.ENABLE_QUERY_PREPROCESSING:
            logger.debug("Query preprocessing deshabilitado en settings, usando query original")
            return query
        
        if not self.openai_adapter:
            # Fallback: retornar query original si OpenAI no está disponible
            logger.warning("OpenAI adapter no disponible para keyword extraction, usando query original")
            return query
        
        try:
            # Prompt especializado para extracción de keywords de traducción
            extraction_prompt = f"""Eres un asistente experto en análisis de consultas de traducción Español-Bora.

Tu tarea: Extraer los términos clave para búsqueda semántica, eliminando ruido conversacional pero preservando contexto semántico importante.

Reglas:
1. Extrae palabras/frases que necesitan traducción
2. Elimina: saludos, presentaciones, muletillas ("hola", "oye", "soy X")
3. Preserva: verbos, sustantivos, adjetivos, contexto semántico
4. Si la consulta ya es directa, devuélvela sin cambios
5. Responde SOLO con los términos clave, sin explicaciones

Ejemplos:
Usuario: "hola soy pablito, estoy estudiando y no se como saludar en la lengua bora"
Asistente: como saludar

Usuario: "oye amigo, necesito saber como se dice casa en bora"
Asistente: como se dice casa

Usuario: "estoy en clase y me preguntaron como se dice buenos dias en bora"
Asistente: como se dice buenos dias

Usuario: "que significa áábukɨ en español"
Asistente: que significa áábukɨ

Usuario: "como digo yo soy estudiante en bora"
Asistente: yo soy estudiante

Usuario: "como se dice abrigar en bora"
Asistente: como se dice abrigar

Usuario: "abrigar"
Asistente: abrigar

Ahora extrae de esta consulta:
Usuario: {query}
Asistente:"""

            # Llamar a gpt-4o-mini con temperatura baja para consistencia
            response = await self.openai_adapter.chat_completion(
                messages=[{"role": "user", "content": extraction_prompt}],
                temperature=0.2,  # Temperatura ligeramente más alta para flexibilidad
                max_tokens=100,    # Permitir frases más largas con contexto
            )
            
            extracted = response.strip()
            
            # Validación básica: si la extracción está vacía o es muy larga, usar original
            if not extracted or len(extracted) > len(query) * 1.5:
                logger.warning(f"Keyword extraction inválida: '{extracted}', usando query original")
                return query
            
            logger.info(f"🔍 Query preprocessing | Original: '{query}' → Cleaned: '{extracted}'")
            return extracted
            
        except Exception as e:
            logger.error(f"Error en keyword extraction: {e}", exc_info=True)
            return query  # Fallback seguro
        
        if self.openai_adapter and settings.OPENAI_API_KEY:
            logger.info(f"✓ RAGService configurado para usar OpenAI ({settings.OPENAI_MODEL}) con fallback local")
        else:
            logger.info("RAGService usando adaptador LLM local únicamente")

    # ==========================================
    # LEXICON: búsqueda semántica + respuesta RAG
    # ==========================================

    async def _detect_query_direction(self, query: str) -> Optional[str]:
        """
        Detecta la dirección de traducción del query usando LLM.
        
        Ejemplos:
        - "Como se dice cantar en bora" → 'es_bora' (español a Bora)
        - "Que significa majtsíva" → 'bora_es' (Bora a español)
        - "cantar" → None (ambiguo, buscar en ambas direcciones)
        
        Returns:
            'es_bora': Query en español buscando traducción al Bora
            'bora_es': Query en Bora buscando traducción al español
            None: Ambiguo o no se puede determinar
        """
        # Si el preprocesamiento está deshabilitado, no detectar dirección
        if not settings.ENABLE_QUERY_PREPROCESSING:
            logger.debug("Query preprocessing deshabilitado, sin detección de dirección")
            return None
        
        if not self.openai_adapter:
            logger.warning("OpenAI adapter no disponible para detección de dirección")
            return None
        
        try:
            detection_prompt = f"""Eres un clasificador de consultas de traducción Español-Bora.

Tu tarea: Determinar la DIRECCIÓN de la traducción que el usuario necesita.

Opciones:
- ES_BORA: Usuario tiene palabra/frase en ESPAÑOL y busca traducción al BORA
- BORA_ES: Usuario tiene palabra/frase en BORA y busca traducción al ESPAÑOL
- AMBIGUO: No se puede determinar la dirección con certeza

Señales para ES_BORA:
- "como se dice X en bora"
- "como digo X en bora"
- "traducir X al bora"
- Palabra claramente española: "cantar", "casa", "buenos dias"

Señales para BORA_ES:
- "que significa X"
- "que quiere decir X"
- "traducir X al español"
- Palabra con caracteres Bora: "majtsíva", "áábukɨ", "tsʉ́bɨ"
- Palabras con diacríticos: ɨ, ́, ʉ

Ejemplos:
Query: "como se dice cantar en bora"
Respuesta: ES_BORA

Query: "que significa majtsíva"
Respuesta: BORA_ES

Query: "áábukɨ"
Respuesta: BORA_ES

Query: "cantar"
Respuesta: AMBIGUO

Query: "como digo buenos dias en bora"
Respuesta: ES_BORA

Query: "traducir tsʉ́bɨ al español"
Respuesta: BORA_ES

Ahora clasifica esta consulta (responde SOLO: ES_BORA, BORA_ES, o AMBIGUO):
Query: {query}
Respuesta:"""

            response = await self.openai_adapter.chat_completion(
                messages=[{"role": "user", "content": detection_prompt}],
                temperature=0.0,
                max_tokens=10,
            )
            
            detected = response.strip().upper()
            
            # Mapear respuesta a valores internos
            if detected == "ES_BORA":
                logger.info(f"🧭 Dirección detectada: ES→Bora para query '{query}'")
                return "es_bora"
            elif detected == "BORA_ES":
                logger.info(f"🧭 Dirección detectada: Bora→ES para query '{query}'")
                return "bora_es"
            else:
                logger.info(f"🧭 Dirección ambigua para query '{query}', buscando en ambas")
                return None
            
        except Exception as e:
            logger.error(f"Error en detección de dirección: {e}", exc_info=True)
            return None

    async def search_lexicon(
        self,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.7,
        category: Optional[str] = None,
        direction: Optional[str] = None,  # ✅ NUEVO: 'es_bora', 'bora_es', o None
    ) -> List[Dict[str, Any]]:
        """Busca en el lexicón usando match_bora_docs (unificado) y filtra por similitud mínima."""
        emb = self.hf_adapter.generate_embedding(query)
        if not emb:
            return []
        
        # NO auto-detectar dirección - siempre buscar en AMBAS direcciones
        # Esto asegura que el vector search retorne los top_k resultados más similares
        # sin filtrar por dirección (mejor recall)
        
        results = await self.supabase_adapter.vector_search_bora_docs(
            query_embedding=emb,
            top_k=top_k,
            kinds=None,  # ['lemma','subentry','example']
            pos_full=category,
            min_similarity=min_similarity,
            direction=None,  # ✅ SIEMPRE None para buscar en ambas direcciones
        )
        # match_bora_docs ya aplica el threshold; devolvemos tal cual
        return results or []

    async def answer_with_lexicon(
        self,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.7,
        category: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        fast: bool = False,
        db: Optional[Session] = None,
        user_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
        persist: bool = False,
        history_limit: int = 6,
    ) -> Dict[str, Any]:
        """Pipeline RAG unificado: retrieve (con boost por lemma exacto) -> prompt -> LLM."""
        t0 = time.perf_counter()
        timings: Dict[str, float] = {}
        counters: Dict[str, int] = {}

        if conversation_history is None and db and conversation_id:
            conversation_history = self._fetch_conversation_history_from_db(
                db, conversation_id, history_limit
            )

        use_cache = not (conversation_history or conversation_id or persist)
        cache_key: Optional[str] = None
        now = time.time()

        # 0) Cache lookup
        if use_cache:
            cache_key = _make_lexicon_cache_key(query, top_k, min_similarity, category, fast)
            cached = _lexicon_cache.get(cache_key)
            if cached and cached[0] > now:
                result = cached[1]
                result = dict(result)
                t_elapsed = (time.perf_counter() - t0) * 1000.0
                ts = dict(result.get("timings", {}))
                ts["cache_hit_ms"] = t_elapsed
                result["timings"] = ts
                return result

        # 1) Preprocesar query para extraer keywords/frases clave (mejora búsqueda vectorial)
        t_prep0 = time.perf_counter()
        cleaned_query = await self._extract_search_keywords(query)
        timings["preprocessing_ms"] = (time.perf_counter() - t_prep0) * 1000.0
        
        # 1.5) Detectar dirección de traducción del query (solo para logging, NO para filtrar)
        t_dir0 = time.perf_counter()
        detected_direction = await self._detect_query_direction(query)
        timings["direction_detection_ms"] = (time.perf_counter() - t_dir0) * 1000.0
        logger.info(f"🧭 Dirección detectada (informativo): {detected_direction}")
        
        # 2) Embedding de la query LIMPIA (no la original)
        t_emb0 = time.perf_counter()
        emb = self.hf_adapter.generate_embedding(cleaned_query)
        timings["embedding_ms"] = (time.perf_counter() - t_emb0) * 1000.0
        if not emb:
            timings["total_ms"] = (time.perf_counter() - t0) * 1000.0
            logger.info("⏱️ Timings RAG (falló embedding) | %s", timings)
            return {"answer": "", "response": "", "results": [], "timings": timings, "counters": counters}

        t_vs0 = time.perf_counter()
        # Reducir top_k en modo rápido para acotar latencia en la recuperación
        effective_top_k = top_k if not fast else min(top_k, 6)

        hits = await self.supabase_adapter.vector_search_bora_docs(
            query_embedding=emb,
            top_k=effective_top_k,
            kinds=None,
            pos_full=category,
            min_similarity=min_similarity,
            direction=None,  # ✅ SIEMPRE None - buscar en AMBAS direcciones (mejor recall)
        )
        hits = hits or []
        timings["vector_search_ms"] = (time.perf_counter() - t_vs0) * 1000.0

        # Boost si el query coincide exactamente con un lemma (case-sensitive)
        t_lemq0 = time.perf_counter()
        lemma_row = await self.supabase_adapter.find_lemma_by_text(query)
        timings["lemma_lookup_ms"] = (time.perf_counter() - t_lemq0) * 1000.0
        if lemma_row:
            # Determinar la traducción correcta según dirección
            direction = lemma_row.get('direction', 'bora_es')
            translation = (
                lemma_row.get('gloss_bora') if direction == 'es_bora' 
                else lemma_row.get('gloss_es')
            )
            
            boosted = {
                'id': -1,
                'kind': 'lemma',
                'parent_lemma_id': lemma_row['id'],
                'subentry_id': None,
                'example_id': None,
                'lemma': lemma_row['lemma'],
                'pos_full': lemma_row.get('pos_full'),
                'bora_text': None,
                'spanish_text': None,
                'gloss_es': lemma_row.get('gloss_es'),
                'gloss_bora': lemma_row.get('gloss_bora'),
                'direction': direction,
                'translation': translation,  # Helper field
                'similarity': 1.0,  # fuerza al top
            }
            # Evitar duplicado del mismo lemma si ya está
            if not any(h.get('kind') == 'lemma' and h.get('lemma') == boosted['lemma'] for h in hits):
                hits = [boosted] + hits
        hits = hits[:top_k]

        # Agrupar por lemma y tomar ejemplos de apoyo
        groups: Dict[str, Dict[str, Any]] = {}
        for h in hits:
            lemma = h.get('lemma') or ''
            # Determinar traducción según dirección
            direction = h.get('direction', 'bora_es')
            translation = (
                h.get('gloss_bora') if direction == 'es_bora'
                else h.get('gloss_es')
            )
            
            g = groups.setdefault(lemma, {
                'lemma': lemma,
                'pos_full': h.get('pos_full'),
                'gloss_es': h.get('gloss_es'),
                'gloss_bora': h.get('gloss_bora'),
                'direction': direction,
                'translation': translation,  # Campo helper con la traducción correcta
                'best_similarity': h.get('similarity', 0.0),
                'items': [],
                'examples': [],
            })
            g['best_similarity'] = max(g['best_similarity'], h.get('similarity', 0.0))
            g['items'].append(h)

        counters["hits_count"] = len(hits)
        counters["groups_count"] = len(groups)

        # Traer hasta 3 ejemplos por lemma (si no vinieron ya como hits)
        # En modo rápido, omitimos llamadas adicionales para ejemplos
        examples_api_calls = 0
        examples_total = 0
        t_examples_total0 = time.perf_counter()
        for lemma, g in groups.items():
            examples = [
                {'bora': it.get('bora_text'), 'es': it.get('spanish_text')}
                for it in g['items'] if it.get('kind') == 'example' and it.get('bora_text') and it.get('spanish_text')
            ]
            if not fast and len(examples) < 3:
                # Buscar por lemma exacto solo si no estamos en modo rápido
                lemma_row = await self.supabase_adapter.find_lemma_by_text(lemma)
                if lemma_row:
                    t_ex0 = time.perf_counter()
                    ex_rows = await self.supabase_adapter.get_examples_by_lemma_id(lemma_row['id'], limit=3-len(examples))
                    timings.setdefault("examples_fetch_detail", 0.0)
                    timings["examples_fetch_detail"] += (time.perf_counter() - t_ex0) * 1000.0
                    examples_api_calls += 1
                    for er in ex_rows:
                        examples.append({'bora': er.get('bora_text'), 'es': er.get('spanish_text')})
            # En modo rápido, nos quedamos solo con los ejemplos ya presentes en hits
            g['examples'] = examples[: (1 if fast else 3)]
            examples_total += len(g['examples'])
        timings["examples_fetch_ms"] = (time.perf_counter() - t_examples_total0) * 1000.0
        counters["examples_api_calls"] = examples_api_calls
        counters["examples_returned_total"] = examples_total

        # Construir contexto interno (solo para el LLM). No debe ser repetido en la respuesta.
        # Ordenar grupos por similitud
        t_ctx0 = time.perf_counter()
        ordered = sorted(groups.values(), key=lambda x: x['best_similarity'], reverse=True)
        context_lines: List[str] = ["[CONTEXTO (no lo repitas en la respuesta)]"]
        for i, g in enumerate(ordered, 1):
            sim = g['best_similarity']
            # Mostrar traducción según dirección del diccionario
            direction = g.get('direction', 'bora_es')
            translation = g.get('translation') or ''
            
            # Formato adaptado según dirección
            if direction == 'es_bora':
                # ES→Bora: lemma es español, traducción es Bora
                line = f"{i}. [Lemma ES→Bora | sim {sim:.2f}] {g['lemma']} — DEF_BORA: {translation} — POS: {g.get('pos_full') or ''}"
            else:
                # Bora→ES: lemma es Bora, traducción es español (default)
                line = f"{i}. [Lemma | sim {sim:.2f}] {g['lemma']} — DEF_ES: {translation} — POS: {g.get('pos_full') or ''}"
            
            context_lines.append(line)
            for ex in g['examples']:
                context_lines.append(f"   • Ejemplo: BORA: \"{ex['bora']}\" — ES: \"{ex['es']}\"")
        context = "\n".join(context_lines) if len(context_lines) > 1 else "No se encontró información relevante."
        timings["context_build_ms"] = (time.perf_counter() - t_ctx0) * 1000.0

        # Generar respuesta con el LLM existente
        t_llm0 = time.perf_counter()
        # Reducir presupuesto de salida en modo rápido para acelerar la respuesta del modelo
        fast_max_tokens = min(getattr(settings, "OPENAI_MAX_TOKENS", 500), 220) if fast else None
        answer = await self.generate_response(
            query=query,
            context=context,
            conversation_history=conversation_history,
            response_max_tokens=fast_max_tokens,
        )
        timings["llm_ms"] = (time.perf_counter() - t_llm0) * 1000.0
        timings["total_ms"] = (time.perf_counter() - t0) * 1000.0

        logger.info(
            "⏱️ Timings RAG | total=%.0fms prep=%.0fms emb=%.0fms vs=%.0fms lemma=%.0fms ex=%.0fms ctx=%.0fms llm=%.0fms | hits=%d groups=%d ex_calls=%d ex_total=%d",
            timings.get("total_ms", 0.0),
            timings.get("preprocessing_ms", 0.0),
            timings.get("embedding_ms", 0.0),
            timings.get("vector_search_ms", 0.0),
            timings.get("lemma_lookup_ms", 0.0),
            timings.get("examples_fetch_ms", 0.0),
            timings.get("context_build_ms", 0.0),
            timings.get("llm_ms", 0.0),
            counters.get("hits_count", 0),
            counters.get("groups_count", 0),
            counters.get("examples_api_calls", 0),
            counters.get("examples_returned_total", 0),
        )

        # Devolvemos ambas claves por compatibilidad retro (algunas vistas usan "response")
        result = {
            "answer": answer,
            "response": answer,
            "results": hits,
            "timings": timings,
            "counters": counters,
            "conversation_id": conversation_id,
        }

        if persist:
            if not db or not user_id:
                logger.warning("Persistencia de chat solicitada sin db/user_id")
            else:
                stored_conversation_id = self._persist_chat_exchange(
                    db=db,
                    user_id=user_id,
                    query=query,
                    answer=answer,
                    conversation_id=conversation_id,
                )
                if stored_conversation_id:
                    conversation_id = stored_conversation_id
                    result["conversation_id"] = stored_conversation_id

        # Guardar en cache
        if use_cache and cache_key:
            _lexicon_cache[cache_key] = (now + _CACHE_TTL_SECONDS, result)

        return result

    # ==========================================
    # INGESTA DE CORPUS DESDE salida.json
    # ==========================================

    def _normalize_category(self, entry: Dict[str, Any]) -> str:
        return entry.get('pos_full') or entry.get('pos') or 'Diccionario'

    def _extract_examples(self, entry: Dict[str, Any]) -> List[Dict[str, str]]:
        examples: List[Dict[str, str]] = []
        for ex in entry.get('examples', []) or []:
            bora = (ex.get('bora') or '').strip()
            es = (ex.get('es') or '').strip()
            if bora and es:
                examples.append({'bora': bora, 'es': es})
        for sub in entry.get('subentries', []) or []:
            for ex in sub.get('examples', []) or []:
                bora = (ex.get('bora') or '').strip()
                es = (ex.get('es') or '').strip()
                if bora and es:
                    examples.append({'bora': bora, 'es': es})
        return examples

    def _build_phrase_rows(self, entry: Dict[str, Any]) -> List[Dict[str, Any]]:
        category = self._normalize_category(entry)
        rows: List[Dict[str, Any]] = []
        for ex in self._extract_examples(entry):
            rows.append({
                'bora_text': ex['bora'],
                'spanish_text': ex['es'],
                'category': category,
                'difficulty': 1,
                'usage_context': None,
                'pronunciation_guide': None,
            })
        return rows

    def ingest_from_salida_json(self, file_path: str) -> Dict[str, int]:
        """
        Ingesta del archivo salida.json: crea frases y embeddings en Supabase.

        Nota: usa el adaptador híbrido de HuggingFace a través del wrapper de RAG,
        y el adaptador de Supabase. Está diseñado para ejecutarse puntualmente.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {path}")

        with path.open('r', encoding='utf-8') as f:
            data = json.load(f)

        inserted = 0
        skipped = 0
        embedded = 0

        for entry in data:
            rows = self._build_phrase_rows(entry)
            for row in rows:
                # Evitar duplicados por textos
                existing = self.supabase_adapter.find_phrase_by_texts(row['bora_text'], row['spanish_text'])
                # Métodos del adaptador son async por firma pero síncronos internamente: llamamos directo
                if isinstance(existing, dict) and existing:
                    phrase_id = existing['id']
                    skipped += 1
                else:
                    created = self.supabase_adapter.insert_phrase(row)
                    if isinstance(created, dict) and created:
                        phrase_id = created['id']
                        inserted += 1
                    else:
                        continue

                # Embeddings
                has_emb = self.supabase_adapter.has_embedding(phrase_id)
                if has_emb:
                    continue
                text_for_embedding = f"{row['spanish_text']} — Bora: {row['bora_text']} — {row['category']}"
                emb = self.hf_adapter.generate_embedding(text_for_embedding)
                if not emb:
                    continue
                meta = {
                    'source': 'salida.json',
                    'category': row['category'],
                    'lemma': entry.get('lemma'),
                    'page': entry.get('page'),
                }
                ok = self.supabase_adapter.store_embedding(phrase_id, emb, meta)
                if ok:
                    embedded += 1

        return {"inserted": inserted, "skipped": skipped, "embedded": embedded}
    
    # ==========================================
    # BÚSQUEDA Y RECUPERACIÓN
    # ==========================================
    
    async def search_similar_phrases(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Busca frases similares usando búsqueda vectorial
        
        Args:
            query: Consulta del usuario
            category: Filtro opcional por categoría
            top_k: Número de resultados
        
        Returns:
            Lista de frases similares con scores
        """
        # Generar embedding de la consulta
        query_embedding = self.hf_adapter.generate_embedding(query)
        
        if not query_embedding:
            logger.error("No se pudo generar embedding de la consulta")
            return []
        
        # Buscar en Supabase con pgvector
        if self.supabase_adapter.is_connected():
            results = await self.supabase_adapter.vector_search(
                query_embedding=query_embedding,
                top_k=top_k,
                category=category
            )
            return results
        
        # Fallback: buscar en BD local (SQLite)
        # TODO: Implementar búsqueda local si Supabase no está disponible
        logger.warning("Supabase no disponible, usando búsqueda local")
        return []
    
    async def get_context_from_phrases(
        self,
        phrases: List[Dict]
    ) -> str:
        """
        Construye contexto a partir de frases recuperadas
        
        Args:
            phrases: Lista de frases del corpus
        
        Returns:
            Texto de contexto formateado
        """
        if not phrases:
            return "No se encontró información relevante en el corpus Bora."
        
        context_parts = []
        for i, phrase in enumerate(phrases, 1):
            bora = phrase.get('bora_text', '')
            spanish = phrase.get('spanish_text', '')
            category = phrase.get('category', '')
            
            context_parts.append(
                f"{i}. [{category}] Bora: \"{bora}\" - Español: \"{spanish}\""
            )
        
        return "\n".join(context_parts)
    
    # ==========================================
    # GENERACIÓN DE RESPUESTAS
    # ==========================================
    
    async def generate_response(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None,
        response_max_tokens: Optional[int] = None,
    ) -> str:
        """
        Genera respuesta usando LLM con contexto

        Estrategia (configurable por settings):
        - Si settings.LLM_PROVIDER == 'openai': usar OpenAI. Si falla y
          settings.ALLOW_HF_LLM_FALLBACK es False, lanzar excepción.
          Si ALLOW_HF_LLM_FALLBACK es True, intentar Hugging Face (API).
        - Si settings.LLM_PROVIDER == 'huggingface': usar Hugging Face (API).

        Args:
            query: Pregunta del usuario
            context: Contexto de frases recuperadas
            conversation_history: Historial previo de conversación

        Returns:
            Respuesta generada
        """
        # Construir mensajes (system + user) para mejorar obediencia al estilo
        messages = self._build_messages(query, context, conversation_history)

        response = None

        provider = getattr(settings, "LLM_PROVIDER", "openai").lower()
        # Permite reducir tokens de salida en modo rápido
        max_tokens_override = response_max_tokens if (response_max_tokens and response_max_tokens > 0) else None

        if provider == "openai":
            # OpenAI como proveedor principal
            if self.openai_adapter and settings.OPENAI_API_KEY:
                try:
                    logger.info(f"🤖 Generando respuesta con OpenAI ({settings.OPENAI_MODEL})...")
                    response = await self.openai_adapter.chat_completion(
                        messages=messages,
                        temperature=settings.OPENAI_TEMPERATURE,
                        max_tokens=(max_tokens_override or settings.OPENAI_MAX_TOKENS)
                    )
                    logger.info("✓ Respuesta generada con OpenAI")
                except Exception as e:
                    logger.error(f"❌ OpenAI falló: {e}")
                    # ¿Permitir fallback a HF?
                    if getattr(settings, "ALLOW_HF_LLM_FALLBACK", False):
                        logger.info("🔁 Intentando con Hugging Face (Inference API) como fallback...")
                        response = self.hf_adapter.chat_completion(
                            messages=messages,
                            max_tokens=(max_tokens_override or getattr(settings, "LLM_MAX_NEW_TOKENS", 320)),
                        )
                    else:
                        # Modo estricto: fallar inmediatamente
                        raise RuntimeError("LLM (OpenAI) no disponible y fallback deshabilitado")
            else:
                # OpenAI no configurado
                if getattr(settings, "ALLOW_HF_LLM_FALLBACK", False):
                    logger.info("🔁 OpenAI no configurado. Usando Hugging Face (Inference API) como fallback...")
                    response = self.hf_adapter.chat_completion(
                        messages=messages,
                        max_tokens=(max_tokens_override or getattr(settings, "LLM_MAX_NEW_TOKENS", 320)),
                    )
                else:
                    raise RuntimeError("OpenAI no configurado y fallback deshabilitado")

        elif provider == "huggingface":
            # Usar directamente Hugging Face (Inference API)
            logger.info("🤖 Generando respuesta con Hugging Face (Inference API)...")
            response = self.hf_adapter.chat_completion(
                messages=messages,
                max_tokens=(max_tokens_override or getattr(settings, "LLM_MAX_NEW_TOKENS", 320)),
            )
        else:
            raise ValueError(f"LLM_PROVIDER no soportado: {provider}")

        if not response:
            # Si llegamos aquí sin respuesta, entregar fallback simple (mensaje educativo)
            return self._generate_fallback_response(context)

        # Post-procesar para asegurar estilo mentor (sin encabezados/listas/eco del contexto)
        final_text = self._post_process_mentor_response(response)

        # Asegurar que nunca devolvemos vacío al frontend
        if not final_text or not final_text.strip():
            return self._generate_fallback_response(context)

        return final_text
    
    def _build_prompt(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Construye prompt para el LLM

        Template del prompt adaptado al idioma Bora (mentoring style)
        """
        prompt_template = """Eres el Mentor Bora, un profesor paciente y cercano del idioma Bora (Amazonía peruana).

Tu objetivo:
- Responder SOLO con información presente en el CONTEXTO.
- Hablar en español claro y cálido, en 5–8 líneas máximo.
- Usar la mejor información disponible: traducción literal si existe, o la aproximación más cercana.
- Complementar con 1–2 ejemplos de uso cuando sea útil para el entendimiento.
- Si hay varias opciones, menciona la más pertinente y, al final, 1–2 alternativas.
- No inventes datos. Si falta información, dilo y sugiere cómo afinar la consulta.

Reglas de estilo:
- NO copies ni cites el bloque de CONTEXTO; úsalo solo como referencia.
- Evita encabezados o listas numeradas (no incluyas "Entradas relevantes" ni bullets).
- Escribe en párrafos cortos, sin viñetas.
- Sé ADAPTATIVO: si encuentras traducción literal (DEF_BORA/DEF_ES), úsala primero; si solo encuentras aproximaciones o ejemplos, úsalos como mejor opción disponible.

CONTEXTO:
{context}

{history}

Pregunta del estudiante: {query}

Responde en un solo bloque de texto usando la mejor información del CONTEXTO: si hay traducción literal, úsala primero (ejemplo: "En bora, 'abrazar' se dice 'ámabúcu' o 'chiááve'"); si solo hay aproximaciones o ejemplos, úsalos como mejor opción. Luego 1 ejemplo de uso, y una nota breve si aplica."""
        
        # Agregar historial si existe
        history_text = ""
        if conversation_history:
            history_parts = []
            for msg in conversation_history[-3:]:  # Últimos 3 mensajes
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                history_parts.append(f"{role.capitalize()}: {content}")
            history_text = "Historial de conversación:\n" + "\n".join(history_parts)
        
        return prompt_template.format(
            context=context,
            history=history_text,
            query=query
        )

    def _build_messages(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> List[Dict[str, str]]:
        """Construye mensajes con rol system+user para usar chat_completion."""
        system = (
            "Eres el Mentor Bora, un profesor amable y cercano que enseña el idioma Bora (lengua indígena amazónica) a hispanohablantes.\n\n"
            
            "Tu misión:\n"
            "- Responder de forma conversacional, clara y educativa (150-200 palabras máximo)\n"
            "- Usar SOLO información del CONTEXTO proporcionado - nunca inventes datos\n"
            "- Ayudar con: traducciones Bora-Español, definiciones, ejemplos de uso, pronunciación básica\n\n"
            
            "Reglas importantes:\n"
            "- Usa la MEJOR información disponible del CONTEXTO: traducción literal si existe, o la aproximación más cercana\n"
            "- Responde directamente a la pregunta del estudiante con un tono cálido y motivador\n"
            "- Explica el por qué cuando sea relevante (etimología, contexto cultural, diferencias con sinónimos)\n"
            "- Incluye 1-2 ejemplos prácticos en Bora con su traducción al español cuando ayuden al entendimiento\n"
            "- Si el contexto es insuficiente, sé honesto pero ofrece alternativas relacionadas\n"
            "- Escribe en párrafos naturales (NO uses formato tipo formulario o secciones rígidas)\n"
            "- Evita términos técnicos innecesarios - habla como un maestro, no como un diccionario\n\n"
            
            "Formato de respuesta ADAPTATIVO:\n"
            "1. Si hay traducción literal → úsala primero (ej: 'En bora, abrazar se dice ámabúcu o chiááve')\n"
            "2. Si solo hay aproximaciones o ejemplos → úsalos como mejor opción disponible\n"
            "3. Explica el contexto o significado si es relevante\n"
            "4. Da ejemplos prácticos cuando clarifiquen el uso\n"
            "5. Agrega un consejo o nota cultural si es relevante\n\n"
            
            "Ejemplo de buen estilo:\n"
            "Claro! Para saludar en Bora puedes decir 'a uúj' cuando llegas. Esta palabra significa 'hola' en general. Por ejemplo: ' ¿A aabye uúj; kiávú u pééhií?' significa 'Hola amigo, ¿a dónde vas?'. Los Bora valoran mucho los saludos al encontrarse, así que es una excelente forma de iniciar cualquier conversación.\n\n"
            
            "NUNCA uses estos formatos rígidos:\n"
            "- Respuesta: ...\n"
            "- Por qué: ...\n"
            "- Confianza: Alta o Baja\n"
            "- Citas: ...\n"
            "Simplemente responde de forma natural y conversacional.\n\n"
            
            "Recibirás:\n"
            "- query: La pregunta del estudiante\n"
            "- context: Información del lexicón Bora (usa esto como referencia, pero no lo copies literalmente)"
        )
        # Historial breve opcional
        history_parts: List[Dict[str, str]] = []
        if conversation_history:
            for msg in conversation_history[-3:]:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                history_parts.append({'role': role, 'content': content})

        user = (
            f"<query>{query}</query>\n"
            f"<context>\n{context}\n</context>"
        )
        return [{'role': 'system', 'content': system}] + history_parts + [{'role': 'user', 'content': user}]

    def _post_process_mentor_response(self, text: str) -> str:
        """Limpia ecos del contexto pero conserva el formato de secciones solicitado."""
        if not text:
            return text
        lines = [l for l in text.splitlines() if l.strip()]
        cleaned: List[str] = []
        import re
        for l in lines:
            ls = l.strip()
            # Filtrar ecos típicos
            if ls.startswith('[CONTEXTO') or 'Entradas relevantes' in ls:
                continue
            # Filtrar líneas que parezcan ser el listado crudo del contexto
            if re.match(r'^\d+\.\s*\[Lemma\b', ls):
                continue
            cleaned.append(ls)
        # Conservar saltos de línea para las secciones (Respuesta/Por qué/Ejemplo/Citas/Confianza)
        return "\n".join(cleaned)
    
    def _generate_fallback_response(self, context: str) -> str:
        """Genera una respuesta útil a partir del contexto cuando el LLM falla."""
        if not context or context.strip().lower().startswith("no se encontró"):
            return "No encontré suficiente información en el corpus para responder. Intenta con otra forma de preguntar o con palabras más simples."

        # Intentar extraer hasta 3 mejores coincidencias del contexto
        import re
        lines = [l.strip() for l in context.splitlines() if l.strip()]
        picks = []
        for line in lines:
            # Formato esperado: 1. [Categoria | sim 0.85] Bora: "..." - Español: "..."
            m = re.search(r'Bora:\s*"([^"]+)"\s*-\s*Español:\s*"([^"]+)"', line)
            if m:
                picks.append((m.group(1), m.group(2)))
            if len(picks) >= 3:
                break

        if not picks:
            return f"Encontré estas frases relevantes en Bora:\n\n{context}"

        bora, esp = picks[0]
        alts = picks[1:]
        alt_text = ""
        if alts:
            alt_pairs = ', '.join([f'"{b}" — "{e}"' for b, e in alts])
            alt_text = f"\n4) Alternativas: {alt_pairs}"

        return (
            f"1) Frase en Bora: {bora}\n"
            f"2) Traducción: {esp}\n"
            f"3) Cuándo usarla: Frase sugerida según similitud semántica con tu consulta." 
            f"{alt_text}"
        )
    
    # ==========================================
    # PIPELINE COMPLETO DE RAG
    # ==========================================
    
    async def process_query(
        self,
        db: Session,
        user_id: str,
        query: str,
        category: Optional[str] = None,
        conversation_id: Optional[int] = None
    ) -> Dict:
        """
        Procesa una consulta completa usando RAG
        
        Pipeline:
        1. Buscar frases similares
        2. Construir contexto
        3. Generar respuesta
        4. Guardar en historial
        5. Retornar respuesta + fuentes
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario
            query: Consulta del usuario
            category: Filtro opcional por categoría
            conversation_id: ID de conversación existente
        
        Returns:
            Dict con response, conversation_id, sources
        """
        try:
            # 1. Buscar frases similares
            similar_phrases = await self.search_similar_phrases(
                query=query,
                category=category,
                top_k=settings.TOP_K_RESULTS
            )
            
            # 2. Construir contexto
            context = await self.get_context_from_phrases(similar_phrases)
            
            # 3. Obtener historial si existe conversación
            conversation_history = []
            if conversation_id:
                conversation = db.query(ChatConversation).filter(
                    ChatConversation.id == conversation_id
                ).first()
                
                if conversation:
                    messages = db.query(ChatMessage).filter(
                        ChatMessage.conversation_id == conversation_id
                    ).order_by(ChatMessage.created_at).all()
                    
                    conversation_history = [
                        {"role": msg.role, "content": msg.content}
                        for msg in messages
                    ]
            
            # 4. Generar respuesta
            response_text = await self.generate_response(
                query=query,
                context=context,
                conversation_history=conversation_history
            )
            
            # 5. Guardar en historial
            if not conversation_id:
                # Crear nueva conversación
                new_conversation = ChatConversation(
                    user_id=user_id,
                    title=query[:50] + "..." if len(query) > 50 else query
                )
                db.add(new_conversation)
                db.commit()
                db.refresh(new_conversation)
                conversation_id = new_conversation.id
            
            # Guardar mensaje del usuario
            user_message = ChatMessage(
                conversation_id=conversation_id,
                role="user",
                content=query
            )
            db.add(user_message)
            
            # Guardar respuesta del asistente
            assistant_message = ChatMessage(
                conversation_id=conversation_id,
                role="assistant",
                content=response_text
            )
            db.add(assistant_message)
            
            db.commit()
            
            # 6. Retornar resultado
            return {
                "response": response_text,
                "conversation_id": conversation_id,
                "sources": similar_phrases
            }
            
        except Exception as e:
            logger.error(f"Error en pipeline RAG: {e}")
            raise


# Instancia global del servicio
rag_service = RAGService()


def get_rag_service() -> RAGService:
    """Función helper para obtener el servicio"""
    return rag_service

