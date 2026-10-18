"""
Dibujo del árbol de funcionalidades.

Diseño de posiciones: los 3 hijos de cada rama (Feed / Comunidad / Seguridad)
salen directo de esa rama, nunca uno del otro. Dos de ellos van lado a lado
justo debajo de la rama, y el tercero (el de nombre más largo) va centrado
una fila más abajo, exactamente en el hueco entre los otros dos: así la línea
que baja desde la rama pasa limpia por el medio en vez de parecer que sale de
alguno de sus "hermanos".

Qué se ve en cada nodo:
- color según el tipo (bloqueado / efecto fijo / interactivo);
- su costo si todavía no se compró (en rojo si no alcanza el dinero);
- su estado si es interactivo (ENCENDIDO/APAGADO, porcentaje del dial o la
  variante elegida);
- un aro amarillo pulsante si se puede comprar ahora, y un aro verde si es un
  interruptor encendido.
"""

import pygame

from ui import tema
from ui.animacion import pulso
from ui.formato import formato_numero

Y_LEYENDA = 624

POSICIONES = {
    "red_social": (510, 146, 260, 56),

    "feed": (136, 250, 240, 56),
    "comunidad": (520, 250, 240, 56),
    "seguridad": (904, 250, 240, 56),

    # Feed (hijos directos de "feed", no encadenados entre sí)
    "feed_basico": (76, 362, 170, 64),
    "feed_scroll": (266, 362, 170, 64),
    "feed_algoritmo": (141, 480, 230, 64),

    # Comunidad (hijos directos de "comunidad")
    "comunidad_grupos": (460, 362, 170, 64),
    "comunidad_mensajes": (650, 362, 170, 64),
    "comunidad_verificacion": (525, 480, 230, 64),

    # Seguridad (hijos directos de "seguridad", solo 2, caben en una fila)
    "seguridad_basica": (844, 362, 170, 64),
    "seguridad_avanzada": (1034, 362, 170, 64),
}


def nodo_en_posicion(arbol, pos):
    """Devuelve el nodo bajo la posición del mouse, o None."""
    for nodo in arbol.recorrido_bfs():
        posicion = POSICIONES.get(nodo.id)
        if posicion is not None and pygame.Rect(*posicion).collidepoint(pos):
            return nodo
    return None


def color_de_nodo(nodo):
    """Color del nodo con la paleta activa: gris si está bloqueado, teal si es de
    efecto fijo y naranja si es interactivo."""
    if not nodo.desbloqueado:
        return tema.COLOR_BLOQUEADO
    return tema.COLOR_TEAL if nodo.tipo_control == "fijo" else tema.COLOR_NARANJA


def subtitulo_de_nodo(nodo):
    """Texto pequeño bajo el nombre: costo o estado actual. '' si no hay nada que decir."""
    if not nodo.desbloqueado:
        return f"${formato_numero(nodo.costo)}" if nodo.costo > 0 else ""
    if nodo.tipo_control == "interruptor":
        return "ENCENDIDO" if nodo.activo else "APAGADO"
    if nodo.tipo_control == "dial":
        return f"{nodo.valor}%"
    if nodo.tipo_control == "bifurcacion":
        return nodo.variante_actual.replace("_", " ").capitalize() if nodo.variante_actual else "Sin elegir"
    return "Comprado" if nodo.costo > 0 else ""


def dibujar_conexiones(pantalla, arbol):
    """Líneas en ángulo recto de cada nodo hacia su padre real (según el árbol
    de datos, no según la posición en pantalla). Se iluminan cuando el hijo
    ya está desbloqueado, marcando el camino recorrido."""
    for nodo in arbol.recorrido_bfs():
        if nodo.padre is None:
            continue
        pos_padre = POSICIONES.get(nodo.padre.id)
        pos_hijo = POSICIONES.get(nodo.id)
        if pos_padre is None or pos_hijo is None:
            continue
        xp, yp, wp, hp = pos_padre
        xh, yh, wh, hh = pos_hijo
        x_padre, y_padre = xp + wp // 2, yp + hp
        x_hijo, y_hijo = xh + wh // 2, yh
        y_medio = min(y_padre + 28, (y_padre + y_hijo) // 2)

        color = tema.COLOR_ACENTO if nodo.desbloqueado else tema.COLOR_BORDE
        pygame.draw.line(pantalla, color, (x_padre, y_padre), (x_padre, y_medio), 3)
        pygame.draw.line(pantalla, color, (x_padre, y_medio), (x_hijo, y_medio), 3)
        pygame.draw.line(pantalla, color, (x_hijo, y_medio), (x_hijo, y_hijo), 3)


def _dibujar_icono_tipo(pantalla, nodo, rect, tinta):
    """Ícono en la esquina inferior derecha según el tipo de control: así se ve
    qué tipo de nodo es sin depender del color (interruptor, dial o bifurcación)."""
    cx, cy = rect.right - 24, rect.bottom - 17
    if nodo.tipo_control == "interruptor":
        pygame.draw.rect(pantalla, tinta, pygame.Rect(cx - 12, cy - 6, 24, 12), width=2, border_radius=6)
        perilla = cx + 6 if nodo.activo else cx - 6
        pygame.draw.circle(pantalla, tinta, (perilla, cy), 4)
    elif nodo.tipo_control == "dial":
        pygame.draw.circle(pantalla, tinta, (cx, cy), 9, width=2)
        pygame.draw.line(pantalla, tinta, (cx, cy), (cx + 5, cy - 5), 2)
    elif nodo.tipo_control == "bifurcacion":
        pygame.draw.line(pantalla, tinta, (cx, cy + 8), (cx, cy), 2)
        pygame.draw.line(pantalla, tinta, (cx, cy), (cx - 7, cy - 8), 2)
        pygame.draw.line(pantalla, tinta, (cx, cy), (cx + 7, cy - 8), 2)


def _dibujar_nodo(pantalla, fuentes, nodo, rect, recursos, t):
    base = color_de_nodo(nodo)
    disponible = nodo.puede_desbloquearse(recursos)
    encima = tema.esta_encima(rect)

    # Aros de atención (se dibujan debajo de la caja)
    if disponible:
        brillo = tema.mezclar(tema.COLOR_AMARILLO, tema.COLOR_TEXTO, pulso(t, 1.2))
        pygame.draw.rect(pantalla, brillo, rect.inflate(10 + int(pulso(t, 1.2) * 6), 10 + int(pulso(t, 1.2) * 6)),
                         width=2, border_radius=18)
    elif nodo.tipo_control == "interruptor" and nodo.activo:
        brillo = tema.mezclar(tema.COLOR_VERDE, tema.COLOR_TEXTO, pulso(t, 1.6))
        pygame.draw.rect(pantalla, brillo, rect.inflate(12, 12), width=3, border_radius=19)

    relleno = tema.aclarar(base, 0.15) if encima else base
    tema.dibujar_panel(pantalla, rect, radio=14, color=relleno, borde=tema.aclarar(base, 0.35))

    subtitulo = subtitulo_de_nodo(nodo)
    color_nombre = tema.color_sobre(relleno) if nodo.desbloqueado or disponible else tema.COLOR_TEXTO_SEC
    if subtitulo:
        tema.dibujar_texto(pantalla, fuentes.arbol, nodo.nombre, color_nombre,
                           center=(rect.centerx, rect.centery - 11))
        if not nodo.desbloqueado and recursos.dinero < nodo.costo:
            color_sub = tema.COLOR_ROJO
        elif nodo.desbloqueado:
            color_sub = tema.color_sobre(relleno)
        else:
            color_sub = tema.COLOR_AMARILLO
        tema.dibujar_texto(pantalla, fuentes.arbol_pequena, subtitulo, color_sub,
                           center=(rect.centerx, rect.centery + 14))
    else:
        tema.dibujar_texto(pantalla, fuentes.arbol, nodo.nombre, color_nombre, center=rect.center)

    _dibujar_icono_tipo(pantalla, nodo, rect, color_nombre)


def _dibujar_leyenda(pantalla, fuentes):
    items = (
        (tema.COLOR_BLOQUEADO, "Bloqueado"),
        (tema.COLOR_TEAL, "Efecto fijo"),
        (tema.COLOR_NARANJA, "Interactivo"),
        (tema.COLOR_AMARILLO, "Disponible: clic para comprar"),
    )
    fuente = fuentes.pequena
    separacion = 30
    anchos = [14 + 8 + fuente.size(texto)[0] for _, texto in items]
    x = (pantalla.get_width() - (sum(anchos) + separacion * (len(items) - 1))) // 2
    for (color, texto), ancho in zip(items, anchos):
        muestra = pygame.Rect(x, Y_LEYENDA, 14, 14)
        pygame.draw.rect(pantalla, color, muestra, border_radius=4)
        tema.dibujar_texto(pantalla, fuente, texto, tema.COLOR_TEXTO_SEC, midleft=(x + 22, Y_LEYENDA + 7))
        x += ancho + separacion


def dibujar_arbol(pantalla, arbol, fuentes, recursos, t):
    dibujar_conexiones(pantalla, arbol)
    for nodo in arbol.recorrido_bfs():
        posicion = POSICIONES.get(nodo.id)
        if posicion is None:
            continue
        _dibujar_nodo(pantalla, fuentes, nodo, pygame.Rect(*posicion), recursos, t)
    _dibujar_leyenda(pantalla, fuentes)
