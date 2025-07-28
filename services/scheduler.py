import json
import time
from serial import Serial
import os

# Ruta al archivo JSON (relativa al directorio actual)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")

# Abre la conexión serial con Arduino Mega
arduino = Serial('/dev/ttyACM0', 9600, timeout=1)  # Cambia el puerto si es necesario

def cargar_config_agua():
    with open(SETTINGS_PATH, "r") as file:
        data = json.load(file)
        return data["sensor_agua"]["min_nivel"]

def enviar_configuracion():
    umbral = cargar_config_agua()
    mensaje = json.dumps({
        "sensor": "agua",
        "min": umbral
    })
    arduino.write((mensaje + "\n").encode())  # importante: añadir salto de línea
    print(f"[OK] Enviado al Arduino: {mensaje}")

if __name__ == "__main__":
    while True:
        try:
            enviar_configuracion()
        except Exception as e:
            print(f"[ERROR] No se pudo enviar la configuración: {e}")
        time.sleep(30)  # Cada 30 segundos se reenvía la configuración
