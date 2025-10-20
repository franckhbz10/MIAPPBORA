"""
Configuración central de MIAPPBORA
Carga .env automáticamente con pydantic-settings (v2).
"""

from typing import Optional, List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---- Config de pydantic-settings ----
    # Carga .env; ignora claves no declaradas; case-sensitive opcional
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ---- App ----
    APP_NAME: str = "MIAPPBORA"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ---- Base de datos ----
    # Si POSTGRES_URL está en .env, la usaremos como DATABASE_URL
    DATABASE_URL: Optional[str] = None
    POSTGRES_URL: Optional[str] = None  # alias “supabase pg uri”

    # ---- Supabase ----
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None

    # ---- HuggingFace ----
    HUGGINGFACE_API_KEY: Optional[str] = None
    USE_EMBEDDING_API: bool = False

    # ---- Modelos ----
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    # Modelo LLM por defecto (probando Qwen 3 1.7B)
    LLM_MODEL: str = "Qwen/Qwen3-1.7B"
    EMBEDDING_DIMENSION: int = 384

    # Backend del LLM: "transformers" (local) o "inference-api" (HuggingFace Inference)
    LLM_BACKEND: str = "transformers"
    # Parámetros de generación por defecto (pueden sobreescribirse por llamada)
    LLM_MAX_NEW_TOKENS: int = 256
    LLM_TEMPERATURE: float = 0.7
    LLM_TOP_P: float = 0.9
    # Control de plantilla de chat (modelos con chat_template)
    LLM_ENABLE_THINKING: bool = False
    # Config de carga de modelo local
    LLM_DEVICE_MAP: str = "auto"  # e.g., "auto", "cpu", "cuda"
    LLM_DTYPE: str = "auto"       # "auto", "bfloat16", "float16", "float32"

    # ---- JWT ----
    SECRET_KEY: str = "change-me"
    JWT_SECRET: Optional[str] = None  # si no se setea, usaremos SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 días

    # ---- CORS ----
    # Puedes pasar JSON o CSV en .env (ver validador)
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",  # Puerto alternativo de Vite
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",  # Puerto alternativo IPv4
    ]

    # ---- RAG ----
    TOP_K_RESULTS: int = 3
    SIMILARITY_THRESHOLD: float = 0.7

    # ====== Validadores / post-procesado ======

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """
        Permite CORS_ORIGINS como:
        - JSON: '["http://a","http://b"]'
        - CSV:  'http://a,http://b'
        - Lista Python ya parseada
        """
        if v is None:
            return v
        if isinstance(v, list):
            return v
        s = str(v).strip()
        if s.startswith("["):
            # JSON
            import json
            return json.loads(s)
        # CSV
        return [x.strip() for x in s.split(",") if x.strip()]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fill_database_url(cls, v, info):
        """
        Si DATABASE_URL no está definida pero POSTGRES_URL sí,
        usamos POSTGRES_URL como fallback.
        """
        if v:
            return v
        # En modo 'before', Pydantic te da los valores previos en info.data
        data = info.data or {}
        pg = data.get("POSTGRES_URL")
        return pg or v


    @field_validator("JWT_SECRET", mode="after")
    def default_jwt_secret(cls, v, info):
        """
        Si no hay JWT_SECRET, usa SECRET_KEY.
        """
        if v:
            return v
        data = info.data or {}
        return data.get("SECRET_KEY")

# instancia reutilizable
settings = Settings()

def get_settings() -> Settings:
    return settings
