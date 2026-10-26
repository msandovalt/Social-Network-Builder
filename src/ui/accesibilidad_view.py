"""
Pantalla de accesibilidad: elegir la paleta de colores para distintos tipos de
daltonismo. El cambio se aplica al instante (la propia pantalla cambia de color).

Cada opción muestra una vista previa con SUS colores (no los de la paleta
activa) para que puedas comparar, y cada muestra lleva una marca (✓ ✗ + !) para
recordar que en el juego el color nunca va solo: siempre hay una forma.
"""

import pygame

from ui import tema
from ui.hub_view import dibujar_boton_volver
from ui.paletas import OPCIONES, PALETAS
from ui.tema import ANCHO

RECTS_OPCION = [pygame.Rect(200, 150 + i * 92, 880, 84) for i in range(len(OPCIONES))]
Y_NOTA = 624
TAM_MUESTRA = 30

# Qué color y qué marca se muestran en la vista previa de cada opción
MUESTRAS = (("verde", "check"), ("rojo", "cruz"), ("amarillo", "mas"), ("naranja", "aviso"))


def _dibujar_marca(pantalla, tipo, centro, tinta):
    cx, cy = centro
    if tipo == "check":
        pygame.draw.line(pantalla, tinta, (cx - 7, cy), (cx - 2, cy + 6), 4)
        pygame.draw.line(pantalla, tinta, (cx - 2, cy + 6), (cx + 8, cy - 7), 4)
    elif tipo == "cruz":
        pygame.draw.line(pantalla, tinta, (cx - 6, cy - 6), (cx + 6, cy + 6), 4)
        pygame.draw.line(pantalla, tinta, (cx - 6, cy + 6), (cx + 6, cy - 6), 4)
    elif tipo == "mas":
        pygame.draw.line(pantalla, tinta, (cx - 7, cy), (cx + 7, cy), 4)
        pygame.draw.line(pantalla, tinta, (cx, cy - 7), (cx, cy + 7), 4)
    else:  # aviso
        pygame.draw.line(pantalla, tinta, (cx, cy - 8), (cx, cy + 2), 4)
        pygame.draw.circle(pantalla, tinta, (cx, cy + 8), 2)


def dibujar_accesibilidad(pantalla, fuentes, seleccionada, t):
    """`seleccionada` es el id de la paleta activa."""
    tema.dibujar_fondo(pantalla, t)
    tema.dibujar_texto(pantalla, fuentes.subtitulo, "Accesibilidad", tema.COLOR_TEXTO, midtop=(ANCHO // 2, 86))
    dibujar_boton_volver(pantalla, fuentes)
    tema.dibujar_texto(pantalla, fuentes.pequena,
                       "Elige la paleta que mejor veas. El cambio se aplica al instante.",
                       tema.COLOR_TEXTO_SEC, midtop=(ANCHO // 2, 122))

    for rect, (id_paleta, nombre, descripcion) in zip(RECTS_OPCION, OPCIONES):
        activa = id_paleta == seleccionada
        encima = tema.esta_encima(rect)
        relleno = tema.aclarar(tema.COLOR_PANEL, 0.06) if encima else tema.COLOR_PANEL
        tema.dibujar_panel(pantalla, rect, radio=16, color=relleno,
                           borde=tema.COLOR_ACENTO if activa else tema.COLOR_BORDE,
                           grosor=4 if activa else 2)

        # Botón de opción (radio)
        centro_radio = (rect.x + 36, rect.centery)
        pygame.draw.circle(pantalla, tema.COLOR_TEXTO_SEC, centro_radio, 12, width=3)
        if activa:
            pygame.draw.circle(pantalla, tema.COLOR_ACENTO, centro_radio, 7)

        tema.dibujar_texto(pantalla, fuentes.boton, nombre, tema.COLOR_TEXTO, topleft=(rect.x + 68, rect.y + 8))
        ancho_descripcion = rect.width - 68 - 24 - len(MUESTRAS) * (TAM_MUESTRA + 8) - 16
        y = rect.y + 38
        for linea in tema.envolver_texto(fuentes.pequena, descripcion, ancho_descripcion)[:2]:
            tema.dibujar_texto(pantalla, fuentes.pequena, linea, tema.COLOR_TEXTO_SEC, topleft=(rect.x + 68, y))
            y += 20

        # Vista previa con los colores de ESA opción
        paleta = PALETAS[id_paleta]
        x = rect.right - 24 - len(MUESTRAS) * (TAM_MUESTRA + 8) + 8
        for clave, marca in MUESTRAS:
            muestra = pygame.Rect(x, rect.centery - TAM_MUESTRA // 2, TAM_MUESTRA, TAM_MUESTRA)
            pygame.draw.rect(pantalla, paleta[clave], muestra, border_radius=8)
            _dibujar_marca(pantalla, marca, muestra.center, tema.color_sobre(paleta[clave]))
            x += TAM_MUESTRA + 8

    tema.dibujar_texto(pantalla, fuentes.pequena,
                       "El juego también usa íconos y formas (marcas, flechas, candados), no solo color.",
                       tema.COLOR_TEXTO_SEC, midtop=(ANCHO // 2, Y_NOTA))
