"""
Dibujo del árbol de funcionalidades.

Diseño de posiciones: las cinco ramas tienen una columna propia. Las opciones
independientes forman una cuadrícula; las dependientes aparecen debajo de su
requisito. Un bus común hace visibles los niveles de hermanos.

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
    "red_social": (540, 128, 200, 48),

    "feed": (8, 216, 240, 48),
    "comunidad": (264, 216, 240, 48),
    "seguridad": (520, 216, 240, 48),
    "monetizacion": (776, 216, 240, 48),
    "marca": (1032, 216, 240, 48),

    # Las ramas con dependencia centran su primer nodo y abren sus mejoras debajo.
    "feed_basico": (56, 294, 144, 52),
    "feed_scroll": (16, 370, 112, 52),
    "feed_algoritmo": (136, 370, 112, 52),
    "feed_saludable": (72, 432, 112, 52),

    # Las herramientas de Comunidad son opciones hermanas en una cuadrícula.
    "comunidad_grupos": (272, 294, 112, 52),
    "comunidad_mensajes": (392, 294, 112, 52),
    "comunidad_verificacion": (272, 366, 112, 52),
    "comunidad_consejo": (392, 366, 112, 52),

    "seguridad_basica": (568, 294, 144, 52),
    "seguridad_avanzada": (528, 370, 112, 52),
    "seguridad_privacidad": (648, 370, 112, 52),
    "seguridad_transparencia": (584, 432, 112, 52),

    "monetizacion_anuncios": (784, 294, 112, 52),
    "monetizacion_suscripcion": (904, 294, 112, 52),
    "monetizacion_datos": (844, 366, 112, 52),

    "marketing_referidos": (1040, 294, 112, 52),
    "marketing_creadores": (1160, 294, 112, 52),
    "marketing_campana": (1100, 366, 112, 52),
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


def _dibujar_flecha_dependencia(pantalla, x, y, color):
    """Marca el sentido requisito -> mejora en el extremo de cada conexión."""
    pygame.draw.polygon(
        pantalla, color,
        ((x - 5, y - 4), (x + 5, y - 4), (x, y + 4)),
    )


def dibujar_conexiones(pantalla, arbol, t=0.0, recursos=None):
    """Dibuja buses de requisitos y flechas hacia cada mejora hija.

    Los hermanos comparten un tronco y se separan en un bus horizontal; así el
    dibujo deja claro que parten del mismo requisito y no forman una cadena.
    """
    indice = 0
    for padre in arbol.recorrido_bfs():
        pos_padre = POSICIONES.get(padre.id)
        if pos_padre is None:
            continue
        hijos = [(hijo, POSICIONES.get(hijo.id)) for hijo in padre.hijos]
        hijos = [(hijo, pos) for hijo, pos in hijos if pos is not None]
        if not hijos:
            continue

        xp, yp, wp, hp = pos_padre
        x_padre, y_padre = xp + wp // 2, yp + hp
        centros = [(pos[0] + pos[2] // 2, pos[1]) for _, pos in hijos]
        bus_y = min(y for _, y in centros) - 12

        if len(hijos) > 1:
            pygame.draw.line(pantalla, tema.COLOR_BORDE, (x_padre, y_padre), (x_padre, bus_y), 2)
            pygame.draw.line(
                pantalla, tema.COLOR_BORDE,
                (min(x for x, _ in centros), bus_y),
                (max(x for x, _ in centros), bus_y), 2,
            )

        for hijo, (x_hijo, y_hijo) in zip((h for h, _ in hijos), centros):
            if hijo.desbloqueado:
                color = tema.COLOR_ACENTO
            elif recursos is not None and hijo.puede_desbloquearse(recursos):
                color = tema.COLOR_AMARILLO
            else:
                color = tema.COLOR_BORDE

            if len(hijos) == 1:
                y_medio = min(y_padre + 24, (y_padre + y_hijo) // 2)
                puntos = [(x_padre, y_padre), (x_padre, y_medio),
                          (x_hijo, y_medio), (x_hijo, y_hijo)]
                for a, b in zip(puntos, puntos[1:]):
                    pygame.draw.line(pantalla, color, a, b, 3)
            else:
                puntos = [(x_padre, y_padre), (x_padre, bus_y),
                          (x_hijo, bus_y), (x_hijo, y_hijo)]
                pygame.draw.line(pantalla, color, (x_hijo, bus_y), (x_hijo, y_hijo), 3)

            _dibujar_flecha_dependencia(pantalla, x_hijo, y_hijo + 1, color)
            if hijo.desbloqueado:
                fase = (t * 0.55 + indice * 0.17) % 1.0
                px, py = _punto_en_polilinea(puntos, fase)
                color_pulso = tema.aclarar(tema.COLOR_CIAN, 0.35)
                pygame.draw.circle(pantalla, color, (px, py), 5)
                pygame.draw.circle(pantalla, color_pulso, (px, py), 2)
            indice += 1


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
    elif nid.startswith("monetizacion"):
        pygame.draw.circle(pantalla, tinta, (cx, cy), 7, width=2)
        pygame.draw.line(pantalla, tinta, (cx, cy - 4), (cx, cy + 4), 2)
    elif nid.startswith(("marca", "marketing")):
        pygame.draw.circle(pantalla, tinta, (cx, cy), 6, width=2)
        pygame.draw.line(pantalla, tinta, (cx, cy - 9), (cx, cy + 9), 1)
        pygame.draw.line(pantalla, tinta, (cx - 9, cy), (cx + 9, cy), 1)


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
    compacto = rect.width < 150

    # Aros de atención (se dibujan debajo de la caja)
    if disponible:
        brillo = tema.mezclar(tema.COLOR_AMARILLO, tema.COLOR_TEXTO, pulso(t, 1.2))
        expansion = 4 + int(pulso(t, 1.2) * 2) if compacto else 10 + int(pulso(t, 1.2) * 6)
        pygame.draw.rect(pantalla, brillo, rect.inflate(expansion, expansion),
                         width=2, border_radius=18)
    elif nodo.tipo_control == "interruptor" and nodo.activo:
        brillo = tema.mezclar(tema.COLOR_VERDE, tema.COLOR_TEXTO, pulso(t, 1.6))
        pygame.draw.rect(pantalla, brillo, rect.inflate(12, 12), width=3, border_radius=19)

    relleno = tema.aclarar(base, 0.15) if encima else base
    tema.dibujar_panel(pantalla, rect, radio=14, color=relleno, borde=tema.aclarar(base, 0.35))

    subtitulo = subtitulo_de_nodo(nodo)
    color_nombre = tema.color_sobre(relleno) if nodo.desbloqueado or disponible else tema.COLOR_TEXTO_SEC
    nombre = {
        "feed_saludable": "Saludable",
        "seguridad_transparencia": "Transparenc.",
        "comunidad_verificacion": "Verificación",
        "comunidad_consejo": "Consejo",
        "marketing_campana": "Campaña",
    }.get(nodo.id, nodo.nombre)
    fuente_nombre = fuentes.arbol_pequena if compacto else fuentes.arbol
    if subtitulo:
        tema.dibujar_texto(pantalla, fuente_nombre, nombre, color_nombre,
                           center=(rect.centerx if compacto else rect.centerx + 4,
                                   rect.centery - (9 if compacto else 11)))
        if not nodo.desbloqueado and recursos.dinero < nodo.costo:
            color_sub = tema.COLOR_ROJO
        elif nodo.desbloqueado:
            color_sub = tema.color_sobre(relleno)
        else:
            color_sub = tema.COLOR_AMARILLO
        tema.dibujar_texto(pantalla, fuentes.arbol_pequena, subtitulo, color_sub,
                           center=(rect.centerx, rect.centery + (14 if compacto else 13)))
    else:
        tema.dibujar_texto(pantalla, fuente_nombre, nombre, color_nombre,
                           center=(rect.centerx if compacto else rect.centerx + 4, rect.centery))

    if not compacto:
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
    dibujar_conexiones(pantalla, arbol, t, recursos)
    for nodo in arbol.recorrido_bfs():
        posicion = POSICIONES.get(nodo.id)
        if posicion is None:
            continue
        _dibujar_nodo(pantalla, fuentes, nodo, pygame.Rect(*posicion), recursos, t)
    _dibujar_leyenda(pantalla, fuentes)
