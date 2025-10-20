from fastapi import APIRouter, Depends, Query
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from services.rag_service import RAGService
from config.database_connection import get_db

router = APIRouter(prefix="/api/lexicon", tags=["Lexicon"])


@router.get("/search")
async def search_lexicon(
    q: str = Query(..., description="Consulta del usuario"),
    top_k: int = Query(10, ge=1, le=50),
    min_similarity: float = Query(0.7, ge=0.0, le=1.0),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    service = RAGService()
    result = await service.answer_with_lexicon(
        query=q,
        top_k=top_k,
        min_similarity=min_similarity,
        category=category,
        conversation_history=None,
    )
    return result
