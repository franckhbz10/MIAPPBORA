"""
Servicio RAG (Retrieval-Augmented Generation) para MIAPPBORA
Implementa el pipeline completo de RAG con Langchain
"""
from typing import List, Dict, Optional, Any
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
from config.settings import settings
import logging
import json

logger = logging.getLogger(__name__)


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
        self.hf_adapter = get_huggingface_adapter()
        self.supabase_adapter = get_supabase_adapter()
        self.embeddings = CustomHuggingFaceEmbeddings()

    # ==========================================
    # LEXICON: búsqueda semántica + respuesta RAG
    # ==========================================

    async def search_lexicon(
        self,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.7,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Busca en el lexicón usando match_bora_docs (unificado) y filtra por similitud mínima."""
        emb = self.hf_adapter.generate_embedding(query)
        if not emb:
            return []
        results = await self.supabase_adapter.vector_search_bora_docs(
            query_embedding=emb,
            top_k=top_k,
            kinds=None,  # ['lemma','subentry','example']
            pos_full=category,
            min_similarity=min_similarity,
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
    ) -> Dict[str, Any]:
        """Pipeline RAG unificado: retrieve (con boost por lemma exacto) -> prompt -> LLM."""
        # Búsqueda semántica normal
        hits = await self.search_lexicon(query, top_k=top_k, min_similarity=min_similarity, category=category)

        # Boost si el query coincide exactamente con un lemma (case-sensitive)
        lemma_row = await self.supabase_adapter.find_lemma_by_text(query)
        if lemma_row:
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
                'gloss_es': lemma_row['gloss_es'],
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
            g = groups.setdefault(lemma, {
                'lemma': lemma,
                'pos_full': h.get('pos_full'),
                'gloss_es': h.get('gloss_es'),
                'best_similarity': h.get('similarity', 0.0),
                'items': [],
                'examples': [],
            })
            g['best_similarity'] = max(g['best_similarity'], h.get('similarity', 0.0))
            g['items'].append(h)

        # Traer hasta 3 ejemplos por lemma (si no vinieron ya como hits)
        for lemma, g in groups.items():
            # Si ya hay ejemplos en los hits, los usamos; sino pedimos a la BD
            examples = [
                {'bora': it.get('bora_text'), 'es': it.get('spanish_text')}
                for it in g['items'] if it.get('kind') == 'example' and it.get('bora_text') and it.get('spanish_text')
            ]
            if len(examples) < 3:
                # Buscar por lemma exacto
                lemma_row = await self.supabase_adapter.find_lemma_by_text(lemma)
                if lemma_row:
                    ex_rows = await self.supabase_adapter.get_examples_by_lemma_id(lemma_row['id'], limit=3-len(examples))
                    for er in ex_rows:
                        examples.append({'bora': er.get('bora_text'), 'es': er.get('spanish_text')})
            g['examples'] = examples[:3]

        # Construir contexto mentoring-friendly
        # Ordenar grupos por similitud
        ordered = sorted(groups.values(), key=lambda x: x['best_similarity'], reverse=True)
        context_lines: List[str] = ["Entradas relevantes:"]
        for i, g in enumerate(ordered, 1):
            sim = g['best_similarity']
            line = f"{i}. [Lemma | sim {sim:.2f}] {g['lemma']} — DEF_ES: {g.get('gloss_es') or ''} — POS: {g.get('pos_full') or ''}"
            context_lines.append(line)
            for ex in g['examples']:
                context_lines.append(f"   • Ejemplo: BORA: \"{ex['bora']}\" — ES: \"{ex['es']}\"")
        context = "\n".join(context_lines) if len(context_lines) > 1 else "No se encontró información relevante."

        # Generar respuesta con el LLM existente
        answer = await self.generate_response(query=query, context=context, conversation_history=conversation_history)
        return {"answer": answer, "results": hits}

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
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Genera respuesta usando LLM con contexto
        
        Args:
            query: Pregunta del usuario
            context: Contexto de frases recuperadas
            conversation_history: Historial previo de conversación
        
        Returns:
            Respuesta generada
        """
        # Construir prompt con contexto
        prompt = self._build_prompt(query, context, conversation_history)
        
        # Generar respuesta con HuggingFace LLM
        response = self.hf_adapter.generate_text(
            prompt=prompt,
            max_length=getattr(settings, "LLM_MAX_NEW_TOKENS", 320),
            temperature=getattr(settings, "LLM_TEMPERATURE", 0.4)
        )
        
        if not response:
            # Fallback a respuesta básica
            return self._generate_fallback_response(context)
        
        return response
    
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
        prompt_template = """Eres el Mentor Bora, un asistente experto en el idioma Bora (Amazonía peruana).

Objetivo:
- Responder a la consulta usando EXCLUSIVAMENTE la información del contexto.
- Ser claro, pedagógico y breve (máx. ~8 líneas), con foco en enseñar.

Contexto (agrupado por lemma con ejemplos):
{context}

Instrucciones de razonamiento:
- Si el usuario consulta por un lemma específico, explica su significado (gloss_es), categoría (POS) y comparte hasta 2–3 ejemplos.
- Si hay varios lemas cercanos, ordena por relevancia y menciona alternativas.
- No inventes traducciones ni definiciones; usa sólo lo que aparece en el contexto.
- Responde SIEMPRE en español y sin código.

Estructura sugerida:
• Definición: <lemma> — <gloss_es> (POS: <pos_full>)
• Ejemplos: "<bora_1>" — "<es_1>", "<bora_2>" — "<es_2>"
• Nota/uso: <breve orientación de uso si aplica>
• Alternativas (opcional): <lemma_alt_1> — <gloss_es_alt_1>

{history}

Pregunta del usuario: {query}

Ahora responde siguiendo la estructura sugerida. Si el contexto no tiene suficiente información, dilo explícitamente y sugiere cómo refinar la consulta."""
        
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
