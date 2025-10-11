"""
Script de prueba para login de usuarios
Prueba el endpoint /auth/login con diferentes casos
"""
import requests
import json
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8000"
REGISTER_URL = f"{BASE_URL}/auth/register"
LOGIN_URL = f"{BASE_URL}/auth/login"
ME_URL = f"{BASE_URL}/auth/me"


def print_separator():
    """Imprime separador visual"""
    print("\n" + "=" * 80 + "\n")


def create_test_user():
    """Crea un usuario de prueba para los tests de login"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    data = {
        "email": f"logintest{timestamp}@example.com",
        "username": f"logintest{timestamp}",
        "phone": f"97777777{timestamp[-2:]}",
        "password": "testpassword123",
        "full_name": "Usuario Login Test"
    }
    
    print("📝 Creando usuario de prueba...")
    print(f"   Email: {data['email']}")
    print(f"   Password: {data['password']}")
    
    try:
        response = requests.post(REGISTER_URL, json=data)
        if response.status_code == 201:
            result = response.json()
            print("✅ Usuario de prueba creado exitosamente")
            return {
                "email": data["email"],
                "password": data["password"],
                "user_id": result["user"]["id"],
                "username": result["user"]["username"]
            }
        else:
            print(f"❌ Error al crear usuario: {response.status_code}")
            print(response.json())
            return None
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None


def test_login_success(test_user):
    """Prueba de login exitoso"""
    print("🧪 TEST 1: Login exitoso")
    print_separator()
    
    if not test_user:
        print("❌ No hay usuario de prueba disponible")
        return None
    
    data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }
    
    print("📤 Enviando credenciales:")
    print(json.dumps(data, indent=2))
    
    try:
        response = requests.post(LOGIN_URL, json=data)
        print(f"\n📥 Respuesta: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Login exitoso!")
            print(f"\nUsuario autenticado:")
            print(f"  - ID: {result['user']['id']}")
            print(f"  - Email: {result['user']['email']}")
            print(f"  - Username: {result['user']['username']}")
            print(f"  - Full Name: {result['user']['full_name']}")
            print(f"  - Level: {result['user']['level']}")
            print(f"  - Points: {result['user']['total_points']}")
            print(f"\n🔑 Token recibido: {result['access_token'][:50]}...")
            print(f"   Token Type: {result['token_type']}")
            return result
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.json())
            return None
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None


def test_login_wrong_password(test_user):
    """Prueba de login con contraseña incorrecta"""
    print("🧪 TEST 2: Login con contraseña incorrecta")
    print_separator()
    
    if not test_user:
        print("❌ No hay usuario de prueba disponible")
        return
    
    data = {
        "email": test_user["email"],
        "password": "contraseña_incorrecta"
    }
    
    print("📤 Enviando credenciales con contraseña incorrecta:")
    print(json.dumps(data, indent=2))
    
    try:
        response = requests.post(LOGIN_URL, json=data)
        print(f"\n📥 Respuesta: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Test exitoso - Contraseña incorrecta rechazada correctamente")
            print(f"Mensaje: {response.json()['detail']}")
        else:
            print(f"❌ Test fallido - Debería retornar 401 Unauthorized")
            print(response.json())
    except Exception as e:
        print(f"❌ Error: {e}")


def test_login_nonexistent_user():
    """Prueba de login con usuario inexistente"""
    print("🧪 TEST 3: Login con usuario inexistente")
    print_separator()
    
    data = {
        "email": "usuario_que_no_existe@example.com",
        "password": "alguna_contraseña"
    }
    
    print("📤 Enviando credenciales de usuario inexistente:")
    print(json.dumps(data, indent=2))
    
    try:
        response = requests.post(LOGIN_URL, json=data)
        print(f"\n📥 Respuesta: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Test exitoso - Usuario inexistente rechazado correctamente")
            print(f"Mensaje: {response.json()['detail']}")
        else:
            print(f"❌ Test fallido - Debería retornar 401 Unauthorized")
            print(response.json())
    except Exception as e:
        print(f"❌ Error: {e}")


def test_login_invalid_email():
    """Prueba de login con email inválido"""
    print("🧪 TEST 4: Login con email inválido")
    print_separator()
    
    data = {
        "email": "email-sin-formato-valido",
        "password": "password123"
    }
    
    print("📤 Enviando email inválido:")
    print(json.dumps(data, indent=2))
    
    try:
        response = requests.post(LOGIN_URL, json=data)
        print(f"\n📥 Respuesta: {response.status_code}")
        
        if response.status_code == 422:
            print("✅ Test exitoso - Email inválido rechazado correctamente")
            print(f"Errores de validación:")
            errors = response.json()
            print(json.dumps(errors, indent=2))
        else:
            print(f"❌ Test fallido - Debería retornar 422 Validation Error")
            print(response.json())
    except Exception as e:
        print(f"❌ Error: {e}")


def test_login_missing_fields():
    """Prueba de login con campos faltantes"""
    print("🧪 TEST 5: Login con campos faltantes")
    print_separator()
    
    data = {
        "email": "test@example.com"
        # Falta el campo password
    }
    
    print("📤 Enviando datos incompletos:")
    print(json.dumps(data, indent=2))
    
    try:
        response = requests.post(LOGIN_URL, json=data)
        print(f"\n📥 Respuesta: {response.status_code}")
        
        if response.status_code == 422:
            print("✅ Test exitoso - Campos faltantes detectados correctamente")
            print(f"Errores de validación:")
            errors = response.json()
            print(json.dumps(errors, indent=2))
        else:
            print(f"❌ Test fallido - Debería retornar 422 Validation Error")
            print(response.json())
    except Exception as e:
        print(f"❌ Error: {e}")


def test_get_current_user(login_result):
    """Prueba del endpoint /auth/me con token válido"""
    print("🧪 TEST 6: Obtener información del usuario actual (/auth/me)")
    print_separator()
    
    if not login_result:
        print("❌ No hay token disponible (login previo falló)")
        return
    
    token = login_result["access_token"]
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print("📤 Enviando petición con token de autenticación")
    print(f"   Token: {token[:50]}...")
    
    try:
        response = requests.get(ME_URL, headers=headers)
        print(f"\n📥 Respuesta: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Información del usuario obtenida correctamente!")
            print(f"\nDatos del usuario:")
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.json())
    except Exception as e:
        print(f"❌ Error: {e}")


def test_get_current_user_invalid_token():
    """Prueba del endpoint /auth/me con token inválido"""
    print("🧪 TEST 7: Acceso con token inválido")
    print_separator()
    
    headers = {
        "Authorization": "Bearer token_invalido_12345"
    }
    
    print("📤 Enviando petición con token inválido")
    
    try:
        response = requests.get(ME_URL, headers=headers)
        print(f"\n📥 Respuesta: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Test exitoso - Token inválido rechazado correctamente")
            print(f"Mensaje: {response.json()['detail']}")
        else:
            print(f"❌ Test fallido - Debería retornar 401 Unauthorized")
            print(response.json())
    except Exception as e:
        print(f"❌ Error: {e}")


def test_get_current_user_no_token():
    """Prueba del endpoint /auth/me sin token"""
    print("🧪 TEST 8: Acceso sin token de autenticación")
    print_separator()
    
    print("📤 Enviando petición sin token")
    
    try:
        response = requests.get(ME_URL)
        print(f"\n📥 Respuesta: {response.status_code}")
        
        if response.status_code == 401 or response.status_code == 403:
            print("✅ Test exitoso - Acceso sin token rechazado correctamente")
            print(f"Mensaje: {response.json()['detail']}")
        else:
            print(f"❌ Test fallido - Debería retornar 401 o 403")
            print(response.json())
    except Exception as e:
        print(f"❌ Error: {e}")


def run_all_tests():
    """Ejecuta todos los tests"""
    print("=" * 80)
    print("🚀 INICIANDO TESTS DE LOGIN")
    print("=" * 80)
    print(f"\n🔗 Servidor: {BASE_URL}")
    print(f"📍 Endpoint Login: {LOGIN_URL}")
    print(f"📍 Endpoint Me: {ME_URL}")
    
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
    
    # Crear usuario de prueba
    test_user = create_test_user()
    print_separator()
    
    # Ejecutar tests de login
    login_result = test_login_success(test_user)
    print_separator()
    
    test_login_wrong_password(test_user)
    print_separator()
    
    test_login_nonexistent_user()
    print_separator()
    
    test_login_invalid_email()
    print_separator()
    
    test_login_missing_fields()
    print_separator()
    
    # Tests de endpoint protegido /auth/me
    test_get_current_user(login_result)
    print_separator()
    
    test_get_current_user_invalid_token()
    print_separator()
    
    test_get_current_user_no_token()
    
    print("\n" + "=" * 80)
    print("✅ TESTS COMPLETADOS")
    print("=" * 80)
    
    if test_user:
        print("\n💡 Credenciales del usuario de prueba:")
        print(f"   Email: {test_user['email']}")
        print(f"   Password: {test_user['password']}")
        print(f"   Username: {test_user['username']}")


if __name__ == "__main__":
    run_all_tests()
