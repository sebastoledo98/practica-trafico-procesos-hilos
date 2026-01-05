import time


class Vehiculo:

    id: int
    via: str
    hora_llegada: float

    def __init__(self, id, via):
        self.id = id
        self.via = via
        self.hora_llegada = time.time()

    def calcular_espera(self) -> float:
        return time.time() - self.hora_llegada
