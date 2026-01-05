import tkinter as tk
import random
import time
from config import VIAS, ROJO, VERDE, AMARILLO

# Colores y Medidas
C_PASTO = "#2ecc71"
C_ASFALTO = "#34495e"
C_CALLE_BORDE = "#2c3e50"
C_TECHO = ["#e74c3c", "#e67e22", "#8e44ad", "#d35400"] # Variedad para casas
ANCHO_CALLE = 140
CENTRO = 300

class InterfazTrafico:
    def __init__(self, root, controlador):
        self.root = root
        self.controlador = controlador
        self.root.title("Simulación de Tráfico - UPS (Gráficos Vectoriales)")
        
        self.canvas = tk.Canvas(root, width=600, height=600, bg=C_PASTO)
        self.canvas.pack()

        # Para detectar cambios en la cola y animar el cruce
        self.prev_tam_colas = [0, 0, 0, 0] 
        self.animaciones_activas = [] # Lista de autos cruzando visualmente

        # 1. Dibujar el escenario estático (Casas y calles)
        self.dibujar_barrio()
        self.dibujar_calles()
        
        # 2. Inicializar semáforos
        self.luces_gui = {}
        self.crear_semaforos()

        # 3. Panel de Info
        self.rect_info = self.canvas.create_rectangle(10, 10, 250, 70, fill="black", stipple="gray50")
        self.stats_text = self.canvas.create_text(
            20, 20, anchor="nw", text="Cargando simulación...", fill="white", font=("Consolas", 10)
        )

        self.actualizar_vista()

    def dibujar_barrio(self):
        """Dibuja casas decorativas en las 4 esquinas"""
        # Coordenadas de las 4 esquinas (evitando el centro donde van las calles)
        zonas = [
            (0, 0, CENTRO-ANCHO_CALLE//2, CENTRO-ANCHO_CALLE//2), # Noroeste
            (CENTRO+ANCHO_CALLE//2, 0, 600, CENTRO-ANCHO_CALLE//2), # Noreste
            (0, CENTRO+ANCHO_CALLE//2, CENTRO-ANCHO_CALLE//2, 600), # Suroeste
            (CENTRO+ANCHO_CALLE//2, CENTRO+ANCHO_CALLE//2, 600, 600) # Sureste
        ]
        
        for x1, y1, x2, y2 in zonas:
            # Dibujar 3 casitas por zona
            for _ in range(3):
                cx = random.randint(int(x1)+20, int(x2)-40)
                cy = random.randint(int(y1)+20, int(y2)-40)
                tam = 30
                color_techo = random.choice(C_TECHO)
                
                # Pared
                self.canvas.create_rectangle(cx, cy, cx+tam, cy+tam, fill="#ecf0f1", outline="#bdc3c7")
                # Techo (triángulo)
                self.canvas.create_polygon(cx-5, cy, cx+tam+5, cy, cx+tam/2, cy-15, fill=color_techo, outline="black")
                # Puerta
                self.canvas.create_rectangle(cx+10, cy+15, cx+20, cy+tam, fill="#7f8c8d")

    def dibujar_calles(self):
        c = CENTRO
        m = ANCHO_CALLE // 2
        
        # Bordes de calle
        self.canvas.create_rectangle(c-m-5, 0, c+m+5, 600, fill=C_CALLE_BORDE, outline="")
        self.canvas.create_rectangle(0, c-m-5, 600, c+m+5, fill=C_CALLE_BORDE, outline="")
        
        # Asfalto
        self.canvas.create_rectangle(c-m, 0, c+m, 600, fill=C_ASFALTO, outline="")
        self.canvas.create_rectangle(0, c-m, 600, c+m, fill=C_ASFALTO, outline="")

        # Líneas amarillas centrales
        for i in range(0, 600, 40):
            if not (c-m < i < c+m): # Evitar cruce
                self.canvas.create_line(c, i, c, i+20, fill="#f1c40f", width=2)
                self.canvas.create_line(i, c, i+20, c, fill="#f1c40f", width=2)
                
        # Líneas de PARE (Blancas gruesas)
        self.canvas.create_line(c, c-m, c+m, c-m, fill="white", width=4) # N
        self.canvas.create_line(c-m, c+m, c, c+m, fill="white", width=4) # S
        self.canvas.create_line(c+m, c, c+m, c+m, fill="white", width=4) # E
        self.canvas.create_line(c-m, c-m, c-m, c, fill="white", width=4) # O

    def crear_semaforos(self):
        offset = ANCHO_CALLE // 2 + 30
        c = CENTRO
        posiciones = {
            "NORTE": (c + offset, c - offset),
            "SUR":   (c - offset, c + offset),
            "ESTE":  (c + offset, c + offset),
            "OESTE": (c - offset, c - offset)
        }
        for via, (x, y) in posiciones.items():
            # Poste
            self.canvas.create_line(x, y, x, y+20 if via in ["NORTE","ESTE"] else y-20, width=3)
            # Caja
            self.canvas.create_rectangle(x-10, y-10, x+10, y+10, fill="black")
            # Luz
            self.luces_gui[via] = self.canvas.create_oval(x-7, y-7, x+7, y+7, fill="grey")

    def dibujar_auto_detallado(self, x, y, direccion, color_base, frenado=False):
        """Dibuja un auto con parabrisas y luces"""
        w, h = 24, 40 # Dimensiones base (ancho, largo)
        
        # Coordenadas relativas para rotación manual simple
        # Cuerpo, Parabrisas, Luces Freno
        coords_cuerpo = []
        coords_vidrio = []
        luces = []

        if direccion == "NORTE": # Apunta abajo (hacia el cruce)
            coords_cuerpo = [x-w/2, y, x+w/2, y+h]
            coords_vidrio = [x-w/2+2, y+h-15, x+w/2-2, y+h-5] # Vidrio adelante
            if frenado: luces = [(x-w/2+2, y, "red"), (x+w/2-4, y, "red")] # Luces atrás (arriba)
            
        elif direccion == "SUR": # Apunta arriba
            coords_cuerpo = [x-w/2, y-h, x+w/2, y]
            coords_vidrio = [x-w/2+2, y-h+5, x+w/2-2, y-h+15]
            if frenado: luces = [(x-w/2+2, y-2, "red"), (x+w/2-4, y-2, "red")]
            
        elif direccion == "ESTE": # Apunta izquierda
            coords_cuerpo = [x-h, y-w/2, x, y+w/2] # Invertimos w y h
            coords_vidrio = [x-h+5, y-w/2+2, x-h+15, y+w/2-2]
            if frenado: luces = [(x-2, y-w/2+2, "red"), (x-2, y+w/2-4, "red")]
            
        elif direccion == "OESTE": # Apunta derecha
            coords_cuerpo = [x, y-w/2, x+h, y+w/2]
            coords_vidrio = [x+h-15, y-w/2+2, x+h-5, y+w/2-2]
            if frenado: luces = [(x+2, y-w/2+2, "red"), (x+2, y+w/2-4, "red")]

        # Dibujar chasis
        self.canvas.create_rectangle(*coords_cuerpo, fill=color_base, outline="black", tags="movil")
        # Dibujar parabrisas (simula dirección)
        self.canvas.create_rectangle(*coords_vidrio, fill="#3498db", outline="black", tags="movil")
        
        # Dibujar luces de freno si corresponde
        for lx, ly, lcolor in luces:
            self.canvas.create_oval(lx, ly, lx+4, ly+4, fill=lcolor, outline=lcolor, tags="movil")

    def gestionar_colas_visuales(self, via, idx_via, cantidad, estado_luz):
        """Dibuja la cola estática y detecta si alguien cruzó para animarlo"""
        c = CENTRO
        m = ANCHO_CALLE // 4 # Carril
        sep = 50 # Separación entre autos
        
        # 1. Detectar si un auto salió de la cola (Cruce)
        # Si la cantidad actual es MENOR a la anterior y luz VERDE/AMARILLA
        if cantidad < self.prev_tam_colas[idx_via] and estado_luz != ROJO:
            self.iniciar_animacion_cruce(via)
        
        self.prev_tam_colas[idx_via] = cantidad # Actualizar memoria

        # 2. Dibujar autos en espera
        colores = ["#e74c3c", "#f1c40f", "#9b59b6", "#1abc9c", "#ecf0f1"]
        frenando = (estado_luz == ROJO)

        for i in range(cantidad):
            if i > 6: break # Límite visual
            dist = (ANCHO_CALLE//2) + 20 + (i * sep)
            color = colores[i % len(colores)]
            
            x, y = c, c
            if via == "NORTE": x, y = c - m - 10, c - dist
            elif via == "SUR": x, y = c + m - 10, c + dist
            elif via == "ESTE": x, y = c + dist, c - m - 10
            elif via == "OESTE": x, y = c - dist, c + m - 10
            
            self.dibujar_auto_detallado(x, y, via, color, frenado=frenando)

    def iniciar_animacion_cruce(self, via):
        """Crea un objeto de animación para que el auto cruce suavemente"""
        c = CENTRO
        m = ANCHO_CALLE // 4
        
        # Posición inicial (Línea de pare)
        x, y, dx, dy = 0, 0, 0, 0
        velocidad = 15 # Pixeles por frame
        
        if via == "NORTE": 
            x, y = c - m - 10, c - 80
            dx, dy = 0, velocidad
        elif via == "SUR": 
            x, y = c + m - 10, c + 80
            dx, dy = 0, -velocidad
        elif via == "ESTE": 
            x, y = c + 80, c - m - 10
            dx, dy = -velocidad, 0
        elif via == "OESTE": 
            x, y = c - 80, c + m - 10
            dx, dy = velocidad, 0
            
        anim_data = {
            "via": via, "x": x, "y": y, "dx": dx, "dy": dy, 
            "steps": 20, "color": "#2ecc71" # Verde brillante para el que cruza
        }
        self.animaciones_activas.append(anim_data)

    def procesar_animaciones(self):
        """Mueve los autos que están cruzando"""
        nuevas_animaciones = []
        for anim in self.animaciones_activas:
            anim["x"] += anim["dx"]
            anim["y"] += anim["dy"]
            anim["steps"] -= 1
            
            # Dibujar el auto en movimiento (Sin luces de freno, va acelerando)
            self.dibujar_auto_detallado(anim["x"], anim["y"], anim["via"], anim["color"], frenado=False)
            
            if anim["steps"] > 0:
                nuevas_animaciones.append(anim)
        
        self.animaciones_activas = nuevas_animaciones

    def actualizar_vista(self):
        self.canvas.delete("movil") # Borrar solo elementos móviles
        
        mapa_colores = {ROJO: "#c0392b", VERDE: "#2ecc71", AMARILLO: "#f1c40f"}
        txt_info = "ESTADO DEL TRÁFICO:\n"

        for i, via in enumerate(VIAS):
            # Estado Luz
            val = self.controlador.estados_luz[i].value
            self.canvas.itemconfig(self.luces_gui[via], fill=mapa_colores[val])
            
            # Cantidad cola
            try: cant = self.controlador.colas[i].qsize()
            except: cant = 0
            
            # Gestionar visualización (Estáticos y Trigger de animación)
            self.gestionar_colas_visuales(via, i, cant, val)
            
            txt_info += f"{via}: {cant} autos\n"

        # Procesar animaciones de cruce independientes
        self.procesar_animaciones()

        self.canvas.itemconfig(self.stats_text, text=txt_info)
        
        if not self.controlador.evento_fin.is_set():
            self.root.after(50, self.actualizar_vista)