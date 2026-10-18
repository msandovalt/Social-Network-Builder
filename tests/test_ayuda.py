"""Pruebas del contenido de la ayuda (sin Pygame)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from eventos.gestor import INTERVALO_EVENTOS
from tree.ronda import DURACION_RONDA, UMBRAL_FUGA
from ui.ayuda_contenido import (
    PAGINAS, TOTAL_PAGINAS, INDICE_ACCESIBILIDAD, MAX_PUNTOS_POR_PAGINA, MAX_CARACTERES_POR_PUNTO,
)


def texto_completo():
    return " ".join(cab + " " + txt for p in PAGINAS for cab, txt in p["puntos"])


class TestContenidoDeLaAyuda(unittest.TestCase):
    def test_hay_paginas_con_titulos_unicos(self):
        self.assertGreaterEqual(TOTAL_PAGINAS, 6)
        titulos = [p["titulo"] for p in PAGINAS]
        self.assertEqual(len(titulos), len(set(titulos)))

    def test_cada_pagina_tiene_entre_dos_y_cuatro_puntos_con_texto(self):
        for pagina in PAGINAS:
            self.assertTrue(pagina["titulo"].strip())
            self.assertGreaterEqual(len(pagina["puntos"]), 2, pagina["titulo"])
            self.assertLessEqual(len(pagina["puntos"]), MAX_PUNTOS_POR_PAGINA, pagina["titulo"])
            for cabecera, texto in pagina["puntos"]:
                self.assertTrue(cabecera.strip() and texto.strip())

    def test_ningun_texto_es_demasiado_largo_para_la_pantalla(self):
        for pagina in PAGINAS:
            for cabecera, texto in pagina["puntos"]:
                self.assertLessEqual(len(texto), MAX_CARACTERES_POR_PUNTO, (pagina["titulo"], cabecera))

    def test_cubre_los_temas_que_pide_el_laboratorio(self):
        titulos = " ".join(p["titulo"].lower() for p in PAGINAS)
        for tema in ("objetivo", "recursos", "árbol", "mapa", "tragamonedas", "controles", "accesibilidad"):
            self.assertIn(tema, titulos)

    def test_los_numeros_salen_de_las_constantes_del_juego(self):
        texto = texto_completo()
        self.assertIn(f"{round(DURACION_RONDA)} segundos", texto)
        self.assertIn(f"{round(INTERVALO_EVENTOS)} segundos", texto)
        self.assertIn(f"baja de {UMBRAL_FUGA}", texto)

    def test_menciona_los_cuatro_tipos_de_daltonismo(self):
        pagina = PAGINAS[INDICE_ACCESIBILIDAD]
        texto = " ".join(t for _, t in pagina["puntos"]).lower()
        for nombre in ("protanopía", "deuteranopía", "tritanopía", "acromatopsia"):
            self.assertIn(nombre, texto)

    def test_el_texto_esta_en_tuteo(self):
        texto = texto_completo().lower()
        for voseo in ("tenés", "podés", "elegí", "hacé", "cuidá", "expandite", "tu comunidad vos"):
            self.assertNotIn(voseo, texto)


if __name__ == "__main__":
    unittest.main()
