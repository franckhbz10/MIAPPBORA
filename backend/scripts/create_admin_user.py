"""
Script para crear el usuario administrador
"""
import requests
import json

# URL del backend
API_URL = "http://localhost:8000"

# Datos del administrador
ADMIN_DATA = {
    "email": "admin-bora@superadminbora.com",
    "username": "admin",
    "password": "Admin123!",  # Cambiar por una contraseña segura
    "full_name": "Administrador BORA"
}

def create_admin_user():
    """Crear usuario administrador"""
    
    print("🔧 Creando usuario administrador...")
    print(f"Email: {ADMIN_DATA['email']}")
    print(f"Username: {ADMIN_DATA['username']}")
    
    try:
        # Intentar registrar
        response = requests.post(
            f"{API_URL}/auth/register",
            json=ADMIN_DATA
        )
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            print("\n✅ Usuario administrador creado exitosamente!")
            print(f"ID: {data.get('user', {}).get('id')}")
            print(f"Token: {data.get('access_token', 'N/A')[:20]}...")
            print("\n📝 Credenciales para login:")
            print(f"Email: {ADMIN_DATA['email']}")
            print(f"Password: {ADMIN_DATA['password']}")
            print("\n🌐 Accede al panel admin en:")
            print("file:///D:/documents/UPC/Ciclo%20IX/TP1/workspace/MIAPPBORA/admin/html/login.html")
            return True
            
        elif response.status_code == 400:
            error_data = response.json()
            if "already registered" in error_data.get("detail", "").lower():
                print("\n⚠️  El usuario administrador ya existe")
                print(f"Email: {ADMIN_DATA['email']}")
                print("Puedes usar este email para hacer login")
                return True
            else:
                print(f"\n❌ Error: {error_data.get('detail')}")
                return False
                
        else:
            print(f"\n❌ Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: No se puede conectar al backend")
        print("Asegúrate de que el servidor esté corriendo en http://localhost:8000")
        return False
        
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("CREAR USUARIO ADMINISTRADOR - BORA APP")
    print("=" * 60)
    
    success = create_admin_user()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ CONFIGURACIÓN COMPLETADA")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ ERROR EN LA CONFIGURACIÓN")
        print("=" * 60)
