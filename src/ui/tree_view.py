"""
Dibujo muy preliminar del árbol sobre una superficie de Pygame.

Esto es un punto de partida: coordenadas fijas, sin estética final ni arte
propio todavía. Sirve para verificar visualmente el comportamiento del árbol
mientras se desarrolla la lógica (requisito de la primera entrega: interfaz
gráfica funcional, aunque sea preliminar).
"""

import pygame

COLOR_BLOQUEADO = (90, 90, 90)
COLOR_FIJO = (60, 150, 130)
COLOR_INTERACTIVO = (200, 90, 70)
COLOR_TEXTO = (255, 255, 255)

# Posiciones fijas por id de nodo, siguiendo el layout de 3 columnas
# (Feed / Comunidad / Seguridad) definido en el documento de diseño.
POSICIONES = {
    "red_social": (270, 20, 160, 40),
    "feed": (80, 90, 160, 40),
    "comunidad": (270, 90, 160, 40),
    "seguridad": (460, 90, 160, 40),
    "feed_basico": (80, 160, 160, 50),
    "comunidad_grupos": (270, 160, 160, 50),
    "seguridad_basica": (460, 160, 160, 50),
    "feed_scroll": (80, 230, 160, 50),
    "comunidad_mensajes": (270, 230, 160, 50),
    "seguridad_avanzada": (460, 230, 160, 50),
    "feed_algoritmo": (80, 300, 160, 50),
    "comunidad_verificacion": (270, 300, 160, 50),
}


def dibujar_arbol(pantalla, arbol, fuente):
    for nodo in arbol.recorrido_bfs():
        posicion = POSICIONES.get(nodo.id)
        if posicion is None:
            continue
        x, y, ancho, alto = posicion

        if not nodo.desbloqueado:
            color = COLOR_BLOQUEADO
        elif nodo.tipo_control == "fijo":
            color = COLOR_FIJO
        else:
            color = COLOR_INTERACTIVO

        rect = pygame.Rect(x, y, ancho, alto)
        pygame.draw.rect(pantalla, color, rect, border_radius=8)

        texto = fuente.render(nodo.nombre, True, COLOR_TEXTO)
        texto_rect = texto.get_rect(center=rect.center)
        pantalla.blit(texto, texto_rect)


def nodo_en_posicion(arbol, pos_click):
    """Devuelve el nodo cuyo rectángulo contiene pos_click, o None."""
    for nodo in arbol.recorrido_bfs():
        posicion = POSICIONES.get(nodo.id)
        if posicion is None:
            continue
        x, y, ancho, alto = posicion
        rect = pygame.Rect(x, y, ancho, alto)
        if rect.collidepoint(pos_click):
            return nodo
    return None
