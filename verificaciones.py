import json
from pathlib import Path
from lector_zip import LectorZIP

class Verificaciones:
    def __init__(self, config_path):
        self.config = self._cargar_config(config_path)

    def _cargar_config(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando configuración: {e}")
            return {}

    def obtener_requisitos(self, eps):
        """Devuelve los requisitos para una EPS específica o por defecto."""
        eps_key = eps.upper()
        if eps_key in self.config.get("eps_requirements", {}):
            return self.config["eps_requirements"][eps_key]
        return self.config["eps_requirements"]["DEFAULT"]

    def verificar_factura(self, archivos_encontrados, eps):
        """
        Verifica si los archivos encontrados cumplen con los requisitos de la EPS.
        archivos_encontrados: Lista de objetos Path (o strings de rutas).
        eps: Nombre de la EPS.
        """
        requisitos = self.obtener_requisitos(eps)
        archivos_requeridos = requisitos.get("required_files", [])
        chequear_zip = requisitos.get("zip_check", False)

        estado = {
            "completa": True,
            "archivos_presentes": [],
            "archivos_faltantes": [],
            "detalles": []
        }

        # Normalizar nombres de archivos encontrados para búsqueda simple
        # Se guarda una lista plana de todos los archivos disponibles (incluyendo contenido de ZIPs)
        lista_archivos_flat = []

        for archivo_path in archivos_encontrados:
            archivo_path = Path(archivo_path)
            lista_archivos_flat.append(archivo_path.name.lower())
            
            # Si se requiere chequear dentro de ZIPs y es un ZIP
            if chequear_zip and archivo_path.suffix.lower() == '.zip':
                contenido_zip = LectorZIP.listar_contenido(archivo_path)
                # Agregar contenido del zip a la lista plana, solo el nombre del archivo
                lista_archivos_flat.extend([Path(f).name.lower() for f in contenido_zip])

        # Verificar cada requisito
        for req in archivos_requeridos:
            req_lower = req.lower()
            encontrado = False
            
            # Búsqueda simple: si el string requisito está en el nombre del archivo
            for nombre_archivo in lista_archivos_flat:
                if req_lower in nombre_archivo:
                    encontrado = True
                    break
            
            if encontrado:
                estado["archivos_presentes"].append(req)
            else:
                estado["archivos_faltantes"].append(req)
                estado["completa"] = False

        if estado["completa"]:
            estado["detalles"].append("Todos los soportes requeridos fueron encontrados.")
        else:
            estado["detalles"].append(f"Faltan soportes: {', '.join(estado['archivos_faltantes'])}")

        return estado
