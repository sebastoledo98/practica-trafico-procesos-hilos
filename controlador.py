import multiprocessing
import time
from typing import List

from config import VIAS, AMARILLO, ROJO, VERDE, TIEMPO_VERDE, TIEMPO_AMARILLO, TIEMPO_ROJO, CANTIDAD_CICLOS
from utils import print_safe
from semaforo import SemaforoProcesos
from trafico import GeneradorTrafico

class ControladorTrafico:
    def __init__(self):
        self.lock_print = multiprocessing.Lock()
        self.semaforo = multiprocessing.Semaphore(1)

        self.evento_fin = multiprocessing.Event()

        self.colas = [multiprocessing.Queue() for _ in range(4)]
        self.estados_luz = [multiprocessing.Value('i', ROJO) for _ in range(4)]

        self.procesos_semaforos: List[SemaforoProcesos] = []

        # Pasamos evento_fin a los Semáforos
        for i in range(4):
            s = SemaforoProcesos(
                id=i,
                via=VIAS[i],
                vehiculos=self.colas[i],
                estado=self.estados_luz[i],
                lock_print=self.lock_print,
                semaforo=self.semaforo,
                evento_fin=self.evento_fin # <--- Pasa el evento
            )
            self.procesos_semaforos.append(s)

        # Pasamos evento_fin al Generador
        self.generador = GeneradorTrafico(
            self.colas,
            self.lock_print,
            self.evento_fin # <--- Pasa el evento
        )

    def iniciar(self) -> None:
        print("--- INICIANDO SIMULACIÓN DE TRÁFICO ---")
        print("--- (Ctrl + C para detener ordenadamente) ---")

        for s in self.procesos_semaforos:
            s.start()
        self.generador.start()

        try:
            for i in range(CANTIDAD_CICLOS):
                if self.evento_fin.is_set(): break
                print_safe(self.lock_print, f"\n === INICIANDO CICLO {i+1}/{CANTIDAD_CICLOS} ===")
                self._cambiar_fase(norte_sur=True)
                self._cambiar_fase(norte_sur=False)
            print_safe(self.lock_print, f"\n === FINALIZANDO CICLOS ===")
        except KeyboardInterrupt:
            print("\n--- SEÑAL DE PARADA RECIBIDA ---")
        finally:
            self._limpiar()

    def _cambiar_fase(self, norte_sur: bool) -> None:
        # Verificamos si pidieron salir antes de iniciar una espera larga
        if self.evento_fin.is_set(): return

        indices = [0, 1] if norte_sur else [2, 3]
        etiqueta = "NORTE/SUR" if norte_sur else "ESTE/OESTE"

        print_safe(self.lock_print, f">>> [CONTROL] FASE {etiqueta} VERDE")
        for i in indices: self.estados_luz[i].value = VERDE
        self._esperar(TIEMPO_VERDE)

        print_safe(self.lock_print, f">>> [CONTROL] FASE {etiqueta} AMARILLO")
        for i in indices: self.estados_luz[i].value = AMARILLO
        self._esperar(TIEMPO_AMARILLO)

        print_safe(self.lock_print, f">>> [CONTROL] FASE {etiqueta} ROJO")
        for i in indices: self.estados_luz[i].value = ROJO
        self._esperar(TIEMPO_ROJO)


    def _esperar(self, segundos: float) -> None:
        inicio = time.time()
        print(f"DEBUG: Esperando {segundos}s")
        while (time.time() - inicio) < segundos:
            if self.evento_fin.is_set(): return
            time.sleep(0.1)

    def _limpiar(self) -> None:
        print("Enviando señal de parada a procesos hijos...")
        self.evento_fin.set() # 1. Activa la bandera

        print("Esperando a que los procesos terminen sus tareas pendientes...")
        # 2. Espera (Join) a que cada proceso termine su bucle y se cierre
        self.generador.join()
        for s in self.procesos_semaforos:
            s.join()

        print("Todos los procesos cerrados. Sistema apagado.")
