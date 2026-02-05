import zipfile
from pathlib import Path

class LectorZIP:
    @staticmethod
    def listar_contenido(zip_path):
        """
        Lista los archivos contenidos en un archivo ZIP sin descomprimirlos.
        Devuelve una lista de nombres de archivos.
        """
        contenidos = []
        try:
            zip_path = Path(zip_path)
            if not zip_path.exists() or not zipfile.is_zipfile(zip_path):
                return []

            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Obtener lista de nombres de archivos en el ZIP
                contenidos = zf.namelist()
                
                # Filtrar directorios y quedarse solo con archivos
                # y decodificar caracteres si fuera necesario (aunque namelist ya devuelve str)
                contenidos = [f for f in contenidos if not f.endswith('/')]

        except zipfile.BadZipFile:
            print(f"Error: El archivo {zip_path} es un ZIP corrupto.")
        except Exception as e:
            print(f"Error leyendo el ZIP {zip_path}: {e}")

        return contenidos

    @staticmethod
    def buscar_en_zip(zip_path, termino_busqueda):
        """Busca si un archivo específico existe dentro del ZIP."""
        contenido = LectorZIP.listar_contenido(zip_path)
        for archivo in contenido:
            if termino_busqueda.lower() in archivo.lower():
                return True
        return False

    @staticmethod
    def extraer_archivo(zip_path, member_name, output_dir):
        """Extrae un archivo específico del ZIP a un directorio de salida."""
        try:
           with zipfile.ZipFile(zip_path, 'r') as zf:
               return zf.extract(member_name, output_dir)
        except Exception as e:
            print(f"Error extrayendo {member_name} de {zip_path}: {e}")
            return None
