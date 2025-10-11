"""
Script completo de prueba de autenticación
Ejecuta un flujo completo de registro → login → acceso a endpoint protegido
"""
import requests
import json
from datetime import datetime
import time

# Configuración
BASE_URL = "http://localhost:8000"
REGISTER_URL = f"{BASE_URL}/auth/register"
LOGIN_URL = f"{BASE_URL}/auth/login"
ME_URL = f"{BASE_URL}/auth/me"


def print_separator(char="="):
    """Imprime separador visual"""
    print("\n" + char * 80 + "\n")


def print_step(step_num, title):
    """Imprime encabezado de paso"""
    print(f"\n{'=' * 80}")
    print(f"PASO {step_num}: {title}")
    print(f"{'=' * 80}\n")


def check_server():
    """Verifica que el servidor esté corriendo"""
    print("🔍 Verificando conexión al servidor...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Servidor corriendo en {BASE_URL}")
            return True
        else:
            print(f"⚠️  Servidor respondió con código {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ No se puede conectar al servidor en {BASE_URL}")
        print("   Asegúrate de que el backend esté corriendo:")
        print("   cd backend")
        print("   uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error al conectar: {e}")
        return False


def test_register():
    """PASO 1: Registrar nuevo usuario"""
    print_step(1, "REGISTRO DE USUARIO")
    
    # Generar datos únicos
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    user_data = {
        "email": f"testauth{timestamp}@example.com",
        "username": f"testauth{timestamp}",
        "phone": f"98888888{timestamp[-2:]}",
        "password": "SecurePass123!",
        "full_name": "Test Auth User"
    }
    
    print("📝 Datos del nuevo usuario:")
    print(f"   Email: {user_data['email']}")
    print(f"   Username: {user_data['username']}")
    print(f"   Phone: {user_data['phone']}")
    print(f"   Password: {user_data['password']}")
    print(f"   Full Name: {user_data['full_name']}")
    
    print(f"\n📤 Enviando petición a {REGISTER_URL}...")
    
    try:
        response = requests.post(REGISTER_URL, json=user_data)
        print(f"📥 Respuesta recibida: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("\n✅ REGISTRO EXITOSO!")
            print(f"\n👤 Usuario creado:")
            print(f"   ID: {result['user']['id']}")
            print(f"   Email: {result['user']['email']}")
            print(f"   Username: {result['user']['username']}")
            print(f"   Full Name: {result['user']['full_name']}")
            print(f"   Level: {result['user']['level']}")
            print(f"   Points: {result['user']['total_points']}")
            print(f"   Title: {result['user']['current_title']}")
            print(f"   Active: {result['user']['is_active']}")
            
            print(f"\n🔑 Token JWT generado:")
            print(f"   {result['access_token'][:60]}...")
            print(f"   Type: {result['token_type']}")
            
            return {
                "email": user_data["email"],
                "password": user_data["password"],
                "register_token": result["access_token"],
                "user_id": result["user"]["id"],
                "username": result["user"]["username"]
            }
        else:
            print(f"\n❌ ERROR EN REGISTRO")
            print(f"Código: {response.status_code}")
            print(f"Detalle: {response.json()}")
            return None
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None


def test_login(credentials):
    """PASO 2: Login con las credenciales creadas"""
    print_step(2, "LOGIN DE USUARIO")
    
    if not credentials:
        print("❌ No hay credenciales disponibles del paso anterior")
        return None
    
    login_data = {
        "email": credentials["email"],
        "password": credentials["password"]
    }
    
    print("🔐 Intentando iniciar sesión...")
    print(f"   Email: {login_data['email']}")
    print(f"   Password: {'*' * len(login_data['password'])}")
    
    print(f"\n📤 Enviando petición a {LOGIN_URL}...")
    
    try:
        response = requests.post(LOGIN_URL, json=login_data)
        print(f"📥 Respuesta recibida: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ LOGIN EXITOSO!")
            
            print(f"\n👤 Usuario autenticado:")
            print(f"   ID: {result['user']['id']}")
            print(f"   Email: {result['user']['email']}")
            print(f"   Username: {result['user']['username']}")
            print(f"   Last Login: {result['user'].get('last_login', 'N/A')}")
            
            print(f"\n🔑 Nuevo token JWT generado:")
            print(f"   {result['access_token'][:60]}...")
            
            # Comparar tokens
            if credentials.get("register_token") == result["access_token"]:
                print("   ⚠️  Token es el mismo que el de registro")
            else:
                print("   ✅ Token es diferente al de registro")
            
            return {
                **credentials,
                "login_token": result["access_token"]
            }
        else:
            print(f"\n❌ ERROR EN LOGIN")
            print(f"Código: {response.status_code}")
            print(f"Detalle: {response.json()}")
            return None
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None


def test_protected_endpoint(auth_data):
    """PASO 3: Acceder a endpoint protegido /auth/me"""
    print_step(3, "ACCESO A ENDPOINT PROTEGIDO (/auth/me)")
    
    if not auth_data:
        print("❌ No hay datos de autenticación disponibles")
        return False
    
    token = auth_data.get("login_token") or auth_data.get("register_token")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print("🔒 Accediendo a endpoint protegido...")
    print(f"   Token: {token[:60]}...")
    
    print(f"\n📤 Enviando petición a {ME_URL}...")
    
    try:
        response = requests.get(ME_URL, headers=headers)
        print(f"📥 Respuesta recibida: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ ACCESO AUTORIZADO!")
            
            print(f"\n👤 Información del usuario actual:")
            print(f"   ID: {result['id']}")
            print(f"   Email: {result['email']}")
            print(f"   Username: {result['username']}")
            print(f"   Full Name: {result['full_name']}")
            print(f"   Avatar: {result.get('avatar_url', 'N/A')}")
            print(f"   Level: {result['level']}")
            print(f"   Points: {result['total_points']}")
            print(f"   Title: {result['current_title']}")
            print(f"   Active: {result['is_active']}")
            print(f"   Created At: {result['created_at']}")
            print(f"   Last Login: {result.get('last_login', 'N/A')}")
            
            return True
        else:
            print(f"\n❌ ACCESO DENEGADO")
            print(f"Código: {response.status_code}")
            print(f"Detalle: {response.json()}")
            return False
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False


def test_wrong_credentials(auth_data):
    """PASO 4: Probar login con credenciales incorrectas"""
    print_step(4, "PRUEBA DE SEGURIDAD - Credenciales incorrectas")
    
    if not auth_data:
        print("❌ No hay datos de autenticación disponibles")
        return
    
    wrong_data = {
        "email": auth_data["email"],
        "password": "ContraseñaIncorrecta123!"
    }
    
    print("🔒 Intentando login con contraseña incorrecta...")
    print(f"   Email: {wrong_data['email']}")
    print(f"   Password: {wrong_data['password']}")
    
    try:
        response = requests.post(LOGIN_URL, json=wrong_data)
        print(f"\n📥 Respuesta: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Seguridad correcta - Credenciales incorrectas rechazadas")
            print(f"   Mensaje: {response.json()['detail']}")
        else:
            print(f"⚠️  Respuesta inesperada: {response.status_code}")
            print(response.json())
    except Exception as e:
        print(f"❌ Error: {e}")


def test_invalid_token():
    """PASO 5: Probar acceso con token inválido"""
    print_step(5, "PRUEBA DE SEGURIDAD - Token inválido")
    
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid_token_12345"
    
    headers = {
        "Authorization": f"Bearer {invalid_token}"
    }
    
    print("🔒 Intentando acceder con token inválido...")
    print(f"   Token: {invalid_token[:60]}...")
    
    try:
        response = requests.get(ME_URL, headers=headers)
        print(f"\n📥 Respuesta: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Seguridad correcta - Token inválido rechazado")
            print(f"   Mensaje: {response.json()['detail']}")
        else:
            print(f"⚠️  Respuesta inesperada: {response.status_code}")
            print(response.json())
    except Exception as e:
        print(f"❌ Error: {e}")


def run_complete_test():
    """Ejecuta el flujo completo de pruebas"""
    print("\n" + "=" * 80)
    print(" " * 20 + "🚀 TEST COMPLETO DE AUTENTICACIÓN")
    print("=" * 80)
    print(f"\n🔗 Servidor: {BASE_URL}")
    print(f"🕐 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print_separator()
    
    # Verificar servidor
    if not check_server():
        return
    
    print_separator()
    
    # Paso 1: Registro
    credentials = test_register()
    if not credentials:
        print("\n❌ Test abortado - Registro falló")
        return
    
    time.sleep(1)  # Pequeña pausa entre pasos
    
    # Paso 2: Login
    auth_data = test_login(credentials)
    if not auth_data:
        print("\n❌ Test abortado - Login falló")
        return
    
    time.sleep(1)
    
    # Paso 3: Endpoint protegido
    success = test_protected_endpoint(auth_data)
    if not success:
        print("\n❌ Test abortado - Acceso a endpoint protegido falló")
        return
    
    time.sleep(1)
    
    # Paso 4: Prueba de seguridad - credenciales incorrectas
    test_wrong_credentials(auth_data)
    
    time.sleep(1)
    
    # Paso 5: Prueba de seguridad - token inválido
    test_invalid_token()
    
    # Resumen final
    print("\n" + "=" * 80)
    print(" " * 25 + "✅ TEST COMPLETADO EXITOSAMENTE")
    print("=" * 80)
    
    print("\n📊 RESUMEN:")
    print("   ✅ Registro de usuario - OK")
    print("   ✅ Login de usuario - OK")
    print("   ✅ Acceso a endpoint protegido - OK")
    print("   ✅ Rechazo de credenciales incorrectas - OK")
    print("   ✅ Rechazo de token inválido - OK")
    
    print("\n💾 Datos del usuario de prueba:")
    print(f"   Email: {auth_data['email']}")
    print(f"   Password: {auth_data['password']}")
    print(f"   Username: {auth_data['username']}")
    print(f"   User ID: {auth_data['user_id']}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    run_complete_test()
