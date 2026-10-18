"""Pruebas unitarias para las métricas post-mortem y la pantalla de resumen final."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pygame
from audio import GestorAudio
from juego import Juego, FIN, PRINCIPAL
from tree.arbol import Arbol
from tree.recursos import Recursos
from tree.ronda import Rondas, VICTORIA, QUIEBRA, EXODO, SATURACION
from ui import tema
from ui.resumen_view import (
    calcular_calificacion,
    dibujar_fin,
    RECT_BOTON_NUEVA,
    RECT_BOTON_SALIR,
    MOTIVOS_FIN,
)


class TestMetricasPostMortem(unittest.TestCase):
    def test_recursos_rastrean_usuarios_pico_y_dinero_generado_total(self):
        r = Recursos()
        self.assertEqual(r.usuarios_pico, 500)
        self.assertEqual(r.dinero_generado_total, 0)

        r.aplicar_efectos({"dinero": 1500, "usuarios": 300})
        self.assertEqual(r.dinero_generado_total, 1500)
        self.assertEqual(r.usuarios_pico, 800)

        # Gastos o pérdidas de usuarios no reducen el pico ni el acumulado generado
        r.aplicar_efectos({"dinero": -2500, "usuarios": -400})
        self.assertEqual(r.dinero_generado_total, 1500)
        self.assertEqual(r.usuarios_pico, 800)

    def test_rondas_registran_historial_ronda_a_ronda(self):
        r = Recursos()
        arbol = Arbol.construir_arbol_inicial()
        arbol.desbloquear_gratuitos(r)
        rondas = Rondas(duracion=10.0)
        rondas.registrar_muestra(r, 0)

        rondas.actualizar(10.0, arbol, r)
        rondas.actualizar(10.0, arbol, r)

        self.assertEqual(len(rondas.historial), 3)
        self.assertEqual([m["ronda"] for m in rondas.historial], [0, 1, 2])
        for muestra in rondas.historial:
            self.assertIn("usuarios", muestra)
            self.assertIn("bienestar", muestra)
            self.assertIn("dinero", muestra)
            self.assertIn("reputacion", muestra)


class TestCalificacionFinal(unittest.TestCase):
    def test_victoria_sana_y_alta_reputacion_obtiene_s(self):
        resumen = {
            "rondas": 12,
            "usuarios": 50000,
            "usuarios_pico": 50000,
            "dinero_generado": 45000,
            "bienestar": 75,
            "reputacion": 80,
            "regiones": 8,
            "total_regiones": 8,
        }
        self.assertEqual(calcular_calificacion(VICTORIA, resumen), "S")

    def test_victoria_con_bienestar_moderado_obtiene_a(self):
        resumen = {
            "rondas": 14,
            "usuarios": 40000,
            "usuarios_pico": 40000,
            "dinero_generado": 30000,
            "bienestar": 42,
            "reputacion": 50,
            "regiones": 8,
            "total_regiones": 8,
        }
        self.assertEqual(calcular_calificacion(VICTORIA, resumen), "A")

    def test_derrota_avanzada_obtiene_b_y_derrota_temprana_obtiene_c(self):
        resumen_avanzado = {
            "rondas": 9,
            "usuarios": 0,
            "usuarios_pico": 12000,
            "dinero_generado": 18000,
            "bienestar": 20,
            "reputacion": 40,
            "regiones": 5,
            "total_regiones": 8,
        }
        resumen_temprano = {
            "rondas": 1,
            "usuarios": 200,
            "usuarios_pico": 500,
            "dinero_generado": 120,
            "bienestar": 30,
            "reputacion": 30,
            "regiones": 1,
            "total_regiones": 8,
        }
        self.assertEqual(calcular_calificacion(QUIEBRA, resumen_avanzado), "B")
        self.assertEqual(calcular_calificacion(EXODO, resumen_temprano), "C")
        self.assertIn(SATURACION, MOTIVOS_FIN)


class TestResumenView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()
        cls.pantalla = pygame.Surface((tema.ANCHO, tema.ALTO))
        cls.fuentes = tema.crear_fuentes()

    def test_dibujar_fin_renderiza_todos_los_motivos_sin_errores(self):
        historial = [
            {"ronda": 0, "usuarios": 500, "bienestar": 50, "dinero": 10000, "reputacion": 50},
            {"ronda": 1, "usuarios": 900, "bienestar": 58, "dinero": 11200, "reputacion": 55},
            {"ronda": 2, "usuarios": 1600, "bienestar": 45, "dinero": 13500, "reputacion": 60},
        ]
        for motivo in (VICTORIA, QUIEBRA, EXODO, SATURACION):
            resumen = {
                "rondas": 2,
                "usuarios": 1600,
                "usuarios_pico": 1600,
                "dinero_generado": 3500,
                "bienestar": 45,
                "reputacion": 60,
                "regiones": 3,
                "total_regiones": 8,
                "historial": historial,
            }
            dibujar_fin(self.pantalla, self.fuentes, motivo, resumen, 1.5)

    def test_reinicio_rapido_desde_boton_de_resumen_view(self):
        juego = Juego(audio=GestorAudio(habilitar_mixer=False))
        juego.estado = PRINCIPAL
        juego.recursos.dinero = -5000
        juego.actualizar(juego.rondas.duracion)
        self.assertEqual(juego.estado, FIN)

        resumen = juego._resumen_final()
        self.assertIn("usuarios_pico", resumen)
        self.assertIn("dinero_generado", resumen)
        self.assertIn("calificacion", resumen)
        self.assertGreaterEqual(len(resumen["historial"]), 2)

        # Clic en el botón "Nueva partida" de resumen_view reinicia sin salir
        juego.manejar_evento(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=RECT_BOTON_NUEVA.center, button=1)
        )
        self.assertEqual(juego.estado, PRINCIPAL)
        self.assertTrue(juego.corriendo)
        self.assertEqual(juego.rondas.numero, 1)

        # Y el botón "Salir" en FIN cierra la aplicación
        juego._ir_a(FIN)
        juego.manejar_evento(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=RECT_BOTON_SALIR.center, button=1)
        )
        self.assertFalse(juego.corriendo)


if __name__ == "__main__":
    unittest.main()
