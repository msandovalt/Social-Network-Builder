"""
Pantalla principal (hub) del juego y encabezado compartido.

El encabezado (tarjetas de recursos con valores animados, indicador de ronda)
se dibuja igual en Principal, Árbol y Mapa. El área central del hub aloja la
tragamonedas; los botones inferiores llevan al Árbol y al Mapa.

Las funciones que reciben `juego` solo necesitan que tenga `fuentes`,
`contadores`, `rondas` y `tiempo` (ver juego.Juego).
"""

import math

import pygame

from ui import tema
from ui.formato import formato_numero
from ui.modelos_2d import dibujar_modelo_recurso
from ui.tema import ANCHO
from tree.ronda import UMBRAL_FUGA, balance_por_ronda

MARGEN = 24
Y_TARJETAS = 14
ANCHO_TARJETA = 204
ALTO_TARJETA = 64
ESPACIO_TARJETAS = 10

RECT_BOTON_VOLVER = pygame.Rect(MARGEN, 88, 130, 38)  # usado en Árbol y Mapa para volver a Principal
RECT_AREA_MINIJUEGO = pygame.Rect(220, 140, 840, 440)
RECT_BOTON_ARBOL = pygame.Rect(120, 604, 210, 60)
RECT_BOTON_BIENESTAR = pygame.Rect(348, 604, 240, 60)
RECT_CAMPANIA_CONFIRMAR = pygame.Rect(348, 604, 115, 60)
RECT_CAMPANIA_CANCELAR = pygame.Rect(473, 604, 115, 60)
RECT_BOTON_MAPA = pygame.Rect(606, 604, 210, 60)
RECT_MINI_FEED = pygame.Rect(834, 600, 326, 68)

# (clave en Recursos, etiqueta, ¿es una escala 0-100?). El color de cada recurso
# sale de la paleta activa: tema.COLOR_RECURSO[clave].
TARJETAS = (
    ("dinero", "Dinero", False),
    ("usuarios", "Usuarios", False),
    ("bienestar", "Bienestar", True),
    ("reputacion", "Reputación", True),
    ("engagement", "Engagement", True),
)


def _formatear_tasa(clave, delta):
    """Formatea el cambio neto por ronda (ej. '+$120/r', '-6/r'). '' si es ~0."""
    redondeado = int(round(delta))
    if redondeado == 0:
        return ""
    signo = "+" if redondeado > 0 else "-"
    abs_txt = formato_numero(abs(redondeado))
    if clave == "dinero":
        return f"{signo}${abs_txt}/r"
    return f"{signo}{abs_txt}/r"


def _dibujar_icono_recurso(pantalla, fuentes, clave, centro, color):
    """Dibuja el modelo 2D multicapa de cada recurso dentro de la insignia."""
    dibujar_modelo_recurso(pantalla, clave, centro, 11, color)


def _dibujar_tarjeta(pantalla, fuentes, rect, etiqueta, color, contador, clave, es_escala, limite=None, delta_ronda=0):
    tema.dibujar_panel(pantalla, rect, radio=14)

    # Insignia con icono vectorial a la izquierda
    badge = pygame.Rect(rect.x + 10, rect.y + 10, 30, 30)
    pygame.draw.rect(pantalla, tema.oscurecer(color, 0.65), badge, border_radius=8)
    pygame.draw.rect(pantalla, color, badge, width=2, border_radius=8)
    _dibujar_icono_recurso(pantalla, fuentes, clave, badge.center, color)

    valor = contador.valor
    if clave == "dinero":
        texto = f"-${formato_numero(abs(valor))}" if valor < 0 else f"${formato_numero(valor)}"
    else:
        texto = formato_numero(valor)

    # Verde mientras sube, rojo mientras baja
    lleno = limite is not None and valor >= limite
    if lleno:  # el mercado de tus regiones está completo: hay que expandirse para crecer
        color_valor = tema.COLOR_AMARILLO
    elif contador.direccion > 0:
        color_valor = tema.COLOR_VERDE
    elif contador.direccion < 0 or (clave == "dinero" and valor < 0):
        color_valor = tema.COLOR_ROJO
    else:
        color_valor = tema.COLOR_TEXTO

    x_texto = rect.x + 46
    color_etiqueta = tema.COLOR_TEXTO_SEC
    if clave == "bienestar" and valor < UMBRAL_FUGA:  # los usuarios se están yendo
        etiqueta, color_etiqueta = "Bienestar (bajo)", tema.COLOR_ROJO
    tema.dibujar_texto(pantalla, fuentes.pequena, etiqueta, color_etiqueta,
                       topleft=(x_texto, rect.y + 5))
    rect_valor = tema.dibujar_texto(pantalla, fuentes.boton, texto, color_valor,
                                    topleft=(x_texto, rect.y + 21))
    if contador.direccion != 0:  # la flecha cuenta lo mismo que el color: sube o baja
        _dibujar_flecha(pantalla, (rect_valor.right + 12, rect_valor.centery), contador.direccion > 0, color_valor)

    texto_tasa = _formatear_tasa(clave, delta_ronda)
    if texto_tasa:
        color_tasa = tema.COLOR_VERDE if delta_ronda > 0 else tema.COLOR_ROJO
        tema.dibujar_texto(pantalla, fuentes.arbol_pequena, texto_tasa, color_tasa,
                           topright=(rect.right - 10, rect.y + 6))

    if limite is not None:
        tema.dibujar_texto(pantalla, fuentes.arbol_pequena, f"/{formato_numero(limite)}",
                           tema.COLOR_AMARILLO if lleno else tema.COLOR_TEXTO_SEC,
                           topright=(rect.right - 10, rect.y + 26))

    # Barra inferior de progreso / capacidad
    barra = pygame.Rect(rect.x + 10, rect.bottom - 10, rect.width - 20, 5)
    pygame.draw.rect(pantalla, tema.COLOR_PANEL_CLARO, barra, border_radius=3)
    if es_escala:
        proporcion = max(0.0, min(1.0, valor / 100.0))
    elif limite is not None:
        proporcion = max(0.0, min(1.0, valor / max(1, limite)))
    else:
        proporcion = max(0.0, min(1.0, valor / 20000.0))

    if proporcion > 0:
        relleno = pygame.Rect(barra.x, barra.y, max(4, int(barra.width * proporcion)), barra.height)
        if es_escala and valor < UMBRAL_FUGA:
            color_barra = tema.COLOR_ROJO
        elif lleno:
            color_barra = tema.COLOR_AMARILLO
        else:
            color_barra = color
        pygame.draw.rect(pantalla, color_barra, relleno, border_radius=3)

    if clave == "bienestar":
        x_umbral = barra.x + int(barra.width * (UMBRAL_FUGA / 100.0))
        pygame.draw.line(pantalla, tema.COLOR_ROJO, (x_umbral, barra.y - 1), (x_umbral, barra.bottom), 2)


def _dibujar_flecha(pantalla, centro, hacia_arriba, color):
    """Triángulo que indica si un valor está subiendo o bajando (no depende del color)."""
    x, y = centro
    if hacia_arriba:
        puntos = [(x - 7, y + 5), (x + 7, y + 5), (x, y - 7)]
    else:
        puntos = [(x - 7, y - 5), (x + 7, y - 5), (x, y + 7)]
    pygame.draw.polygon(pantalla, color, puntos)


def dibujar_encabezado(pantalla, juego, titulo):
    """Tarjetas de recursos, título de la pantalla e indicador de ronda."""
    fuentes = juego.fuentes
    tasas = {}
    if hasattr(juego, "arbol") and hasattr(juego, "recursos"):
        tasas = balance_por_ronda(juego.arbol, juego.recursos, getattr(juego, "mundo", None))

    for i, (clave, etiqueta, es_escala) in enumerate(TARJETAS):
        color = tema.COLOR_RECURSO[clave]
        rect = pygame.Rect(MARGEN + i * (ANCHO_TARJETA + ESPACIO_TARJETAS), Y_TARJETAS,
                           ANCHO_TARJETA, ALTO_TARJETA)
        limite = juego.recursos.limite_usuarios if clave == "usuarios" else None
        _dibujar_tarjeta(pantalla, fuentes, rect, etiqueta, color, juego.contadores[clave],
                         clave, es_escala, limite, delta_ronda=tasas.get(clave, 0))

    tema.dibujar_texto(pantalla, fuentes.subtitulo, titulo, tema.COLOR_TEXTO, midtop=(ANCHO // 2, 86))

    rondas = juego.rondas
    crecimiento = juego.recursos.crecimiento * 100
    tema.dibujar_texto(pantalla, fuentes.pequena,
                       f"Ronda {rondas.numero}   ·   Crecimiento pasivo {crecimiento:.0f}%",
                       tema.COLOR_TEXTO_SEC, topright=(ANCHO - MARGEN, 84))
    _dibujar_barra(pantalla, 108, 1 - rondas.segundos_restantes() / rondas.duracion, tema.COLOR_ACENTO)
    if getattr(getattr(juego, "audio", None), "mute", False):
        tema.dibujar_texto(pantalla, fuentes.pequena, "[M] Silenciado", tema.COLOR_AMARILLO,
                           midright=(ANCHO - MARGEN - 240 - 10, 107))


def _dibujar_barra(pantalla, y, progreso, color):
    barra = pygame.Rect(ANCHO - MARGEN - 240, y, 240, 6)
    pygame.draw.rect(pantalla, tema.COLOR_PANEL_CLARO, barra, border_radius=3)
    if progreso > 0:
        relleno = pygame.Rect(barra.x, barra.y, max(6, int(barra.width * min(1.0, progreso))), barra.height)
        pygame.draw.rect(pantalla, color, relleno, border_radius=3)


def dibujar_base(pantalla, juego, titulo):
    """Fondo animado + encabezado: la base común de Principal, Árbol y Mapa."""
    tema.dibujar_fondo(pantalla, juego.tiempo)
    dibujar_encabezado(pantalla, juego, titulo)


def generar_comentarios_comunidad(juego):
    """Genera una lista de tuplas (autor, mensaje, tono) según el estado real
    de la partida (bienestar, nodos activos, regiones y último evento)."""
    recursos = getattr(juego, "recursos", None)
    arbol = getattr(juego, "arbol", None)
    mundo = getattr(juego, "mundo", None)
    eventos = getattr(juego, "eventos", None)
    comentarios = []

    if eventos is not None and getattr(eventos, "ultimo", None) is not None:
        ev = eventos.ultimo.evento
        tono = "positivo" if ev.tono == "positivo" else "negativo"
        comentarios.append(("@noticias_red", f"Último suceso: {ev.titulo}", tono))

    if recursos is not None:
        if recursos.bienestar < UMBRAL_FUGA:
            comentarios.append(("@ana_99", "El ambiente es agotador, estoy pensando cerrar mi cuenta...", "negativo"))
            comentarios.append(("@carlos_ux", "Demasiada toxicidad y estrés en el feed últimamente.", "negativo"))
        elif recursos.bienestar >= 72:
            comentarios.append(("@elena_v", "Qué buena comunidad hay aquí, da gusto conectarse.", "positivo"))
            comentarios.append(("@marco_dev", "Se nota que cuidan el bienestar de los usuarios.", "positivo"))
        else:
            comentarios.append(("@dani_m", "La plataforma crece rápido, veremos cómo evoluciona.", "neutro"))

    if arbol is not None:
        scroll = arbol.nodo_por_id("feed_scroll")
        if scroll is not None and scroll.desbloqueado and scroll.activo:
            comentarios.append(("@sofi_m", "Llevo horas haciendo scroll sin poder parar...", "negativo"))
        alg = arbol.nodo_por_id("feed_algoritmo")
        if alg is not None and alg.desbloqueado and alg.valor >= 60:
            comentarios.append(("@leo_tech", f"El algoritmo al {alg.valor}% engancha, pero satura un poco.", "neutro"))
        seg = arbol.nodo_por_id("seguridad_avanzada")
        if seg is not None and seg.desbloqueado and seg.variante_actual:
            comentarios.append(("@vera_sec", "La moderación activa mantiene la red mucho más sana.", "positivo"))

    if mundo is not None and recursos is not None:
        conquistadas = mundo.conquistadas()
        if conquistadas:
            ultima = mundo.regiones[conquistadas[-1]].nombre
            comentarios.append((f"@{conquistadas[-1]}", f"¡Saludos desde {ultima}! Ya somos {formato_numero(recursos.usuarios)}.", "positivo"))

    if not comentarios:
        comentarios.append(("@comunidad", "Tu red social acaba de nacer en Sudamérica.", "neutro"))
    return comentarios


def _dibujar_mini_feed(pantalla, juego):
    """Panel compacto entre los botones Árbol y Mapa con reacciones en vivo."""
    rect = RECT_MINI_FEED
    fuentes = juego.fuentes
    comentarios = generar_comentarios_comunidad(juego)
    idx = int(getattr(juego, "tiempo", 0.0) // 4.0) % len(comentarios)
    autor, mensaje, tono = comentarios[idx]

    if tono == "negativo":
        color_tono = tema.COLOR_ROJO
    elif tono == "positivo":
        color_tono = tema.COLOR_VERDE
    else:
        color_tono = tema.COLOR_ACENTO

    tema.dibujar_panel(pantalla, rect, radio=14, color=tema.COLOR_PANEL, borde=tema.COLOR_BORDE)
    # Avatar circular con inicial
    cx, cy = rect.x + 22, rect.centery + 2
    pygame.draw.circle(pantalla, color_tono, (cx, cy), 13)
    inicial = autor[1:2].upper() if len(autor) > 1 else "U"
    tema.dibujar_texto(pantalla, fuentes.arbol_pequena, inicial, tema.color_sobre(color_tono), center=(cx, cy))

    # Encabezado: autor + indicadores de carrusel
    tema.dibujar_texto(pantalla, fuentes.arbol_pequena, f"Pulso · {autor}", color_tono,
                       topleft=(rect.x + 42, rect.y + 8))
    for k in range(min(5, len(comentarios))):
        px = rect.right - 14 - (min(5, len(comentarios)) - 1 - k) * 9
        py = rect.y + 15
        c_punto = color_tono if k == (idx % min(5, len(comentarios))) else tema.COLOR_BORDE
        pygame.draw.circle(pantalla, c_punto, (px, py), 3)

    # Mensaje recortado a dos líneas compactas dentro de la tarjeta
    ancho_max = rect.width - 52
    lineas = tema.envolver_texto(fuentes.arbol_pequena, mensaje, ancho_max)[:2]
    for i, linea in enumerate(lineas):
        tema.dibujar_texto(pantalla, fuentes.arbol_pequena, linea, tema.COLOR_TEXTO,
                           topleft=(rect.x + 42, rect.y + 27 + i * 17))


def dibujar_principal(pantalla, juego):
    fuentes = juego.fuentes
    dibujar_base(pantalla, juego, "Panel principal")
    mundo = juego.mundo
    multi = getattr(juego, "multi", None)
    if multi is not None and multi.conectado and multi.partida_iniciada:
        from ui.multijugador_view import dibujar_marcador_rival
        dibujar_marcador_rival(pantalla, fuentes, multi, juego)
    else:
        if mundo.todas_conquistadas():
            objetivo = (f"Objetivo final: llenar la comunidad "
                        f"({juego.recursos.usuarios:,}/{mundo.capacidad_total():,})").replace(",", ".")
        else:
            objetivo = f"Objetivo: conquistar el planeta ({len(mundo.conquistadas())}/{len(mundo.regiones)})"
        tema.dibujar_texto(pantalla, fuentes.normal, objetivo,
                           tema.COLOR_TEXTO_SEC, topleft=(MARGEN, 96))
    tema.dibujar_panel(pantalla, RECT_AREA_MINIJUEGO, radio=22)
    tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_ARBOL, "Árbol", tema.COLOR_ACENTO, radio=16)
    costo_campania = juego.costo_campania_marca()
    if juego.campania_marca_pendiente:
        tema.dibujar_texto(
            pantalla, fuentes.pequena,
            f"¿Invertir ${formato_numero(costo_campania)}? +5 bienestar y +3 reputación",
            tema.COLOR_TEXTO_SEC, center=(ANCHO // 2, 590),
        )
        tema.dibujar_boton(pantalla, fuentes.pequena, RECT_CAMPANIA_CONFIRMAR,
                           "Confirmar", tema.COLOR_BOTON_OK,
                           habilitado=juego.puede_aplicar_campania_marca(), radio=12)
        tema.dibujar_boton(pantalla, fuentes.pequena, RECT_CAMPANIA_CANCELAR,
                           "Cancelar", tema.COLOR_BOTON_PELIGRO, radio=12)
    else:
        disponible = juego.puede_aplicar_campania_marca()
        nodo_campana = juego.arbol.nodo_por_id("marketing_campana")
        if not nodo_campana.desbloqueado:
            estado_campania = "Desbloquea Campaña de marca en el árbol"
        elif juego.rondas_hasta_campania_disponible() > 0:
            faltan_rondas = juego.rondas_hasta_campania_disponible()
            estado_campania = f"Disponible en {faltan_rondas} rondas"
        elif juego.recursos.bienestar >= 100 and juego.recursos.reputacion >= 100:
            estado_campania = "Bienestar y reputación al máximo"
        elif juego.recursos.dinero < costo_campania:
            estado_campania = f"Faltan ${formato_numero(costo_campania - juego.recursos.dinero)}"
        else:
            estado_campania = f"Invierte ${formato_numero(costo_campania)}: +5 bienestar y +3 reputación"
        tema.dibujar_texto(pantalla, fuentes.pequena, estado_campania,
                           tema.COLOR_TEXTO_SEC, center=(RECT_BOTON_BIENESTAR.centerx, 590))
        tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_BIENESTAR,
                           "Campaña de marca", tema.COLOR_BOTON_OK,
                           habilitado=disponible, radio=16)
    tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_MAPA, "Mapa", tema.COLOR_ACENTO, radio=16)
    _dibujar_mini_feed(pantalla, juego)
    tema.dibujar_texto(pantalla, fuentes.pequena, "Pulsa el botón ? de arriba para ver la ayuda",
                       tema.COLOR_TEXTO_SEC, center=(ANCHO // 2, 692))


def dibujar_boton_volver(pantalla, fuentes):
    tema.dibujar_boton(pantalla, fuentes.normal, RECT_BOTON_VOLVER, "< Volver", tema.COLOR_PANEL_CLARO, radio=10)
