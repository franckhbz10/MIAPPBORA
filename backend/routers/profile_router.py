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
        
        # Obtener IDs de recompensas ya reclamadas para marcarlas
        from models.database import UserReward
        claimed_reward_ids = [ur.reward_id for ur in db.query(UserReward).filter(
            UserReward.user_id == current_user.id
        ).all()]
        
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
                    "is_active": r.is_active,
                    "can_afford": current_user.total_points >= r.points_required,
                    "already_claimed": r.id in claimed_reward_ids
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
    Muestra TODAS las recompensas activas con indicadores de:
    - can_afford: Si el usuario tiene suficientes puntos
    - already_claimed: Si ya fue reclamada
    """
    try:
        from models.database import Reward, UserReward
        
        # Obtener IDs de recompensas ya reclamadas
        claimed_reward_ids = [ur.reward_id for ur in db.query(UserReward).filter(
            UserReward.user_id == current_user.id
        ).all()]
        
        # Obtener TODAS las recompensas activas
        rewards = db.query(Reward).filter(Reward.is_active == True).all()
        
        # Obtener level_progress para puntos disponibles
        from models.database import LevelProgress
        level_progress = db.query(LevelProgress).filter(
            LevelProgress.user_id == current_user.id
        ).first()
        
        available_points = level_progress.current_points if level_progress else 0
        
        return {
            "success": True,
            "user_points": current_user.total_points,
            "available_points": available_points,
            "rewards": [
                {
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "icon_url": r.icon_url,
                    "points_required": r.points_required,
                    "reward_type": r.reward_type,
                    "reward_value": r.reward_value,
                    "can_afford": available_points >= r.points_required,
                    "already_claimed": r.id in claimed_reward_ids
                }
                for r in rewards
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener recompensas: {str(e)}"
        )


@router.get("/achievements")
def get_achievements(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Obtener logros/achievements disponibles
    Los achievements SUMAN puntos al reclamarlos en lugar de restarlos
    """
    try:
        from models.database import Reward, UserReward, LevelProgress, GameSession
        from sqlalchemy import func
        
        # Obtener IDs de achievements ya reclamados
        claimed_achievement_ids = [ur.reward_id for ur in db.query(UserReward).filter(
            UserReward.user_id == current_user.id,
            UserReward.reward_id.in_(
                db.query(Reward.id).filter(Reward.reward_type == 'achievement')
            )
        ).all()]
        
        # Obtener TODOS los achievements
        achievements = db.query(Reward).filter(
            Reward.reward_type == 'achievement',
            Reward.is_active == True
        ).all()
        
        # Obtener estadísticas del usuario para verificar requisitos
        level_progress = db.query(LevelProgress).filter(
            LevelProgress.user_id == current_user.id
        ).first()
        
        perfect_games = db.query(func.count(GameSession.id)).filter(
            GameSession.user_id == current_user.id,
            GameSession.is_perfect == True
        ).scalar() or 0
        
        achievements_list = []
        for achievement in achievements:
            # Determinar si cumple requisitos según el tipo de logro
            meets_requirements = False
            progress = 0
            target = 0
            
            if "Maestro de Frases" in achievement.name:
                target = 10
                progress = perfect_games
                meets_requirements = perfect_games >= 10
            elif "Campeón del Chat" in achievement.name:
                target = 50
                progress = level_progress.chat_interactions if level_progress else 0
                meets_requirements = progress >= 50
            elif "Explorador de Frases" in achievement.name:
                target = 100
                progress = level_progress.phrases_learned if level_progress else 0
                meets_requirements = progress >= 100
            
            achievements_list.append({
                "id": achievement.id,
                "name": achievement.name,
                "description": achievement.description,
                "icon_url": achievement.icon_url,
                "points_reward": achievement.points_required,  # Ahora es recompensa
                "reward_value": achievement.reward_value,
                "already_claimed": achievement.id in claimed_achievement_ids,
                "meets_requirements": meets_requirements,
                "progress": progress,
                "target": target
            })
        
        return {
            "success": True,
            "achievements": achievements_list
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener achievements: {str(e)}"
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
    - Verifica puntos suficientes
    - Deduce los puntos del total_points del usuario
    - Aplica el efecto según el tipo de recompensa
    """
    try:
        from models.database import Reward, UserReward
        
        # Verificar que la recompensa existe
        reward = db.query(Reward).filter(Reward.id == reward_data.reward_id).first()
        if not reward:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recompensa no encontrada"
            )
        
        # Verificar que no la haya reclamado antes
        existing = db.query(UserReward).filter(
            UserReward.user_id == current_user.id,
            UserReward.reward_id == reward_data.reward_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya has reclamado esta recompensa"
            )
        
        # Obtener level_progress para verificar puntos disponibles
        from models.database import LevelProgress
        level_progress = db.query(LevelProgress).filter(
            LevelProgress.user_id == current_user.id
        ).first()
        
        if not level_progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Progreso de nivel no encontrado"
            )
        
        # LÓGICA DIFERENTE PARA ACHIEVEMENTS
        if reward.reward_type == 'achievement':
            # Los achievements SUMAN puntos en lugar de restar
            from services.profile_service import ProfileService
            profile_service = ProfileService(db)
            
            # Sumar puntos (points_required se convierte en points_reward)
            points_to_add = reward.points_required
            profile_service.add_points(
                current_user.id, 
                points_to_add, 
                f"Achievement desbloqueado: {reward.name}"
            )
            
            # Crear registro de achievement reclamado
            user_reward = UserReward(
                user_id=current_user.id,
                reward_id=reward_data.reward_id
            )
            db.add(user_reward)
            db.commit()
            db.refresh(user_reward)
            db.refresh(current_user)
            db.refresh(level_progress)
            
            return {
                "success": True,
                "message": f"¡Achievement '{reward.name}' desbloqueado!",
                "reward": {
                    "id": reward.id,
                    "name": reward.name,
                    "description": reward.description,
                    "reward_type": reward.reward_type,
                    "reward_value": reward.reward_value
                },
                "points_earned": points_to_add,
                "points_remaining": level_progress.current_points,
                "total_points": current_user.total_points,
                "claimed_at": user_reward.claimed_at.isoformat()
            }
        
        # LÓGICA NORMAL PARA OTRAS RECOMPENSAS (avatares, títulos, etc.)
        # Verificar que tenga suficientes puntos DISPONIBLES (current_points)
        if level_progress.current_points < reward.points_required:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Puntos insuficientes. Necesitas {reward.points_required} puntos, tienes {level_progress.current_points} disponibles"
            )
        
        # Deducir puntos SOLO de current_points (puntos disponibles)
        # total_points se mantiene fijo para el leaderboard
        level_progress.current_points -= reward.points_required
        
        # Crear registro de recompensa
        user_reward = UserReward(
            user_id=current_user.id,
            reward_id=reward_data.reward_id
        )
        db.add(user_reward)
        
        # Aplicar la recompensa según su tipo
        if reward.reward_type == 'avatar':
            current_user.avatar_url = reward.reward_value
        elif reward.reward_type == 'title':
            current_user.current_title = reward.reward_value
        
        db.commit()
        db.refresh(current_user)
        db.refresh(user_reward)
        
        return {
            "success": True,
            "message": f"¡Recompensa '{reward.name}' reclamada exitosamente!",
            "reward": {
                "id": reward.id,
                "name": reward.name,
                "description": reward.description,
                "reward_type": reward.reward_type,
                "reward_value": reward.reward_value
            },
            "points_remaining": level_progress.current_points,
            "total_points": current_user.total_points,
            "claimed_at": user_reward.claimed_at.isoformat()
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
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


@router.get("/titles/available")
def get_available_titles(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Obtener lista de títulos disponibles para el usuario
    
    Incluye:
    - Títulos de nivel desbloqueados (según nivel actual)
    - Títulos de recompensas reclamadas
    """
    try:
        profile_service = ProfileService(db)
        
        # Obtener títulos desbloqueados
        unlocked_titles = profile_service.get_unlocked_titles(current_user.id)
        
        return {
            "success": True,
            "current_title": current_user.current_title,
            "unlocked_titles": unlocked_titles,
            "total_unlocked": len(unlocked_titles)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener títulos disponibles: {str(e)}"
        )


@router.put("/title/select")
def select_title(
    title_data: dict,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Seleccionar un título de los disponibles
    
    Body:
    - title_value: Texto del título seleccionado
    """
    try:
        title_value = title_data.get("title_value")
        
        if not title_value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se requiere title_value"
            )
        
        profile_service = ProfileService(db)
        
        # Verificar que el título esté disponible para el usuario
        is_available = profile_service.verify_title_available(current_user.id, title_value)
        
        if not is_available:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Este título no está disponible para ti"
            )
        
        # Actualizar título del usuario
        current_user.current_title = title_value
        db.commit()
        db.refresh(current_user)
        
        return {
            "success": True,
            "message": "Título actualizado exitosamente",
            "current_title": current_user.current_title
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al seleccionar título: {str(e)}"
        )


@router.get("/leaderboard")
def get_leaderboard(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Obtener tabla de clasificación (top usuarios por puntos)
    
    - **limit**: Número de usuarios a mostrar (default: 10)
    - Retorna: Lista de usuarios ordenados por total_points descendente
    - Incluye: posición, nombre, puntos, avatar, nivel
    """
    try:
        # Obtener top usuarios por puntos
        top_users = db.query(User).filter(
            User.is_active == True
        ).order_by(
            User.total_points.desc()
        ).limit(limit).all()
        
        # Construir respuesta con posición
        leaderboard = []
        for index, user in enumerate(top_users, start=1):
            leaderboard.append({
                "position": index,
                "user_id": user.id,
                "username": user.username,
                "avatar_url": user.avatar_url,
                "total_points": user.total_points,
                "level": user.level,
                "current_title": user.current_title,
                "is_current_user": user.id == current_user.id
            })
        
        # Si el usuario actual no está en el top, agregarlo al final
        current_user_in_top = any(u["user_id"] == current_user.id for u in leaderboard)
        
        if not current_user_in_top:
            # Calcular posición real del usuario
            users_above = db.query(User).filter(
                User.is_active == True,
                User.total_points > current_user.total_points
            ).count()
            
            current_user_position = users_above + 1
            
            current_user_data = {
                "position": current_user_position,
                "user_id": current_user.id,
                "username": current_user.username,
                "avatar_url": current_user.avatar_url,
                "total_points": current_user.total_points,
                "level": current_user.level,
                "current_title": current_user.current_title,
                "is_current_user": True
            }
        else:
            current_user_data = None
        
        return {
            "success": True,
            "leaderboard": leaderboard,
            "current_user": current_user_data,
            "total_users": db.query(User).filter(User.is_active == True).count()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener tabla de clasificación: {str(e)}"
        )

