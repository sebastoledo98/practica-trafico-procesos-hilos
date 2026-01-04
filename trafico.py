import multiprocessing
import time
import random
from config import VIAS
from vehiculo import Vehiculo
from utils import print_safe


class GeneradorTrafico(multiprocessing.Process):
    def __init__(
        self,
        colas: list[multiprocessing.Queue],
        lock_print: multiprocessing.Lock,
        evento_fin: multiprocessing.Event
    ):
        super().__init__()
        self.colas = colas
        self.lock_print = lock_print
        self.evento_fin = evento_fin

    def run(self) -> None:
        contador = 0
        while not self.evento_fin.is_set():
            time.sleep(random.uniform(0.5, 2.0))

            idx = random.randint(0, 3)
            contador += 1

            nuevo_vehiculo = Vehiculo(contador, VIAS[idx])
            self.colas[idx].put(nuevo_vehiculo)

            try:
                tam = self.colas[idx].qsize()
            except NotImplementedError:
                tam = "?"

            print_safe(
                self.lock_print,
                f"Nuevo auto en {VIAS[idx]} (En espera: {tam})"
            )

        print_safe(self.lock_print, "Generador de tráfico DETENIDO.")
