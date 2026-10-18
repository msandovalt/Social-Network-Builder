"""
Pantalla de ayuda: instrucciones del juego en páginas.

A la izquierda, una pestaña por tema; a la derecha, el contenido de la página
elegida con botones Anterior / Siguiente. El texto está en ayuda_contenido.py.
"""

import pygame

from ui import tema
from ui.ayuda_contenido import PAGINAS, TOTAL_PAGINAS, INDICE_ACCESIBILIDAD
from ui.hub_view import dibujar_boton_volver
from ui.tema import ANCHO

RECTS_TAB = [pygame.Rect(24, 140 + i * 62, 320, 52) for i in range(TOTAL_PAGINAS)]
RECT_PANEL_AYUDA = pygame.Rect(364, 140, 892, 556)
RECT_BOTON_ANTERIOR = pygame.Rect(396, 632, 160, 44)
RECT_BOTON_SIGUIENTE = pygame.Rect(1064, 632, 160, 44)
RECT_BOTON_ABRIR_ACCESIBILIDAD = pygame.Rect(396, 540, 320, 52)  # solo en la página de accesibilidad


def pagina_valida(pagina):
    """Mantiene el número de página dentro de los límites."""
    return max(0, min(TOTAL_PAGINAS - 1, pagina))


def dibujar_ayuda(pantalla, fuentes, pagina, t):
    pagina = pagina_valida(pagina)
    tema.dibujar_fondo(pantalla, t)
    tema.dibujar_texto(pantalla, fuentes.subtitulo, "Ayuda", tema.COLOR_TEXTO, midtop=(ANCHO // 2, 86))
    dibujar_boton_volver(pantalla, fuentes)

    for i, contenido in enumerate(PAGINAS):
        activa = i == pagina
        tema.dibujar_boton(pantalla, fuentes.normal, RECTS_TAB[i], contenido["titulo"],
                           tema.COLOR_ACENTO if activa else tema.COLOR_PANEL_CLARO, activo=activa, radio=12)

    panel = RECT_PANEL_AYUDA
    tema.dibujar_panel(pantalla, panel, radio=22)
    contenido = PAGINAS[pagina]
    x = panel.x + 36
    y = panel.y + 26
    tema.dibujar_texto(pantalla, fuentes.subtitulo, contenido["titulo"], tema.COLOR_TEXTO, topleft=(x, y))
    pygame.draw.line(pantalla, tema.COLOR_ACENTO, (x, y + 46), (x + 90, y + 46), 4)

    y = panel.y + 100
    ancho_texto = panel.width - 72 - 22
    for cabecera, texto in contenido["puntos"]:
        pygame.draw.circle(pantalla, tema.COLOR_ACENTO, (x + 6, y + 13), 6)
        tema.dibujar_texto(pantalla, fuentes.boton, cabecera, tema.COLOR_AMARILLO, topleft=(x + 22, y))
        y += 30
        for linea in tema.envolver_texto(fuentes.normal, texto, ancho_texto):
            tema.dibujar_texto(pantalla, fuentes.normal, linea, tema.COLOR_TEXTO, topleft=(x + 22, y))
            y += 25
        y += 14

    if pagina == INDICE_ACCESIBILIDAD:
        tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_ABRIR_ACCESIBILIDAD,
                           "Abrir accesibilidad", tema.COLOR_BOTON_OK)

    tema.dibujar_boton(pantalla, fuentes.normal, RECT_BOTON_ANTERIOR, "Anterior",
                       tema.COLOR_PANEL_CLARO, habilitado=pagina > 0)
    tema.dibujar_boton(pantalla, fuentes.normal, RECT_BOTON_SIGUIENTE, "Siguiente",
                       tema.COLOR_PANEL_CLARO, habilitado=pagina < TOTAL_PAGINAS - 1)
    tema.dibujar_texto(pantalla, fuentes.normal, f"{pagina + 1} / {TOTAL_PAGINAS}", tema.COLOR_TEXTO_SEC,
                       center=((RECT_BOTON_ANTERIOR.right + RECT_BOTON_SIGUIENTE.left) // 2,
                               RECT_BOTON_ANTERIOR.centery))
