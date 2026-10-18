"""Pruebas del flujo de pantallas y los clics (sin abrir ninguna ventana).

Usa pygame solo para sus constantes, `Rect` y `Event`; no se dibuja nada,
así que no hace falta una pantalla.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import tempfile

import pygame

import juego as modulo_juego
from ajustes import Ajustes
from juego import Juego, MENU, PRINCIPAL, ARBOL, MAPA, PAUSA, FIN, AYUDA, ACCESIBILIDAD
from ui import tema
from ui.accesibilidad_view import RECTS_OPCION
from ui.ayuda_contenido import INDICE_ACCESIBILIDAD
from ui.ayuda_view import RECT_BOTON_ABRIR_ACCESIBILIDAD
from ui.paletas import OPCIONES
from minijuego.tragamonedas import RESUELTO, POR_RESOLVER, DURACION_ASENTADO
from ui.hub_view import RECT_BOTON_ARBOL, RECT_BOTON_MAPA, RECT_BOTON_VOLVER
from ui.menu_view import (
    RECT_BOTON_START, RECT_BOTON_REANUDAR, RECT_BOTON_NUEVA, RECT_BOTON_PAUSA,
    RECT_BOTON_AYUDA_MENU, RECT_BOTON_AYUDA_JUEGO, RECT_BOTON_AYUDA_PAUSA, RECT_BOTON_SALIR_PAUSA,
    RECT_BOTON_ACCESIBILIDAD_MENU, RECT_BOTON_ACCESIBILIDAD_PAUSA,
)
from ui.nodo_detalle_view import (
    RECT_BOTON_COMPRAR, RECT_BOTON_CERRAR, RECT_INTERRUPTOR, RECT_DIAL_MAS,
    RECT_DIAL_BARRA, RECT_VARIANTES,
)
from ui.tragamonedas_view import RECT_BOTON_ACCION
from ui.mapa_view import POSICIONES_REGION, RECT_BOTON_EXPANDIR, texto_requisito
from ui.eventos_view import RECT_AVISO, DURACION_AVISO
from ui.ayuda_view import RECTS_TAB, RECT_BOTON_ANTERIOR, RECT_BOTON_SIGUIENTE
from ui.ayuda_contenido import TOTAL_PAGINAS
from tree.ronda import VICTORIA
from eventos.gestor import INTERVALO_EVENTOS
from tree.ronda import UMBRAL_FUGA
from ui.tree_view import POSICIONES


VOLVER = RECT_BOTON_VOLVER  # mismo botón del Árbol, el Mapa y la Ayuda


def click(juego, rect_o_pos, boton=1):
    pos = rect_o_pos.center if hasattr(rect_o_pos, "center") else rect_o_pos
    juego.manejar_evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=boton))


def tecla(juego, codigo):
    juego.manejar_evento(pygame.event.Event(pygame.KEYDOWN, key=codigo))


def centro_de_nodo(id_nodo):
    x, y, ancho, alto = POSICIONES[id_nodo]
    return (x + ancho // 2, y + alto // 2)


def nodo(juego, id_nodo):
    return next(n for n in juego.arbol.recorrido_bfs() if n.id == id_nodo)


class TestFlujoDePantallas(unittest.TestCase):
    def setUp(self):
        self.juego = Juego()

    def test_empieza_en_el_menu_y_start_lleva_al_hub(self):
        self.assertEqual(self.juego.estado, MENU)
        click(self.juego, RECT_BOTON_START)
        self.assertEqual(self.juego.estado, PRINCIPAL)

    def test_hub_navega_a_arbol_y_mapa_y_vuelve(self):
        click(self.juego, RECT_BOTON_START)
        click(self.juego, RECT_BOTON_ARBOL)
        self.assertEqual(self.juego.estado, ARBOL)
        click(self.juego, RECT_BOTON_VOLVER)
        click(self.juego, RECT_BOTON_MAPA)
        self.assertEqual(self.juego.estado, MAPA)
        click(self.juego, RECT_BOTON_VOLVER)
        self.assertEqual(self.juego.estado, PRINCIPAL)

    def test_escape_pausa_y_reanuda_en_la_misma_pantalla(self):
        click(self.juego, RECT_BOTON_START)
        click(self.juego, RECT_BOTON_ARBOL)
        tecla(self.juego, pygame.K_ESCAPE)
        self.assertEqual(self.juego.estado, PAUSA)
        click(self.juego, RECT_BOTON_REANUDAR)
        self.assertEqual(self.juego.estado, ARBOL)

    def test_el_tiempo_no_corre_en_pausa_ni_en_el_menu(self):
        self.juego.actualizar(100)
        self.assertEqual(self.juego.rondas.numero, 1)
        click(self.juego, RECT_BOTON_START)
        click(self.juego, RECT_BOTON_PAUSA)
        self.assertEqual(self.juego.estado, PAUSA)
        self.juego.actualizar(100)
        self.assertEqual(self.juego.rondas.numero, 1)

    def test_la_rueda_del_mouse_no_cuenta_como_clic(self):
        click(self.juego, RECT_BOTON_START, boton=4)
        self.assertEqual(self.juego.estado, MENU)


class TestArbolEnElJuego(unittest.TestCase):
    def setUp(self):
        self.juego = Juego()
        click(self.juego, RECT_BOTON_START)
        click(self.juego, RECT_BOTON_ARBOL)

    def test_la_partida_empieza_con_raiz_y_categorias_desbloqueadas(self):
        for id_nodo in ("red_social", "feed", "comunidad", "seguridad"):
            self.assertTrue(nodo(self.juego, id_nodo).desbloqueado, id_nodo)

    def test_comprar_un_nodo_fijo_cobra_y_cierra_el_panel(self):
        click(self.juego, centro_de_nodo("feed_basico"))
        self.assertIsNotNone(self.juego.nodo_seleccionado)
        click(self.juego, RECT_BOTON_COMPRAR)
        self.assertTrue(nodo(self.juego, "feed_basico").desbloqueado)
        self.assertEqual(self.juego.recursos.dinero, 10000 - 2000)
        self.assertIsNone(self.juego.nodo_seleccionado)

    def test_comprar_un_interruptor_deja_el_panel_abierto_y_se_puede_encender(self):
        scroll = nodo(self.juego, "feed_scroll")
        click(self.juego, centro_de_nodo("feed_scroll"))
        click(self.juego, RECT_BOTON_COMPRAR)
        self.assertTrue(scroll.desbloqueado)
        self.assertIs(self.juego.nodo_seleccionado, scroll)

        click(self.juego, RECT_INTERRUPTOR)
        self.assertTrue(scroll.activo)
        click(self.juego, RECT_INTERRUPTOR)
        self.assertFalse(scroll.activo)

        click(self.juego, RECT_BOTON_CERRAR)
        self.assertIsNone(self.juego.nodo_seleccionado)

    def test_dial_se_ajusta_desde_el_panel(self):
        algoritmo = nodo(self.juego, "feed_algoritmo")
        click(self.juego, centro_de_nodo("feed_algoritmo"))
        click(self.juego, RECT_BOTON_COMPRAR)
        click(self.juego, RECT_DIAL_MAS)
        click(self.juego, RECT_DIAL_MAS)
        self.assertEqual(algoritmo.valor, 20)

    def test_dial_se_ajusta_haciendo_clic_en_la_barra(self):
        algoritmo = nodo(self.juego, "feed_algoritmo")
        click(self.juego, centro_de_nodo("feed_algoritmo"))
        click(self.juego, RECT_BOTON_COMPRAR)
        click(self.juego, (RECT_DIAL_BARRA.centerx, RECT_DIAL_BARRA.centery))
        self.assertEqual(algoritmo.valor, 50)
        click(self.juego, (RECT_DIAL_BARRA.right - 1, RECT_DIAL_BARRA.centery))
        self.assertEqual(algoritmo.valor, 100)

    def test_bifurcacion_se_elige_desde_el_panel(self):
        mensajes = nodo(self.juego, "comunidad_mensajes")
        click(self.juego, centro_de_nodo("comunidad_mensajes"))
        click(self.juego, RECT_BOTON_COMPRAR)
        click(self.juego, RECT_VARIANTES[1])
        self.assertEqual(mensajes.variante_actual, list(mensajes.variantes)[1])

    def test_no_se_puede_comprar_si_el_padre_esta_bloqueado(self):
        # Se fuerza un padre bloqueado para comprobar que el botón Comprar no aparece.
        basico = nodo(self.juego, "feed_basico")
        basico.padre.desbloqueado = False
        click(self.juego, centro_de_nodo("feed_basico"))
        click(self.juego, RECT_BOTON_COMPRAR)
        self.assertFalse(basico.desbloqueado)


class TestMapaEnElJuego(unittest.TestCase):
    def setUp(self):
        self.juego = Juego()
        click(self.juego, RECT_BOTON_START)
        click(self.juego, RECT_BOTON_MAPA)

    def cumplir_requisitos_de_centroamerica(self):
        self.juego.arbol.nodo_por_id("feed_basico").desbloquear(self.juego.recursos)
        self.juego.recursos.usuarios = 1000

    def test_el_mapa_empieza_sin_region_elegida_y_con_sudamerica_conquistada(self):
        self.assertEqual(self.juego.estado, MAPA)
        self.assertIsNone(self.juego.region_seleccionada)
        self.assertEqual(self.juego.mundo.conquistadas(), ["sudamerica"])

    def test_clic_en_una_region_la_selecciona(self):
        click(self.juego, POSICIONES_REGION["europa"])
        self.assertEqual(self.juego.region_seleccionada, "europa")

    def test_clic_en_el_vacio_mantiene_la_seleccion(self):
        click(self.juego, POSICIONES_REGION["europa"])
        click(self.juego, (60, 600))
        self.assertEqual(self.juego.region_seleccionada, "europa")

    def test_escape_cierra_la_seleccion_antes_de_pausar(self):
        click(self.juego, POSICIONES_REGION["europa"])
        tecla(self.juego, pygame.K_ESCAPE)
        self.assertIsNone(self.juego.region_seleccionada)
        self.assertEqual(self.juego.estado, MAPA)
        tecla(self.juego, pygame.K_ESCAPE)
        self.assertEqual(self.juego.estado, PAUSA)

    def test_no_se_expande_si_faltan_requisitos(self):
        click(self.juego, POSICIONES_REGION["centroamerica"])
        click(self.juego, RECT_BOTON_EXPANDIR)
        self.assertFalse(self.juego.mundo.regiones["centroamerica"].conquistada)
        self.assertEqual(self.juego.recursos.dinero, 10000)

    def test_expandir_con_los_requisitos_cumplidos_conquista_cobra_y_celebra(self):
        self.cumplir_requisitos_de_centroamerica()
        dinero = self.juego.recursos.dinero
        click(self.juego, POSICIONES_REGION["centroamerica"])
        click(self.juego, RECT_BOTON_EXPANDIR)
        self.assertTrue(self.juego.mundo.regiones["centroamerica"].conquistada)
        self.assertEqual(self.juego.recursos.dinero, dinero - 1500)
        self.assertTrue(self.juego.particulas.hay_activas)

    def test_expandir_dos_veces_no_cobra_dos_veces(self):
        self.cumplir_requisitos_de_centroamerica()
        click(self.juego, POSICIONES_REGION["centroamerica"])
        click(self.juego, RECT_BOTON_EXPANDIR)
        dinero = self.juego.recursos.dinero
        click(self.juego, RECT_BOTON_EXPANDIR)
        self.assertEqual(self.juego.recursos.dinero, dinero)

    def test_el_boton_expandir_sin_region_elegida_no_hace_nada(self):
        click(self.juego, RECT_BOTON_EXPANDIR)
        self.assertIsNone(self.juego.region_seleccionada)
        self.assertEqual(self.juego.mundo.conquistadas(), ["sudamerica"])

    def test_cada_ronda_las_regiones_conquistadas_aportan_su_ingreso(self):
        dinero = self.juego.recursos.dinero
        self.juego.actualizar(self.juego.rondas.duracion)
        self.assertEqual(self.juego.recursos.dinero, dinero + 120)

    def test_una_partida_nueva_reinicia_el_mapa(self):
        self.cumplir_requisitos_de_centroamerica()
        click(self.juego, POSICIONES_REGION["centroamerica"])
        click(self.juego, RECT_BOTON_EXPANDIR)
        self.juego.nueva_partida()
        self.assertEqual(self.juego.mundo.conquistadas(), ["sudamerica"])
        self.assertIsNone(self.juego.region_seleccionada)

    def test_los_textos_de_los_requisitos_son_legibles(self):
        reqs = self.juego.mundo.requisitos("centroamerica", self.juego.arbol, self.juego.recursos)
        textos = [texto_requisito(r) for r in reqs]
        self.assertIn("Usuarios: 500 / 600", textos)
        self.assertTrue(any(t.startswith("Nodo «") for t in textos))
        self.assertTrue(any(t.startswith("Pagar $1.500") for t in textos))


def preparar_conquista_total(juego, excepto="oceania"):
    """Deja todo listo para ganar: nodos desbloqueados, recursos altos y todas
    las regiones conquistadas menos `excepto`."""
    recursos = juego.recursos
    recursos.dinero, recursos.usuarios, recursos.reputacion = 10 ** 7, 99999, 100
    for n in juego.arbol.recorrido_bfs():
        if n.puede_desbloquearse(recursos):
            n.desbloquear(recursos)
    for id_region in ("centroamerica", "norteamerica", "africa", "europa", "medio_oriente", "asia", "oceania"):
        if id_region != excepto:
            recursos.usuarios = 99999  # entre conquistas los usuarios crecen hacia el nuevo tope
            assert juego.mundo.expandir(id_region, juego.arbol, recursos), id_region
    recursos.usuarios = 99999


class TestAyudaEnElJuego(unittest.TestCase):
    def setUp(self):
        self.juego = Juego()

    def test_se_abre_desde_el_menu_y_vuelve_al_menu(self):
        click(self.juego, RECT_BOTON_AYUDA_MENU)
        self.assertEqual(self.juego.estado, AYUDA)
        tecla(self.juego, pygame.K_ESCAPE)
        self.assertEqual(self.juego.estado, MENU)

    def test_el_boton_volver_regresa_a_donde_estabas(self):
        click(self.juego, RECT_BOTON_AYUDA_MENU)
        click(self.juego, VOLVER)
        self.assertEqual(self.juego.estado, MENU)

    def test_se_abre_desde_las_tres_pantallas_de_juego_y_vuelve_a_la_misma(self):
        click(self.juego, RECT_BOTON_START)
        for abrir, esperado in ((None, PRINCIPAL), (RECT_BOTON_ARBOL, ARBOL), (RECT_BOTON_VOLVER, PRINCIPAL),
                                (RECT_BOTON_MAPA, MAPA)):
            if abrir is not None:
                click(self.juego, abrir)
            self.assertEqual(self.juego.estado, esperado)
            click(self.juego, RECT_BOTON_AYUDA_JUEGO)
            self.assertEqual(self.juego.estado, AYUDA)
            tecla(self.juego, pygame.K_ESCAPE)
            self.assertEqual(self.juego.estado, esperado)

    def test_se_abre_desde_la_pausa_y_vuelve_a_la_pausa(self):
        click(self.juego, RECT_BOTON_START)
        tecla(self.juego, pygame.K_ESCAPE)
        click(self.juego, RECT_BOTON_AYUDA_PAUSA)
        self.assertEqual(self.juego.estado, AYUDA)
        tecla(self.juego, pygame.K_ESCAPE)
        self.assertEqual(self.juego.estado, PAUSA)
        click(self.juego, RECT_BOTON_REANUDAR)
        self.assertEqual(self.juego.estado, PRINCIPAL)

    def test_el_boton_salir_de_la_pausa_sigue_funcionando(self):
        click(self.juego, RECT_BOTON_START)
        tecla(self.juego, pygame.K_ESCAPE)
        click(self.juego, RECT_BOTON_SALIR_PAUSA)
        self.assertFalse(self.juego.corriendo)

    def test_el_tiempo_no_corre_mientras_se_lee_la_ayuda(self):
        click(self.juego, RECT_BOTON_START)
        click(self.juego, RECT_BOTON_AYUDA_JUEGO)
        self.juego.actualizar(INTERVALO_EVENTOS * 3)
        self.assertEqual(self.juego.rondas.numero, 1)
        self.assertEqual(len(self.juego.eventos.historial), 0)

    def test_el_aviso_de_un_evento_no_se_apaga_mientras_estas_en_la_ayuda(self):
        click(self.juego, RECT_BOTON_START)
        self.juego.actualizar(INTERVALO_EVENTOS)
        click(self.juego, RECT_BOTON_AYUDA_JUEGO)
        self.juego.actualizar(DURACION_AVISO * 2)
        tecla(self.juego, pygame.K_ESCAPE)
        self.assertIsNotNone(self.juego.aviso)

    def test_navegar_con_las_flechas_respeta_los_limites(self):
        click(self.juego, RECT_BOTON_AYUDA_MENU)
        tecla(self.juego, pygame.K_LEFT)
        self.assertEqual(self.juego.pagina_ayuda, 0)
        for _ in range(TOTAL_PAGINAS + 5):
            tecla(self.juego, pygame.K_RIGHT)
        self.assertEqual(self.juego.pagina_ayuda, TOTAL_PAGINAS - 1)

    def test_navegar_con_los_botones_anterior_y_siguiente(self):
        click(self.juego, RECT_BOTON_AYUDA_MENU)
        click(self.juego, RECT_BOTON_SIGUIENTE)
        click(self.juego, RECT_BOTON_SIGUIENTE)
        self.assertEqual(self.juego.pagina_ayuda, 2)
        click(self.juego, RECT_BOTON_ANTERIOR)
        self.assertEqual(self.juego.pagina_ayuda, 1)
        click(self.juego, RECT_BOTON_ANTERIOR)
        click(self.juego, RECT_BOTON_ANTERIOR)
        self.assertEqual(self.juego.pagina_ayuda, 0)

    def test_las_pestanas_llevan_a_su_pagina(self):
        click(self.juego, RECT_BOTON_AYUDA_MENU)
        click(self.juego, RECTS_TAB[3])
        self.assertEqual(self.juego.pagina_ayuda, 3)

    def test_las_flechas_no_hacen_nada_fuera_de_la_ayuda(self):
        click(self.juego, RECT_BOTON_START)
        tecla(self.juego, pygame.K_RIGHT)
        self.assertEqual(self.juego.pagina_ayuda, 0)
        self.assertEqual(self.juego.estado, PRINCIPAL)

    def test_el_boton_de_ayuda_no_hace_nada_con_un_panel_de_nodo_abierto(self):
        click(self.juego, RECT_BOTON_START)
        click(self.juego, RECT_BOTON_ARBOL)
        click(self.juego, centro_de_nodo("feed_basico"))
        click(self.juego, RECT_BOTON_AYUDA_JUEGO)
        self.assertEqual(self.juego.estado, ARBOL)
        self.assertIsNotNone(self.juego.nodo_seleccionado)


def opcion(id_paleta):
    """Rectángulo de la opción de accesibilidad con ese id."""
    return RECTS_OPCION[[i for i, _, _ in OPCIONES].index(id_paleta)]


class TestAccesibilidadEnElJuego(unittest.TestCase):
    def setUp(self):
        self.juego = Juego()
        self.addCleanup(tema.aplicar_paleta, "normal")  # la paleta es global: se restaura siempre

    def test_se_abre_desde_el_menu_y_vuelve_al_menu(self):
        click(self.juego, RECT_BOTON_ACCESIBILIDAD_MENU)
        self.assertEqual(self.juego.estado, ACCESIBILIDAD)
        tecla(self.juego, pygame.K_ESCAPE)
        self.assertEqual(self.juego.estado, MENU)

    def test_se_abre_desde_la_pausa_y_vuelve_a_la_pausa(self):
        click(self.juego, RECT_BOTON_START)
        tecla(self.juego, pygame.K_ESCAPE)
        click(self.juego, RECT_BOTON_ACCESIBILIDAD_PAUSA)
        self.assertEqual(self.juego.estado, ACCESIBILIDAD)
        click(self.juego, VOLVER)
        self.assertEqual(self.juego.estado, PAUSA)

    def test_se_abre_desde_la_ayuda_y_vuelve_a_la_ayuda_y_luego_al_menu(self):
        click(self.juego, RECT_BOTON_AYUDA_MENU)
        self.juego.pagina_ayuda = INDICE_ACCESIBILIDAD
        click(self.juego, RECT_BOTON_ABRIR_ACCESIBILIDAD)
        self.assertEqual(self.juego.estado, ACCESIBILIDAD)
        tecla(self.juego, pygame.K_ESCAPE)
        self.assertEqual(self.juego.estado, AYUDA)
        tecla(self.juego, pygame.K_ESCAPE)
        self.assertEqual(self.juego.estado, MENU)

    def test_el_boton_de_la_ayuda_solo_existe_en_la_pagina_de_accesibilidad(self):
        click(self.juego, RECT_BOTON_AYUDA_MENU)
        self.juego.pagina_ayuda = 0
        click(self.juego, RECT_BOTON_ABRIR_ACCESIBILIDAD)
        self.assertEqual(self.juego.estado, AYUDA)

    def test_elegir_una_opcion_cambia_la_paleta_al_instante(self):
        click(self.juego, RECT_BOTON_ACCESIBILIDAD_MENU)
        for id_paleta, _, _ in OPCIONES:
            click(self.juego, opcion(id_paleta))
            self.assertEqual(tema.PALETA_ACTUAL, id_paleta)
            self.assertEqual(self.juego.estado, ACCESIBILIDAD)  # sigue en la pantalla para poder probar otra

    def test_volver_a_visión_normal_restaura_los_colores(self):
        click(self.juego, RECT_BOTON_ACCESIBILIDAD_MENU)
        colores_normales = tema.COLOR_VERDE
        click(self.juego, opcion("deuteranopia"))
        self.assertNotEqual(tema.COLOR_VERDE, colores_normales)
        click(self.juego, opcion("normal"))
        self.assertEqual(tema.COLOR_VERDE, colores_normales)

    def test_la_paleta_elegida_se_mantiene_al_empezar_una_partida_nueva(self):
        click(self.juego, RECT_BOTON_ACCESIBILIDAD_MENU)
        click(self.juego, opcion("tritanopia"))
        self.juego.nueva_partida()
        self.assertEqual(tema.PALETA_ACTUAL, "tritanopia")

    def test_el_tiempo_no_corre_en_la_pantalla_de_accesibilidad(self):
        click(self.juego, RECT_BOTON_START)
        tecla(self.juego, pygame.K_ESCAPE)
        click(self.juego, RECT_BOTON_ACCESIBILIDAD_PAUSA)
        self.juego.actualizar(INTERVALO_EVENTOS * 3)
        self.assertEqual(self.juego.rondas.numero, 1)

    def test_un_id_invalido_no_cambia_la_paleta(self):
        self.juego._elegir_daltonismo("marciano")
        self.assertEqual(tema.PALETA_ACTUAL, "normal")

    def test_clic_fuera_de_las_opciones_no_hace_nada(self):
        click(self.juego, RECT_BOTON_ACCESIBILIDAD_MENU)
        click(self.juego, (5, 700))
        self.assertEqual(tema.PALETA_ACTUAL, "normal")
        self.assertEqual(self.juego.estado, ACCESIBILIDAD)


class TestAccesibilidadPersistente(unittest.TestCase):
    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(self.carpeta.cleanup)
        self.addCleanup(tema.aplicar_paleta, "normal")
        self.ruta = os.path.join(self.carpeta.name, "ajustes.json")

    def test_la_eleccion_se_guarda_y_la_siguiente_sesion_la_recupera(self):
        juego = Juego(ajustes=Ajustes(self.ruta))
        click(juego, RECT_BOTON_ACCESIBILIDAD_MENU)
        click(juego, opcion("protanopia"))
        tema.aplicar_paleta("normal")  # simula cerrar y volver a abrir el juego
        Juego(ajustes=Ajustes(self.ruta))
        self.assertEqual(tema.PALETA_ACTUAL, "protanopia")

    def test_sin_ajustes_la_eleccion_funciona_pero_no_se_guarda(self):
        juego = Juego()
        click(juego, RECT_BOTON_ACCESIBILIDAD_MENU)
        click(juego, opcion("tritanopia"))
        self.assertEqual(tema.PALETA_ACTUAL, "tritanopia")
        self.assertFalse(os.path.exists(self.ruta))

    def test_si_no_se_puede_guardar_el_juego_sigue_funcionando(self):
        juego = Juego(ajustes=Ajustes(self.carpeta.name))  # ruta inválida: una carpeta
        click(juego, RECT_BOTON_ACCESIBILIDAD_MENU)
        click(juego, opcion("acromatopsia"))
        self.assertEqual(tema.PALETA_ACTUAL, "acromatopsia")


class TestTopeEnElJuego(unittest.TestCase):
    def setUp(self):
        self.juego = Juego()
        click(self.juego, RECT_BOTON_START)

    def test_la_partida_empieza_con_el_tope_de_sudamerica(self):
        self.assertEqual(self.juego.recursos.limite_usuarios,
                         self.juego.mundo.regiones["sudamerica"].capacidad)

    def test_los_usuarios_no_pasan_del_tope_aunque_ganes_muchos(self):
        self.juego.recursos.aplicar_efectos({"usuarios": 10 ** 7})
        self.assertEqual(self.juego.recursos.usuarios, self.juego.recursos.limite_usuarios)

    def test_una_partida_nueva_vuelve_al_tope_inicial(self):
        self.juego.mundo.regiones["centroamerica"].conquistada = True
        self.juego.nueva_partida()
        self.assertEqual(self.juego.recursos.limite_usuarios,
                         self.juego.mundo.regiones["sudamerica"].capacidad)


class TestVictoria(unittest.TestCase):
    def setUp(self):
        self.juego = Juego()
        click(self.juego, RECT_BOTON_START)
        click(self.juego, RECT_BOTON_MAPA)

    def test_conquistar_la_ultima_region_gana_la_partida(self):
        preparar_conquista_total(self.juego)
        self.assertEqual(self.juego.estado, MAPA)  # con 7 de 8 todavía no se gana
        click(self.juego, POSICIONES_REGION["oceania"])
        click(self.juego, RECT_BOTON_EXPANDIR)
        self.assertTrue(self.juego.mundo.todas_conquistadas())
        self.assertEqual(self.juego.estado, FIN)
        self.assertEqual(self.juego.rondas.resultado, VICTORIA)

    def test_con_siete_regiones_conquistadas_el_juego_sigue(self):
        preparar_conquista_total(self.juego)
        self.juego.actualizar(1.0)
        self.assertEqual(self.juego.estado, MAPA)
        self.assertFalse(self.juego.rondas.terminada)

    def test_tras_ganar_el_tiempo_ya_no_corre_y_hay_confeti(self):
        preparar_conquista_total(self.juego)
        click(self.juego, POSICIONES_REGION["oceania"])
        click(self.juego, RECT_BOTON_EXPANDIR)
        self.juego.actualizar(0.016)
        self.assertTrue(self.juego.particulas.hay_activas)  # confeti de la victoria
        numero = self.juego.rondas.numero
        self.juego.actualizar(self.juego.rondas.duracion * 3)
        self.assertEqual(self.juego.rondas.numero, numero)

    def test_el_resumen_final_refleja_la_partida(self):
        preparar_conquista_total(self.juego)
        resumen = self.juego._resumen_final()
        self.assertEqual(resumen["regiones"], 7)
        self.assertEqual(resumen["total_regiones"], 8)
        self.assertEqual(resumen["usuarios"], self.juego.recursos.usuarios)

    def test_se_puede_empezar_otra_partida_despues_de_ganar(self):
        preparar_conquista_total(self.juego)
        click(self.juego, POSICIONES_REGION["oceania"])
        click(self.juego, RECT_BOTON_EXPANDIR)
        click(self.juego, RECT_BOTON_NUEVA)
        self.assertEqual(self.juego.estado, PRINCIPAL)
        self.assertEqual(self.juego.mundo.conquistadas(), ["sudamerica"])
        self.assertFalse(self.juego.rondas.terminada)


class TestEventosEnElJuego(unittest.TestCase):
    def setUp(self):
        self.juego = Juego()
        click(self.juego, RECT_BOTON_START)

    def test_no_hay_evento_antes_de_los_30_segundos(self):
        self.juego.actualizar(INTERVALO_EVENTOS - 1)
        self.assertIsNone(self.juego.aviso)
        self.assertEqual(len(self.juego.eventos.historial), 0)

    def test_a_los_30_segundos_ocurre_un_evento_y_se_muestra_el_aviso(self):
        self.juego.actualizar(INTERVALO_EVENTOS)
        self.assertEqual(len(self.juego.eventos.historial), 1)
        self.assertIsNotNone(self.juego.aviso)
        self.assertEqual(self.juego.tiempo_aviso, 0.0)

    def test_el_aviso_se_cierra_solo_con_el_tiempo(self):
        self.juego.actualizar(INTERVALO_EVENTOS)
        self.juego.actualizar(DURACION_AVISO + 0.1)
        self.assertIsNone(self.juego.aviso)

    def test_el_clic_sobre_el_aviso_lo_cierra_sin_activar_lo_de_atras(self):
        self.juego.actualizar(INTERVALO_EVENTOS)
        self.assertIsNotNone(self.juego.aviso)
        click(self.juego, RECT_AVISO)
        self.assertIsNone(self.juego.aviso)
        self.assertEqual(self.juego.estado, PRINCIPAL)

    def test_el_clic_fuera_del_aviso_funciona_normal(self):
        self.juego.actualizar(INTERVALO_EVENTOS)
        click(self.juego, RECT_BOTON_ARBOL)
        self.assertEqual(self.juego.estado, ARBOL)
        self.assertIsNotNone(self.juego.aviso)

    def test_los_eventos_no_corren_en_pausa(self):
        tecla(self.juego, pygame.K_ESCAPE)
        self.juego.actualizar(INTERVALO_EVENTOS * 3)
        self.assertEqual(len(self.juego.eventos.historial), 0)

    def test_el_aviso_no_avanza_en_pausa(self):
        self.juego.actualizar(INTERVALO_EVENTOS)
        tecla(self.juego, pygame.K_ESCAPE)
        self.juego.actualizar(DURACION_AVISO * 2)
        self.assertIsNotNone(self.juego.aviso)

    def test_el_temporizador_de_eventos_corre_tambien_en_el_arbol_y_el_mapa(self):
        click(self.juego, RECT_BOTON_ARBOL)
        self.juego.actualizar(INTERVALO_EVENTOS)
        self.assertEqual(len(self.juego.eventos.historial), 1)

    def test_una_partida_nueva_reinicia_los_eventos(self):
        self.juego.actualizar(INTERVALO_EVENTOS)
        self.juego.nueva_partida()
        self.assertIsNone(self.juego.aviso)
        self.assertEqual(self.juego.eventos.historial, [])
        self.assertEqual(self.juego.eventos.acumulado, 0.0)

    def test_al_terminar_la_partida_se_quita_el_aviso(self):
        self.juego.actualizar(INTERVALO_EVENTOS)
        self.juego.recursos.dinero = -50000
        self.juego.actualizar(self.juego.rondas.duracion)
        self.assertEqual(self.juego.estado, FIN)
        self.assertIsNone(self.juego.aviso)


class TestBienestarEnElJuego(unittest.TestCase):
    def setUp(self):
        self.juego = Juego()
        click(self.juego, RECT_BOTON_START)

    def test_con_bienestar_normal_no_hay_alerta(self):
        self.juego.actualizar(0.016)
        self.assertIsNone(self.juego.aviso)

    def test_al_caer_bajo_el_umbral_se_avisa_una_vez(self):
        self.juego.recursos.bienestar = UMBRAL_FUGA - 10
        self.juego.actualizar(0.016)
        self.assertIsNotNone(self.juego.aviso)
        self.assertEqual(self.juego.aviso.evento.id, "alerta_bienestar")

    def test_no_repite_la_alerta_mientras_siga_bajo_ni_despues_de_cerrarla(self):
        self.juego.recursos.bienestar = UMBRAL_FUGA - 10
        self.juego.actualizar(0.016)
        click(self.juego, RECT_AVISO)  # el jugador la cierra
        self.assertIsNone(self.juego.aviso)
        self.juego.actualizar(0.016)
        self.assertIsNone(self.juego.aviso)

    def test_vuelve_a_avisar_si_se_recupera_y_cae_de_nuevo(self):
        self.juego.recursos.bienestar = UMBRAL_FUGA - 10
        self.juego.actualizar(0.016)
        click(self.juego, RECT_AVISO)
        self.juego.recursos.bienestar = UMBRAL_FUGA + 10   # se recupera
        self.juego.actualizar(0.016)
        self.juego.recursos.bienestar = UMBRAL_FUGA - 10   # vuelve a caer
        self.juego.actualizar(0.016)
        self.assertEqual(self.juego.aviso.evento.id, "alerta_bienestar")

    def test_la_alerta_no_pisa_un_evento_que_se_esta_mostrando(self):
        self.juego.actualizar(INTERVALO_EVENTOS)
        evento = self.juego.aviso
        self.juego.recursos.bienestar = 5
        self.juego.actualizar(0.016)
        self.assertIs(self.juego.aviso, evento)

    def test_una_partida_nueva_reinicia_la_alerta(self):
        self.juego.recursos.bienestar = 5
        self.juego.actualizar(0.016)
        self.juego.nueva_partida()
        self.juego.recursos.bienestar = 5
        self.juego.actualizar(0.016)
        self.assertEqual(self.juego.aviso.evento.id, "alerta_bienestar")

    def test_con_bienestar_bajo_los_usuarios_bajan_en_cada_ronda(self):
        self.juego.recursos.bienestar = 0
        usuarios = self.juego.recursos.usuarios
        self.juego.actualizar(self.juego.rondas.duracion)
        # +25 de Sudamérica, pero la fuga (12 %) pesa más
        self.assertLess(self.juego.recursos.usuarios, usuarios)

    def test_el_texto_del_requisito_de_bienestar_es_legible(self):
        self.juego.recursos.bienestar = 33
        reqs = self.juego.mundo.requisitos("africa", self.juego.arbol, self.juego.recursos)
        self.assertIn("Bienestar: 33 / 40", [texto_requisito(r) for r in reqs])


class TestAnimacionesDelJuego(unittest.TestCase):
    def setUp(self):
        self.juego = Juego()
        click(self.juego, RECT_BOTON_START)

    def test_cambiar_de_pantalla_inicia_un_fundido_que_se_apaga(self):
        self.assertEqual(self.juego.fade, 1.0)
        self.juego.actualizar(1.0)
        self.assertEqual(self.juego.fade, 0.0)

    def test_pausar_no_hace_fundido(self):
        self.juego.actualizar(1.0)
        tecla(self.juego, pygame.K_ESCAPE)
        self.assertEqual(self.juego.fade, 0.0)

    def test_los_contadores_siguen_a_los_recursos_con_suavidad(self):
        self.juego.recursos.dinero = 20000
        self.juego.actualizar(0.05)
        valor = self.juego.contadores["dinero"].valor
        self.assertTrue(10000 < valor < 20000)
        for _ in range(300):
            self.juego.actualizar(0.016)
        self.assertEqual(self.juego.contadores["dinero"].valor, 20000)

    def test_una_partida_nueva_reinicia_los_contadores(self):
        self.juego.recursos.dinero = 99999
        self.juego.actualizar(5)
        self.juego.nueva_partida()
        self.assertEqual(self.juego.contadores["dinero"].valor, 10000)

    def test_ganar_en_la_tragamonedas_espera_el_frenado_y_lanza_particulas(self):
        click(self.juego, RECT_BOTON_ACCION)           # jugar
        for codigo in (pygame.K_1, pygame.K_2, pygame.K_3):
            tecla(self.juego, codigo)                  # los tres en el símbolo 0 -> dinero
        self.assertEqual(self.juego.maquina.estado, POR_RESOLVER)

        self.juego.actualizar(DURACION_ASENTADO / 2)   # todavía frenando: no se resuelve
        self.assertEqual(self.juego.maquina.estado, POR_RESOLVER)
        self.assertFalse(self.juego.particulas.hay_activas)

        self.juego.actualizar(DURACION_ASENTADO)       # ya alineados: se resuelve
        self.assertEqual(self.juego.maquina.estado, RESUELTO)
        self.assertEqual(self.juego.maquina.resultado_tipo, "dinero")
        self.assertEqual(self.juego.recursos.dinero, 10000 - 500 + 3000)
        self.assertTrue(self.juego.particulas.hay_activas)


class TestFinDePartida(unittest.TestCase):
    def setUp(self):
        self.juego = Juego()
        click(self.juego, RECT_BOTON_START)

    def test_quiebra_lleva_a_la_pantalla_de_fin(self):
        self.juego.recursos.dinero = -500  # más que el ingreso de la ronda (+120)
        self.juego.actualizar(self.juego.rondas.duracion)
        self.assertEqual(self.juego.estado, FIN)

    def test_nueva_partida_reinicia_todo(self):
        self.juego.recursos.dinero = -500  # más que el ingreso de la ronda (+120)
        self.juego.actualizar(self.juego.rondas.duracion)
        click(self.juego, RECT_BOTON_NUEVA)
        self.assertEqual(self.juego.estado, PRINCIPAL)
        self.assertEqual(self.juego.recursos.dinero, 10000)
        self.assertEqual(self.juego.rondas.numero, 1)
        self.assertTrue(nodo(self.juego, "feed").desbloqueado)


if __name__ == "__main__":
    unittest.main()
