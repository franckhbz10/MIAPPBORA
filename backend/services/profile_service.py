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

# Tabla simple de progresión por niveles (4 niveles estandarizados)
LEVEL_CONFIG = [
    {
        "level": 1, 
        "title": "Entusiasta", 
        "next_threshold": 50,
        "avatar_url": "https://bsetkzhqjehhoaoietbq.supabase.co/storage/v1/object/public/assets/avatars/avatar-entusiasta.png"
    },
    {
        "level": 2, 
        "title": "Hablante", 
        "next_threshold": 300,
        "avatar_url": "https://bsetkzhqjehhoaoietbq.supabase.co/storage/v1/object/public/assets/avatars/avatar-hablante.png"
    },
    {
        "level": 3, 
        "title": "Nativo", 
        "next_threshold": 600,
        "avatar_url": "https://bsetkzhqjehhoaoietbq.supabase.co/storage/v1/object/public/assets/avatars/avatar-nativo.png"
    },
    {
        "level": 4, 
        "title": "Maestro Bora", 
        "next_threshold": None,
        "avatar_url": "https://bsetkzhqjehhoaoietbq.supabase.co/storage/v1/object/public/assets/avatars/avatar-maestro-bora.png"
    },
]


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
        
        # Obtener TODAS las recompensas activas (sin filtrar por puntos)
        # El filtrado por puntos se hace en el frontend con can_afford
        available_rewards = self.db.query(Reward).filter(
            Reward.is_active == True
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
                points_to_next_level=50,
                level=1,
                title='Entusiasta'
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
        
        Incrementa AMBOS campos:
        - current_points: Puntos disponibles para gastar en recompensas
        - total_points (en User): Puntos históricos acumulados para leaderboard (nunca se descuentan)
        """
        progress = self.get_or_create_level_progress(user_id)
        user = self.db.query(User).filter(User.id == user_id).first()
        
        # Incrementar puntos disponibles para gastar
        progress.current_points += points
        
        # Incrementar puntos históricos (para leaderboard) - nunca se descuentan
        if user:
            user.total_points += points
        
        # Actualizar estadísticas según razón
        if "juego" in reason.lower():
            progress.games_completed += 1
        elif "perfecto" in reason.lower():
            progress.perfect_games += 1
        elif "chat" in reason.lower() or "consulta" in reason.lower():
            progress.chat_interactions += 1
        elif "frase" in reason.lower():
            progress.phrases_learned += 1
        
        # Ajustar nivel, título y puntos restantes hasta el próximo nivel
        self._recalculate_level(progress)
        
        self.db.flush()
        self.db.refresh(progress)
        
        return progress

    def _recalculate_level(self, progress: LevelProgress) -> None:
        """
        Recalcular nivel, título, puntos restantes y avatar usando la tabla de configuración.
        El avatar se actualiza automáticamente al subir de nivel, pero el usuario puede personalizarlo.
        """
        total_points = progress.current_points
        user = progress.user or self.db.query(User).filter(User.id == progress.user_id).first()
        
        # Recorrer configuraciones en orden y seleccionar la primera cuyo umbral siguiente no se haya alcanzado
        for config in LEVEL_CONFIG:
            threshold = config["next_threshold"]
            if threshold is None or total_points < threshold:
                old_level = progress.level
                progress.level = config["level"]
                progress.title = config["title"]
                progress.points_to_next_level = max((threshold - total_points) if threshold else 0, 0)
                
                # Mantener sincronizado el nivel del usuario
                if user:
                    user.level = progress.level
                    user.current_title = progress.title
                    
                    # Auto-actualizar avatar solo si subió de nivel Y no tiene avatar personalizado
                    # (avatar personalizado = no coincide con ningún avatar de nivel)
                    if old_level < progress.level:
                        is_custom_avatar = not any(
                            user.avatar_url == cfg.get("avatar_url") 
                            for cfg in LEVEL_CONFIG
                        )
                        # Si no tiene avatar personalizado, actualizar al avatar del nuevo nivel
                        if not is_custom_avatar or not user.avatar_url or "ui-avatars.com" in user.avatar_url:
                            user.avatar_url = config.get("avatar_url", user.avatar_url)
                break
        else:
            # Fallback por si la tabla se queda corta
            old_level = progress.level
            progress.level = LEVEL_CONFIG[-1]["level"]
            progress.title = LEVEL_CONFIG[-1]["title"]
            progress.points_to_next_level = 0
            
            if user:
                user.level = progress.level
                user.current_title = progress.title
                
                # Auto-actualizar avatar si llegó al nivel máximo
                if old_level < progress.level:
                    is_custom_avatar = not any(
                        user.avatar_url == cfg.get("avatar_url") 
                        for cfg in LEVEL_CONFIG
                    )
                    if not is_custom_avatar or not user.avatar_url or "ui-avatars.com" in user.avatar_url:
                        user.avatar_url = LEVEL_CONFIG[-1].get("avatar_url", user.avatar_url)
    
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
    
    def get_unlocked_level_avatars(self, user_id: int) -> list:
        """
        Obtener avatares de nivel desbloqueados por el usuario
        El usuario tiene acceso a todos los avatares de niveles <= su nivel actual
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        unlocked = []
        current_level = user.level
        
        for config in LEVEL_CONFIG:
            if config["level"] <= current_level:
                unlocked.append({
                    "id": f"level_{config['level']}",
                    "name": config["title"],
                    "description": f"Avatar de nivel {config['level']}",
                    "avatar_url": config["avatar_url"],
                    "type": "level",
                    "level": config["level"],
                    "is_current_level": config["level"] == current_level,
                    "unlocked_at": f"Al alcanzar nivel {config['level']}"
                })
        
        return unlocked
    
    def get_unlocked_reward_avatars(self, user_id: int) -> list:
        """
        Obtener avatares de recompensas reclamadas por el usuario
        Solo incluye recompensas de tipo 'avatar'
        """
        user_rewards = self.db.query(UserReward).join(Reward).filter(
            UserReward.user_id == user_id,
            Reward.reward_type == 'avatar'
        ).all()
        
        unlocked = []
        for user_reward in user_rewards:
            reward = user_reward.reward
            unlocked.append({
                "id": f"reward_{reward.id}",
                "name": reward.name,
                "description": reward.description,
                "avatar_url": reward.reward_value,  # reward_value contiene la URL del avatar
                "type": "reward",
                "unlocked_at": user_reward.claimed_at.strftime("%d/%m/%Y"),
                "points_required": reward.points_required
            })
        
        return unlocked
    
    def verify_avatar_available(self, user_id: int, avatar_url: str) -> bool:
        """
        Verificar si un avatar está disponible para el usuario
        Retorna True si el avatar está en los desbloqueados
        """
        level_avatars = self.get_unlocked_level_avatars(user_id)
        reward_avatars = self.get_unlocked_reward_avatars(user_id)
        
        all_available = level_avatars + reward_avatars
        
        for avatar in all_available:
            if avatar["avatar_url"] == avatar_url:
                return True
        
        return False
    
    def get_unlocked_titles(self, user_id: int) -> list:
        """
        Obtener títulos desbloqueados por el usuario
        Incluye:
        - Títulos de nivel (según nivel actual del usuario)
        - Títulos de recompensas reclamadas
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        unlocked = []
        current_level = user.level
        
        # Títulos de nivel desbloqueados
        for config in LEVEL_CONFIG:
            if config["level"] <= current_level:
                unlocked.append({
                    "id": f"level_{config['level']}",
                    "name": config["title"],
                    "description": f"Título de nivel {config['level']}",
                    "title_value": config["title"],
                    "type": "level",
                    "level": config["level"],
                    "is_current_level": config["level"] == current_level,
                    "unlocked_at": f"Al alcanzar nivel {config['level']}"
                })
        
        # Títulos de recompensas reclamadas
        user_rewards = self.db.query(UserReward).join(Reward).filter(
            UserReward.user_id == user_id,
            Reward.reward_type == 'title'
        ).all()
        
        for user_reward in user_rewards:
            reward = user_reward.reward
            unlocked.append({
                "id": f"reward_{reward.id}",
                "name": reward.name,
                "description": reward.description,
                "title_value": reward.reward_value,  # reward_value contiene el texto del título
                "type": "reward",
                "unlocked_at": user_reward.claimed_at.strftime("%d/%m/%Y"),
                "points_required": reward.points_required,
                "icon": reward.icon_url or "🏆"
            })
        
        return unlocked
    
    def verify_title_available(self, user_id: int, title_value: str) -> bool:
        """
        Verificar si un título está disponible para el usuario
        Retorna True si el título está en los desbloqueados
        """
        unlocked_titles = self.get_unlocked_titles(user_id)
        
        for title in unlocked_titles:
            if title["title_value"] == title_value:
                return True
        
        return False
