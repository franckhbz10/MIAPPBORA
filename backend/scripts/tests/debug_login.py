"""
Script de debugging para el endpoint de login
Muestra la respuesta completa del servidor
"""
import requests
import json

BASE_URL = "http://localhost:8000"
REGISTER_URL = f"{BASE_URL}/auth/register"
LOGIN_URL = f"{BASE_URL}/auth/login"

# Crear usuario
print("1. Creando usuario de prueba...")
timestamp = "debug001"
register_data = {
    "email": f"debug{timestamp}@example.com",
    "username": f"debug{timestamp}",
    "phone": f"999999999",
    "password": "debugpass123"
}

response = requests.post(REGISTER_URL, json=register_data)
print(f"Registro: {response.status_code}")
if response.status_code == 201:
    print("Usuario creado exitosamente")
elif response.status_code == 400:
    print("Usuario ya existe, continuando con login...")
else:
    print(f"Error: {response.text}")

# Intentar login
print("\n2. Intentando login...")
login_data = {
    "email": register_data["email"],
    "password": register_data["password"]
}

print(f"Datos de login: {json.dumps(login_data, indent=2)}")

try:
    response = requests.post(LOGIN_URL, json=login_data)
    print(f"\nCódigo de estado: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"\nContenido raw:")
    print(response.text)
    print(f"\nLongitud del contenido: {len(response.text)}")
    
    if response.text:
        try:
            json_data = response.json()
            print(f"\nJSON parseado:")
            print(json.dumps(json_data, indent=2, default=str))
        except:
            print("No se pudo parsear como JSON")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
