"""
Indicador flotante de audio (HUD): al pulsar M aparece arriba al centro, se desliza
suavemente, es visible por un momento y se desvanece.

Muestra un altavoz con ondas cuando hay sonido y un altavoz tachado cuando está
silenciado, siempre acompañado del texto del estado: nunca depende solo del color.
"""

import pygame

from ui import tema
from ui.animacion import ease_out_cubic
from ui.tema import ANCHO

DURACION_INDICADOR_AUDIO = 1.8   # segundos que se ve el indicador
DURACION_ENTRADA = 0.16
DURACION_SALIDA = 0.40
ALTO = 58
RADIO = 18
MARGEN_SUPERIOR = 18

_PADDING_IZQ = 20
_PADDING_DER = 24
_TAM_ICONO = 30
_SEPARACION = 12
_MARGEN_SOMBRA = 12

_cache_iconos = {}


def _icono_altavoz(silenciado, color, fondo):
    """Altavoz (con ondas o tachado) dibujado a 2x y reducido para suavizar bordes."""
    llave = (silenciado, tuple(color), tuple(fondo))
    if llave in _cache_iconos:
        return _cache_iconos[llave]

    escala = 2
    lado = 32 * escala
    icono = pygame.Surface((lado, lado), pygame.SRCALPHA)

    # Cuerpo y cono del altavoz
    pygame.draw.rect(icono, color, (8, 25, 12, 14), border_radius=2)
    pygame.draw.polygon(icono, color, [(20, 25), (36, 10), (36, 54), (20, 39)])

    if silenciado:
        # Barra diagonal con un hueco del color del fondo para que se lea bien
        pygame.draw.line(icono, fondo, (6, 6), (58, 58), 11)
        pygame.draw.line(icono, color, (6, 6), (58, 58), 6)
    else:
        # Dos ondas de sonido a la derecha del altavoz
        for radio in (10, 19):
            pygame.draw.arc(icono, color, pygame.Rect(36 - radio, 32 - radio, radio * 2, radio * 2),
                            -0.85, 0.85, 4)

    icono = pygame.transform.smoothscale(icono, (_TAM_ICONO, _TAM_ICONO))
    _cache_iconos[llave] = icono
    return icono


def dibujar_indicador_audio(pantalla, fuentes, silenciado, tiempo):
    """Dibuja el HUD sobre `pantalla`. `tiempo` son los segundos desde que apareció."""
    etiqueta = "Audio silenciado" if silenciado else "Audio activado"
    fondo = tema.oscurecer(tema.COLOR_PANEL, 0.18)
    tinta = tema.color_sobre(fondo)
    texto = fuentes.boton.render(etiqueta, True, tinta)
    ancho = _PADDING_IZQ + _TAM_ICONO + _SEPARACION + texto.get_width() + _PADDING_DER

    lienzo = pygame.Surface((ancho + _MARGEN_SOMBRA * 2, ALTO + _MARGEN_SOMBRA * 2 + 6),
                            pygame.SRCALPHA)
    rect = pygame.Rect(_MARGEN_SOMBRA, _MARGEN_SOMBRA, ancho, ALTO)

    # Sombra y cuerpo redondeado semitransparente
    pygame.draw.rect(lienzo, (0, 0, 0, 100), rect.move(0, 6), border_radius=RADIO + 2)
    pygame.draw.rect(lienzo, (*fondo, 242), rect, border_radius=RADIO)
    pygame.draw.rect(lienzo, (*tema.COLOR_BORDE, 255), rect, width=1, border_radius=RADIO)

    icono = _icono_altavoz(silenciado, tinta, fondo)
    lienzo.blit(icono, (rect.x + _PADDING_IZQ, rect.centery - _TAM_ICONO // 2))
    lienzo.blit(texto, (rect.x + _PADDING_IZQ + _TAM_ICONO + _SEPARACION,
                        rect.centery - texto.get_height() // 2))

    entrada = ease_out_cubic(tiempo / DURACION_ENTRADA)
    salida = ease_out_cubic((DURACION_INDICADOR_AUDIO - tiempo) / DURACION_SALIDA)
    avance = max(0.0, min(entrada, salida))
    lienzo.set_alpha(int(255 * avance))

    x = (ANCHO - ancho) // 2 - _MARGEN_SOMBRA
    y = MARGEN_SUPERIOR + int((1 - entrada) * -14) - _MARGEN_SOMBRA
    pantalla.blit(lienzo, (x, y))
