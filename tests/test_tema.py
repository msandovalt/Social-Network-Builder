"""Pruebas del cambio de paleta en el tema (usa solo constantes de Pygame)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pygame

from _cvd import contraste
from ui import tema
from ui.paletas import PALETAS, NOMBRES_COLOR


class TestCambioDePaleta(unittest.TestCase):
    def tearDown(self):
        tema.aplicar_paleta("normal")

    def test_empieza_con_la_paleta_normal(self):
        tema.aplicar_paleta("normal")
        self.assertEqual(tema.PALETA_ACTUAL, "normal")
        self.assertEqual(tema.COLOR_VERDE, PALETAS["normal"]["verde"])

    def test_aplicar_una_paleta_cambia_los_colores_del_modulo(self):
        tema.aplicar_paleta("deuteranopia")
        self.assertEqual(tema.PALETA_ACTUAL, "deuteranopia")
        self.assertEqual(tema.COLOR_VERDE, PALETAS["deuteranopia"]["verde"])
        self.assertNotEqual(tema.COLOR_VERDE, PALETAS["normal"]["verde"])

    def test_cada_color_de_cada_paleta_llega_al_tema(self):
        for nombre, paleta in PALETAS.items():
            tema.aplicar_paleta(nombre)
            for clave in NOMBRES_COLOR:
                if clave.startswith("recurso_"):
                    self.assertEqual(tema.COLOR_RECURSO[clave[len("recurso_"):]], paleta[clave], (nombre, clave))
                else:
                    self.assertEqual(getattr(tema, "COLOR_" + clave.upper()), paleta[clave], (nombre, clave))

    def test_el_diccionario_de_recursos_se_actualiza_en_el_mismo_objeto(self):
        referencia = tema.COLOR_RECURSO  # quien lo guardó antes del cambio sigue viendo los valores nuevos
        tema.aplicar_paleta("tritanopia")
        self.assertIs(tema.COLOR_RECURSO, referencia)
        self.assertEqual(referencia["dinero"], PALETAS["tritanopia"]["recurso_dinero"])

    def test_una_paleta_desconocida_lanza_error_y_no_cambia_nada(self):
        tema.aplicar_paleta("protanopia")
        with self.assertRaises(ValueError):
            tema.aplicar_paleta("inventada")
        self.assertEqual(tema.PALETA_ACTUAL, "protanopia")
        self.assertEqual(tema.COLOR_VERDE, PALETAS["protanopia"]["verde"])

    def test_cambiar_de_paleta_descarta_las_superficies_en_cache(self):
        tema._cache[("prueba",)] = object()
        tema.aplicar_paleta("acromatopsia")
        self.assertNotIn(("prueba",), tema._cache)

    def test_volver_a_la_paleta_normal_restaura_los_colores(self):
        tema.aplicar_paleta("acromatopsia")
        tema.aplicar_paleta("normal")
        for clave in NOMBRES_COLOR:
            if not clave.startswith("recurso_"):
                self.assertEqual(getattr(tema, "COLOR_" + clave.upper()), PALETAS["normal"][clave])


class TestColorSobre(unittest.TestCase):
    def tearDown(self):
        tema.aplicar_paleta("normal")

    def test_texto_oscuro_sobre_fondo_claro_y_claro_sobre_fondo_oscuro(self):
        self.assertEqual(tema.color_sobre((255, 255, 255)), tema.COLOR_FONDO_ARRIBA)
        self.assertEqual(tema.color_sobre((10, 10, 10)), tema.COLOR_TEXTO)

    def test_siempre_alcanza_buen_contraste_con_los_colores_de_cada_paleta(self):
        for nombre, paleta in PALETAS.items():
            tema.aplicar_paleta(nombre)
            for clave, fondo in paleta.items():
                if clave in ("texto", "texto_sec"):
                    continue
                tinta = tema.color_sobre(fondo)
                self.assertGreaterEqual(contraste(tinta, fondo), 3.0, (nombre, clave, fondo, tinta))

    def test_luminancia_en_los_extremos(self):
        self.assertAlmostEqual(tema.luminancia((0, 0, 0)), 0.0)
        self.assertAlmostEqual(tema.luminancia((255, 255, 255)), 1.0, places=3)


if __name__ == "__main__":
    unittest.main()
