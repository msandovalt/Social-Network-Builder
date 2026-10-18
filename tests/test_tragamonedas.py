"""Pruebas mínimas de la lógica de la tragamonedas (sin Pygame de por medio)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tree.recursos import Recursos
from minijuego.tragamonedas import (
    Tragamonedas, INACTIVO, GIRANDO, POR_RESOLVER, RESUELTO, DURACION_ASENTADO,
)


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


class TestGiroSuave(unittest.TestCase):
    def setUp(self):
        self.recursos = Recursos(dinero=10000, bienestar=100)
        self.maquina = Tragamonedas()
        self.maquina.iniciar(self.recursos)

    def test_la_posicion_avanza_de_forma_continua(self):
        self.maquina.actualizar(0.1)
        # bienestar 100 -> 0.45 s por símbolo -> 0.1 s = 0.222 símbolos
        self.assertAlmostEqual(self.maquina.posiciones[0], 0.1 / 0.45)
        self.assertEqual(self.maquina.indices[0], 0)

    def test_el_indice_es_el_simbolo_mas_cercano_al_centro(self):
        self.maquina.actualizar(0.45 * 0.6)  # 0.6 símbolos -> el más cercano es el 1
        self.assertEqual(self.maquina.indices[0], 1)

    def test_la_posicion_da_la_vuelta_al_completar_los_simbolos(self):
        self.maquina.actualizar(0.45 * 3.5)
        self.assertTrue(0 <= self.maquina.posiciones[0] < 3)

    def test_al_detener_queda_el_simbolo_que_estaba_al_centro(self):
        self.maquina.actualizar(0.45 * 1.2)  # posición 1.2 -> símbolo 1
        self.maquina.detener(0)
        self.assertEqual(self.maquina.indices[0], 1)
        self.assertFalse(self.maquina.girando[0])

    def test_el_carrete_frena_suavemente_hasta_alinearse(self):
        self.maquina.actualizar(0.45 * 1.3)
        self.maquina.detener(0)
        self.assertFalse(self.maquina.asentada())
        self.maquina.actualizar(DURACION_ASENTADO / 2)
        self.assertNotEqual(self.maquina.posiciones[0], 1.0)  # todavía frenando
        self.maquina.actualizar(DURACION_ASENTADO)
        self.assertEqual(self.maquina.posiciones[0], 1.0)
        self.assertTrue(self.maquina.asentada())

    def test_el_ultimo_carrete_pasa_a_por_resolver_aunque_siga_frenando(self):
        for i in range(3):
            self.maquina.detener(i)
        self.assertEqual(self.maquina.estado, POR_RESOLVER)
        self.assertFalse(self.maquina.asentada())

    def test_resolver_registra_el_simbolo_ganador(self):
        for i in range(3):
            self.maquina.detener(i)  # los tres en la posición 0 -> dinero
        self.maquina.actualizar(1.0)
        self.maquina.resolver(self.recursos)
        self.assertEqual(self.maquina.resultado_tipo, "dinero")

    def test_sin_premio_el_resultado_es_none(self):
        self.maquina.actualizar(0.45)
        self.maquina.detener(0)  # símbolo 1
        self.maquina.detener(1)
        self.maquina.indices[1] = 2
        self.maquina.detener(2)
        self.maquina.indices[2] = 0
        self.maquina.resolver(self.recursos)
        self.assertIsNone(self.maquina.resultado_tipo)

    def test_el_tiempo_del_resultado_solo_corre_una_vez_resuelto(self):
        self.maquina.actualizar(0.2)
        self.assertEqual(self.maquina.tiempo_resultado, 0.0)
        for i in range(3):
            self.maquina.detener(i)
        self.maquina.actualizar(1.0)
        self.maquina.resolver(self.recursos)
        self.maquina.actualizar(0.5)
        self.assertAlmostEqual(self.maquina.tiempo_resultado, 0.5)

    def test_mas_bienestar_gira_mas_lento(self):
        lento = Tragamonedas(); lento.iniciar(Recursos(bienestar=100))
        rapido = Tragamonedas(); rapido.iniciar(Recursos(bienestar=0))
        lento.actualizar(0.3); rapido.actualizar(0.3)
        self.assertGreater(rapido.posiciones[0], lento.posiciones[0])


if __name__ == "__main__":
    unittest.main()
