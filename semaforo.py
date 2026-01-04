import multiprocessing
import threading
import time
import queue
import random
from vehiculo import Vehiculo
from utils import print_safe
from config import ROJO, AMARILLO, VERDE, TIEMPO_CRUCE, CRUCE_AMARILLO


class SemaforoProcesos(multiprocessing.Process):

    def __init__(self,
                 id: int,
                 via: str,
                 vehiculos: multiprocessing.Queue,
                 estado: multiprocessing.Value,
                 lock_print: multiprocessing.Lock,
                 semaforo: multiprocessing.Semaphore,
                 evento_fin: multiprocessing.Event
                 ):
        super().__init__()
        self.id = id
        self.via = via
        self.vehiculos = vehiculos
        self.estado = estado
        self.lock_print = lock_print
        self.semaforo = semaforo
        self.evento_fin = evento_fin
        self.pendiente: Vehiculo = None # buffer para guardar si un auto decidio esperar en amarillo

    def run(self) -> None:
        print_safe(self.lock_print, f"Semáforo {self.via} Iniciado")

        # El bucle se rompe cuando el Controlador activa el evento
        while not self.evento_fin.is_set():

            if self.estado.value == ROJO:
                time.sleep(0.1)
                continue

            try:
                if self.pendiente:
                    vehiculo: Vehiculo = self.pendiente
                    self.pendiente = None
                else:
                    vehiculo: Vehiculo = self.vehiculos.get_nowait()

                estado = self.estado

                # semaforo en amarillo
                if self.estado.value == AMARILLO:
                    decision = random.random()
                    if decision > CRUCE_AMARILLO:
                        print_safe(self.lock_print, f"Auto #{vehiculo.id} ({self.via}) frena en amarillo")
                        self.pendiente = vehiculo
                        time.sleep(0.5)
                        continue
                    else:
                        print_safe(self.lock_print, f"Auto #{vehiculo.id} ({self.via}) cruza en amarillo")

                # semaforo en verde
                self.semaforo.acquire()
                try:
                    time.sleep(TIEMPO_CRUCE)
                    espera = vehiculo.calcular_espera()
                    print_safe(
                        self.lock_print,
                        f"Auto #{vehiculo.id} ({self.via}) CRUZÓ. Espera: {espera:.1f}s"
                    )
                finally:
                    self.semaforo.release()

            except queue.Empty:
                time.sleep(0.1)
            except Exception as e:
                print_safe(self.lock_print, f"ERROR en {self.via}: {e}")

        # Mensaje de despedida cuando el bucle termina
        print_safe(self.lock_print, f"Semáforo {self.via} CERRANDO...")


#class Semaforo_Hilos(threading.Thread):
