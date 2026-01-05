import multiprocessing
import threading
import queue
import time
from config import VIAS, AMARILLO, ROJO, VERDE, TIEMPO_VERDE, TIEMPO_AMARILLO, TIEMPO_ROJO, CANTIDAD_CICLOS
from utils import print_safe
from semaforo import SemaforoProcesos, SemaforoHilos
from trafico import GeneradorTrafico

class ControladorTrafico:
    def __init__(self, modo="PROCESO"):
        self.modo = modo
        
        if self.modo == "PROCESO":
            self.lock_print = multiprocessing.Lock()
            self.semaforo_cruce = multiprocessing.Semaphore(1)
            self.evento_fin = multiprocessing.Event()
            self.colas = [multiprocessing.Queue() for _ in range(4)]
            self.estados_luz = [multiprocessing.Value('i', ROJO) for _ in range(4)]
        else: # MODO HILO
            self.lock_print = threading.Lock()
            self.semaforo_cruce = threading.Lock()
            self.evento_fin = threading.Event()
            self.colas = [queue.Queue() for _ in range(4)]
            class EstadoCompartido:
                def __init__(self): self.value = ROJO
            self.estados_luz = [EstadoCompartido() for _ in range(4)]

        self.procesos_semaforos = []
        for i in range(4):
            if self.modo == "PROCESO":
                s = SemaforoProcesos(i, VIAS[i], self.colas[i], self.estados_luz[i], 
                                     self.lock_print, self.semaforo_cruce, self.evento_fin)
            else:
                s = SemaforoHilos(i, VIAS[i], self.colas[i], self.estados_luz[i], 
                                  self.lock_print, self.semaforo_cruce, self.evento_fin)
            self.procesos_semaforos.append(s)

        if self.modo == "PROCESO":
            self.generador = GeneradorTrafico(self.colas, self.lock_print, self.evento_fin)
        else:
            self.generador = threading.Thread(target=self._generador_hilos_wrapper)

    def _generador_hilos_wrapper(self):
        from vehiculo import Vehiculo
        import random
        contador = 0
        while not self.evento_fin.is_set():
            time.sleep(random.uniform(0.5, 2.0))
            idx = random.randint(0, 3)
            contador += 1
            nuevo = Vehiculo(contador, VIAS[idx])
            self.colas[idx].put(nuevo)
            print_safe(self.lock_print, f"Nuevo auto (HILO) en {VIAS[idx]}")

    def iniciar(self) -> None:
        print(f"--- INICIANDO SIMULACIÓN ({self.modo}) ---")
        for s in self.procesos_semaforos: s.start()
        self.generador.start()

        try:
            for i in range(CANTIDAD_CICLOS):
                if self.evento_fin.is_set(): break
                print_safe(self.lock_print, f"\n === CICLO {i+1}/{CANTIDAD_CICLOS} ===")
                self._cambiar_fase(norte_sur=True)
                self._cambiar_fase(norte_sur=False)
            print_safe(self.lock_print, f"\n === FIN DE CICLOS ===")
        except KeyboardInterrupt:
            print("\n--- STOP ---")
        finally:
            self._limpiar()

    def _cambiar_fase(self, norte_sur: bool) -> None:
        if self.evento_fin.is_set(): return
        indices = [0, 1] if norte_sur else [2, 3]
        for i in indices: self.estados_luz[i].value = VERDE
        self._esperar(TIEMPO_VERDE)
        for i in indices: self.estados_luz[i].value = AMARILLO
        self._esperar(TIEMPO_AMARILLO)
        for i in indices: self.estados_luz[i].value = ROJO
        self._esperar(TIEMPO_ROJO)

    def _esperar(self, segundos):
        inicio = time.time()
        while (time.time() - inicio) < segundos:
            if self.evento_fin.is_set(): return
            time.sleep(0.1)

    def _limpiar(self):
        self.evento_fin.set()
        self.generador.join()
        for s in self.procesos_semaforos: s.join()