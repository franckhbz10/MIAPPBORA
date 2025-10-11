"""
Script para cargar el corpus de frases Bora-Español en Supabase
Ejecutar: python scripts/load_bora_corpus.py
"""
import sys
from pathlib import Path
import asyncio

# Agregar directorio padre al path
sys.path.append(str(Path(__file__).parent.parent))

from adapters.supabase_adapter import get_supabase_adapter
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Corpus completo de frases Bora organizadas por categorías
BORA_CORPUS = [
    # ==========================================
    # CATEGORÍA 1: Saludos y Presentaciones
    # ==========================================
    {
        "bora_text": "Mɨɨchaajúne",
        "spanish_translation": "¿Cómo estás?",
        "category": "Saludos y Presentaciones",
        "difficulty_level": 1,
        "usage_context": "Saludo informal cotidiano",
        "pronunciation_guide": "mii-chaa-JU-ne"
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
        "bora_text": "Aahjíba mɨɨchaajúne",
        "spanish_translation": "¿Y tú cómo estás?",
        "category": "Saludos y Presentaciones",
        "difficulty_level": 1,
        "usage_context": "Reciprocar el saludo",
        "pronunciation_guide": "aa-JI-ba mii-chaa-JU-ne"
    },
    {
        "bora_text": "Tsanípɨjíba",
        "spanish_translation": "También estoy bien",
        "category": "Saludos y Presentaciones",
        "difficulty_level": 1,
        "usage_context": "Respuesta recíproca positiva",
        "pronunciation_guide": "tsa-NI-pɨ-JI-ba"
    },
    {
        "bora_text": "Tsúudi ajchyé",
        "spanish_translation": "Hasta luego",
        "category": "Saludos y Presentaciones",
        "difficulty_level": 1,
        "usage_context": "Despedida informal",
        "pronunciation_guide": "TSUU-di aj-CHY-e"
    },
    {
        "bora_text": "Iímɨnéne",
        "spanish_translation": "¿Cómo te llamas?",
        "category": "Saludos y Presentaciones",
        "difficulty_level": 1,
        "usage_context": "Pregunta de presentación",
        "pronunciation_guide": "ii-mɨ-NE-ne"
    },
    {
        "bora_text": "Mɨɨnéjpa ___",
        "spanish_translation": "Me llamo ___",
        "category": "Saludos y Presentaciones",
        "difficulty_level": 1,
        "usage_context": "Presentación personal (llenar con nombre)",
        "pronunciation_guide": "mɨɨ-NE-jpa"
    },
    {
        "bora_text": "Pítohllé tʃííménaa",
        "spanish_translation": "Mucho gusto",
        "category": "Saludos y Presentaciones",
        "difficulty_level": 1,
        "usage_context": "Cortesía al conocer a alguien",
        "pronunciation_guide": "PI-to-lle chii-ME-naa"
    },
    {
        "bora_text": "Ɨɨ́htsidyé ímɨɨné",
        "spanish_translation": "Buenos días",
        "category": "Saludos y Presentaciones",
        "difficulty_level": 1,
        "usage_context": "Saludo matutino",
        "pronunciation_guide": "ɨɨ-htsi-DYE i-mɨɨ-NE"
    },
    {
        "bora_text": "Ímɨɨnébatsi",
        "spanish_translation": "Buenas tardes",
        "category": "Saludos y Presentaciones",
        "difficulty_level": 1,
        "usage_context": "Saludo vespertino",
        "pronunciation_guide": "i-mɨɨ-NE-ba-tsi"
    },
    
    # ==========================================
    # CATEGORÍA 2: Conversación General
    # ==========================================
    {
        "bora_text": "Íhjíúmúné",
        "spanish_translation": "¿Qué haces?",
        "category": "Conversación General",
        "difficulty_level": 2,
        "usage_context": "Pregunta casual sobre actividades",
        "pronunciation_guide": "i-JI-u-MU-ne"
    },
    {
        "bora_text": "Ɨɨ́llémɨ",
        "spanish_translation": "Estoy trabajando",
        "category": "Conversación General",
        "difficulty_level": 2,
        "usage_context": "Responder sobre trabajo actual",
        "pronunciation_guide": "ɨɨ-lle-Mɨ"
    },
    {
        "bora_text": "Mɨɨ́tʃáábémɨ",
        "spanish_translation": "Estoy comiendo",
        "category": "Conversación General",
        "difficulty_level": 2,
        "usage_context": "Indicar que estás comiendo",
        "pronunciation_guide": "mɨɨ-CHAA-be-mɨ"
    },
    {
        "bora_text": "Íhjíáábétso",
        "spanish_translation": "¿Qué quieres?",
        "category": "Conversación General",
        "difficulty_level": 2,
        "usage_context": "Preguntar por deseos o necesidades",
        "pronunciation_guide": "i-JI-aa-BE-tso"
    },
    {
        "bora_text": "Mɨɨ́tʃááné áábétso",
        "spanish_translation": "Quiero comer",
        "category": "Conversación General",
        "difficulty_level": 2,
        "usage_context": "Expresar hambre",
        "pronunciation_guide": "mɨɨ-CHAA-ne aa-BE-tso"
    },
    {
        "bora_text": "Ímɨɨ́tsɨ́ɨ́né áábétso",
        "spanish_translation": "Quiero dormir",
        "category": "Conversación General",
        "difficulty_level": 2,
        "usage_context": "Expresar cansancio",
        "pronunciation_guide": "i-mɨɨ-tsɨɨ-NE aa-BE-tso"
    },
    {
        "bora_text": "Píímɨ",
        "spanish_translation": "Sí",
        "category": "Conversación General",
        "difficulty_level": 1,
        "usage_context": "Afirmación",
        "pronunciation_guide": "PII-mɨ"
    },
    {
        "bora_text": "Ááhɨ",
        "spanish_translation": "No",
        "category": "Conversación General",
        "difficulty_level": 1,
        "usage_context": "Negación",
        "pronunciation_guide": "AA-hɨ"
    },
    {
        "bora_text": "Mɨɨ́méne",
        "spanish_translation": "No sé",
        "category": "Conversación General",
        "difficulty_level": 2,
        "usage_context": "Expresar desconocimiento",
        "pronunciation_guide": "mɨɨ-ME-ne"
    },
    {
        "bora_text": "Pítohtʃípɨ",
        "spanish_translation": "Por favor",
        "category": "Conversación General",
        "difficulty_level": 1,
        "usage_context": "Cortesía al pedir algo",
        "pronunciation_guide": "PI-toh-CHI-pɨ"
    },
    {
        "bora_text": "Tʃííménaa",
        "spanish_translation": "Gracias",
        "category": "Conversación General",
        "difficulty_level": 1,
        "usage_context": "Agradecimiento",
        "pronunciation_guide": "CHII-me-naa"
    },
    {
        "bora_text": "Ááhjíllépáhkye",
        "spanish_translation": "De nada",
        "category": "Conversación General",
        "difficulty_level": 2,
        "usage_context": "Respuesta a agradecimiento",
        "pronunciation_guide": "AA-ji-lle-PA-hkye"
    },
    
    # ==========================================
    # CATEGORÍA 3: Ubicación
    # ==========================================
    {
        "bora_text": "Ímɨchíhjíne áábémɨ",
        "spanish_translation": "¿Dónde estás?",
        "category": "Ubicación",
        "difficulty_level": 2,
        "usage_context": "Preguntar por ubicación de persona",
        "pronunciation_guide": "i-mɨ-CHI-ji-ne aa-BE-mɨ"
    },
    {
        "bora_text": "Pááné mɨɨ́ɨɨbémɨ",
        "spanish_translation": "Estoy en mi casa",
        "category": "Ubicación",
        "difficulty_level": 2,
        "usage_context": "Indicar que estás en casa",
        "pronunciation_guide": "PAA-ne mɨɨ-ɨɨ-BE-mɨ"
    },
    {
        "bora_text": "Ímɨchíhjí pááné",
        "spanish_translation": "¿Dónde está la casa?",
        "category": "Ubicación",
        "difficulty_level": 2,
        "usage_context": "Preguntar ubicación de lugar",
        "pronunciation_guide": "i-mɨ-CHI-ji PAA-ne"
    },
    {
        "bora_text": "Ítsíhjíne",
        "spanish_translation": "Aquí",
        "category": "Ubicación",
        "difficulty_level": 1,
        "usage_context": "Indicar cercanía",
        "pronunciation_guide": "i-TSI-ji-ne"
    },
    {
        "bora_text": "Óóhyéne",
        "spanish_translation": "Allá",
        "category": "Ubicación",
        "difficulty_level": 1,
        "usage_context": "Indicar lejanía",
        "pronunciation_guide": "OO-hye-ne"
    },
    {
        "bora_text": "Mɨɨ́hchóné báámɨ",
        "spanish_translation": "Voy al río",
        "category": "Ubicación",
        "difficulty_level": 2,
        "usage_context": "Indicar movimiento hacia el río",
        "pronunciation_guide": "mɨɨ-CHO-ne BAA-mɨ"
    },
    {
        "bora_text": "Tʃáákúné báámɨ",
        "spanish_translation": "Voy a la chacra",
        "category": "Ubicación",
        "difficulty_level": 2,
        "usage_context": "Indicar que vas al campo/huerto",
        "pronunciation_guide": "CHAA-ku-NE BAA-mɨ"
    },
    {
        "bora_text": "Úwáné báámɨ",
        "spanish_translation": "Voy al pueblo",
        "category": "Ubicación",
        "difficulty_level": 2,
        "usage_context": "Indicar viaje al pueblo",
        "pronunciation_guide": "u-WA-ne BAA-mɨ"
    },
    {
        "bora_text": "Ɨ́pɨ́hné",
        "spanish_translation": "Cerca",
        "category": "Ubicación",
        "difficulty_level": 1,
        "usage_context": "Describir proximidad",
        "pronunciation_guide": "ɨ-pɨh-NE"
    },
    {
        "bora_text": "Óóhpáné",
        "spanish_translation": "Lejos",
        "category": "Ubicación",
        "difficulty_level": 1,
        "usage_context": "Describir distancia",
        "pronunciation_guide": "OO-pa-NE"
    },
    
    # ==========================================
    # CATEGORÍA 4: Relaciones Cotidianas
    # ==========================================
    {
        "bora_text": "Mɨɨ́pá",
        "spanish_translation": "Mi papá",
        "category": "Relaciones Cotidianas",
        "difficulty_level": 2,
        "usage_context": "Referirse al padre",
        "pronunciation_guide": "mɨɨ-PA"
    },
    {
        "bora_text": "Mɨɨ́tyú",
        "spanish_translation": "Mi mamá",
        "category": "Relaciones Cotidianas",
        "difficulty_level": 2,
        "usage_context": "Referirse a la madre",
        "pronunciation_guide": "mɨɨ-TYU"
    },
    {
        "bora_text": "Mɨɨ́ɨ́hɨ́",
        "spanish_translation": "Mi hermano/a",
        "category": "Relaciones Cotidianas",
        "difficulty_level": 2,
        "usage_context": "Referirse a hermano o hermana",
        "pronunciation_guide": "mɨɨ-ɨ-Hɨ"
    },
    {
        "bora_text": "Mɨɨ́ɨ́ɨbíkyo",
        "spanish_translation": "Mi hijo/a",
        "category": "Relaciones Cotidianas",
        "difficulty_level": 2,
        "usage_context": "Referirse a hijo o hija",
        "pronunciation_guide": "mɨɨ-ɨɨ-BI-kyo"
    },
    {
        "bora_text": "Mɨɨ́ɨ́bóómyú",
        "spanish_translation": "Mi esposo/a",
        "category": "Relaciones Cotidianas",
        "difficulty_level": 2,
        "usage_context": "Referirse a pareja",
        "pronunciation_guide": "mɨɨ-ɨ-BOO-myu"
    },
    {
        "bora_text": "Mɨɨ́ájtsú",
        "spanish_translation": "Mi abuelo/a",
        "category": "Relaciones Cotidianas",
        "difficulty_level": 2,
        "usage_context": "Referirse a los abuelos",
        "pronunciation_guide": "mɨɨ-AJ-tsu"
    },
    {
        "bora_text": "Mɨɨ́wáhtyú",
        "spanish_translation": "Mi amigo/a",
        "category": "Relaciones Cotidianas",
        "difficulty_level": 2,
        "usage_context": "Referirse a amistades",
        "pronunciation_guide": "mɨɨ-WAH-tyu"
    },
    {
        "bora_text": "Píhkú",
        "spanish_translation": "Hombre",
        "category": "Relaciones Cotidianas",
        "difficulty_level": 1,
        "usage_context": "Género masculino",
        "pronunciation_guide": "PIH-ku"
    },
    {
        "bora_text": "Ímyúú",
        "spanish_translation": "Mujer",
        "category": "Relaciones Cotidianas",
        "difficulty_level": 1,
        "usage_context": "Género femenino",
        "pronunciation_guide": "i-MYU-u"
    },
    {
        "bora_text": "Ɨ́ɨbíkyo",
        "spanish_translation": "Niño/a",
        "category": "Relaciones Cotidianas",
        "difficulty_level": 1,
        "usage_context": "Referirse a niños",
        "pronunciation_guide": "ɨɨ-BI-kyo"
    },
    
    # ==========================================
    # CATEGORÍA 5: Emergencias
    # ==========================================
    {
        "bora_text": "Íhjóóbámɨ!",
        "spanish_translation": "¡Ayuda!",
        "category": "Emergencias",
        "difficulty_level": 3,
        "usage_context": "Pedir ayuda urgente",
        "pronunciation_guide": "i-JOO-ba-mɨ"
    },
    {
        "bora_text": "Mɨɨ́kwáábémɨ",
        "spanish_translation": "Estoy enfermo/a",
        "category": "Emergencias",
        "difficulty_level": 3,
        "usage_context": "Indicar enfermedad",
        "pronunciation_guide": "mɨɨ-KWAA-be-mɨ"
    },
    {
        "bora_text": "Mítsítsípɨ!",
        "spanish_translation": "¡Cuidado!",
        "category": "Emergencias",
        "difficulty_level": 2,
        "usage_context": "Advertir peligro",
        "pronunciation_guide": "MI-tsi-TSI-pɨ"
    },
    {
        "bora_text": "Mɨɨ́mɨ́htsímɨ",
        "spanish_translation": "Me duele",
        "category": "Emergencias",
        "difficulty_level": 3,
        "usage_context": "Expresar dolor",
        "pronunciation_guide": "mɨɨ-mɨh-TSI-mɨ"
    },
    {
        "bora_text": "Ítsóné áábétso",
        "spanish_translation": "Necesito agua",
        "category": "Emergencias",
        "difficulty_level": 2,
        "usage_context": "Pedir agua",
        "pronunciation_guide": "i-TSO-ne aa-BE-tso"
    },
    {
        "bora_text": "Tʃáábíné áábétso",
        "spanish_translation": "Necesito comida",
        "category": "Emergencias",
        "difficulty_level": 2,
        "usage_context": "Pedir alimento",
        "pronunciation_guide": "CHAA-bi-NE aa-BE-tso"
    },
    {
        "bora_text": "Íhjóóbá úmúné ímɨchíhjíne",
        "spanish_translation": "¿Dónde hay un médico?",
        "category": "Emergencias",
        "difficulty_level": 3,
        "usage_context": "Buscar atención médica",
        "pronunciation_guide": "i-JOO-ba u-MU-ne i-mɨ-CHI-ji-ne"
    },
    {
        "bora_text": "Ááhjíbámɨ mɨɨ́ɨ́pɨ́hné",
        "spanish_translation": "Estoy perdido/a",
        "category": "Emergencias",
        "difficulty_level": 3,
        "usage_context": "Indicar que estás perdido",
        "pronunciation_guide": "AA-ji-BA-mɨ mɨɨ-ɨ-pɨh-NE"
    },
    {
        "bora_text": "Íímɨ́ɨ́bámɨ!",
        "spanish_translation": "¡Peligro!",
        "category": "Emergencias",
        "difficulty_level": 3,
        "usage_context": "Alertar de peligro inminente",
        "pronunciation_guide": "II-mɨ-ɨ-BA-mɨ"
    },
    {
        "bora_text": "Mɨɨ́hpákómɨ",
        "spanish_translation": "Tengo miedo",
        "category": "Emergencias",
        "difficulty_level": 3,
        "usage_context": "Expresar temor",
        "pronunciation_guide": "mɨɨ-PA-ko-mɨ"
    }
]


async def load_corpus():
    """Carga el corpus de frases Bora en Supabase"""
    
    logger.info("🌿 Iniciando carga de corpus Bora...")
    logger.info(f"📚 Total de frases a cargar: {len(BORA_CORPUS)}")
    
    try:
        # Obtener adaptador de Supabase
        supabase = get_supabase_adapter()
        
        if not supabase.is_connected():
            logger.error("❌ No hay conexión con Supabase")
            logger.error("Verifica tu archivo .env y las credenciales")
            return False
        
        logger.info("✅ Conexión con Supabase establecida")
        
        # Contador de éxitos y errores
        success_count = 0
        error_count = 0
        
        # Cargar cada frase
        for i, phrase_data in enumerate(BORA_CORPUS, 1):
            try:
                result = await supabase.insert_phrase(phrase_data)
                
                if result:
                    success_count += 1
                    logger.info(
                        f"✓ [{i}/{len(BORA_CORPUS)}] "
                        f"{phrase_data['bora_text']} → {phrase_data['spanish_translation']}"
                    )
                else:
                    error_count += 1
                    logger.warning(f"⚠ Error al insertar frase {i}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error en frase {i}: {e}")
        
        # Resumen final
        logger.info("\n" + "="*60)
        logger.info("📊 RESUMEN DE CARGA")
        logger.info("="*60)
        logger.info(f"✅ Frases cargadas exitosamente: {success_count}")
        logger.info(f"❌ Errores encontrados: {error_count}")
        logger.info(f"📈 Tasa de éxito: {(success_count/len(BORA_CORPUS)*100):.1f}%")
        logger.info("="*60)
        
        # Mostrar distribución por categorías
        categories = {}
        for phrase in BORA_CORPUS:
            cat = phrase['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        logger.info("\n📚 DISTRIBUCIÓN POR CATEGORÍAS:")
        for cat, count in sorted(categories.items()):
            logger.info(f"  • {cat}: {count} frases")
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"❌ Error fatal durante la carga: {e}")
        return False


if __name__ == "__main__":
    logger.info("🚀 MIAPPBORA - Carga de Corpus Bora")
    logger.info("="*60)
    
    success = asyncio.run(load_corpus())
    
    if success:
        logger.info("\n✅ Corpus cargado exitosamente!")
        logger.info("🎯 Siguiente paso: Generar embeddings con HuggingFace")
    else:
        logger.error("\n❌ Hubo problemas al cargar el corpus")
        logger.error("Revisa los errores arriba y vuelve a intentar")
        sys.exit(1)
