"""Pruebas de las utilidades de animación y las partículas."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ui.animacion import NumeroAnimado, ease_out_cubic, ease_in_out, pulso
from ui.particulas import SistemaParticulas


class TestEasing(unittest.TestCase):
    def test_extremos_y_limites(self):
        for ease in (ease_out_cubic, ease_in_out):
            self.assertEqual(ease(0), 0)
            self.assertEqual(ease(1), 1)
            self.assertEqual(ease(-5), 0)
            self.assertEqual(ease(5), 1)

    def test_ease_out_avanza_mas_rapido_al_principio(self):
        self.assertGreater(ease_out_cubic(0.5), 0.5)

    def test_pulso_se_mantiene_entre_0_y_1(self):
        for i in range(50):
            self.assertTrue(0 <= pulso(i * 0.1) <= 1)


class TestNumeroAnimado(unittest.TestCase):
    def test_se_acerca_al_objetivo_sin_pasarse(self):
        n = NumeroAnimado(0)
        n.actualizar(0.1, 1000)
        self.assertTrue(0 < n.valor < 1000)
        self.assertEqual(n.direccion, 1)

    def test_llega_exacto_al_objetivo(self):
        n = NumeroAnimado(0)
        for _ in range(300):
            n.actualizar(0.016, 500)
        self.assertEqual(n.valor, 500)
        self.assertEqual(n.direccion, 0)

    def test_direccion_negativa_al_bajar(self):
        n = NumeroAnimado(100)
        n.actualizar(0.05, 20)
        self.assertEqual(n.direccion, -1)

    def test_con_dt_enorme_no_se_pasa_del_objetivo(self):
        n = NumeroAnimado(0)
        n.actualizar(100, 50)
        self.assertEqual(n.valor, 50)


class TestParticulas(unittest.TestCase):
    def test_emitir_crea_particulas_y_se_apagan_con_el_tiempo(self):
        sistema = SistemaParticulas()
        sistema.emitir(100, 100, (255, 0, 0), 10)
        self.assertTrue(sistema.hay_activas)
        self.assertEqual(len(sistema.particulas), 10)
        for _ in range(200):
            sistema.actualizar(0.016)
        self.assertFalse(sistema.hay_activas)


if __name__ == "__main__":
    unittest.main()
