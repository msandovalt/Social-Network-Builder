"""
Panel modal que se abre al hacer clic en un nodo del árbol: muestra su
nombre, tipo de control, costo y descripción, y pide confirmar la compra
en vez de desbloquear el nodo de inmediato con un solo clic.
"""

import pygame

RECT_PANEL = pygame.Rect(210, 90, 440, 230)
RECT_BOTON_COMPRAR = pygame.Rect(260, 280, 150, 32)
RECT_BOTON_CANCELAR = pygame.Rect(450, 280, 150, 32)
RECT_BOTON_CERRAR = pygame.Rect(355, 280, 150, 32)  # cuando solo hay un botón

COLOR_PANEL = (35, 35, 42)
COLOR_BORDE = (90, 90, 100)
COLOR_TEXTO = (255, 255, 255)
COLOR_TEXTO_SECUNDARIO = (190, 190, 195)
COLOR_COMPRAR = (60, 150, 130)
COLOR_CANCELAR = (150, 70, 70)
COLOR_CERRAR = (80, 80, 85)

ETIQUETAS_TIPO = {
    "fijo": "Efecto fijo",
    "interruptor": "Interruptor",
    "dial": "Dial",
    "bifurcacion": "Bifurcación",
}


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


def _envolver_texto(fuente, texto, ancho_maximo):
    palabras = texto.split(" ")
    lineas = []
    actual = ""
    for palabra in palabras:
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


def dibujar_panel_detalle(pantalla, fuente, fuente_boton, nodo, recursos):
    overlay = pygame.Surface(pantalla.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    pantalla.blit(overlay, (0, 0))

    pygame.draw.rect(pantalla, COLOR_PANEL, RECT_PANEL, border_radius=10)
    pygame.draw.rect(pantalla, COLOR_BORDE, RECT_PANEL, width=2, border_radius=10)

    x_texto = RECT_PANEL.x + 20
    y = RECT_PANEL.y + 15

    titulo = fuente_boton.render(nodo.nombre, True, COLOR_TEXTO)
    pantalla.blit(titulo, (x_texto, y))
    y += 30

    tipo = fuente.render(ETIQUETAS_TIPO.get(nodo.tipo_control, nodo.tipo_control), True, COLOR_TEXTO_SECUNDARIO)
    pantalla.blit(tipo, (x_texto, y))
    y += 26

    estado = evaluar_estado(nodo, recursos)

    if estado == "desbloqueado":
        estado_texto = fuente.render("Ya desbloqueado.", True, (140, 210, 170))
    elif estado == "bloqueado_padre":
        estado_texto = fuente.render(f"Bloqueado: primero desbloquea '{nodo.padre.nombre}'.", True, (210, 140, 140))
    elif estado == "bloqueado_dinero":
        falta = nodo.costo - recursos.dinero
        estado_texto = fuente.render(f"Te faltan ${falta} para poder comprarlo.", True, (210, 140, 140))
    else:
        estado_texto = fuente.render(f"Costo: ${nodo.costo}", True, COLOR_TEXTO)
    pantalla.blit(estado_texto, (x_texto, y))
    y += 30

    for linea in _envolver_texto(fuente, nodo.descripcion, RECT_PANEL.width - 40):
        render_linea = fuente.render(linea, True, COLOR_TEXTO_SECUNDARIO)
        pantalla.blit(render_linea, (x_texto, y))
        y += 20

    if estado == "disponible":
        pygame.draw.rect(pantalla, COLOR_COMPRAR, RECT_BOTON_COMPRAR, border_radius=8)
        texto_comprar = fuente_boton.render("Comprar", True, COLOR_TEXTO)
        pantalla.blit(texto_comprar, texto_comprar.get_rect(center=RECT_BOTON_COMPRAR.center))

        pygame.draw.rect(pantalla, COLOR_CANCELAR, RECT_BOTON_CANCELAR, border_radius=8)
        texto_cancelar = fuente_boton.render("Cancelar", True, COLOR_TEXTO)
        pantalla.blit(texto_cancelar, texto_cancelar.get_rect(center=RECT_BOTON_CANCELAR.center))
    else:
        pygame.draw.rect(pantalla, COLOR_CERRAR, RECT_BOTON_CERRAR, border_radius=8)
        texto_cerrar = fuente_boton.render("Cerrar", True, COLOR_TEXTO)
        pantalla.blit(texto_cerrar, texto_cerrar.get_rect(center=RECT_BOTON_CERRAR.center))
