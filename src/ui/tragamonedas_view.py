"""
Dibujo de la tragamonedas dentro del área central del hub.

Los carretes son ventanas con símbolos que se desplazan en vertical según la
posición continua que calcula la lógica (`maquina.posiciones`). Los rectángulos
de los carretes y el botón de acción son constantes de módulo (no cambian de
posición), así juego.py puede usarlos directamente para detectar clics.
"""

import math

import pygame

from ui import tema
from ui.animacion import pulso
from ui.formato import formatear_efectos
from ui.hub_view import RECT_AREA_MINIJUEGO
from minijuego.tragamonedas import (
    SIMBOLOS, ETIQUETAS, RECOMPENSAS, GIRANDO, RESUELTO, INACTIVO,
)

ANCHO_REEL = 170
ALTO_REEL = 220
ESPACIO = 40
CELDA = 110        # distancia entre símbolos consecutivos dentro del carrete
TAM_FICHA = 88     # lado de la ficha de cada símbolo
SEGUNDOS_BRILLO = 3.0

_total_ancho = ANCHO_REEL * 3 + ESPACIO * 2
_x0 = RECT_AREA_MINIJUEGO.x + (RECT_AREA_MINIJUEGO.width - _total_ancho) // 2
_y0 = RECT_AREA_MINIJUEGO.y + 90

RECTS_REEL = [
    pygame.Rect(_x0 + i * (ANCHO_REEL + ESPACIO), _y0, ANCHO_REEL, ALTO_REEL)
    for i in range(3)
]
RECT_BOTON_ACCION = pygame.Rect(
    RECT_AREA_MINIJUEGO.centerx - 140, RECT_AREA_MINIJUEGO.bottom - 74, 280, 52
)

_cache = {}


def _color_ventana():
    """Fondo oscuro de la ventana de cada carrete (depende de la paleta)."""
    return tema.oscurecer(tema.COLOR_PANEL, 0.4)


def _color_simbolo(simbolo):
    """Cada símbolo usa el color de su recurso en la paleta activa."""
    return tema.COLOR_RECURSO[simbolo]


def _degradado_carrete(ancho, alto):
    """Desvanecido arriba y abajo del carrete: da sensación de profundidad y
    esconde el corte de los símbolos que asoman."""
    ventana = _color_ventana()
    clave = (ancho, alto, ventana)
    if clave not in _cache:
        superficie = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        largo = 48
        for y in range(largo):
            alpha = int(255 * (1 - y / largo) ** 1.5)
            color = (ventana[0], ventana[1], ventana[2], alpha)
            pygame.draw.line(superficie, color, (0, y), (ancho, y))
            pygame.draw.line(superficie, color, (0, alto - 1 - y), (ancho, alto - 1 - y))
        _cache[clave] = superficie
    return _cache[clave]


def _dibujar_icono(pantalla, fuentes, simbolo, centro, radio, fondo):
    """Ícono del símbolo sobre una ficha de color `fondo`. La forma (moneda con $,
    persona, estrella) es lo que lo identifica: el color es solo un refuerzo."""
    cx, cy = centro
    tinta = tema.color_sobre(fondo)  # claro u oscuro, según el fondo de la ficha
    if simbolo == "dinero":
        pygame.draw.circle(pantalla, tinta, centro, radio, width=4)
        tema.dibujar_texto(pantalla, fuentes.subtitulo, "$", tinta, center=centro)
    elif simbolo == "usuarios":
        pygame.draw.circle(pantalla, tinta, (cx, cy - int(radio * 0.35)), int(radio * 0.32))
        cuerpo = pygame.Rect(cx - int(radio * 0.65), cy + int(radio * 0.05),
                             int(radio * 1.3), int(radio * 0.95))
        pygame.draw.ellipse(pantalla, tinta, cuerpo)
    else:  # reputacion: estrella
        puntos = []
        for k in range(10):
            angulo = -math.pi / 2 + k * math.pi / 5
            r = radio if k % 2 == 0 else radio * 0.45
            puntos.append((cx + math.cos(angulo) * r, cy + math.sin(angulo) * r))
        pygame.draw.polygon(pantalla, tinta, puntos)


def _dibujar_ficha(pantalla, fuentes, simbolo, centro, girando):
    color = _color_simbolo(simbolo)
    if girando:
        color = tema.mezclar(color, _color_ventana(), 0.3)  # un poco más apagado mientras gira
    rect = pygame.Rect(centro[0] - TAM_FICHA // 2, centro[1] - TAM_FICHA // 2, TAM_FICHA, TAM_FICHA)
    pygame.draw.rect(pantalla, color, rect, border_radius=18)
    pygame.draw.rect(pantalla, tema.aclarar(color, 0.35), rect, width=3, border_radius=18)
    _dibujar_icono(pantalla, fuentes, simbolo, centro, 26, color)


def _dibujar_carrete(pantalla, fuentes, maquina, i, rect, t):
    girando = maquina.estado == GIRANDO and maquina.girando[i]
    detenido_esperando = maquina.estado == GIRANDO and not maquina.girando[i]
    brillando = (maquina.estado == RESUELTO and maquina.resultado_tipo is not None
                 and maquina.tiempo_resultado < SEGUNDOS_BRILLO)

    if brillando:
        borde = tema.mezclar(_color_simbolo(maquina.resultado_tipo), tema.COLOR_TEXTO, pulso(t, 0.6))
    elif detenido_esperando:
        borde = tema.COLOR_ACENTO
    else:
        borde = tema.COLOR_BORDE
    tema.dibujar_panel(pantalla, rect, radio=20, color=_color_ventana(), borde=borde, grosor=3)

    interior = rect.inflate(-14, -14)
    pantalla.set_clip(interior)
    posicion = maquina.posiciones[i]
    base = int(round(posicion))
    for d in range(-2, 3):
        k = base + d
        simbolo = SIMBOLOS[k % len(SIMBOLOS)]
        y = rect.centery + (k - posicion) * CELDA
        _dibujar_ficha(pantalla, fuentes, simbolo, (rect.centerx, int(y)), girando)
    pantalla.blit(_degradado_carrete(interior.width, interior.height), interior.topleft)
    pantalla.set_clip(None)

    # Marco de la línea de pago (la fila central)
    linea = pygame.Rect(rect.x + 8, rect.centery - CELDA // 2, rect.width - 16, CELDA)
    pygame.draw.rect(pantalla, tema.mezclar(_color_ventana(), tema.COLOR_TEXTO, 0.22), linea,
                     width=2, border_radius=18)

    if brillando:
        grosor = 2 + int(pulso(t, 0.6) * 3)
        pygame.draw.rect(pantalla, borde, rect.inflate(12, 12), width=grosor, border_radius=26)


def _dibujar_marcadores(pantalla):
    """Triángulos a los costados que señalan la fila ganadora."""
    y = RECTS_REEL[0].centery
    izq = RECTS_REEL[0].left - 20
    der = RECTS_REEL[-1].right + 20
    pygame.draw.polygon(pantalla, tema.COLOR_AMARILLO, [(izq - 16, y - 13), (izq - 16, y + 13), (izq, y)])
    pygame.draw.polygon(pantalla, tema.COLOR_AMARILLO, [(der + 16, y - 13), (der + 16, y + 13), (der, y)])


def _texto_recompensas():
    partes = [f"{ETIQUETAS[s]} = {formatear_efectos(RECOMPENSAS[s])}" for s in SIMBOLOS]
    return "Tres iguales:   " + "    ".join(partes)


def dibujar_tragamonedas(pantalla, fuentes, maquina, recursos, t):
    area = RECT_AREA_MINIJUEGO
    tema.dibujar_texto(pantalla, fuentes.subtitulo, "Tragamonedas", tema.COLOR_TEXTO,
                       topleft=(area.x + 32, area.y + 20))
    tema.dibujar_texto(pantalla, fuentes.pequena, _texto_recompensas(), tema.COLOR_TEXTO_SEC,
                       topleft=(area.x + 32, area.y + 58))

    for i, rect in enumerate(RECTS_REEL):
        _dibujar_carrete(pantalla, fuentes, maquina, i, rect, t)
    _dibujar_marcadores(pantalla)

    if maquina.estado == GIRANDO:
        for i, rect in enumerate(RECTS_REEL):
            if maquina.girando[i]:
                tema.dibujar_texto(pantalla, fuentes.pequena, f"[{i + 1}] Detener",
                                   tema.COLOR_TEXTO_SEC, midtop=(rect.centerx, rect.bottom + 12))

    elif maquina.estado == INACTIVO:
        costo = maquina.costo(recursos)
        puede_jugar = maquina.puede_jugar(recursos)
        tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_ACCION, f"Jugar (${costo:,})".replace(",", "."),
                           tema.COLOR_BOTON_OK, habilitado=puede_jugar)
        if not puede_jugar:
            tema.dibujar_texto(pantalla, fuentes.pequena, "No tienes dinero suficiente para jugar",
                               tema.COLOR_ROJO, center=(area.centerx, RECT_BOTON_ACCION.top - 22))

    elif maquina.estado == RESUELTO:
        color = tema.COLOR_VERDE if maquina.resultado_tipo else tema.COLOR_TEXTO_SEC
        tema.dibujar_texto(pantalla, fuentes.boton, maquina.mensaje_resultado, color,
                           center=(area.centerx, RECT_BOTON_ACCION.top - 22))
        tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_ACCION, "Continuar", tema.COLOR_PANEL_CLARO)
