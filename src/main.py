"""
Punto de entrada del juego.

Solo inicializa Pygame y corre el loop principal; todo el estado y el flujo
de pantallas (Menú -> Principal -> Árbol / Mapa, Pausa, Fin) vive en
`juego.Juego`, y el aspecto visual en `ui/`.

La ventana es de 1280x720 con `pygame.SCALED`: Pygame la escala sola si la
pantalla es más chica y traduce las coordenadas del mouse, así que el resto
del código siempre trabaja en 1280x720.
"""

import pygame

from ajustes import Ajustes
from juego import Juego, crear_fuentes
from ui.tema import ANCHO, ALTO

FPS = 60


def main():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO), pygame.SCALED | pygame.RESIZABLE)
    pygame.display.set_caption("Social Network Builder")
    reloj = pygame.time.Clock()

    juego = Juego(pantalla, crear_fuentes(), Ajustes())  # Ajustes recuerda la paleta elegida

    while juego.corriendo:
        dt = reloj.tick(FPS) / 1000.0

        for evento in pygame.event.get():
            juego.manejar_evento(evento)

        juego.actualizar(dt)
        juego.dibujar()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
