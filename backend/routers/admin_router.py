from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta
from config.database_connection import get_db
from models.database import User
from dependencies import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])

# Email del administrador
ADMIN_EMAIL = "admin-bora@superadminbora.com"

# Dependency para verificar admin
def verify_admin(current_user: User = Depends(get_current_user)):
    if current_user.email != ADMIN_EMAIL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador"
        )
    return current_user

@router.get("/users")
async def get_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """Obtener todos los usuarios (solo admin)"""
    users = db.query(User).all()
    
    result = []
    for user in users:
        result.append({
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "phone": user.phone,
            "points": user.total_points,
            "level": user.level,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else datetime.now().isoformat()
        })
    
    return result

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: dict,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """Actualizar datos de un usuario (solo admin)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Actualizar campos permitidos
    allowed_fields = ['email', 'username', 'full_name', 'phone', 'level', 'is_active']
    for key, value in user_data.items():
        if key in allowed_fields and hasattr(user, key):
            setattr(user, key, value)
        elif key == 'points':
            # Mapear 'points' del frontend a 'total_points' del backend
            user.total_points = value
    
    db.commit()
    db.refresh(user)
    
    return {
        "message": "Usuario actualizado correctamente",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "phone": user.phone,
            "points": user.total_points,
            "level": user.level
        }
    }

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """Eliminar un usuario (solo admin)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # No permitir eliminar al admin
    if user.email == ADMIN_EMAIL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No se puede eliminar al administrador"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "Usuario eliminado correctamente"}

@router.get("/stats/dashboard")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """Obtener estadísticas completas del sistema (solo admin)"""
    
    # Total de usuarios
    total_users = db.query(func.count(User.id)).scalar() or 0
    
    # Usuarios activos (estimado - todos por ahora)
    active_users = total_users
    
    # Nuevos usuarios (última semana)
    week_ago = datetime.now() - timedelta(days=7)
    new_users_week = db.query(func.count(User.id)).filter(
        User.created_at >= week_ago
    ).scalar() or 0
    
    # Usuarios por nivel
    users_by_level = db.query(
        User.level,
        func.count(User.id).label('count')
    ).group_by(User.level).all()
    
    users_by_level_data = [
        {"level": level, "count": count}
        for level, count in users_by_level
    ]
    
    # Si no hay datos por nivel, generar estructura vacía
    if not users_by_level_data:
        users_by_level_data = [
            {"level": i, "count": 0} for i in range(1, 6)
        ]
    
    # Distribución de puntos
    points_ranges = [
        (0, 100, "0-100"),
        (100, 500, "100-500"),
        (500, 1000, "500-1000"),
        (1000, 2000, "1000-2000"),
        (2000, 999999, "2000+")
    ]
    
    points_distribution = []
    for min_points, max_points, label in points_ranges:
        count = db.query(func.count(User.id)).filter(
            User.total_points >= min_points,
            User.total_points < max_points
        ).scalar() or 0
        
        points_distribution.append({
            "range": label,
            "count": count
        })
    
    # Actividad diaria (últimos 7 días) - simulado por ahora
    daily_activity = []
    for i in range(6, -1, -1):
        date = datetime.now() - timedelta(days=i)
        daily_activity.append({
            "date": date.strftime("%Y-%m-%d"),
            "games": 0,  # Por implementar
            "queries": 0  # Por implementar
        })
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "new_users_this_week": new_users_week,
        "chat_queries": 0,  # Por implementar
        "rewards_claimed": 0,  # Por implementar
        "users_by_level": users_by_level_data,
        "daily_activity": daily_activity,
        "points_distribution": points_distribution
    }

@router.get("/feedback")
async def get_all_feedback(
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """Obtener todo el feedback (solo admin)"""
    from models.database import AppFeedback
    
    try:
        # Obtener todos los feedbacks con información del usuario
        feedbacks = db.query(AppFeedback).join(User).all()
        
        result = []
        for feedback in feedbacks:
            # Calcular rating promedio
            ratings = [
                r for r in [
                    feedback.mentor_rating,
                    feedback.games_rating,
                    feedback.general_rating
                ] if r is not None
            ]
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            
            # Determinar categoría basada en el rating más alto
            category = 'General'
            if feedback.mentor_rating and feedback.mentor_rating == max(ratings):
                category = 'Mentor'
            elif feedback.games_rating and feedback.games_rating == max(ratings):
                category = 'Gamificación'
            
            result.append({
                "id": feedback.id,
                "user_id": feedback.user_id,
                "username": feedback.user.username,
                "rating": round(avg_rating),
                "mentor_rating": feedback.mentor_rating,
                "games_rating": feedback.games_rating,
                "general_rating": feedback.general_rating,
                "comment": feedback.comments or '',
                "category": category,
                "created_at": feedback.created_at.isoformat() if feedback.created_at else datetime.now().isoformat()
            })
        
        return result
        
    except Exception as e:
        print(f"Error getting feedback: {e}")
        return []
