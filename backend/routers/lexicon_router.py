from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from services.rag_service import RAGService
from config.database_connection import get_db
from dependencies import get_current_user
from models.database import User, ChatConversation, ChatMessage

router = APIRouter(prefix="/lexicon", tags=["Lexicon"])


class LexiconChatRequest(BaseModel):
    q: str
    top_k: int = 10
    min_similarity: float = 0.7
    category: Optional[str] = None
    fast: bool = False
    conversation_id: Optional[int] = None


@router.get("/search")
async def search_lexicon(
    q: str = Query(..., description="Consulta del usuario"),
    top_k: int = Query(10, ge=1, le=50),
    min_similarity: float = Query(0.7, ge=0.0, le=1.0),
    category: Optional[str] = Query(None),
    fast: bool = Query(False, description="Modo rápido: menos contexto y respuesta más corta"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    service = RAGService()
    result = await service.answer_with_lexicon(
        query=q,
        top_k=top_k,
        min_similarity=min_similarity,
        category=category,
        conversation_history=None,
        fast=fast,
    )
    return result


@router.post("/chat")
async def chat_with_lexicon(
    payload: LexiconChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    service = RAGService()
    result = await service.answer_with_lexicon(
        query=payload.q,
        top_k=payload.top_k,
        min_similarity=payload.min_similarity,
        category=payload.category,
        conversation_history=None,
        fast=payload.fast,
        db=db,
        user_id=current_user.id,
        conversation_id=payload.conversation_id,
        persist=True,
    )
    return result


@router.get("/conversations/recent", response_model=List[Dict[str, Any]])
async def get_recent_conversations(
    limit: int = Query(10, ge=1, le=50, description="Número máximo de conversaciones a retornar"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Retorna las conversaciones recientes del usuario autenticado.

    Se usa para la sección "Conversaciones anteriores" del Mentor Bora.
    """
    # Obtener conversaciones del usuario, más recientes primero
    conversations = (
        db.query(ChatConversation)
        .filter(ChatConversation.user_id == current_user.id)
        .order_by(ChatConversation.updated_at.desc())
        .limit(limit)
        .all()
    )

    if not conversations:
        return []

    # Obtener último mensaje de cada conversación
    convo_ids = [c.id for c in conversations]

    last_messages_subquery = (
        db.query(
            ChatMessage.conversation_id,
            ChatMessage.content,
            ChatMessage.role,
            ChatMessage.created_at,
        )
        .filter(ChatMessage.conversation_id.in_(convo_ids))
        .order_by(ChatMessage.conversation_id, ChatMessage.created_at.desc())
    )

    # Construir diccionario con último mensaje por conversación
    last_message_by_convo: Dict[int, Dict[str, Any]] = {}
    for msg in last_messages_subquery:
        if msg.conversation_id not in last_message_by_convo:
            last_message_by_convo[msg.conversation_id] = {
                "content": msg.content,
                "role": msg.role,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            }

    # Armar respuesta
    result: List[Dict[str, Any]] = []
    for convo in conversations:
        last_msg = last_message_by_convo.get(convo.id)
        result.append(
            {
                "id": convo.id,
                "title": convo.title,
                "created_at": convo.created_at.isoformat() if convo.created_at else None,
                "updated_at": convo.updated_at.isoformat() if convo.updated_at else None,
                "last_message": last_msg,
            }
        )

    return result
