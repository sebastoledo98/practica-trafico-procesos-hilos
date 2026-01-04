from controlador import ControladorTrafico

if __name__ == "__main__":
    # Es importante ejecutar esto dentro del bloque main para
    # compatibilidad con Windows en multiprocessing
    app = ControladorTrafico()
    app.iniciar()
