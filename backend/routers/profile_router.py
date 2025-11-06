"""
Router de API para Perfil y Gamificación
Endpoints para perfil de usuario, misiones, recompensas y progreso
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from typing import List

from config.database_connection import get_db
from dependencies import get_current_user
from services.profile_service import ProfileService
from schemas.schemas import (
    UserProfileUpdate, UserResponse,
    CompleteProfileResponse, LevelProgressResponse,
    DailyMissionResponse, RewardResponse, UserRewardResponse,
    ClaimRewardRequest, DashboardStatsResponse
)
from models.database import User

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Obtener información básica del perfil actual
    """
    return current_user


@router.put("/me")
def update_my_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Actualizar información del perfil
    
    - **phone**: Número de teléfono (editable)
    - **avatar_url**: URL del avatar (editable)
    """
    try:
        profile_service = ProfileService(db)
        updated_user = profile_service.update_profile(
            user_id=current_user.id,
            phone=profile_data.phone,
            avatar_url=profile_data.avatar_url
        )
        
        return {
            "message": "Perfil actualizado exitosamente",
            "user": {
                "id": updated_user.id,
                "email": updated_user.email,
                "username": updated_user.username,
                "phone": updated_user.phone,
                "full_name": updated_user.full_name,
                "avatar_url": updated_user.avatar_url,
                "level": updated_user.level,
                "total_points": updated_user.total_points,
                "current_title": updated_user.current_title
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar perfil: {str(e)}"
        )


@router.get("/complete")
def get_complete_profile(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Obtener perfil completo con gamificación
    
    Incluye:
    - Información del usuario
    - Progreso de nivel
    - Misiones diarias
    - Recompensas disponibles
    - Recompensas reclamadas
    """
    try:
        profile_service = ProfileService(db)
        profile_data = profile_service.get_complete_profile(current_user.id)
        
        # Commit la transacción después de generar misiones/progreso
        db.commit()
        
        # Serializar manualmente para evitar problemas de circular refs
        return {
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "username": current_user.username,
                "phone": current_user.phone,
                "full_name": current_user.full_name,
                "avatar_url": current_user.avatar_url,
                "level": current_user.level,
                "total_points": current_user.total_points,
                "current_title": current_user.current_title,
                "is_active": current_user.is_active,
                "created_at": current_user.created_at,
                "last_login": current_user.last_login
            },
            "level_progress": {
                "level": profile_data["level_progress"].level,
                "title": profile_data["level_progress"].title,
                "current_points": profile_data["level_progress"].current_points,
                "points_to_next_level": profile_data["level_progress"].points_to_next_level,
                "phrases_learned": profile_data["level_progress"].phrases_learned,
                "games_completed": profile_data["level_progress"].games_completed,
                "perfect_games": profile_data["level_progress"].perfect_games,
                "chat_interactions": profile_data["level_progress"].chat_interactions
            },
            "daily_missions": [
                {
                    "id": m.id,
                    "mission_type": m.mission_type,
                    "mission_name": m.mission_name,
                    "mission_description": m.mission_description,
                    "target_value": m.target_value,
                    "current_value": m.current_value,
                    "is_completed": m.is_completed,
                    "points_reward": m.points_reward,
                    "mission_date": m.mission_date,
                    "completed_at": m.completed_at
                }
                for m in profile_data["daily_missions"]
            ],
            "available_rewards": [
                {
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "icon_url": r.icon_url,
                    "points_required": r.points_required,
                    "reward_type": r.reward_type,
                    "reward_value": r.reward_value,
                    "is_active": r.is_active
                }
                for r in profile_data["available_rewards"]
            ],
            "claimed_rewards": [
                {
                    "id": ur.id,
                    "reward": {
                        "id": ur.reward.id,
                        "name": ur.reward.name,
                        "description": ur.reward.description,
                        "icon_url": ur.reward.icon_url,
                        "reward_type": ur.reward.reward_type,
                        "reward_value": ur.reward.reward_value
                    },
                    "claimed_at": ur.claimed_at,
                    "is_active": ur.is_active
                }
                for ur in profile_data["claimed_rewards"]
            ]
        }
    except ValueError as e:
        import logging
        logging.error(f"ValueError en get_complete_profile: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        import logging
        import traceback
        logging.error(f"Exception en get_complete_profile: {str(e)}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener perfil: {str(e)}"
        )


@router.get("/progress", response_model=LevelProgressResponse)
def get_level_progress(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Obtener progreso de nivel del usuario
    """
    try:
        profile_service = ProfileService(db)
        progress = profile_service.get_or_create_level_progress(current_user.id)
        return progress
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener progreso: {str(e)}"
        )


@router.get("/missions")
def get_daily_missions(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Obtener misiones diarias del usuario
    """
    try:
        profile_service = ProfileService(db)
        profile_service.generate_daily_missions(current_user.id)
        
        from models.database import DailyMission
        from datetime import date
        
        today = date.today()
        missions = db.query(DailyMission).filter(
            DailyMission.user_id == current_user.id,
            DailyMission.mission_date == today
        ).all()
        
        return [
            {
                "id": m.id,
                "mission_type": m.mission_type,
                "mission_name": m.mission_name,
                "mission_description": m.mission_description,
                "target_value": m.target_value,
                "current_value": m.current_value,
                "is_completed": m.is_completed,
                "points_reward": m.points_reward,
                "mission_date": m.mission_date,
                "completed_at": m.completed_at
            }
            for m in missions
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener misiones: {str(e)}"
        )


@router.get("/rewards/available")
def get_available_rewards(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Obtener recompensas disponibles para reclamar
    """
    try:
        profile_service = ProfileService(db)
        progress = profile_service.get_or_create_level_progress(current_user.id)
        
        from models.database import Reward, UserReward
        
        # Obtener IDs de recompensas ya reclamadas
        claimed_reward_ids = [ur.reward_id for ur in db.query(UserReward).filter(
            UserReward.user_id == current_user.id
        ).all()]
        
        # Obtener recompensas disponibles
        rewards = db.query(Reward).filter(
            Reward.is_active == True,
            Reward.points_required <= progress.current_points,
            ~Reward.id.in_(claimed_reward_ids) if claimed_reward_ids else True
        ).all()
        
        return [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "icon_url": r.icon_url,
                "points_required": r.points_required,
                "reward_type": r.reward_type,
                "reward_value": r.reward_value,
                "is_active": r.is_active
            }
            for r in rewards
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener recompensas: {str(e)}"
        )


@router.post("/rewards/claim")
def claim_reward(
    reward_data: ClaimRewardRequest,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Reclamar una recompensa
    
    - **reward_id**: ID de la recompensa a reclamar
    """
    try:
        profile_service = ProfileService(db)
        user_reward = profile_service.claim_reward(current_user.id, reward_data.reward_id)
        
        return {
            "message": "Recompensa reclamada exitosamente",
            "reward": {
                "id": user_reward.reward.id,
                "name": user_reward.reward.name,
                "description": user_reward.reward.description,
                "reward_type": user_reward.reward.reward_type,
                "reward_value": user_reward.reward.reward_value
            },
            "claimed_at": user_reward.claimed_at
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al reclamar recompensa: {str(e)}"
        )


@router.get("/stats/dashboard")
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Obtener estadísticas para el dashboard
    """
    try:
        profile_service = ProfileService(db)
        stats = profile_service.get_dashboard_stats(current_user.id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )


@router.get("/avatars/available")
def get_available_avatars(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Obtener lista de avatares disponibles para el usuario
    
    Incluye:
    - Avatares de nivel desbloqueados (según nivel actual)
    - Avatares de recompensas reclamadas
    """
    try:
        profile_service = ProfileService(db)
        
        # Obtener avatares desbloqueados
        level_avatars = profile_service.get_unlocked_level_avatars(current_user.id)
        reward_avatars = profile_service.get_unlocked_reward_avatars(current_user.id)
        
        return {
            "success": True,
            "current_avatar": current_user.avatar_url,
            "unlocked_avatars": level_avatars + reward_avatars,
            "total_unlocked": len(level_avatars) + len(reward_avatars)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener avatares disponibles: {str(e)}"
        )


@router.put("/avatar/select")
def select_avatar(
    avatar_data: dict,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Seleccionar un avatar de los disponibles
    
    Body:
    - avatar_url: URL del avatar seleccionado
    """
    try:
        avatar_url = avatar_data.get("avatar_url")
        
        if not avatar_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se requiere avatar_url"
            )
        
        profile_service = ProfileService(db)
        
        # Verificar que el avatar esté disponible para el usuario
        is_available = profile_service.verify_avatar_available(current_user.id, avatar_url)
        
        if not is_available:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Este avatar no está disponible para ti"
            )
        
        # Actualizar avatar del usuario
        updated_user = profile_service.update_profile(
            user_id=current_user.id,
            avatar_url=avatar_url
        )
        
        db.commit()
        
        return {
            "success": True,
            "message": "Avatar actualizado exitosamente",
            "avatar_url": updated_user.avatar_url
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al seleccionar avatar: {str(e)}"
        )

