"""
Estado y flujo del juego.

Flujo de pantallas: Menú -> Principal (hub) -> Árbol / Mapa, con Pausa
disponible desde cualquiera de las tres últimas. La Ayuda se abre desde el menú,
la pausa o el botón "?" de las pantallas de juego, y siempre vuelve a donde
estabas (`_abrir` / `_volver`). Accesibilidad (paleta para daltonismo) se abre
igual y se recuerda entre partidas si se le pasa un objeto `Ajustes`. Si la partida termina
(quiebra o éxodo de usuarios) se pasa a la pantalla Fin.

Cada pantalla tiene su propio manejador de clics (`_click_<pantalla>`), y
`manejar_evento` solo despacha al que corresponde. Así, agregar una pantalla
nueva (eventos, mapa real) no obliga a tocar un `if/elif` gigante.

Además de la lógica, `Juego` lleva el estado puramente visual: tiempo para las
animaciones, contadores que suben y bajan suavemente, partículas de
celebración y el fundido entre pantallas.
"""

import random

import pygame

from audio import GestorAudio
from eventos.evento import ResultadoEvento, ALERTA_BIENESTAR, NEGATIVO
from eventos.gestor import GestorEventos
from mapa.mundo import Mundo
from tree.arbol import Arbol
from tree.recursos import Recursos
from tree.ronda import Rondas, VICTORIA, UMBRAL_FUGA
from minijuego.tragamonedas import (
    Tragamonedas, GIRANDO, POR_RESOLVER, RESUELTO, INACTIVO,
)

from ui import tema
from ui.tema import crear_fuentes  # noqa: F401  (main.py lo importa desde aquí)
from ui.animacion import NumeroAnimado
from ui.particulas import SistemaParticulas
from ui.tree_view import dibujar_arbol, nodo_en_posicion
from ui.nodo_detalle_view import (
    dibujar_panel_detalle, evaluar_estado, manejar_click_controles,
    RECT_BOTON_COMPRAR, RECT_BOTON_CANCELAR, RECT_BOTON_CERRAR,
)
from ui.menu_view import (
    dibujar_menu, dibujar_boton_pausa, dibujar_boton_ayuda, dibujar_pausa, dibujar_fin,
    RECT_BOTON_START, RECT_BOTON_AYUDA_MENU, RECT_BOTON_ACCESIBILIDAD_MENU, RECT_BOTON_PAUSA,
    RECT_BOTON_AYUDA_JUEGO, RECT_BOTON_REANUDAR, RECT_BOTON_AYUDA_PAUSA,
    RECT_BOTON_ACCESIBILIDAD_PAUSA, RECT_BOTON_SALIR_PAUSA, RECT_BOTON_SALIR, RECT_BOTON_NUEVA,
)
from ui.resumen_view import (
    calcular_calificacion,
    RECT_BOTON_NUEVA as RECT_BOTON_NUEVA_RESUMEN,
    RECT_BOTON_SALIR as RECT_BOTON_SALIR_RESUMEN,
)
from ui.hub_view import (
    dibujar_principal, dibujar_base, dibujar_boton_volver,
    RECT_BOTON_ARBOL, RECT_BOTON_MAPA, RECT_BOTON_VOLVER,
)
from ui.accesibilidad_view import dibujar_accesibilidad, RECTS_OPCION
from ui.ayuda_contenido import TOTAL_PAGINAS, INDICE_ACCESIBILIDAD
from ui.ayuda_view import (
    dibujar_ayuda, pagina_valida, RECTS_TAB, RECT_BOTON_ANTERIOR, RECT_BOTON_SIGUIENTE,
    RECT_BOTON_ABRIR_ACCESIBILIDAD,
)
from ui.paletas import OPCIONES, es_paleta_valida
from ui.eventos_view import dibujar_aviso, DURACION_AVISO, RECT_AVISO
from ui.mapa_view import dibujar_mapa, region_en_posicion, POSICIONES_REGION, RECT_BOTON_EXPANDIR
from ui.tragamonedas_view import dibujar_tragamonedas, RECTS_REEL, RECT_BOTON_ACCION

MENU = "menu"
PRINCIPAL = "principal"
ARBOL = "arbol"
MAPA = "mapa"
PAUSA = "pausa"
FIN = "fin"
AYUDA = "ayuda"
ACCESIBILIDAD = "accesibilidad"

PANTALLAS_DE_JUEGO = (PRINCIPAL, ARBOL, MAPA)  # donde corre el tiempo y se puede pausar
ESTADOS_CONGELADOS = (PAUSA, AYUDA, ACCESIBILIDAD)  # el juego se ve igual pero no avanza

TECLAS_REEL = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}

RECURSOS_VISIBLES = ("dinero", "usuarios", "bienestar", "reputacion", "engagement")
DURACION_FADE = 0.25  # segundos del fundido al cambiar de pantalla


class Juego:
    def __init__(self, pantalla=None, fuentes=None, ajustes=None, audio=None):
        self.pantalla = pantalla
        self.fuentes = fuentes
        self.ajustes = ajustes  # opcional: guarda la paleta elegida entre partidas
        if ajustes is not None:
            tema.aplicar_paleta(ajustes.daltonismo)
        if audio is not None:
            self.audio = audio
        elif ajustes is not None:
            self.audio = GestorAudio(
                volumen_sfx=ajustes.volumen_sfx,
                volumen_musica=ajustes.volumen_musica,
                mute=ajustes.mute,
            )
        else:
            self.audio = GestorAudio()
        self.corriendo = True
        self.estado = MENU
        self.estado_antes_pausa = None
        self._origen = {}          # pantalla secundaria -> pantalla a la que se vuelve
        self.pagina_ayuda = 0
        self.tiempo = 0.0   # segundos desde que arrancó la ventana (para las animaciones)
        self.fade = 0.0     # 1.0 recién cambiada la pantalla, baja a 0
        self.nueva_partida()

    def nueva_partida(self):
        """Reinicia todo el estado de la partida (no el de la ventana)."""
        self.recursos = Recursos()
        self.arbol = Arbol.construir_arbol_inicial()
        self.arbol.desbloquear_gratuitos(self.recursos)
        self.maquina = Tragamonedas()
        self.rondas = Rondas()
        self.mundo = Mundo.construir_mundo_inicial()
        self.recursos.actualizar_limite_usuarios(self.mundo.capacidad_total())
        self.rondas.registrar_muestra(self.recursos, 0)
        self.eventos = GestorEventos()
        self.aviso = None          # ResultadoEvento que se está mostrando, o None
        self.tiempo_aviso = 0.0
        self._alerta_bienestar = False  # ya se avisó que el bienestar está bajo
        self.tiempo_fin = 0.0      # segundos en la pantalla de fin (para el confeti)
        self._confeti = 0.0
        self.nodo_seleccionado = None
        self.region_seleccionada = None
        self.particulas = SistemaParticulas()
        self.contadores = {
            nombre: NumeroAnimado(getattr(self.recursos, nombre)) for nombre in RECURSOS_VISIBLES
        }

    def _ir_a(self, estado):
        """Cambia de pantalla con un breve fundido."""
        self.estado = estado
        self.fade = 1.0
        if estado == FIN:
            self.aviso = None
            self.tiempo_fin = 0.0
            self._confeti = 0.0
            self.rondas.registrar_muestra(self.recursos, self.rondas.numero)
            self.audio.fin_partida(victoria=(self.rondas.resultado == VICTORIA))

    # ------------------------------------------------------------------ eventos

    def manejar_evento(self, evento):
        if evento.type == pygame.QUIT:
            self.corriendo = False
        elif evento.type == pygame.KEYDOWN:
            self._tecla(evento.key)
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if (self.aviso is not None and self.estado in PANTALLAS_DE_JUEGO
                    and RECT_AVISO.collidepoint(evento.pos)):
                self.aviso = None  # el clic sobre el aviso solo lo cierra
                self.audio.clic_ui()
                return
            manejador = {
                MENU: self._click_menu,
                PRINCIPAL: self._click_principal,
                ARBOL: self._click_arbol,
                MAPA: self._click_mapa,
                PAUSA: self._click_pausa,
                FIN: self._click_fin,
                AYUDA: self._click_ayuda,
                ACCESIBILIDAD: self._click_accesibilidad,
            }[self.estado]
            manejador(evento.pos)

    def _abrir(self, pantalla):
        """Abre una pantalla secundaria (ayuda) recordando de dónde venías."""
        self._origen[pantalla] = self.estado
        self.estado = pantalla

    def _volver(self):
        self.estado = self._origen.get(self.estado, MENU)

    def _pausar(self):
        self.estado_antes_pausa = self.estado
        self.estado = PAUSA

    def _tecla(self, tecla):
        if tecla == pygame.K_m:
            mute = self.audio.alternar_mute()
            if self.ajustes is not None:
                self.ajustes.mute = mute
                self.ajustes.guardar()
            return
        if tecla == pygame.K_ESCAPE:
            if self.estado == ARBOL and self.nodo_seleccionado is not None:
                self.nodo_seleccionado = None
            elif self.estado == MAPA and self.region_seleccionada is not None:
                self.region_seleccionada = None
            elif self.estado in PANTALLAS_DE_JUEGO:
                self._pausar()
            elif self.estado == PAUSA:
                self.estado = self.estado_antes_pausa
            elif self.estado in (AYUDA, ACCESIBILIDAD):
                self._volver()
        elif self.estado == AYUDA and tecla in (pygame.K_LEFT, pygame.K_RIGHT):
            self.pagina_ayuda = pagina_valida(self.pagina_ayuda + (1 if tecla == pygame.K_RIGHT else -1))
            self.audio.clic_ui()
        elif self.estado == PRINCIPAL and tecla in TECLAS_REEL:
            if self.maquina.estado == GIRANDO:
                idx = TECLAS_REEL[tecla]
                if self.maquina.girando[idx]:
                    self.maquina.detener(idx)
                    self.audio.frenar_carrete()

    def _click_menu(self, pos):
        if RECT_BOTON_START.collidepoint(pos):
            self.audio.clic_ui()
            self._ir_a(PRINCIPAL)
        elif RECT_BOTON_AYUDA_MENU.collidepoint(pos):
            self.audio.clic_ui()
            self._abrir(AYUDA)
        elif RECT_BOTON_ACCESIBILIDAD_MENU.collidepoint(pos):
            self.audio.clic_ui()
            self._abrir(ACCESIBILIDAD)

    def _click_principal(self, pos):
        if RECT_BOTON_PAUSA.collidepoint(pos):
            self.audio.clic_ui()
            self._pausar()
        elif RECT_BOTON_AYUDA_JUEGO.collidepoint(pos):
            self.audio.clic_ui()
            self._abrir(AYUDA)
        elif RECT_BOTON_ARBOL.collidepoint(pos):
            self.audio.clic_ui()
            self._ir_a(ARBOL)
        elif RECT_BOTON_MAPA.collidepoint(pos):
            self.audio.clic_ui()
            self._ir_a(MAPA)
        else:
            self._click_tragamonedas(pos)

    def _click_tragamonedas(self, pos):
        for i, rect in enumerate(RECTS_REEL):
            if rect.collidepoint(pos) and self.maquina.estado == GIRANDO:
                if self.maquina.girando[i]:
                    self.maquina.detener(i)
                    self.audio.frenar_carrete()
                return

        if RECT_BOTON_ACCION.collidepoint(pos):
            if self.maquina.estado == INACTIVO:
                if self.maquina.iniciar(self.recursos):
                    self.audio.giro_tragamonedas()
            elif self.maquina.estado == RESUELTO:
                self.audio.clic_ui()
                self.maquina.reiniciar()

    def _click_arbol(self, pos):
        if self.nodo_seleccionado is not None:
            self._click_panel_nodo(pos)
        elif RECT_BOTON_PAUSA.collidepoint(pos):
            self.audio.clic_ui()
            self._pausar()
        elif RECT_BOTON_AYUDA_JUEGO.collidepoint(pos):
            self.audio.clic_ui()
            self._abrir(AYUDA)
        elif RECT_BOTON_VOLVER.collidepoint(pos):
            self.audio.clic_ui()
            self._ir_a(PRINCIPAL)
        else:
            nodo = nodo_en_posicion(self.arbol, pos)
            if nodo is not None:
                self.audio.clic_ui()
            self.nodo_seleccionado = nodo

    def _click_panel_nodo(self, pos):
        nodo = self.nodo_seleccionado
        if evaluar_estado(nodo, self.recursos) == "disponible":
            if RECT_BOTON_COMPRAR.collidepoint(pos):
                comprado = nodo.desbloquear(self.recursos)
                if comprado:
                    self.audio.compra_nodo()
                # Los nodos interactivos dejan el panel abierto para poder configurarlos.
                if not comprado or nodo.tipo_control == "fijo":
                    self.nodo_seleccionado = None
            elif RECT_BOTON_CANCELAR.collidepoint(pos):
                self.audio.clic_ui()
                self.nodo_seleccionado = None
        else:
            if manejar_click_controles(nodo, pos):
                self.audio.clic_ui()
                return
            if RECT_BOTON_CERRAR.collidepoint(pos):
                self.audio.clic_ui()
                self.nodo_seleccionado = None

    def _click_mapa(self, pos):
        if RECT_BOTON_PAUSA.collidepoint(pos):
            self.audio.clic_ui()
            self._pausar()
        elif RECT_BOTON_AYUDA_JUEGO.collidepoint(pos):
            self.audio.clic_ui()
            self._abrir(AYUDA)
        elif RECT_BOTON_VOLVER.collidepoint(pos):
            self.audio.clic_ui()
            self._ir_a(PRINCIPAL)
        elif self.region_seleccionada is not None and RECT_BOTON_EXPANDIR.collidepoint(pos):
            self._expandir(self.region_seleccionada)
        else:
            region = region_en_posicion(self.mundo, pos)
            if region is not None:
                self.audio.clic_ui()
                self.region_seleccionada = region

    def _expandir(self, id_region):
        """Intenta conquistar la región; si lo logra, celebra con partículas."""
        if self.mundo.expandir(id_region, self.arbol, self.recursos):
            self.audio.expansion_region()
            x, y = POSICIONES_REGION[id_region]
            self.particulas.emitir(x, y, tema.COLOR_VERDE, 30)
            self.particulas.emitir(x, y, (255, 255, 255), 8)
            if self.mundo.todas_conquistadas():  # meta cumplida: ganaste
                self.rondas.finalizar(VICTORIA)
                self._ir_a(FIN)

    def _click_pausa(self, pos):
        if RECT_BOTON_REANUDAR.collidepoint(pos):
            self.audio.clic_ui()
            self.estado = self.estado_antes_pausa
        elif RECT_BOTON_AYUDA_PAUSA.collidepoint(pos):
            self.audio.clic_ui()
            self._abrir(AYUDA)
        elif RECT_BOTON_ACCESIBILIDAD_PAUSA.collidepoint(pos):
            self.audio.clic_ui()
            self._abrir(ACCESIBILIDAD)
        elif RECT_BOTON_SALIR_PAUSA.collidepoint(pos):
            self.audio.clic_ui()
            self.corriendo = False

    def _click_ayuda(self, pos):
        if RECT_BOTON_VOLVER.collidepoint(pos):
            self.audio.clic_ui()
            self._volver()
        elif RECT_BOTON_ANTERIOR.collidepoint(pos):
            self.audio.clic_ui()
            self.pagina_ayuda = pagina_valida(self.pagina_ayuda - 1)
        elif RECT_BOTON_SIGUIENTE.collidepoint(pos):
            self.audio.clic_ui()
            self.pagina_ayuda = pagina_valida(self.pagina_ayuda + 1)
        elif self.pagina_ayuda == INDICE_ACCESIBILIDAD and RECT_BOTON_ABRIR_ACCESIBILIDAD.collidepoint(pos):
            self.audio.clic_ui()
            self._abrir(ACCESIBILIDAD)
        else:
            for i, rect in enumerate(RECTS_TAB):
                if rect.collidepoint(pos):
                    self.audio.clic_ui()
                    self.pagina_ayuda = i
                    return

    def _click_accesibilidad(self, pos):
        if RECT_BOTON_VOLVER.collidepoint(pos):
            self.audio.clic_ui()
            self._volver()
            return
        for rect, (id_paleta, _, _) in zip(RECTS_OPCION, OPCIONES):
            if rect.collidepoint(pos):
                self.audio.clic_ui()
                self._elegir_daltonismo(id_paleta)
                return

    def _elegir_daltonismo(self, id_paleta):
        """Aplica la paleta al instante y, si hay ajustes, la recuerda para la próxima vez."""
        if not es_paleta_valida(id_paleta):
            return
        tema.aplicar_paleta(id_paleta)
        if self.ajustes is not None:
            self.ajustes.daltonismo = id_paleta
            self.ajustes.guardar()

    def _click_fin(self, pos):
        if RECT_BOTON_NUEVA.collidepoint(pos) or RECT_BOTON_NUEVA_RESUMEN.collidepoint(pos):
            self.audio.clic_ui()
            self.nueva_partida()
            self._ir_a(PRINCIPAL)
        elif RECT_BOTON_SALIR.collidepoint(pos) or RECT_BOTON_SALIR_RESUMEN.collidepoint(pos):
            self.audio.clic_ui()
            self.corriendo = False

    # ------------------------------------------------------------- actualización

    def actualizar(self, dt):
        self.tiempo += dt
        self.fade = max(0.0, self.fade - dt / DURACION_FADE)

        if self.estado not in ESTADOS_CONGELADOS and self.aviso is not None:
            self.tiempo_aviso += dt
            if self.tiempo_aviso >= DURACION_AVISO:
                self.aviso = None

        if self.estado == PRINCIPAL:
            self.maquina.actualizar(dt)
            # Se resuelve cuando el último carrete terminó de frenar
            if self.maquina.estado == POR_RESOLVER and self.maquina.asentada():
                self.maquina.resolver(self.recursos)
                es_triple = (len(set(self.maquina.indices)) == 1)
                self.audio.premio_tragamonedas(
                    es_triple=es_triple,
                    hay_premio=(self.maquina.resultado_tipo is not None),
                )
                if self.maquina.resultado_tipo is not None:
                    self._celebrar(self.maquina.resultado_tipo)

        if self.estado in PANTALLAS_DE_JUEGO:
            self.rondas.actualizar(dt, self.arbol, self.recursos, self.mundo)
            if self.rondas.terminada:
                self._ir_a(FIN)
            else:
                evento = self.eventos.actualizar(dt, self.arbol, self.recursos, self.mundo)
                if evento is not None:
                    self.aviso = evento
                    self.tiempo_aviso = 0.0
                    self.audio.alerta_evento(
                        critico=(evento.evento.tono == NEGATIVO and not evento.mitigado)
                    )
                self._vigilar_bienestar()

        if self.estado == FIN and self.rondas.resultado == VICTORIA:
            self._lanzar_confeti(dt)

        if self.estado not in ESTADOS_CONGELADOS:
            self.particulas.actualizar(dt)
            for nombre, contador in self.contadores.items():
                contador.actualizar(dt, getattr(self.recursos, nombre))

    def _vigilar_bienestar(self):
        """Avisa una sola vez cuando el bienestar cae bajo el umbral de fuga, y
        vuelve a avisar solo después de que se recupere un poco."""
        bienestar = self.recursos.bienestar
        if bienestar >= UMBRAL_FUGA + 5:
            self._alerta_bienestar = False
        elif bienestar < UMBRAL_FUGA and not self._alerta_bienestar and self.aviso is None:
            self._alerta_bienestar = True
            self.aviso = ResultadoEvento(ALERTA_BIENESTAR, {}, None, [], False, False)
            self.tiempo_aviso = 0.0
            self.audio.alerta_evento(critico=True)

    def _lanzar_confeti(self, dt):
        """Ráfagas de confeti durante los primeros segundos de la victoria."""
        self.tiempo_fin += dt
        self._confeti -= dt
        if self._confeti <= 0 and self.tiempo_fin < 8:
            self._confeti = 0.5
            colores = list(tema.COLOR_RECURSO.values())
            for _ in range(3):
                self.particulas.emitir(random.randint(200, 1080), random.randint(120, 320),
                                       random.choice(colores), 26)

    def _resumen_final(self):
        resumen = {
            "rondas": self.rondas.numero - 1,
            "usuarios": self.recursos.usuarios,
            "usuarios_pico": self.recursos.usuarios_pico,
            "dinero_generado": self.recursos.dinero_generado_total,
            "bienestar": self.recursos.bienestar,
            "reputacion": self.recursos.reputacion,
            "regiones": len(self.mundo.conquistadas()),
            "total_regiones": len(self.mundo.regiones),
            "historial": list(self.rondas.historial),
        }
        resumen["calificacion"] = calcular_calificacion(self.rondas.resultado, resumen)
        return resumen

    def _celebrar(self, simbolo):
        """Ráfaga de partículas sobre cada carrete con el color del símbolo ganador."""
        for rect in RECTS_REEL:
            self.particulas.emitir(rect.centerx, rect.centery, tema.COLOR_RECURSO[simbolo], 22)
            self.particulas.emitir(rect.centerx, rect.centery, (255, 255, 255), 6)

    # ------------------------------------------------------------------- dibujo

    def dibujar(self):
        f = self.fuentes
        if self.estado == MENU:
            dibujar_menu(self.pantalla, f, self.tiempo)
        elif self.estado == FIN:
            dibujar_fin(self.pantalla, f, self.rondas.resultado, self._resumen_final(), self.tiempo)
            self.particulas.dibujar(self.pantalla)
        elif self.estado == AYUDA:
            dibujar_ayuda(self.pantalla, f, self.pagina_ayuda, self.tiempo)
        elif self.estado == ACCESIBILIDAD:
            dibujar_accesibilidad(self.pantalla, f, tema.PALETA_ACTUAL, self.tiempo)
        elif self.estado == PAUSA:
            self._dibujar_pantalla_de_juego(self.estado_antes_pausa, None)
            dibujar_boton_pausa(self.pantalla, f)
            dibujar_boton_ayuda(self.pantalla, f)
            dibujar_pausa(self.pantalla, f)
        else:
            self._dibujar_pantalla_de_juego(self.estado, self.nodo_seleccionado)
            dibujar_boton_pausa(self.pantalla, f)
            dibujar_boton_ayuda(self.pantalla, f)
            if self.aviso is not None:
                dibujar_aviso(self.pantalla, f, self.aviso, self.tiempo_aviso, self.mundo)

        if self.fade > 0:
            tema.dibujar_overlay(self.pantalla, int(255 * self.fade * self.fade), usar_cache=False)

    def _dibujar_pantalla_de_juego(self, estado, nodo_seleccionado):
        """Dibuja Principal, Árbol o Mapa. Se usa tanto para el estado activo
        como para el fondo congelado que se ve detrás del overlay de pausa."""
        f, pantalla = self.fuentes, self.pantalla
        if estado == PRINCIPAL:
            dibujar_principal(pantalla, self)
            dibujar_tragamonedas(pantalla, f, self.maquina, self.recursos, self.tiempo)
            self.particulas.dibujar(pantalla)
        elif estado == ARBOL:
            dibujar_base(pantalla, self, "Árbol de funcionalidades")
            dibujar_boton_volver(pantalla, f)
            dibujar_arbol(pantalla, self.arbol, f, self.recursos, self.tiempo)
            if nodo_seleccionado is not None:
                dibujar_panel_detalle(pantalla, f, nodo_seleccionado, self.recursos)
        elif estado == MAPA:
            dibujar_mapa(pantalla, self)
            dibujar_boton_volver(pantalla, f)
            self.particulas.dibujar(pantalla)
