"""
Router de API para Minijuegos
Endpoints para gestionar sesiones, preguntas, respuestas y estadísticas
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from typing import List

from config.database_connection import get_db
from dependencies import get_current_user
from services.game_service import GameService
from schemas.schemas import (
    GameSessionCreate, GameSessionUpdate, GameSessionResponse,
    GameAnswerCreate, GameAnswerResponse, GameQuestionResponse,
    UserGameStats, GameAnswerSubmit
)
from models.database import User

router = APIRouter(prefix="/api/games", tags=["Games"])


@router.post("/session", status_code=status.HTTP_201_CREATED)
def create_game_session(
    session_data: GameSessionCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Crear nueva sesión de juego
    
    - **game_type**: Tipo de juego ('complete_phrase' o 'context_match')
    """
    try:
        game_service = GameService(db)
        session = game_service.create_session(
            user_id=current_user.id,
            game_type=session_data.game_type
        )
        # Retornar datos básicos sin la lista de answers
        return {
            "id": session.id,
            "user_id": session.user_id,
            "game_type": session.game_type,
            "total_questions": session.total_questions,
            "correct_answers": session.correct_answers,
            "incorrect_answers": session.incorrect_answers,
            "total_score": session.total_score,
            "is_perfect": session.is_perfect,
            "time_spent_seconds": session.time_spent_seconds,
            "completed_at": session.completed_at,
            "answers": []
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear sesión: {str(e)}"
        )


@router.put("/session/{session_id}")
def complete_game_session(
    session_id: int,
    update_data: GameSessionUpdate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Completar sesión de juego y actualizar estadísticas
    
    - **session_id**: ID de la sesión
    - **update_data**: Estadísticas finales de la sesión
    """
    try:
        game_service = GameService(db)
        session = game_service.complete_session(
            session_id=session_id,
            total_questions=update_data.total_questions,
            correct_answers=update_data.correct_answers,
            incorrect_answers=update_data.incorrect_answers,
            total_score=update_data.total_score,
            is_perfect=update_data.is_perfect,
            time_spent_seconds=update_data.time_spent_seconds
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sesión no encontrada"
            )
        
        # Verificar que la sesión pertenece al usuario actual
        if session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para actualizar esta sesión"
            )
        
        return {
            "id": session.id,
            "user_id": session.user_id,
            "game_type": session.game_type,
            "total_questions": session.total_questions,
            "correct_answers": session.correct_answers,
            "incorrect_answers": session.incorrect_answers,
            "total_score": session.total_score,
            "is_perfect": session.is_perfect,
            "time_spent_seconds": session.time_spent_seconds,
            "completed_at": session.completed_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al completar sesión: {str(e)}"
        )


@router.get("/session/{session_id}")
def get_game_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Obtener detalles de una sesión específica
    
    - **session_id**: ID de la sesión
    """
    try:
        from models.database import GameSession, GameAnswer
        
        session = db.query(GameSession).filter(GameSession.id == session_id).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sesión {session_id} no encontrada"
            )
        
        # Verificar que la sesión pertenece al usuario actual
        if session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver esta sesión"
            )
        
        # Cargar respuestas
        answers = db.query(GameAnswer).filter(GameAnswer.session_id == session_id).all()
        
        return {
            "id": session.id,
            "user_id": session.user_id,
            "game_type": session.game_type,
            "total_questions": session.total_questions,
            "correct_answers": session.correct_answers,
            "incorrect_answers": session.incorrect_answers,
            "total_score": session.total_score,
            "is_perfect": session.is_perfect,
            "time_spent_seconds": session.time_spent_seconds,
            "completed_at": session.completed_at,
            "answers": [
                {
                    "id": a.id,
                    "session_id": a.session_id,
                    "phrase_id": a.phrase_id,
                    "user_answer": a.user_answer,
                    "correct_answer": a.correct_answer,
                    "is_correct": a.is_correct,
                    "points_earned": a.points_earned,
                    "created_at": a.created_at
                }
                for a in answers
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener sesión: {str(e)}"
        )


@router.get("/question/{game_type}", response_model=GameQuestionResponse)
def get_game_question(
    game_type: str,
    difficulty: int = 1,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Obtener pregunta aleatoria para el juego
    
    - **game_type**: Tipo de juego ('complete_phrase' o 'context_match')
    - **difficulty**: Nivel de dificultad (1-3)
    """
    try:
        game_service = GameService(db)
        question = game_service.get_random_question(
            game_type=game_type,
            difficulty_level=difficulty
        )
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay frases disponibles para este nivel de dificultad"
            )
        
        return question
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener pregunta: {str(e)}"
        )


@router.post("/answer", response_model=dict)
def submit_game_answer(
    answer_data: GameAnswerSubmit,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Enviar respuesta a una pregunta
    
    - **answer_data**: Datos de la respuesta del usuario
    
    Returns:
        - **correct**: Si la respuesta es correcta
        - **points**: Puntos ganados
        - **explanation**: Explicación de la respuesta
    """
    from models.database import GameSession
    
    try:
        # Verificar que la sesión existe y pertenece al usuario
        session = db.query(GameSession).filter(
            GameSession.id == answer_data.session_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sesión {answer_data.session_id} no encontrada"
            )
        
        if session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para responder en esta sesión"
            )
        
        # Usar el servicio para verificar y guardar la respuesta
        game_service = GameService(db)
        result = game_service.check_answer(
            session_id=answer_data.session_id,
            phrase_id=answer_data.phrase_id,
            selected_option=answer_data.selected_option
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar respuesta: {str(e)}"
        )


@router.get("/stats", response_model=UserGameStats)
def get_user_game_stats(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Obtener estadísticas de juegos del usuario actual
    
    Returns:
        - **total_sessions**: Total de sesiones jugadas
        - **total_questions**: Total de preguntas respondidas
        - **correct_answers**: Total de respuestas correctas
        - **accuracy**: Porcentaje de precisión
        - **total_score**: Puntuación total acumulada
        - **perfect_games**: Juegos perfectos (sin errores)
        - **games_by_type**: Distribución por tipo de juego
    """
    try:
        game_service = GameService(db)
        stats = game_service.get_user_stats(user_id=current_user.id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )


@router.get("/sessions")
def get_user_game_sessions(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Obtener historial de sesiones del usuario
    
    - **limit**: Número máximo de sesiones a retornar (default: 10)
    """
    try:
        game_service = GameService(db)
        sessions = game_service.get_user_sessions(
            user_id=current_user.id,
            limit=limit
        )
        
        # Retornar sesiones sin las respuestas para evitar problemas de circular reference
        return [
            {
                "id": s.id,
                "user_id": s.user_id,
                "game_type": s.game_type,
                "total_questions": s.total_questions,
                "correct_answers": s.correct_answers,
                "incorrect_answers": s.incorrect_answers,
                "total_score": s.total_score,
                "is_perfect": s.is_perfect,
                "time_spent_seconds": s.time_spent_seconds,
                "completed_at": s.completed_at
            }
            for s in sessions
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener sesiones: {str(e)}"
        )


@router.get("/leaderboard")
def get_leaderboard(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Obtener tabla de clasificación global
    
    - **limit**: Número de usuarios en el leaderboard (default: 10)
    
    Returns:
        - Lista de usuarios ordenados por puntos totales
        - Incluye rank, username, avatar, puntos, nivel, título
    """
    try:
        game_service = GameService(db)
        leaderboard = game_service.get_leaderboard(limit=limit)
        
        return {
            "leaderboard": leaderboard,
            "total_users": len(leaderboard),
            "user_rank": next(
                (entry["rank"] for entry in leaderboard if entry["username"] == current_user.username),
                None
            )
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener leaderboard: {str(e)}"
        )
