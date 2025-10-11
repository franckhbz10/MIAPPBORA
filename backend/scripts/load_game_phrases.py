"""
Script para cargar frases iniciales de Bora en la base de datos
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database_connection import SessionLocal
from models.database import BoraPhrase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Frases para minijuegos
GAME_PHRASES = [
    {
        "bora_text": "Ímíhjúkye amyéba ámíné",
        "spanish_translation": "Buenos días a ti",
        "category": "Saludos y Presentaciones",
        "difficulty_level": 1,
        "usage_context": "Saludo matutino formal",
        "pronunciation_guide": "i-MI-ju-kye a-MYE-ba A-mi-ne"
    },
    {
        "bora_text": "Díímújcú cúhúváájó ábííbá",
        "spanish_translation": "¿Cómo estás?",
        "category": "Saludos y Presentaciones",
        "difficulty_level": 1,
        "usage_context": "Pregunta común sobre el estado de alguien",
        "pronunciation_guide": "dii-MU-ju-cu cu-hu-VAA-jo a-BII-ba"
    },
    {
        "bora_text": "Tsani",
        "spanish_translation": "Bien",
        "category": "Saludos y Presentaciones",
        "difficulty_level": 1,
        "usage_context": "Respuesta común a saludos",
        "pronunciation_guide": "TSA-ni"
    },
    {
        "bora_text": "Íímé píínéjé páako",
        "spanish_translation": "Hasta luego",
        "category": "Saludos y Presentaciones",
        "difficulty_level": 1,
        "usage_context": "Despedida informal",
        "pronunciation_guide": "II-me PII-ne-je PAA-ko"
    },
    {
        "bora_text": "Píímé íhímétsi ámíné",
        "spanish_translation": "¿Cómo te llamas?",
        "category": "Saludos y Presentaciones",
        "difficulty_level": 1,
        "usage_context": "Pregunta para conocer el nombre de alguien",
        "pronunciation_guide": "PII-me i-hi-ME-tsi A-mi-ne"
    },
    {
        "bora_text": "Ííné múhúbá tsáámé",
        "spanish_translation": "Gracias",
        "category": "Conversación General",
        "difficulty_level": 1,
        "usage_context": "Expresión de agradecimiento",
        "pronunciation_guide": "II-ne MU-hu-ba TSAA-me"
    },
    {
        "bora_text": "Mííné tsííbá úváámé",
        "spanish_translation": "¿Dónde estás?",
        "category": "Ubicación",
        "difficulty_level": 1,
        "usage_context": "Pregunta sobre ubicación",
        "pronunciation_guide": "MII-ne TSII-ba u-VAA-me"
    },
    {
        "bora_text": "Páako díícájú míhímé",
        "spanish_translation": "Vamos a comer",
        "category": "Conversación General",
        "difficulty_level": 1,
        "usage_context": "Invitación a comer",
        "pronunciation_guide": "PAA-ko DII-ca-ju MI-hi-me"
    },
    {
        "bora_text": "Aahjíba mɨɨchaajúne",
        "spanish_translation": "¿Y tú cómo estás?",
        "category": "Saludos y Presentaciones",
        "difficulty_level": 2,
        "usage_context": "Reciprocar el saludo",
        "pronunciation_guide": "aa-JI-ba mɨɨ-chaa-JU-ne"
    },
    {
        "bora_text": "Tsanípɨjíba",
        "spanish_translation": "También estoy bien",
        "category": "Saludos y Presentaciones",
        "difficulty_level": 2,
        "usage_context": "Respuesta recíproca positiva",
        "pronunciation_guide": "tsa-NI-pɨ-JI-ba"
    },
    {
        "bora_text": "Tsúudi ajchyé",
        "spanish_translation": "Hasta luego",
        "category": "Saludos y Presentaciones",
        "difficulty_level": 1,
        "usage_context": "Despedida común",
        "pronunciation_guide": "TSUU-di aj-CHY-e"
    },
    {
        "bora_text": "Mɨɨ́jtsíbajé",
        "spanish_translation": "¿Qué estás haciendo?",
        "category": "Conversación General",
        "difficulty_level": 2,
        "usage_context": "Pregunta sobre actividad actual",
        "pronunciation_guide": "mɨɨ-JI-tsi-ba-je"
    },
    {
        "bora_text": "Óomene",
        "spanish_translation": "No sé",
        "category": "Conversación General",
        "difficulty_level": 1,
        "usage_context": "Expresar desconocimiento",
        "pronunciation_guide": "OO-me-ne"
    },
    {
        "bora_text": "Mɨɨ́ba",
        "spanish_translation": "Sí",
        "category": "Conversación General",
        "difficulty_level": 1,
        "usage_context": "Afirmación",
        "pronunciation_guide": "mɨɨ-BA"
    },
    {
        "bora_text": "Ajcá",
        "spanish_translation": "No",
        "category": "Conversación General",
        "difficulty_level": 1,
        "usage_context": "Negación",
        "pronunciation_guide": "aj-CA"
    },
    {
        "bora_text": "Díhcyúúbá",
        "spanish_translation": "Ayúdame",
        "category": "Emergencias",
        "difficulty_level": 2,
        "usage_context": "Solicitar ayuda",
        "pronunciation_guide": "DI-hcy-UU-ba"
    },
    {
        "bora_text": "Tsáni únéjáábá",
        "spanish_translation": "Estoy bien/De acuerdo",
        "category": "Conversación General",
        "difficulty_level": 2,
        "usage_context": "Confirmar acuerdo o bienestar",
        "pronunciation_guide": "TSA-ni u-NE-jaa-ba"
    },
    {
        "bora_text": "Amyébájéné",
        "spanish_translation": "Te extraño",
        "category": "Relaciones Cotidianas",
        "difficulty_level": 2,
        "usage_context": "Expresar que extrañas a alguien",
        "pronunciation_guide": "a-MYE-ba-JE-ne"
    },
    {
        "bora_text": "Púújé íímé",
        "spanish_translation": "Cuídate",
        "category": "Saludos y Presentaciones",
        "difficulty_level": 2,
        "usage_context": "Despedida con buenos deseos",
        "pronunciation_guide": "PUU-je II-me"
    },
    {
        "bora_text": "Mɨhɨ́úcú",
        "spanish_translation": "Perdón/Disculpa",
        "category": "Conversación General",
        "difficulty_level": 1,
        "usage_context": "Pedir disculpas",
        "pronunciation_guide": "mɨ-hɨ-U-cu"
    }
]


def load_game_phrases():
    """Cargar frases para minijuegos"""
    db = SessionLocal()
    
    try:
        # Verificar si ya existen frases
        existing_count = db.query(BoraPhrase).count()
        
        if existing_count > 0:
            logger.info(f"Ya existen {existing_count} frases en la base de datos")
            response = input("¿Deseas agregar más frases de todas formas? (s/n): ")
            if response.lower() != 's':
                logger.info("Operación cancelada")
                return
        
        # Insertar frases
        added = 0
        for phrase_data in GAME_PHRASES:
            # Verificar si la frase ya existe
            existing = db.query(BoraPhrase).filter(
                BoraPhrase.bora_text == phrase_data["bora_text"]
            ).first()
            
            if not existing:
                phrase = BoraPhrase(**phrase_data)
                db.add(phrase)
                added += 1
                logger.info(f"✓ Agregada: {phrase_data['bora_text']} - {phrase_data['spanish_translation']}")
            else:
                logger.info(f"⊘ Ya existe: {phrase_data['bora_text']}")
        
        db.commit()
        logger.info(f"\n✅ {added} frases agregadas exitosamente")
        logger.info(f"📊 Total de frases en BD: {db.query(BoraPhrase).count()}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("🎮 Cargando frases para minijuegos...")
    logger.info(f"📦 {len(GAME_PHRASES)} frases disponibles para cargar\n")
    load_game_phrases()
