"""
Dibujo muy preliminar del árbol sobre una superficie de Pygame.

Esto es un punto de partida: coordenadas fijas, sin estética final ni arte
propio todavía. Sirve para verificar visualmente el comportamiento del árbol
mientras se desarrolla la lógica (requisito de la primera entrega: interfaz
gráfica funcional, aunque sea preliminar).

Diseño de posiciones: los 3 hijos de cada rama (Feed / Comunidad / Seguridad)
salen directo de esa rama, nunca uno del otro. Dos de ellos van lado a lado
justo debajo de la rama, y el tercero (el de nombre más largo) va centrado
una fila más abajo, exactamente en el hueco entre los otros dos — así la
línea que baja desde la rama pasa limpia por el medio en vez de parecer que
sale de alguno de sus "hermanos".
"""

import pygame

COLOR_BLOQUEADO = (90, 90, 90)
COLOR_FIJO = (60, 150, 130)
COLOR_INTERACTIVO = (200, 90, 70)
COLOR_TEXTO = (255, 255, 255)

# Etiquetas cortas SOLO para el texto dentro de la caja (por espacio).
# El nombre completo (nodo.nombre) se sigue usando en el panel de detalle.
ETIQUETAS_CORTAS = {
    "feed_scroll": "Scroll",
    "comunidad_verificacion": "Verif. paga",
}

POSICIONES = {
    "red_social": (350, 20, 160, 44),

    "feed": (90, 90, 160, 44),
    "comunidad": (350, 90, 160, 44),
    "seguridad": (610, 90, 160, 44),

    # Feed (hijos directos de "feed", no encadenados entre sí)
    "feed_basico": (70, 170, 90, 50),
    "feed_scroll": (180, 170, 90, 50),
    "feed_algoritmo": (95, 240, 150, 50),

    # Comunidad (hijos directos de "comunidad")
    "comunidad_grupos": (330, 170, 90, 50),
    "comunidad_mensajes": (440, 170, 90, 50),
    "comunidad_verificacion": (355, 240, 150, 50),

    # Seguridad (hijos directos de "seguridad", solo 2, caben en una fila)
    "seguridad_basica": (590, 170, 90, 50),
    "seguridad_avanzada": (700, 170, 90, 50),
}


def dibujar_conexiones(pantalla, arbol):
    """Dibuja una línea de cada nodo hacia su padre real (según el árbol de
    datos, no según la posición en pantalla), para que se lea como un árbol
    genuino y no sugiera dependencias que no existen."""
    color = (95, 95, 105)
    for nodo in arbol.recorrido_bfs():
        if nodo.padre is None:
            continue
        pos_padre = POSICIONES.get(nodo.padre.id)
        pos_hijo = POSICIONES.get(nodo.id)
        if pos_padre is None or pos_hijo is None:
            continue
        xp, yp, wp, hp = pos_padre
        xh, yh, wh, hh = pos_hijo
        inicio = (xp + wp // 2, yp + hp)
        fin = (xh + wh // 2, yh)
        pygame.draw.line(pantalla, color, inicio, fin, 2)


def dibujar_arbol(pantalla, arbol, fuente):
    dibujar_conexiones(pantalla, arbol)
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

        texto_mostrar = ETIQUETAS_CORTAS.get(nodo.id, nodo.nombre)
        texto = fuente.render(texto_mostrar, True, COLOR_TEXTO)
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
