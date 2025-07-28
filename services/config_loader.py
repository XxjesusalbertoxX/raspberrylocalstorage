import json
import os

def load_settings():
    ruta = os.path.join(os.path.dirname(__file__), 'settings.json')
    with open(ruta, 'r') as archivo:
        return json.load(archivo)
