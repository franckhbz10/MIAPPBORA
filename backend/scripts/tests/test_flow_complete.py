"""
Script de prueba rápida para verificar el flujo de autenticación completo
Simula: Registro -> Login -> Acceso al Home
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
REGISTER_URL = f"{BASE_URL}/auth/register"
LOGIN_URL = f"{BASE_URL}/auth/login"
ME_URL = f"{BASE_URL}/auth/me"

def print_step(num, title):
    print(f"\n{'='*60}")
    print(f"  PASO {num}: {title}")
    print(f"{'='*60}\n")

print("\n" + "="*60)
print("  🧪 PRUEBA DE FLUJO COMPLETO DE AUTENTICACIÓN")
print("="*60)

# PASO 1: REGISTRO
print_step(1, "REGISTRO DE USUARIO")

timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
user_data = {
    "email": f"flowtest{timestamp}@example.com",
    "username": f"flowtest{timestamp}",
    "phone": f"98765432{timestamp[-2:]}",
    "password": "TestFlow123!",
    "full_name": "Usuario Flow Test"
}

print(f"📝 Registrando usuario: {user_data['email']}")
response = requests.post(REGISTER_URL, json=user_data)

if response.status_code == 201:
    result = response.json()
    print(f"✅ Registro exitoso - Usuario ID: {result['user']['id']}")
    print(f"   → El frontend debería cambiar a modo 'Iniciar Sesión'")
else:
    print(f"❌ Error en registro: {response.status_code}")
    print(response.text)
    exit(1)

# PASO 2: LOGIN
print_step(2, "LOGIN CON CREDENCIALES REGISTRADAS")

login_data = {
    "email": user_data["email"],
    "password": user_data["password"]
}

print(f"🔐 Iniciando sesión: {login_data['email']}")
response = requests.post(LOGIN_URL, json=login_data)

if response.status_code == 200:
    result = response.json()
    token = result['access_token']
    print(f"✅ Login exitoso")
    print(f"   → Token JWT recibido")
    print(f"   → El frontend debería redirigir a '/' (Home)")
    print(f"   → Usuario: {result['user']['username']}")
else:
    print(f"❌ Error en login: {response.status_code}")
    print(response.text)
    exit(1)

# PASO 3: VERIFICAR ACCESO CON TOKEN
print_step(3, "VERIFICAR ACCESO A ENDPOINT PROTEGIDO")

headers = {"Authorization": f"Bearer {token}"}
print(f"🔒 Accediendo a /auth/me con token")
response = requests.get(ME_URL, headers=headers)

if response.status_code == 200:
    result = response.json()
    print(f"✅ Acceso autorizado al Home")
    print(f"   → Usuario autenticado: {result['username']}")
    print(f"   → Email: {result['email']}")
    print(f"   → Level: {result['level']}")
    print(f"   → Points: {result['total_points']}")
else:
    print(f"❌ Error al acceder: {response.status_code}")
    print(response.text)
    exit(1)

# RESUMEN
print("\n" + "="*60)
print("  ✅ FLUJO COMPLETO EXITOSO")
print("="*60)
print("\n📊 Resumen del flujo:")
print("   1. ✅ Usuario registrado exitosamente")
print("   2. ✅ Login realizado con éxito")
print("   3. ✅ Acceso al Home autenticado")
print("\n💡 Comportamiento esperado en Frontend:")
print("   - Al REGISTRARSE → Cambia a pantalla de Login")
print("   - Al HACER LOGIN → Redirige a Home (/)")
print("   - Token guardado en localStorage")
print("\n" + "="*60)
