"""Pruebas de los ajustes guardados (sin Pygame)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import json
import tempfile

from ajustes import Ajustes
from ui.paletas import PALETA_POR_DEFECTO


class TestAjustes(unittest.TestCase):
    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(self.carpeta.cleanup)
        self.ruta = os.path.join(self.carpeta.name, "ajustes.json")

    def escribir(self, contenido):
        with open(self.ruta, "w", encoding="utf-8") as f:
            f.write(contenido)

    def test_sin_archivo_usa_la_paleta_por_defecto(self):
        self.assertEqual(Ajustes(self.ruta).daltonismo, PALETA_POR_DEFECTO)

    def test_guarda_y_recupera_la_paleta(self):
        ajustes = Ajustes(self.ruta)
        ajustes.daltonismo = "tritanopia"
        self.assertTrue(ajustes.guardar())
        self.assertEqual(Ajustes(self.ruta).daltonismo, "tritanopia")

    def test_cada_paleta_valida_se_puede_guardar_y_recuperar(self):
        from ui.paletas import PALETAS
        for nombre in PALETAS:
            ajustes = Ajustes(self.ruta)
            ajustes.daltonismo = nombre
            ajustes.guardar()
            self.assertEqual(Ajustes(self.ruta).daltonismo, nombre)

    def test_un_archivo_danado_no_rompe_el_juego(self):
        self.escribir("esto no es json {{{")
        self.assertEqual(Ajustes(self.ruta).daltonismo, PALETA_POR_DEFECTO)

    def test_un_archivo_vacio_no_rompe_el_juego(self):
        self.escribir("")
        self.assertEqual(Ajustes(self.ruta).daltonismo, PALETA_POR_DEFECTO)

    def test_un_valor_invalido_se_ignora(self):
        self.escribir(json.dumps({"daltonismo": "marciano"}))
        self.assertEqual(Ajustes(self.ruta).daltonismo, PALETA_POR_DEFECTO)

    def test_un_json_que_no_es_un_diccionario_se_ignora(self):
        for contenido in ("[1, 2, 3]", '"deuteranopia"', "null", "42"):
            self.escribir(contenido)
            self.assertEqual(Ajustes(self.ruta).daltonismo, PALETA_POR_DEFECTO, contenido)

    def test_un_tipo_equivocado_en_el_valor_se_ignora(self):
        self.escribir(json.dumps({"daltonismo": ["deuteranopia"]}))
        self.assertEqual(Ajustes(self.ruta).daltonismo, PALETA_POR_DEFECTO)

    def test_si_no_se_puede_guardar_no_lanza_error(self):
        ajustes = Ajustes(self.carpeta.name)  # una carpeta no se puede abrir como archivo
        ajustes.daltonismo = "protanopia"
        self.assertFalse(ajustes.guardar())

    def test_guardar_en_una_ruta_inexistente_no_lanza_error(self):
        ajustes = Ajustes(os.path.join(self.carpeta.name, "no_existe", "a.json"))
        self.assertFalse(ajustes.guardar())


if __name__ == "__main__":
    unittest.main()
