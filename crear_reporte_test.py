"""
Script para crear reportes de prueba rápidamente
"""
import requests
from datetime import datetime

API_URL = "http://localhost:8000"

def crear_reporte_prueba(numero):
    """Crea un reporte de prueba"""
    reporte = {
        "nombre": f"Usuario Test {numero}",
        "email": f"test{numero}@example.com",
        "tipo_error": ["Prueba Sistema", "Error de Sistema", "Información Incorrecta"][numero % 3],
        "descripcion": f"Reporte de prueba número {numero} - {datetime.now().strftime('%H:%M:%S')}",
        "numero_radicado": f"TEST{numero:03d}" if numero % 2 == 0 else None
    }
    
    try:
        response = requests.post(
            f"{API_URL}/api/v1/reportes/crear",
            json=reporte,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            print(f"✅ Reporte {numero} creado: {data.get('reporte_id')}")
            return True
        else:
            print(f"❌ Error en reporte {numero}: {data.get('message')}")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cantidad = int(sys.argv[1])
    else:
        cantidad = 1
    
    print(f"Creando {cantidad} reporte(s) de prueba...")
    print()
    
    for i in range(1, cantidad + 1):
        crear_reporte_prueba(i)
    
    print()
    print(f"✅ Proceso completado. Creados {cantidad} reportes.")
    print("   Ve a http://localhost:8501 para verificar la actualización automática")
