"""
Pantallas de menú inicial, pausa y fin de partida.

Todas usan el tema compartido (fondo animado, paneles, botones con hover).
"""

import math

import pygame

from ui import tema
from ui.tema import ANCHO, ALTO
from ui.resumen_view import (
    dibujar_fin,
    UMBRAL_BIENESTAR_SANO,
    MENSAJE_VICTORIA_SANA,
    MENSAJE_VICTORIA_BAJO_BIENESTAR,
    MENSAJE_EXODO_BIENESTAR,
    MOTIVOS_FIN,
)

_X_BOTON = ANCHO // 2 - 130

RECT_BOTON_START = pygame.Rect(_X_BOTON, 400, 260, 64)
RECT_BOTON_AYUDA_MENU = pygame.Rect(_X_BOTON, 480, 260, 56)
RECT_BOTON_ACCESIBILIDAD_MENU = pygame.Rect(_X_BOTON, 548, 260, 56)
RECT_BOTON_PAUSA = pygame.Rect(ANCHO - 24 - 48, 16, 48, 48)         # esquina superior derecha, durante el juego
RECT_BOTON_AYUDA_JUEGO = pygame.Rect(ANCHO - 24 - 48 - 12 - 48, 16, 48, 48)  # a la izquierda de la pausa
RECT_BOTON_REANUDAR = pygame.Rect(_X_BOTON, 300, 260, 58)
RECT_BOTON_AYUDA_PAUSA = pygame.Rect(_X_BOTON, 366, 260, 58)
RECT_BOTON_ACCESIBILIDAD_PAUSA = pygame.Rect(_X_BOTON, 432, 260, 58)
RECT_BOTON_SALIR_PAUSA = pygame.Rect(_X_BOTON, 498, 260, 58)
RECT_BOTON_SALIR = pygame.Rect(_X_BOTON, 374, 260, 58)              # pantalla de fin de partida (compatibilidad)
RECT_BOTON_NUEVA = pygame.Rect(_X_BOTON, 300, 260, 58)              # pantalla de fin de partida (compatibilidad)


def dibujar_menu(pantalla, fuentes, t):
    tema.dibujar_fondo(pantalla, t)

    flotar = math.sin(t * 1.5) * 4
    tema.dibujar_texto(pantalla, fuentes.titulo, "Social Network Builder", tema.COLOR_TEXTO,
                       center=(ANCHO // 2, 240 + flotar))
    tema.dibujar_texto(pantalla, fuentes.normal, "Construye tu red social. Cuida a tus usuarios.",
                       tema.COLOR_TEXTO_SEC, center=(ANCHO // 2, 310))

    tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_START, "Jugar", tema.COLOR_ACENTO, radio=16)
    tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_AYUDA_MENU, "Ayuda", tema.COLOR_PANEL_CLARO, radio=16)
    tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_ACCESIBILIDAD_MENU, "Accesibilidad",
                       tema.COLOR_PANEL_CLARO, radio=16)
    tema.dibujar_texto(pantalla, fuentes.pequena, "Esc para pausar   ·   M para silenciar audio", tema.COLOR_TEXTO_SEC,
                       center=(ANCHO // 2, ALTO - 40))


def dibujar_boton_pausa(pantalla, fuentes):
    rect = RECT_BOTON_PAUSA
    color = tema.aclarar(tema.COLOR_PANEL_CLARO, 0.15) if tema.esta_encima(rect) else tema.COLOR_PANEL_CLARO
    pygame.draw.rect(pantalla, color, rect, border_radius=12)
    pygame.draw.rect(pantalla, tema.COLOR_BORDE, rect, width=2, border_radius=12)
    for dx in (-10, 4):
        barra = pygame.Rect(rect.centerx + dx, rect.centery - 10, 6, 20)
        pygame.draw.rect(pantalla, tema.COLOR_TEXTO, barra, border_radius=2)


def dibujar_boton_ayuda(pantalla, fuentes):
    """Botón "?" de la esquina superior, a la izquierda del de pausa."""
    rect = RECT_BOTON_AYUDA_JUEGO
    color = tema.aclarar(tema.COLOR_PANEL_CLARO, 0.15) if tema.esta_encima(rect) else tema.COLOR_PANEL_CLARO
    pygame.draw.rect(pantalla, color, rect, border_radius=12)
    pygame.draw.rect(pantalla, tema.COLOR_BORDE, rect, width=2, border_radius=12)
    tema.dibujar_texto(pantalla, fuentes.boton, "?", tema.COLOR_TEXTO, center=rect.center)


def dibujar_pausa(pantalla, fuentes):
    """Se dibuja ENCIMA del estado del juego (que ya se dibujó antes),
    con un overlay semitransparente para que se note que está pausado."""
    tema.dibujar_overlay(pantalla, 180)
    panel = pygame.Rect(ANCHO // 2 - 200, 150, 400, 420)
    tema.dibujar_panel(pantalla, panel, radio=22)
    tema.dibujar_texto(pantalla, fuentes.subtitulo, "Pausado", tema.COLOR_TEXTO,
                       center=(ANCHO // 2, 215))
    tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_REANUDAR, "Reanudar", tema.COLOR_ACENTO)
    tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_AYUDA_PAUSA, "Ayuda", tema.COLOR_PANEL_CLARO)
    tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_ACCESIBILIDAD_PAUSA, "Accesibilidad", tema.COLOR_PANEL_CLARO)
    tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_SALIR_PAUSA, "Salir", tema.COLOR_BOTON_PELIGRO)

