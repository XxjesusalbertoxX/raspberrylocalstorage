import serial
import time
import json
from services.config_loader import load_settings

# Ajusta al puerto correcto si no es /dev/ttyACM0
SERIAL_PORT = '/dev/ttyACM0'
BAUDRATE = 9600

def enviar_configuracion_al_arduino():
    # Cargar configuración del archivo JSON
    config = load_settings()

    # Solo vamos a enviar la del sensor de agua por ahora
    sensor_agua = next((s for s in config if s['sensor'] == 'agua'), None)
    if not sensor_agua:
        print("[ERROR] No se encontró configuración para sensor de agua.")
        return

    try:
        # Conexión serial
        with serial.Serial(SERIAL_PORT, BAUDRATE, timeout=2) as arduino:
            time.sleep(2)  # Esperar a que el Arduino se reinicie

            mensaje = json.dumps(sensor_agua) + '\n'
            arduino.write(mensaje.encode('utf-8'))
            print(f"[OK] Enviado al Arduino: {mensaje.strip()}")

            # Leer respuesta (opcional)
            while arduino.in_waiting:
                print(arduino.readline().decode().strip())

    except serial.SerialException as e:
        print(f"[ERROR] No se pudo abrir el puerto serial: {e}")
