"""Pruebas mínimas para validar la lógica del árbol antes de mezclarla con Pygame."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tree.arbol import Arbol
from tree.recursos import Recursos


class TestArbol(unittest.TestCase):
    def setUp(self):
        self.arbol = Arbol.construir_arbol_inicial()
        self.recursos = Recursos(dinero=10000)

    def test_raiz_se_desbloquea_sin_costo(self):
        self.assertTrue(self.arbol.raiz.desbloquear(self.recursos))

    def test_no_se_puede_desbloquear_hijo_sin_desbloquear_padre(self):
        feed = self.arbol.raiz.hijos[0]
        basico = feed.hijos[0]
        self.assertFalse(basico.puede_desbloquearse(self.recursos))

    def test_desbloqueo_en_orden_correcto(self):
        feed = self.arbol.raiz.hijos[0]
        basico = feed.hijos[0]
        self.arbol.raiz.desbloquear(self.recursos)
        feed.desbloquear(self.recursos)
        self.assertTrue(basico.desbloquear(self.recursos))
        self.assertTrue(basico.desbloqueado)

    def test_dial_escala_el_efecto_segun_su_valor(self):
        feed = self.arbol.raiz.hijos[0]
        algoritmo = feed.hijos[2]  # Algoritmo es el tercer hijo de Feed
        self.arbol.raiz.desbloquear(self.recursos)
        feed.desbloquear(self.recursos)
        algoritmo.desbloquear(self.recursos)

        algoritmo.ajustar_dial(50)
        efecto = algoritmo.efecto_por_ronda()
        self.assertAlmostEqual(efecto["bienestar"], -3)  # -6 * 0.5

    def test_interruptor_apagado_no_aporta_efecto(self):
        feed = self.arbol.raiz.hijos[0]
        scroll = feed.hijos[1]  # Scroll infinito es el segundo hijo de Feed
        self.arbol.raiz.desbloquear(self.recursos)
        feed.desbloquear(self.recursos)
        scroll.desbloquear(self.recursos)

        self.assertEqual(scroll.efecto_por_ronda(), {})
        scroll.alternar_interruptor()
        self.assertNotEqual(scroll.efecto_por_ronda(), {})

    def test_no_se_puede_desbloquear_sin_dinero_suficiente(self):
        feed = self.arbol.raiz.hijos[0]
        algoritmo = feed.hijos[2]  # cuesta 5000
        self.arbol.raiz.desbloquear(self.recursos)
        feed.desbloquear(self.recursos)
        pobres = Recursos(dinero=100)
        self.assertFalse(algoritmo.puede_desbloquearse(pobres))
        self.assertFalse(algoritmo.desbloquear(pobres))
        self.assertFalse(algoritmo.desbloqueado)
        self.assertEqual(pobres.dinero, 100)

    def test_desbloquear_cobra_el_costo(self):
        feed = self.arbol.raiz.hijos[0]
        basico = feed.hijos[0]  # cuesta 2000
        self.arbol.raiz.desbloquear(self.recursos)
        feed.desbloquear(self.recursos)
        basico.desbloquear(self.recursos)
        self.assertEqual(self.recursos.dinero, 10000 - 2000)

    def test_nodo_fijo_aplica_su_efecto_una_sola_vez(self):
        feed = self.arbol.raiz.hijos[0]
        basico = feed.hijos[0]  # crecimiento +0.02
        self.arbol.raiz.desbloquear(self.recursos)
        feed.desbloquear(self.recursos)
        basico.desbloquear(self.recursos)
        self.assertAlmostEqual(self.recursos.crecimiento, 0.02)
        self.assertEqual(basico.efecto_por_ronda(), {})  # no se repite cada ronda

    def test_desbloquear_gratuitos_abre_raiz_y_categorias_pero_no_lo_que_cuesta(self):
        self.arbol.desbloquear_gratuitos(self.recursos)
        nodos = {n.id: n for n in self.arbol.recorrido_bfs()}
        for id_nodo in ("red_social", "feed", "comunidad", "seguridad"):
            self.assertTrue(nodos[id_nodo].desbloqueado, id_nodo)
        self.assertFalse(nodos["feed_basico"].desbloqueado)
        self.assertEqual(self.recursos.dinero, 10000)

    def test_dial_se_mantiene_entre_0_y_100(self):
        feed = self.arbol.raiz.hijos[0]
        algoritmo = feed.hijos[2]
        self.arbol.desbloquear_gratuitos(self.recursos)
        algoritmo.desbloquear(self.recursos)
        algoritmo.ajustar_dial(250)
        self.assertEqual(algoritmo.valor, 100)
        algoritmo.ajustar_dial(-30)
        self.assertEqual(algoritmo.valor, 0)

    def test_controles_se_ignoran_si_el_nodo_no_esta_desbloqueado(self):
        feed = self.arbol.raiz.hijos[0]
        scroll, algoritmo = feed.hijos[1], feed.hijos[2]
        scroll.alternar_interruptor()
        algoritmo.ajustar_dial(80)
        self.assertFalse(scroll.activo)
        self.assertEqual(algoritmo.valor, 0)

    def test_bifurcacion_solo_aporta_efecto_despues_de_elegir_variante(self):
        comunidad = self.arbol.raiz.hijos[1]
        mensajes = comunidad.hijos[1]
        self.arbol.desbloquear_gratuitos(self.recursos)
        mensajes.desbloquear(self.recursos)

        self.assertEqual(mensajes.efecto_por_ronda(), {})
        mensajes.elegir_variante("cifrado")
        self.assertEqual(mensajes.efecto_por_ronda()["reputacion"], 5)
        mensajes.elegir_variante("abierta")
        self.assertEqual(mensajes.efecto_por_ronda()["crecimiento"], 0.03)

    def test_bifurcacion_ignora_variantes_que_no_existen(self):
        comunidad = self.arbol.raiz.hijos[1]
        mensajes = comunidad.hijos[1]
        self.arbol.desbloquear_gratuitos(self.recursos)
        mensajes.desbloquear(self.recursos)
        mensajes.elegir_variante("cifrado")
        mensajes.elegir_variante("inexistente")
        self.assertEqual(mensajes.variante_actual, "cifrado")

    def test_efectos_totales_suman_interruptores_diales_y_bifurcaciones(self):
        recursos = Recursos(dinero=100000)
        feed, comunidad = self.arbol.raiz.hijos[0], self.arbol.raiz.hijos[1]
        scroll, algoritmo = feed.hijos[1], feed.hijos[2]
        mensajes = comunidad.hijos[1]
        self.arbol.desbloquear_gratuitos(recursos)
        for nodo in (scroll, algoritmo, mensajes):
            nodo.desbloquear(recursos)

        scroll.alternar_interruptor()       # bienestar -4
        algoritmo.ajustar_dial(50)          # bienestar -3
        mensajes.elegir_variante("abierta")  # bienestar -2

        totales = self.arbol.efectos_totales_de_la_ronda()
        self.assertAlmostEqual(totales["bienestar"], -9)

    def test_nodos_disponibles_respeta_padre_y_dinero(self):
        self.arbol.desbloquear_gratuitos(self.recursos)
        ids = {n.id for n in self.arbol.nodos_disponibles(self.recursos)}
        self.assertIn("feed_basico", ids)
        self.assertNotIn("red_social", ids)  # ya desbloqueado

    def test_tipo_de_control_invalido_lanza_error(self):
        from tree.nodo import Nodo
        with self.assertRaises(ValueError):
            Nodo("x", "X", "inventado", costo=0)


if __name__ == "__main__":
    unittest.main()
