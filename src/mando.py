"""
Soporte completo para control / mando de Xbox (y gamepads compatibles con SDL2).

Combina dos modos de uso simultáneos:
1. Cursor virtual con el Stick Izquierdo o la Cruceta (D-Pad), que mueve el
   puntero por la pantalla (activando los efectos hover existentes) y hace clic
   con el botón A.
2. Atajos directos de mando para jugar sin necesidad de apuntar:
   - A (0): Confirmar / Hacer clic / Iniciar tirada / Frenar siguiente carrete.
   - X (2), Y (3), B (1) durante el giro: Frenar carretes 1, 2 y 3.
   - B (1) fuera del giro: Volver / Cerrar panel / Salir de pausa (ESC).
   - LB (4) y RB (5): Alternar entre Árbol, Principal y Mapa (o páginas de Ayuda).
   - View / Back (6): Abrir o cerrar la Ayuda.
   - Menu / Start (7): Pausar o reanudar la partida.
"""

import pygame

from ui import tema
from ui.tema import ANCHO, ALTO

# Mapeo estándar de botones SDL2 / Xbox en Windows
BOTON_A = 0
BOTON_B = 1
BOTON_X = 2
BOTON_Y = 3
BOTON_LB = 4
BOTON_RB = 5
BOTON_BACK = 6
BOTON_START = 7

ZONA_MUERTA = 0.18
VELOCIDAD_CURSOR = 560.0  # píxeles por segundo a máxima inclinación del stick


class GestorMando:
    def __init__(self):
        self.mandos = {}
        self.x = float(ANCHO // 2)
        self.y = float(ALTO // 2)
        self.activo = False  # True cuando el último input vino del mando
        self._hat_x = 0
        self._hat_y = 0
        self._inicializar_subsistema()

    def _inicializar_subsistema(self):
        try:
            if not pygame.joystick.get_init():
                pygame.joystick.init()
            for i in range(pygame.joystick.get_count()):
                self._conectar_indice(i)
        except pygame.error:
            pass

    def _conectar_indice(self, device_index):
        try:
            joy = pygame.joystick.Joystick(device_index)
            joy.init()
            self.mandos[joy.get_instance_id()] = joy
            self.activo = True
        except pygame.error:
            pass

    @property
    def conectado(self):
        return bool(self.mandos)

    def nombre_mando(self):
        for joy in self.mandos.values():
            try:
                return joy.get_name()
            except pygame.error:
                pass
        return "Mando Xbox"

    def manejar_evento(self, evento, juego):
        """Procesa eventos de conexión, botones y cruceta del mando.
        Devuelve True si el evento fue consumido por el mando."""
        if evento.type == pygame.MOUSEMOTION:
            self.x, self.y = float(evento.pos[0]), float(evento.pos[1])
            self.activo = False
            return False

        if evento.type == getattr(pygame, "JOYDEVICEADDED", None):
            self._conectar_indice(evento.device_index)
            return True

        if evento.type == getattr(pygame, "JOYDEVICEREMOVED", None):
            self.mandos.pop(getattr(evento, "instance_id", None), None)
            if not self.mandos:
                self.activo = False
            return True

        if evento.type == pygame.JOYHATMOTION:
            self.activo = True
            hx, hy = evento.value
            self._hat_x = hx
            self._hat_y = -hy  # en SDL hat_y es +1 arriba, -1 abajo
            if hx != 0 and juego.estado == "ayuda":
                juego._tecla(pygame.K_RIGHT if hx > 0 else pygame.K_LEFT)
            return True

        if evento.type == pygame.JOYBUTTONDOWN:
            self.activo = True
            self._presionar_boton(evento.button, juego)
            return True

        return False

    def _presionar_boton(self, boton, juego):
        from juego import MENU, PRINCIPAL, ARBOL, MAPA, PAUSA, FIN, AYUDA
        from minijuego.tragamonedas import GIRANDO, INACTIVO, RESUELTO
        from ui.menu_view import (
            RECT_BOTON_START, RECT_BOTON_REANUDAR, RECT_BOTON_NUEVA,
            RECT_BOTON_AYUDA_MENU, RECT_BOTON_ACCESIBILIDAD_MENU,
            RECT_BOTON_AYUDA_PAUSA, RECT_BOTON_ACCESIBILIDAD_PAUSA, RECT_BOTON_SALIR_PAUSA,
        )
        from ui.tragamonedas_view import RECT_BOTON_ACCION, RECTS_REEL, RECT_PALANCA
        from ui.hub_view import RECT_BOTON_ARBOL, RECT_BOTON_MAPA, RECT_BOTON_VOLVER
        from ui.eventos_view import RECT_AVISO

        pos = (int(self.x), int(self.y))

        # Si hay un aviso de evento en pantalla, A o B lo cierran rápido
        if juego.aviso is not None and juego.estado in (PRINCIPAL, ARBOL, MAPA):
            if boton in (BOTON_A, BOTON_B):
                juego.aviso = None
                juego.audio.clic_ui()
                return

        if boton == BOTON_START:
            if juego.estado == MENU:
                juego._click_menu(RECT_BOTON_START.center)
            elif juego.estado in (PRINCIPAL, ARBOL, MAPA, PAUSA):
                juego._tecla(pygame.K_ESCAPE)
            elif juego.estado == FIN:
                juego._click_fin(RECT_BOTON_NUEVA.center)
            return

        if boton == BOTON_BACK:
            if juego.estado in (PRINCIPAL, ARBOL, MAPA):
                juego.audio.clic_ui()
                juego._abrir(AYUDA)
            elif juego.estado == AYUDA:
                juego._tecla(pygame.K_ESCAPE)
            return

        if boton in (BOTON_LB, BOTON_RB):
            direccion = 1 if boton == BOTON_RB else -1
            if juego.estado == AYUDA:
                juego._tecla(pygame.K_RIGHT if direccion > 0 else pygame.K_LEFT)
                return
            orden = (ARBOL, PRINCIPAL, MAPA)
            if juego.estado in orden:
                juego.nodo_seleccionado = None
                juego.region_seleccionada = None
                idx = (orden.index(juego.estado) + direccion) % len(orden)
                juego.audio.clic_ui()
                juego._ir_a(orden[idx])
            return

        # En la tragamonedas: X, Y, B frenan los carretes 1, 2 y 3 mientras gira
        if juego.estado == PRINCIPAL and juego.maquina.estado == GIRANDO:
            mapa_carrete = {BOTON_X: pygame.K_1, BOTON_Y: pygame.K_2, BOTON_B: pygame.K_3}
            if boton in mapa_carrete:
                juego._tecla(mapa_carrete[boton])
                return

        if boton == BOTON_B:
            juego._tecla(pygame.K_ESCAPE)
            return

        if boton == BOTON_A:
            # Clic izquierdo virtual exactamente donde está el cursor del mando
            evento_clic = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)
            juego.manejar_evento(evento_clic)

    def actualizar(self, dt):
        """Mueve el cursor virtual leyendo los ejes del stick izquierdo o el D-Pad."""
        dx = float(self._hat_x)
        dy = float(self._hat_y)

        for joy in list(self.mandos.values()):
            try:
                if joy.get_numaxes() >= 2:
                    ax = joy.get_axis(0)
                    ay = joy.get_axis(1)
                    if abs(ax) > ZONA_MUERTA:
                        dx += ax
                        self.activo = True
                    if abs(ay) > ZONA_MUERTA:
                        dy += ay
                        self.activo = True
            except pygame.error:
                pass

        if dx != 0.0 or dy != 0.0:
            self.x = max(8.0, min(float(ANCHO - 8), self.x + dx * VELOCIDAD_CURSOR * dt))
            self.y = max(8.0, min(float(ALTO - 8), self.y + dy * VELOCIDAD_CURSOR * dt))
            try:
                pygame.mouse.set_pos((int(self.x), int(self.y)))
            except pygame.error:
                pass

    def dibujar(self, pantalla, fuentes=None):
        """Dibuja el puntero virtual del mando cuando está activo."""
        if not self.activo:
            return
        cx, cy = int(self.x), int(self.y)
        pygame.draw.circle(pantalla, (0, 0, 0), (cx + 1, cy + 2), 12, width=3)
        pygame.draw.circle(pantalla, tema.COLOR_CIAN, (cx, cy), 11, width=3)
        pygame.draw.circle(pantalla, tema.COLOR_AMARILLO, (cx, cy), 3)
        for ox, oy in ((-15, 0), (15, 0), (0, -15), (0, 15)):
            pygame.draw.line(pantalla, tema.COLOR_CIAN,
                             (cx + ox // 2, cy + oy // 2), (cx + ox, cy + oy), 2)
