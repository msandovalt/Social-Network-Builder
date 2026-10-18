"""Pruebas del planeta: expansión, requisitos, rutas e ingresos (sin Pygame)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import math

from mapa.mundo import Mundo, Region, CONQUISTADA, DISPONIBLE, BLOQUEADA, LEJANA
from tree.arbol import Arbol
from tree.recursos import Recursos


class TestMundoInicial(unittest.TestCase):
    def setUp(self):
        self.mundo = Mundo.construir_mundo_inicial()
        self.arbol = Arbol.construir_arbol_inicial()
        self.recursos = Recursos(dinero=100000, usuarios=10000, reputacion=100)
        self.arbol.desbloquear_gratuitos(self.recursos)

    def _desbloquear(self, *ids):
        for id_nodo in ids:
            nodo = self.arbol.nodo_por_id(id_nodo)
            nodo.desbloquear(self.recursos)

    def test_el_planeta_tiene_8_regiones_y_es_conexo(self):
        self.assertEqual(len(self.mundo.regiones), 8)
        self.assertTrue(self.mundo.grafo.es_conexo())

    def test_empieza_conquistando_solo_sudamerica(self):
        self.assertEqual(self.mundo.conquistadas(), ["sudamerica"])

    def test_la_frontera_inicial_son_las_vecinas_de_sudamerica(self):
        self.assertEqual(set(self.mundo.frontera()), {"centroamerica", "africa"})

    def test_todos_los_nodos_exigidos_existen_en_el_arbol(self):
        ids = {n.id for n in self.arbol.recorrido_bfs()}
        for region in self.mundo.regiones.values():
            for id_nodo in region.nodos:
                self.assertIn(id_nodo, ids)

    def test_estados_de_las_regiones(self):
        estado = lambda r: self.mundo.estado_region(r, self.arbol, self.recursos)
        self.assertEqual(estado("sudamerica"), CONQUISTADA)
        self.assertEqual(estado("centroamerica"), BLOQUEADA)  # vecina, pero falta el nodo
        self.assertEqual(estado("europa"), LEJANA)
        self._desbloquear("feed_basico")
        self.assertEqual(estado("centroamerica"), DISPONIBLE)

    def test_el_costo_de_expansion_es_la_arista_mas_barata_desde_una_region_tuya(self):
        self.assertEqual(self.mundo.costo_expansion("centroamerica"), 1500)
        self.assertEqual(self.mundo.costo_expansion("africa"), 4500)
        self.assertIsNone(self.mundo.costo_expansion("europa"))      # lejana
        self.assertIsNone(self.mundo.costo_expansion("sudamerica"))  # ya es tuya

    def test_costo_toma_la_arista_mas_barata_entre_varias_regiones_tuyas(self):
        self.mundo.regiones["africa"].conquistada = True
        self.mundo.regiones["europa"].conquistada = False
        # Medio Oriente conecta con África (2500) y con Europa (2500, no tuya)
        self.assertEqual(self.mundo.costo_expansion("medio_oriente"), 2500)
        self.mundo.regiones["asia"].conquistada = True
        self.assertEqual(self.mundo.costo_expansion("medio_oriente"), 2000)  # ahora Asia es más barata


class TestRequisitos(unittest.TestCase):
    def setUp(self):
        self.mundo = Mundo.construir_mundo_inicial()
        self.arbol = Arbol.construir_arbol_inicial()
        self.recursos = Recursos(dinero=10000, usuarios=500)
        self.arbol.desbloquear_gratuitos(self.recursos)

    def test_los_requisitos_de_una_region_vecina_se_listan_con_su_estado(self):
        reqs = {r.tipo: r for r in self.mundo.requisitos("centroamerica", self.arbol, self.recursos)}
        self.assertTrue(reqs["vecina"].cumplido)
        self.assertFalse(reqs["nodo"].cumplido)
        self.assertEqual(reqs["nodo"].etiqueta, self.arbol.nodo_por_id("feed_basico").nombre)
        self.assertFalse(reqs["usuarios"].cumplido)
        self.assertEqual((reqs["usuarios"].actual, reqs["usuarios"].necesario), (500, 600))
        self.assertTrue(reqs["dinero"].cumplido)

    def test_una_region_lejana_no_exige_dinero_porque_aun_no_se_puede_pagar_su_ruta(self):
        tipos = [r.tipo for r in self.mundo.requisitos("europa", self.arbol, self.recursos)]
        self.assertNotIn("dinero", tipos)
        self.assertFalse(self.mundo.requisitos("europa", self.arbol, self.recursos)[0].cumplido)

    def test_una_region_conquistada_no_tiene_requisitos(self):
        self.assertEqual(self.mundo.requisitos("sudamerica", self.arbol, self.recursos), [])

    def test_la_reputacion_minima_se_exige_cuando_la_region_la_pide(self):
        region = self.mundo.regiones["norteamerica"]
        self.assertGreater(region.reputacion, 0)
        tipos = [r.tipo for r in self.mundo.requisitos("norteamerica", self.arbol, self.recursos)]
        self.assertIn("reputacion", tipos)


class TestBienestarMinimo(unittest.TestCase):
    def setUp(self):
        self.mundo = Mundo.construir_mundo_inicial()
        self.arbol = Arbol.construir_arbol_inicial()
        self.recursos = Recursos(dinero=100000, usuarios=9999, reputacion=100, bienestar=70)
        self.arbol.desbloquear_gratuitos(self.recursos)
        self.arbol.nodo_por_id("seguridad_basica").desbloquear(self.recursos)
        self.mundo.regiones["sudamerica"].conquistada = True

    def tipos(self, id_region):
        return [r.tipo for r in self.mundo.requisitos(id_region, self.arbol, self.recursos)]

    def test_las_regiones_lejanas_exigen_bienestar_pero_la_primera_no(self):
        self.assertNotIn("bienestar", self.tipos("centroamerica"))
        for id_region in ("norteamerica", "africa", "europa", "medio_oriente", "asia", "oceania"):
            self.assertIn("bienestar", self.tipos(id_region), id_region)

    def test_el_bienestar_exigido_crece_con_la_distancia_a_los_mercados_exigentes(self):
        minimos = {id_region: r.bienestar for id_region, r in self.mundo.regiones.items()}
        self.assertLess(minimos["africa"], minimos["europa"])
        self.assertLess(minimos["europa"], minimos["oceania"])

    def test_con_bienestar_bajo_no_se_puede_expandir_aunque_se_cumpla_todo_lo_demas(self):
        self.assertEqual(self.mundo.estado_region("africa", self.arbol, self.recursos), DISPONIBLE)
        self.recursos.bienestar = 30
        self.assertEqual(self.mundo.estado_region("africa", self.arbol, self.recursos), BLOQUEADA)
        dinero = self.recursos.dinero
        self.assertFalse(self.mundo.expandir("africa", self.arbol, self.recursos))
        self.assertEqual(self.recursos.dinero, dinero)

    def test_el_requisito_de_bienestar_muestra_el_valor_actual_y_el_necesario(self):
        self.recursos.bienestar = 33
        req = next(r for r in self.mundo.requisitos("africa", self.arbol, self.recursos) if r.tipo == "bienestar")
        self.assertEqual((req.actual, req.necesario, req.cumplido), (33, 40, False))

    def test_recuperar_el_bienestar_reabre_la_expansion(self):
        self.recursos.bienestar = 30
        self.assertFalse(self.mundo.puede_expandirse("africa", self.arbol, self.recursos))
        self.recursos.bienestar = 40
        self.assertTrue(self.mundo.puede_expandirse("africa", self.arbol, self.recursos))


class TestExpansion(unittest.TestCase):
    def setUp(self):
        self.mundo = Mundo.construir_mundo_inicial()
        self.arbol = Arbol.construir_arbol_inicial()
        self.recursos = Recursos(dinero=20000, usuarios=5000, reputacion=100)
        self.arbol.desbloquear_gratuitos(self.recursos)

    def test_no_se_puede_expandir_si_falta_un_requisito(self):
        self.assertFalse(self.mundo.expandir("centroamerica", self.arbol, self.recursos))
        self.assertFalse(self.mundo.regiones["centroamerica"].conquistada)
        self.assertEqual(self.recursos.dinero, 20000)

    def test_expandir_cobra_el_costo_y_conquista(self):
        self.arbol.nodo_por_id("feed_basico").desbloquear(self.recursos)  # cuesta 2000
        dinero = self.recursos.dinero
        self.assertTrue(self.mundo.expandir("centroamerica", self.arbol, self.recursos))
        self.assertTrue(self.mundo.regiones["centroamerica"].conquistada)
        self.assertEqual(self.recursos.dinero, dinero - 1500)

    def test_no_se_puede_expandir_a_una_region_lejana_aunque_se_tenga_todo(self):
        for id_nodo in ("seguridad_basica", "seguridad_avanzada"):
            self.arbol.nodo_por_id(id_nodo).desbloquear(self.recursos)
        self.recursos.dinero = 100000
        self.assertFalse(self.mundo.expandir("europa", self.arbol, self.recursos))  # no es vecina aún

    def test_sin_dinero_suficiente_no_se_expande(self):
        self.arbol.nodo_por_id("feed_basico").desbloquear(self.recursos)
        self.recursos.dinero = 1499
        self.assertFalse(self.mundo.expandir("centroamerica", self.arbol, self.recursos))
        self.assertEqual(self.recursos.dinero, 1499)

    def test_expandir_abre_nuevas_regiones_en_la_frontera(self):
        self.arbol.nodo_por_id("feed_basico").desbloquear(self.recursos)
        self.mundo.expandir("centroamerica", self.arbol, self.recursos)
        self.assertIn("norteamerica", self.mundo.frontera())
        self.assertNotIn("centroamerica", self.mundo.frontera())

    def test_no_se_puede_conquistar_dos_veces(self):
        self.arbol.nodo_por_id("feed_basico").desbloquear(self.recursos)
        self.mundo.expandir("centroamerica", self.arbol, self.recursos)
        dinero = self.recursos.dinero
        self.assertFalse(self.mundo.expandir("centroamerica", self.arbol, self.recursos))
        self.assertEqual(self.recursos.dinero, dinero)


class TestRutas(unittest.TestCase):
    def test_la_ruta_mas_barata_a_europa_da_un_rodeo_por_norteamerica(self):
        mundo = Mundo.construir_mundo_inicial()
        costo, camino = mundo.ruta_mas_barata("europa")
        self.assertEqual(camino, ["sudamerica", "centroamerica", "norteamerica", "europa"])
        self.assertEqual(costo, 6000)  # por África serían 6500

    def test_bfs_y_dijkstra_no_coinciden_en_europa(self):
        mundo = Mundo.construir_mundo_inicial()
        saltos_bfs = mundo.saltos()["europa"]
        _, camino = mundo.ruta_mas_barata("europa")
        self.assertEqual(saltos_bfs, 2)             # por África, el camino más corto en saltos
        self.assertEqual(len(camino) - 1, 3)        # pero el más barato usa 3 pasos

    def test_la_ruta_parte_de_la_region_conquistada_mas_conveniente(self):
        mundo = Mundo.construir_mundo_inicial()
        mundo.regiones["norteamerica"].conquistada = True
        costo, camino = mundo.ruta_mas_barata("europa")
        self.assertEqual((costo, camino), (3000, ["norteamerica", "europa"]))

    def test_sin_regiones_conquistadas_no_hay_ruta(self):
        mundo = Mundo.construir_mundo_inicial()
        mundo.regiones["sudamerica"].conquistada = False
        self.assertEqual(mundo.ruta_mas_barata("europa"), (math.inf, []))


class TestVictoriaYPropagacion(unittest.TestCase):
    def test_la_victoria_requiere_conquistar_todo_el_planeta(self):
        mundo = Mundo.construir_mundo_inicial()
        self.assertFalse(mundo.todas_conquistadas())
        for region in mundo.regiones.values():
            region.conquistada = True
        self.assertTrue(mundo.todas_conquistadas())
        mundo.regiones["oceania"].conquistada = False
        self.assertFalse(mundo.todas_conquistadas())

    def test_regiones_alcanzadas_solo_pasa_por_regiones_conquistadas(self):
        mundo = Mundo.construir_mundo_inicial()
        self.assertEqual(mundo.regiones_alcanzadas("sudamerica", 5), ["sudamerica"])
        mundo.regiones["centroamerica"].conquistada = True
        self.assertEqual(mundo.regiones_alcanzadas("sudamerica", 5), ["sudamerica", "centroamerica"])

    def test_regiones_alcanzadas_respeta_el_limite_de_saltos(self):
        mundo = Mundo.construir_mundo_inicial()
        for id_region in ("centroamerica", "norteamerica", "europa"):
            mundo.regiones[id_region].conquistada = True
        self.assertEqual(mundo.regiones_alcanzadas("sudamerica", 2), ["sudamerica", "centroamerica", "norteamerica"])
        self.assertEqual(mundo.regiones_alcanzadas("sudamerica", 0), ["sudamerica"])


class TestCapacidad(unittest.TestCase):
    def setUp(self):
        self.mundo = Mundo.construir_mundo_inicial()
        self.arbol = Arbol.construir_arbol_inicial()
        self.recursos = Recursos(dinero=100000, usuarios=500, reputacion=100, bienestar=70)
        self.arbol.desbloquear_gratuitos(self.recursos)

    def test_la_capacidad_inicial_es_la_de_sudamerica(self):
        self.assertEqual(self.mundo.capacidad_total(), self.mundo.regiones["sudamerica"].capacidad)
        self.assertGreater(self.mundo.capacidad_total(), 0)

    def test_la_capacidad_suma_las_regiones_conquistadas(self):
        antes = self.mundo.capacidad_total()
        self.mundo.regiones["centroamerica"].conquistada = True
        self.assertEqual(self.mundo.capacidad_total(), antes + self.mundo.regiones["centroamerica"].capacidad)

    def test_expandir_sube_el_limite_de_usuarios_de_los_recursos(self):
        self.recursos.actualizar_limite_usuarios(self.mundo.capacidad_total())
        self.arbol.nodo_por_id("feed_basico").desbloquear(self.recursos)
        self.recursos.usuarios = 1000
        antes = self.recursos.limite_usuarios
        self.assertTrue(self.mundo.expandir("centroamerica", self.arbol, self.recursos))
        self.assertEqual(self.recursos.limite_usuarios, antes + self.mundo.regiones["centroamerica"].capacidad)

    def test_todas_las_regiones_aportan_capacidad(self):
        for region in self.mundo.regiones.values():
            self.assertGreater(region.capacidad, 0, region.id)

    def test_el_planeta_se_puede_conquistar_con_los_topes(self):
        """Cada región debe poder alcanzarse: sus usuarios mínimos no pueden
        superar la capacidad que ya tienes cuando te toca conquistarla.
        Se simula conquistando siempre lo que el tope permite."""
        conquistadas = {"sudamerica"}
        progreso = True
        while progreso:
            progreso = False
            capacidad = sum(self.mundo.regiones[i].capacidad for i in conquistadas)
            for id_region, region in self.mundo.regiones.items():
                if id_region in conquistadas:
                    continue
                vecina = any(v in conquistadas for v in self.mundo.grafo.vecinos(id_region))
                if vecina and region.usuarios <= capacidad:
                    conquistadas.add(id_region)
                    progreso = True
        self.assertEqual(conquistadas, set(self.mundo.regiones))

    def test_cada_region_exige_menos_usuarios_que_su_capacidad_acumulada_minima(self):
        # El mínimo de usuarios de una región nunca supera el tope total del planeta.
        total = sum(r.capacidad for r in self.mundo.regiones.values())
        for region in self.mundo.regiones.values():
            self.assertLessEqual(region.usuarios, total)


class TestIngresos(unittest.TestCase):
    def test_los_ingresos_suman_solo_las_regiones_conquistadas(self):
        mundo = Mundo.construir_mundo_inicial()
        self.assertEqual(mundo.efectos_totales_de_la_ronda(), {"usuarios": 25, "dinero": 120})
        mundo.regiones["centroamerica"].conquistada = True
        self.assertEqual(mundo.efectos_totales_de_la_ronda(), {"usuarios": 55, "dinero": 220})

    def test_mundo_propio_con_regiones_personalizadas(self):
        mundo = Mundo()
        mundo.agregar_region(Region("a", "A", "", {"dinero": 10}))
        mundo.agregar_region(Region("b", "B", "", {"dinero": 5, "usuarios": 1}))
        mundo.conectar("a", "b", 7)
        mundo.regiones["a"].conquistada = True
        mundo.regiones["b"].conquistada = True
        self.assertEqual(mundo.efectos_totales_de_la_ronda(), {"dinero": 15, "usuarios": 1})


if __name__ == "__main__":
    unittest.main()
