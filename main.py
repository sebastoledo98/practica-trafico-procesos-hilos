#from controlador import ControladorTrafico
from gui_app import InterfazTrafico
import tkinter as tk
#import threading

if __name__ == "__main__":
    MODO_EJECUCION = "PROCESO"  # "PROCESO" o "HILO"

    #app_logica = ControladorTrafico(modo=MODO_EJECUCION)

    #t = threading.Thread(target=app_logica.iniciar)
    #t.start()

    root = tk.Tk()
    #gui = InterfazTrafico(root, app_logica)
    app = InterfazTrafico(root)

    def on_closing():
        if app.controlador:
            app.controlador.evento_fin.set()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
