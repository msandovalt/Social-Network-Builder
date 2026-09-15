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


if __name__ == "__main__":
    unittest.main()
