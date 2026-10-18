"""Pruebas del formato de números y efectos (sin Pygame)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ui.formato import formato_numero, formatear_efecto, formatear_efectos


class TestFormato(unittest.TestCase):
    def test_numero_con_separador_de_miles(self):
        self.assertEqual(formato_numero(10000), "10.000")
        self.assertEqual(formato_numero(500), "500")
        self.assertEqual(formato_numero(1234567), "1.234.567")
        self.assertEqual(formato_numero(66.4), "66")
        self.assertEqual(formato_numero(-2500), "-2.500")

    def test_crecimiento_se_muestra_como_porcentaje(self):
        self.assertEqual(formatear_efecto("crecimiento", 0.05), "+5% crecimiento")
        self.assertEqual(formatear_efecto("crecimiento", -0.01), "-1% crecimiento")

    def test_engagement_fraccion_se_muestra_en_puntos(self):
        self.assertEqual(formatear_efecto("engagement", 0.08), "+8 engagement")

    def test_dinero_lleva_signo_y_prefijo(self):
        self.assertEqual(formatear_efecto("dinero", 3000), "+$3.000 dinero")
        self.assertEqual(formatear_efecto("dinero", -300), "-$300 dinero")

    def test_los_valores_fraccionarios_no_se_redondean_a_cero(self):
        self.assertEqual(formatear_efecto("reputacion", 0.5), "+0,5 reputación")
        self.assertEqual(formatear_efecto("bienestar", -1.5), "-1,5 bienestar")

    def test_otros_recursos_y_varios_efectos(self):
        self.assertEqual(formatear_efecto("reputacion", 5), "+5 reputación")
        self.assertEqual(formatear_efectos({"bienestar": -4, "usuarios": 300}), "-4 bienestar, +300 usuarios")


if __name__ == "__main__":
    unittest.main()
