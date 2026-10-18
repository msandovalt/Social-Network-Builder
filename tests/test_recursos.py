"""Pruebas de los recursos del jugador: límites, enteros y condiciones de derrota."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tree.recursos import Recursos, efectos_en_puntos


class TestRecursos(unittest.TestCase):
    def test_las_escalas_no_pasan_de_100_ni_bajan_de_0(self):
        r = Recursos(bienestar=90, reputacion=10, engagement=50)
        r.aplicar_efectos({"bienestar": 50, "reputacion": -50, "engagement": 500})
        self.assertEqual(r.bienestar, 100)
        self.assertEqual(r.reputacion, 0)
        self.assertEqual(r.engagement, 100)

    def test_dinero_y_usuarios_quedan_enteros(self):
        r = Recursos(dinero=1000, usuarios=500)
        r.aplicar_efectos({"dinero": 150.0, "usuarios": 12.6})
        self.assertIsInstance(r.dinero, int)
        self.assertIsInstance(r.usuarios, int)
        self.assertEqual(r.usuarios, 513)

    def test_usuarios_nunca_son_negativos(self):
        r = Recursos(usuarios=10)
        r.aplicar_efectos({"usuarios": -500})
        self.assertEqual(r.usuarios, 0)

    def test_claves_desconocidas_se_ignoran(self):
        r = Recursos()
        r.aplicar_efectos({"inventado": 99})
        self.assertFalse(hasattr(r, "inventado"))

    def test_quiebra_es_deuda_no_quedarse_en_cero(self):
        self.assertFalse(Recursos(dinero=0).esta_en_quiebra())
        self.assertFalse(Recursos(dinero=500).esta_en_quiebra())
        self.assertTrue(Recursos(dinero=-1).esta_en_quiebra())

    def test_exodo_cuando_no_quedan_usuarios(self):
        self.assertTrue(Recursos(usuarios=0).sufre_exodo())
        self.assertFalse(Recursos(usuarios=1).sufre_exodo())

    def test_los_usuarios_no_superan_el_limite(self):
        r = Recursos(usuarios=500)
        r.actualizar_limite_usuarios(1500)
        r.aplicar_efectos({"usuarios": 5000})
        self.assertEqual(r.usuarios, 1500)

    def test_sin_limite_los_usuarios_no_tienen_tope(self):
        r = Recursos(usuarios=500)
        r.aplicar_efectos({"usuarios": 5000000})
        self.assertEqual(r.usuarios, 5000500)

    def test_bajar_el_limite_recorta_los_usuarios_de_inmediato(self):
        r = Recursos(usuarios=3000)
        r.actualizar_limite_usuarios(2000)
        self.assertEqual(r.usuarios, 2000)

    def test_el_limite_no_sube_los_usuarios_por_si_solo(self):
        r = Recursos(usuarios=500)
        r.actualizar_limite_usuarios(9000)
        self.assertEqual(r.usuarios, 500)

    def test_efectos_en_puntos_convierte_solo_el_engagement(self):
        original = {"engagement": 0.08, "dinero": 100, "bienestar": -4}
        convertidos = efectos_en_puntos(original)
        self.assertAlmostEqual(convertidos["engagement"], 8)
        self.assertEqual(convertidos["dinero"], 100)
        self.assertEqual(original["engagement"], 0.08)  # no modifica el original


if __name__ == "__main__":
    unittest.main()
