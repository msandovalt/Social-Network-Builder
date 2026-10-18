"""Pruebas de layout: que nada se salga de la pantalla ni se superponga.

Usan solo los rectángulos que definen las vistas (sin dibujar nada).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pygame

from tree.arbol import Arbol
from ui.tema import ANCHO, ALTO
from mapa.mundo import Mundo
from ui import accesibilidad_view, ayuda_view, eventos_view, mapa_view, hub_view, menu_view, resumen_view, nodo_detalle_view as detalle, tragamonedas_view as slot
from ui.tree_view import POSICIONES, Y_LEYENDA

PANTALLA = pygame.Rect(0, 0, ANCHO, ALTO)
Y_INICIO_CONTENIDO = 136  # debajo del encabezado (tarjetas + título + ronda)


def hay_solapes(rects):
    return [(i, j) for i in range(len(rects)) for j in range(i + 1, len(rects))
            if rects[i].colliderect(rects[j])]


class TestLayoutArbol(unittest.TestCase):
    def test_todos_los_nodos_tienen_posicion(self):
        ids = {n.id for n in Arbol.construir_arbol_inicial().recorrido_bfs()}
        self.assertEqual(ids, set(POSICIONES))

    def test_los_nodos_no_se_superponen(self):
        rects = [pygame.Rect(*p) for p in POSICIONES.values()]
        self.assertEqual(hay_solapes(rects), [])

    def test_los_nodos_caben_en_pantalla_debajo_del_encabezado_y_de_la_leyenda(self):
        for id_nodo, pos in POSICIONES.items():
            rect = pygame.Rect(*pos)
            self.assertTrue(PANTALLA.contains(rect), id_nodo)
            self.assertGreaterEqual(rect.top, Y_INICIO_CONTENIDO, id_nodo)
            self.assertLess(rect.bottom, Y_LEYENDA, id_nodo)


class TestLayoutHub(unittest.TestCase):
    def test_los_botones_caben_en_pantalla(self):
        for nombre in ("RECT_BOTON_ARBOL", "RECT_BOTON_MAPA", "RECT_BOTON_VOLVER", "RECT_AREA_MINIJUEGO"):
            self.assertTrue(PANTALLA.contains(getattr(hub_view, nombre)), nombre)
        for nombre in ("RECT_BOTON_START", "RECT_BOTON_AYUDA_MENU", "RECT_BOTON_PAUSA", "RECT_BOTON_AYUDA_JUEGO",
                       "RECT_BOTON_ACCESIBILIDAD_MENU", "RECT_BOTON_ACCESIBILIDAD_PAUSA",
                       "RECT_BOTON_REANUDAR", "RECT_BOTON_AYUDA_PAUSA", "RECT_BOTON_SALIR_PAUSA",
                       "RECT_BOTON_SALIR", "RECT_BOTON_NUEVA"):
            self.assertTrue(PANTALLA.contains(getattr(menu_view, nombre)), nombre)

    def test_el_hub_no_se_superpone_con_el_encabezado_ni_entre_si(self):
        rects = [hub_view.RECT_AREA_MINIJUEGO, hub_view.RECT_BOTON_ARBOL, hub_view.RECT_BOTON_MAPA]
        self.assertEqual(hay_solapes(rects), [])
        for rect in rects:
            self.assertGreaterEqual(rect.top, Y_INICIO_CONTENIDO)

    def test_las_tarjetas_de_recursos_caben_en_pantalla(self):
        ultima = hub_view.MARGEN + len(hub_view.TARJETAS) * (hub_view.ANCHO_TARJETA + hub_view.ESPACIO_TARJETAS)
        self.assertLess(ultima, ANCHO)

    def test_el_boton_de_pausa_no_pisa_las_tarjetas_de_recursos(self):
        ultima = hub_view.MARGEN + len(hub_view.TARJETAS) * (hub_view.ANCHO_TARJETA + hub_view.ESPACIO_TARJETAS)
        self.assertGreater(menu_view.RECT_BOTON_PAUSA.left, ultima)

    def test_el_boton_volver_no_pisa_el_arbol(self):
        volver = hub_view.RECT_BOTON_VOLVER
        for pos in POSICIONES.values():
            self.assertFalse(volver.colliderect(pygame.Rect(*pos)))

    def test_los_botones_de_pausa_y_fin_no_se_superponen(self):
        pausa = [menu_view.RECT_BOTON_REANUDAR, menu_view.RECT_BOTON_AYUDA_PAUSA,
                 menu_view.RECT_BOTON_ACCESIBILIDAD_PAUSA, menu_view.RECT_BOTON_SALIR_PAUSA]
        self.assertEqual(hay_solapes(pausa), [])
        self.assertEqual(hay_solapes([menu_view.RECT_BOTON_NUEVA, menu_view.RECT_BOTON_SALIR]), [])

    def test_los_botones_de_la_pausa_caben_dentro_de_su_panel(self):
        panel = pygame.Rect(ANCHO // 2 - 200, 150, 400, 420)
        for rect in (menu_view.RECT_BOTON_REANUDAR, menu_view.RECT_BOTON_AYUDA_PAUSA,
                     menu_view.RECT_BOTON_ACCESIBILIDAD_PAUSA, menu_view.RECT_BOTON_SALIR_PAUSA):
            self.assertTrue(panel.contains(rect))

    def test_los_botones_del_menu_no_se_superponen(self):
        self.assertEqual(hay_solapes([menu_view.RECT_BOTON_START, menu_view.RECT_BOTON_AYUDA_MENU,
                                      menu_view.RECT_BOTON_ACCESIBILIDAD_MENU]), [])

    def test_el_boton_de_ayuda_no_pisa_la_pausa_ni_las_tarjetas(self):
        ayuda = menu_view.RECT_BOTON_AYUDA_JUEGO
        self.assertFalse(ayuda.colliderect(menu_view.RECT_BOTON_PAUSA))
        ultima = hub_view.MARGEN + len(hub_view.TARJETAS) * (hub_view.ANCHO_TARJETA + hub_view.ESPACIO_TARJETAS)
        self.assertGreater(ayuda.left, ultima)


class TestLayoutTragamonedas(unittest.TestCase):
    def test_carretes_y_boton_caben_dentro_del_area_sin_superponerse(self):
        area = hub_view.RECT_AREA_MINIJUEGO
        elementos = list(slot.RECTS_REEL) + [slot.RECT_BOTON_ACCION]
        for rect in elementos:
            self.assertTrue(area.contains(rect))
        self.assertEqual(hay_solapes(elementos), [])

    def test_los_carretes_estan_centrados_en_el_area(self):
        area = hub_view.RECT_AREA_MINIJUEGO
        izquierda = slot.RECTS_REEL[0].left - area.left
        derecha = area.right - slot.RECTS_REEL[-1].right
        self.assertLessEqual(abs(izquierda - derecha), 1)


class TestLayoutMapa(unittest.TestCase):
    def setUp(self):
        self.mundo = Mundo.construir_mundo_inicial()
        self.centros = mapa_view.POSICIONES_REGION

    def test_cada_region_tiene_posicion_y_no_sobran(self):
        self.assertEqual(set(self.centros), set(self.mundo.regiones))

    def test_las_regiones_caben_dentro_del_mapa_con_su_nombre(self):
        r = mapa_view.RADIO_REGION
        for id_region, (x, y) in self.centros.items():
            circulo = pygame.Rect(x - r, y - r, 2 * r, 2 * r)
            self.assertTrue(mapa_view.RECT_MAPA.contains(circulo), id_region)
            self.assertLess(y + r + 34, mapa_view.Y_LEYENDA, id_region)  # el nombre no pisa la leyenda

    def test_las_regiones_no_se_superponen_y_dejan_espacio_para_el_costo(self):
        ids = list(self.centros)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                (xa, ya), (xb, yb) = self.centros[ids[i]], self.centros[ids[j]]
                self.assertGreaterEqual(((xa - xb) ** 2 + (ya - yb) ** 2) ** 0.5, 100, (ids[i], ids[j]))

    def test_ninguna_ruta_atraviesa_otra_region(self):
        r = mapa_view.RADIO_REGION
        for a, b, _ in self.mundo.grafo.aristas():
            (xa, ya), (xb, yb) = self.centros[a], self.centros[b]
            largo = ((xb - xa) ** 2 + (yb - ya) ** 2) ** 0.5
            for otra, (x, y) in self.centros.items():
                if otra in (a, b):
                    continue
                # distancia de la región `otra` al segmento a-b
                t = max(0, min(1, ((x - xa) * (xb - xa) + (y - ya) * (yb - ya)) / largo ** 2))
                px, py = xa + t * (xb - xa), ya + t * (yb - ya)
                distancia = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
                self.assertGreater(distancia, r + 8, (a, b, otra))

    def test_mapa_y_panel_caben_en_pantalla_sin_superponerse_ni_pisar_el_encabezado(self):
        for rect in (mapa_view.RECT_MAPA, mapa_view.RECT_PANEL_REGION):
            self.assertTrue(PANTALLA.contains(rect))
            self.assertGreaterEqual(rect.top, Y_INICIO_CONTENIDO)
        self.assertFalse(mapa_view.RECT_MAPA.colliderect(mapa_view.RECT_PANEL_REGION))

    def test_el_boton_expandir_esta_dentro_del_panel(self):
        self.assertTrue(mapa_view.RECT_PANEL_REGION.contains(mapa_view.RECT_BOTON_EXPANDIR))

    def test_el_boton_volver_no_pisa_el_mapa(self):
        self.assertFalse(hub_view.RECT_BOTON_VOLVER.colliderect(mapa_view.RECT_MAPA))


class TestLayoutAyuda(unittest.TestCase):
    def test_pestanas_panel_y_botones_caben_en_pantalla(self):
        for rect in (*ayuda_view.RECTS_TAB, ayuda_view.RECT_PANEL_AYUDA):
            self.assertTrue(PANTALLA.contains(rect))
            self.assertGreaterEqual(rect.top, Y_INICIO_CONTENIDO)
        self.assertTrue(ayuda_view.RECT_PANEL_AYUDA.contains(ayuda_view.RECT_BOTON_ANTERIOR))
        self.assertTrue(ayuda_view.RECT_PANEL_AYUDA.contains(ayuda_view.RECT_BOTON_SIGUIENTE))
        self.assertTrue(ayuda_view.RECT_PANEL_AYUDA.contains(ayuda_view.RECT_BOTON_ABRIR_ACCESIBILIDAD))

    def test_las_pestanas_no_se_superponen_entre_si_ni_con_el_panel(self):
        self.assertEqual(hay_solapes(list(ayuda_view.RECTS_TAB)), [])
        for tab in ayuda_view.RECTS_TAB:
            self.assertFalse(tab.colliderect(ayuda_view.RECT_PANEL_AYUDA))

    def test_los_botones_del_panel_no_se_superponen(self):
        rects = [ayuda_view.RECT_BOTON_ANTERIOR, ayuda_view.RECT_BOTON_SIGUIENTE, ayuda_view.RECT_BOTON_ABRIR_ACCESIBILIDAD]
        self.assertEqual(hay_solapes(rects), [])

    def test_el_boton_volver_no_pisa_las_pestanas(self):
        for tab in ayuda_view.RECTS_TAB:
            self.assertFalse(hub_view.RECT_BOTON_VOLVER.colliderect(tab))


class TestLayoutAccesibilidad(unittest.TestCase):
    def test_hay_un_rectangulo_por_opcion_y_caben_en_pantalla(self):
        from ui.paletas import OPCIONES
        self.assertEqual(len(accesibilidad_view.RECTS_OPCION), len(OPCIONES))
        for rect in accesibilidad_view.RECTS_OPCION:
            self.assertTrue(PANTALLA.contains(rect))
            self.assertGreaterEqual(rect.top, Y_INICIO_CONTENIDO)

    def test_las_opciones_no_se_superponen_ni_pisan_la_nota_ni_el_boton_volver(self):
        self.assertEqual(hay_solapes(list(accesibilidad_view.RECTS_OPCION)), [])
        ultima = accesibilidad_view.RECTS_OPCION[-1]
        self.assertLess(ultima.bottom, accesibilidad_view.Y_NOTA)
        for rect in accesibilidad_view.RECTS_OPCION:
            self.assertFalse(rect.colliderect(hub_view.RECT_BOTON_VOLVER))

    def test_la_nota_final_cabe_en_la_pantalla(self):
        self.assertLess(accesibilidad_view.Y_NOTA + 30, ALTO)


class TestLayoutAviso(unittest.TestCase):
    def test_el_aviso_cabe_en_pantalla_y_esta_centrado(self):
        rect = eventos_view.RECT_AVISO
        self.assertTrue(PANTALLA.contains(rect))
        self.assertLessEqual(abs(rect.centerx - ANCHO // 2), 1)

    def test_el_aviso_no_tapa_el_encabezado(self):
        self.assertGreaterEqual(eventos_view.RECT_AVISO.top, Y_INICIO_CONTENIDO - 4)

    def test_el_boton_de_pausa_queda_fuera_del_aviso(self):
        self.assertFalse(eventos_view.RECT_AVISO.colliderect(menu_view.RECT_BOTON_PAUSA))


class TestLayoutPanelDetalle(unittest.TestCase):
    def test_botones_y_controles_estan_dentro_del_panel(self):
        elementos = [detalle.RECT_BOTON_COMPRAR, detalle.RECT_BOTON_CANCELAR, detalle.RECT_BOTON_CERRAR,
                     detalle.RECT_INTERRUPTOR, detalle.RECT_DIAL_MENOS, detalle.RECT_DIAL_MAS,
                     detalle.RECT_DIAL_BARRA, *detalle.RECT_VARIANTES]
        for rect in elementos:
            self.assertTrue(detalle.RECT_PANEL.contains(rect), rect)
        self.assertTrue(PANTALLA.contains(detalle.RECT_PANEL))

    def test_los_controles_de_cada_tipo_no_se_superponen_entre_si(self):
        self.assertEqual(hay_solapes([detalle.RECT_DIAL_MENOS, detalle.RECT_DIAL_BARRA, detalle.RECT_DIAL_MAS]), [])
        self.assertEqual(hay_solapes(list(detalle.RECT_VARIANTES)), [])

    def test_los_controles_no_pisan_los_botones_de_abajo(self):
        controles = [detalle.RECT_INTERRUPTOR, detalle.RECT_DIAL_MENOS, detalle.RECT_DIAL_MAS,
                     detalle.RECT_DIAL_BARRA.inflate(0, 24), *detalle.RECT_VARIANTES]
        botones = [detalle.RECT_BOTON_COMPRAR, detalle.RECT_BOTON_CANCELAR, detalle.RECT_BOTON_CERRAR]
        for control in controles:
            for boton in botones:
                self.assertFalse(control.colliderect(boton))

    def test_comprar_y_cancelar_no_se_superponen(self):
        self.assertFalse(detalle.RECT_BOTON_COMPRAR.colliderect(detalle.RECT_BOTON_CANCELAR))


class TestLayoutResumen(unittest.TestCase):
    def test_panel_subpaneles_y_botones_caben_en_pantalla_sin_solapes(self):
        panel = resumen_view.RECT_PANEL_RESUMEN
        self.assertTrue(PANTALLA.contains(panel))
        for sub in (resumen_view.RECT_GRAFICO, resumen_view.RECT_ESTADISTICAS,
                    resumen_view.RECT_BOTON_NUEVA, resumen_view.RECT_BOTON_SALIR):
            self.assertTrue(panel.contains(sub), sub)
        self.assertEqual(
            hay_solapes([
                resumen_view.RECT_GRAFICO,
                resumen_view.RECT_ESTADISTICAS,
                resumen_view.RECT_BOTON_NUEVA,
                resumen_view.RECT_BOTON_SALIR,
            ]),
            [],
        )


if __name__ == "__main__":
    unittest.main()
