"""
Router para gestión de feedback de la aplicación
Endpoints para crear, consultar y obtener estadísticas de feedback
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from models.database import AppFeedback, User
from schemas.schemas import (
    FeedbackCreate, 
    FeedbackResponse, 
    FeedbackStatsResponse
)
from config.database_connection import get_db
from dependencies import get_current_user

router = APIRouter(
    prefix="/feedback",
    tags=["feedback"]
)


@router.post("/submit", response_model=FeedbackResponse, status_code=status.HTTP_200_OK)
async def submit_feedback(
    feedback_data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crear o actualizar feedback del usuario
    - Awards +10 puntos por enviar feedback por primera vez
    - Permite actualizar feedback existente
    - Todos los campos son opcionales para permitir feedback parcial
    """
    # Buscar feedback existente del usuario
    existing_feedback = db.query(AppFeedback).filter(
        AppFeedback.user_id == current_user.id
    ).first()
    
    is_first_feedback = existing_feedback is None
    
    if existing_feedback:
        # Actualizar feedback existente (solo los campos proporcionados)
        if feedback_data.mentor_rating is not None:
            existing_feedback.mentor_rating = feedback_data.mentor_rating
        if feedback_data.games_rating is not None:
            existing_feedback.games_rating = feedback_data.games_rating
        if feedback_data.general_rating is not None:
            existing_feedback.general_rating = feedback_data.general_rating
        if feedback_data.comments is not None:
            existing_feedback.comments = feedback_data.comments
        
        db.commit()
        db.refresh(existing_feedback)
        
        print(f"✏️ Feedback actualizado para usuario {current_user.username}")
        
        return existing_feedback
    
    # Crear nuevo feedback
    new_feedback = AppFeedback(
        user_id=current_user.id,
        mentor_rating=feedback_data.mentor_rating,
        games_rating=feedback_data.games_rating,
        general_rating=feedback_data.general_rating,
        comments=feedback_data.comments
    )
    
    db.add(new_feedback)
    
    # Award +10 puntos por enviar feedback por primera vez
    if is_first_feedback:
        current_user.total_points += 10
        print(f"✅ Feedback creado para usuario {current_user.username} (+10 puntos)")
    
    db.commit()
    db.refresh(new_feedback)
    
    return new_feedback


@router.get("/my-feedback", response_model=Optional[FeedbackResponse])
async def get_my_feedback(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener el feedback del usuario actual
    Retorna None si no ha enviado feedback aún
    """
    feedback = db.query(AppFeedback).filter(
        AppFeedback.user_id == current_user.id
    ).first()
    
    return feedback


@router.get("/stats", response_model=FeedbackStatsResponse)
async def get_feedback_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener estadísticas agregadas de todos los feedbacks
    Solo disponible para usuarios autenticados
    """
    # Contar total de feedbacks
    total_feedbacks = db.query(func.count(AppFeedback.id)).scalar()
    
    if total_feedbacks == 0:
        return FeedbackStatsResponse(
            total_feedbacks=0,
            avg_mentor_rating=0.0,
            avg_games_rating=0.0,
            avg_general_rating=0.0,
            avg_overall_rating=0.0
        )
    
    # Calcular promedios (ignorando valores NULL)
    avg_mentor = db.query(func.avg(AppFeedback.mentor_rating)).scalar() or 0.0
    avg_games = db.query(func.avg(AppFeedback.games_rating)).scalar() or 0.0
    avg_general = db.query(func.avg(AppFeedback.general_rating)).scalar() or 0.0
    
    # Promedio general de los 3 ratings
    ratings = [r for r in [avg_mentor, avg_games, avg_general] if r > 0]
    avg_overall = sum(ratings) / len(ratings) if ratings else 0.0
    
    return FeedbackStatsResponse(
        total_feedbacks=total_feedbacks,
        avg_mentor_rating=round(avg_mentor, 2),
        avg_games_rating=round(avg_games, 2),
        avg_general_rating=round(avg_general, 2),
        avg_overall_rating=round(avg_overall, 2)
    )
