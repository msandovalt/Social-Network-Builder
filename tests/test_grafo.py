"""Pruebas del grafo: BFS, Dijkstra y casos borde (sin Pygame)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import math

from mapa.grafo import Grafo


def grafo_de_ejemplo():
    r"""
        A --1-- B --1-- C
        |               |
        +-------5-------+      (A-C directo cuesta 5; A-B-C cuesta 2)
        C --1-- D        E (aislado)
    """
    g = Grafo()
    g.agregar_arista("A", "B", 1)
    g.agregar_arista("B", "C", 1)
    g.agregar_arista("A", "C", 5)
    g.agregar_arista("C", "D", 1)
    g.agregar_nodo("E")
    return g


class TestConstruccion(unittest.TestCase):
    def test_las_aristas_son_en_ambos_sentidos(self):
        g = grafo_de_ejemplo()
        self.assertEqual(g.peso("A", "B"), 1)
        self.assertEqual(g.peso("B", "A"), 1)

    def test_aristas_lista_cada_una_una_sola_vez(self):
        self.assertEqual(len(grafo_de_ejemplo().aristas()), 4)

    def test_vecinos_devuelve_una_copia(self):
        g = grafo_de_ejemplo()
        g.vecinos("A")["Z"] = 99
        self.assertNotIn("Z", g.vecinos("A"))

    def test_peso_negativo_lanza_error(self):
        with self.assertRaises(ValueError):
            Grafo().agregar_arista("A", "B", -1)

    def test_nodo_aislado_no_tiene_vecinos(self):
        self.assertEqual(grafo_de_ejemplo().vecinos("E"), {})


class TestBFS(unittest.TestCase):
    def test_bfs_visita_por_capas_y_solo_lo_alcanzable(self):
        orden = grafo_de_ejemplo().bfs("A")
        self.assertEqual(orden[0], "A")
        self.assertEqual(set(orden[1:3]), {"B", "C"})  # los dos vecinos de A van primero
        self.assertEqual(orden[3], "D")
        self.assertNotIn("E", orden)

    def test_bfs_con_nodo_inexistente_lanza_error(self):
        with self.assertRaises(KeyError):
            grafo_de_ejemplo().bfs("Z")

    def test_niveles_cuentan_saltos_e_ignoran_pesos(self):
        niveles = grafo_de_ejemplo().bfs_niveles(["A"])
        self.assertEqual(niveles, {"A": 0, "B": 1, "C": 1, "D": 2})

    def test_niveles_con_varios_origenes(self):
        niveles = grafo_de_ejemplo().bfs_niveles(["A", "D"])
        self.assertEqual(niveles["A"], 0)
        self.assertEqual(niveles["D"], 0)
        self.assertEqual(niveles["C"], 1)

    def test_niveles_con_limite_de_saltos(self):
        niveles = grafo_de_ejemplo().bfs_niveles(["A"], max_saltos=1)
        self.assertEqual(niveles, {"A": 0, "B": 1, "C": 1})  # D está a 2 saltos

    def test_niveles_con_limite_cero_solo_incluye_los_origenes(self):
        self.assertEqual(grafo_de_ejemplo().bfs_niveles(["A"], max_saltos=0), {"A": 0})

    def test_niveles_con_filtro_no_pasa_por_nodos_no_permitidos(self):
        niveles = grafo_de_ejemplo().bfs_niveles(["A"], permitido=lambda n: n != "C")
        self.assertEqual(niveles, {"A": 0, "B": 1})  # sin C no se llega a D

    def test_es_conexo(self):
        g = grafo_de_ejemplo()
        self.assertFalse(g.es_conexo())  # E está aislado
        g.agregar_arista("D", "E", 1)
        self.assertTrue(g.es_conexo())


class TestDijkstra(unittest.TestCase):
    def test_distancias_minimas(self):
        distancias, _ = grafo_de_ejemplo().dijkstra(["A"])
        self.assertEqual(distancias["B"], 1)
        self.assertEqual(distancias["C"], 2)  # por B, no el directo de costo 5
        self.assertEqual(distancias["D"], 3)

    def test_nodo_inalcanzable_tiene_distancia_infinita(self):
        distancias, _ = grafo_de_ejemplo().dijkstra(["A"])
        self.assertEqual(distancias["E"], math.inf)

    def test_camino_minimo_prefiere_menor_costo_aunque_tenga_mas_saltos(self):
        costo, camino = grafo_de_ejemplo().camino_minimo(["A"], "C")
        self.assertEqual(costo, 2)
        self.assertEqual(camino, ["A", "B", "C"])  # 2 saltos, pero más barato que el directo

    def test_camino_a_un_origen_es_el_mismo_nodo(self):
        self.assertEqual(grafo_de_ejemplo().camino_minimo(["A"], "A"), (0, ["A"]))

    def test_camino_a_nodo_inalcanzable(self):
        self.assertEqual(grafo_de_ejemplo().camino_minimo(["A"], "E"), (math.inf, []))

    def test_con_varios_origenes_elige_el_mas_conveniente(self):
        costo, camino = grafo_de_ejemplo().camino_minimo(["A", "D"], "C")
        self.assertEqual(costo, 1)
        self.assertEqual(camino, ["D", "C"])

    def test_sin_origenes_no_hay_camino(self):
        self.assertEqual(grafo_de_ejemplo().camino_minimo([], "C"), (math.inf, []))

    def test_origen_o_destino_inexistente_lanza_error(self):
        g = grafo_de_ejemplo()
        with self.assertRaises(KeyError):
            g.dijkstra(["Z"])
        with self.assertRaises(KeyError):
            g.camino_minimo(["A"], "Z")


if __name__ == "__main__":
    unittest.main()
