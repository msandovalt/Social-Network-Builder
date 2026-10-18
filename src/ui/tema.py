"""
Tema visual compartido: tamaño de ventana, paleta, fuentes y utilidades de
dibujo (fondo animado, paneles con sombra, botones con hover).

Todas las pantallas se apoyan en estas funciones para verse coherentes.
Las superficies pesadas (degradados, sombras, orbes) se crean una sola vez
y se guardan en `_cache`.

Fuente propia (opcional): si existe `assets/fuentes/principal.ttf` en la raíz
del proyecto se usa; si no, se prueba con fuentes comunes del sistema.
"""

import math
import os
from types import SimpleNamespace

import pygame

from ui import paletas

ANCHO, ALTO = 1280, 720

# --- Paleta ---------------------------------------------------------------
# Los colores viven como atributos de este módulo (tema.COLOR_VERDE...) y se
# reemplazan al cambiar de paleta con `aplicar_paleta`. Por eso el resto del
# código debe leerlos en el momento de dibujar, NUNCA guardarlos en constantes
# al importar el módulo ni usarlos como valor por defecto de un parámetro.
# Las paletas (incluidas las de daltonismo) están en ui/paletas.py.
COLOR_FONDO_ARRIBA = COLOR_FONDO_ABAJO = COLOR_PANEL = COLOR_PANEL_CLARO = COLOR_BORDE = None
COLOR_TEXTO = COLOR_TEXTO_SEC = COLOR_DESHABILITADO = COLOR_BLOQUEADO = None
COLOR_ACENTO = COLOR_ROSA = COLOR_VERDE = COLOR_ROJO = COLOR_AMARILLO = None
COLOR_CIAN = COLOR_MORADO = COLOR_NARANJA = COLOR_TEAL = None
COLOR_BOTON_OK = COLOR_BOTON_PELIGRO = None

# Un color por recurso (tarjetas del encabezado, tragamonedas): "dinero", "usuarios", ...
COLOR_RECURSO = {}

PALETA_ACTUAL = paletas.PALETA_POR_DEFECTO


def aplicar_paleta(nombre):
    """Cambia todos los colores del juego a la paleta `nombre`. Las superficies
    guardadas en caché (degradados, orbes) dependen del color, así que se descartan."""
    global PALETA_ACTUAL
    if not paletas.es_paleta_valida(nombre):
        raise ValueError(f"paleta desconocida: {nombre!r}")
    modulo = globals()
    for clave, valor in paletas.PALETAS[nombre].items():
        if clave.startswith("recurso_"):
            COLOR_RECURSO[clave[len("recurso_"):]] = valor
        else:
            modulo["COLOR_" + clave.upper()] = valor
    PALETA_ACTUAL = nombre
    _cache.clear()


FUENTES_PREFERIDAS = "segoeui,helveticaneue,helvetica,arial,dejavusans"
RUTA_FUENTE = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "fuentes", "principal.ttf")
_FUENTES_SISTEMA_REGULAR = (
    ("segoeui.ttf", "segoeuib.ttf"),
    ("arial.ttf", "arialbd.ttf"),
)

_cache = {}


# --- Colores ----------------------------------------------------------------
def mezclar(c1, c2, t):
    """Mezcla lineal entre dos colores (t=0 -> c1, t=1 -> c2)."""
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1[:3], c2[:3]))


def aclarar(color, factor):
    return mezclar(color, (255, 255, 255), factor)


def oscurecer(color, factor):
    return mezclar(color, (0, 0, 0), factor)


def luminancia(color):
    """Luminancia relativa (0 negro, 1 blanco) según WCAG."""
    def lineal(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lineal(c) for c in color[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def color_sobre(fondo):
    """Color de texto o ícono que se lee mejor sobre `fondo`: oscuro si el fondo
    es claro y claro si es oscuro (elige el de mayor contraste)."""
    oscuro, claro = COLOR_FONDO_ARRIBA, COLOR_TEXTO
    def contraste(a, b):
        la, lb = sorted((luminancia(a), luminancia(b)), reverse=True)
        return (la + 0.05) / (lb + 0.05)
    return claro if contraste(fondo, claro) >= contraste(fondo, oscuro) else oscuro


def esta_encima(rect):
    """True si el mouse está sobre el rectángulo (para el efecto hover)."""
    return rect.collidepoint(pygame.mouse.get_pos())


# --- Fuentes ----------------------------------------------------------------
def _ruta_fuente_sistema(negrita=False):
    """En Windows, `SysFont('segoeui')` suele devolver `segoeuil.ttf` (Light),
    que se ve demasiado fina en tamaños pequeños. Si existe `segoeui.ttf`
    (Regular) o `segoeuib.ttf` (Bold) en la carpeta de fuentes del sistema,
    la cargamos directamente."""
    windir = os.environ.get("WINDIR") or os.environ.get("SystemRoot")
    if not windir:
        return None
    carpeta = os.path.join(windir, "Fonts")
    for regular, bold in _FUENTES_SISTEMA_REGULAR:
        candidato = os.path.join(carpeta, bold if negrita else regular)
        if os.path.isfile(candidato):
            return candidato
    return None


def cargar_fuente(tamano, negrita=False):
    if os.path.isfile(RUTA_FUENTE):
        fuente = pygame.font.Font(RUTA_FUENTE, tamano)
        fuente.set_bold(negrita)
        return fuente
    ruta_sis = _ruta_fuente_sistema(negrita)
    if ruta_sis is not None:
        return pygame.font.Font(ruta_sis, tamano)
    return pygame.font.SysFont(FUENTES_PREFERIDAS, tamano, bold=negrita)


def crear_fuentes():
    """Se llama después de pygame.init()."""
    return SimpleNamespace(
        pequena=cargar_fuente(18),
        normal=cargar_fuente(22),
        boton=cargar_fuente(24, True),
        subtitulo=cargar_fuente(32, True),
        titulo=cargar_fuente(60, True),
        simbolo=cargar_fuente(64, True),
        arbol=cargar_fuente(20, True),
        arbol_pequena=cargar_fuente(16),
    )


# --- Fondo animado ----------------------------------------------------------
def _orbes():
    """(x relativo, y relativo, radio, color, velocidad, fase) con la paleta actual."""
    return (
        (0.15, 0.25, 230, COLOR_ACENTO, 0.30, 0.0),
        (0.85, 0.30, 260, COLOR_ROSA, 0.22, 2.0),
        (0.55, 0.92, 300, COLOR_CIAN, 0.18, 4.0),
        (0.05, 0.88, 200, COLOR_MORADO, 0.26, 1.0),
    )


def _fondo_degradado(tamano):
    clave = ("fondo", tamano)
    if clave not in _cache:
        ancho, alto = tamano
        superficie = pygame.Surface(tamano)
        for y in range(alto):
            color = mezclar(COLOR_FONDO_ARRIBA, COLOR_FONDO_ABAJO, y / max(1, alto - 1))
            pygame.draw.line(superficie, color, (0, y), (ancho, y))
        _cache[clave] = superficie
    return _cache[clave]


def _orbe(radio, color):
    clave = ("orbe", radio, color)
    if clave not in _cache:
        superficie = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
        pasos = 24
        for i in range(pasos):
            r = max(1, radio - i * radio // pasos)
            alpha = int(46 * (i + 1) / pasos)
            pygame.draw.circle(superficie, (color[0], color[1], color[2], alpha), (radio, radio), r)
        _cache[clave] = superficie
    return _cache[clave]


def dibujar_fondo(pantalla, t):
    """Degradado vertical con orbes de luz que flotan lentamente."""
    tamano = pantalla.get_size()
    ancho, alto = tamano
    pantalla.blit(_fondo_degradado(tamano), (0, 0))
    for fx, fy, radio, color, velocidad, fase in _orbes():
        x = fx * ancho + math.sin(t * velocidad + fase) * 50
        y = fy * alto + math.cos(t * velocidad * 0.8 + fase) * 35
        pantalla.blit(_orbe(radio, color), (int(x - radio), int(y - radio)))


def dibujar_overlay(pantalla, alpha, usar_cache=True):
    """Capa negra semitransparente sobre toda la pantalla.
    Cuando `usar_cache=False` (ej. durante el fundido entre pantallas), reutiliza
    una única superficie negra con `set_alpha` en vez de reservar memoria por cuadro."""
    tamano = pantalla.get_size()
    if not usar_cache:
        clave_dinamica = ("overlay_dinamico", tamano)
        superficie = _cache.get(clave_dinamica)
        if superficie is None:
            superficie = pygame.Surface(tamano)
            superficie.fill((0, 0, 0))
            _cache[clave_dinamica] = superficie
        superficie.set_alpha(alpha)
        pantalla.blit(superficie, (0, 0))
        return

    clave = ("overlay", tamano, alpha)
    if clave in _cache:
        superficie = _cache[clave]
    else:
        superficie = pygame.Surface(tamano, pygame.SRCALPHA)
        superficie.fill((0, 0, 0, alpha))
        _cache[clave] = superficie
    pantalla.blit(superficie, (0, 0))


# --- Paneles y botones --------------------------------------------------------
_MARGEN_SOMBRA = 16


def _sombra(ancho, alto, radio):
    clave = ("sombra", ancho, alto, radio)
    if clave not in _cache:
        pad = _MARGEN_SOMBRA
        superficie = pygame.Surface((ancho + 2 * pad, alto + 2 * pad), pygame.SRCALPHA)
        for i in range(pad):
            alpha = int(90 * ((i + 1) / pad) ** 2)
            rect = pygame.Rect(i, i, ancho + 2 * pad - 2 * i, alto + 2 * pad - 2 * i)
            pygame.draw.rect(superficie, (0, 0, 0, alpha), rect, border_radius=radio + pad - i)
        _cache[clave] = superficie
    return _cache[clave]


def dibujar_sombra(pantalla, rect, radio=16):
    pantalla.blit(_sombra(rect.width, rect.height, radio),
                  (rect.x - _MARGEN_SOMBRA, rect.y - _MARGEN_SOMBRA + 6))


def dibujar_panel(pantalla, rect, radio=16, color=None, borde="auto", sombra=True, grosor=2):
    """`color=None` usa el color de panel de la paleta; `borde="auto"` usa el
    borde de la paleta y `borde=None` no dibuja borde."""
    color = COLOR_PANEL if color is None else color
    borde = COLOR_BORDE if borde == "auto" else borde
    if sombra:
        dibujar_sombra(pantalla, rect, radio)
    pygame.draw.rect(pantalla, color, rect, border_radius=radio)
    if borde:
        pygame.draw.rect(pantalla, borde, rect, width=grosor, border_radius=radio)


def dibujar_texto(pantalla, fuente, texto, color, **anclaje):
    """Dibuja texto anclado con cualquier atributo de Rect (center=, topleft=,
    midtop=, topright=...). Devuelve el rectángulo ocupado."""
    superficie = fuente.render(texto, True, color)
    rect = superficie.get_rect(**anclaje)
    pantalla.blit(superficie, rect)
    return rect


def envolver_texto(fuente, texto, ancho_maximo):
    """Parte `texto` en líneas que no superen `ancho_maximo` píxeles."""
    lineas = []
    actual = ""
    for palabra in texto.split(" "):
        prueba = (actual + " " + palabra).strip()
        if fuente.size(prueba)[0] <= ancho_maximo:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


def dibujar_boton(pantalla, fuente, rect, texto, color, habilitado=True, activo=False, radio=12):
    """Botón con sombra y efecto hover. `activo` lo resalta con un aro."""
    if habilitado:
        encima = esta_encima(rect)
        relleno = aclarar(color, 0.18) if encima else color
        dibujar_sombra(pantalla, rect, radio)
    else:
        encima = False
        relleno = COLOR_DESHABILITADO
    pygame.draw.rect(pantalla, relleno, rect, border_radius=radio)
    borde = aclarar(relleno, 0.35) if (encima or activo) else oscurecer(relleno, 0.2)
    pygame.draw.rect(pantalla, borde, rect, width=2, border_radius=radio)
    if activo:
        pygame.draw.rect(pantalla, COLOR_TEXTO, rect.inflate(8, 8), width=2, border_radius=radio + 4)
    color_texto = color_sobre(relleno) if habilitado else COLOR_TEXTO_SEC
    dibujar_texto(pantalla, fuente, texto, color_texto, center=rect.center)


aplicar_paleta(paletas.PALETA_POR_DEFECTO)
