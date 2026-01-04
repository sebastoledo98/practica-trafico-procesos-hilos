from typing import Final, List

ROJO: Final[int] = 0
VERDE: Final[int] = 1
AMARILLO: Final[int] = 2

VIAS: Final[List[str]] = ["NORTE", "SUR", "ESTE", "OESTE"] # nombres de las vias

TIEMPO_CRUCE: Final[float] = 1.0 # tiempo que tarda un auto en cruzar
TIEMPO_VERDE: Final[float] = 5.0 # tiempo que dura una luz en verde
TIEMPO_AMARILLO: Final[float] = 2.0 # tiempo que dura una luz en amarillo
TIEMPO_ROJO: Final[float] = 0.5 # tiempo en el que todos los semaforos se mantienen en rojo

CRUCE_AMARILLO: Final[float] = 0.4 # probabilidad de que el conductor cruce en amarillo
CANTIDAD_CICLOS: Final[int] = 10 # cantidad de ciclos (norte/sur, este/oeste) a simular
