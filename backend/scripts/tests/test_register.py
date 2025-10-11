"""
Script de prueba para registro de usuarios
Prueba el endpoint /auth/register con diferentes casos
"""
import requests
import json
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8000"
REGISTER_URL = f"{BASE_URL}/auth/register"


def print_separator():
    """Imprime separador visual"""
    print("\n" + "=" * 80 + "\n")


def test_register_success():
    """Prueba de registro exitoso"""
    print("🧪 TEST 1: Registro exitoso")
    print_separator()
    
    # Generar email único con timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    data = {
        "email": f"testuser{timestamp}@example.com",
        "username": f"testuser{timestamp}",
        "phone": f"98765432{timestamp[-2:]}",
        "password": "password123",
        "full_name": "Usuario de Prueba"
    }
    
    print("📤 Enviando datos:")
    print(json.dumps(data, indent=2))
    
    try:
        response = requests.post(REGISTER_URL, json=data)
        print(f"\n📥 Respuesta: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Registro exitoso!")
            print(f"\nUsuario creado:")
            print(f"  - ID: {result['user']['id']}")
            print(f"  - Email: {result['user']['email']}")
            print(f"  - Username: {result['user']['username']}")
            print(f"  - Full Name: {result['user']['full_name']}")
            print(f"  - Level: {result['user']['level']}")
            print(f"  - Points: {result['user']['total_points']}")
            print(f"  - Title: {result['user']['current_title']}")
            print(f"\n🔑 Token: {result['access_token'][:50]}...")
            return result
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.json())
            return None
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None


def test_register_duplicate_email():
    """Prueba de registro con email duplicado"""
    print("🧪 TEST 2: Registro con email duplicado")
    print_separator()
    
    # Primero crear un usuario
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    email = f"duplicate{timestamp}@example.com"
    
    data = {
        "email": email,
        "username": f"user1_{timestamp}",
        "phone": f"91111111{timestamp[-2:]}",
        "password": "password123"
    }
    
    print("📤 Creando primer usuario...")
    response1 = requests.post(REGISTER_URL, json=data)
    
    if response1.status_code == 201:
        print(f"✅ Primer usuario creado: {email}")
        
        # Intentar crear otro con el mismo email
        data2 = {
            "email": email,  # Email duplicado
            "username": f"user2_{timestamp}",  # Username diferente
            "phone": f"92222222{timestamp[-2:]}",  # Teléfono diferente
            "password": "password456"
        }
        
        print(f"\n📤 Intentando crear segundo usuario con mismo email...")
        response2 = requests.post(REGISTER_URL, json=data2)
        
        print(f"📥 Respuesta: {response2.status_code}")
        
        if response2.status_code == 400:
            print("✅ Test exitoso - Email duplicado rechazado correctamente")
            print(f"Mensaje: {response2.json()['detail']}")
        else:
            print(f"❌ Test fallido - Debería rechazar email duplicado")
            print(response2.json())
    else:
        print(f"❌ No se pudo crear el primer usuario")
        print(response1.json())


def test_register_duplicate_username():
    """Prueba de registro con username duplicado"""
    print("🧪 TEST 3: Registro con username duplicado")
    print_separator()
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    username = f"duplicateuser{timestamp}"
    
    data = {
        "email": f"email1_{timestamp}@example.com",
        "username": username,
        "phone": f"93333333{timestamp[-2:]}",
        "password": "password123"
    }
    
    print("📤 Creando primer usuario...")
    response1 = requests.post(REGISTER_URL, json=data)
    
    if response1.status_code == 201:
        print(f"✅ Primer usuario creado: {username}")
        
        # Intentar crear otro con el mismo username
        data2 = {
            "email": f"email2_{timestamp}@example.com",  # Email diferente
            "username": username,  # Username duplicado
            "phone": f"94444444{timestamp[-2:]}",  # Teléfono diferente
            "password": "password456"
        }
        
        print(f"\n📤 Intentando crear segundo usuario con mismo username...")
        response2 = requests.post(REGISTER_URL, json=data2)
        
        print(f"📥 Respuesta: {response2.status_code}")
        
        if response2.status_code == 400:
            print("✅ Test exitoso - Username duplicado rechazado correctamente")
            print(f"Mensaje: {response2.json()['detail']}")
        else:
            print(f"❌ Test fallido - Debería rechazar username duplicado")
            print(response2.json())
    else:
        print(f"❌ No se pudo crear el primer usuario")
        print(response1.json())


def test_register_invalid_email():
    """Prueba de registro con email inválido"""
    print("🧪 TEST 4: Registro con email inválido")
    print_separator()
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    data = {
        "email": "email-invalido-sin-arroba",  # Email sin @
        "username": f"testuser{timestamp}",
        "phone": f"95555555{timestamp[-2:]}",
        "password": "password123"
    }
    
    print("📤 Enviando datos con email inválido:")
    print(json.dumps(data, indent=2))
    
    try:
        response = requests.post(REGISTER_URL, json=data)
        print(f"\n📥 Respuesta: {response.status_code}")
        
        if response.status_code == 422:
            print("✅ Test exitoso - Email inválido rechazado correctamente")
            print(f"Errores de validación:")
            errors = response.json()
            print(json.dumps(errors, indent=2))
        else:
            print(f"❌ Test fallido - Debería rechazar email inválido")
            print(response.json())
    except Exception as e:
        print(f"❌ Error: {e}")


def test_register_short_password():
    """Prueba de registro con contraseña corta"""
    print("🧪 TEST 5: Registro con contraseña muy corta")
    print_separator()
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    data = {
        "email": f"testshort{timestamp}@example.com",
        "username": f"testshort{timestamp}",
        "phone": f"96666666{timestamp[-2:]}",
        "password": "12345"  # Solo 5 caracteres (mínimo es 6)
    }
    
    print("📤 Enviando datos con contraseña de 5 caracteres:")
    print(json.dumps(data, indent=2))
    
    try:
        response = requests.post(REGISTER_URL, json=data)
        print(f"\n📥 Respuesta: {response.status_code}")
        
        if response.status_code == 422:
            print("✅ Test exitoso - Contraseña corta rechazada correctamente")
            print(f"Errores de validación:")
            errors = response.json()
            print(json.dumps(errors, indent=2))
        else:
            print(f"❌ Test fallido - Debería rechazar contraseña corta")
            print(response.json())
    except Exception as e:
        print(f"❌ Error: {e}")


def test_register_missing_fields():
    """Prueba de registro con campos faltantes"""
    print("🧪 TEST 6: Registro con campos faltantes")
    print_separator()
    
    data = {
        "email": "test@example.com",
        # Faltan username, phone y password
    }
    
    print("📤 Enviando datos incompletos:")
    print(json.dumps(data, indent=2))
    
    try:
        response = requests.post(REGISTER_URL, json=data)
        print(f"\n📥 Respuesta: {response.status_code}")
        
        if response.status_code == 422:
            print("✅ Test exitoso - Campos faltantes detectados correctamente")
            print(f"Errores de validación:")
            errors = response.json()
            print(json.dumps(errors, indent=2))
        else:
            print(f"❌ Test fallido - Debería rechazar datos incompletos")
            print(response.json())
    except Exception as e:
        print(f"❌ Error: {e}")


def run_all_tests():
    """Ejecuta todos los tests"""
    print("=" * 80)
    print("🚀 INICIANDO TESTS DE REGISTRO")
    print("=" * 80)
    print(f"\n🔗 Servidor: {BASE_URL}")
    print(f"📍 Endpoint: {REGISTER_URL}")
    
    # Verificar que el servidor esté corriendo
    try:
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code == 200:
            print("✅ Servidor en línea")
        else:
            print("⚠️  Servidor respondió pero con estado no esperado")
    except Exception as e:
        print(f"❌ No se puede conectar al servidor: {e}")
        print("   Asegúrate de que el backend esté corriendo en http://localhost:8000")
        return
    
    print_separator()
    
    # Ejecutar tests
    user_data = test_register_success()
    print_separator()
    
    test_register_duplicate_email()
    print_separator()
    
    test_register_duplicate_username()
    print_separator()
    
    test_register_invalid_email()
    print_separator()
    
    test_register_short_password()
    print_separator()
    
    test_register_missing_fields()
    
    print("\n" + "=" * 80)
    print("✅ TESTS COMPLETADOS")
    print("=" * 80)
    
    if user_data:
        print("\n💡 Usuario de prueba creado para usar en test_login.py:")
        print(f"   Email: {user_data['user']['email']}")
        print(f"   Password: password123")


if __name__ == "__main__":
    run_all_tests()
