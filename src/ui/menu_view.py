"""
Pantallas de menú inicial y pausa.

Mantiene el mismo estilo simple del árbol preliminar; el objetivo aquí es
dar estructura al flujo del juego (menú -> jugando -> pausa), no la
estética final.
"""

import pygame

COLOR_FONDO = (25, 25, 30)
COLOR_TITULO = (255, 255, 255)
COLOR_BOTON_START = (60, 150, 130)
COLOR_BOTON_SALIR = (150, 70, 70)
COLOR_BOTON_TEXTO = (255, 255, 255)

RECT_BOTON_START = pygame.Rect(270, 220, 160, 50)
RECT_BOTON_PAUSA = pygame.Rect(650, 15, 30, 30)       # esquina superior derecha, durante el juego
RECT_BOTON_REANUDAR = pygame.Rect(270, 180, 160, 50)
RECT_BOTON_SALIR = pygame.Rect(270, 250, 160, 50)


def dibujar_menu(pantalla, fuente_titulo, fuente_boton):
    pantalla.fill(COLOR_FONDO)

    titulo = fuente_titulo.render("Social Network Builder", True, COLOR_TITULO)
    pantalla.blit(titulo, titulo.get_rect(center=(pantalla.get_width() // 2, 120)))

    pygame.draw.rect(pantalla, COLOR_BOTON_START, RECT_BOTON_START, border_radius=8)
    texto = fuente_boton.render("Start", True, COLOR_BOTON_TEXTO)
    pantalla.blit(texto, texto.get_rect(center=RECT_BOTON_START.center))


def dibujar_boton_pausa(pantalla, fuente):
    pygame.draw.rect(pantalla, (70, 70, 75), RECT_BOTON_PAUSA, border_radius=4)
    texto = fuente.render("II", True, (255, 255, 255))
    pantalla.blit(texto, texto.get_rect(center=RECT_BOTON_PAUSA.center))


def dibujar_pausa(pantalla, fuente_titulo, fuente_boton):
    """Se dibuja ENCIMA del estado del juego (que ya se dibujó antes),
    con un overlay semitransparente para que se note que está pausado."""
    overlay = pygame.Surface(pantalla.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    pantalla.blit(overlay, (0, 0))

    titulo = fuente_titulo.render("Pausado", True, (255, 255, 255))
    pantalla.blit(titulo, titulo.get_rect(center=(pantalla.get_width() // 2, 130)))

    pygame.draw.rect(pantalla, COLOR_BOTON_START, RECT_BOTON_REANUDAR, border_radius=8)
    texto_reanudar = fuente_boton.render("Reanudar", True, COLOR_BOTON_TEXTO)
    pantalla.blit(texto_reanudar, texto_reanudar.get_rect(center=RECT_BOTON_REANUDAR.center))

    pygame.draw.rect(pantalla, COLOR_BOTON_SALIR, RECT_BOTON_SALIR, border_radius=8)
    texto_salir = fuente_boton.render("Salir", True, COLOR_BOTON_TEXTO)
    pantalla.blit(texto_salir, texto_salir.get_rect(center=RECT_BOTON_SALIR.center))
