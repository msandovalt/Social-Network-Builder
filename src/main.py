"""
Punto de entrada del juego.

Por ahora solo muestra el árbol de funcionalidades y permite desbloquear
nodos haciendo clic, para cumplir con el alcance de la primera entrega
(árbol + interfaz gráfica funcional, aunque preliminar). El sistema de
eventos, el minijuego de habilidad y el grafo de expansión se agregan
en entregas posteriores, según lo definido en el documento de diseño.
"""

import pygame

from tree.arbol import Arbol
from tree.recursos import Recursos
from ui.tree_view import dibujar_arbol, nodo_en_posicion

ANCHO, ALTO = 700, 420
FPS = 60


def main():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Social Network Builder - Árbol (preliminar)")
    reloj = pygame.time.Clock()
    fuente = pygame.font.SysFont(None, 20)

    arbol = Arbol.construir_arbol_inicial()
    recursos = Recursos()

    corriendo = True
    while corriendo:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                corriendo = False
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                nodo = nodo_en_posicion(arbol, evento.pos)
                if nodo:
                    nodo.desbloquear(recursos)

        pantalla.fill((25, 25, 30))
        dibujar_arbol(pantalla, arbol, fuente)

        panel = fuente.render(
            f"Dinero: {recursos.dinero}   Usuarios: {recursos.usuarios}   "
            f"Bienestar: {recursos.bienestar}   Reputación: {recursos.reputacion}",
            True, (255, 255, 255),
        )
        pantalla.blit(panel, (20, ALTO - 30))

        pygame.display.flip()
        reloj.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
