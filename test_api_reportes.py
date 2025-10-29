"""
Script para probar la API de reportes
"""
import requests
import json

API_URL = "http://localhost:8000"

# Crear un reporte de prueba
print("Creando reporte de prueba...")
reporte = {
    "nombre": "Usuario Prueba",
    "email": "test@example.com",
    "tipo_error": "Prueba Sistema",
    "descripcion": "Este es un reporte de prueba para verificar que el sistema guarda en reportes.json",
    "numero_radicado": "TEST001"
}

try:
    response = requests.post(
        f"{API_URL}/api/v1/reportes/crear",
        json=reporte,
        timeout=10
    )
    response.raise_for_status()
    data = response.json()
    
    print(f"✅ Reporte creado exitosamente!")
    print(f"   ID: {data.get('reporte_id')}")
    print(f"   Mensaje: {data.get('message')}")
    print()
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    exit(1)

# Listar reportes
print("Listando reportes...")
try:
    response = requests.get(
        f"{API_URL}/api/v1/reportes/listar",
        timeout=10
    )
    response.raise_for_status()
    data = response.json()
    
    reportes = data.get("reportes", [])
    total = data.get("total", 0)
    
    print(f"✅ Total de reportes: {total}")
    
    if reportes:
        print("\n📋 Reportes:")
        for i, reporte in enumerate(reportes, 1):
            print(f"\n{i}. {reporte.get('reporte_id')}")
            print(f"   Nombre: {reporte.get('nombre')}")
            print(f"   Email: {reporte.get('email')}")
            print(f"   Tipo: {reporte.get('tipo_error')}")
            print(f"   Descripción: {reporte.get('descripcion')[:50]}...")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    exit(1)

print("\n✅ Prueba completada. Verifica el archivo reports/reportes.json")
