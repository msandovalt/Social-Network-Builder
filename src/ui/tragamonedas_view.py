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
from ui.modelos_2d import dibujar_modelo_recurso
from minijuego.tragamonedas import (
    SIMBOLOS, ETIQUETAS, RECOMPENSAS, GIRANDO, POR_RESOLVER, RESUELTO, INACTIVO,
)

ANCHO_REEL = 170
ALTO_REEL = 220
ESPACIO = 40
CELDA = 110        # distancia entre símbolos consecutivos dentro del carrete
TAM_FICHA = 88     # lado de la ficha de cada símbolo
SEGUNDOS_BRILLO = 3.0

_total_ancho = ANCHO_REEL * 3 + ESPACIO * 2
_x0 = RECT_AREA_MINIJUEGO.x + (RECT_AREA_MINIJUEGO.width - _total_ancho) // 2
_y0 = RECT_AREA_MINIJUEGO.y + 96

RECTS_REEL = [
    pygame.Rect(_x0 + i * (ANCHO_REEL + ESPACIO), _y0, ANCHO_REEL, ALTO_REEL)
    for i in range(3)
]
RECT_BOTON_ACCION = pygame.Rect(
    RECT_AREA_MINIJUEGO.centerx - 140, RECT_AREA_MINIJUEGO.bottom - 74, 280, 52
)
RECT_PALANCA = pygame.Rect(RECTS_REEL[-1].right + 22, _y0 + 10, 62, ALTO_REEL - 20)

_ANCHO_PREMIO = 174
_ALTO_PREMIO = 52
_ESPACIO_PREMIO = 10
_X0_PREMIO = RECT_AREA_MINIJUEGO.right - 32 - (_ANCHO_PREMIO * 3 + _ESPACIO_PREMIO * 2)
RECTS_PREMIO = [
    pygame.Rect(
        _X0_PREMIO + i * (_ANCHO_PREMIO + _ESPACIO_PREMIO),
        RECT_AREA_MINIJUEGO.y + 24,
        _ANCHO_PREMIO,
        _ALTO_PREMIO,
    )
    for i in range(len(SIMBOLOS))
]

_NOMBRES_SIMBOLO = {
    "dinero": ("+$3.000", "Dinero"),
    "usuarios": ("+150", "Usuarios"),
    "reputacion": ("+6", "Reputación"),
}

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
    """Dibuja el modelo 2D multicapa del símbolo sobre una ficha de color `fondo`."""
    dibujar_modelo_recurso(pantalla, simbolo, centro, radio, fondo)


def _dibujar_ficha(pantalla, fuentes, simbolo, centro, girando):
    color = _color_simbolo(simbolo)
    if girando:
        color = tema.mezclar(color, _color_ventana(), 0.3)  # un poco más apagado mientras gira
    rect = pygame.Rect(centro[0] - TAM_FICHA // 2, centro[1] - TAM_FICHA // 2, TAM_FICHA, TAM_FICHA)
    fondo_ficha = tema.oscurecer(color, 0.42)
    pygame.draw.rect(pantalla, fondo_ficha, rect, border_radius=18)
    pygame.draw.rect(pantalla, tema.aclarar(color, 0.35), rect, width=3, border_radius=18)
    _dibujar_icono(pantalla, fuentes, simbolo, centro, 30, color)


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
    """Triángulos a los costados y puentes centrales que señalan la línea ganadora."""
    y = RECTS_REEL[0].centery
    for a, b in zip(RECTS_REEL, RECTS_REEL[1:]):
        pygame.draw.line(pantalla, tema.COLOR_AMARILLO, (a.right + 4, y), (b.left - 4, y), 3)
    izq = RECTS_REEL[0].left - 6
    der = RECTS_REEL[-1].right + 6
    pygame.draw.polygon(pantalla, tema.COLOR_AMARILLO, [(izq - 14, y - 11), (izq - 14, y + 11), (izq, y)])
    pygame.draw.polygon(pantalla, tema.COLOR_AMARILLO, [(der + 14, y - 11), (der + 14, y + 11), (der, y)])


def _dibujar_luces_marquesina(pantalla, maquina, t):
    """Bombillos decorativos en el borde superior e inferior de la máquina."""
    area = RECT_AREA_MINIJUEGO
    girando = maquina.estado == GIRANDO
    premio = maquina.estado == RESUELTO and maquina.resultado_tipo is not None
    velocidad = 9.0 if girando else (6.0 if premio else 2.2)
    paso = int(t * velocidad)

    xs = range(area.x + 36, area.right - 30, 38)
    for idx, x in enumerate(xs):
        for fila, y in enumerate((area.y + 10, area.bottom - 10)):
            encendida = ((idx + fila + paso) % 3 == 0) if not premio else ((idx + paso) % 2 == 0)
            if encendida:
                if premio:
                    color = _color_simbolo(maquina.resultado_tipo)
                elif girando:
                    color = tema.COLOR_AMARILLO if idx % 2 == 0 else tema.COLOR_CIAN
                else:
                    color = tema.COLOR_AMARILLO
                pygame.draw.circle(pantalla, color, (x, y), 4)
            else:
                pygame.draw.circle(pantalla, tema.COLOR_BORDE, (x, y), 3)


def _dibujar_medidor_velocidad(pantalla, fuentes, recursos, t):
    """Medidor lateral izquierdo que muestra cómo el Bienestar regula la
    velocidad de giro de los carretes."""
    bienestar = max(0.0, min(100.0, float(getattr(recursos, "bienestar", 70))))
    cx = (RECT_AREA_MINIJUEGO.left + RECTS_REEL[0].left) // 2 - 4
    y_top = _y0 + 26
    alto_barra = ALTO_REEL - 56
    barra = pygame.Rect(cx - 8, y_top, 16, alto_barra)

    tema.dibujar_texto(pantalla, fuentes.arbol_pequena, "Ritmo", tema.COLOR_TEXTO_SEC,
                       center=(cx, _y0 + 10))
    pygame.draw.rect(pantalla, _color_ventana(), barra, border_radius=8)
    pygame.draw.rect(pantalla, tema.COLOR_BORDE, barra, width=2, border_radius=8)

    # Nivel de estrés/velocidad: inverso al bienestar
    estres = 1.0 - (bienestar / 100.0)
    if bienestar < 40:
        color_nivel = tema.COLOR_ROJO
        etiqueta = "¡Frenesí!"
    elif bienestar < 65:
        color_nivel = tema.COLOR_AMARILLO
        etiqueta = "Rápido"
    else:
        color_nivel = tema.COLOR_VERDE
        etiqueta = "Calma"

    alto_relleno = max(8, int((alto_barra - 4) * max(0.12, estres)))
    relleno = pygame.Rect(barra.x + 2, barra.bottom - 2 - alto_relleno, barra.width - 4, alto_relleno)
    pygame.draw.rect(pantalla, color_nivel, relleno, border_radius=6)

    # Marcas de escala
    for frac in (0.35, 0.65):
        ym = barra.y + int(barra.height * frac)
        pygame.draw.line(pantalla, tema.COLOR_BORDE, (barra.left - 3, ym), (barra.right + 3, ym), 1)

    tema.dibujar_texto(pantalla, fuentes.arbol_pequena, etiqueta, color_nivel,
                       center=(cx, barra.bottom + 16))


def _dibujar_palanca(pantalla, fuentes, maquina, t):
    """Palanca mecánica a la derecha de los carretes que baja al girar."""
    rect = RECT_PALANCA
    base_x = RECTS_REEL[-1].right + 42
    base_y = _y0 + ALTO_REEL - 38

    # Soporte lateral unido a la parte inferior derecha del tercer carrete (lejos del marcador)
    soporte = pygame.Rect(RECTS_REEL[-1].right, base_y - 12, 42, 24)
    pygame.draw.rect(pantalla, tema.COLOR_PANEL_CLARO, soporte, border_radius=6)
    pygame.draw.rect(pantalla, tema.COLOR_BORDE, soporte, width=2, border_radius=6)
    pygame.draw.circle(pantalla, tema.COLOR_BORDE, (base_x, base_y), 10)

    # Posición del pomo según cuántos carretes siguen girando
    if maquina.estado == GIRANDO:
        activos = sum(1 for g in maquina.girando if g)
        frac = activos / 3.0
    else:
        frac = 0.0

    pomo_x = base_x + 12
    y_arriba = _y0 + 26
    y_abajo = _y0 + ALTO_REEL - 22
    pomo_y = int(y_arriba + (y_abajo - y_arriba) * frac)

    # Brazo metálico y pomo
    pygame.draw.line(pantalla, tema.COLOR_TEXTO_SEC, (base_x, base_y), (pomo_x, pomo_y), 6)
    color_pomo = tema.COLOR_AMARILLO if maquina.estado == GIRANDO else tema.COLOR_ROJO
    if maquina.estado == INACTIVO and tema.esta_encima(rect):
        color_pomo = tema.aclarar(color_pomo, 0.25)
    pygame.draw.circle(pantalla, color_pomo, (pomo_x, pomo_y), 15)
    pygame.draw.circle(pantalla, tema.aclarar(color_pomo, 0.4), (pomo_x - 4, pomo_y - 4), 5)


def progreso_premio(maquina, simbolo):
    """Cuántos carretes detenidos están alineados actualmente hacia `simbolo` (0..3).
    Si ya hay dos símbolos distintos detenidos, devuelve 0."""
    if maquina.estado == RESUELTO:
        return 3 if maquina.resultado_tipo == simbolo else 0
    if maquina.estado in (GIRANDO, POR_RESOLVER):
        detenidos = [SIMBOLOS[maquina.indices[i]] for i in range(3) if not maquina.girando[i]]
        if detenidos and all(s == simbolo for s in detenidos):
            return len(detenidos)
    return 0


def _dibujar_tabla_premios(pantalla, fuentes, maquina, t):
    """Tres tarjetas de recompensa con mini-fichas reales y resaltado reactivo."""
    for idx, simbolo in enumerate(SIMBOLOS):
        rect = RECTS_PREMIO[idx]
        color_sim = _color_simbolo(simbolo)
        progreso = progreso_premio(maquina, simbolo)
        ganador = maquina.estado == RESUELTO and maquina.resultado_tipo == simbolo
        en_carrera = progreso in (1, 2, 3) and maquina.estado in (GIRANDO, POR_RESOLVER)

        if ganador:
            p = pulso(t, 0.55)
            fondo = tema.mezclar(_color_ventana(), color_sim, 0.22 + 0.12 * p)
            borde = tema.mezclar(color_sim, tema.COLOR_TEXTO, p)
            grosor = 3
        elif en_carrera:
            fondo = tema.mezclar(_color_ventana(), color_sim, 0.14)
            borde = tema.aclarar(color_sim, 0.2)
            grosor = 2
        else:
            fondo = _color_ventana()
            borde = tema.mezclar(tema.COLOR_BORDE, color_sim, 0.35)
            grosor = 2

        pygame.draw.rect(pantalla, fondo, rect, border_radius=12)
        pygame.draw.rect(pantalla, borde, rect, width=grosor, border_radius=12)

        # 3 mini-fichas superpuestas a la izquierda de la tarjeta
        lado = 22
        cy = rect.centery
        for k in range(3):
            mx = rect.x + 10 + k * 14
            mrect = pygame.Rect(mx, cy - lado // 2, lado, lado)
            activa_k = (maquina.estado == INACTIVO) or ganador or (k < progreso)
            cf = color_sim if activa_k else tema.mezclar(color_sim, _color_ventana(), 0.55)
            pygame.draw.rect(pantalla, tema.oscurecer(cf, 0.45), mrect, border_radius=6)
            pygame.draw.rect(pantalla, tema.aclarar(cf, 0.35), mrect, width=1, border_radius=6)
            _dibujar_icono(pantalla, fuentes, simbolo, mrect.center, 7, cf)

        # Valor y nombre del premio a la derecha
        cantidad_txt, nombre_txt = _NOMBRES_SIMBOLO[simbolo]
        color_cant = tema.COLOR_TEXTO if ganador else tema.aclarar(color_sim, 0.25)
        tema.dibujar_texto(pantalla, fuentes.arbol, cantidad_txt, color_cant,
                           topleft=(rect.x + 68, rect.y + 6))
        tema.dibujar_texto(pantalla, fuentes.arbol_pequena, nombre_txt, tema.COLOR_TEXTO_SEC,
                           topleft=(rect.x + 68, rect.y + 28))

        if en_carrera:
            badge_txt = f"{progreso}/3"
            tema.dibujar_texto(pantalla, fuentes.arbol_pequena, badge_txt,
                               tema.COLOR_AMARILLO, topright=(rect.right - 8, rect.y + 6))


def _texto_recompensas():
    partes = [f"{ETIQUETAS[s]} = {formatear_efectos(RECOMPENSAS[s])}" for s in SIMBOLOS]
    return "Tres iguales:   " + "    ".join(partes)


def dibujar_tragamonedas(pantalla, fuentes, maquina, recursos, t):
    area = RECT_AREA_MINIJUEGO
    _dibujar_luces_marquesina(pantalla, maquina, t)
    tema.dibujar_texto(pantalla, fuentes.subtitulo, "Tragamonedas", tema.COLOR_TEXTO,
                       topleft=(area.x + 32, area.y + 20))
    tema.dibujar_texto(pantalla, fuentes.arbol_pequena, "Alinea 3 fichas iguales",
                       tema.COLOR_TEXTO_SEC, topleft=(area.x + 32, area.y + 56))
    _dibujar_tabla_premios(pantalla, fuentes, maquina, t)

    _dibujar_medidor_velocidad(pantalla, fuentes, recursos, t)
    for i, rect in enumerate(RECTS_REEL):
        _dibujar_carrete(pantalla, fuentes, maquina, i, rect, t)
    _dibujar_marcadores(pantalla)
    _dibujar_palanca(pantalla, fuentes, maquina, t)

    if maquina.estado == GIRANDO:
        botones_mando = ("X", "Y", "B")
        for i, rect in enumerate(RECTS_REEL):
            if maquina.girando[i]:
                tema.dibujar_texto(pantalla, fuentes.pequena, f"[{i + 1} / {botones_mando[i]}] Detener",
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
