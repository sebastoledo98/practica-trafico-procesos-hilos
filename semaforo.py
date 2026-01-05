import multiprocessing
import threading
import time
import queue
import random
from vehiculo import Vehiculo
from utils import print_safe
from config import ROJO, AMARILLO, VERDE, TIEMPO_CRUCE, CRUCE_AMARILLO

class SemaforoProcesos(multiprocessing.Process):
    def __init__(self, id, via, vehiculos, estado, lock_print, semaforo, evento_fin):
        super().__init__()
        self.id = id
        self.via = via
        self.vehiculos = vehiculos
        self.estado = estado
        self.lock_print = lock_print
        self.semaforo = semaforo
        self.evento_fin = evento_fin
        self.pendiente = None

    def run(self) -> None:
        print_safe(self.lock_print, f"[PROCESO] Semáforo {self.via} Iniciado")
        while not self.evento_fin.is_set():
            if self.estado.value == ROJO:
                time.sleep(0.1)
                continue

            try:
                vehiculo = self.pendiente if self.pendiente else self.vehiculos.get_nowait()
                self.pendiente = None
                
                # Lógica Amarillo
                if self.estado.value == AMARILLO:
                    if random.random() > CRUCE_AMARILLO:
                        print_safe(self.lock_print, f"Auto #{vehiculo.id} ({self.via}) frena en amarillo")
                        self.pendiente = vehiculo
                        time.sleep(0.5)
                        continue
                    else:
                        print_safe(self.lock_print, f"Auto #{vehiculo.id} ({self.via}) cruza en amarillo")

                # Cruce (Zona Crítica)
                self.semaforo.acquire()
                try:
                    time.sleep(TIEMPO_CRUCE)
                    espera = vehiculo.calcular_espera()
                    print_safe(self.lock_print, f"Auto #{vehiculo.id} ({self.via}) CRUZÓ. Espera: {espera:.1f}s")
                finally:
                    self.semaforo.release()

            except queue.Empty:
                time.sleep(0.1)
            except Exception as e:
                print_safe(self.lock_print, f"ERROR en {self.via}: {e}")

class SemaforoHilos(threading.Thread):
    def __init__(self, id, via, vehiculos, estado, lock_print, semaforo_cruce, evento_fin):
        super().__init__()
        self.id = id
        self.via = via
        self.vehiculos = vehiculos
        self.estado = estado
        self.lock_print = lock_print
        self.semaforo_cruce = semaforo_cruce # Lock obligatorio para hilos
        self.evento_fin = evento_fin
        self.pendiente = None

    def run(self) -> None:
        print_safe(self.lock_print, f"[HILO] Semáforo {self.via} Iniciado")
        while not self.evento_fin.is_set():
            estado_actual = self.estado.value 
            if estado_actual == ROJO:
                time.sleep(0.1)
                continue

            try:
                vehiculo = self.pendiente if self.pendiente else self.vehiculos.get_nowait()
                self.pendiente = None

                if estado_actual == AMARILLO:
                    if random.random() > CRUCE_AMARILLO:
                        print_safe(self.lock_print, f"[HILO] Auto #{vehiculo.id} ({self.via}) frena amarillo")
                        self.pendiente = vehiculo
                        time.sleep(0.5)
                        continue

                # ZONA CRÍTICA con LOCK
                with self.semaforo_cruce: 
                    time.sleep(TIEMPO_CRUCE)
                    espera = vehiculo.calcular_espera()
                    print_safe(self.lock_print, f"[HILO] Auto #{vehiculo.id} ({self.via}) CRUZÓ. T: {espera:.1f}s")

            except queue.Empty:
                time.sleep(0.1)
            except Exception as e:
                print_safe(self.lock_print, f"Error Hilo {self.via}: {e}")