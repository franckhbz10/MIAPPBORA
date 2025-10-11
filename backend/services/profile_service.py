"""
Servicio de Perfil y Gamificación para MIAPPBORA
Gestiona perfil de usuario, misiones diarias, recompensas y progreso de nivel
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Optional
from datetime import datetime, date

from models.database import (
    User, DailyMission, Reward, UserReward, 
    LevelProgress, GameSession, ChatConversation
)


class ProfileService:
    """
    Servicio para gestionar perfil y gamificación
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_complete_profile(self, user_id: int) -> Dict:
        """
        Obtener perfil completo con todas las métricas de gamificación
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("Usuario no encontrado")
        
        # Obtener o crear progreso de nivel
        level_progress = self.get_or_create_level_progress(user_id)
        
        # Generar misiones diarias si no existen (retorna las misiones)
        daily_missions = self.generate_daily_missions(user_id)
        
        # Obtener recompensas disponibles (no reclamadas)
        claimed_reward_ids = [ur.reward_id for ur in self.db.query(UserReward).filter(
            UserReward.user_id == user_id
        ).all()]
        
        available_rewards = self.db.query(Reward).filter(
            Reward.is_active == True,
            Reward.points_required <= level_progress.current_points,
            ~Reward.id.in_(claimed_reward_ids) if claimed_reward_ids else True
        ).all()
        
        # Obtener recompensas ya reclamadas
        claimed_rewards = self.db.query(UserReward).filter(
            UserReward.user_id == user_id
        ).all()
        
        return {
            "user": user,
            "level_progress": level_progress,
            "daily_missions": daily_missions,
            "available_rewards": available_rewards,
            "claimed_rewards": claimed_rewards
        }
    
    def get_or_create_level_progress(self, user_id: int) -> LevelProgress:
        """
        Obtener o crear progreso de nivel para un usuario
        """
        progress = self.db.query(LevelProgress).filter(
            LevelProgress.user_id == user_id
        ).first()
        
        if not progress:
            progress = LevelProgress(
                user_id=user_id,
                current_points=0,
                points_to_next_level=500,
                level=1,
                title='Principiante'
            )
            self.db.add(progress)
            self.db.flush()
            # No hacer refresh aquí, flush() es suficiente para que el objeto esté disponible
        
        return progress
    
    def update_profile(self, user_id: int, phone: Optional[str] = None, 
                      avatar_url: Optional[str] = None) -> User:
        """
        Actualizar información del perfil
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("Usuario no encontrado")
        
        if phone:
            user.phone = phone
        if avatar_url:
            user.avatar_url = avatar_url
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def generate_daily_missions(self, user_id: int) -> list:
        """
        Generar misiones diarias para el usuario si no existen
        Retorna las misiones (existentes o recién creadas)
        """
        today = date.today()
        
        # Verificar si ya tiene misiones para hoy
        existing_missions = self.db.query(DailyMission).filter(
            DailyMission.user_id == user_id,
            DailyMission.mission_date == today
        ).all()
        
        if len(existing_missions) > 0:
            return existing_missions  # Ya tiene misiones
        
        # Crear 3 misiones diarias
        missions = [
            DailyMission(
                user_id=user_id,
                mission_date=today,
                mission_type='chat_questions',
                mission_name='Pregunta al Mentor',
                mission_description='Realiza 3 consultas al Mentor Bora',
                target_value=3,
                current_value=0,
                points_reward=50
            ),
            DailyMission(
                user_id=user_id,
                mission_date=today,
                mission_type='game_plays',
                mission_name='Practica Jugando',
                mission_description='Completa 2 sesiones de minijuegos',
                target_value=2,
                current_value=0,
                points_reward=30
            ),
            DailyMission(
                user_id=user_id,
                mission_date=today,
                mission_type='perfect_games',
                mission_name='Perfección Bora',
                mission_description='Logra 1 partida perfecta (100% aciertos)',
                target_value=1,
                current_value=0,
                points_reward=100
            )
        ]
        
        for mission in missions:
            self.db.add(mission)
        
        # No hacer commit aquí, dejar que el router maneje la transacción
        self.db.flush()  # Asegurar que se escriben en la BD pero sin commit
        
        return missions  # Retornar las misiones creadas
    
    def update_mission_progress(self, user_id: int, mission_type: str, increment: int = 1):
        """
        Actualizar progreso de misión y completarla si alcanza el objetivo
        """
        today = date.today()
        
        mission = self.db.query(DailyMission).filter(
            DailyMission.user_id == user_id,
            DailyMission.mission_date == today,
            DailyMission.mission_type == mission_type,
            DailyMission.is_completed == False
        ).first()
        
        if not mission:
            return None
        
        mission.current_value += increment
        
        # Verificar si se completó
        if mission.current_value >= mission.target_value and not mission.is_completed:
            mission.is_completed = True
            mission.completed_at = datetime.utcnow()
            
            # Otorgar puntos
            self.add_points(user_id, mission.points_reward, "Misión completada")
        
        self.db.flush()
        self.db.refresh(mission)
        
        return mission
    
    def add_points(self, user_id: int, points: int, reason: str = "") -> LevelProgress:
        """
        Agregar puntos al usuario y actualizar su nivel
        """
        progress = self.get_or_create_level_progress(user_id)
        
        progress.current_points += points
        
        # Actualizar estadísticas según razón
        if "juego" in reason.lower():
            progress.games_completed += 1
        elif "perfecto" in reason.lower():
            progress.perfect_games += 1
        elif "chat" in reason.lower() or "consulta" in reason.lower():
            progress.chat_interactions += 1
        elif "frase" in reason.lower():
            progress.phrases_learned += 1
        
        # El trigger de SQL actualizará automáticamente el nivel y título
        self.db.flush()
        self.db.refresh(progress)
        
        return progress
    
    def claim_reward(self, user_id: int, reward_id: int) -> UserReward:
        """
        Reclamar una recompensa
        """
        # Verificar que la recompensa existe
        reward = self.db.query(Reward).filter(Reward.id == reward_id).first()
        if not reward:
            raise ValueError("Recompensa no encontrada")
        
        # Verificar que el usuario tiene suficientes puntos
        progress = self.get_or_create_level_progress(user_id)
        if progress.current_points < reward.points_required:
            raise ValueError("Puntos insuficientes para reclamar esta recompensa")
        
        # Verificar que no la haya reclamado antes
        existing = self.db.query(UserReward).filter(
            UserReward.user_id == user_id,
            UserReward.reward_id == reward_id
        ).first()
        
        if existing:
            raise ValueError("Recompensa ya reclamada")
        
        # Crear registro de recompensa
        user_reward = UserReward(
            user_id=user_id,
            reward_id=reward_id
        )
        
        self.db.add(user_reward)
        
        # Aplicar la recompensa según su tipo
        if reward.reward_type == 'avatar':
            user = self.db.query(User).filter(User.id == user_id).first()
            user.avatar_url = reward.reward_value
        elif reward.reward_type == 'title':
            user = self.db.query(User).filter(User.id == user_id).first()
            user.current_title = reward.reward_value
        
        self.db.flush()
        self.db.refresh(user_reward)
        
        return user_reward
    
    def get_dashboard_stats(self, user_id: int) -> Dict:
        """
        Obtener estadísticas para el dashboard
        """
        # Contar sesiones de juego
        games_played = self.db.query(func.count(GameSession.id)).filter(
            GameSession.user_id == user_id,
            GameSession.completed_at != None
        ).scalar() or 0
        
        # Contar juegos perfectos
        perfect_games = self.db.query(func.count(GameSession.id)).filter(
            GameSession.user_id == user_id,
            GameSession.is_perfect == True
        ).scalar() or 0
        
        # Contar consultas al chat
        chat_queries = self.db.query(func.count(ChatConversation.id)).filter(
            ChatConversation.user_id == user_id
        ).scalar() or 0
        
        return {
            "total_visits": 0,  # Se puede implementar con tabla de tracking
            "home_visits": 0,
            "phrases_visits": 0,
            "games_visits": 0,
            "chat_queries": chat_queries,
            "games_played": games_played,
            "perfect_games": perfect_games
        }
