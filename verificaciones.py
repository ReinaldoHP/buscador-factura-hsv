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

    def get_expected_filename(self, code, nit, factura):
        """Genera el nombre base esperado: CODIGO_NIT_FACTURA"""
        return f"{code}_{nit}_{factura}"

    def verificar_factura(self, archivos_encontrados, eps, numero_factura, nit_val=None):
        """
        Verifica si los archivos encontrados cumplen con los requisitos de la EPS
        y siguen el patrón de la imagen (Prefijo_Nit_Factura).
        """
        eps_key = eps.upper() if eps else "OTRA"
        eps_config = self.config.get("eps_config", {})
        
        # Obtener configuración de la EPS o usar OTRA por defecto
        reglas = eps_config.get(eps_key, eps_config.get("OTRA", {}))
        
        prefijo_factura = reglas.get("factura", "FEV")
        prefijo_evidencia = reglas.get("evidencia", "PDE")
        
        nit = nit_val if nit_val else self.config.get("nit", "899999032")
        common_files = self.config.get("common_files", [])
        
        estado = {
            "completa": False,
            "archivos_identificados": [], # Lista de tuplas (NombreArchivo, TipoDetectado, EsCorrecto)
            "faltantes_obligatorios": [],
            "detalles": []
        }

        # Preparar lista plana de archivos encontrados (nombre)
        lista_archivos = []
        for archivo_path in archivos_encontrados:
            archivo_path = Path(archivo_path)
            lista_archivos.append(archivo_path.name)
            if archivo_path.suffix.lower() == '.zip':
                try:
                    contenido_zip = LectorZIP.listar_contenido(archivo_path)
                    lista_archivos.extend([Path(f).name for f in contenido_zip])
                except: pass

        # 1. Buscar Factura Principal (Obligatorio)
        # Patrón: PREFIJO_NIT_FACTURA (puede haber extension)
        patron_factura = self.get_expected_filename(prefijo_factura, nit, numero_factura)
        factura_encontrada = False
        
        for archivo in lista_archivos:
            if patron_factura in archivo:
                estado["archivos_identificados"].append((archivo, f"Factura ({prefijo_factura})", True))
                factura_encontrada = True
        
        if not factura_encontrada:
            estado["faltantes_obligatorios"].append(f"Factura ({patron_factura})")

        # 2. Buscar Evidencia (Opcional o checkear si existe)
        patron_evidencia = self.get_expected_filename(prefijo_evidencia, nit, numero_factura)
        for archivo in lista_archivos:
             if patron_evidencia in archivo:
                 estado["archivos_identificados"].append((archivo, f"Evidencia ({prefijo_evidencia})", True))
        
        # 3. Buscar Archivos Comunes
        for item in common_files:
            code = item["code"]
            name = item["name"]
            patron = self.get_expected_filename(code, nit, numero_factura)
            
            for archivo in lista_archivos:
                if patron in archivo:
                    estado["archivos_identificados"].append((archivo, name, True))

        # Determinar estado final
        if factura_encontrada:
            estado["completa"] = True
            estado["detalles"].append("Factura encontrada y verificada.")
        else:
            estado["completa"] = False
            estado["detalles"].append(f"Falta factura: {patron_factura}")

        return estado
