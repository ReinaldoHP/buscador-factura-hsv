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
        self.nit = tk.StringVar(value="899999032")
        
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

        ttk.Label(grid_frame, text="Nro. Factura:").grid(row=0, column=0, padx=5, pady=5)
        factura_entry = ttk.Entry(grid_frame, textvariable=self.factura)
        factura_entry.grid(row=0, column=1, padx=5, pady=5)
        factura_entry.bind("<Return>", lambda event: self.iniciar_busqueda())

        ttk.Label(grid_frame, text="EPS:").grid(row=0, column=2, padx=5, pady=5)
        eps_combo = ttk.Combobox(grid_frame, textvariable=self.eps, values=[
            "FAMISANAR", "SALUD TOTAL", "COOSALUD", "SANITAS", "COMPENSAR", "NUEVA EPS", "FOMAG", "OTRA"
        ])
        eps_combo.grid(row=0, column=3, padx=5, pady=5)
        eps_combo.current(0)

        ttk.Label(grid_frame, text="NIT Proveedor:").grid(row=0, column=4, padx=5, pady=5)
        ttk.Entry(grid_frame, textvariable=self.nit, width=15).grid(row=0, column=5, padx=5, pady=5)

        # Botón Buscar
        ttk.Button(main_frame, text="BUSCAR FACTURA", command=self.iniciar_busqueda).pack(pady=10)

        # Resultados
        res_frame = ttk.LabelFrame(main_frame, text="Resultados")
        res_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Treeview para mostrar archivos
        columns = ("nombre", "tipo", "estado", "detalles")
        self.tree = ttk.Treeview(res_frame, columns=columns, show="headings")
        self.tree.heading("nombre", text="Archivo / Carpeta")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("estado", text="Info")
        self.tree.heading("detalles", text="Detalles")
        
        self.tree.column("nombre", width=300)
        self.tree.column("tipo", width=100)
        self.tree.column("estado", width=100)
        self.tree.column("detalles", width=300)

        scrollbar = ttk.Scrollbar(res_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.tag_configure("error", foreground="red")

        # Menu Contextual
        self.menu_contextual = tk.Menu(self.root, tearoff=0)
        self.menu_contextual.add_command(label="Abrir", command=lambda: self.abrir_archivo())
        self.menu_contextual.add_command(label="Abrir Ubicación", command=self.abrir_ubicacion)
        self.menu_contextual.add_separator()
        self.menu_contextual.add_command(label="Nueva Carpeta", command=self.crear_carpeta)
        self.menu_contextual.add_command(label="Importar Archivo", command=self.importar_archivo)
        self.menu_contextual.add_separator()
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

        firma_label = ttk.Label(bottom_frame, text="Reinaldo RH", font=("Arial", 8), foreground="gray")
        firma_label.pack(side=tk.RIGHT, padx=5)

    def seleccionar_directorio(self):
        directorio = filedialog.askdirectory()
        if directorio:
            self.ruta_raiz.set(directorio)
            self.buscador = Buscador(directorio)

    def iniciar_busqueda(self):
        root_dir = self.ruta_raiz.get()
        factura = self.factura.get()
        
        if not root_dir:
            messagebox.showwarning("Advertencia", "Por favor seleccione una carpeta raíz.")
            return
        if not factura:
            messagebox.showwarning("Advertencia", "Por favor ingrese el número de factura.")
            return

        # Limpiar resultados anteriores
        self.item_paths.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.status_var.set("Buscando...")
        self.root.update_idletasks()
        
        # Ejecutar en hilo para no congelar GUI
        threading.Thread(target=self._proceso_busqueda, args=(factura,), daemon=True).start()

    def _proceso_busqueda(self, factura):
        eps = self.eps.get()
        nit_proveedor = self.nit.get()

        if not self.buscador:
            self.buscador = Buscador(self.ruta_raiz.get())

        carpetas_encontradas = self.buscador.buscar_factura(factura)

        if not carpetas_encontradas:
            self.root.after(0, lambda: messagebox.showinfo("Información", "No se encontraron carpetas para esa factura."))
            self.root.after(0, lambda: self.status_var.set("Búsqueda finalizada. Sin resultados."))
            return

        # Procesar resultados
        for item_path in carpetas_encontradas:
            # Determinar si es carpeta o ZIP
            if item_path.is_dir():
                # Es una carpeta
                folder_node = self.tree.insert("", tk.END, values=(item_path.name, "Carpeta", "Encontrada", str(item_path)), open=True)
                self.item_paths[folder_node] = item_path
                
                # Listar todo el contenido
                contenido = self.buscador.listar_archivos(item_path)
                
                # Filtrar archivos para verificación (solo PDFs en raíz cuentan para "completa" por ahora, o ajustamos lógica)
                archivos_para_verificacion = [f for f in contenido if f.is_file() and f.suffix.upper() in ['.PDF', '.ZIP']]
                
                # Verificar estado de la factura
                resultado_verificacion = self.verificador.verificar_factura(archivos_para_verificacion, eps, factura, nit_proveedor)
                status_text = "COMPLETA" if resultado_verificacion["completa"] else "INCOMPLETA"
                
                self.tree.insert(folder_node, tk.END, values=("Estado Factura", "Info", status_text, resultado_verificacion["detalles"][0]))

                # Listar contenido (carpetas y archivos)
                for item in contenido:
                    if item.is_dir():
                        # Es una subcarpeta
                        sub_node = self.tree.insert(folder_node, tk.END, values=(item.name, "Carpeta", "Contenido", str(item)))
                        self.item_paths[sub_node] = item
                    else:
                        # Es un archivo
                        tipo = item.suffix.upper()
                        info_extra = ""
                        tags = ()

                        if tipo == '.PDF':
                            info_pdf = LectorPDF.obtener_info(item)
                            if info_pdf["es_valido"]:
                                info_extra = f"Páginas: {info_pdf['paginas']}"
                            else:
                                info_extra = "PDF Inválido o Error"
                            
                            if factura not in item.name:
                                tags = ("error",)
                        
                        elif tipo == '.ZIP':
                            pass # Se procesa abajo
                        
                        else:
                            # Otros archivos
                            info_extra = "Archivo"

                        # Insertar nodo del archivo
                        file_node = self.tree.insert(folder_node, tk.END, values=(item.name, tipo, "Archivo", info_extra), tags=tags)
                        self.item_paths[file_node] = item

                        # Si es ZIP, listar contenido
                        if tipo == '.ZIP':
                            try:
                                contenido_zip = LectorZIP.listar_contenido(item)
                                for zitem in contenido_zip:
                                    tags_zip = ()
                                    if zitem.upper().endswith('.PDF') and factura not in zitem:
                                        tags_zip = ("error",)
                                    zip_content_node = self.tree.insert(file_node, tk.END, values=(zitem, "CONTENIDO ZIP", "", ""), tags=tags_zip)
                                    self.item_paths[zip_content_node] = (item, zitem)
                            except Exception as e:
                                print(f"Error listando ZIP {item}: {e}")

            elif item_path.is_file() and item_path.suffix.upper() == '.ZIP':
                # Es un ZIP encontrado directamente como resultado principal
                zip_node = self.tree.insert("", tk.END, values=(item_path.name, "ZIP", "Encontrado", str(item_path)), open=True)
                self.item_paths[zip_node] = item_path
                
                try:
                    contenido_zip = LectorZIP.listar_contenido(item_path)
                    for item in contenido_zip:
                        tags_zip = ()
                        if item.upper().endswith('.PDF') and factura not in item:
                            tags_zip = ("error",)
                        zip_content_node = self.tree.insert(zip_node, tk.END, values=(item, "CONTENIDO ZIP", "", ""), tags=tags_zip)
                        self.item_paths[zip_content_node] = (item_path, item)
                except Exception as e:
                    print(f"Error listando ZIP principal {item_path}: {e}")

        self.root.after(0, lambda: self.status_var.set(f"Búsqueda finalizada. {len(carpetas_encontradas)} carpetas encontradas."))

    def mostrar_menu_contextual(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            # Habilitar/Deshabilitar opciones según tipo
            path = self.item_paths.get(item)
            
            if path:
                # Es un archivo o carpeta real
                self.menu_contextual.entryconfig("Nueva Carpeta", state="normal" if path.is_dir() else "disabled")
                self.menu_contextual.entryconfig("Importar Archivo", state="normal" if path.is_dir() else "disabled")
                
                # Opción para ver PDF
                if path.is_file() and path.suffix.upper() == '.PDF':
                     self.menu_contextual.add_command(label="Ver Contenido PDF", command=self.ver_contenido)
                else:
                     try:
                        self.menu_contextual.delete("Ver Contenido PDF")
                     except: pass

                self.menu_contextual.post(event.x_root, event.y_root)
            else:
                # Es contenido de un ZIP u otro elemento virtual
                pass

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
                current_values = self.tree.item(item, "values")
                new_values = (nuevo_nombre,) + current_values[1:]
                self.tree.item(item, values=new_values)
                self.status_var.set(f"Renombrado a {nuevo_nombre}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo renombrar: {e}")

    def eliminar_elemento(self):
        item = self.tree.selection()[0]
        path = self.item_paths.get(item)
        if not path: return

        confirm = messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de eliminar '{path.name}'?\nEsta acción no se puede deshacer.")
        if confirm:
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                
                self.tree.delete(item)
                del self.item_paths[item]
                self.status_var.set(f"Eliminado: {path.name}")
            except Exception as e:
                 messagebox.showerror("Error", f"No se pudo eliminar: {e}")

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
                node = self.tree.insert(item, 0, values=(nombre, "Carpeta", "Nueva", str(new_dir)))
                self.item_paths[node] = new_dir
                self.tree.item(item, open=True)
                self.status_var.set(f"Carpeta creada: {nombre}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear carpeta: {e}")

    def importar_archivo(self):
        item = self.tree.selection()[0]
        parent_path = self.item_paths.get(item)
        if not parent_path or not parent_path.is_dir(): return

        filepath = filedialog.askopenfilename(title="Seleccionar archivo para importar")
        if filepath:
            src = Path(filepath)
            dest = parent_path / src.name
            try:
                shutil.copy2(src, dest)
                 # Insertar en treeview
                tipo = src.suffix.upper()
                node = self.tree.insert(item, tk.END, values=(src.name, tipo, "Importado", ""))
                self.item_paths[node] = dest
                self.tree.item(item, open=True)
                
                # Si es ZIP, intentar expandir (opcional, pero consistente)
                if tipo == '.ZIP':
                     try:
                        contenido_zip = LectorZIP.listar_contenido(dest)
                        for zitem in contenido_zip:
                             self.tree.insert(node, tk.END, values=(zitem, "CONTENIDO ZIP", "", ""))
                     except: pass

                self.status_var.set(f"Archivo importado: {src.name}")
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
