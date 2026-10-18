"""Pruebas del sistema de rondas (sin Pygame de por medio)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mapa.mundo import Mundo
from tree.arbol import Arbol
from tree.recursos import Recursos
from tree.ronda import (
    Rondas, avanzar_ronda, tasa_fuga, QUIEBRA, EXODO, VICTORIA, UMBRAL_FUGA, FUGA_MAXIMA,
)


class TestAvanzarRonda(unittest.TestCase):
    def setUp(self):
        self.arbol = Arbol.construir_arbol_inicial()
        self.recursos = Recursos(dinero=100000)
        self.arbol.desbloquear_gratuitos(self.recursos)
        self.feed = self.arbol.raiz.hijos[0]

    def test_sin_nodos_activos_solo_crece_el_crecimiento_pasivo(self):
        self.recursos.crecimiento = 0.10
        self.assertIsNone(avanzar_ronda(self.arbol, self.recursos))
        self.assertEqual(self.recursos.usuarios, 550)
        self.assertEqual(self.recursos.bienestar, 70)

    def test_interruptor_encendido_aplica_sus_efectos_cada_ronda(self):
        scroll = self.feed.hijos[1]  # crecimiento +5%, engagement +0.08, bienestar -4
        scroll.desbloquear(self.recursos)
        scroll.alternar_interruptor()

        avanzar_ronda(self.arbol, self.recursos)
        self.assertEqual(self.recursos.usuarios, 525)       # 500 * 5%
        self.assertAlmostEqual(self.recursos.engagement, 38)  # 30 + 0.08*100
        self.assertAlmostEqual(self.recursos.bienestar, 66)

        avanzar_ronda(self.arbol, self.recursos)
        self.assertAlmostEqual(self.recursos.bienestar, 62)

    def test_interruptor_apagado_no_cambia_nada(self):
        scroll = self.feed.hijos[1]
        scroll.desbloquear(self.recursos)
        avanzar_ronda(self.arbol, self.recursos)
        self.assertEqual(self.recursos.usuarios, 500)
        self.assertEqual(self.recursos.bienestar, 70)

    def test_dial_escala_los_efectos_por_ronda(self):
        algoritmo = self.feed.hijos[2]  # usuarios +300, engagement +0.1, bienestar -6
        algoritmo.desbloquear(self.recursos)
        algoritmo.ajustar_dial(50)

        avanzar_ronda(self.arbol, self.recursos)
        self.assertEqual(self.recursos.usuarios, 650)
        self.assertAlmostEqual(self.recursos.engagement, 35)
        self.assertAlmostEqual(self.recursos.bienestar, 67)

    def test_bifurcacion_con_costo_recurrente_baja_el_dinero(self):
        seguridad = self.arbol.raiz.hijos[2]
        avanzada = seguridad.hijos[1]  # "humana": dinero -300 por ronda
        avanzada.desbloquear(self.recursos)
        avanzada.elegir_variante("humana")
        antes = self.recursos.dinero
        avanzar_ronda(self.arbol, self.recursos)
        self.assertEqual(self.recursos.dinero, antes - 300)

    def test_quiebra_cuando_el_dinero_queda_negativo(self):
        seguridad = self.arbol.raiz.hijos[2]
        avanzada = seguridad.hijos[1]
        avanzada.desbloquear(self.recursos)
        avanzada.elegir_variante("humana")
        self.recursos.dinero = 100
        self.assertEqual(avanzar_ronda(self.arbol, self.recursos), QUIEBRA)

    def test_exodo_cuando_no_quedan_usuarios(self):
        self.recursos.usuarios = 0
        self.assertEqual(avanzar_ronda(self.arbol, self.recursos), EXODO)

    def test_las_regiones_conquistadas_aportan_su_ingreso_cada_ronda(self):
        mundo = Mundo.construir_mundo_inicial()
        dinero, usuarios = self.recursos.dinero, self.recursos.usuarios
        avanzar_ronda(self.arbol, self.recursos, mundo)
        self.assertEqual(self.recursos.dinero, dinero + 120)
        self.assertEqual(self.recursos.usuarios, usuarios + 25)

    def test_sin_mundo_no_hay_ingreso_de_regiones(self):
        dinero = self.recursos.dinero
        avanzar_ronda(self.arbol, self.recursos)
        self.assertEqual(self.recursos.dinero, dinero)

    def test_el_ingreso_de_las_regiones_se_suma_al_de_los_nodos(self):
        mundo = Mundo.construir_mundo_inicial()
        algoritmo = self.feed.hijos[2]  # usuarios +300 al 100%
        algoritmo.desbloquear(self.recursos)
        algoritmo.ajustar_dial(100)
        usuarios = self.recursos.usuarios
        avanzar_ronda(self.arbol, self.recursos, mundo)
        self.assertEqual(self.recursos.usuarios, usuarios + 300 + 25)


class TestTopeDeUsuarios(unittest.TestCase):
    def setUp(self):
        self.arbol = Arbol.construir_arbol_inicial()
        self.recursos = Recursos(dinero=100000, usuarios=1400)
        self.arbol.desbloquear_gratuitos(self.recursos)
        self.mundo = Mundo.construir_mundo_inicial()

    def test_la_ronda_fija_el_tope_segun_las_regiones_conquistadas(self):
        avanzar_ronda(self.arbol, self.recursos, self.mundo)
        self.assertEqual(self.recursos.limite_usuarios, self.mundo.capacidad_total())

    def test_el_crecimiento_se_detiene_en_el_tope(self):
        self.recursos.crecimiento = 0.50
        for _ in range(10):
            avanzar_ronda(self.arbol, self.recursos, self.mundo)
        self.assertEqual(self.recursos.usuarios, self.mundo.capacidad_total())

    def test_conquistar_una_region_levanta_el_tope_y_permite_seguir_creciendo(self):
        self.recursos.crecimiento = 0.50
        for _ in range(10):
            avanzar_ronda(self.arbol, self.recursos, self.mundo)
        lleno = self.recursos.usuarios
        self.mundo.regiones["centroamerica"].conquistada = True
        avanzar_ronda(self.arbol, self.recursos, self.mundo)
        self.assertGreater(self.recursos.usuarios, lleno)

    def test_sin_mundo_no_hay_tope(self):
        self.recursos.crecimiento = 0.50
        for _ in range(5):
            avanzar_ronda(self.arbol, self.recursos)
        self.assertGreater(self.recursos.usuarios, 5000)


class TestFugaPorBajoBienestar(unittest.TestCase):
    def setUp(self):
        self.arbol = Arbol.construir_arbol_inicial()
        self.recursos = Recursos(dinero=100000, usuarios=1000)
        self.arbol.desbloquear_gratuitos(self.recursos)

    def test_no_hay_fuga_con_el_bienestar_en_el_umbral_o_por_encima(self):
        self.assertEqual(tasa_fuga(UMBRAL_FUGA), 0.0)
        self.assertEqual(tasa_fuga(100), 0.0)

    def test_la_fuga_crece_al_bajar_el_bienestar_hasta_el_maximo(self):
        self.assertEqual(tasa_fuga(0), FUGA_MAXIMA)
        self.assertAlmostEqual(tasa_fuga(UMBRAL_FUGA / 2), FUGA_MAXIMA / 2)
        self.assertGreater(tasa_fuga(10), tasa_fuga(30))

    def test_con_bienestar_bajo_se_van_usuarios_cada_ronda(self):
        self.recursos.bienestar = 0
        avanzar_ronda(self.arbol, self.recursos)
        self.assertEqual(self.recursos.usuarios, round(1000 * (1 - FUGA_MAXIMA)))

    def test_con_bienestar_suficiente_no_se_va_nadie(self):
        self.recursos.bienestar = UMBRAL_FUGA
        avanzar_ronda(self.arbol, self.recursos)
        self.assertEqual(self.recursos.usuarios, 1000)

    def test_el_crecimiento_compensa_la_fuga(self):
        self.recursos.bienestar = 0
        self.recursos.crecimiento = 0.20
        avanzar_ronda(self.arbol, self.recursos)
        self.assertEqual(self.recursos.usuarios, round(1000 * (1 + 0.20 - FUGA_MAXIMA)))

    def test_la_fuga_nunca_deja_usuarios_negativos(self):
        self.recursos.usuarios = 3
        self.recursos.bienestar = 0
        for _ in range(100):
            avanzar_ronda(self.arbol, self.recursos)
        self.assertGreaterEqual(self.recursos.usuarios, 0)


class TestRondas(unittest.TestCase):
    def setUp(self):
        self.arbol = Arbol.construir_arbol_inicial()
        self.recursos = Recursos()
        self.arbol.desbloquear_gratuitos(self.recursos)
        self.rondas = Rondas(duracion=1.0)

    def test_no_avanza_hasta_completar_la_duracion(self):
        self.assertFalse(self.rondas.actualizar(0.5, self.arbol, self.recursos))
        self.assertEqual(self.rondas.numero, 1)
        self.assertAlmostEqual(self.rondas.segundos_restantes(), 0.5)

    def test_al_completar_la_duracion_juega_una_ronda(self):
        self.rondas.actualizar(0.5, self.arbol, self.recursos)
        self.assertTrue(self.rondas.actualizar(0.6, self.arbol, self.recursos))
        self.assertEqual(self.rondas.numero, 2)
        self.assertAlmostEqual(self.rondas.acumulado, 0.1)

    def test_rondas_pasa_el_mundo_a_la_ronda(self):
        mundo = Mundo.construir_mundo_inicial()
        dinero = self.recursos.dinero
        self.rondas.actualizar(1.0, self.arbol, self.recursos, mundo)
        self.assertEqual(self.recursos.dinero, dinero + 120)

    def test_finalizar_con_victoria_termina_la_partida(self):
        self.rondas.finalizar(VICTORIA)
        self.assertTrue(self.rondas.terminada)
        self.assertEqual(self.rondas.resultado, VICTORIA)
        self.assertFalse(self.rondas.actualizar(5.0, self.arbol, self.recursos))

    def test_finalizar_no_pisa_un_resultado_anterior(self):
        self.recursos.dinero = -10
        self.rondas.actualizar(1.0, self.arbol, self.recursos)
        self.rondas.finalizar(VICTORIA)
        self.assertEqual(self.rondas.resultado, QUIEBRA)

    def test_tras_la_derrota_la_partida_queda_terminada_y_no_avanza_mas(self):
        self.recursos.dinero = -10
        self.rondas.actualizar(1.0, self.arbol, self.recursos)
        self.assertTrue(self.rondas.terminada)
        self.assertEqual(self.rondas.resultado, QUIEBRA)
        numero = self.rondas.numero
        self.assertFalse(self.rondas.actualizar(5.0, self.arbol, self.recursos))
        self.assertEqual(self.rondas.numero, numero)


if __name__ == "__main__":
    unittest.main()
