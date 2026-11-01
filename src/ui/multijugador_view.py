"""
Pantalla de Sala Multijugador (1 vs 1 en línea / red) y widget de estado del
rival en vivo durante la partida.
"""

import pygame

from ui import tema
from ui.animacion import pulso
from ui.formato import formato_numero
from ui.hub_view import dibujar_boton_volver
from ui.tema import ANCHO, ALTO

RECT_PANEL_MULTI = pygame.Rect(ANCHO // 2 - 420, 146, 840, 510)
RECT_CAJA_HOST = pygame.Rect(RECT_PANEL_MULTI.x + 32, RECT_PANEL_MULTI.y + 84, 372, 320)
RECT_CAJA_CLIENTE = pygame.Rect(RECT_PANEL_MULTI.right - 32 - 372, RECT_PANEL_MULTI.y + 84, 372, 320)

RECT_BOTON_CREAR_SALA = pygame.Rect(RECT_CAJA_HOST.centerx - 130, RECT_CAJA_HOST.y + 72, 260, 48)
RECT_BOTON_ABRIR_VENTANA = pygame.Rect(RECT_CAJA_HOST.centerx - 130, RECT_CAJA_HOST.y + 258, 260, 44)
RECT_CAMPO_CODIGO = pygame.Rect(RECT_CAJA_CLIENTE.centerx - 130, RECT_CAJA_CLIENTE.y + 82, 260, 48)
RECT_BOTON_UNIRSE_SALA = pygame.Rect(RECT_CAJA_CLIENTE.centerx - 130, RECT_CAJA_CLIENTE.y + 146, 260, 48)
RECT_BOTON_DETECTAR_SALA = pygame.Rect(RECT_CAJA_CLIENTE.centerx - 130, RECT_CAJA_CLIENTE.y + 206, 260, 44)
RECT_BOTON_INICIAR_MULTI = pygame.Rect(ANCHO // 2 - 160, RECT_PANEL_MULTI.bottom - 76, 320, 54)


def dibujar_multijugador(pantalla, fuentes, multi, t):
    """Dibuja la sala de espera para crear o unirse a una carrera 1 vs 1."""
    tema.dibujar_fondo(pantalla, t)
    dibujar_boton_volver(pantalla, fuentes)

    tema.dibujar_texto(pantalla, fuentes.subtitulo, "Multijugador 1 vs 1 · Carrera Planetaria",
                       tema.COLOR_TEXTO, midtop=(ANCHO // 2, 86))

    tema.dibujar_panel(pantalla, RECT_PANEL_MULTI, radio=22)
    tema.dibujar_texto(
        pantalla,
        fuentes.normal,
        "Compite en vivo: cada uno construye su red y gana el primero en conquistar las 8 regiones.",
        tema.COLOR_TEXTO_SEC,
        center=(RECT_PANEL_MULTI.centerx, RECT_PANEL_MULTI.y + 42),
    )

    # --- Columna izquierda: Crear Sala (Anfitrión) ---------------------------
    borde_host = tema.COLOR_VERDE if multi.rol == "host" else tema.COLOR_BORDE
    tema.dibujar_panel(pantalla, RECT_CAJA_HOST, radio=16,
                       color=tema.oscurecer(tema.COLOR_PANEL, 0.25), borde=borde_host)
    tema.dibujar_texto(pantalla, fuentes.boton, "1. Anfitrión (Crear Sala)", tema.COLOR_TEXTO,
                       center=(RECT_CAJA_HOST.centerx, RECT_CAJA_HOST.y + 38))

    texto_btn_host = "Sala Activa" if multi.rol == "host" and multi.activo else "Crear Sala"
    tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_CREAR_SALA, texto_btn_host,
                       tema.COLOR_ACENTO, activo=(multi.rol == "host"))

    y_info = RECT_BOTON_CREAR_SALA.bottom + 16
    if multi.rol == "host" and multi.codigo_sala:
        tema.dibujar_texto(pantalla, fuentes.pequena, "Comparte este código con el Jugador 2:",
                           tema.COLOR_TEXTO_SEC, center=(RECT_CAJA_HOST.centerx, y_info))
        placa = pygame.Rect(RECT_CAJA_HOST.centerx - 110, y_info + 16, 220, 56)
        pygame.draw.rect(pantalla, tema.COLOR_PANEL, placa, border_radius=14)
        pygame.draw.rect(pantalla, tema.COLOR_AMARILLO, placa, width=3, border_radius=14)
        tema.dibujar_texto(pantalla, fuentes.subtitulo, multi.codigo_sala, tema.COLOR_AMARILLO,
                           center=placa.center)
        tema.dibujar_texto(pantalla, fuentes.arbol_pequena,
                           f"IP de red: {multi.ip_local}:{multi.puerto}",
                           tema.COLOR_TEXTO_SEC, center=(RECT_CAJA_HOST.centerx, placa.bottom + 16))
    else:
        for linea in ("Genera un código corto de 4 letras",
                      "para que otro jugador se conecte",
                      "desde la misma red o PC."):
            tema.dibujar_texto(pantalla, fuentes.pequena, linea, tema.COLOR_TEXTO_SEC,
                               center=(RECT_CAJA_HOST.centerx, y_info + 18))
            y_info += 24

    tema.dibujar_boton(pantalla, fuentes.pequena, RECT_BOTON_ABRIR_VENTANA,
                       "Abrir 2ª Ventana (Probar en este PC)", tema.COLOR_PANEL_CLARO)

    # --- Columna derecha: Unirse a Sala (Cliente) ----------------------------
    borde_cli = tema.COLOR_CIAN if multi.rol == "cliente" else tema.COLOR_BORDE
    tema.dibujar_panel(pantalla, RECT_CAJA_CLIENTE, radio=16,
                       color=tema.oscurecer(tema.COLOR_PANEL, 0.25), borde=borde_cli)
    tema.dibujar_texto(pantalla, fuentes.boton, "2. Invitado (Unirse)", tema.COLOR_TEXTO,
                       center=(RECT_CAJA_CLIENTE.centerx, RECT_CAJA_CLIENTE.y + 38))
    tema.dibujar_texto(pantalla, fuentes.arbol_pequena, "Escribe el código de 4 letras (o IP):",
                       tema.COLOR_TEXTO_SEC, center=(RECT_CAJA_CLIENTE.centerx, RECT_CAMPO_CODIGO.top - 14))

    # Caja de texto para el código
    pygame.draw.rect(pantalla, tema.COLOR_FONDO_ARRIBA, RECT_CAMPO_CODIGO, border_radius=10)
    pygame.draw.rect(pantalla, tema.COLOR_CIAN, RECT_CAMPO_CODIGO, width=2, border_radius=10)
    cursor = "|" if int(t * 2) % 2 == 0 else ""
    mostrado = (multi.codigo_entrada + cursor) if multi.codigo_entrada else ("Ej. A7K2" if int(t) % 2 == 0 else "")
    color_txt = tema.COLOR_TEXTO if multi.codigo_entrada else tema.COLOR_TEXTO_SEC
    tema.dibujar_texto(pantalla, fuentes.boton, mostrado, color_txt, center=RECT_CAMPO_CODIGO.center)

    tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_UNIRSE_SALA, "Conectar con Código",
                       tema.COLOR_BOTON_OK, habilitado=bool(multi.codigo_entrada.strip()))
    tema.dibujar_boton(pantalla, fuentes.pequena, RECT_BOTON_DETECTAR_SALA,
                       "Buscar Sala Automáticamente (LAN/PC)", tema.COLOR_PANEL_CLARO)

    # --- Estado de conexión y botón de iniciar carrera -----------------------
    color_est = tema.COLOR_VERDE if multi.conectado else tema.COLOR_AMARILLO
    tema.dibujar_texto(pantalla, fuentes.pequena, multi.mensaje_estado, color_est,
                       center=(RECT_PANEL_MULTI.centerx, RECT_CAJA_HOST.bottom + 20))

    tema.dibujar_boton(
        pantalla,
        fuentes.boton,
        RECT_BOTON_INICIAR_MULTI,
        "¡Iniciar Carrera 1 vs 1!",
        tema.COLOR_VERDE,
        habilitado=multi.conectado,
        activo=multi.conectado and pulso(t, 0.8) > 0.5,
    )


def dibujar_marcador_rival(pantalla, fuentes, multi, juego):
    """Widget compacto en vivo que compara tus regiones con las del rival."""
    if not getattr(multi, "conectado", False) or not getattr(multi, "partida_iniciada", False):
        return

    rival = multi.estado_rival
    mis_reg = len(juego.mundo.conquistadas())
    tot_reg = len(juego.mundo.regiones)
    riv_reg = int(rival.get("regiones", 1))
    riv_usr = int(rival.get("usuarios", 500))

    rect = pygame.Rect(24, 82, 356, 46)
    pygame.draw.rect(pantalla, tema.COLOR_PANEL, rect, border_radius=12)
    pygame.draw.rect(pantalla, tema.COLOR_CIAN, rect, width=2, border_radius=12)

    tema.dibujar_texto(
        pantalla,
        fuentes.arbol_pequena,
        f"1v1 · Tú: {mis_reg}/{tot_reg} reg.",
        tema.COLOR_VERDE,
        topleft=(rect.x + 12, rect.y + 5),
    )
    tema.dibujar_texto(
        pantalla,
        fuentes.arbol_pequena,
        f"Rival: {riv_reg}/{tot_reg} reg. ({formato_numero(riv_usr)} U)",
        tema.COLOR_ROSA,
        topright=(rect.right - 12, rect.y + 5),
    )

    # Doble barra de progreso de conquista
    barra_tu = pygame.Rect(rect.x + 12, rect.bottom - 16, (rect.width - 32) // 2, 7)
    barra_rv = pygame.Rect(barra_tu.right + 8, rect.bottom - 16, (rect.width - 32) // 2, 7)
    pygame.draw.rect(pantalla, tema.COLOR_PANEL_CLARO, barra_tu, border_radius=3)
    pygame.draw.rect(pantalla, tema.COLOR_PANEL_CLARO, barra_rv, border_radius=3)

    w_tu = max(4, int(barra_tu.width * min(1.0, mis_reg / max(1, tot_reg))))
    w_rv = max(4, int(barra_rv.width * min(1.0, riv_reg / max(1, tot_reg))))
    pygame.draw.rect(pantalla, tema.COLOR_VERDE,
                     pygame.Rect(barra_tu.x, barra_tu.y, w_tu, barra_tu.height), border_radius=3)
    pygame.draw.rect(pantalla, tema.COLOR_ROSA,
                     pygame.Rect(barra_rv.x, barra_rv.y, w_rv, barra_rv.height), border_radius=3)
