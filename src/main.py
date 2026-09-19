"""
Punto de entrada del juego.

Flujo de pantallas: Menú -> Principal (hub) -> Árbol / Mapa, con Pausa
disponible desde cualquiera de las tres últimas. La pantalla Principal es
el hub del juego: muestra los recursos, la tragamonedas (minijuego de
habilidad que genera dinero/usuarios/reputación) y da acceso a los paneles
de Árbol y Mapa.
"""

import pygame

from tree.arbol import Arbol
from tree.recursos import Recursos
from tree.nodo import Nodo  # noqa: F401  (import usado indirectamente vía Arbol)
from minijuego.tragamonedas import Tragamonedas, GIRANDO, POR_RESOLVER, RESUELTO, INACTIVO

from ui.tree_view import dibujar_arbol, nodo_en_posicion
from ui.menu_view import (
    dibujar_menu, dibujar_boton_pausa, dibujar_pausa,
    RECT_BOTON_START, RECT_BOTON_PAUSA, RECT_BOTON_REANUDAR, RECT_BOTON_SALIR,
)
from ui.hub_view import (
    dibujar_principal, dibujar_boton_volver, dibujar_mapa_placeholder,
    RECT_BOTON_ARBOL, RECT_BOTON_MAPA, RECT_BOTON_VOLVER,
)
from ui.tragamonedas_view import dibujar_tragamonedas, RECTS_REEL, RECT_BOTON_ACCION

ANCHO, ALTO = 700, 420
FPS = 60

MENU = "menu"
PRINCIPAL = "principal"
ARBOL = "arbol"
MAPA = "mapa"
PAUSA = "pausa"

TECLAS_REEL = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}


def dibujar_fondo_juego(pantalla, estado, arbol, recursos, maquina, fuente, fuente_boton, fuente_titulo, fuente_simbolo):
    """Dibuja Principal, Árbol o Mapa. Se usa tanto para el estado activo
    como para el fondo congelado que se ve detrás del overlay de pausa."""
    if estado == PRINCIPAL:
        dibujar_principal(pantalla, fuente, fuente_boton, recursos)
        dibujar_tragamonedas(pantalla, fuente, fuente_boton, fuente_simbolo, maquina, recursos)
    elif estado == ARBOL:
        pantalla.fill((25, 25, 30))
        dibujar_arbol(pantalla, arbol, fuente)
        dibujar_boton_volver(pantalla, fuente_boton)
    elif estado == MAPA:
        dibujar_mapa_placeholder(pantalla, fuente_titulo)
        dibujar_boton_volver(pantalla, fuente_boton)


def manejar_click_tragamonedas(maquina, recursos, pos):
    for i, rect in enumerate(RECTS_REEL):
        if rect.collidepoint(pos) and maquina.estado == GIRANDO:
            maquina.detener(i)
            return

    if RECT_BOTON_ACCION.collidepoint(pos):
        if maquina.estado == INACTIVO:
            maquina.iniciar(recursos)
        elif maquina.estado == RESUELTO:
            maquina.reiniciar()


def main():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Social Network Builder")
    reloj = pygame.time.Clock()
    fuente = pygame.font.SysFont(None, 20)
    fuente_titulo = pygame.font.SysFont(None, 36)
    fuente_boton = pygame.font.SysFont(None, 24)
    fuente_simbolo = pygame.font.SysFont(None, 40)

    arbol = Arbol.construir_arbol_inicial()
    recursos = Recursos()
    maquina = Tragamonedas()

    estado = MENU
    estado_antes_pausa = None
    corriendo = True

    while corriendo:
        dt = reloj.tick(FPS) / 1000.0

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                corriendo = False

            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    if estado in (PRINCIPAL, ARBOL, MAPA):
                        estado_antes_pausa = estado
                        estado = PAUSA
                    elif estado == PAUSA:
                        estado = estado_antes_pausa
                elif estado == PRINCIPAL and evento.key in TECLAS_REEL:
                    if maquina.estado == GIRANDO:
                        maquina.detener(TECLAS_REEL[evento.key])

            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if estado == MENU:
                    if RECT_BOTON_START.collidepoint(evento.pos):
                        estado = PRINCIPAL

                elif estado == PRINCIPAL:
                    if RECT_BOTON_PAUSA.collidepoint(evento.pos):
                        estado_antes_pausa = PRINCIPAL
                        estado = PAUSA
                    elif RECT_BOTON_ARBOL.collidepoint(evento.pos):
                        estado = ARBOL
                    elif RECT_BOTON_MAPA.collidepoint(evento.pos):
                        estado = MAPA
                    else:
                        manejar_click_tragamonedas(maquina, recursos, evento.pos)

                elif estado == ARBOL:
                    if RECT_BOTON_PAUSA.collidepoint(evento.pos):
                        estado_antes_pausa = ARBOL
                        estado = PAUSA
                    elif RECT_BOTON_VOLVER.collidepoint(evento.pos):
                        estado = PRINCIPAL
                    else:
                        nodo = nodo_en_posicion(arbol, evento.pos)
                        if nodo:
                            nodo.desbloquear(recursos)

                elif estado == MAPA:
                    if RECT_BOTON_PAUSA.collidepoint(evento.pos):
                        estado_antes_pausa = MAPA
                        estado = PAUSA
                    elif RECT_BOTON_VOLVER.collidepoint(evento.pos):
                        estado = PRINCIPAL

                elif estado == PAUSA:
                    if RECT_BOTON_REANUDAR.collidepoint(evento.pos):
                        estado = estado_antes_pausa
                    elif RECT_BOTON_SALIR.collidepoint(evento.pos):
                        corriendo = False

        if estado == PRINCIPAL:
            maquina.actualizar(dt)
            if maquina.estado == POR_RESOLVER:
                maquina.resolver(recursos)

        if estado == MENU:
            dibujar_menu(pantalla, fuente_titulo, fuente_boton)

        elif estado == PAUSA:
            dibujar_fondo_juego(pantalla, estado_antes_pausa, arbol, recursos, maquina,
                                 fuente, fuente_boton, fuente_titulo, fuente_simbolo)
            dibujar_boton_pausa(pantalla, fuente)
            dibujar_pausa(pantalla, fuente_titulo, fuente_boton)

        else:  # PRINCIPAL, ARBOL o MAPA
            dibujar_fondo_juego(pantalla, estado, arbol, recursos, maquina,
                                 fuente, fuente_boton, fuente_titulo, fuente_simbolo)
            dibujar_boton_pausa(pantalla, fuente)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
