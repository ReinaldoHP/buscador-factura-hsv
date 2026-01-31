import os
import shutil
from pathlib import Path
from buscador import Buscador
from verificaciones import Verificaciones

# Configuración de prueba
TEST_DIR = Path("test_env")
FACTURA_NUM = "123456"
EPS = "SANITAS"

def setup_environment():
    """Crea un entorno de prueba con archivos simulados."""
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    TEST_DIR.mkdir()
    
    # Crear carpeta de factura
    factura_dir = TEST_DIR / f"Factura_{FACTURA_NUM}_Enero_2024"
    factura_dir.mkdir()
    
    # Crear archivos simulados
    (factura_dir / "factura.pdf").touch()
    (factura_dir / "historia_clinica.pdf").touch()
    
    # Simular un ZIP con archivos dentro (no podemos crear un zip 'real' facilmente sin contenido real, 
    # pero podemos intentar crear un zip vacío o mockear el lector_zip. 
    # Para este test, crearemos un zip real vacío o con un archivo dummy)
    import zipfile
    zip_path = factura_dir / "soportes.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr('autorizacion.pdf', 'dummy content')
        zf.writestr('rids.pdf', 'dummy content')
        
    print(f"Entorno de prueba creado en: {TEST_DIR.absolute()}")

def run_test():
    setup_environment()
    
    print("\n--- Iniciando Búsqueda ---")
    buscador = Buscador(TEST_DIR)
    res = buscador.buscar_factura(FACTURA_NUM)
    print(f"Carpetas encontradas: {res}")
    
    if not res:
        print("FALLO: No se encontró la carpeta.")
        return

    carpeta_factura = res[0]
    archivos = buscador.listar_archivos(carpeta_factura)
    print(f"Archivos encontrados: {[f.name for f in archivos]}")
    
    print("\n--- Iniciando Verificación ---")
    verificador = Verificaciones("config/requisitos.json")
    resultado = verificador.verificar_factura(archivos, EPS)
    
    print(f"Resultado Verificación para {EPS}:")
    print(f"Completa: {resultado['completa']}")
    print(f"Archivos Presentes: {resultado['archivos_presentes']}")
    print(f"Archivos Faltantes: {resultado['archivos_faltantes']}")
    print(f"Detalles: {resultado['detalles']}")
    
    # Limpieza
    # shutil.rmtree(TEST_DIR)

if __name__ == "__main__":
    run_test()
