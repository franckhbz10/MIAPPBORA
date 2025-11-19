"""
Inicialización del paquete routers

NOTA: lexicon_router NO se importa automáticamente porque requiere
dependencias ML opcionales (sentence-transformers). Se importa
dinámicamente en main.py con try/except.
"""
from . import health_router, auth_router, game_router, profile_router, admin_router

__all__ = [
	'health_router',
	'auth_router',
	'game_router',
	'profile_router',
	'admin_router',
	# 'lexicon_router',  # Import dinámico en main.py
]
