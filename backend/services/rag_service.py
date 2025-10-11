"""
Servicio RAG (Retrieval-Augmented Generation) para MIAPPBORA
Implementa el pipeline completo de RAG con Langchain
"""
from typing import List, Dict, Optional
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
            max_length=200,
            temperature=0.7
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
        
        Template del prompt adaptado al idioma Bora
        """
        prompt_template = """Eres un asistente experto en el idioma Bora, una lengua indígena de la Amazonía peruana.

Tu objetivo es ayudar a los usuarios a aprender frases cotidianas en Bora, explicando su uso y contexto.

Contexto relevante del corpus Bora:
{context}

{history}

Pregunta del usuario: {query}

Responde de manera clara y educativa, explicando:
1. La frase en Bora relevante
2. Su traducción al español
3. El contexto de uso apropiado
4. Ejemplos adicionales si es pertinente

Respuesta:"""
        
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
        """
        Genera respuesta básica cuando el LLM falla
        Simplemente retorna el contexto formateado
        """
        return f"Encontré estas frases relevantes en Bora:\n\n{context}"
    
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
