"""
Script para crear datos de feedback de muestra
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from config.database_connection import SessionLocal
from models.database import User, AppFeedback
from datetime import datetime, timedelta
import random

def create_sample_feedback():
    """Crear feedback de muestra para testing"""
    db = SessionLocal()
    
    try:
        # Obtener todos los usuarios
        users = db.query(User).all()
        
        if not users:
            print("❌ No hay usuarios en la base de datos")
            print("   Ejecuta primero: python scripts/create_admin_user.py")
            return
        
        print(f"📊 Encontrados {len(users)} usuarios")
        
        # Comentarios de ejemplo
        comments_list = [
            "Excelente aplicación, me ayuda mucho a aprender quechua",
            "El chatbot es muy útil pero a veces se demora en responder",
            "Me encanta el sistema de gamificación y las recompensas",
            "Sería genial tener más niveles de dificultad",
            "La interfaz es muy intuitiva y fácil de usar",
            "El mentor Bora es muy amigable y educativo",
            "Necesita más frases para practicar",
            "Las traducciones son muy precisas",
            "Me gustaría poder competir con otros usuarios",
            "Excelente para aprender vocabulario básico",
            "La gamificación me motiva a seguir aprendiendo",
            "El sistema de puntos es muy entretenido",
            "Me gusta que pueda ver mi progreso",
            "Los juegos son divertidos y educativos",
            "El mentor responde de forma clara y educativa"
        ]
        
        # Verificar si ya existe feedback
        existing_feedback = db.query(AppFeedback).count()
        if existing_feedback > 0:
            print(f"⚠️  Ya existen {existing_feedback} registros de feedback")
            response = input("¿Deseas crear más feedback? (s/n): ")
            if response.lower() != 's':
                print("❌ Operación cancelada")
                return
        
        # Crear 15 feedbacks de muestra
        feedbacks_created = 0
        
        for i in range(15):
            user = random.choice(users)
            
            # Generar ratings aleatorios (tendencia positiva)
            mentor_rating = random.choices([3, 4, 5], weights=[1, 3, 4])[0]
            games_rating = random.choices([3, 4, 5], weights=[1, 2, 3])[0]
            general_rating = random.choices([3, 4, 5], weights=[1, 3, 5])[0]
            
            # Fecha aleatoria en los últimos 30 días
            days_ago = random.randint(0, 30)
            created_date = datetime.now() - timedelta(days=days_ago)
            
            feedback = AppFeedback(
                user_id=user.id,
                mentor_rating=mentor_rating,
                games_rating=games_rating,
                general_rating=general_rating,
                comments=random.choice(comments_list),
                created_at=created_date
            )
            
            db.add(feedback)
            feedbacks_created += 1
        
        db.commit()
        print(f"✅ {feedbacks_created} feedbacks creados exitosamente")
        
        # Mostrar resumen
        total_feedback = db.query(AppFeedback).count()
        avg_mentor = db.query(AppFeedback.mentor_rating).filter(
            AppFeedback.mentor_rating.isnot(None)
        ).all()
        avg_games = db.query(AppFeedback.games_rating).filter(
            AppFeedback.games_rating.isnot(None)
        ).all()
        avg_general = db.query(AppFeedback.general_rating).filter(
            AppFeedback.general_rating.isnot(None)
        ).all()
        
        if avg_mentor:
            avg_mentor_val = sum([r[0] for r in avg_mentor]) / len(avg_mentor)
            print(f"   📊 Rating promedio Mentor: {avg_mentor_val:.2f}/5")
        
        if avg_games:
            avg_games_val = sum([r[0] for r in avg_games]) / len(avg_games)
            print(f"   🎮 Rating promedio Juegos: {avg_games_val:.2f}/5")
        
        if avg_general:
            avg_general_val = sum([r[0] for r in avg_general]) / len(avg_general)
            print(f"   ⭐ Rating promedio General: {avg_general_val:.2f}/5")
        
        print(f"\n📈 Total de feedbacks en la base de datos: {total_feedback}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 CREAR FEEDBACK DE MUESTRA")
    print("=" * 60)
    create_sample_feedback()
    print("=" * 60)
