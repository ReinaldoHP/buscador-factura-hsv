import os
from pathlib import Path

class Buscador:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)

    def buscar_factura(self, numero_factura):
        """
        Busca una carpeta que contenga el número de factura en su nombre.
        """
        # Convertir a cadena para facilitar la búsqueda
        numero_factura = str(numero_factura)
        resultados = []

        try:
            # Recorrer el directorio raíz
            for root, dirs, files in os.walk(self.root_dir):
                dirpath = Path(root)
                dirname = dirpath.name

                # Verificar si el nombre de la carpeta contiene el número de factura
                if numero_factura in dirname:
                     resultados.append(dirpath)

                # Verificar si hay archivos ZIP que contengan el número de factura
                for file in files:
                    if file.lower().endswith('.zip') and numero_factura in file:
                        resultados.append(dirpath / file)
        except Exception as e:
            print(f"Error durante la búsqueda: {e}")
            return []

        return resultados
    
    def listar_archivos(self, carpeta_path):
        """Lista todo el contenido (archivos y subcarpetas) de una carpeta."""
        contenido = []
        try:
            path = Path(carpeta_path)
            if path.exists() and path.is_dir():
                # Listar todo el contenido ordenado (carpetas primero, luego archivos)
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
                for item in items:
                    contenido.append(item)
        except Exception as e:
             print(f"Error listando contenido en {carpeta_path}: {e}")
        
        return contenido
