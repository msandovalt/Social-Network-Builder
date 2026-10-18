"""
Panel modal que se abre al hacer clic en un nodo del árbol: muestra su
nombre, tipo de control, costo, descripción y efectos, y pide confirmar la
compra en vez de desbloquear el nodo de inmediato con un solo clic.

Una vez desbloqueado, los nodos interactivos muestran sus controles en el
mismo panel: botón de encendido (interruptor), botones -/+ y barra clicable
(dial) o un botón por variante (bifurcación).
"""

import pygame

from ui import tema
from ui.formato import formato_numero, formatear_efectos
from ui.tema import ANCHO

RECT_PANEL = pygame.Rect((ANCHO - 620) // 2, 100, 620, 520)
RECT_BOTON_COMPRAR = pygame.Rect(370, 556, 200, 48)
RECT_BOTON_CANCELAR = pygame.Rect(710, 556, 200, 48)
RECT_BOTON_CERRAR = pygame.Rect(540, 556, 200, 48)  # cuando solo hay un botón

# Controles de nodos interactivos ya desbloqueados (fila entre los efectos y los botones)
Y_CONTROLES = 488
RECT_INTERRUPTOR = pygame.Rect(460, Y_CONTROLES, 360, 44)
RECT_DIAL_MENOS = pygame.Rect(370, Y_CONTROLES, 52, 44)
RECT_DIAL_MAS = pygame.Rect(858, Y_CONTROLES, 52, 44)
RECT_DIAL_BARRA = pygame.Rect(440, Y_CONTROLES + 16, 400, 12)
RECT_VARIANTES = (
    pygame.Rect(370, Y_CONTROLES, 260, 44),
    pygame.Rect(650, Y_CONTROLES, 260, 44),
)
PASO_DIAL = 10
PASO_BARRA = 5  # al hacer clic en la barra el valor se ajusta de a 5

ETIQUETAS_TIPO = {
    "fijo": "Efecto fijo",
    "interruptor": "Interruptor",
    "dial": "Dial",
    "bifurcacion": "Bifurcación",
}


def color_de_tipo(tipo):
    """Color del chip de tipo con la paleta activa: teal para fijo, naranja para interactivo."""
    return tema.COLOR_TEAL if tipo == "fijo" else tema.COLOR_NARANJA


def evaluar_estado(nodo, recursos):
    """Devuelve en qué situación está el nodo respecto a poder comprarlo:
    'desbloqueado', 'bloqueado_padre', 'bloqueado_dinero' o 'disponible'."""
    if nodo.desbloqueado:
        return "desbloqueado"
    if nodo.padre is not None and not nodo.padre.desbloqueado:
        return "bloqueado_padre"
    if recursos.dinero < nodo.costo:
        return "bloqueado_dinero"
    return "disponible"


def _etiqueta_variante(nombre):
    return nombre.replace("_", " ").capitalize()


def lineas_de_efectos(nodo):
    """Textos que describen qué hace el nodo (vacío si no tiene efectos)."""
    if nodo.tipo_control == "bifurcacion":
        return [f"{_etiqueta_variante(nombre)}: {formatear_efectos(datos.get('efectos', {}))}"
                for nombre, datos in nodo.variantes.items()]
    if not nodo.efectos:
        return []
    texto = formatear_efectos(nodo.efectos)
    if nodo.tipo_control == "interruptor":
        return [f"Cada ronda, encendido: {texto}"]
    if nodo.tipo_control == "dial":
        return [f"Cada ronda, al 100%: {texto}"]
    return [f"Al comprarlo: {texto}"]


def _dibujar_controles(pantalla, fuentes, nodo):
    """Dibuja los controles del nodo según su tipo (solo si está desbloqueado)."""
    if nodo.tipo_control == "interruptor":
        texto = "Encendido (clic para apagar)" if nodo.activo else "Apagado (clic para encender)"
        color = tema.COLOR_NARANJA if nodo.activo else tema.COLOR_PANEL_CLARO
        tema.dibujar_boton(pantalla, fuentes.normal, RECT_INTERRUPTOR, texto, color, activo=nodo.activo)

    elif nodo.tipo_control == "dial":
        tema.dibujar_boton(pantalla, fuentes.boton, RECT_DIAL_MENOS, "-", tema.COLOR_PANEL_CLARO)
        tema.dibujar_boton(pantalla, fuentes.boton, RECT_DIAL_MAS, "+", tema.COLOR_PANEL_CLARO)
        barra = RECT_DIAL_BARRA
        pygame.draw.rect(pantalla, tema.COLOR_PANEL_CLARO, barra, border_radius=6)
        if nodo.valor > 0:
            relleno = pygame.Rect(barra.x, barra.y, int(barra.width * nodo.valor / 100), barra.height)
            pygame.draw.rect(pantalla, tema.COLOR_NARANJA, relleno, border_radius=6)
        perilla = (barra.x + int(barra.width * nodo.valor / 100), barra.centery)
        pygame.draw.circle(pantalla, tema.COLOR_TEXTO, perilla, 10)
        pygame.draw.circle(pantalla, tema.COLOR_NARANJA, perilla, 10, width=3)
        tema.dibujar_texto(pantalla, fuentes.normal, f"{nodo.valor}%", tema.COLOR_TEXTO,
                           midbottom=(barra.centerx, barra.y - 8))

    elif nodo.tipo_control == "bifurcacion":
        for rect, nombre in zip(RECT_VARIANTES, nodo.variantes):
            elegida = nodo.variante_actual == nombre
            color = tema.COLOR_NARANJA if elegida else tema.COLOR_PANEL_CLARO
            tema.dibujar_boton(pantalla, fuentes.normal, rect, _etiqueta_variante(nombre), color, activo=elegida)


def manejar_click_controles(nodo, pos):
    """Aplica el clic sobre los controles del nodo. Devuelve True si el clic
    cayó sobre un control (para que el llamador no lo trate como otra cosa)."""
    if not nodo.desbloqueado:
        return False

    if nodo.tipo_control == "interruptor" and RECT_INTERRUPTOR.collidepoint(pos):
        nodo.alternar_interruptor()
        return True

    if nodo.tipo_control == "dial":
        if RECT_DIAL_MENOS.collidepoint(pos):
            nodo.ajustar_dial(nodo.valor - PASO_DIAL)
            return True
        if RECT_DIAL_MAS.collidepoint(pos):
            nodo.ajustar_dial(nodo.valor + PASO_DIAL)
            return True
        if RECT_DIAL_BARRA.inflate(0, 24).collidepoint(pos):
            proporcion = (pos[0] - RECT_DIAL_BARRA.x) / RECT_DIAL_BARRA.width
            nodo.ajustar_dial(round(proporcion * 100 / PASO_BARRA) * PASO_BARRA)
            return True

    if nodo.tipo_control == "bifurcacion":
        for rect, nombre in zip(RECT_VARIANTES, nodo.variantes):
            if rect.collidepoint(pos):
                nodo.elegir_variante(nombre)
                return True

    return False


def dibujar_panel_detalle(pantalla, fuentes, nodo, recursos):
    tema.dibujar_overlay(pantalla, 170)
    tema.dibujar_panel(pantalla, RECT_PANEL, radio=20)

    ancho_texto = RECT_PANEL.width - 80
    x = RECT_PANEL.x + 40
    y = RECT_PANEL.y + 22

    tema.dibujar_texto(pantalla, fuentes.subtitulo, nodo.nombre, tema.COLOR_TEXTO, topleft=(x, y))
    y += 46

    etiqueta, color_tipo = ETIQUETAS_TIPO[nodo.tipo_control], color_de_tipo(nodo.tipo_control)
    ancho_chip = fuentes.pequena.size(etiqueta)[0] + 24
    chip = pygame.Rect(x, y, ancho_chip, 26)
    pygame.draw.rect(pantalla, color_tipo, chip, border_radius=13)
    tema.dibujar_texto(pantalla, fuentes.pequena, etiqueta, tema.color_sobre(color_tipo), center=chip.center)
    if nodo.costo > 0:
        tema.dibujar_texto(pantalla, fuentes.normal, f"Costo: ${formato_numero(nodo.costo)}",
                           tema.COLOR_AMARILLO, midleft=(chip.right + 18, chip.centery))
    y += 40

    estado = evaluar_estado(nodo, recursos)
    if estado == "desbloqueado":
        texto_estado, color_estado = "Ya desbloqueado.", tema.COLOR_VERDE
    elif estado == "bloqueado_padre":
        texto_estado, color_estado = "Primero debes desbloquear el nodo anterior.", tema.COLOR_ROJO
    elif estado == "bloqueado_dinero":
        falta = nodo.costo - recursos.dinero
        texto_estado, color_estado = f"Te faltan ${formato_numero(falta)} para poder comprarlo.", tema.COLOR_ROJO
    else:
        texto_estado, color_estado = "Disponible para comprar.", tema.COLOR_VERDE
    tema.dibujar_texto(pantalla, fuentes.normal, texto_estado, color_estado, topleft=(x, y))
    y += 34

    for linea in tema.envolver_texto(fuentes.normal, nodo.descripcion, ancho_texto):
        tema.dibujar_texto(pantalla, fuentes.normal, linea, tema.COLOR_TEXTO, topleft=(x, y))
        y += 26

    y += 8
    for texto in lineas_de_efectos(nodo):
        for linea in tema.envolver_texto(fuentes.normal, texto, ancho_texto):
            tema.dibujar_texto(pantalla, fuentes.normal, linea, tema.COLOR_CIAN, topleft=(x, y))
            y += 26

    if estado == "desbloqueado":
        _dibujar_controles(pantalla, fuentes, nodo)

    if estado == "disponible":
        tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_COMPRAR, "Comprar", tema.COLOR_BOTON_OK)
        tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_CANCELAR, "Cancelar", tema.COLOR_BOTON_PELIGRO)
    else:
        tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_CERRAR, "Cerrar", tema.COLOR_PANEL_CLARO)
