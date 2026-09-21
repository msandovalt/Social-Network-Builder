"""
Pantalla principal (hub) del juego.

Muestra los recursos actuales y botones para entrar a los distintos paneles
(árbol de desarrollo, mapa de expansión). El área central queda reservada
para el futuro minijuego de habilidad ligado al bienestar; por ahora es
solo un espacio vacío marcado como placeholder.
"""

import pygame

COLOR_FONDO = (25, 25, 30)
COLOR_PANEL = (40, 40, 46)
COLOR_PLACEHOLDER_TEXTO = (140, 140, 145)
COLOR_BOTON = (60, 150, 130)
COLOR_TEXTO = (255, 255, 255)
COLOR_BOTON_VOLVER = (70, 70, 75)

RECT_BOTON_ARBOL = pygame.Rect(90, 350, 160, 44)
RECT_BOTON_MAPA = pygame.Rect(610, 350, 160, 44)
RECT_BOTON_VOLVER = pygame.Rect(15, 15, 90, 30)  # usado en Árbol y Mapa para volver a Principal
RECT_AREA_MINIJUEGO = pygame.Rect(90, 70, 680, 250)


def dibujar_principal(pantalla, fuente, fuente_boton, recursos):
    pantalla.fill(COLOR_FONDO)

    panel_recursos = fuente.render(
        f"Dinero: {recursos.dinero}   Usuarios: {recursos.usuarios}   "
        f"Bienestar: {recursos.bienestar}   Reputación: {recursos.reputacion}",
        True, COLOR_TEXTO,
    )
    pantalla.blit(panel_recursos, (20, 20))

    pygame.draw.rect(pantalla, COLOR_PANEL, RECT_AREA_MINIJUEGO, border_radius=10)

    pygame.draw.rect(pantalla, COLOR_BOTON, RECT_BOTON_ARBOL, border_radius=8)
    texto_arbol = fuente_boton.render("Árbol", True, COLOR_TEXTO)
    pantalla.blit(texto_arbol, texto_arbol.get_rect(center=RECT_BOTON_ARBOL.center))

    pygame.draw.rect(pantalla, COLOR_BOTON, RECT_BOTON_MAPA, border_radius=8)
    texto_mapa = fuente_boton.render("Mapa", True, COLOR_TEXTO)
    pantalla.blit(texto_mapa, texto_mapa.get_rect(center=RECT_BOTON_MAPA.center))


def dibujar_boton_volver(pantalla, fuente_boton):
    pygame.draw.rect(pantalla, COLOR_BOTON_VOLVER, RECT_BOTON_VOLVER, border_radius=6)
    texto = fuente_boton.render("< Volver", True, COLOR_TEXTO)
    pantalla.blit(texto, texto.get_rect(center=RECT_BOTON_VOLVER.center))


def dibujar_mapa_placeholder(pantalla, fuente_titulo):
    pantalla.fill(COLOR_FONDO)
    texto = fuente_titulo.render("Mapa de expansión — próximamente", True, (200, 200, 200))
    pantalla.blit(texto, texto.get_rect(center=(pantalla.get_width() // 2, pantalla.get_height() // 2)))
