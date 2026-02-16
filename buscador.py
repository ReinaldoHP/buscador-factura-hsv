import os
from pathlib import Path

class Buscador:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)

    def buscar_factura(self, numero_factura, stop_event=None):
        """
        Busca carpetas o archivos ZIP que contengan el número de factura.
        Optimizado usando os.scandir para mayor velocidad.
        """
        numero_factura = str(numero_factura).lower()
        resultados = []

        def _escanear(path):
            if stop_event and stop_event.is_set():
                return
            
            try:
                with os.scandir(path) as it:
                    for entry in it:
                        if stop_event and stop_event.is_set():
                            break
                        
                        if entry.is_dir():
                            if numero_factura in entry.name.lower():
                                resultados.append(Path(entry.path))
                            # Búsqueda recursiva
                            _escanear(entry.path)
                        elif entry.is_file() and entry.name.lower().endswith('.zip'):
                            if numero_factura in entry.name.lower():
                                resultados.append(Path(entry.path))
            except PermissionError:
                pass
            except Exception as e:
                print(f"Error escaneando {path}: {e}")

        _escanear(self.root_dir)
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
