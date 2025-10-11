"""
Script para poblar las tablas de gamificación en Supabase
Crea misiones diarias y recompensas según la especificación del sistema
"""
import sys
from pathlib import Path
from datetime import date

# Agregar el directorio backend al path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from adapters.supabase_adapter import SupabaseAdapter

def populate_gamification_data():
    print("🚀 Poblando datos de gamificación en Supabase...")
    print("=" * 70)
    
    adapter = SupabaseAdapter()
    
    # ========================================
    # 1. CREAR MISIONES DIARIAS (3 misiones)
    # ========================================
    print("\n📋 Creando Misiones Diarias...")
    print("-" * 70)
    
    missions = [
        {
            "mission_type": "chat_questions",
            "mission_name": "Pregunta al Mentor",
            "mission_description": "Realiza 3 consultas al Mentor Bora hoy",
            "target_value": 3,
            "current_value": 0,
            "points_reward": 50,
            "is_completed": False
        },
        {
            "mission_type": "game_plays",
            "mission_name": "Practica Jugando",
            "mission_description": "Completa 2 sesiones de minijuegos hoy",
            "target_value": 2,
            "current_value": 0,
            "points_reward": 30,
            "is_completed": False
        },
        {
            "mission_type": "perfect_games",
            "mission_name": "Perfección Bora",
            "mission_description": "Logra 1 partida perfecta (100% de aciertos)",
            "target_value": 1,
            "current_value": 0,
            "points_reward": 100,
            "is_completed": False
        }
    ]
    
    # Verificar si ya existen misiones
    existing = adapter.client.table('daily_missions').select('*').execute()
    if existing.data and len(existing.data) > 0:
        print("⚠️  Ya existen misiones en la base de datos")
        print(f"   Total: {len(existing.data)} misiones")
    else:
        # Insertar misiones (sin user_id, se crearán por usuario al usarlas)
        print("✅ Las misiones se crearán automáticamente por usuario")
        print(f"   Tipos de misiones configurados: {len(missions)}")
        for mission in missions:
            print(f"   - {mission['mission_name']}: {mission['points_reward']} pts")
    
    # ========================================
    # 2. CREAR RECOMPENSAS
    # ========================================
    print("\n🎁 Creando Recompensas...")
    print("-" * 70)
    
    rewards = [
        # PUNTOS por acciones
        {
            "name": "Bienvenida Bora",
            "description": "Recompensa por crear tu cuenta",
            "icon_url": "🎉",
            "points_required": 0,
            "reward_type": "points",
            "reward_value": "50",
            "is_active": True
        },
        {
            "name": "Explorador de Inicio",
            "description": "Recompensa por visitar la interfaz principal",
            "icon_url": "🏠",
            "points_required": 0,
            "reward_type": "points",
            "reward_value": "10",
            "is_active": True
        },
        {
            "name": "Cazador de Frases",
            "description": "Recompensa por visitar la interfaz de frases",
            "icon_url": "📚",
            "points_required": 0,
            "reward_type": "points",
            "reward_value": "10",
            "is_active": True
        },
        {
            "name": "Jugador Curioso",
            "description": "Recompensa por visitar la interfaz de minijuegos",
            "icon_url": "🎮",
            "points_required": 0,
            "reward_type": "points",
            "reward_value": "10",
            "is_active": True
        },
        {
            "name": "Respuesta Correcta",
            "description": "Puntos por responder correctamente una pregunta",
            "icon_url": "✅",
            "points_required": 0,
            "reward_type": "points",
            "reward_value": "10",
            "is_active": True
        },
        {
            "name": "Maestro Completa Frases",
            "description": "Puntos por lograr puntuación perfecta en Completa la Frase",
            "icon_url": "🎯",
            "points_required": 0,
            "reward_type": "points",
            "reward_value": "100",
            "is_active": True
        },
        {
            "name": "Maestro del Contexto",
            "description": "Puntos por lograr puntuación perfecta en Contexto Correcto",
            "icon_url": "🏆",
            "points_required": 0,
            "reward_type": "points",
            "reward_value": "100",
            "is_active": True
        },
        
        # AVATARES temáticos (reclamables con puntos)
        {
            "name": "Avatar Jugador Bora",
            "description": "Avatar especial por jugar a los minijuegos",
            "icon_url": "🎲",
            "points_required": 100,
            "reward_type": "avatar",
            "reward_value": "https://ui-avatars.com/api/?name=Jugador&background=10b981&color=fff&size=200",
            "is_active": True
        },
        {
            "name": "Avatar Entusiasta Bora",
            "description": "Avatar con diseño Bora tradicional",
            "icon_url": "🌟",
            "points_required": 500,
            "reward_type": "avatar",
            "reward_value": "https://ui-avatars.com/api/?name=Entusiasta&background=059669&color=fff&size=200",
            "is_active": True
        },
        {
            "name": "Avatar Hablante Bora",
            "description": "Avatar de hablante avanzado",
            "icon_url": "💬",
            "points_required": 1000,
            "reward_type": "avatar",
            "reward_value": "https://ui-avatars.com/api/?name=Hablante&background=047857&color=fff&size=200",
            "is_active": True
        },
        {
            "name": "Avatar Nativo Bora",
            "description": "Avatar de maestro del idioma Bora",
            "icon_url": "👑",
            "points_required": 2000,
            "reward_type": "avatar",
            "reward_value": "https://ui-avatars.com/api/?name=Nativo&background=065f46&color=fff&size=200",
            "is_active": True
        },
        
        # LOGROS especiales
        {
            "name": "Maestro de Frases",
            "description": "Completa 10 partidas perfectas",
            "icon_url": "🎯",
            "points_required": 1500,
            "reward_type": "achievement",
            "reward_value": "perfect_master",
            "is_active": True
        },
        {
            "name": "Campeón del Chat",
            "description": "Realiza 50 consultas al mentor",
            "icon_url": "💬",
            "points_required": 800,
            "reward_type": "achievement",
            "reward_value": "chat_champion",
            "is_active": True
        },
        {
            "name": "Explorador de Frases",
            "description": "Aprende 100 frases diferentes",
            "icon_url": "📚",
            "points_required": 1200,
            "reward_type": "achievement",
            "reward_value": "phrase_explorer",
            "is_active": True
        },
        
        # TÍTULOS especiales
        {
            "name": "Título: Guerrero Bora",
            "description": "Título especial por dedicación",
            "icon_url": "⚔️",
            "points_required": 3000,
            "reward_type": "title",
            "reward_value": "Guerrero Bora",
            "is_active": True
        },
        {
            "name": "Título: Sabio Bora",
            "description": "Título especial por sabiduría",
            "icon_url": "🧙",
            "points_required": 5000,
            "reward_type": "title",
            "reward_value": "Sabio Bora",
            "is_active": True
        }
    ]
    
    # Verificar si ya existen recompensas
    existing_rewards = adapter.client.table('rewards').select('*').execute()
    
    if existing_rewards.data and len(existing_rewards.data) > 0:
        print(f"⚠️  Ya existen {len(existing_rewards.data)} recompensas en la base de datos")
        print("   Limpiando recompensas existentes...")
        # Limpiar recompensas existentes
        adapter.client.table('rewards').delete().neq('id', 0).execute()
    
    # Insertar recompensas
    try:
        result = adapter.client.table('rewards').insert(rewards).execute()
        print(f"✅ {len(rewards)} recompensas creadas exitosamente")
        print("\n   📊 Resumen de Recompensas:")
        print(f"      - Puntos automáticos: 7 recompensas")
        print(f"      - Avatares temáticos: 4 avatares")
        print(f"      - Logros especiales: 3 logros")
        print(f"      - Títulos especiales: 2 títulos")
    except Exception as e:
        print(f"❌ Error al crear recompensas: {str(e)}")
    
    print("\n" + "=" * 70)
    print("✅ Proceso completado exitosamente")
    print("\n💡 Próximos pasos:")
    print("   1. Inicia sesión en la aplicación")
    print("   2. Ve a tu perfil para ver las recompensas disponibles")
    print("   3. Completa misiones para ganar puntos")
    print("   4. Reclama avatares y logros con tus puntos")
    print("=" * 70)

if __name__ == "__main__":
    populate_gamification_data()
