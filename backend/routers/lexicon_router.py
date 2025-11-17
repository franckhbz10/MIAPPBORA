from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from services.rag_service import RAGService
from config.database_connection import get_db
from dependencies import get_current_user
from models.database import User

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
