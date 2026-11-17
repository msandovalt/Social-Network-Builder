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

RECT_BOTON_START = pygame.Rect(_X_BOTON, 366, 260, 56)
RECT_BOTON_MULTIJUGADOR = pygame.Rect(_X_BOTON, 434, 260, 52)
RECT_BOTON_AYUDA_MENU = pygame.Rect(_X_BOTON, 498, 260, 52)
RECT_BOTON_ACCESIBILIDAD_MENU = pygame.Rect(_X_BOTON, 562, 260, 52)
RECT_BOTON_PAUSA = pygame.Rect(ANCHO - 24 - 48, 16, 48, 48)         # esquina superior derecha, durante el juego
RECT_BOTON_AYUDA_JUEGO = pygame.Rect(ANCHO - 24 - 48 - 12 - 48, 16, 48, 48)  # a la izquierda de la pausa
RECT_BOTON_REANUDAR = pygame.Rect(_X_BOTON, 232, 260, 50)
RECT_BOTON_AYUDA_PAUSA = pygame.Rect(_X_BOTON, 292, 260, 50)
RECT_BOTON_ACCESIBILIDAD_PAUSA = pygame.Rect(_X_BOTON, 352, 260, 50)
RECT_BOTON_MENU_PAUSA = pygame.Rect(_X_BOTON, 412, 260, 50)
RECT_BOTON_SALIR_PAUSA = pygame.Rect(_X_BOTON, 472, 260, 50)
RECT_BOTON_SALIR = pygame.Rect(_X_BOTON, 374, 260, 58)              # pantalla de fin de partida (compatibilidad)
RECT_BOTON_NUEVA = pygame.Rect(_X_BOTON, 300, 260, 58)              # pantalla de fin de partida (compatibilidad)


# (x_base, y_base, amp_x, amp_y, freq_x, freq_y, fase, clave_color)
_NODOS_FONDO = (
    (130, 120, 28, 22, 0.45, 0.38, 0.0, "dinero"),
    (290, 95, 24, 30, 0.35, 0.50, 1.1, "usuarios"),
    (110, 290, 32, 24, 0.52, 0.41, 2.2, "bienestar"),
    (260, 250, 22, 28, 0.40, 0.46, 3.0, "reputacion"),
    (140, 470, 30, 25, 0.48, 0.36, 0.7, "engagement"),
    (310, 430, 25, 30, 0.37, 0.52, 1.8, "usuarios"),
    (170, 620, 28, 20, 0.42, 0.44, 2.6, "dinero"),
    (360, 600, 24, 26, 0.50, 0.39, 3.9, "bienestar"),
    (990, 105, 26, 28, 0.44, 0.47, 0.4, "reputacion"),
    (1150, 130, 30, 22, 0.39, 0.49, 1.5, "usuarios"),
    (1010, 260, 24, 30, 0.51, 0.37, 2.8, "dinero"),
    (1170, 300, 28, 25, 0.43, 0.45, 3.4, "bienestar"),
    (970, 440, 26, 26, 0.47, 0.40, 1.2, "engagement"),
    (1140, 475, 30, 24, 0.36, 0.53, 2.1, "reputacion"),
    (930, 605, 25, 24, 0.49, 0.42, 0.9, "usuarios"),
    (1120, 625, 28, 22, 0.41, 0.48, 3.7, "dinero"),
)


def _dibujar_red_fondo(pantalla, t):
    """Grafo animado de nodos y aristas en el fondo del menú."""
    mx, my = pygame.mouse.get_pos() if pygame.display.get_init() else (-999, -999)
    posiciones = []
    colores = []
    for xb, yb, ax, ay, fx, fy, fase, clave in _NODOS_FONDO:
        x = xb + math.sin(t * fx + fase) * ax
        y = yb + math.cos(t * fy + fase * 1.3) * ay
        dx, dy = mx - x, my - y
        dist_m = math.hypot(dx, dy)
        if 1 < dist_m < 210:
            empuje = (1.0 - dist_m / 210.0) * 14.0
            x += (dx / dist_m) * empuje
            y += (dy / dist_m) * empuje
        posiciones.append((int(x), int(y)))
        colores.append(tema.COLOR_RECURSO.get(clave, tema.COLOR_ACENTO))

    color_arista = tema.mezclar(tema.COLOR_FONDO_ABAJO, tema.COLOR_BORDE, 0.55)
    color_pulso = tema.mezclar(tema.COLOR_FONDO_ABAJO, tema.COLOR_CIAN, 0.75)
    n = len(posiciones)
    for i in range(n):
        x1, y1 = posiciones[i]
        for j in range(i + 1, n):
            x2, y2 = posiciones[j]
            dist = math.hypot(x2 - x1, y2 - y1)
            if dist < 245:
                pygame.draw.line(pantalla, color_arista, (x1, y1), (x2, y2), 1)
                if (i + j) % 3 == 0:
                    u = (t * 0.35 + (i * 0.19 + j * 0.11)) % 1.0
                    px = int(x1 + (x2 - x1) * u)
                    py = int(y1 + (y2 - y1) * u)
                    pygame.draw.circle(pantalla, color_pulso, (px, py), 2)

    for (x, y), c in zip(posiciones, colores):
        suave = tema.mezclar(tema.COLOR_FONDO_ABAJO, c, 0.65)
        aro = tema.mezclar(tema.COLOR_FONDO_ABAJO, c, 0.28)
        pygame.draw.circle(pantalla, aro, (x, y), 9, width=1)
        pygame.draw.circle(pantalla, suave, (x, y), 4)


def dibujar_menu(pantalla, fuentes, t):
    tema.dibujar_fondo(pantalla, t)
    _dibujar_red_fondo(pantalla, t)

    flotar = math.sin(t * 1.5) * 4
    insignia = pygame.Rect(ANCHO // 2 - 190, int(166 + flotar * 0.5), 380, 30)
    pygame.draw.rect(pantalla, tema.COLOR_PANEL, insignia, border_radius=15)
    pygame.draw.rect(pantalla, tema.COLOR_ACENTO, insignia, width=1, border_radius=15)
    tema.dibujar_texto(pantalla, fuentes.arbol_pequena, "SIMULADOR DE REDES SOCIALES SALUDABLES",
                       tema.COLOR_CIAN, center=insignia.center)

    tema.dibujar_texto(pantalla, fuentes.titulo, "Social Network Builder",
                       tema.oscurecer(tema.COLOR_ACENTO, 0.55),
                       center=(ANCHO // 2 + 2, 243 + flotar))
    tema.dibujar_texto(pantalla, fuentes.titulo, "Social Network Builder", tema.COLOR_TEXTO,
                       center=(ANCHO // 2, 240 + flotar))
    tema.dibujar_texto(pantalla, fuentes.normal, "Construye tu red social. Cuida a tus usuarios.",
                       tema.COLOR_TEXTO_SEC, center=(ANCHO // 2, 310))

    tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_START, "Jugar", tema.COLOR_ACENTO, radio=16)
    tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_MULTIJUGADOR, "Multijugador (1v1)",
                       tema.COLOR_BOTON_OK, radio=16)
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
                       center=(ANCHO // 2, 196))
    tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_REANUDAR, "Reanudar", tema.COLOR_ACENTO)
    tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_AYUDA_PAUSA, "Ayuda", tema.COLOR_PANEL_CLARO)
    tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_ACCESIBILIDAD_PAUSA, "Accesibilidad", tema.COLOR_PANEL_CLARO)
    tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_MENU_PAUSA, "Menú principal", tema.COLOR_PANEL_CLARO)
    tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_SALIR_PAUSA, "Salir", tema.COLOR_BOTON_PELIGRO)

