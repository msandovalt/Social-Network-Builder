"""
Pantalla principal (hub) del juego y encabezado compartido.

El encabezado (tarjetas de recursos con valores animados, indicador de ronda)
se dibuja igual en Principal, Árbol y Mapa. El área central del hub aloja la
tragamonedas; los botones inferiores llevan al Árbol y al Mapa.

Las funciones que reciben `juego` solo necesitan que tenga `fuentes`,
`contadores`, `rondas` y `tiempo` (ver juego.Juego).
"""

import pygame

from ui import tema
from ui.formato import formato_numero
from ui.tema import ANCHO
from tree.ronda import UMBRAL_FUGA

MARGEN = 24
Y_TARJETAS = 14
ANCHO_TARJETA = 204
ALTO_TARJETA = 64
ESPACIO_TARJETAS = 10

RECT_BOTON_VOLVER = pygame.Rect(MARGEN, 88, 130, 38)  # usado en Árbol y Mapa para volver a Principal
RECT_AREA_MINIJUEGO = pygame.Rect(220, 140, 840, 440)
RECT_BOTON_ARBOL = pygame.Rect(220, 604, 260, 60)
RECT_BOTON_MAPA = pygame.Rect(800, 604, 260, 60)

# (clave en Recursos, etiqueta, ¿es una escala 0-100?). El color de cada recurso
# sale de la paleta activa: tema.COLOR_RECURSO[clave].
TARJETAS = (
    ("dinero", "Dinero", False),
    ("usuarios", "Usuarios", False),
    ("bienestar", "Bienestar", True),
    ("reputacion", "Reputación", True),
    ("engagement", "Engagement", True),
)


def _dibujar_tarjeta(pantalla, fuentes, rect, etiqueta, color, contador, clave, es_escala, limite=None):
    tema.dibujar_panel(pantalla, rect, radio=14)
    acento = pygame.Rect(rect.x + 10, rect.y + 12, 5, rect.height - 24)
    pygame.draw.rect(pantalla, color, acento, border_radius=3)

    valor = contador.valor
    if clave == "dinero":
        texto = f"-${formato_numero(abs(valor))}" if valor < 0 else f"${formato_numero(valor)}"
    else:
        texto = formato_numero(valor)

    # Verde mientras sube, rojo mientras baja
    lleno = limite is not None and valor >= limite
    if lleno:  # el mercado de tus regiones está completo: hay que expandirse para crecer
        color_valor = tema.COLOR_AMARILLO
    elif contador.direccion > 0:
        color_valor = tema.COLOR_VERDE
    elif contador.direccion < 0 or (clave == "dinero" and valor < 0):
        color_valor = tema.COLOR_ROJO
    else:
        color_valor = tema.COLOR_TEXTO

    color_etiqueta = tema.COLOR_TEXTO_SEC
    if clave == "bienestar" and valor < UMBRAL_FUGA:  # los usuarios se están yendo
        etiqueta, color_etiqueta = "Bienestar ¡bajo!", tema.COLOR_ROJO
    tema.dibujar_texto(pantalla, fuentes.pequena, etiqueta, color_etiqueta,
                       topleft=(rect.x + 26, rect.y + 6))
    rect_valor = tema.dibujar_texto(pantalla, fuentes.boton, texto, color_valor,
                                    topleft=(rect.x + 26, rect.y + 22))
    if contador.direccion != 0:  # la flecha cuenta lo mismo que el color: sube o baja
        _dibujar_flecha(pantalla, (rect_valor.right + 14, rect_valor.centery), contador.direccion > 0, color_valor)

    if limite is not None:
        tema.dibujar_texto(pantalla, fuentes.arbol_pequena, f"máx. {formato_numero(limite)}",
                           tema.COLOR_AMARILLO if lleno else tema.COLOR_TEXTO_SEC,
                           topright=(rect.right - 12, rect.y + 8))

    if es_escala or limite is not None:
        barra = pygame.Rect(rect.x + 26, rect.bottom - 9, rect.width - 44, 5)
        pygame.draw.rect(pantalla, tema.COLOR_PANEL_CLARO, barra, border_radius=3)
        proporcion = max(0.0, min(1.0, valor / (limite if limite else 100)))
        if proporcion > 0:
            relleno = pygame.Rect(barra.x, barra.y, max(4, int(barra.width * proporcion)), barra.height)
            color_barra = tema.COLOR_ROJO if (es_escala and valor < UMBRAL_FUGA) else color
            pygame.draw.rect(pantalla, color_barra, relleno, border_radius=3)


def _dibujar_flecha(pantalla, centro, hacia_arriba, color):
    """Triángulo que indica si un valor está subiendo o bajando (no depende del color)."""
    x, y = centro
    if hacia_arriba:
        puntos = [(x - 7, y + 5), (x + 7, y + 5), (x, y - 7)]
    else:
        puntos = [(x - 7, y - 5), (x + 7, y - 5), (x, y + 7)]
    pygame.draw.polygon(pantalla, color, puntos)


def dibujar_encabezado(pantalla, juego, titulo):
    """Tarjetas de recursos, título de la pantalla e indicador de ronda."""
    fuentes = juego.fuentes
    for i, (clave, etiqueta, es_escala) in enumerate(TARJETAS):
        color = tema.COLOR_RECURSO[clave]
        rect = pygame.Rect(MARGEN + i * (ANCHO_TARJETA + ESPACIO_TARJETAS), Y_TARJETAS,
                           ANCHO_TARJETA, ALTO_TARJETA)
        limite = juego.recursos.limite_usuarios if clave == "usuarios" else None
        _dibujar_tarjeta(pantalla, fuentes, rect, etiqueta, color, juego.contadores[clave], clave, es_escala, limite)

    tema.dibujar_texto(pantalla, fuentes.subtitulo, titulo, tema.COLOR_TEXTO, midtop=(ANCHO // 2, 86))

    rondas, eventos = juego.rondas, juego.eventos
    crecimiento = juego.recursos.crecimiento * 100
    tema.dibujar_texto(pantalla, fuentes.pequena,
                       f"Ronda {rondas.numero}   ·   Crecimiento pasivo {crecimiento:.0f}%",
                       tema.COLOR_TEXTO_SEC, topright=(ANCHO - MARGEN, 84))
    _dibujar_barra(pantalla, 108, 1 - rondas.segundos_restantes() / rondas.duracion, tema.COLOR_ACENTO)
    _dibujar_barra(pantalla, 120, 1 - eventos.segundos_restantes() / eventos.intervalo, tema.COLOR_ROSA)
    tema.dibujar_texto(pantalla, fuentes.pequena, "Evento", tema.COLOR_TEXTO_SEC,
                       midright=(ANCHO - MARGEN - 240 - 10, 123))
    if getattr(getattr(juego, "audio", None), "mute", False):
        tema.dibujar_texto(pantalla, fuentes.pequena, "[M] Silenciado", tema.COLOR_AMARILLO,
                           midright=(ANCHO - MARGEN - 240 - 10, 107))


def _dibujar_barra(pantalla, y, progreso, color):
    barra = pygame.Rect(ANCHO - MARGEN - 240, y, 240, 6)
    pygame.draw.rect(pantalla, tema.COLOR_PANEL_CLARO, barra, border_radius=3)
    if progreso > 0:
        relleno = pygame.Rect(barra.x, barra.y, max(6, int(barra.width * min(1.0, progreso))), barra.height)
        pygame.draw.rect(pantalla, color, relleno, border_radius=3)


def dibujar_base(pantalla, juego, titulo):
    """Fondo animado + encabezado: la base común de Principal, Árbol y Mapa."""
    tema.dibujar_fondo(pantalla, juego.tiempo)
    dibujar_encabezado(pantalla, juego, titulo)


def dibujar_principal(pantalla, juego):
    fuentes = juego.fuentes
    dibujar_base(pantalla, juego, "Panel principal")
    mundo = juego.mundo
    tema.dibujar_texto(pantalla, fuentes.normal,
                       f"Objetivo: conquistar el planeta ({len(mundo.conquistadas())}/{len(mundo.regiones)})",
                       tema.COLOR_TEXTO_SEC, topleft=(MARGEN, 96))
    tema.dibujar_panel(pantalla, RECT_AREA_MINIJUEGO, radio=22)
    tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_ARBOL, "Árbol", tema.COLOR_ACENTO, radio=16)
    tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_MAPA, "Mapa", tema.COLOR_ACENTO, radio=16)
    tema.dibujar_texto(pantalla, fuentes.pequena, "Pulsa el botón ? de arriba para ver la ayuda",
                       tema.COLOR_TEXTO_SEC, center=(ANCHO // 2, 692))


def dibujar_boton_volver(pantalla, fuentes):
    tema.dibujar_boton(pantalla, fuentes.normal, RECT_BOTON_VOLVER, "< Volver", tema.COLOR_PANEL_CLARO, radio=10)
