"""
Modelos de base de datos para MIAPPBORA
Sincronizado con esquema de Supabase PostgreSQL
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    """
    Modelo de Usuario
    Almacena información de autenticación y perfil
    """
    __tablename__ = "users"

    # Campos base
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(Text, nullable=False)
    avatar_url = Column(Text, default='https://ui-avatars.com/api/?name=User')

    # Gamificación
    level = Column(Integer, default=1)
    total_points = Column(Integer, default=0)
    current_title = Column(String(100), default='Principiante')
    is_active = Column(Boolean, default=True)    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relaciones
    chat_conversations = relationship("ChatConversation", back_populates="user", cascade="all, delete-orphan")
    game_sessions = relationship("GameSession", back_populates="user", cascade="all, delete-orphan")
    daily_missions = relationship("DailyMission", back_populates="user", cascade="all, delete-orphan")
    user_rewards = relationship("UserReward", back_populates="user", cascade="all, delete-orphan")
    level_progress = relationship("LevelProgress", back_populates="user", uselist=False, cascade="all, delete-orphan")
    app_feedback = relationship("AppFeedback", back_populates="user", cascade="all, delete-orphan")


class BoraPhrase(Base):
    """
    Modelo de Frases del Corpus Bora-Español
    Almacena todas las frases del corpus para aprendizaje
    """
    __tablename__ = "bora_phrases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bora_text = Column(Text, nullable=False)
    spanish_translation = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    difficulty_level = Column(Integer, default=1, index=True)
    usage_context = Column(Text, nullable=True)
    pronunciation_guide = Column(Text, nullable=True)
    audio_url = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    embeddings = relationship("PhraseEmbedding", back_populates="phrase", cascade="all, delete-orphan")
    game_answers = relationship("GameAnswer", back_populates="phrase")


class PhraseEmbedding(Base):
    """
    Modelo de Embeddings para Vector Store (RAG)
    Almacena representaciones vectoriales de frases
    """
    __tablename__ = "phrase_embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phrase_id = Column(Integer, ForeignKey('bora_phrases.id', ondelete='CASCADE'), nullable=False)
    
    # En Supabase con pgvector: vector(384)
    # Aquí usamos Text como placeholder, el tipo real se configura en Supabase
    embedding = Column(Text, nullable=False)  # Será vector(384) en Supabase
    model_version = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    phrase = relationship("BoraPhrase", back_populates="embeddings")


class ChatConversation(Base):
    """
    Modelo de Conversaciones del Chat RAG (Mentor Bora)
    Agrupa mensajes en conversaciones
    """
    __tablename__ = "chat_conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String(200), default='Nueva conversación')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="chat_conversations")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")


class ChatMessage(Base):
    """
    Modelo de Mensajes del Chat
    Almacena el historial de conversaciones con el asistente
    """
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('chat_conversations.id', ondelete='CASCADE'), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' o 'assistant'
    content = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    conversation = relationship("ChatConversation", back_populates="messages")


class GameSession(Base):
    """
    Modelo de Sesiones de Minijuegos
    Registra cada sesión completa de juego
    """
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    game_type = Column(String(50), nullable=False)  # 'complete_phrase' o 'context_match'
    
    # Estadísticas de la sesión
    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    incorrect_answers = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    is_perfect = Column(Boolean, default=False)
    time_spent_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="game_sessions")
    answers = relationship("GameAnswer", back_populates="session", cascade="all, delete-orphan")


class GameAnswer(Base):
    """
    Modelo de Respuestas de Minijuegos
    Registra cada respuesta individual dentro de una sesión
    """
    __tablename__ = "game_answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('game_sessions.id', ondelete='CASCADE'), nullable=False)
    phrase_id = Column(Integer, ForeignKey('bora_phrases.id'), nullable=True)
    
    user_answer = Column(Text, nullable=True)
    correct_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    points_earned = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    session = relationship("GameSession", back_populates="answers")
    phrase = relationship("BoraPhrase", back_populates="game_answers")


class DailyMission(Base):
    """
    Modelo de Misiones Diarias
    Sistema de gamificación con objetivos diarios
    """
    __tablename__ = "daily_missions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    mission_date = Column(Date, nullable=False, default=datetime.utcnow().date, index=True)
    mission_type = Column(String(50), nullable=False)  # 'chat_questions', 'game_plays', 'perfect_games'
    mission_name = Column(String(200), nullable=False)
    mission_description = Column(Text, nullable=True)
    
    target_value = Column(Integer, nullable=False)
    current_value = Column(Integer, default=0)
    points_reward = Column(Integer, default=10)
    
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="daily_missions")


class Reward(Base):
    """
    Modelo de Recompensas
    Define las recompensas disponibles en el sistema
    """
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    icon_url = Column(Text, nullable=True)
    
    points_required = Column(Integer, nullable=False)
    reward_type = Column(String(50), nullable=False)  # 'badge', 'avatar', 'title', 'achievement'
    reward_value = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user_rewards = relationship("UserReward", back_populates="reward")


class UserReward(Base):
    """
    Modelo de Recompensas de Usuarios
    Relaciona usuarios con las recompensas que han obtenido
    """
    __tablename__ = "user_rewards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    reward_id = Column(Integer, ForeignKey('rewards.id', ondelete='CASCADE'), nullable=False)
    
    claimed_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relaciones
    user = relationship("User", back_populates="user_rewards")
    reward = relationship("Reward", back_populates="user_rewards")


class LevelProgress(Base):
    """
    Modelo de Progreso de Nivel
    Rastrea el progreso y nivel actual del usuario
    """
    __tablename__ = "level_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    
    current_points = Column(Integer, default=0)
    points_to_next_level = Column(Integer, default=100)
    level = Column(Integer, default=1)
    title = Column(String(100), default='Principiante')
    
    # Estadísticas
    phrases_learned = Column(Integer, default=0)
    games_completed = Column(Integer, default=0)
    perfect_games = Column(Integer, default=0)
    chat_interactions = Column(Integer, default=0)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="level_progress")


class AppFeedback(Base):
    """
    Modelo de Feedback de Aplicación
    Almacena las opiniones y calificaciones de los usuarios
    """
    __tablename__ = "app_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    mentor_rating = Column(Integer, nullable=True)  # 1-5
    games_rating = Column(Integer, nullable=True)  # 1-5
    general_rating = Column(Integer, nullable=True)  # 1-5
    comments = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="app_feedback")
