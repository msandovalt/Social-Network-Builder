"""
Pantalla de Fin de Partida (Victory / Game Over) con Métricas y Post-Mortem.

Muestra:
- Motivo de finalización: éxito al dominar el mapa, quiebra financiera o
  saturación/éxodo de servidores y usuarios.
- Gráfico lineal comparativo de retención (bienestar) y crecimiento de usuarios
  ronda a ronda (con marcadores de forma distintos para accesibilidad/daltonismo).
- Desglose de estadísticas clave: total de usuarios pico alcanzado, dinero
  generado acumulado, rondas sobrevividas y regiones conquistadas.
- Calificación final de desempeño (S / A / B / C).
- Botón de reinicio rápido de la partida sin reiniciar la aplicación y botón de
  salida.
"""

import pygame

from ui import tema
from ui.formato import formato_numero
from ui.tema import ANCHO
from tree.ronda import VICTORIA, QUIEBRA, EXODO, SATURACION, UMBRAL_FUGA

RECT_PANEL_RESUMEN = pygame.Rect(32, 32, ANCHO - 64, 656)
RECT_PANEL_GRAFICO = pygame.Rect(48, 224, 700, 356)
RECT_PANEL_ESTADISTICAS = pygame.Rect(772, 224, 460, 356)
RECT_GRAFICO = RECT_PANEL_GRAFICO
RECT_ESTADISTICAS = RECT_PANEL_ESTADISTICAS

RECT_BOTON_NUEVA = pygame.Rect(ANCHO // 2 - 280, 614, 260, 56)
RECT_BOTON_SALIR = pygame.Rect(ANCHO // 2 + 20, 614, 260, 56)

UMBRAL_BIENESTAR_SANO = 60  # con este bienestar o más, la victoria se considera "sana"
MENSAJE_VICTORIA_SANA = "Y lo lograste cuidando el bienestar de tu comunidad. Así se construye una red sana."
MENSAJE_VICTORIA_BAJO_BIENESTAR = (
    "Conquistaste el planeta, pero el bienestar de tus usuarios quedó bajo. "
    "¿Podrías lograrlo cuidándolos más?"
)

MENSAJE_EXODO_BIENESTAR = (
    "Con el bienestar tan bajo, tus usuarios se fueron. "
    "Una red que los cuida es una red que crece."
)

MOTIVOS_FIN = {
    VICTORIA: "Éxito al dominar el mapa: tu red conectó todas las regiones del planeta.",
    QUIEBRA: "Quiebra financiera: te quedaste sin dinero para sostener la red.",
    EXODO: "Saturación y éxodo: todos tus usuarios abandonaron la plataforma.",
    SATURACION: "Saturación total de servidores: la infraestructura colapsó bajo la demanda.",
}


def _color_calificacion(letra):
    """Devuelve el color de la calificación leyendo la paleta activa en tiempo de dibujo."""
    mapa = {
        "S": tema.COLOR_AMARILLO,
        "A": tema.COLOR_VERDE,
        "B": tema.COLOR_CIAN,
        "C": tema.COLOR_ROSA,
    }
    return mapa.get(letra, tema.COLOR_TEXTO)


def calcular_calificacion(resultado, resumen):
    """Calcula la calificación final de desempeño ('S', 'A', 'B' o 'C') según
    el resultado, el bienestar final, las regiones conquistadas y los usuarios pico."""
    regiones = resumen.get("regiones", 1)
    total_regiones = max(1, resumen.get("total_regiones", 8))
    bienestar = resumen.get("bienestar", 0)
    reputacion = resumen.get("reputacion", 0)
    usuarios_pico = resumen.get("usuarios_pico", resumen.get("usuarios", 0))

    if resultado == VICTORIA:
        if bienestar >= UMBRAL_BIENESTAR_SANO and reputacion >= 60:
            return "S"
        return "A"

    progreso_mapa = regiones / total_regiones
    if progreso_mapa >= 0.75 or (progreso_mapa >= 0.5 and bienestar >= 50 and usuarios_pico >= 3000):
        return "A"
    if progreso_mapa >= 0.35 or usuarios_pico >= 1500 or resumen.get("rondas", 0) >= 6:
        return "B"
    return "C"


def _extraer_series(resumen):
    """Obtiene las listas de (ronda, usuarios, bienestar) para graficar."""
    historial = resumen.get("historial") or []
    if not historial:
        usuarios = resumen.get("usuarios", 500)
        bienestar = resumen.get("bienestar", 70)
        return [0, 1], [500, usuarios], [70, bienestar]

    rondas = [m.get("ronda", i) for i, m in enumerate(historial)]
    usuarios = [m.get("usuarios", 0) for m in historial]
    bienestar = [m.get("bienestar", 0) for m in historial]
    if len(rondas) == 1:
        rondas = [0, max(1, resumen.get("rondas", 1))]
        usuarios = [usuarios[0], resumen.get("usuarios", usuarios[0])]
        bienestar = [bienestar[0], resumen.get("bienestar", bienestar[0])]
    return rondas, usuarios, bienestar


def _dibujar_rombo(pantalla, color, centro, radio=5):
    cx, cy = centro
    puntos = [(cx, cy - radio), (cx + radio, cy), (cx, cy + radio), (cx - radio, cy)]
    pygame.draw.polygon(pantalla, color, puntos)


def _dibujar_grafico(pantalla, fuentes, resumen):
    rect = RECT_PANEL_GRAFICO
    tema.dibujar_panel(pantalla, rect, radio=20)

    color_u = tema.COLOR_RECURSO["usuarios"]
    color_b = tema.COLOR_RECURSO["bienestar"]

    tema.dibujar_texto(pantalla, fuentes.boton, "Evolución por Ronda",
                       tema.COLOR_TEXTO, topleft=(rect.x + 24, rect.y + 18))

    # Leyenda del gráfico con formas distintas (círculo vs rombo) para daltonismo
    x_ley = rect.right - 290
    y_ley = rect.y + 24
    pygame.draw.line(pantalla, color_u, (x_ley, y_ley + 8), (x_ley + 24, y_ley + 8), 3)
    pygame.draw.circle(pantalla, color_u, (x_ley + 12, y_ley + 8), 4)
    tema.dibujar_texto(pantalla, fuentes.pequena, "Usuarios", color_u, topleft=(x_ley + 30, y_ley - 3))

    x_ley2 = x_ley + 124
    pygame.draw.line(pantalla, color_b, (x_ley2, y_ley + 8), (x_ley2 + 24, y_ley + 8), 3)
    _dibujar_rombo(pantalla, color_b, (x_ley2 + 12, y_ley + 8), 5)
    tema.dibujar_texto(pantalla, fuentes.pequena, "Retención %", color_b, topleft=(x_ley2 + 30, y_ley - 3))

    area = pygame.Rect(rect.x + 62, rect.y + 66, rect.width - 96, rect.height - 108)
    pygame.draw.rect(pantalla, tema.oscurecer(tema.COLOR_PANEL, 0.35), area, border_radius=10)
    pygame.draw.rect(pantalla, tema.COLOR_BORDE, area, width=1, border_radius=10)

    # Líneas guía horizontales
    color_guia = tema.mezclar(tema.COLOR_PANEL, tema.COLOR_BORDE, 0.45)
    for i in range(1, 4):
        gy = area.y + (area.height * i) // 4
        pygame.draw.line(pantalla, color_guia, (area.left, gy), (area.right, gy), 1)

    rondas, serie_u, serie_b = _extraer_series(resumen)
    max_u = max(max(serie_u), 100)
    min_u = 0
    n = len(rondas)

    puntos_u = []
    puntos_b = []
    pad_x = 16
    pad_y = 14
    ancho_util = max(1, area.width - 2 * pad_x)
    alto_util = max(1, area.height - 2 * pad_y)

    for idx in range(n):
        proporcion_x = idx / max(1, n - 1)
        px = int(area.left + pad_x + proporcion_x * ancho_util)

        norm_u = (serie_u[idx] - min_u) / max(1, max_u - min_u)
        py_u = int(area.bottom - pad_y - norm_u * alto_util)
        puntos_u.append((px, py_u))

        norm_b = max(0.0, min(1.0, serie_b[idx] / 100.0))
        py_b = int(area.bottom - pad_y - norm_b * alto_util)
        puntos_b.append((px, py_b))

    if len(puntos_u) >= 2:
        pygame.draw.lines(pantalla, color_u, False, puntos_u, 3)
    if len(puntos_b) >= 2:
        pygame.draw.lines(pantalla, color_b, False, puntos_b, 3)

    for pu, pb in zip(puntos_u, puntos_b):
        pygame.draw.circle(pantalla, color_u, pu, 4)
        _dibujar_rombo(pantalla, color_b, pb, 5)

    # Etiquetas de ejes
    tema.dibujar_texto(pantalla, fuentes.arbol_pequena, formato_numero(max_u), color_u,
                       midright=(area.left - 8, area.top + pad_y))
    tema.dibujar_texto(pantalla, fuentes.arbol_pequena, "0", tema.COLOR_TEXTO_SEC,
                       midright=(area.left - 8, area.bottom - pad_y))
    tema.dibujar_texto(pantalla, fuentes.arbol_pequena, f"R{rondas[0]}", tema.COLOR_TEXTO_SEC,
                       midtop=(area.left + pad_x, area.bottom + 6))
    tema.dibujar_texto(pantalla, fuentes.arbol_pequena, f"R{rondas[-1]}", tema.COLOR_TEXTO_SEC,
                       midtop=(area.right - pad_x, area.bottom + 6))


def _dibujar_estadisticas(pantalla, fuentes, resultado, resumen):
    rect = RECT_PANEL_ESTADISTICAS
    tema.dibujar_panel(pantalla, rect, radio=20)

    calificacion = resumen.get("calificacion") or calcular_calificacion(resultado, resumen)
    color_cal = _color_calificacion(calificacion)

    tema.dibujar_texto(pantalla, fuentes.boton, "Post-Mortem y Métricas",
                       tema.COLOR_TEXTO, topleft=(rect.x + 24, rect.y + 18))

    # Insignia de calificación S / A / B / C
    insignia = pygame.Rect(rect.right - 92, rect.y + 16, 68, 68)
    pygame.draw.rect(pantalla, tema.oscurecer(color_cal, 0.72), insignia, border_radius=16)
    pygame.draw.rect(pantalla, color_cal, insignia, width=3, border_radius=16)
    tema.dibujar_texto(pantalla, fuentes.arbol_pequena, "RANGO", tema.COLOR_TEXTO_SEC,
                       midtop=(insignia.centerx, insignia.top + 6))
    tema.dibujar_texto(pantalla, fuentes.subtitulo, calificacion, color_cal,
                       center=(insignia.centerx, insignia.centery + 10))

    usuarios_pico = resumen.get("usuarios_pico", resumen.get("usuarios", 0))
    dinero_gen = resumen.get("dinero_generado", 0)
    rondas = resumen.get("rondas", 0)
    regiones = resumen.get("regiones", 1)
    total_reg = resumen.get("total_regiones", 8)
    bienestar = resumen.get("bienestar", 0)
    reputacion = resumen.get("reputacion", 0)

    filas = (
        ("Usuarios pico alcanzados", formato_numero(usuarios_pico), tema.COLOR_RECURSO["usuarios"]),
        ("Dinero total generado", f"${formato_numero(dinero_gen)}", tema.COLOR_RECURSO["dinero"]),
        ("Rondas sobrevividas", str(rondas), tema.COLOR_TEXTO),
        ("Regiones conquistadas", f"{regiones} / {total_reg}", tema.COLOR_AMARILLO),
        ("Retención / Bienestar final", f"{formato_numero(bienestar)}%", tema.COLOR_RECURSO["bienestar"]),
        ("Reputación final", f"{formato_numero(reputacion)} pts", tema.COLOR_RECURSO["reputacion"]),
    )

    y = rect.y + 78
    x_izq = rect.x + 24
    x_der_insignia = rect.right - 108  # deja espacio para la insignia en la primera fila
    for i, (etiqueta, valor, color) in enumerate(filas):
        limite_der = x_der_insignia if i < 1 else rect.right - 24
        tema.dibujar_texto(pantalla, fuentes.pequena, etiqueta, tema.COLOR_TEXTO_SEC, topleft=(x_izq, y))
        tema.dibujar_texto(pantalla, fuentes.normal, valor, color, topright=(limite_der, y - 2))
        y += 42


def dibujar_fin(pantalla, fuentes, resultado, resumen, t):
    """Dibuja la pantalla completa de Fin de Partida con diagnóstico, gráfico
    lineal y desglose de métricas."""
    gano = resultado == VICTORIA
    tema.dibujar_fondo(pantalla, t)

    titulo = "¡Conquistaste el planeta!" if gano else "Fin de la partida"
    tema.dibujar_texto(pantalla, fuentes.titulo, titulo,
                       tema.COLOR_VERDE if gano else tema.COLOR_TEXTO, center=(ANCHO // 2, 62))

    if gano:
        subtitulo = f"Tu red social conectó a las {resumen.get('total_regiones', 8)} regiones."
        color_subtitulo = tema.COLOR_TEXTO
    else:
        subtitulo = MOTIVOS_FIN.get(resultado, "La partida ha finalizado.")
        color_subtitulo = tema.COLOR_ROJO
    tema.dibujar_texto(pantalla, fuentes.boton, subtitulo, color_subtitulo, center=(ANCHO // 2, 124))

    if gano:
        sano = resumen.get("bienestar", 0) >= UMBRAL_BIENESTAR_SANO
        mensaje = MENSAJE_VICTORIA_SANA if sano else MENSAJE_VICTORIA_BAJO_BIENESTAR
        y = 158
        for linea in tema.envolver_texto(fuentes.normal, mensaje, 920)[:2]:
            tema.dibujar_texto(pantalla, fuentes.normal, linea,
                               tema.COLOR_VERDE if sano else tema.COLOR_AMARILLO, center=(ANCHO // 2, y))
            y += 24
    elif resultado == EXODO and resumen.get("bienestar", 100) < UMBRAL_FUGA:
        y = 158
        for linea in tema.envolver_texto(fuentes.normal, MENSAJE_EXODO_BIENESTAR, 920)[:2]:
            tema.dibujar_texto(pantalla, fuentes.normal, linea, tema.COLOR_AMARILLO, center=(ANCHO // 2, y))
            y += 24

    _dibujar_grafico(pantalla, fuentes, resumen)
    _dibujar_estadisticas(pantalla, fuentes, resultado, resumen)

    tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_NUEVA, "Nueva partida", tema.COLOR_ACENTO, radio=14)
    tema.dibujar_boton(pantalla, fuentes.boton, RECT_BOTON_SALIR, "Salir", tema.COLOR_BOTON_PELIGRO, radio=14)
