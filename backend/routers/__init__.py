"""
Inicialización del paquete routers
"""
from . import health_router, auth_router, game_router, profile_router, lexicon_router

__all__ = [
	'health_router',
	'auth_router',
	'game_router',
	'profile_router',
	'lexicon_router',
]
