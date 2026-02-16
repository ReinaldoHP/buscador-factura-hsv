---
description: Agente de Pruebas - Valida la aplicación antes de actualizar
---
Este flujo de trabajo actúa como un agente de control de calidad (QA) para verificar que la aplicación funciona correctamente.

// turbo-all
# Pasos de Verificación

1. Verificar dependencias e instalar si faltan:
```powershell
pip install -r requirements.txt
```

2. Ejecutar la suite de pruebas completa:
```powershell
pytest tests/test_logic.py
```

3. (Opcional) Ejecutar pruebas de integración legacy:
```powershell
python test_integration.py
```

# Guía de Errores
- Si `pytest` falla, revisa los cambios recientes en `buscador.py` o `verificaciones.py`.
- Si fallan los archivos ZIP, verifica que `lector_zip.py` no haya sido modificado incorrectamente.
- Si fallan los requisitos de EPS, revisa `config/requisitos.json`.
