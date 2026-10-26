"""
Modelos 2D vectoriales de alta definición para los 5 símbolos de recursos
(Dinero, Usuarios, Bienestar, Reputación, Engagement) y el Mapa Mundial 2D.

Todos los modelos se construyen con geometría 2D multicapa (sombra proyectada,
cuerpo biselado, facetas de iluminación, reflejos especulares y detalles
internos) y se almacenan en caché según el tamaño y el color activo de la
paleta (incluidas las paletas para daltonismo).
"""

import math
import pygame

from ui import tema

_cache_iconos = {}
_cache_mapa = {}


# =============================================================================
# 1. MODELOS 2D DE LOS 5 SÍMBOLOS DE RECURSOS
# =============================================================================

def _superficie_modelo_recurso(clave, radio, color_base, color_fondo=None):
    """Renderiza (o recupera de caché) un modelo 2D en una superficie SRCALPHA
    con supersampling 2x para bordes suaves."""
    if color_fondo is None:
        color_fondo = tema.oscurecer(color_base, 0.65)
    llave = (clave, int(radio), tuple(color_base), tuple(color_fondo))
    if llave in _cache_iconos:
        return _cache_iconos[llave]

    # Supersampling 2x para antialiasing limpio
    escala = 2
    r = max(8, int(radio) * escala)
    lado = r * 2 + 8 * escala
    surf = pygame.Surface((lado, lado), pygame.SRCALPHA)
    cx = cy = lado // 2

    if clave == "dinero":
        _render_modelo_dinero(surf, cx, cy, r, color_base)
    elif clave == "usuarios":
        _render_modelo_usuarios(surf, cx, cy, r, color_base)
    elif clave == "bienestar":
        _render_modelo_bienestar(surf, cx, cy, r, color_base)
    elif clave == "reputacion":
        _render_modelo_reputacion(surf, cx, cy, r, color_base)
    else:
        _render_modelo_engagement(surf, cx, cy, r, color_base)

    tam_final = (lado // escala, lado // escala)
    final = pygame.transform.smoothscale(surf, tam_final)
    _cache_iconos[llave] = final
    return final


def _render_modelo_dinero(surf, cx, cy, r, color_base):
    """Moneda 2D en relieve con canto biselado, muescas perimetrales, brillo
    diagonal y símbolo '$' tallado en el centro."""
    sombra = (0, 0, 0, 95)
    canto = tema.oscurecer(color_base, 0.45)
    cuerpo = color_base
    aro_claro = tema.aclarar(color_base, 0.45)
    centro_moneda = tema.oscurecer(color_base, 0.22)
    simbolo_col = tema.aclarar(color_base, 0.72)

    # Sombra inferior y canto metálico
    pygame.draw.circle(surf, sombra, (cx + max(2, r // 10), cy + max(3, r // 7)), r)
    pygame.draw.circle(surf, canto, (cx, cy + max(2, r // 12)), r)
    pygame.draw.circle(surf, cuerpo, (cx, cy), r)
    pygame.draw.circle(surf, aro_claro, (cx, cy), r, width=max(2, r // 7))

    # Centro hundido de la moneda
    r_int = int(r * 0.74)
    pygame.draw.circle(surf, centro_moneda, (cx, cy), r_int)
    pygame.draw.circle(surf, aro_claro, (cx, cy), r_int, width=max(1, r // 12))

    # Muescas decorativas en el anillo exterior
    for k in range(12):
        ang = k * (math.pi / 6)
        x1 = cx + int(math.cos(ang) * (r * 0.80))
        y1 = cy + int(math.sin(ang) * (r * 0.80))
        x2 = cx + int(math.cos(ang) * (r * 0.92))
        y2 = cy + int(math.sin(ang) * (r * 0.92))
        pygame.draw.line(surf, aro_claro, (x1, y1), (x2, y2), max(1, r // 14))

    # Brillo especular superior izquierdo
    pygame.draw.circle(surf, (255, 255, 255, 70),
                       (cx - int(r * 0.28), cy - int(r * 0.28)), max(2, int(r * 0.22)))

    # Símbolo '$' vectorial en relieve (doble barra vertical + doble curva en S)
    grosor = max(2, int(r * 0.16))
    sep_barra = max(1, int(r * 0.08))
    for dx in (-sep_barra, sep_barra):
        pygame.draw.line(surf, canto, (cx + dx + 1, cy - int(r * 0.52) + 2),
                         (cx + dx + 1, cy + int(r * 0.52) + 2), grosor)
        pygame.draw.line(surf, simbolo_col, (cx + dx, cy - int(r * 0.52)),
                         (cx + dx, cy + int(r * 0.52)), grosor)

    ancho_s = int(r * 0.36)
    alto_s = int(r * 0.22)
    puntos_s = [
        (cx + ancho_s, cy - int(alto_s * 1.45)),
        (cx - int(ancho_s * 0.6), cy - int(alto_s * 1.65)),
        (cx - ancho_s, cy - int(alto_s * 0.65)),
        (cx - int(ancho_s * 0.4), cy - int(alto_s * 0.08)),
        (cx + int(ancho_s * 0.5), cy + int(alto_s * 0.12)),
        (cx + ancho_s, cy + int(alto_s * 0.75)),
        (cx + int(ancho_s * 0.5), cy + int(alto_s * 1.6)),
        (cx - ancho_s, cy + int(alto_s * 1.4)),
    ]
    sombra_s = [(x + 1, y + 2) for x, y in puntos_s]
    pygame.draw.lines(surf, canto, False, sombra_s, grosor)
    pygame.draw.lines(surf, simbolo_col, False, puntos_s, grosor)


def _render_modelo_usuarios(surf, cx, cy, r, color_base):
    """Modelo 2D de comunidad: usuario principal en primer plano con volumen
    más un segundo usuario detrás y un halo de conexión."""
    sombra = (0, 0, 0, 90)
    secundario = tema.oscurecer(color_base, 0.28)
    borde_sec = tema.aclarar(color_base, 0.25)
    principal = tema.aclarar(color_base, 0.18)
    borde_pri = tema.aclarar(color_base, 0.62)
    brillo = (255, 255, 255, 110)

    # Silueta trasera (derecha)
    cx2, cy2 = cx + int(r * 0.34), cy - int(r * 0.08)
    r_cab2 = max(3, int(r * 0.28))
    pygame.draw.circle(surf, secundario, (cx2, cy2 - int(r * 0.32)), r_cab2)
    pygame.draw.circle(surf, borde_sec, (cx2, cy2 - int(r * 0.32)), r_cab2, width=max(1, r // 14))
    hombros2 = pygame.Rect(cx2 - int(r * 0.48), cy2 + int(r * 0.02), int(r * 0.96), int(r * 0.68))
    pygame.draw.ellipse(surf, secundario, hombros2)
    pygame.draw.ellipse(surf, borde_sec, hombros2, width=max(1, r // 14))

    # Silueta principal (frente izquierda)
    cx1, cy1 = cx - int(r * 0.14), cy + int(r * 0.04)
    r_cab1 = max(4, int(r * 0.36))
    cab_pos = (cx1, cy1 - int(r * 0.36))
    hombros1 = pygame.Rect(cx1 - int(r * 0.66), cy1 + int(r * 0.04), int(r * 1.32), int(r * 0.86))

    pygame.draw.ellipse(surf, sombra, hombros1.move(2, 3))
    pygame.draw.circle(surf, sombra, (cab_pos[0] + 2, cab_pos[1] + 3), r_cab1)

    pygame.draw.ellipse(surf, principal, hombros1)
    pygame.draw.ellipse(surf, borde_pri, hombros1, width=max(2, r // 10))
    pygame.draw.circle(surf, principal, cab_pos, r_cab1)
    pygame.draw.circle(surf, borde_pri, cab_pos, r_cab1, width=max(2, r // 10))

    # Brillo especular en la cabeza y hombro
    pygame.draw.circle(surf, brillo, (cab_pos[0] - int(r_cab1 * 0.3), cab_pos[1] - int(r_cab1 * 0.3)),
                       max(1, int(r_cab1 * 0.28)))


def _render_modelo_bienestar(surf, cx, cy, r, color_base):
    """Corazón 2D paramétrico con bisel, brillo especular y línea de pulso ECG."""
    sombra = (0, 0, 0, 95)
    cuerpo = tema.aclarar(color_base, 0.10)
    borde = tema.aclarar(color_base, 0.58)
    pulso_col = (255, 255, 255, 230)

    puntos = []
    pasos = 44
    escala = (r * 0.95) / 17.0
    for i in range(pasos):
        t = (2 * math.pi * i) / pasos
        hx = 16 * (math.sin(t) ** 3)
        hy = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        puntos.append((cx + int(hx * escala), cy - int(r * 0.08) + int(hy * escala)))

    sombra_pts = [(x + 2, y + 3) for x, y in puntos]
    pygame.draw.polygon(surf, sombra, sombra_pts)
    pygame.draw.polygon(surf, cuerpo, puntos)
    pygame.draw.polygon(surf, borde, puntos, width=max(2, r // 10))

    # Brillo en el lóbulo izquierdo
    pygame.draw.circle(surf, (255, 255, 255, 90),
                       (cx - int(r * 0.34), cy - int(r * 0.30)), max(2, int(r * 0.18)))

    # Línea de pulso vital (ECG)
    ecg = [
        (cx - int(r * 0.55), cy + int(r * 0.02)),
        (cx - int(r * 0.22), cy + int(r * 0.02)),
        (cx - int(r * 0.10), cy - int(r * 0.34)),
        (cx + int(r * 0.08), cy + int(r * 0.32)),
        (cx + int(r * 0.22), cy - int(r * 0.08)),
        (cx + int(r * 0.52), cy - int(r * 0.08)),
    ]
    pygame.draw.lines(surf, pulso_col, False, ecg, max(2, r // 9))


def _render_modelo_reputacion(surf, cx, cy, r, color_base):
    """Estrella facetada 2D de 5 puntas con 10 caras biseladas (luz/sombra)."""
    sombra = (0, 0, 0, 95)
    cara_clara = tema.aclarar(color_base, 0.48)
    cara_oscura = tema.oscurecer(color_base, 0.22)
    borde = tema.aclarar(color_base, 0.72)

    vertices = []
    for k in range(10):
        ang = -math.pi / 2 + k * (math.pi / 5)
        rad = r if k % 2 == 0 else int(r * 0.44)
        vertices.append((cx + int(math.cos(ang) * rad), cy + int(math.sin(ang) * rad)))

    sombra_pts = [(x + 2, y + 3) for x, y in vertices]
    pygame.draw.polygon(surf, sombra, sombra_pts)

    # 10 facetas triangulares alternando iluminación
    for k in range(10):
        p1 = vertices[k]
        p2 = vertices[(k + 1) % 10]
        color_cara = cara_clara if k % 2 == 0 else cara_oscura
        pygame.draw.polygon(surf, color_cara, [(cx, cy), p1, p2])

    pygame.draw.polygon(surf, borde, vertices, width=max(2, r // 11))
    pygame.draw.circle(surf, (255, 255, 255, 120), (cx, cy), max(2, r // 8))


def _render_modelo_engagement(surf, cx, cy, r, color_base):
    """Rayo energético 2D facetado con anillo orbital de interacción."""
    sombra = (0, 0, 0, 95)
    anillo = tema.oscurecer(color_base, 0.15)
    cuerpo = tema.aclarar(color_base, 0.28)
    borde = tema.aclarar(color_base, 0.70)

    # Anillo de onda de interacción alrededor del rayo
    pygame.draw.circle(surf, anillo, (cx, cy), int(r * 0.88), width=max(2, r // 10))

    rayo = [
        (cx + int(r * 0.18), cy - int(r * 0.92)),
        (cx - int(r * 0.58), cy + int(r * 0.08)),
        (cx - int(r * 0.04), cy + int(r * 0.08)),
        (cx - int(r * 0.22), cy + int(r * 0.92)),
        (cx + int(r * 0.58), cy - int(r * 0.08)),
        (cx + int(r * 0.06), cy - int(r * 0.08)),
    ]
    sombra_r = [(x + 2, y + 3) for x, y in rayo]
    pygame.draw.polygon(surf, sombra, sombra_r)
    pygame.draw.polygon(surf, cuerpo, rayo)
    pygame.draw.polygon(surf, borde, rayo, width=max(2, r // 11))


def dibujar_modelo_recurso(pantalla, clave, centro, radio, color_base, color_fondo=None):
    """Dibuja el modelo 2D del recurso centrado en `centro` con radio `radio`."""
    surf = _superficie_modelo_recurso(clave, radio, color_base, color_fondo)
    rect = surf.get_rect(center=centro)
    pantalla.blit(surf, rect)


# =============================================================================
# 2. MODELO CARTOGRÁFICO 2D DEL MAPA MUNDIAL
# =============================================================================

# Polígonos continentales de alta precisión (coordenadas absolutas dentro de
# RECT_OCEANO = pygame.Rect(42, 182, 824, 476))
CONTINENTES_DETALLADOS_2D = {
    "norteamerica": [
        # Norteamérica: Alaska, Yukón, Bahía de Hudson, Labrador, Costa Este, Florida, Golfo de México, Baja California
        [(52, 236), (68, 214), (98, 204), (132, 206), (160, 198), (186, 214),
         (196, 232), (218, 212), (252, 216), (282, 236), (294, 254), (272, 274),
         (256, 296), (242, 318), (236, 344), (226, 346), (218, 328), (196, 332),
         (182, 350), (166, 356), (146, 346), (134, 326), (126, 336), (118, 314),
         (110, 282), (96, 260), (74, 256), (56, 248)],
        # Archipiélago Ártico Canadiense
        [(194, 190), (236, 188), (252, 202), (218, 206), (192, 200)],
        # Groenlandia
        [(286, 188), (324, 186), (358, 194), (364, 214), (338, 236), (308, 240), (290, 218)],
        # Cuba y La Española (Caribe)
        [(210, 364), (240, 368), (256, 376), (234, 378), (206, 372)],
    ],
    "centroamerica": [
        # Sur de México, Yucatán, Guatemala, Honduras, Nicaragua, Costa Rica, Panamá
        [(142, 348), (168, 354), (186, 350), (198, 358), (190, 374),
         (204, 386), (212, 404), (226, 420), (236, 428), (222, 436),
         (204, 426), (186, 412), (166, 396), (148, 376)],
    ],
    "sudamerica": [
        # Colombia, Venezuela, Guayanas, Brasil, Uruguay, Argentina, Chile, Perú, Ecuador
        [(226, 426), (254, 420), (282, 432), (308, 448), (344, 470), (352, 496),
         (338, 528), (318, 558), (298, 588), (284, 622), (274, 646), (256, 642),
         (250, 610), (246, 572), (242, 536), (224, 504), (212, 474), (216, 446)],
    ],
    "europa": [
        # Península Ibérica, Francia, Países Bajos, Jutlandia, Escandinavia, Europa Oriental, Balcanes, Italia
        [(388, 304), (384, 282), (402, 278), (408, 260), (426, 246), (434, 224),
         (448, 198), (476, 190), (504, 196), (528, 212), (538, 244), (532, 272),
         (512, 288), (494, 304), (480, 310), (470, 294), (456, 290), (464, 308),
         (454, 314), (442, 294), (424, 296), (408, 310)],
        # Gran Bretaña e Irlanda
        [(384, 236), (404, 230), (410, 252), (394, 258), (382, 248)],
        # Islandia
        [(362, 206), (382, 204), (386, 216), (366, 218)],
    ],
    "africa": [
        # Marruecos, Argelia, Egipto, Cuerno de África, Kenia, Sudáfrica, Angola, Golfo de Guinea, Senegal
        [(386, 326), (422, 318), (456, 326), (492, 334), (510, 352), (528, 392),
         (556, 412), (544, 448), (526, 488), (516, 532), (494, 578), (470, 598),
         (450, 586), (442, 546), (432, 506), (426, 466), (412, 444), (382, 442),
         (364, 416), (362, 382), (374, 350)],
        # Madagascar
        [(538, 522), (554, 516), (560, 556), (546, 568), (536, 548)],
    ],
    "medio_oriente": [
        # Anatolia, Siria/Levante, Península Arábiga, Irak, Irán
        [(502, 296), (542, 290), (578, 298), (608, 316), (618, 348), (604, 376),
         (586, 404), (552, 414), (532, 392), (514, 356), (506, 326)],
    ],
    "asia": [
        # Rusia/Siberia, Kazajistán, India, Indochina, China, Corea, Kamchatka
        [(534, 208), (586, 194), (658, 192), (736, 196), (808, 206), (846, 224),
         (836, 256), (812, 268), (802, 292), (792, 326), (776, 360), (748, 382),
         (734, 418), (718, 428), (706, 396), (690, 384), (668, 404), (652, 432),
         (636, 418), (624, 382), (608, 352), (604, 316), (574, 296), (536, 272)],
        # Japón
        [(808, 282), (824, 276), (832, 306), (818, 328), (806, 314)],
        # Sumatra, Java, Borneo y Filipinas
        [(714, 434), (754, 436), (788, 446), (796, 462), (756, 466), (718, 454)],
        # Sri Lanka
        [(658, 434), (666, 434), (668, 446), (658, 446)],
    ],
    "oceania": [
        # Australia (con Golfo de Carpentaria y Gran Bahía Australiana)
        [(712, 496), (742, 480), (766, 488), (782, 476), (808, 494), (826, 524),
         (820, 558), (796, 578), (768, 572), (738, 566), (712, 554), (702, 526)],
        # Papúa Nueva Guinea
        [(786, 454), (822, 458), (828, 470), (792, 468)],
        # Tasmania
        [(786, 584), (798, 584), (796, 596), (784, 594)],
        # Nueva Zelanda
        [(838, 564), (854, 552), (858, 586), (842, 602), (834, 588)],
    ],
}

# Polígonos interiores de relieve (cordilleras / mesetas continentales)
_RELIEVE_INTERIOR_2D = {
    "norteamerica": [[(92, 232), (138, 228), (168, 268), (154, 316), (124, 294)]],
    "sudamerica": [[(232, 452), (254, 464), (274, 536), (266, 598), (248, 548)]],
    "europa": [[(428, 256), (484, 242), (506, 268), (456, 280)]],
    "africa": [[(404, 356), (476, 354), (506, 424), (484, 522), (448, 476)]],
    "medio_oriente": [[(526, 316), (578, 322), (588, 368), (546, 378)]],
    "asia": [[(618, 236), (734, 232), (772, 288), (724, 348), (646, 336)]],
    "oceania": [[(732, 510), (794, 508), (802, 546), (742, 548)]],
}


def _dibujar_rosa_vientos(pantalla, cx, cy, radio):
    """Rosa de los vientos náutica en una esquina del océano 2D."""
    c_borde = tema.mezclar(tema.COLOR_FONDO_ARRIBA, tema.COLOR_CIAN, 0.45)
    c_claro = tema.mezclar(tema.COLOR_FONDO_ARRIBA, tema.COLOR_TEXTO, 0.55)
    pygame.draw.circle(pantalla, c_borde, (cx, cy), radio, width=1)
    pygame.draw.circle(pantalla, c_borde, (cx, cy), int(radio * 0.65), width=1)
    # Puntas N, S, E, O
    for dx, dy in ((0, -radio - 4), (0, radio + 4), (-radio - 4, 0), (radio + 4, 0)):
        if dy != 0:
            pts = [(cx, cy + dy), (cx - 4, cy), (cx + 4, cy)]
        else:
            pts = [(cx + dx, cy), (cx, cy - 4), (cx, cy + 4)]
        pygame.draw.polygon(pantalla, c_claro if dy < 0 else c_borde, pts)


def dibujar_modelo_mapa_2d(pantalla, rect_oceano, colores_por_region, seleccion=None):
    """Dibuja el modelo cartográfico 2D completo dentro de `rect_oceano`.
    `colores_por_region` es un dict `{id_region: (color_relleno, color_costa)}`."""
    oceano = rect_oceano
    color_mar_profundo = tema.oscurecer(tema.COLOR_FONDO_ARRIBA, 0.30)
    color_mar_centro = tema.mezclar(color_mar_profundo, tema.COLOR_CIAN, 0.08)
    pygame.draw.rect(pantalla, color_mar_profundo, oceano, border_radius=16)

    # Franja ecuatorial sutilmente iluminada
    franja_eq = pygame.Rect(oceano.x + 4, oceano.centery - 70, oceano.width - 8, 140)
    pygame.draw.rect(pantalla, color_mar_centro, franja_eq, border_radius=12)

    # Cuadrícula geográfica (meridianos y paralelos)
    color_red = tema.mezclar(color_mar_profundo, tema.COLOR_BORDE, 0.40)
    color_ecuador = tema.mezclar(color_mar_profundo, tema.COLOR_CIAN, 0.35)
    for frac_x in (0.14, 0.28, 0.42, 0.56, 0.70, 0.84):
        x = oceano.x + int(oceano.width * frac_x)
        pygame.draw.line(pantalla, color_red, (x, oceano.top + 4), (x, oceano.bottom - 4), 1)
    for frac_y in (0.18, 0.36, 0.54, 0.72, 0.88):
        y = oceano.y + int(oceano.height * frac_y)
        es_ecuador = abs(frac_y - 0.54) < 0.01
        pygame.draw.line(pantalla, color_ecuador if es_ecuador else color_red,
                         (oceano.left + 4, y), (oceano.right - 4, y), 2 if es_ecuador else 1)

    sombra_plataforma = tema.oscurecer(color_mar_profundo, 0.48)
    halo_costero = tema.mezclar(color_mar_profundo, tema.COLOR_CIAN, 0.16)

    # 1. Plataforma continental y sombra marina
    for id_region, poligonos in CONTINENTES_DETALLADOS_2D.items():
        for poly in poligonos:
            sombra = [(px + 4, py + 5) for px, py in poly]
            pygame.draw.polygon(pantalla, sombra_plataforma, sombra)
            pygame.draw.polygon(pantalla, halo_costero, poly, width=5)

    # 2. Masa continental, relieve interior y línea costera
    for id_region, poligonos in CONTINENTES_DETALLADOS_2D.items():
        relleno, costa = colores_por_region.get(
            id_region,
            (tema.mezclar(tema.COLOR_PANEL_CLARO, tema.COLOR_FONDO_ABAJO, 0.2), tema.COLOR_BORDE),
        )
        for poly in poligonos:
            pygame.draw.polygon(pantalla, relleno, poly)

        # Relieve topográfico interior
        color_relieve = tema.aclarar(relleno, 0.12)
        for sub_poly in _RELIEVE_INTERIOR_2D.get(id_region, ()):
            pygame.draw.polygon(pantalla, color_relieve, sub_poly)

        grosor_costa = 3 if id_region == seleccion else 2
        for poly in poligonos:
            pygame.draw.polygon(pantalla, costa, poly, width=grosor_costa)

    # Rosa de los vientos en el Pacífico Sur
    _dibujar_rosa_vientos(pantalla, oceano.left + 46, oceano.bottom - 46, 22)
    pygame.draw.rect(pantalla, tema.COLOR_BORDE, oceano, width=2, border_radius=16)
