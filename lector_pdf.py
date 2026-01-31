import pdfplumber
from pathlib import Path

class LectorPDF:
    @staticmethod
    def obtener_info(pdf_path):
        """
        Extrae información básica de un archivo PDF.
        Retorna un diccionario con metadatos.
        """
        info = {
            "nombre": Path(pdf_path).name,
            "paginas": 0,
            "es_valido": False,
            "error": None
        }

        try:
            with pdfplumber.open(pdf_path) as pdf:
                info["paginas"] = len(pdf.pages)
                info["es_valido"] = True
                
                # Aquí se podría agregar lógica extra para buscar 
                # texto específico si fuera necesario en el futuro
                # first_page_text = pdf.pages[0].extract_text()
                
        except Exception as e:
            info["error"] = str(e)
            
        return info

    @staticmethod
    def es_pdf_valido(pdf_path):
        """Verifica si el archivo es un PDF válido y legible."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return True
        except:
            return False

    @staticmethod
    def extraer_texto(pdf_path):
        """Extrae el texto completo del PDF."""
        texto_completo = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    texto_pag = page.extract_text()
                    if texto_pag:
                        texto_completo += texto_pag + "\n\n"
        except Exception as e:
            return f"Error al leer el PDF: {e}"
        
        if not texto_completo.strip():
            return "El PDF no contiene texto extraíble (posiblemente escaneado)."
            
        return texto_completo
