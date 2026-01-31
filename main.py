import ttkbootstrap as ttk
from interfaz import App

def main():
    # Temas modernos: flatly, cosmo, journal, superhero, darkly (oscuro)...
    root = ttk.Window(themename="darkly")
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
