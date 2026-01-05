import multiprocessing
import time
import random
from config import VIAS
from vehiculo import Vehiculo
from utils import print_safe

class GeneradorTrafico(multiprocessing.Process):
    def __init__(self, colas, lock_print, evento_fin):
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
            nuevo = Vehiculo(contador, VIAS[idx])
            
            # Put es seguro tanto en Queue (hilos) como mp.Queue (procesos)
            self.colas[idx].put(nuevo)

            try:
                tam = self.colas[idx].qsize()
            except NotImplementedError:
                tam = "?"
            
            print_safe(self.lock_print, f"Nuevo auto en {VIAS[idx]} (En espera: {tam})")