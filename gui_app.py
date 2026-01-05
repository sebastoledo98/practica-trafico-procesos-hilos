import tkinter as tk
from tkinter import ttk, messagebox
import threading
from config import VIAS, ROJO, VERDE, AMARILLO
import random

# Importamos tu controlador unificado
from controlador import ControladorTrafico

# Configuración Visual
C_PASTO = "#2ecc71"
C_ASFALTO = "#34495e"
C_CALLE_BORDE = "#2c3e50"
C_TECHO = ["#e74c3c", "#e67e22", "#8e44ad", "#d35400"]
ANCHO_CALLE = 140
CENTRO = 300


class InterfazTrafico:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Tráfico - Panel de Control")
        self.root.geometry("900x650")

        # --- Estado de la App ---
        self.controlador = None
        self.hilo_simulacion = None
        self.simulacion_activa = False

        # Variables de Control (Tkinter)
        self.var_modo = tk.StringVar(value="PROCESO")  # "PROCESO" o "HILO"
        self.var_ciclos = tk.IntVar(value=5)

        # Listas para animación
        self.prev_tam_colas = [0, 0, 0, 0]
        self.animaciones_activas = []
        self.luces_gui = {}

        # --- Layout Principal ---
        # 1. Panel Lateral (Izquierda)
        self.frame_control = tk.Frame(
            root, width=250, bg="#ecf0f1", padx=15, pady=15)
        self.frame_control.pack(side=tk.LEFT, fill=tk.Y)
        self.frame_control.pack_propagate(False)  # Forzar ancho fijo

        # 2. Canvas (Derecha)
        self.frame_canvas = tk.Frame(root, bg=C_PASTO)
        self.frame_canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            self.frame_canvas, width=600, height=600, bg=C_PASTO)
        self.canvas.pack(pady=20)

        # --- Construcción de UI ---
        self.crear_panel_control()
        self.inicializar_canvas()

    def crear_panel_control(self):
        """Crea los widgets del panel lateral"""
        # Título
        tk.Label(self.frame_control, text="🚦 CONTROL DE TRÁFICO",
                 bg="#ecf0f1", font=("Arial", 14, "bold")).pack(pady=(0, 20))

        # Sección: Modo de Ejecución
        frame_modo = tk.LabelFrame(
            self.frame_control, text="Modo de Ejecución", bg="#ecf0f1", padx=5, pady=5)
        frame_modo.pack(fill="x", pady=10)

        ttk.Radiobutton(frame_modo, text="Multiprocessing (Procesos)",
                        variable=self.var_modo, value="PROCESO").pack(anchor="w")
        ttk.Radiobutton(frame_modo, text="Threading (Hilos)",
                        variable=self.var_modo, value="HILO").pack(anchor="w")

        # Sección: Configuración
        frame_config = tk.LabelFrame(
            self.frame_control, text="Configuración", bg="#ecf0f1", padx=5, pady=5)
        frame_config.pack(fill="x", pady=10)

        tk.Label(frame_config, text="Cantidad de Ciclos:",
                 bg="#ecf0f1").pack(anchor="w")
        ttk.Spinbox(frame_config, from_=1, to=50,
                    textvariable=self.var_ciclos, width=10).pack(pady=5)

        # Botones
        self.btn_iniciar = tk.Button(self.frame_control, text="▶ INICIAR SIMULACIÓN",
                                     bg="#27ae60", fg="white", font=("Arial", 10, "bold"),
                                     command=self.accion_iniciar)
        self.btn_iniciar.pack(fill="x", pady=(20, 5))

        self.btn_reset = tk.Button(self.frame_control, text="⏹ DETENER / LIMPIAR",
                                   bg="#c0392b", fg="white", font=("Arial", 10, "bold"),
                                   state="disabled", command=self.accion_reset)
        self.btn_reset.pack(fill="x", pady=5)

        # Etiqueta de Estado
        self.lbl_estado = tk.Label(self.frame_control, text="Estado: LISTO",
                                   bg="#ecf0f1", fg="#7f8c8d", font=("Arial", 10))
        self.lbl_estado.pack(side=tk.BOTTOM, pady=10)

    def inicializar_canvas(self):
        self.canvas.delete("all")
        self.dibujar_barrio()
        self.dibujar_calles()
        self.crear_semaforos_gui()

        # Panel info en canvas
        self.txt_stats = self.canvas.create_text(20, 20, anchor="nw",
                                                 text="Esperando configuración...",
                                                 fill="white", font=("Consolas", 10))
        bbox = self.canvas.bbox(self.txt_stats)
        self.rect_info = self.canvas.create_rectangle(
            10, 10, 250, 80, fill="black", stipple="gray50")
        self.canvas.tag_lower(self.rect_info, self.txt_stats)

    # --- LÓGICA DE CONTROL ---

    def accion_iniciar(self):
        if self.simulacion_activa:
            return

        # 1. Obtener configuración
        modo = self.var_modo.get()
        ciclos = self.var_ciclos.get()

        self.lbl_estado.config(text=f"Iniciando en modo {
                               modo}...", fg="#d35400")
        self.root.update()

        # 2. Instanciar Controlador (Aquí pasamos los ciclos dinámicos)
        try:
            self.controlador = ControladorTrafico(
                modo=modo, cantidad_ciclos=ciclos)
        except Exception as e:
            messagebox.showerror(
                "Error", f"No se pudo iniciar el controlador: {e}")
            return

        # 3. Arrancar en hilo secundario
        self.hilo_simulacion = threading.Thread(
            target=self.controlador.iniciar)
        self.hilo_simulacion.daemon = True  # Morirá si cerramos la ventana
        self.hilo_simulacion.start()

        # 4. Actualizar GUI
        self.simulacion_activa = True
        self.btn_iniciar.config(state="disabled", bg="gray")
        self.btn_reset.config(state="normal", bg="#c0392b")
        self.lbl_estado.config(text="Estado: EJECUTANDO 🚀", fg="#27ae60")

        # Iniciar bucle visual
        self.actualizar_vista()

    def accion_reset(self):
        if self.controlador:
            self.lbl_estado.config(text="Deteniendo procesos...", fg="#e67e22")
            self.root.update()

            # Señal de parada
            self.controlador.evento_fin.set()

            # Importante: No hacemos join() aquí para no congelar la GUI.
            # Dejamos que los hilos/procesos terminen a su ritmo.

        self.simulacion_activa = False
        self.controlador = None
        self.prev_tam_colas = [0, 0, 0, 0]
        self.animaciones_activas = []
        self.canvas.delete("movil")  # Borrar autos

        self.btn_iniciar.config(state="normal", bg="#27ae60")
        self.btn_reset.config(state="disabled", bg="gray")
        self.lbl_estado.config(text="Estado: RESETEADO 🧹", fg="#2980b9")
        self.canvas.itemconfig(
            self.txt_stats, text="Esperando configuración...")

    def actualizar_vista(self):
        """Bucle principal de renderizado (se repite cada 50ms)"""
        if not self.simulacion_activa or not self.controlador:
            return

        # Verificar si la simulación terminó sola (fin de ciclos)
        if self.controlador.evento_fin.is_set():
            self.simulacion_activa = False
            self.lbl_estado.config(text="Estado: FINALIZADO 🏁", fg="black")
            self.btn_iniciar.config(state="normal", bg="#27ae60")
            self.btn_reset.config(state="disabled", bg="gray")
            return

        self.canvas.delete("movil")
        mapa_colores = {ROJO: "#c0392b", VERDE: "#2ecc71", AMARILLO: "#f1c40f"}
        info_txt = f"MODO: {
            self.var_modo.get()}\nCICLOS RESTANTES: Aprox...\n\n"

        for i, via in enumerate(VIAS):
            try:
                # Acceso unificado (.value funciona para Value de multiprocessing y EstadoCompartido de hilos)
                val_luz = self.controlador.estados_luz[i].value
                self.canvas.itemconfig(
                    self.luces_gui[via], fill=mapa_colores[val_luz])

                # Tamaño de cola (Compatible con ambos modos)
                cola = self.controlador.colas[i]
                try:
                    cant = cola.qsize()
                except NotImplementedError:
                    cant = "?"  # Mac OS a veces falla aquí con multiprocessing

                # Renderizar y detectar animaciones
                self.gestionar_colas_visuales(
                    via, i, cant if cant != "?" else 0, val_luz)
                info_txt += f"{via}: {cant} autos\n"

            except Exception:
                pass  # Evitar crash si leemos justo cuando se está cerrando

        self.procesar_animaciones()
        self.canvas.itemconfig(self.txt_stats, text=info_txt)

        # Programar siguiente frame
        self.root.after(50, self.actualizar_vista)

    # --- FUNCIONES DE DIBUJO (Idénticas a las anteriores) ---
    def dibujar_barrio(self):
        """Dibuja casas decorativas en las 4 esquinas"""
        # Coordenadas de las 4 esquinas (evitando el centro donde van las calles)
        zonas = [
            (0, 0, CENTRO-ANCHO_CALLE//2, CENTRO-ANCHO_CALLE//2),  # Noroeste
            (CENTRO+ANCHO_CALLE//2, 0, 600, CENTRO-ANCHO_CALLE//2),  # Noreste
            (0, CENTRO+ANCHO_CALLE//2, CENTRO-ANCHO_CALLE//2, 600),  # Suroeste
            (CENTRO+ANCHO_CALLE//2, CENTRO+ANCHO_CALLE//2, 600, 600)  # Sureste
        ]

        for x1, y1, x2, y2 in zonas:
            # Dibujar 3 casitas por zona
            for _ in range(3):
                cx = random.randint(int(x1)+20, int(x2)-40)
                cy = random.randint(int(y1)+20, int(y2)-40)
                tam = 30
                color_techo = random.choice(C_TECHO)

                # Pared
                self.canvas.create_rectangle(
                    cx, cy, cx+tam, cy+tam, fill="#ecf0f1", outline="#bdc3c7")
                # Techo (triángulo)
                self.canvas.create_polygon(
                    cx-5, cy, cx+tam+5, cy, cx+tam/2, cy-15, fill=color_techo, outline="black")
                # Puerta
                self.canvas.create_rectangle(
                    cx+10, cy+15, cx+20, cy+tam, fill="#7f8c8d")

    def dibujar_calles(self):
        c = CENTRO
        m = ANCHO_CALLE // 2
        # Bordes
        self.canvas.create_rectangle(
            c-m-5, 0, c+m+5, 600, fill=C_CALLE_BORDE, outline="")
        self.canvas.create_rectangle(
            0, c-m-5, 600, c+m+5, fill=C_CALLE_BORDE, outline="")
        # Asfalto
        self.canvas.create_rectangle(
            c-m, 0, c+m, 600, fill=C_ASFALTO, outline="")
        self.canvas.create_rectangle(
            0, c-m, 600, c+m, fill=C_ASFALTO, outline="")
        # Líneas
        for i in range(0, 600, 40):
            if not (c-m < i < c+m):
                self.canvas.create_line(c, i, c, i+20, fill="#f1c40f", width=2)
                self.canvas.create_line(i, c, i+20, c, fill="#f1c40f", width=2)
        # Pare
        self.canvas.create_line(c, c-m, c+m, c-m, fill="white", width=4)
        self.canvas.create_line(c-m, c+m, c, c+m, fill="white", width=4)
        self.canvas.create_line(c+m, c, c+m, c+m, fill="white", width=4)
        self.canvas.create_line(c-m, c-m, c-m, c, fill="white", width=4)

        """
    def crear_semaforos_gui(self):
        offset = ANCHO_CALLE // 2 + 30
        c = CENTRO
        posiciones = {
            "NORTE": (c + offset, c - offset), "SUR": (c - offset, c + offset),
            "ESTE": (c + offset, c + offset), "OESTE": (c - offset, c - offset)
        }
        for via, (x, y) in posiciones.items():
            self.canvas.create_line(
                x, y, x, y+20 if via in ["NORTE", "ESTE"] else y-20, width=3)
            self.canvas.create_rectangle(x-10, y-10, x+10, y+10, fill="black")
            self.luces_gui[via] = self.canvas.create_oval(
                x-7, y-7, x+7, y+7, fill="grey")
                """

    def crear_semaforos_gui(self):
        """
        Dibuja los semáforos orientados según la vía que controlan.
        Norte/Sur -> Rectángulos Horizontales (miran al tráfico vertical)
        Este/Oeste -> Rectángulos Verticales (miran al tráfico horizontal)
        """
        c = CENTRO
        m = ANCHO_CALLE // 2
        offset_calle = m + 15  # Distancia desde el borde de la calle

        # Configuraciones de orientación
        # (x, y) = centro del semáforo
        # 'orientacion': 'H' (Horizontal) o 'V' (Vertical)

        # NOTA: Ajustamos las posiciones según tu descripción:
        # Abajo-Izq y Arriba-Der -> NORTE/SUR
        # Arriba-Izq y Abajo-Der -> ESTE/OESTE
        config_semaforos = {
            "NORTE": {"pos": (c + offset_calle, c - offset_calle), "orientacion": "V"}, # Arriba-Derecha
            "SUR":   {"pos": (c - offset_calle, c + offset_calle), "orientacion": "V"}, # Abajo-Izquierda
            "ESTE":  {"pos": (c + offset_calle, c + offset_calle), "orientacion": "H"}, # Abajo-Derecha
            "OESTE": {"pos": (c - offset_calle, c - offset_calle), "orientacion": "H"}  # Arriba-Izquierda
        }

        for via, datos in config_semaforos.items():
            cx, cy = datos["pos"]

            # Definir forma según orientación
            if datos["orientacion"] == "H":
                # Semáforo Horizontal (para detener tráfico vertical)
                x1, y1 = cx - 15, cy - 6
                x2, y2 = cx + 15, cy + 6
                # Poste (pequeña línea hacia afuera para decoracion)
                self.canvas.create_line(cx, cy, cx + 20, cy, width=2, fill="#7f8c8d")
            else:
                # Semáforo Vertical (para detener tráfico horizontal)
                x1, y1 = cx - 6, cy - 15
                x2, y2 = cx + 6, cy + 15
                # Poste
                self.canvas.create_line(cx, cy, cx, cy - 20, width=2, fill="#7f8c8d")

            # 1. Caja del semáforo (Negra)
            self.canvas.create_rectangle(x1, y1, x2, y2, fill="black", outline="gray")

            # 2. Luz (Círculo)
            # Ajustamos el tamaño de la luz para que quepa en el rectángulo
            self.luces_gui[via] = self.canvas.create_oval(
                cx - 5, cy - 5, cx + 5, cy + 5,
                fill="grey", outline=""
            )

            # 3. Etiqueta pequeña (Opcional, ayuda mucho a depurar)
            # self.canvas.create_text(cx, cy-20, text=via[0], fill="white", font=("Arial", 8, "bold"))

    def dibujar_auto_detallado(self, x, y, direccion, color_base, frenado=False):
        w, h = 24, 40
        coords_cuerpo, luces = [], []
        if direccion == "NORTE":
            coords_cuerpo = [x-w/2, y, x+w/2, y+h]
            if frenado:
                luces = [(x-w/2+2, y, "red"), (x+w/2-4, y, "red")]
        elif direccion == "SUR":
            coords_cuerpo = [x-w/2, y-h, x+w/2, y]
            if frenado:
                luces = [(x-w/2+2, y-2, "red"), (x+w/2-4, y-2, "red")]
        elif direccion == "ESTE":
            coords_cuerpo = [x-h, y-w/2, x, y+w/2]
            if frenado:
                luces = [(x-2, y-w/2+2, "red"), (x-2, y+w/2-4, "red")]
        elif direccion == "OESTE":
            coords_cuerpo = [x, y-w/2, x+h, y+w/2]
            if frenado:
                luces = [(x+2, y-w/2+2, "red"), (x+2, y+w/2-4, "red")]

        self.canvas.create_rectangle(
            *coords_cuerpo, fill=color_base, outline="black", tags="movil")
        for lx, ly, lcolor in luces:
            self.canvas.create_oval(
                lx, ly, lx+4, ly+4, fill=lcolor, outline=lcolor, tags="movil")

    def gestionar_colas_visuales(self, via, idx_via, cantidad, estado_luz):
        if cantidad < self.prev_tam_colas[idx_via] and estado_luz != ROJO:
            self.iniciar_animacion_cruce(via)
        self.prev_tam_colas[idx_via] = cantidad

        c = CENTRO
        m = ANCHO_CALLE // 4
        sep = 50
        colores = ["#e74c3c", "#f1c40f", "#9b59b6", "#1abc9c", "#ecf0f1"]
        frenando = (estado_luz == ROJO)

        for i in range(cantidad):
            if i > 6:
                break
            dist = (ANCHO_CALLE//2) + 20 + (i * sep)
            color = colores[i % 5]
            x, y = c, c
            if via == "NORTE":
                x, y = c - m - 10, c - dist
            elif via == "SUR":
                x, y = c + m - 10, c + dist
            elif via == "ESTE":
                x, y = c + dist, c - m - 10
            elif via == "OESTE":
                x, y = c - dist, c + m - 10
            self.dibujar_auto_detallado(x, y, via, color, frenado=frenando)

    def iniciar_animacion_cruce(self, via):
        c = CENTRO
        m = ANCHO_CALLE // 4
        x, y, dx, dy = 0, 0, 0, 0
        velocidad = 20  # Más rápido
        if via == "NORTE":
            x, y, dy = c - m - 10, c - 80, velocidad
        elif via == "SUR":
            x, y, dy = c + m - 10, c + 80, -velocidad
        elif via == "ESTE":
            x, y, dx = c + 80, c - m - 10, -velocidad
        elif via == "OESTE":
            x, y, dx = c - 80, c + m - 10, velocidad
        self.animaciones_activas.append(
            {"via": via, "x": x, "y": y, "dx": dx, "dy": dy, "steps": 15, "color": "#2ecc71"})

    def procesar_animaciones(self):
        nuevas = []
        for anim in self.animaciones_activas:
            anim["x"] += anim["dx"]
            anim["y"] += anim["dy"]
            anim["steps"] -= 1
            self.dibujar_auto_detallado(
                anim["x"], anim["y"], anim["via"], anim["color"], False)
            if anim["steps"] > 0:
                nuevas.append(anim)
        self.animaciones_activas = nuevas
