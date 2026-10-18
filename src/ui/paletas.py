"""
Paletas de color del juego, incluidas las pensadas para distintos tipos de
daltonismo. Sin Pygame: son solo datos (colores RGB), fáciles de probar.

Cada paleta define los mismos colores "semánticos":
- verde / rojo: lo bueno y lo malo (éxito, peligro).
- amarillo: lo que está disponible o destacado.
- naranja: lo interactivo o que necesita atención. teal: efectos fijos.
- cian / morado / rosa / acento: información y adornos.
- boton_ok / boton_peligro: botones de confirmar y de cancelar o salir.
- recurso_*: el color de cada recurso en las tarjetas y la tragamonedas.

Cómo se diseñaron las paletas para daltonismo: se simuló cómo ve cada tipo
(matrices de Machado et al., 2009) y se eligieron colores que se mantienen
bien distintos en esa simulación (tests/test_paletas.py lo comprueba). Aun
así, el juego NUNCA depende solo del color: también usa íconos y formas.
Sigue siendo recomendable probarlas con personas daltónicas.
"""

PALETA_POR_DEFECTO = "normal"

_BASE_OSCURA = {
    "fondo_arriba": (15, 17, 36), "fondo_abajo": (34, 22, 62), "panel": (30, 33, 60),
    "panel_claro": (46, 50, 86), "borde": (68, 74, 120), "texto": (240, 242, 255),
    "texto_sec": (160, 168, 205), "deshabilitado": (58, 62, 92),
}

PALETAS = {
    "normal": {
        **_BASE_OSCURA,
        "bloqueado": (62, 66, 96), "acento": (99, 102, 241), "rosa": (244, 114, 182),
        "verde": (52, 211, 153), "rojo": (248, 113, 113), "amarillo": (250, 204, 21),
        "cian": (56, 189, 248), "morado": (192, 132, 252), "naranja": (230, 126, 52),
        "teal": (30, 150, 140), "boton_ok": (34, 160, 120), "boton_peligro": (190, 70, 80),
        "recurso_dinero": (52, 211, 153), "recurso_usuarios": (56, 189, 248),
        "recurso_bienestar": (244, 114, 182), "recurso_reputacion": (192, 132, 252),
        "recurso_engagement": (250, 204, 21),
    },
    # Rojo-verde: azul = bueno, naranja = malo (la pareja más segura para estos tipos).
    "protanopia": {
        **_BASE_OSCURA,
        "bloqueado": (74, 78, 108), "acento": (40, 130, 210), "rosa": (225, 205, 255),
        "verde": (86, 180, 233), "rojo": (255, 160, 70), "amarillo": (255, 245, 150),
        "cian": (180, 215, 240), "morado": (150, 150, 255), "naranja": (210, 120, 20),
        "teal": (30, 120, 200), "boton_ok": (20, 110, 190), "boton_peligro": (200, 100, 0),
        "recurso_dinero": (60, 200, 110), "recurso_usuarios": (255, 255, 255),
        "recurso_bienestar": (204, 121, 167), "recurso_reputacion": (170, 120, 255),
        "recurso_engagement": (240, 228, 66),
    },
    "deuteranopia": {
        **_BASE_OSCURA,
        "bloqueado": (74, 78, 108), "acento": (40, 130, 210), "rosa": (204, 121, 167),
        "verde": (86, 180, 233), "rojo": (240, 130, 60), "amarillo": (255, 245, 160),
        "cian": (180, 215, 240), "morado": (150, 150, 255), "naranja": (205, 110, 20),
        "teal": (30, 120, 200), "boton_ok": (20, 110, 190), "boton_peligro": (190, 80, 0),
        "recurso_dinero": (60, 200, 110), "recurso_usuarios": (255, 255, 255),
        "recurso_bienestar": (204, 121, 167), "recurso_reputacion": (150, 150, 255),
        "recurso_engagement": (240, 228, 66),
    },
    # Azul-amarillo: se evita depender de azules y amarillos; rojo y verde sí se distinguen.
    "tritanopia": {
        "fondo_arriba": (22, 20, 28), "fondo_abajo": (44, 22, 36), "panel": (36, 34, 48),
        "panel_claro": (56, 52, 72), "borde": (88, 80, 104), "texto": (245, 243, 245),
        "texto_sec": (175, 170, 180), "deshabilitado": (64, 60, 74),
        "bloqueado": (80, 76, 90), "acento": (200, 50, 90), "rosa": (255, 140, 170),
        "verde": (60, 200, 110), "rojo": (255, 90, 90), "amarillo": (255, 250, 220),
        "cian": (140, 225, 190), "morado": (170, 170, 170), "naranja": (255, 140, 40),
        "teal": (60, 160, 120), "boton_ok": (40, 150, 90), "boton_peligro": (190, 60, 70),
        "recurso_dinero": (120, 230, 200), "recurso_usuarios": (60, 120, 220),
        "recurso_bienestar": (170, 120, 255), "recurso_reputacion": (230, 159, 0),
        "recurso_engagement": (240, 228, 66),
    },
    # Solo grises: cada significado tiene un nivel de claridad muy distinto.
    "acromatopsia": {
        "fondo_arriba": (14, 14, 14), "fondo_abajo": (32, 32, 32), "panel": (30, 30, 30),
        "panel_claro": (52, 52, 52), "borde": (96, 96, 96), "texto": (245, 245, 245),
        "texto_sec": (170, 170, 170), "deshabilitado": (60, 60, 60),
        "bloqueado": (55, 55, 55), "acento": (130, 130, 130), "rosa": (215, 215, 215),
        "verde": (235, 235, 235), "rojo": (140, 140, 140), "amarillo": (165, 165, 165),
        "cian": (200, 200, 200), "morado": (175, 175, 175), "naranja": (110, 110, 110),
        "teal": (190, 190, 190), "boton_ok": (115, 115, 115), "boton_peligro": (60, 60, 60),
        "recurso_dinero": (245, 245, 245), "recurso_usuarios": (205, 205, 205),
        "recurso_bienestar": (170, 170, 170), "recurso_reputacion": (140, 140, 140),
        "recurso_engagement": (115, 115, 115),
    },
}

# (id, nombre, descripción) en el orden en que se muestran en pantalla
OPCIONES = (
    ("normal", "Visión normal", "Los colores originales del juego."),
    ("protanopia", "Protanopía",
     "Dificultad para distinguir rojos y verdes; los rojos se ven más oscuros."),
    ("deuteranopia", "Deuteranopía",
     "Dificultad para distinguir verdes y rojos. Usa azul y naranja en vez de verde y rojo."),
    ("tritanopia", "Tritanopía",
     "Dificultad para distinguir azules de verdes y amarillos de rosados. Es poco frecuente."),
    ("acromatopsia", "Acromatopsia",
     "No se distinguen los colores y se ve en tonos de gris. Usa niveles de claridad muy distintos."),
)

NOMBRES_COLOR = tuple(PALETAS[PALETA_POR_DEFECTO])


def es_paleta_valida(nombre):
    """True solo si `nombre` es el texto de una paleta existente (cualquier otro
    tipo de valor, como una lista leída de un archivo dañado, es inválido)."""
    return isinstance(nombre, str) and nombre in PALETAS
