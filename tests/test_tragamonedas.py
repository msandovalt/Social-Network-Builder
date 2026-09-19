"""Pruebas mínimas de la lógica de la tragamonedas (sin Pygame de por medio)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tree.recursos import Recursos
from minijuego.tragamonedas import Tragamonedas, INACTIVO, GIRANDO, POR_RESOLVER, RESUELTO


class TestTragamonedas(unittest.TestCase):
    def setUp(self):
        self.recursos = Recursos(dinero=10000, bienestar=70)
        self.maquina = Tragamonedas()

    def test_costo_es_proporcional_al_dinero_con_piso_minimo(self):
        self.assertEqual(self.maquina.costo(Recursos(dinero=1000)), 200)  # 5% sería 50, aplica el piso
        self.assertEqual(self.maquina.costo(Recursos(dinero=100000)), 5000)

    def test_iniciar_cobra_el_costo_y_pone_los_carretes_a_girar(self):
        costo_esperado = self.maquina.costo(self.recursos)
        self.assertTrue(self.maquina.iniciar(self.recursos))
        self.assertEqual(self.recursos.dinero, 10000 - costo_esperado)
        self.assertEqual(self.maquina.estado, GIRANDO)
        self.assertTrue(all(self.maquina.girando))

    def test_no_se_puede_iniciar_sin_dinero_suficiente(self):
        recursos_pobres = Recursos(dinero=100, bienestar=70)
        self.assertFalse(self.maquina.iniciar(recursos_pobres))
        self.assertEqual(self.maquina.estado, INACTIVO)

    def test_detener_los_tres_carretes_pasa_a_por_resolver(self):
        self.maquina.iniciar(self.recursos)
        self.maquina.detener(0)
        self.maquina.detener(1)
        self.assertEqual(self.maquina.estado, GIRANDO)  # falta el tercero
        self.maquina.detener(2)
        self.assertEqual(self.maquina.estado, POR_RESOLVER)

    def test_resolver_con_simbolos_iguales_otorga_recompensa(self):
        self.maquina.iniciar(self.recursos)
        self.maquina.indices = [0, 0, 0]  # forzar los tres iguales para la prueba
        for i in range(3):
            self.maquina.detener(i)
        dinero_antes = self.recursos.dinero
        self.maquina.resolver(self.recursos)
        self.assertEqual(self.maquina.estado, RESUELTO)
        self.assertGreater(self.recursos.dinero, dinero_antes)

    def test_bienestar_bajo_produce_intervalo_mas_corto_que_bienestar_alto(self):
        self.maquina.iniciar(Recursos(dinero=10000, bienestar=100))
        intervalo_alto = self.maquina.intervalo
        self.maquina.reiniciar()
        self.maquina.iniciar(Recursos(dinero=10000, bienestar=0))
        intervalo_bajo = self.maquina.intervalo
        self.assertLess(intervalo_bajo, intervalo_alto)


if __name__ == "__main__":
    unittest.main()
