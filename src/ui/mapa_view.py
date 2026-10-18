"""
Pantalla del mapa: el planeta como grafo de regiones.

Cada región es un círculo; las líneas son las rutas entre regiones y llevan su
costo de expansión. Los colores dicen qué puedes hacer con cada región:
- verde: ya la conquistaste;
- amarillo (pulsa): vecina y con todos los requisitos cumplidos, puedes expandirte;
- naranja: vecina, pero todavía faltan requisitos;
- gris: lejana, no es vecina de ninguna región tuya.

Al elegir una región sin conquistar se resalta en amarillo la ruta más barata
hacia ella (Dijkstra) y el panel de la derecha muestra sus requisitos y la
diferencia entre saltos (BFS) y costo.
"""

import math

import pygame

from ui import tema
from ui.animacion import pulso
from ui.formato import formato_numero, formatear_efectos
from ui.hub_view import dibujar_base
from mapa.mundo import CONQUISTADA, DISPONIBLE, BLOQUEADA, LEJANA

RECT_MAPA = pygame.Rect(24, 136, 860, 560)
RECT_PANEL_REGION = pygame.Rect(904, 136, 352, 560)
RECT_BOTON_EXPANDIR = pygame.Rect(924, 636, 312, 48)

CENTRO_PLANETA = (454, 406)
RADIO_PLANETA = 262
RADIO_REGION = 34

POSICIONES_REGION = {
    "norteamerica": (304, 286),
    "centroamerica": (258, 404),
    "sudamerica": (344, 531),
    "europa": (464, 256),
    "africa": (470, 470),
    "medio_oriente": (560, 370),
    "asia": (616, 250),
    "oceania": (650, 470),
}

TEXTOS_ESTADO = {
    CONQUISTADA: "Conquistada",
    DISPONIBLE: "Disponible: puedes expandirte",
    BLOQUEADA: "Faltan requisitos",
    LEJANA: "Fuera de alcance",
}


def colores_estado():
    """Color de cada estado de región con la paleta activa."""
    return {
        CONQUISTADA: tema.COLOR_VERDE,
        DISPONIBLE: tema.COLOR_AMARILLO,
        BLOQUEADA: tema.COLOR_NARANJA,
        LEJANA: tema.COLOR_BLOQUEADO,
    }


Y_LEYENDA = 672


def region_en_posicion(mundo, pos):
    """Devuelve el id de la región bajo el mouse, o None."""
    for id_region in mundo.regiones:
        centro = POSICIONES_REGION.get(id_region)
        if centro is not None and math.hypot(pos[0] - centro[0], pos[1] - centro[1]) <= RADIO_REGION:
            return id_region
    return None


# --- planeta y rutas ------------------------------------------------------------
def _dibujar_planeta(pantalla):
    """Esfera hecha con círculos concéntricos que se desplazan hacia arriba a la
    izquierda: da la sensación de luz y volumen."""
    cx, cy = CENTRO_PLANETA
    pasos = 14
    salto = RADIO_PLANETA // pasos
    for i in range(pasos):
        color = tema.mezclar(tema.COLOR_FONDO_ARRIBA, tema.COLOR_PANEL_CLARO, i / (pasos - 1))
        pygame.draw.circle(pantalla, color, (cx - i, cy - i), RADIO_PLANETA - i * salto)
    pygame.draw.circle(pantalla, tema.COLOR_BORDE, CENTRO_PLANETA, RADIO_PLANETA, width=2)


def _etiqueta_costo(peso):
    return f"${peso / 1000:g}k".replace(".", ",")


# Desplazamiento (t sobre el segmento a->b, dx, dy) para las pastillas de costo
# que de otro modo chocarían con el nombre de una región vecina.
_DESPLAZAMIENTO_PASTILLA = {
    frozenset(("norteamerica", "centroamerica")): (0.35, -36, -6),
    frozenset(("centroamerica", "sudamerica")): (0.58, -24, 6),
    frozenset(("europa", "medio_oriente")): (0.62, 18, -8),
    frozenset(("africa", "medio_oriente")): (0.30, 34, 10),
    frozenset(("medio_oriente", "asia")): (0.42, -22, -8),
}


def _dibujar_rutas(pantalla, fuentes, mundo, aristas_ruta):
    pastillas = []
    for a, b, peso in mundo.grafo.aristas():
        pa, pb = POSICIONES_REGION.get(a), POSICIONES_REGION.get(b)
        if pa is None or pb is None:
            continue
        par = frozenset((a, b))
        if par in aristas_ruta:
            color, grosor = tema.COLOR_AMARILLO, 6
        elif mundo.regiones[a].conquistada and mundo.regiones[b].conquistada:
            color, grosor = tema.mezclar(tema.COLOR_VERDE, tema.COLOR_PANEL, 0.45), 5
        else:
            color, grosor = tema.COLOR_BORDE, 4
        pygame.draw.line(pantalla, color, pa, pb, grosor)
        t_seg, dx, dy = _DESPLAZAMIENTO_PASTILLA.get(par, (0.5, 0, 0))
        # Aseguramos orden determinista (alfabético) para aplicar t_seg de forma consistente
        p1, p2 = (pa, pb) if a < b else (pb, pa)
        px = int(p1[0] + (p2[0] - p1[0]) * t_seg) + dx
        py = int(p1[1] + (p2[1] - p1[1]) * t_seg) + dy
        pastillas.append((px, py, _etiqueta_costo(peso), color))

    # Los costos van encima de todas las líneas
    for x, y, texto, color in pastillas:
        ancho = fuentes.arbol_pequena.size(texto)[0] + 12
        rect = pygame.Rect(x - ancho // 2, y - 11, ancho, 22)
        pygame.draw.rect(pantalla, tema.COLOR_FONDO_ARRIBA, rect, border_radius=8)
        pygame.draw.rect(pantalla, color, rect, width=2, border_radius=8)
        tema.dibujar_texto(pantalla, fuentes.arbol_pequena, texto, tema.COLOR_TEXTO, center=rect.center)


# --- regiones -------------------------------------------------------------------
def _dibujar_icono_region(pantalla, estado, centro, relleno):
    """Cada estado tiene su propia forma, así no se distinguen solo por el color:
    check (conquistada), + (disponible), ! (faltan requisitos) y candado (lejana)."""
    cx, cy = centro
    if estado == CONQUISTADA:
        tinta = tema.color_sobre(relleno)
        pygame.draw.line(pantalla, tinta, (cx - 10, cy + 1), (cx - 3, cy + 9), 5)
        pygame.draw.line(pantalla, tinta, (cx - 3, cy + 9), (cx + 11, cy - 9), 5)
    elif estado == DISPONIBLE:
        pygame.draw.line(pantalla, tema.COLOR_AMARILLO, (cx - 10, cy), (cx + 10, cy), 5)
        pygame.draw.line(pantalla, tema.COLOR_AMARILLO, (cx, cy - 10), (cx, cy + 10), 5)
    elif estado == BLOQUEADA:
        tinta = tema.color_sobre(relleno)
        pygame.draw.line(pantalla, tinta, (cx, cy - 12), (cx, cy + 3), 5)
        pygame.draw.circle(pantalla, tinta, (cx, cy + 11), 3)
    else:  # lejana: candado
        color = tema.COLOR_TEXTO_SEC
        pygame.draw.rect(pantalla, color, pygame.Rect(cx - 10, cy - 1, 20, 15), border_radius=3)
        pygame.draw.line(pantalla, color, (cx - 6, cy - 1), (cx - 6, cy - 9), 3)
        pygame.draw.line(pantalla, color, (cx - 6, cy - 9), (cx + 6, cy - 9), 3)
        pygame.draw.line(pantalla, color, (cx + 6, cy - 9), (cx + 6, cy - 1), 3)


def _dibujar_region(pantalla, fuentes, region, estado, centro, seleccionada, t):
    color = colores_estado()[estado]
    encima = math.hypot(*(a - b for a, b in zip(pygame.mouse.get_pos(), centro))) <= RADIO_REGION

    if estado == DISPONIBLE:
        extra = int(pulso(t, 1.2) * 7)
        pygame.draw.circle(pantalla, tema.mezclar(color, tema.COLOR_TEXTO, pulso(t, 1.2)),
                           centro, RADIO_REGION + 8 + extra, width=2)
    if seleccionada:
        pygame.draw.circle(pantalla, tema.COLOR_TEXTO, centro, RADIO_REGION + 6, width=3)

    relleno = color if estado == CONQUISTADA else tema.oscurecer(color, 0.65)
    if encima:
        relleno = tema.aclarar(relleno, 0.18)
    pygame.draw.circle(pantalla, relleno, centro, RADIO_REGION)
    pygame.draw.circle(pantalla, color, centro, RADIO_REGION, width=4)
    _dibujar_icono_region(pantalla, estado, centro, relleno)

    tema.dibujar_texto(pantalla, fuentes.arbol, region.nombre, tema.COLOR_TEXTO,
                       midtop=(centro[0], centro[1] + RADIO_REGION + 6))


def _dibujar_leyenda(pantalla, fuentes):
    estados = (CONQUISTADA, DISPONIBLE, BLOQUEADA, LEJANA)
    fuente = fuentes.pequena
    separacion = 26
    anchos = [14 + 8 + fuente.size(TEXTOS_ESTADO[e])[0] for e in estados]
    x = RECT_MAPA.centerx - (sum(anchos) + separacion * (len(estados) - 1)) // 2
    for estado, ancho in zip(estados, anchos):
        pygame.draw.circle(pantalla, colores_estado()[estado], (x + 7, Y_LEYENDA + 7), 7)
        tema.dibujar_texto(pantalla, fuente, TEXTOS_ESTADO[estado], tema.COLOR_TEXTO_SEC,
                           midleft=(x + 22, Y_LEYENDA + 7))
        x += ancho + separacion


# --- panel de la región elegida ---------------------------------------------------
def _dibujar_marca(pantalla, centro, cumplido):
    cx, cy = centro
    pygame.draw.circle(pantalla, tema.COLOR_VERDE if cumplido else tema.COLOR_ROJO, centro, 10)
    if cumplido:
        pygame.draw.line(pantalla, tema.COLOR_FONDO_ARRIBA, (cx - 5, cy), (cx - 1, cy + 4), 3)
        pygame.draw.line(pantalla, tema.COLOR_FONDO_ARRIBA, (cx - 1, cy + 4), (cx + 5, cy - 4), 3)
    else:
        pygame.draw.line(pantalla, tema.COLOR_FONDO_ARRIBA, (cx - 4, cy - 4), (cx + 4, cy + 4), 3)
        pygame.draw.line(pantalla, tema.COLOR_FONDO_ARRIBA, (cx - 4, cy + 4), (cx + 4, cy - 4), 3)


def texto_requisito(requisito):
    """Texto legible de un requisito (se usa en el panel y se puede probar aparte)."""
    if requisito.tipo == "vecina":
        return "Región vecina a una tuya"
    if requisito.tipo == "nodo":
        return f"Nodo «{requisito.etiqueta}»"
    if requisito.tipo == "usuarios":
        return f"Usuarios: {formato_numero(requisito.actual)} / {formato_numero(requisito.necesario)}"
    if requisito.tipo == "reputacion":
        return f"Reputación: {formato_numero(requisito.actual)} / {formato_numero(requisito.necesario)}"
    if requisito.tipo == "bienestar":
        return f"Bienestar: {formato_numero(requisito.actual)} / {formato_numero(requisito.necesario)}"
    return f"Pagar ${formato_numero(requisito.necesario)} (tienes ${formato_numero(requisito.actual)})"


def _dibujar_panel_vacio(pantalla, juego):
    f = juego.fuentes
    r = RECT_PANEL_REGION
    total = len(juego.mundo.regiones)
    tema.dibujar_texto(pantalla, f.subtitulo, "Planeta", tema.COLOR_TEXTO, topleft=(r.x + 24, r.y + 20))
    tema.dibujar_texto(pantalla, f.normal, f"Regiones conquistadas: {len(juego.mundo.conquistadas())} / {total}",
                       tema.COLOR_VERDE, topleft=(r.x + 24, r.y + 66))
    y = r.y + 104
    for parrafo in ("Objetivo: conquistar todo el planeta para ganar.",
                    "Elige una región para ver qué necesita.",
                    "Solo puedes expandirte a regiones vecinas de las que ya tienes.",
                    "Lo que desbloquees en el árbol decide hasta dónde puedes llegar.",
                    "Cada región suma capacidad: sin expandirte, tu red deja de crecer.",
                    "Cuida a tus usuarios: sin bienestar no puedes expandirte."):
        for linea in tema.envolver_texto(f.normal, parrafo, r.width - 48):
            tema.dibujar_texto(pantalla, f.normal, linea, tema.COLOR_TEXTO_SEC, topleft=(r.x + 24, y))
            y += 24
        y += 8


def _dibujar_panel_region(pantalla, juego, id_region):
    tema.dibujar_panel(pantalla, RECT_PANEL_REGION, radio=20)
    if id_region is None:
        _dibujar_panel_vacio(pantalla, juego)
        return

    f, mundo = juego.fuentes, juego.mundo
    region = mundo.regiones[id_region]
    estado = mundo.estado_region(id_region, juego.arbol, juego.recursos)
    r = RECT_PANEL_REGION
    x = r.x + 24
    ancho_texto = r.width - 48
    y = r.y + 20

    tema.dibujar_texto(pantalla, f.subtitulo, region.nombre, tema.COLOR_TEXTO, topleft=(x, y))
    y += 38

    texto_chip = TEXTOS_ESTADO[estado]
    chip = pygame.Rect(x, y, f.pequena.size(texto_chip)[0] + 24, 26)
    relleno_chip = colores_estado()[estado]
    pygame.draw.rect(pantalla, relleno_chip, chip, border_radius=13)
    color_chip = tema.color_sobre(relleno_chip)
    tema.dibujar_texto(pantalla, f.pequena, texto_chip, color_chip, center=chip.center)
    y += 32

    for linea in tema.envolver_texto(f.pequena, region.descripcion, ancho_texto):
        tema.dibujar_texto(pantalla, f.pequena, linea, tema.COLOR_TEXTO, topleft=(x, y))
        y += 22
    y += 4

    for linea in tema.envolver_texto(f.pequena, "Cada ronda: " + formatear_efectos(region.ingreso), ancho_texto):
        tema.dibujar_texto(pantalla, f.pequena, linea, tema.COLOR_CIAN, topleft=(x, y))
        y += 22
    tema.dibujar_texto(pantalla, f.pequena, f"Capacidad: +{formato_numero(region.capacidad)} usuarios",
                       tema.COLOR_AMARILLO, topleft=(x, y))
    y += 24

    if estado == CONQUISTADA:
        tema.dibujar_texto(pantalla, f.normal, "Esta región ya es tuya.", tema.COLOR_VERDE, topleft=(x, y))
        return

    tema.dibujar_texto(pantalla, f.boton, "Requisitos", tema.COLOR_TEXTO, topleft=(x, y))
    y += 26
    for requisito in mundo.requisitos(id_region, juego.arbol, juego.recursos):
        lineas = tema.envolver_texto(f.pequena, texto_requisito(requisito), ancho_texto - 32)
        _dibujar_marca(pantalla, (x + 10, y + 10), requisito.cumplido)
        for linea in lineas:
            tema.dibujar_texto(pantalla, f.pequena, linea, tema.COLOR_TEXTO, topleft=(x + 32, y + 1))
            y += 22
        y += 4

    # Ruta más barata (Dijkstra) y saltos (BFS). Para una región vecina la ruta es
    # directa y su costo ya aparece en los requisitos, así que solo se muestra
    # cuando hay regiones intermedias.
    costo, camino = mundo.ruta_mas_barata(id_region)
    if len(camino) > 2:
        y += 2
        nombres = " → ".join(mundo.regiones[i].nombre for i in camino)
        for linea in tema.envolver_texto(f.pequena, f"Ruta: {nombres}", ancho_texto):
            tema.dibujar_texto(pantalla, f.pequena, linea, tema.COLOR_AMARILLO, topleft=(x, y))
            y += 22
        saltos = mundo.saltos().get(id_region)
        tema.dibujar_texto(pantalla, f.pequena, f"Costo ${formato_numero(costo)} · {saltos} saltos",
                           tema.COLOR_TEXTO_SEC, topleft=(x, y))

    puede = estado == DISPONIBLE
    costo_expansion = mundo.costo_expansion(id_region)
    texto_boton = f"Expandir (${formato_numero(costo_expansion)})" if costo_expansion else "Expandir"
    tema.dibujar_boton(pantalla, f.boton, RECT_BOTON_EXPANDIR, texto_boton, tema.COLOR_BOTON_OK,
                       habilitado=puede)


# --- pantalla completa -------------------------------------------------------------
def dibujar_mapa(pantalla, juego):
    fuentes, mundo = juego.fuentes, juego.mundo
    seleccion = juego.region_seleccionada

    dibujar_base(pantalla, juego, "Mapa de expansión")
    tema.dibujar_panel(pantalla, RECT_MAPA, radio=22)
    _dibujar_planeta(pantalla)
    tema.dibujar_texto(pantalla, fuentes.normal,
                       f"Regiones: {len(mundo.conquistadas())} / {len(mundo.regiones)}",
                       tema.COLOR_TEXTO, topleft=(RECT_MAPA.x + 22, RECT_MAPA.y + 16))

    ruta = []
    if seleccion is not None and not mundo.regiones[seleccion].conquistada:
        _, ruta = mundo.ruta_mas_barata(seleccion)
    _dibujar_rutas(pantalla, fuentes, mundo, {frozenset(par) for par in zip(ruta, ruta[1:])})

    for id_region, region in mundo.regiones.items():
        centro = POSICIONES_REGION.get(id_region)
        if centro is None:
            continue
        estado = mundo.estado_region(id_region, juego.arbol, juego.recursos)
        _dibujar_region(pantalla, fuentes, region, estado, centro, id_region == seleccion, juego.tiempo)

    _dibujar_leyenda(pantalla, fuentes)
    _dibujar_panel_region(pantalla, juego, seleccion)
