import pytest
from pathlib import Path
from buscador import Buscador
from verificaciones import Verificaciones
import os

# Fixtures
@pytest.fixture
def mock_fs(tmp_path):
    """Creates a temporary file system structure for testing."""
    root = tmp_path / "test_root"
    root.mkdir()
    
    # Create a directory matching an invoice
    inv_dir = root / "Factura_12345_Enero"
    inv_dir.mkdir()
    (inv_dir / "FEV_899999032_12345.pdf").touch()
    
    # Create a ZIP matching an invoice
    zip_path = root / "Soportes_67890.zip"
    import zipfile
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr('FEV_899999032_67890.pdf', 'dummy content')
    
    return root

# Buscador Tests
def test_buscador_find_folder(mock_fs):
    buscador = Buscador(mock_fs)
    results = buscador.buscar_factura("12345")
    assert len(results) == 1
    assert "Factura_12345_Enero" in results[0].name

def test_buscador_find_zip(mock_fs):
    buscador = Buscador(mock_fs)
    results = buscador.buscar_factura("67890")
    assert len(results) == 1
    assert "Soportes_67890.zip" in results[0].name

# Verificaciones Tests
def test_verificaciones_factura_found(tmp_path):
    # Mock config
    config_file = tmp_path / "config.json"
    import json
    config = {
        "nit": "899999032",
        "eps_config": {
            "SANITAS": {"factura": "FEV", "evidencia": "PDE"}
        },
        "common_files": []
    }
    config_file.write_text(json.dumps(config))
    
    verificador = Verificaciones(str(config_file))
    archivos = [Path("FEV_899999032_12345.pdf")]
    
    resultado = verificador.verificar_factura(archivos, "SANITAS", "12345")
    assert resultado["completa"] is True
    assert len(resultado["archivos_identificados"]) == 1

def test_verificaciones_factura_missing(tmp_path):
    config_file = tmp_path / "config.json"
    import json
    config = {
        "nit": "899999032",
        "eps_config": {
            "SANITAS": {"factura": "FEV", "evidencia": "PDE"}
        },
        "common_files": []
    }
    config_file.write_text(json.dumps(config))
    
    verificador = Verificaciones(str(config_file))
    archivos = [Path("OTRO_ARCHIVO.pdf")]
    
    resultado = verificador.verificar_factura(archivos, "SANITAS", "12345")
    assert resultado["completa"] is False
    assert "FEV_899999032_12345" in resultado["faltantes_obligatorios"][0]
