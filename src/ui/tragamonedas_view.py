"""
Dibujo de la tragamonedas dentro del área central del hub.

Los rectángulos de los carretes y el botón de acción son constantes de
módulo (no cambian de posición), así main.py puede usarlos directamente
para detectar clics sin tener que recalcularlos cada frame.
"""

import pygame

from ui.hub_view import RECT_AREA_MINIJUEGO
from minijuego.tragamonedas import SIMBOLOS, COLORES, ETIQUETAS, GIRANDO, RESUELTO, INACTIVO

ANCHO_REEL = 90
ALTO_REEL = 90
ESPACIO = 40

_total_ancho = ANCHO_REEL * 3 + ESPACIO * 2
_x0 = RECT_AREA_MINIJUEGO.x + (RECT_AREA_MINIJUEGO.width - _total_ancho) // 2
_y0 = RECT_AREA_MINIJUEGO.y + 30

RECTS_REEL = [
    pygame.Rect(_x0 + i * (ANCHO_REEL + ESPACIO), _y0, ANCHO_REEL, ALTO_REEL)
    for i in range(3)
]
RECT_BOTON_ACCION = pygame.Rect(
    RECT_AREA_MINIJUEGO.centerx - 100, RECT_AREA_MINIJUEGO.bottom - 45, 200, 36
)

COLOR_BOTON_ACTIVO = (60, 150, 130)
COLOR_BOTON_INACTIVO = (90, 90, 90)
COLOR_BOTON_CERRAR = (70, 70, 75)


def dibujar_tragamonedas(pantalla, fuente, fuente_boton, fuente_simbolo, maquina, recursos):
    for i, rect in enumerate(RECTS_REEL):
        simbolo = SIMBOLOS[maquina.indices[i]]
        color = COLORES[simbolo]
        pygame.draw.rect(pantalla, color, rect, border_radius=8)

        etiqueta = fuente_simbolo.render(ETIQUETAS[simbolo], True, (255, 255, 255))
        pantalla.blit(etiqueta, etiqueta.get_rect(center=rect.center))

        if maquina.estado == GIRANDO and maquina.girando[i]:
            pista = fuente.render(f"[{i + 1}] Detener", True, (200, 200, 200))
            pantalla.blit(pista, pista.get_rect(midtop=(rect.centerx, rect.bottom + 6)))

    if maquina.estado == INACTIVO:
        costo = maquina.costo(recursos)
        puede_jugar = maquina.puede_jugar(recursos)
        color = COLOR_BOTON_ACTIVO if puede_jugar else COLOR_BOTON_INACTIVO
        pygame.draw.rect(pantalla, color, RECT_BOTON_ACCION, border_radius=8)
        texto = fuente_boton.render(f"Jugar (${costo})", True, (255, 255, 255))
        pantalla.blit(texto, texto.get_rect(center=RECT_BOTON_ACCION.center))

    elif maquina.estado == RESUELTO:
        mensaje = fuente_boton.render(maquina.mensaje_resultado, True, (255, 255, 255))
        pantalla.blit(mensaje, mensaje.get_rect(
            center=(RECT_AREA_MINIJUEGO.centerx, RECT_BOTON_ACCION.top - 20)
        ))
        pygame.draw.rect(pantalla, COLOR_BOTON_CERRAR, RECT_BOTON_ACCION, border_radius=8)
        texto = fuente_boton.render("Cerrar", True, (255, 255, 255))
        pantalla.blit(texto, texto.get_rect(center=RECT_BOTON_ACCION.center))
