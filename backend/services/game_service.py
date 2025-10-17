"""
Servicio de Minijuegos para MIAPPBORA
Gestiona sesiones de juego, preguntas, respuestas y estadísticas

ARQUITECTURA (siguiendo patrón de pruebita):
- Instanciable por request (NO estático)
- Recibe sesión DB en constructor
- Métodos síncronos (FastAPI maneja async en routers)
- Retorna objetos ORM directamente (no dicts cuando es posible)
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Optional
from datetime import datetime
import random

from models.database import GameSession, GameAnswer, User, BoraPhrase


class GameService:
    """
    Servicio para gestionar minijuegos
    
    Patrón de Uso (siguiendo arquitectura de referencia):
        # En el router:
        game_service = GameService(db)
        session = game_service.create_session(user_id, game_type)
    """
    
    def __init__(self, db: Session):
        """
        Inicializar servicio con sesión de base de datos
        
        Args:
            db: Sesión de SQLAlchemy para operaciones de BD
        """
        self.db = db
    
    def create_session(self, user_id: int, game_type: str) -> GameSession:
        """
        Crear nueva sesión de juego
        
        Args:
            user_id: ID del usuario
            game_type: Tipo de juego ('complete_phrase' o 'context_match')
            
        Returns:
            GameSession creado
            
        Raises:
            ValueError: Si hay error al crear la sesión
        """
        session = GameSession(
            user_id=user_id,
            game_type=game_type,
            total_questions=0,
            correct_answers=0,
            incorrect_answers=0,
            total_score=0,
            is_perfect=False,
            time_spent_seconds=0,
            completed_at=None  # No completada aún
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    def get_random_question(
        self, 
        game_type: str, 
        difficulty_level: int = 1
    ) -> Optional[Dict]:
        """
        Obtener pregunta aleatoria de la base de datos
        
        Args:
            game_type: Tipo de juego ('complete_phrase' o 'context_match')
            difficulty_level: Nivel de dificultad (1-3)
            
        Returns:
            Diccionario con datos de la pregunta o None si no hay frases
            
        Estructura del dict para complete_phrase:
            {
                "id": int,
                "bora_text": str,
                "spanish_translation": str,
                "category": str,
                "difficulty_level": int,
                "usage_context": str,
                "pronunciation_guide": str,
                "options": List[str],  # 4 opciones en Bora
                "correct_answer": str,
                "correct_index": int,
                "hint": str
            }
            
        Estructura del dict para context_match:
            {
                "id": int,
                "bora_text": str,  # Respuesta correcta en Bora
                "spanish_translation": str,
                "category": str,
                "difficulty_level": int,
                "usage_context": str,  # Contexto/situación
                "pronunciation_guide": str,
                "options": List[str],  # 2 opciones en Bora
                "correct_answer": str,  # Frase correcta en Bora
                "correct_index": int,
                "hint": str,
                "context": str  # Contexto completo para mostrar
            }
        """
        # Obtener frase aleatoria de la BD según dificultad
        phrase = self.db.query(BoraPhrase).filter(
            BoraPhrase.difficulty_level == difficulty_level
        ).order_by(func.random()).first()
        
        if not phrase:
            # Si no hay frases con ese nivel, obtener cualquiera
            phrase = self.db.query(BoraPhrase).order_by(func.random()).first()
        
        if not phrase:
            return None
        
        # Crear opciones según tipo de juego
        if game_type == 'complete_phrase':
            # MINIJUEGO 1: Completar frases (4 opciones en Bora)
            # Obtener 3 opciones incorrectas aleatorias
            incorrect_options = self.db.query(BoraPhrase).filter(
                BoraPhrase.id != phrase.id,
                BoraPhrase.category == phrase.category
            ).order_by(func.random()).limit(3).all()
            
            # Si no hay suficientes en la misma categoría, obtener de cualquier categoría
            if len(incorrect_options) < 3:
                incorrect_options = self.db.query(BoraPhrase).filter(
                    BoraPhrase.id != phrase.id
                ).order_by(func.random()).limit(3).all()
            
            # Para completar frases, las opciones son frases completas en Bora
            options = [phrase.bora_text]
            for opt in incorrect_options[:3]:
                options.append(opt.bora_text)
            
            # Asegurar que tengamos 4 opciones únicas
            options = list(set(options))  # Eliminar duplicados
            while len(options) < 4:
                options.append(f"Opción {len(options) + 1}")  # Placeholder si faltan
            
            # Guardar la respuesta correcta antes de mezclar
            correct_answer = options[0]
            
            # Mezclar opciones
            random.shuffle(options)
            correct_index = options.index(correct_answer)
            
            return {
                "id": phrase.id,
                "bora_text": phrase.bora_text,
                "spanish_translation": phrase.spanish_translation,
                "category": phrase.category,
                "difficulty_level": phrase.difficulty_level,
                "usage_context": phrase.usage_context,
                "pronunciation_guide": phrase.pronunciation_guide,
                "options": options,
                "correct_answer": correct_answer,
                "correct_index": correct_index,
                "hint": phrase.usage_context or f"Categoría: {phrase.category}"
            }
        
        elif game_type == 'context_match':
            # MINIJUEGO 2: Contexto y selección (2 opciones en Bora)
            # Obtener 1 opción incorrecta de la misma categoría
            incorrect_option = self.db.query(BoraPhrase).filter(
                BoraPhrase.id != phrase.id,
                BoraPhrase.category == phrase.category
            ).order_by(func.random()).first()
            
            # Si no hay en la misma categoría, obtener de cualquier categoría
            if not incorrect_option:
                incorrect_option = self.db.query(BoraPhrase).filter(
                    BoraPhrase.id != phrase.id
                ).order_by(func.random()).first()
            
            # Crear 2 opciones en Bora
            options = [phrase.bora_text]
            if incorrect_option:
                options.append(incorrect_option.bora_text)
            else:
                # Fallback si no hay otra frase
                options.append("Opción alternativa")
            
            # Asegurar opciones únicas
            options = list(set(options))
            while len(options) < 2:
                options.append(f"Opción {len(options) + 1}")
            
            # Guardar la respuesta correcta antes de mezclar
            correct_answer = phrase.bora_text
            
            # Mezclar opciones
            random.shuffle(options)
            correct_index = options.index(correct_answer)
            
            # Crear contexto completo
            context_description = phrase.usage_context or f"Situación relacionada con {phrase.category}"
            full_context = f"{context_description}. Traducción: '{phrase.spanish_translation}'"
            
            return {
                "id": phrase.id,
                "bora_text": phrase.bora_text,
                "spanish_translation": phrase.spanish_translation,
                "category": phrase.category,
                "difficulty_level": phrase.difficulty_level,
                "usage_context": phrase.usage_context,
                "pronunciation_guide": phrase.pronunciation_guide,
                "options": options,  # 2 opciones en Bora
                "correct_answer": correct_answer,  # Respuesta en Bora
                "correct_index": correct_index,
                "hint": phrase.pronunciation_guide or "Escucha con atención",
                "context": full_context  # Contexto completo para mostrar
            }
        
        else:
            # Tipo de juego no soportado
            return None
    
    def check_answer(
        self, 
        session_id: int,
        phrase_id: int, 
        selected_option: str
    ) -> Dict:
        """
        Verificar si la respuesta seleccionada es correcta y guardarla
        
        Args:
            session_id: ID de la sesión actual
            phrase_id: ID de la frase/pregunta
            selected_option: Opción seleccionada por el usuario
            
        Returns:
            dict con:
            - correct (bool): Si la respuesta es correcta
            - points (int): Puntos ganados
            - correct_answer (str): Respuesta correcta
            - explanation (str): Explicación
        """
        # Obtener frase de la BD
        phrase = self.db.query(BoraPhrase).filter(BoraPhrase.id == phrase_id).first()
        
        if not phrase:
            return {
                "correct": False,
                "points": 0,
                "correct_answer": "",
                "explanation": "Pregunta no encontrada"
            }
        
        # Obtener sesión para saber el tipo de juego
        session = self.db.query(GameSession).filter(GameSession.id == session_id).first()
        if not session:
            return {
                "correct": False,
                "points": 0,
                "correct_answer": "",
                "explanation": "Sesión no encontrada"
            }
        
        # Determinar respuesta correcta según tipo de juego
        # Para ambos juegos, la respuesta correcta es el texto en Bora
        correct_answer = phrase.bora_text
        
        # Comparar respuestas (normalizar espacios y mayúsculas)
        is_correct = selected_option.strip().lower() == correct_answer.strip().lower()
        points = 10 if is_correct else 0
        
        # Guardar respuesta en la BD
        answer = GameAnswer(
            session_id=session_id,
            phrase_id=phrase_id,
            user_answer=selected_option,
            correct_answer=correct_answer,
            is_correct=is_correct,
            points_earned=points
        )
        
        self.db.add(answer)
        self.db.commit()
        
        explanation = (
            f"¡Correcto! '{correct_answer}' significa '{phrase.spanish_translation}'" 
            if is_correct 
            else f"La respuesta correcta era '{correct_answer}'. Significa '{phrase.spanish_translation}'"
        )
        
        return {
            "correct": is_correct,
            "points": points,
            "correct_answer": correct_answer,
            "explanation": explanation
        }
    
    def complete_session(
        self,
        session_id: int,
        total_questions: int,
        correct_answers: int,
        incorrect_answers: int,
        total_score: int,
        is_perfect: bool,
        time_spent_seconds: int
    ) -> Optional[GameSession]:
        """
        Finalizar sesión de juego y actualizar estadísticas del usuario
        
        Args:
            session_id: ID de la sesión
            total_questions: Total de preguntas respondidas
            correct_answers: Número de respuestas correctas
            incorrect_answers: Número de respuestas incorrectas
            total_score: Puntaje total obtenido
            is_perfect: Si el juego fue perfecto
            time_spent_seconds: Tiempo en segundos
            
        Returns:
            GameSession actualizado o None si no se encuentra
        """
        # Obtener sesión
        session = self.db.query(GameSession).filter(GameSession.id == session_id).first()
        if not session:
            return None
        
        # Actualizar sesión
        session.total_questions = total_questions
        session.correct_answers = correct_answers
        session.incorrect_answers = incorrect_answers
        session.total_score = total_score
        session.is_perfect = is_perfect
        session.time_spent_seconds = time_spent_seconds
        session.completed_at = datetime.utcnow()
        
        # Actualizar estadísticas del usuario (tabla users)
        user = self.db.query(User).filter(User.id == session.user_id).first()
        if user:
            user.total_points += total_score
            
            # Actualizar nivel basado en puntos
            if user.total_points >= 5000:
                user.level = 5
                user.current_title = "Nativo Bora"
            elif user.total_points >= 2000:
                user.level = 4
                user.current_title = "Hablante Avanzado"
            elif user.total_points >= 1000:
                user.level = 3
                user.current_title = "Entusiasta"
            elif user.total_points >= 500:
                user.level = 2
                user.current_title = "Intermedio"
            else:
                user.level = 1
                user.current_title = "Principiante"
        
        self.db.commit()
        
        # Actualizar misiones diarias y progreso de nivel
        try:
            from services.profile_service import ProfileService
            profile_service = ProfileService(self.db)
            
            # Otorgar puntos por el juego
            profile_service.add_points(session.user_id, total_score, "Juego completado")
            
            # Actualizar progreso de misión de juegos
            profile_service.update_mission_progress(session.user_id, 'game_plays', 1)
            
            # Si fue perfecto, actualizar misión de juegos perfectos
            if is_perfect:
                profile_service.update_mission_progress(session.user_id, 'perfect_games', 1)
            
            # Persistir los cambios de gamificación
            self.db.commit()
        except Exception as e:
            # Revertir solo las actualizaciones de gamificación si fallan
            self.db.rollback()
            print(f"Error actualizando misiones: {e}")
        
        self.db.refresh(session)
        return session
    
    def get_user_stats(self, user_id: int) -> Dict:
        """
        Obtener estadísticas completas del usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            dict con estadísticas del usuario
        """
        # Obtener todas las sesiones del usuario
        sessions = self.db.query(GameSession).filter(
            GameSession.user_id == user_id,
            GameSession.completed_at != None  # Solo sesiones completadas
        ).all()
        
        total_sessions = len(sessions)
        total_questions = sum(s.total_questions for s in sessions)
        correct_answers = sum(s.correct_answers for s in sessions)
        total_score = sum(s.total_score for s in sessions)
        perfect_games = sum(1 for s in sessions if s.is_perfect)
        
        # Calcular precisión
        accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        # Juegos por tipo
        games_by_type = {}
        for session in sessions:
            game_type = session.game_type
            if game_type not in games_by_type:
                games_by_type[game_type] = 0
            games_by_type[game_type] += 1
        
        return {
            "total_sessions": total_sessions,
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "accuracy": round(accuracy, 2),
            "total_score": total_score,
            "perfect_games": perfect_games,
            "games_by_type": games_by_type
        }
    
    def get_user_sessions(self, user_id: int, limit: int = 10) -> List[GameSession]:
        """
        Obtener historial de sesiones del usuario
        
        Args:
            user_id: ID del usuario
            limit: Límite de sesiones a retornar
            
        Returns:
            Lista de GameSession
        """
        sessions = self.db.query(GameSession).filter(
            GameSession.user_id == user_id
        ).order_by(desc(GameSession.completed_at)).limit(limit).all()
        
        return sessions
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """
        Obtener tabla de clasificación por puntos
        
        Args:
            limit: Número de usuarios a retornar
            
        Returns:
            Lista de diccionarios con datos del leaderboard
        """
        users = self.db.query(User).filter(
            User.is_active == True
        ).order_by(desc(User.total_points)).limit(limit).all()
        
        leaderboard = []
        for rank, user in enumerate(users, start=1):
            # Contar juegos completados
            games_completed = self.db.query(func.count(GameSession.id)).filter(
                GameSession.user_id == user.id,
                GameSession.completed_at != None
            ).scalar()
            
            # Contar juegos perfectos
            perfect_games = self.db.query(func.count(GameSession.id)).filter(
                GameSession.user_id == user.id,
                GameSession.is_perfect == True
            ).scalar()
            
            leaderboard.append({
                "rank": rank,
                "username": user.username,
                "avatar_url": user.avatar_url,
                "total_points": user.total_points,
                "level": user.level,
                "current_title": user.current_title,
                "games_completed": games_completed or 0,
                "perfect_games": perfect_games or 0
            })
        
        return leaderboard
