import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import threading
import os
import sys
import shutil
import tempfile
from pathlib import Path
from buscador import Buscador
from verificaciones import Verificaciones
from lector_pdf import LectorPDF
from lector_zip import LectorZIP

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Buscador de Facturas HSV - Reinaldo RH")
        self.root.geometry("1000x700")
        
        # Estilo para Treeview (ttkbootstrap lo maneja, pero los tags necesitan colores compatibles)
        # Se definirá en _setup_ui

        # Configuración
        self.config_path = Path(resource_path("config/requisitos.json"))
        self.verificador = Verificaciones(self.config_path)
        self.buscador = None 
        self.item_paths = {} # Mapeo de ID de treeview a Path real

        # Variables de control
        self.ruta_raiz = tk.StringVar()
        self.factura = tk.StringVar()
        self.eps = tk.StringVar()
        self.nit = tk.StringVar(value="800218979")
        
        # Control de búsqueda asíncrona
        self.search_timer = None
        self.search_thread = None
        self.stop_search_event = threading.Event()

        # Iconos (Generados programáticamente para no depender de archivos externos)
        # Icono PDF - Documento rojo con detalle
        self.img_pdf = tk.PhotoImage(width=16, height=16)
        self.img_pdf.put("#DC143C", to=(3, 1, 13, 15))  # Fondo rojo
        self.img_pdf.put("#8B0000", to=(3, 1, 4, 15))   # Borde izquierdo oscuro
        self.img_pdf.put("#8B0000", to=(12, 1, 13, 15)) # Borde derecho oscuro
        self.img_pdf.put("#8B0000", to=(3, 14, 13, 15)) # Borde inferior
        self.img_pdf.put("#FFFFFF", to=(5, 4, 11, 5))   # Línea blanca 1
        self.img_pdf.put("#FFFFFF", to=(5, 6, 11, 7))   # Línea blanca 2
        self.img_pdf.put("#FFFFFF", to=(5, 8, 11, 9))   # Línea blanca 3
        self.img_pdf.put("#FFFFFF", to=(5, 10, 9, 11))  # Línea blanca 4
        
        # Icono Carpeta - Carpeta amarilla con detalle
        self.img_folder = tk.PhotoImage(width=16, height=16)
        self.img_folder.put("#FFD700", to=(2, 5, 14, 13))  # Cuerpo carpeta dorado
        self.img_folder.put("#FFA500", to=(2, 5, 3, 13))   # Sombra izquierda
        self.img_folder.put("#FFA500", to=(2, 12, 14, 13)) # Sombra inferior
        self.img_folder.put("#FFD700", to=(2, 3, 7, 5))    # Pestaña
        self.img_folder.put("#DAA520", to=(2, 3, 3, 5))    # Sombra pestaña
        self.img_folder.put("#FFED4E", to=(4, 6, 12, 11))  # Brillo interior

        # Icono ZIP - Archivo comprimido azul con cremallera
        self.img_zip = tk.PhotoImage(width=16, height=16)
        self.img_zip.put("#4FC3F7", to=(3, 1, 13, 15))  # Fondo azul claro
        self.img_zip.put("#0288D1", to=(3, 1, 4, 15))   # Borde izquierdo oscuro
        self.img_zip.put("#0288D1", to=(12, 1, 13, 15)) # Borde derecho oscuro
        self.img_zip.put("#0288D1", to=(3, 14, 13, 15)) # Borde inferior
        # Cremallera
        self.img_zip.put("#FFD700", to=(7, 3, 9, 4))    # Tirador cremallera
        self.img_zip.put("#666666", to=(7, 4, 9, 12))   # Línea cremallera
        self.img_zip.put("#888888", to=(6, 5, 7, 6))    # Diente izq 1
        self.img_zip.put("#888888", to=(9, 5, 10, 6))   # Diente der 1
        self.img_zip.put("#888888", to=(6, 7, 7, 8))    # Diente izq 2
        self.img_zip.put("#888888", to=(9, 7, 10, 8))   # Diente der 2
        self.img_zip.put("#888888", to=(6, 9, 7, 10))   # Diente izq 3
        self.img_zip.put("#888888", to=(9, 9, 10, 10))  # Diente der 3

        # Icono .sin/.icon - Checkmark verde
        self.img_sin = tk.PhotoImage(width=16, height=16)
        self.img_sin.put("#4CAF50", to=(2, 2, 14, 14))  # Fondo verde
        self.img_sin.put("#2E7D32", to=(2, 2, 3, 14))   # Borde izquierdo
        self.img_sin.put("#2E7D32", to=(13, 2, 14, 14)) # Borde derecho
        self.img_sin.put("#2E7D32", to=(2, 13, 14, 14)) # Borde inferior
        # Checkmark blanco
        self.img_sin.put("#FFFFFF", to=(5, 8, 6, 9))    # Base check
        self.img_sin.put("#FFFFFF", to=(6, 9, 7, 10))   # 
        self.img_sin.put("#FFFFFF", to=(7, 10, 8, 11))  # Parte baja
        self.img_sin.put("#FFFFFF", to=(8, 9, 9, 10))   # Subida
        self.img_sin.put("#FFFFFF", to=(9, 8, 10, 9))   # 
        self.img_sin.put("#FFFFFF", to=(10, 7, 11, 8))  # 
        self.img_sin.put("#FFFFFF", to=(11, 6, 12, 7))  # Punta

        self._setup_ui()

    def _setup_ui(self):
        # Frame Principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Sección: Selección de Directorio
        dir_frame = ttk.LabelFrame(main_frame, text="Configuración de Búsqueda")
        dir_frame.pack(fill=tk.X, pady=5)

        ttk.Label(dir_frame, text="Carpeta Raíz:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(dir_frame, textvariable=self.ruta_raiz, width=50).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(dir_frame, text="Seleccionar...", command=self.seleccionar_directorio).pack(side=tk.LEFT, padx=5)

        # Sección: Filtros
        filtro_frame = ttk.LabelFrame(main_frame, text="Filtros de Factura")
        filtro_frame.pack(fill=tk.X, pady=5)

        grid_frame = ttk.Frame(filtro_frame)
        grid_frame.pack(fill=tk.X)

        ttk.Label(grid_frame, text="Nro. Factura(s):").grid(row=0, column=0, padx=5, pady=5)
        factura_entry = ttk.Entry(grid_frame, textvariable=self.factura)
        factura_entry.grid(row=0, column=1, padx=5, pady=5)
        # Búsqueda incremental (mientras se escribe)
        factura_entry.bind("<KeyRelease>", self.on_key_release)
        factura_entry.bind("<Return>", lambda event: self.iniciar_busqueda())
        
        # Tooltip o ayuda visual simple
        ttk.Label(grid_frame, text="(Separe con coma o espacio)", font=("Arial", 8), foreground="gray").grid(row=1, column=1, padx=5, sticky="n")


        ttk.Label(grid_frame, text="EPS:").grid(row=0, column=2, padx=5, pady=5)
        eps_combo = ttk.Combobox(grid_frame, textvariable=self.eps, values=[
            "FAMISANAR", "SALUD TOTAL", "COOSALUD", "SANITAS", "COMPENSAR", "NUEVA EPS", "FOMAG", "OTRA"
        ])
        eps_combo.grid(row=0, column=3, padx=5, pady=5)
        eps_combo.current(0)

        ttk.Label(grid_frame, text="NIT Proveedor:").grid(row=0, column=4, padx=5, pady=5)
        ttk.Entry(grid_frame, textvariable=self.nit, width=15).grid(row=0, column=5, padx=5, pady=5)

        # Botón Buscar
        ttk.Button(main_frame, text="BUSCAR FACTURA(S)", command=self.iniciar_busqueda).pack(pady=10)

        # Resultados
        res_frame = ttk.LabelFrame(main_frame, text="Resultados")
        res_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Treeview para mostrar archivos
        # Usamos columna #0 para el árbol (nombre e icono)
        columns = ("tipo", "estado", "detalles")
        self.tree = ttk.Treeview(res_frame, columns=columns, show="tree headings")
        
        self.tree.heading("#0", text="Archivo / Carpeta")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("estado", text="Info")
        self.tree.heading("detalles", text="Detalles")
        
        self.tree.column("#0", width=300)
        self.tree.column("tipo", width=100)
        self.tree.column("estado", width=100)
        self.tree.column("detalles", width=800) # Aumentado para ver ruta completa

        scrollbar = ttk.Scrollbar(res_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.tag_configure("error", foreground="red")
        self.tree.tag_configure("carpeta_verde", foreground="#00e676") # Verde brillante para resaltar en tema oscuro
        self.tree.tag_configure("carpeta_naranja", foreground="#FF9800") # Naranja para pendientes

        # Menu Contextual
        self.menu_contextual = tk.Menu(self.root, tearoff=0)
        self.menu_contextual.add_command(label="Abrir", command=lambda: self.abrir_archivo())
        self.menu_contextual.add_command(label="Abrir Ubicación", command=self.abrir_ubicacion)
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(label="Nueva Carpeta", command=self.crear_carpeta)
        self.menu_contextual.add_command(label="Importar Archivo", command=self.importar_archivo)
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(label="Pegar Archivo", command=self.importar_archivo)
        self.menu_contextual.add_command(label="Renombrar", command=self.renombrar_elemento)
        self.menu_contextual.add_command(label="Eliminar", command=self.eliminar_elemento)

        self.tree.bind("<Button-3>", self.mostrar_menu_contextual)
        self.tree.bind("<Double-1>", self.on_double_click)

        # Status Bar con Firma
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_var = tk.StringVar()
        self.status_var.set("Listo.")
        stat_bar = ttk.Label(bottom_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        stat_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.missing_invoices_var = tk.StringVar()
        missing_lbl = ttk.Label(bottom_frame, textvariable=self.missing_invoices_var, foreground="red", font=("Arial", 9, "bold"))
        missing_lbl.pack(side=tk.LEFT, padx=10)

        firma_label = ttk.Label(bottom_frame, text="Reinaldo RH", font=("Arial", 8), foreground="gray")
        firma_label.pack(side=tk.RIGHT, padx=5)

    def _contar_pdfs(self, item_path):
        """
        Cuenta la cantidad de archivos PDF en una carpeta o ZIP.
        Retorna el número de PDFs encontrados.
        """
        contador = 0
        
        if item_path.is_dir():
            # Contar PDFs en carpeta
            for archivo in item_path.iterdir():
                if archivo.is_file() and archivo.suffix.upper() == '.PDF':
                    contador += 1
        
        elif item_path.is_file() and item_path.suffix.upper() == '.ZIP':
            # Contar PDFs en ZIP
            try:
                contenido_zip = LectorZIP.listar_contenido(item_path)
                for item in contenido_zip:
                    if item.upper().endswith('.PDF'):
                        contador += 1
            except:
                pass
        
        return contador

    def seleccionar_directorio(self):
        directorio = filedialog.askdirectory()
        if directorio:
            self.ruta_raiz.set(directorio)
            self.buscador = Buscador(directorio)

    def on_key_release(self, event):
        """Maneja el evento de soltar tecla con debouncing."""
        if self.search_timer:
            self.root.after_cancel(self.search_timer)
        
        # Solo buscar si hay al menos 3 caracteres (ajustable)
        if len(self.factura.get().strip()) >= 3:
            self.search_timer = self.root.after(400, self.iniciar_busqueda)

    def iniciar_busqueda(self):
        root_dir = self.ruta_raiz.get()
        factura_input = self.factura.get()
        
        if not root_dir:
            return # No molestar con diálogos en búsqueda incremental
            
        if not factura_input:
            # Limpiar si no hay texto
            self.item_paths.clear()
            for item in self.tree.get_children():
                self.tree.delete(item)
            return

        # Detener búsqueda anterior si está corriendo
        self.stop_search_event.set()
        
        # Procesar entrada de facturas
        import re
        facturas = [f.strip() for f in re.split(r'[,\s;]+', factura_input) if f.strip()]
        
        if not facturas:
             return

        # Limpiar resultados anteriores
        self.item_paths.clear()
        self.missing_invoices_var.set("")
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.status_var.set(f"Buscando...")
        
        # Nueva señal de parada
        self.stop_search_event = threading.Event()
        
        # Ejecutar en hilo
        self.search_thread = threading.Thread(
            target=self._proceso_busqueda, 
            args=(facturas, self.stop_search_event), 
            daemon=True
        )
        self.search_thread.start()

    def _proceso_busqueda(self, facturas, stop_event):
        eps = self.eps.get()
        nit_proveedor = self.nit.get()

        if not self.buscador:
            self.buscador = Buscador(self.ruta_raiz.get())

        total_carpetas = 0
        facturas_no_encontradas = []
        
        # Buscar para cada factura
        for factura in facturas:
            if stop_event.is_set(): return
            
            encontrado_algo = False
            carpetas_encontradas = self.buscador.buscar_factura(factura, stop_event=stop_event)
            
            if stop_event.is_set(): return
            
            # Buscar también archivos .sin/.icon
            # Nota: Esto debería idealmente estar en Buscador, pero lo agrego aquí rápido para no tocar lógica interna compleja
            # O mejor, usamos Buscador si tiene método genérico, o escaneamos root
            archivos_extra = []
            try:
                 root_path = Path(self.ruta_raiz.get())
                 # Búsqueda recursiva de archivos .sin o .icon que contengan el número de factura
                 # Esto puede ser lento si hay muchos archivos, pero es lo que pide
                 for ext in ['*.sin', '*.icon', '*.SIN', '*.ICON']:
                     for path in root_path.rglob(ext):
                         if factura in path.name:
                             archivos_extra.append(path)
            except Exception as e:
                print(f"Error buscando extras: {e}")

            if carpetas_encontradas or archivos_extra:
                 encontrado_algo = True
                 total_carpetas += len(carpetas_encontradas) + len(archivos_extra)
            
            if not encontrado_algo:
                facturas_no_encontradas.append(factura)
                continue

            # Agrupar resultados bajo un nodo de "Factura: X"
            factura_node = self.tree.insert("", tk.END, text=f"Resultados Factura: {factura}", values=("", "", ""), open=True)

            # Procesar resultados
            for item_path in carpetas_encontradas:
                # Determinar si es carpeta o ZIP
                if item_path.is_dir():
                    # Es una carpeta - Contar PDFs para determinar color
                    num_pdfs = self._contar_pdfs(item_path)
                    es_completa = num_pdfs >= 4
                    tag_color = "carpeta_verde" if es_completa else "carpeta_naranja"
                    estado_texto = f"Encontrada ({num_pdfs} PDFs)"
                    
                    folder_node = self.tree.insert(factura_node, tk.END, text=item_path.name, image=self.img_folder, 
                                                   values=("Carpeta", estado_texto, str(item_path)), open=True, tags=(tag_color,))
                    self.item_paths[folder_node] = item_path
                    
                    # Listar todo el contenido
                    contenido = self.buscador.listar_archivos(item_path)
                    
                    # Filtrar archivos para verificación (solo PDFs en raíz cuentan para "completa" por ahora, o ajustamos lógica)
                    archivos_para_verificacion = [f for f in contenido if f.is_file() and f.suffix.upper() in ['.PDF', '.ZIP']]
                    
                    # Verificar estado de la factura
                    resultado_verificacion = self.verificador.verificar_factura(archivos_para_verificacion, eps, factura, nit_proveedor)
                    status_text = "COMPLETA" if resultado_verificacion["completa"] else "INCOMPLETA"
                    
                    self.tree.insert(folder_node, tk.END, text="Estado Factura", values=("Info", status_text, resultado_verificacion["detalles"][0]))

                    # Listar contenido (carpetas y archivos)
                    for item in contenido:
                        if item.is_dir():
                            # Es una subcarpeta
                            sub_node = self.tree.insert(folder_node, tk.END, text=item.name, image=self.img_folder, 
                                                        values=("Carpeta", "Contenido", str(item)))
                            self.item_paths[sub_node] = item
                        else:
                            # Es un archivo
                            tipo = item.suffix.upper()
                            info_extra = ""
                            tags = ()
                            img = ""

                            if tipo == '.PDF':
                                info_pdf = LectorPDF.obtener_info(item)
                                if info_pdf["es_valido"]:
                                    info_extra = f"Páginas: {info_pdf['paginas']}"
                                else:
                                    info_extra = "PDF Inválido o Error"
                                
                                if factura not in item.name:
                                    tags = ("error",)
                                img = self.img_pdf
                            
                            elif tipo == '.ZIP':
                                pass # Se procesa abajo
                            
                            else:
                                # Otros archivos
                                info_extra = "Archivo"

                            # Insertar nodo del archivo
                            file_node = self.tree.insert(folder_node, tk.END, text=item.name, image=img, 
                                                         values=(tipo, "Archivo", info_extra), tags=tags)
                            self.item_paths[file_node] = item

                            # Si es ZIP, listar contenido
                            if tipo == '.ZIP':
                                try:
                                    contenido_zip = LectorZIP.listar_contenido(item)
                                    for zitem in contenido_zip:
                                        tags_zip = ()
                                        img_zip = ""
                                        if zitem.upper().endswith('.PDF'):
                                            img_zip = self.img_pdf
                                            if factura not in zitem:
                                                tags_zip = ("error",)
                                        
                                        zip_content_node = self.tree.insert(file_node, tk.END, text=zitem, image=img_zip, 
                                                                            values=("CONTENIDO ZIP", "", ""), tags=tags_zip)
                                        self.item_paths[zip_content_node] = (item, zitem)
                                except Exception as e:
                                    print(f"Error listando ZIP {item}: {e}")

                elif item_path.is_file() and item_path.suffix.upper() == '.ZIP':
                    # Es un ZIP encontrado directamente como resultado principal
                    # Contar PDFs para determinar color
                    num_pdfs = self._contar_pdfs(item_path)
                    es_completa = num_pdfs >= 4
                    tag_color = "carpeta_verde" if es_completa else "carpeta_naranja"
                    estado_texto = f"Encontrado ({num_pdfs} PDFs)"
                    
                    zip_node = self.tree.insert(factura_node, tk.END, text=item_path.name, image=self.img_zip,
                                               values=("ZIP", estado_texto, str(item_path)), open=True, tags=(tag_color,))
                    self.item_paths[zip_node] = item_path
                    
                    try:
                        contenido_zip = LectorZIP.listar_contenido(item_path)
                        for item in contenido_zip:
                            tags_zip = ()
                            img_zip = ""
                            if item.upper().endswith('.PDF'):
                                img_zip = self.img_pdf
                                if factura not in item:
                                    tags_zip = ("error",)
                            zip_content_node = self.tree.insert(zip_node, tk.END, text=item, image=img_zip,
                                                                values=("CONTENIDO ZIP", "", ""), tags=tags_zip)
                            self.item_paths[zip_content_node] = (item_path, item)
                    except Exception as e:
                        print(f"Error listando ZIP principal {item_path}: {e}")

            # Procesar archivos extra (.sin, .icon)
            for file_path in archivos_extra:
                ext = file_path.suffix.lower()
                img = self.img_sin if ext in ['.sin', '.icon'] else ""
                # Insertar como archivo encontrado
                self.tree.insert(factura_node, tk.END, text=file_path.name, image=img, 
                                 values=(file_path.suffix.upper(), "Encontrado", str(file_path)), open=True)
                # No agregamos a item_paths por ahora si no queremos acción de abrir, o sí:
                # self.item_paths[...toca crear nodo...] - simplificado arriba

        if stop_event.is_set(): return
        
        if facturas_no_encontradas:
             msg = f"Facturas NO encontradas: {', '.join(facturas_no_encontradas)}"
             self.root.after(0, lambda: self.missing_invoices_var.set(msg))
        
        if total_carpetas == 0 and not facturas_no_encontradas:
             self.root.after(0, lambda: self.status_var.set("No se encontraron resultados."))
        else:
             self.root.after(0, lambda: self.status_var.set(f"Búsqueda finalizada. {total_carpetas} coincidencias."))

    def mostrar_menu_contextual(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            # Habilitar/Deshabilitar opciones según tipo
            path = self.item_paths.get(item)
            
            if isinstance(path, Path):
                # Es un archivo o carpeta real
                is_dir = path.is_dir()
                self.menu_contextual.entryconfig("Nueva Carpeta", state="normal" if is_dir else "disabled")
                self.menu_contextual.entryconfig("Importar Archivo", state="normal" if is_dir else "disabled")
                self.menu_contextual.entryconfig("Pegar Archivo", state="normal" if is_dir or path.suffix.lower() == '.zip' else "disabled")
                self.menu_contextual.entryconfig("Renombrar", state="normal")
                self.menu_contextual.entryconfig("Eliminar", state="normal")
                
                # Opción para ver PDF
                if path.is_file() and path.suffix.upper() == '.PDF':
                     self.menu_contextual.add_command(label="Ver Contenido PDF", command=self.ver_contenido)
                else:
                     try:
                        self.menu_contextual.delete("Ver Contenido PDF")
                     except: pass

                self.menu_contextual.post(event.x_root, event.y_root)
            else:
                # Es contenido de un ZIP (Tupla)
                self.menu_contextual.entryconfig("Nueva Carpeta", state="disabled")
                self.menu_contextual.entryconfig("Importar Archivo", state="disabled")
                self.menu_contextual.entryconfig("Pegar Archivo", state="disabled")
                self.menu_contextual.entryconfig("Renombrar", state="disabled") # No soportado en ZIP por ahora
                self.menu_contextual.entryconfig("Eliminar", state="normal")
                
                self.menu_contextual.delete("Ver Contenido PDF")
                self.menu_contextual.post(event.x_root, event.y_root)

    def on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.abrir_archivo(item)

    def abrir_archivo(self, item=None):
        if not item:
            item = self.tree.selection()[0]
        
        path_data = self.item_paths.get(item)
        if path_data:
            try:
                # Caso 1: Es un archivo dentro de un ZIP (Tuple: zip_path, member_name)
                if isinstance(path_data, tuple):
                    zip_path, member_name = path_data
                    if zip_path.exists():
                        # Extraer a carpeta temporal
                        temp_dir = Path(tempfile.gettempdir()) / "BuscadorFacturasTemp"
                        temp_dir.mkdir(exist_ok=True)
                        extracted_path = LectorZIP.extraer_archivo(zip_path, member_name, temp_dir)
                        
                        if extracted_path:
                            os.startfile(extracted_path)
                            self.status_var.set(f"Abriendo temporal: {member_name}")
                        else:
                             messagebox.showerror("Error", f"No se pudo extraer {member_name}")
                    else:
                        messagebox.showwarning("Advertencia", f"El archivo ZIP ya no existe: {zip_path}")

                # Caso 2: Es un archivo o carpeta real en disco
                elif isinstance(path_data, Path):
                    if path_data.exists():
                        os.startfile(path_data)
                        self.status_var.set(f"Abriendo: {path_data.name}")
                    else:
                        messagebox.showwarning("Advertencia", f"La ruta no existe: {path_data}")

            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el elemento: {e}")

    def abrir_ubicacion(self):
        item = self.tree.selection()[0]
        path = self.item_paths.get(item)
        if path:
            if path.is_file():
                folder = path.parent
            else:
                folder = path
            try:
                os.startfile(folder)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir la ubicación: {e}")

    def renombrar_elemento(self):
        item = self.tree.selection()[0]
        path = self.item_paths.get(item)
        if not path: return

        nuevo_nombre = simpledialog.askstring("Renombrar", "Nuevo nombre:", initialvalue=path.name)
        if nuevo_nombre and nuevo_nombre != path.name:
            nuevo_path = path.with_name(nuevo_nombre)
            try:
                path.rename(nuevo_path)
                # Actualizar Treeview y dict
                self.item_paths[item] = nuevo_path
                self.tree.item(item, text=nuevo_nombre)
                self.status_var.set(f"Renombrado a {nuevo_nombre}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo renombrar: {e}")

    def eliminar_elemento(self):
        item = self.tree.selection()[0]
        path = self.item_paths.get(item)
        if not path: return

        confirm = messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de eliminar este elemento?\nEsta acción no se puede deshacer.")
        if confirm:
            try:
                # Detectar si es elemento de ZIP (Tupla) o real (Path)
                if isinstance(path, tuple):
                    zip_path, member_name = path
                    if LectorZIP.eliminar_archivo(zip_path, member_name):
                        self.tree.delete(item)
                        del self.item_paths[item]
                        self.status_var.set(f"Eliminado de ZIP: {member_name}")
                        self._actualizar_estado_padre(item)
                else:
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    
                    self.tree.delete(item)
                    del self.item_paths[item]
                    self.status_var.set(f"Eliminado: {path.name}")
                    self._actualizar_estado_padre(item)
            except Exception as e:
                 messagebox.showerror("Error", f"No se pudo eliminar: {e}")

    def _actualizar_estado_padre(self, item_modificado):
        """
        Busca el nodo raíz de la factura o el nodo de carpeta/ZIP principal 
        y vuelve a calcular su estado (color y conteo de PDFs).
        """
        parent = self.tree.parent(item_modificado)
        if not parent: return
        
        # Encontrar el nodo que representa la carpeta o ZIP (el que tiene la ruta en item_paths)
        target_node = item_modificado if item_modificado in self.item_paths and isinstance(self.item_paths[item_modificado], Path) else parent
        
        # Si el target_node es contenido de un ZIP, subir un nivel más
        if target_node in self.item_paths and isinstance(self.item_paths[target_node], tuple):
            target_node = self.tree.parent(target_node)

        path = self.item_paths.get(target_node)
        if not path or not path.exists(): return

        # Recalcular conteo de PDFs
        num_pdfs = self._contar_pdfs(path)
        es_completa = num_pdfs >= 4
        tag_color = "carpeta_verde" if es_completa else "carpeta_naranja"
        estado_texto = f"Encontrada ({num_pdfs} PDFs)" if path.is_dir() else f"Encontrado ({num_pdfs} PDFs)"
        
        # Actualizar valores visuales
        vals = list(self.tree.item(target_node, "values"))
        vals[1] = estado_texto
        self.tree.item(target_node, values=vals, tags=(tag_color,))
        
        # Opcional: Re-verificar la factura completa (lógica de EPS)
        # Esto requiere el número de factura y la EPS, que podemos extraer del nodo abuelo si es necesario
        # Por ahora, con el conteo de PDFs y el color es suficiente para el requerimiento visual.

    def crear_carpeta(self):
        item = self.tree.selection()[0]
        parent_path = self.item_paths.get(item)
        if not parent_path or not parent_path.is_dir(): return

        nombre = simpledialog.askstring("Nueva Carpeta", "Nombre de la carpeta:")
        if nombre:
            new_dir = parent_path / nombre
            try:
                new_dir.mkdir()
                # Insertar en treeview
                node = self.tree.insert(item, 0, text=nombre, image=self.img_folder, values=("Carpeta", "Nueva", str(new_dir)))
                self.item_paths[node] = new_dir
                self.tree.item(item, open=True)
                self.status_var.set(f"Carpeta creada: {nombre}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear carpeta: {e}")

    def importar_archivo(self):
        item = self.tree.selection()[0]
        dest_path = self.item_paths.get(item)
        if not dest_path: return

        filepath = filedialog.askopenfilename(title="Seleccionar archivo para importar")
        if filepath:
            src = Path(filepath)
            
            try:
                # Caso ZIP
                if dest_path.is_file() and dest_path.suffix.lower() == '.zip':
                    if LectorZIP.agregar_archivo(dest_path, src):
                        # Insertar en treeview bajo el ZIP
                        img = self.img_pdf if src.suffix.upper() == '.PDF' else ""
                        node = self.tree.insert(item, tk.END, text=src.name, image=img, values=("CONTENIDO ZIP", "Agregado", ""))
                        self.item_paths[node] = (dest_path, src.name)
                        self.tree.item(item, open=True)
                        self.status_var.set(f"Agregado al ZIP: {src.name}")
                
                # Caso Carpeta
                elif dest_path.is_dir():
                    dest = dest_path / src.name
                    shutil.copy2(src, dest)
                    # Insertar en treeview
                    tipo = src.suffix.upper()
                    img = self.img_pdf if tipo == '.PDF' else ""
                    node = self.tree.insert(item, tk.END, text=src.name, image=img, values=(tipo, "Importado", ""))
                    self.item_paths[node] = dest
                    self.tree.item(item, open=True)
                    self.status_var.set(f"Archivo importado: {src.name}")
                
                # Siempre re-verificar colores de carpetas/ZIPs después de importar
                # (Idealmente llamar a una función que refresque el nodo raíz de la factura)

            except Exception as e:
                 messagebox.showerror("Error", f"No se pudo importar: {e}")

    def ver_contenido(self):
        item = self.tree.selection()[0]
        path = self.item_paths.get(item)
        if not path or not path.is_file() or path.suffix.upper() != '.PDF': return

        contenido = LectorPDF.extraer_texto(path)
        
        # Ventana de visualización
        top = tk.Toplevel(self.root)
        top.title(f"Contenido: {path.name}")
        top.geometry("600x400")
        
        text_area = tk.Text(top, wrap=tk.WORD, padx=10, pady=10)
        text_area.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_area, command=text_area.yview)
        text_area.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_area.insert(tk.END, contenido)
        text_area.config(state=tk.DISABLED) # Solo lectura
