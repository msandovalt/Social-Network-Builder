"""Pruebas de las paletas de color, incluidas las de daltonismo (sin Pygame).

Usan un simulador de daltonismo (_cvd.py, matrices de Machado et al. 2009) para
comprobar que, vista con el tipo de daltonismo al que está dirigida, cada
paleta mantiene bien distintos los colores que importan: éxito/peligro,
botones, estados de nodos y de regiones, y los recursos.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import itertools

from _cvd import delta_e, contraste, simular, a_lab
from ui.paletas import PALETAS, OPCIONES, NOMBRES_COLOR, PALETA_POR_DEFECTO, es_paleta_valida

TIPOS = ("protanopia", "deuteranopia", "tritanopia", "acromatopsia")

# Pares que deben distinguirse siempre, por grupo
GRUPOS = {
    "éxito y peligro": [("verde", "rojo")],
    "botones": [("boton_ok", "boton_peligro")],
    "nodos": list(itertools.combinations(("bloqueado", "teal", "naranja"), 2)),
    "regiones": list(itertools.combinations(("verde", "amarillo", "naranja", "bloqueado"), 2)),
    "recursos": list(itertools.combinations(
        ("recurso_dinero", "recurso_usuarios", "recurso_bienestar", "recurso_reputacion", "recurso_engagement"), 2)),
}
# ΔE mínimo (CIE76) exigido en la simulación; en gris hay menos margen y se compensa con formas e íconos
UMBRALES = {
    "cromaticas": {"éxito y peligro": 60, "botones": 60, "nodos": 25, "regiones": 25, "recursos": 25},
    "acromatopsia": {"éxito y peligro": 30, "botones": 20, "nodos": 20, "regiones": 20, "recursos": 8},
}


class TestEstructura(unittest.TestCase):
    def test_todas_las_paletas_definen_los_mismos_colores(self):
        for nombre, paleta in PALETAS.items():
            self.assertEqual(set(paleta), set(NOMBRES_COLOR), nombre)

    def test_los_colores_son_rgb_validos(self):
        for nombre, paleta in PALETAS.items():
            for clave, color in paleta.items():
                self.assertEqual(len(color), 3, (nombre, clave))
                for canal in color:
                    self.assertIsInstance(canal, int)
                    self.assertTrue(0 <= canal <= 255, (nombre, clave))

    def test_hay_una_opcion_por_paleta_y_cubre_los_cuatro_tipos(self):
        ids = [i for i, _, _ in OPCIONES]
        self.assertEqual(set(ids), set(PALETAS))
        self.assertEqual(len(ids), len(set(ids)))
        for tipo in TIPOS:
            self.assertIn(tipo, ids)
        self.assertEqual(ids[0], PALETA_POR_DEFECTO)
        for _, nombre, descripcion in OPCIONES:
            self.assertTrue(nombre.strip() and descripcion.strip())

    def test_validacion_de_nombres(self):
        self.assertTrue(es_paleta_valida("deuteranopia"))
        self.assertFalse(es_paleta_valida("inventada"))
        self.assertFalse(es_paleta_valida(None))


class TestLegibilidad(unittest.TestCase):
    def test_el_texto_se_lee_sobre_los_paneles_en_todas_las_paletas(self):
        for nombre, p in PALETAS.items():
            self.assertGreaterEqual(contraste(p["texto"], p["panel"]), 7.0, nombre)
            self.assertGreaterEqual(contraste(p["texto_sec"], p["panel"]), 4.5, nombre)
            self.assertGreaterEqual(contraste(p["texto"], p["fondo_arriba"]), 7.0, nombre)

    def test_los_colores_de_significado_se_ven_sobre_el_panel(self):
        # WCAG 1.4.11: los elementos gráficos necesitan al menos 3:1 de contraste
        for nombre, p in PALETAS.items():
            for clave in ("verde", "rojo", "amarillo", "naranja", "teal", "acento"):
                self.assertGreaterEqual(contraste(p[clave], p["panel"]), 2.9, (nombre, clave))

    def test_la_acromatopsia_usa_solo_grises(self):
        for clave, (r, g, b) in PALETAS["acromatopsia"].items():
            self.assertTrue(r == g == b, clave)


class TestSimulador(unittest.TestCase):
    def test_un_color_identico_tiene_distancia_cero(self):
        self.assertEqual(delta_e((10, 200, 30), (10, 200, 30), "deuteranopia"), 0)

    def test_los_grises_no_cambian_con_el_daltonismo_de_color(self):
        for tipo in ("protanopia", "deuteranopia", "tritanopia"):
            for gris in (30, 128, 220):
                sim = simular((gris, gris, gris), tipo)
                for canal in sim:
                    self.assertAlmostEqual(canal, gris, delta=3)

    def test_la_paleta_normal_confunde_verde_y_rojo_para_un_deuteranope(self):
        """Comprueba que el simulador detecta el problema que las paletas nuevas resuelven."""
        normal = PALETAS["normal"]
        self.assertLess(delta_e(normal["verde"], normal["rojo"], "deuteranopia"), 30)
        self.assertLess(delta_e(normal["verde"], normal["rojo"], "protanopia"), 30)


class TestDistinguibilidad(unittest.TestCase):
    def comprobar(self, nombre_paleta, tipo, umbrales):
        paleta = PALETAS[nombre_paleta]
        for grupo, pares in GRUPOS.items():
            for a, b in pares:
                distancia = delta_e(paleta[a], paleta[b], tipo)
                self.assertGreaterEqual(
                    distancia, umbrales[grupo],
                    f"{nombre_paleta} vista como {tipo}: {a} vs {b} ({grupo}) = {distancia:.1f}")

    def test_protanopia(self):
        self.comprobar("protanopia", "protanopia", UMBRALES["cromaticas"])

    def test_deuteranopia(self):
        self.comprobar("deuteranopia", "deuteranopia", UMBRALES["cromaticas"])

    def test_tritanopia(self):
        self.comprobar("tritanopia", "tritanopia", UMBRALES["cromaticas"])

    def test_acromatopsia(self):
        self.comprobar("acromatopsia", "acromatopsia", UMBRALES["acromatopsia"])

    def test_cada_paleta_tambien_funciona_con_el_resto_de_la_pantalla_clara_u_oscura(self):
        # Todas son paletas oscuras: el fondo debe ser mucho más oscuro que el texto
        for nombre, p in PALETAS.items():
            self.assertLess(a_lab(p["fondo_arriba"])[0], 20, nombre)
            self.assertGreater(a_lab(p["texto"])[0], 90, nombre)


if __name__ == "__main__":
    unittest.main()
