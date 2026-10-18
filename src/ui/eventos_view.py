"""
Aviso (toast) que aparece cuando ocurre un evento aleatorio: baja desde arriba,
se queda unos segundos y vuelve a subir. Se puede cerrar haciendo clic.

Muestra el título y la descripción del evento, sus efectos con colores
(verde si suma, rojo si resta) y una nota si el árbol influyó: "tu seguridad
redujo el daño" o "contuvo la propagación", o por cuáles regiones se regó.
"""

import pygame

from ui import tema
from ui.animacion import ease_out_cubic
from ui.formato import formatear_efecto
from ui.tema import ANCHO
from eventos.evento import POSITIVO

DURACION_AVISO = 7.0     # segundos que el aviso permanece en pantalla
DURACION_ENTRADA = 0.35  # segundos que tarda en bajar y en subir

RECT_AVISO = pygame.Rect((ANCHO - 620) // 2, 134, 620, 150)


def _nota(resultado, mundo):
    """Línea final del aviso, o '' si no hay nada que aclarar."""
    if resultado.regiones:
        nombres = ", ".join(mundo.regiones[i].nombre for i in resultado.regiones)
        plural = "regiones" if len(resultado.regiones) != 1 else "región"
        texto = f"Alcanzó {len(resultado.regiones)} {plural}: {nombres}"
        if resultado.contenido:
            texto = "Tu seguridad contuvo la propagación. " + texto
        return texto
    if resultado.mitigado:
        return "Tu seguridad redujo el daño a la mitad."
    return ""


def dibujar_aviso(pantalla, fuentes, resultado, tiempo, mundo):
    """`tiempo` son los segundos desde que apareció el aviso."""
    entrada = ease_out_cubic(tiempo / DURACION_ENTRADA)
    salida = ease_out_cubic((DURACION_AVISO - tiempo) / DURACION_ENTRADA)
    avance = min(entrada, salida)
    rect = RECT_AVISO.move(0, -int((1 - avance) * RECT_AVISO.bottom))

    evento = resultado.evento
    color = tema.COLOR_VERDE if evento.tono == POSITIVO else tema.COLOR_ROJO
    tema.dibujar_panel(pantalla, rect, radio=18, borde=color, grosor=3)

    centro_icono = (rect.x + 44, rect.y + 44)
    pygame.draw.circle(pantalla, color, centro_icono, 24)
    tema.dibujar_texto(pantalla, fuentes.subtitulo, "+" if evento.tono == POSITIVO else "!",
                       tema.color_sobre(color), center=centro_icono)

    x = rect.x + 84
    ancho_texto = rect.width - 84 - 24
    tema.dibujar_texto(pantalla, fuentes.boton, evento.titulo, tema.COLOR_TEXTO, topleft=(x, rect.y + 14))

    y = rect.y + 48
    for linea in tema.envolver_texto(fuentes.pequena, evento.descripcion, ancho_texto)[:2]:
        tema.dibujar_texto(pantalla, fuentes.pequena, linea, tema.COLOR_TEXTO_SEC, topleft=(x, y))
        y += 22

    # Efectos, cada uno con su color
    cursor = x
    for clave, valor in resultado.efectos.items():
        if valor == 0:
            continue
        texto = formatear_efecto(clave, valor)
        ancho = fuentes.normal.size(texto)[0]
        if cursor + ancho > rect.right - 16:
            break
        tema.dibujar_texto(pantalla, fuentes.normal, texto,
                           tema.COLOR_VERDE if valor > 0 else tema.COLOR_ROJO,
                           topleft=(cursor, rect.y + 98))
        cursor += ancho + 18

    nota = _nota(resultado, mundo)
    if nota:
        linea = tema.envolver_texto(fuentes.pequena, nota, ancho_texto)
        texto = linea[0] if len(linea) == 1 else linea[0].rstrip(" ,.:") + "…"
        tema.dibujar_texto(pantalla, fuentes.pequena, texto, tema.COLOR_CIAN, topleft=(x, rect.y + 124))
