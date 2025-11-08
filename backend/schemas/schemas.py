"""
Schemas de Pydantic para MIAPPBORA
Validación y serialización de datos de entrada/salida
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime


# ========================================
# SCHEMAS DE AUTENTICACIÓN
# ========================================

class UserRegister(BaseModel):
    """Schema para registro de usuario"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    phone: str = Field(..., min_length=9, max_length=20)
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = Field(None, max_length=255)
    
    @validator('phone')
    def validate_and_normalize_phone(cls, v):
        """
        Valida y normaliza el número de teléfono
        
        Reglas:
        - Debe empezar con +51 o 9
        - Se eliminan espacios y guiones
        - Se normaliza a formato: 9XXXXXXXX (9 dígitos)
        
        Ejemplos válidos:
        - "987654321" → "987654321"
        - "987 654 321" → "987654321"
        - "+51987654321" → "987654321"
        - "+51 987 654 321" → "987654321"
        - "9 8 7 6 5 4 3 2 1" → "987654321"
        """
        import re
        
        if not v:
            raise ValueError('El teléfono es requerido')
        
        # Eliminar espacios, guiones, paréntesis
        phone_clean = re.sub(r'[\s\-\(\)]', '', v)
        
        # Si empieza con +51, quitarlo
        if phone_clean.startswith('+51'):
            phone_clean = phone_clean[3:]
        
        # Verificar que empiece con 9
        if not phone_clean.startswith('9'):
            raise ValueError('El número de teléfono debe empezar con 9')
        
        # Verificar que tenga exactamente 9 dígitos
        if not re.match(r'^9\d{8}$', phone_clean):
            raise ValueError('El número de teléfono debe tener 9 dígitos y empezar con 9')
        
        return phone_clean


class UserLogin(BaseModel):
    """Schema para login de usuario"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema para respuesta de usuario"""
    id: int  # Changed from str to int (SERIAL)
    email: str
    username: str
    full_name: Optional[str]  # Changed from name to full_name
    avatar_url: Optional[str]
    total_points: int  # Changed from points to total_points
    level: int
    current_title: str  # Added
    is_active: bool  # Added
    created_at: datetime
    last_login: Optional[datetime] = None  # Added

    class Config:
        from_attributes = True
class Token(BaseModel):
    """Schema para token JWT"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema para datos del token"""
    user_id: Optional[str] = None


class LoginResponse(BaseModel):
    """Schema para respuesta de login"""
    user: UserResponse
    access_token: str
    token_type: str = "bearer"


# ========================================
# SCHEMAS DE FRASES BORA
# ========================================

class BoraPhraseBase(BaseModel):
    """Schema base para frases Bora"""
    bora_text: str
    spanish_translation: str  # Changed from spanish_text
    category: str
    usage_context: Optional[str] = None  # Changed from context
    difficulty_level: int = 1  # Changed from difficulty (str) to difficulty_level (int)
    pronunciation_guide: Optional[str] = None  # Added
    audio_url: Optional[str] = None  # Added


class BoraPhraseCreate(BoraPhraseBase):
    """Schema para crear frase Bora"""
    pass


class BoraPhraseResponse(BoraPhraseBase):
    """Schema para respuesta de frase Bora"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========================================
# SCHEMAS DE CHAT
# ========================================

class ChatMessageCreate(BaseModel):
    """Schema para crear mensaje de chat"""
    message: str = Field(..., min_length=1, max_length=1000)
    conversation_id: Optional[int] = None


class ChatMessageResponse(BaseModel):
    """Schema para respuesta de mensaje"""
    id: int
    role: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatConversationResponse(BaseModel):
    """Schema para respuesta de conversación"""
    id: int
    title: Optional[str]
    created_at: datetime
    messages: List[ChatMessageResponse] = []
    
    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """Schema para respuesta del chat RAG"""
    response: str
    conversation_id: int
    sources: List[BoraPhraseResponse] = []


# ========================================
# SCHEMAS DE JUEGOS
# ========================================

class GameSessionCreate(BaseModel):
    """Schema para crear nueva sesión de juego"""
    game_type: str = Field(..., pattern="^(complete_phrase|context_match)$")


class GameSessionUpdate(BaseModel):
    """Schema para actualizar sesión al finalizar"""
    total_questions: int
    correct_answers: int
    incorrect_answers: int
    total_score: int
    is_perfect: bool
    time_spent_seconds: Optional[int] = None


class GameAnswerCreate(BaseModel):
    """Schema para crear respuesta individual"""
    session_id: int
    phrase_id: Optional[int] = None
    user_answer: str
    correct_answer: str
    is_correct: bool
    points_earned: int


class GameAnswerResponse(BaseModel):
    """Schema para respuesta de juego"""
    id: int
    session_id: int
    phrase_id: Optional[int]
    user_answer: str
    correct_answer: str
    is_correct: bool
    points_earned: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class GameSessionResponse(BaseModel):
    """Schema para respuesta de sesión completa"""
    id: int
    user_id: int
    game_type: str
    total_questions: int
    correct_answers: int
    incorrect_answers: int
    total_score: int
    is_perfect: bool
    time_spent_seconds: Optional[int]
    completed_at: datetime
    answers: List[GameAnswerResponse] = []
    
    class Config:
        from_attributes = True


class GameQuestionResponse(BaseModel):
    """Schema para pregunta de juego"""
    id: int
    bora_text: str
    spanish_translation: str
    category: str
    difficulty_level: int
    usage_context: Optional[str] = None
    pronunciation_guide: Optional[str] = None
    options: List[str]  # Generadas dinámicamente
    correct_answer: str
    hint: Optional[str] = None


class GameAnswerSubmit(BaseModel):
    """Schema para enviar respuesta de juego"""
    session_id: int
    phrase_id: int
    selected_option: str  # Texto de la opción seleccionada, no el índice


class UserGameStats(BaseModel):
    """Schema para estadísticas completas del usuario"""
    total_sessions: int
    total_questions: int
    correct_answers: int
    accuracy: float
    total_score: int
    perfect_games: int
    games_by_type: dict


class GameStatsResponse(BaseModel):
    """Schema para estadísticas de juegos (legacy)"""
    total_games: int
    correct_answers: int
    accuracy: float
    points_earned: int
    games_by_category: dict


# ========================================
# SCHEMAS DE PROGRESO
# ========================================

class UserProgressResponse(BaseModel):
    """Schema para progreso del usuario"""
    category: str
    phrases_learned: int
    accuracy: float
    last_practice: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """Schema completo del perfil de usuario"""
    user: UserResponse
    progress: List[UserProgressResponse]
    stats: GameStatsResponse


# ========================================
# SCHEMAS DE MISIONES
# ========================================

class DailyMissionResponse(BaseModel):
    """Schema para misión diaria"""
    id: int
    mission_type: str
    mission_name: str  # Added
    mission_description: Optional[str] = None  # Added
    target_value: int  # Changed from target
    current_value: int  # Changed from progress
    is_completed: bool  # Changed from completed
    points_reward: int  # Changed from reward_points
    mission_date: datetime  # Changed from date
    completed_at: Optional[datetime] = None  # Added

    class Config:
        from_attributes = True
class MissionCompleteResponse(BaseModel):
    """Schema para respuesta de misión completada"""
    mission: DailyMissionResponse
    points_earned: int
    new_total_points: int


# ========================================
# SCHEMAS DE LEADERBOARD
# ========================================

class LeaderboardEntry(BaseModel):
    """Schema para entrada del leaderboard"""
    rank: int
    username: str
    avatar_url: Optional[str]
    total_points: int  # Changed from points
    level: int
    current_title: str  # Added


class LeaderboardResponse(BaseModel):
    """Schema para respuesta del leaderboard"""
    top_users: List[LeaderboardEntry]
    user_rank: Optional[int] = None
    total_users: int


# ========================================
# SCHEMAS DE PERFIL Y GAMIFICACIÓN
# ========================================

class UserProfileUpdate(BaseModel):
    """Schema para actualizar perfil de usuario"""
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


class LevelProgressResponse(BaseModel):
    """Schema para progreso de nivel"""
    level: int
    title: str
    current_points: int
    points_to_next_level: int
    phrases_learned: int
    games_completed: int
    perfect_games: int
    chat_interactions: int
    
    class Config:
        from_attributes = True


class RewardResponse(BaseModel):
    """Schema para recompensa"""
    id: int
    name: str
    description: Optional[str]
    icon_url: Optional[str]
    points_required: int
    reward_type: str
    reward_value: Optional[str]
    is_active: bool
    
    class Config:
        from_attributes = True


class UserRewardResponse(BaseModel):
    """Schema para recompensa de usuario"""
    id: int
    reward: RewardResponse
    claimed_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class ClaimRewardRequest(BaseModel):
    """Schema para reclamar recompensa"""
    reward_id: int


class CompleteProfileResponse(BaseModel):
    """Schema completo del perfil con gamificación"""
    user: UserResponse
    level_progress: LevelProgressResponse
    daily_missions: List[DailyMissionResponse]
    available_rewards: List[RewardResponse]
    claimed_rewards: List[UserRewardResponse]
    
    
class DashboardStatsResponse(BaseModel):
    """Schema para estadísticas del dashboard"""
    total_visits: int
    home_visits: int
    phrases_visits: int
    games_visits: int
    chat_queries: int
    games_played: int
    perfect_games: int
