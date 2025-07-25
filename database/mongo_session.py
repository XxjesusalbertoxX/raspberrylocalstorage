import os
from pymongo import MongoClient
from dotenv import load_dotenv
import json
from datetime import datetime
import glob

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "iot_database")

class MongoSession:
    _instance = None
    
    ## Método para obtener la instancia única de 
    ## MongoSession (Singleton)
    ## mongo sesion siempre entra en el metodo __new__
    ## ese metoodo es el que se encarga de crear la instancia
    def __new__(cls, *args, **kwargs):
        ##si es None, significa que no se ha creado la instancia
        ## entonces se crea una nueva instancia delegandola a el super
        if not cls._instance:
            cls._instance = super(MongoSession, cls).__new__(cls)
        ## sino solo se retorna la instancia ya creada
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        self.mongo_uri = MONGO_URI
        self.db_name = DB_NAME
        self._client = None
        self._db = None
        self.offline_dir = "offline"
        self._create_offline_dir()
        self._connect()
    
    def _create_offline_dir(self):
        """Crea la carpeta offline si no existe"""
        if not os.path.exists(self.offline_dir):
            os.makedirs(self.offline_dir)
    
    def _connect(self):
        """Conecta automáticamente a MongoDB"""
        try:
            self._client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=2000)
            self._client.server_info()
            self._db = self._client[self.db_name]
            print("✓ Conexión con MongoDB establecida exitosamente")
            return True
        except Exception as e:
            print(f"✗ Error de conexión a MongoDB: {e}")
            self._client = None
            self._db = None
            return False
    
    def exportar(self, tabla, json_data):
        """Exporta datos JSON a la tabla especificada"""
        if self._db is None:
            print("✗ Sin conexión a MongoDB. Intentando reconectar...")
            if not self._connect():
                print("✗ No se pudo reconectar. Guardando offline.")
                self._save_offline(tabla, json_data)
                return None
            
        try:
            # Si hay conexión, primero sincronizar datos offline
            self._sync_offline_data()
            
            collection = self._db[tabla]
            result = collection.insert_one(json_data)
            print(f"✓ Datos exportados exitosamente a '{tabla}' con ID: {result.inserted_id}")
            return result.inserted_id
        except Exception as e:
            print(f"✗ Error al exportar a '{tabla}': {e}")
            print("✗ No pudo exportarlo, guardando datos localmente...")
            self._save_offline(tabla, json_data)
            return None
    
    def _sync_offline_data(self):
        """Sincroniza datos offline con MongoDB cuando hay conexión"""
        if self._db is None:
            return
            
        offline_files = glob.glob(os.path.join(self.offline_dir, "*.json"))
        
        if not offline_files:
            return
            
        print(f"📤 Sincronizando {len(offline_files)} archivos offline...")
        
        for filepath in offline_files:
            try:
                # Extraer nombre de tabla del archivo
                filename = os.path.basename(filepath)
                tabla = filename.split('_')[0]  # Formato: tabla_timestamp.json
                
                # Leer datos del archivo
                with open(filepath, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                # Enviar a MongoDB
                collection = self._db[tabla]
                result = collection.insert_one(json_data)
                
                # Si se envió exitosamente, eliminar archivo
                os.remove(filepath)
                print(f"✓ Sincronizado y eliminado: {filename} -> ID: {result.inserted_id}")
                
            except Exception as e:
                print(f"✗ Error al sincronizar {filename}: {e}")
    
    def _save_offline(self, tabla, json_data):
        """Guarda los datos en un único archivo JSON local por tabla"""
        try:
            # Limpieza de _id
            def limpiar_ids(obj):
                if isinstance(obj, dict):
                    return {k: limpiar_ids(v) for k, v in obj.items() if k != '_id'}
                elif isinstance(obj, list):
                    return [limpiar_ids(item) for item in obj]
                else:
                    return obj

            json_data = limpiar_ids(json_data)

            filename = f"{tabla}.json"
            filepath = os.path.join(self.offline_dir, filename)

            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        existing = json.load(f)
                        if not isinstance(existing, list):
                            existing = [existing]
                    except (json.JSONDecodeError, ValueError):
                        existing = []
            else:
                existing = []

            if json_data not in existing:
                existing.append(json_data)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)

            print(f"✓ Datos guardados localmente en: {filepath}")

        except Exception as e:
            print(f"✗ Error al guardar archivo local: {e}")
