import serial
import time
import json
from services.config_loader import load_settings

SERIAL_PORT = '/dev/ttyACM0'
BAUDRATE = 9600

def main():
    config = load_settings()
    sensor_agua = next((s for s in config if s['sensor'] == 'agua'), None)
    if not sensor_agua:
        print("[ERROR] No se encontró configuración para sensor de agua.")
        return

    try:
        with serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1) as arduino:
            time.sleep(2)  # Esperar que Arduino se estabilice
            mensaje = json.dumps(sensor_agua) + '\n'
            arduino.write(mensaje.encode('utf-8'))
            print(f"[OK] Enviado al Arduino: {mensaje.strip()}")

            while True:
                if arduino.in_waiting > 0:
                    linea = arduino.readline().decode('utf-8').strip()
                    if linea:
                        print(linea)

    except serial.SerialException as e:
        print(f"[ERROR] No se pudo abrir el puerto serial: {e}")

if __name__ == "__main__":
    main()
