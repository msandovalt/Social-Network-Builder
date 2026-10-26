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


def _punto_en_polilinea(puntos, fraccion):
    """Interpola un punto a lo largo de una polilínea según `fraccion` en [0, 1]."""
    tramos = []
    total = 0.0
    for a, b in zip(puntos, puntos[1:]):
        dist = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
        tramos.append((a, b, dist))
        total += dist
    if total <= 0:
        return puntos[0]
    objetivo = max(0.0, min(1.0, fraccion)) * total
    acum = 0.0
    for a, b, dist in tramos:
        if acum + dist >= objetivo and dist > 0:
            u = (objetivo - acum) / dist
            return int(a[0] + (b[0] - a[0]) * u), int(a[1] + (b[1] - a[1]) * u)
        acum += dist
    return puntos[-1]


def dibujar_conexiones(pantalla, arbol, t=0.0):
    """Líneas en ángulo recto de cada nodo hacia su padre real (según el árbol
    de datos, no según la posición en pantalla). Se iluminan cuando el hijo
    ya está desbloqueado y muestran un pulso de energía viajando por la rama."""
    for idx, nodo in enumerate(arbol.recorrido_bfs()):
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

        puntos = [(x_padre, y_padre), (x_padre, y_medio), (x_hijo, y_medio), (x_hijo, y_hijo)]
        color = tema.COLOR_ACENTO if nodo.desbloqueado else tema.COLOR_BORDE
        for a, b in zip(puntos, puntos[1:]):
            pygame.draw.line(pantalla, color, a, b, 3)

        if nodo.desbloqueado:
            fase = (t * 0.55 + idx * 0.17) % 1.0
            px, py = _punto_en_polilinea(puntos, fase)
            color_pulso = tema.aclarar(tema.COLOR_CIAN, 0.35)
            pygame.draw.circle(pantalla, color, (px, py), 6)
            pygame.draw.circle(pantalla, color_pulso, (px, py), 3)


def _dibujar_icono_rama(pantalla, nodo, rect, tinta):
    """Ícono vectorial en la esquina superior izquierda según la rama del árbol."""
    cx, cy = rect.x + 18, rect.y + 18
    nid = nodo.id
    if nid == "red_social":
        p1, p2, p3 = (cx - 5, cy + 4), (cx + 5, cy + 4), (cx, cy - 5)
        pygame.draw.line(pantalla, tinta, p1, p2, 1)
        pygame.draw.line(pantalla, tinta, p1, p3, 1)
        pygame.draw.line(pantalla, tinta, p2, p3, 1)
        for p in (p1, p2, p3):
            pygame.draw.circle(pantalla, tinta, p, 3)
    elif nid.startswith("feed"):
        marco = pygame.Rect(cx - 7, cy - 6, 14, 12)
        pygame.draw.rect(pantalla, tinta, marco, width=2, border_radius=3)
        pygame.draw.line(pantalla, tinta, (cx - 4, cy - 2), (cx + 4, cy - 2), 2)
        pygame.draw.line(pantalla, tinta, (cx - 4, cy + 2), (cx + 2, cy + 2), 2)
    elif nid.startswith("comunidad"):
        pygame.draw.circle(pantalla, tinta, (cx - 3, cy - 3), 3, width=1)
        pygame.draw.circle(pantalla, tinta, (cx + 4, cy - 2), 2, width=1)
        pygame.draw.arc(pantalla, tinta, pygame.Rect(cx - 8, cy, 10, 7), 0, 3.14, 2)
        pygame.draw.arc(pantalla, tinta, pygame.Rect(cx, cy + 1, 8, 6), 0, 3.14, 1)
    elif nid.startswith("seguridad"):
        escudo = [(cx, cy - 7), (cx + 6, cy - 4), (cx + 5, cy + 3), (cx, cy + 7), (cx - 5, cy + 3), (cx - 6, cy - 4)]
        pygame.draw.polygon(pantalla, tinta, escudo, width=2)


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


def _dibujar_mini_indicador(pantalla, nodo, rect):
    """Mini-barra o indicador visual de estado en nodos interactivos desbloqueados."""
    if not nodo.desbloqueado:
        return
    if nodo.tipo_control == "dial":
        barra = pygame.Rect(rect.x + 18, rect.bottom - 9, rect.width - 54, 4)
        pygame.draw.rect(pantalla, tema.oscurecer(tema.COLOR_NARANJA, 0.45), barra, border_radius=2)
        ancho = int(barra.width * max(0.0, min(1.0, nodo.valor / 100.0)))
        if ancho > 0:
            relleno = pygame.Rect(barra.x, barra.y, max(4, ancho), barra.height)
            pygame.draw.rect(pantalla, tema.COLOR_TEXTO, relleno, border_radius=2)
    elif nodo.tipo_control == "interruptor":
        color_led = tema.COLOR_VERDE if nodo.activo else tema.COLOR_ROJO
        pygame.draw.circle(pantalla, color_led, (rect.x + 18, rect.bottom - 14), 4)


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
                           center=(rect.centerx + 4, rect.centery - 11))
        if not nodo.desbloqueado and recursos.dinero < nodo.costo:
            color_sub = tema.COLOR_ROJO
        elif nodo.desbloqueado:
            color_sub = tema.color_sobre(relleno)
        else:
            color_sub = tema.COLOR_AMARILLO
        tema.dibujar_texto(pantalla, fuentes.arbol_pequena, subtitulo, color_sub,
                           center=(rect.centerx, rect.centery + 13))
    else:
        tema.dibujar_texto(pantalla, fuentes.arbol, nodo.nombre, color_nombre,
                           center=(rect.centerx + 4, rect.centery))

    _dibujar_icono_rama(pantalla, nodo, rect, color_nombre)
    _dibujar_icono_tipo(pantalla, nodo, rect, color_nombre)
    _dibujar_mini_indicador(pantalla, nodo, rect)


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
    dibujar_conexiones(pantalla, arbol, t)
    for nodo in arbol.recorrido_bfs():
        posicion = POSICIONES.get(nodo.id)
        if posicion is None:
            continue
        _dibujar_nodo(pantalla, fuentes, nodo, pygame.Rect(*posicion), recursos, t)
    _dibujar_leyenda(pantalla, fuentes)
