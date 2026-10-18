"""Pruebas de los eventos aleatorios (sin Pygame)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import random

from eventos.evento import Evento, CATALOGO, POSITIVO, NEGATIVO, ALERTA_BIENESTAR
from eventos.gestor import GestorEventos, aplicar_evento, INTERVALO_EVENTOS
from mapa.mundo import Mundo
from tree.arbol import Arbol
from tree.recursos import Recursos


class RngFijo:
    """Elige siempre el primer elemento: hace las pruebas deterministas."""
    def choice(self, secuencia):
        return secuencia[0]


def partida():
    arbol = Arbol.construir_arbol_inicial()
    recursos = Recursos(dinero=1000000, usuarios=5000, reputacion=50, bienestar=50, engagement=30)
    arbol.desbloquear_gratuitos(recursos)
    return arbol, recursos, Mundo.construir_mundo_inicial()


def desbloquear(arbol, recursos, *ids):
    for id_nodo in ids:
        arbol.nodo_por_id(id_nodo).desbloquear(recursos)


def conquistar(mundo, *ids):
    for id_region in ids:
        mundo.regiones[id_region].conquistada = True


class TestCatalogo(unittest.TestCase):
    def test_los_ids_son_unicos_y_los_tonos_validos(self):
        ids = [e.id for e in CATALOGO]
        self.assertEqual(len(ids), len(set(ids)))
        for evento in CATALOGO:
            self.assertIn(evento.tono, (POSITIVO, NEGATIVO))
            self.assertTrue(evento.titulo and evento.descripcion)

    def test_hay_eventos_buenos_y_malos_y_de_propagacion(self):
        self.assertTrue(any(e.tono == POSITIVO for e in CATALOGO))
        self.assertTrue(any(e.tono == NEGATIVO for e in CATALOGO))
        self.assertTrue(any(e.se_propaga for e in CATALOGO))

    def test_todos_los_nodos_mencionados_existen_en_el_arbol(self):
        arbol = Arbol.construir_arbol_inicial()
        for evento in CATALOGO:
            for id_nodo in (*evento.mitigadores, *evento.contencion, *evento.requiere_nodos):
                arbol.nodo_por_id(id_nodo)  # lanza KeyError si no existe

    def test_la_alerta_de_bienestar_no_sale_al_azar(self):
        self.assertNotIn(ALERTA_BIENESTAR.id, [e.id for e in CATALOGO])
        self.assertEqual(ALERTA_BIENESTAR.tono, NEGATIVO)

    def test_ningun_evento_puede_dejar_en_quiebra_de_golpe_a_quien_empieza(self):
        recursos_iniciales = Recursos()
        for evento in CATALOGO:
            perdida = evento.efectos.get("dinero", 0)
            self.assertGreater(recursos_iniciales.dinero + perdida, 0, evento.id)


class TestTemporizador(unittest.TestCase):
    def setUp(self):
        self.arbol, self.recursos, self.mundo = partida()
        self.gestor = GestorEventos(rng=random.Random(1))

    def test_el_intervalo_por_defecto_es_de_30_segundos(self):
        self.assertEqual(INTERVALO_EVENTOS, 30.0)
        self.assertEqual(self.gestor.intervalo, 30.0)

    def test_no_hay_evento_antes_del_intervalo(self):
        self.assertIsNone(self.gestor.actualizar(29.9, self.arbol, self.recursos, self.mundo))
        self.assertAlmostEqual(self.gestor.segundos_restantes(), 0.1)

    def test_al_completar_el_intervalo_ocurre_un_evento(self):
        self.gestor.actualizar(29.9, self.arbol, self.recursos, self.mundo)
        resultado = self.gestor.actualizar(0.2, self.arbol, self.recursos, self.mundo)
        self.assertIsNotNone(resultado)
        self.assertIs(self.gestor.ultimo, resultado)
        self.assertEqual(len(self.gestor.historial), 1)

    def test_con_un_dt_enorme_solo_ocurre_un_evento(self):
        self.gestor.actualizar(500, self.arbol, self.recursos, self.mundo)
        self.assertEqual(len(self.gestor.historial), 1)
        self.assertLess(self.gestor.acumulado, self.gestor.intervalo)

    def test_los_eventos_siguen_ocurriendo_cada_intervalo(self):
        for _ in range(3):
            self.gestor.actualizar(30.0, self.arbol, self.recursos, self.mundo)
        self.assertEqual(len(self.gestor.historial), 3)


class TestSeleccion(unittest.TestCase):
    def test_la_misma_semilla_da_la_misma_secuencia(self):
        def secuencia(semilla):
            arbol, recursos, mundo = partida()
            gestor = GestorEventos(rng=random.Random(semilla))
            return [gestor.disparar(arbol, recursos, mundo).evento.id for _ in range(6)]
        self.assertEqual(secuencia(7), secuencia(7))

    def test_no_repite_el_evento_anterior_si_hay_otra_opcion(self):
        arbol, recursos, mundo = partida()
        a = Evento("a", "A", "x", POSITIVO, efectos={"dinero": 1})
        b = Evento("b", "B", "x", POSITIVO, efectos={"dinero": 1})
        gestor = GestorEventos(catalogo=[a, b], rng=random.Random(3))
        ids = [gestor.disparar(arbol, recursos, mundo).evento.id for _ in range(10)]
        for anterior, siguiente in zip(ids, ids[1:]):
            self.assertNotEqual(anterior, siguiente)

    def test_con_un_solo_evento_posible_se_puede_repetir(self):
        arbol, recursos, mundo = partida()
        unico = Evento("u", "U", "x", POSITIVO, efectos={"dinero": 1})
        gestor = GestorEventos(catalogo=[unico])
        self.assertEqual(gestor.disparar(arbol, recursos, mundo).evento.id, "u")
        self.assertEqual(gestor.disparar(arbol, recursos, mundo).evento.id, "u")

    def test_un_evento_con_requisito_de_nodo_solo_sale_si_el_nodo_esta_desbloqueado(self):
        arbol, recursos, mundo = partida()
        scroll = next(e for e in CATALOGO if e.id == "adiccion_scroll")
        self.assertFalse(scroll.es_elegible(arbol))
        desbloquear(arbol, recursos, "feed_scroll")
        self.assertTrue(scroll.es_elegible(arbol))

    def test_el_evento_de_scroll_nunca_sale_si_no_se_construyo_el_scroll(self):
        arbol, recursos, mundo = partida()
        gestor = GestorEventos(rng=random.Random(11))
        for _ in range(200):
            self.assertNotEqual(gestor.elegir_evento(arbol).id, "adiccion_scroll")

    def test_sin_eventos_elegibles_no_pasa_nada(self):
        arbol, recursos, mundo = partida()
        solo_scroll = [e for e in CATALOGO if e.id == "adiccion_scroll"]
        gestor = GestorEventos(catalogo=solo_scroll)
        self.assertIsNone(gestor.disparar(arbol, recursos, mundo))


class TestEfectos(unittest.TestCase):
    def setUp(self):
        self.arbol, self.recursos, self.mundo = partida()
        self.rng = RngFijo()

    def test_aplica_los_efectos_a_los_recursos(self):
        evento = Evento("e", "E", "x", POSITIVO, efectos={"dinero": 1500, "reputacion": 8})
        dinero, reputacion = self.recursos.dinero, self.recursos.reputacion
        aplicar_evento(evento, self.arbol, self.recursos, self.mundo, self.rng)
        self.assertEqual(self.recursos.dinero, dinero + 1500)
        self.assertEqual(self.recursos.reputacion, reputacion + 8)

    def test_el_engagement_se_convierte_de_fraccion_a_puntos(self):
        evento = Evento("e", "E", "x", POSITIVO, efectos={"engagement": 0.04})
        aplicar_evento(evento, self.arbol, self.recursos, self.mundo, self.rng)
        self.assertAlmostEqual(self.recursos.engagement, 34)

    def test_los_recursos_respetan_sus_limites(self):
        evento = Evento("e", "E", "x", NEGATIVO, efectos={"bienestar": -500})
        aplicar_evento(evento, self.arbol, self.recursos, self.mundo, self.rng)
        self.assertEqual(self.recursos.bienestar, 0)

    def test_un_nodo_mitigador_reduce_a_la_mitad_solo_las_perdidas(self):
        evento = Evento("e", "E", "x", NEGATIVO, efectos={"reputacion": -12, "dinero": -800, "usuarios": 100},
                        mitigadores=("seguridad_basica",))
        sin = aplicar_evento(evento, self.arbol, Recursos(), self.mundo, self.rng)
        self.assertFalse(sin.mitigado)
        self.assertEqual(sin.efectos["reputacion"], -12)

        desbloquear(self.arbol, self.recursos, "seguridad_basica")
        con = aplicar_evento(evento, self.arbol, self.recursos, self.mundo, self.rng)
        self.assertTrue(con.mitigado)
        self.assertEqual(con.efectos, {"reputacion": -6, "dinero": -400, "usuarios": 100})

    def test_cualquiera_de_los_mitigadores_alcanza(self):
        evento = Evento("e", "E", "x", NEGATIVO, efectos={"bienestar": -8},
                        mitigadores=("comunidad_verificacion", "seguridad_avanzada"))
        desbloquear(self.arbol, self.recursos, "seguridad_basica", "seguridad_avanzada")
        self.assertTrue(aplicar_evento(evento, self.arbol, self.recursos, self.mundo, self.rng).mitigado)

    def test_un_mitigador_no_cuenta_si_el_evento_no_tiene_perdidas(self):
        evento = Evento("e", "E", "x", POSITIVO, efectos={"usuarios": 100}, mitigadores=("seguridad_basica",))
        desbloquear(self.arbol, self.recursos, "seguridad_basica")
        self.assertFalse(aplicar_evento(evento, self.arbol, self.recursos, self.mundo, self.rng).mitigado)


class TestPropagacion(unittest.TestCase):
    def setUp(self):
        self.arbol, self.recursos, self.mundo = partida()
        self.rng = RngFijo()
        self.rumor = next(e for e in CATALOGO if e.id == "desinformacion")  # -3 reputación por región, 3 saltos

    def test_con_una_sola_region_solo_se_afecta_esa(self):
        resultado = aplicar_evento(self.rumor, self.arbol, self.recursos, self.mundo, self.rng)
        self.assertEqual(resultado.origen, "sudamerica")
        self.assertEqual(resultado.regiones, ["sudamerica"])
        self.assertEqual(resultado.efectos["reputacion"], -3)

    def test_se_propaga_por_las_regiones_conquistadas_conectadas(self):
        conquistar(self.mundo, "centroamerica", "norteamerica")
        resultado = aplicar_evento(self.rumor, self.arbol, self.recursos, self.mundo, self.rng)
        self.assertEqual(resultado.regiones, ["sudamerica", "centroamerica", "norteamerica"])
        self.assertEqual(resultado.efectos["reputacion"], -9)

    def test_no_pasa_por_regiones_sin_conquistar(self):
        conquistar(self.mundo, "norteamerica")  # no está conectada a Sudamérica por regiones tuyas
        resultado = aplicar_evento(self.rumor, self.arbol, self.recursos, self.mundo, self.rng)
        self.assertEqual(resultado.regiones, ["sudamerica"])

    def test_el_alcance_se_limita_por_saltos(self):
        # Cadena Sudamérica - Centroamérica - Norteamérica - Europa - Asia (sin África):
        # Asia queda a 4 saltos por regiones conquistadas y el rumor llega solo hasta 3.
        conquistar(self.mundo, "centroamerica", "norteamerica", "europa", "asia")
        resultado = aplicar_evento(self.rumor, self.arbol, self.recursos, self.mundo, self.rng)
        self.assertEqual(resultado.regiones, ["sudamerica", "centroamerica", "norteamerica", "europa"])
        self.assertNotIn("asia", resultado.regiones)

    def test_la_seguridad_contiene_la_propagacion(self):
        conquistar(self.mundo, "centroamerica", "norteamerica", "europa")
        sin = aplicar_evento(self.rumor, self.arbol, Recursos(), self.mundo, self.rng)
        self.assertFalse(sin.contenido)
        self.assertEqual(len(sin.regiones), 4)

        desbloquear(self.arbol, self.recursos, "seguridad_basica")   # -1 salto
        basica = aplicar_evento(self.rumor, self.arbol, self.recursos, self.mundo, self.rng)
        self.assertTrue(basica.contenido)
        self.assertEqual(basica.regiones, ["sudamerica", "centroamerica", "norteamerica"])

        desbloquear(self.arbol, self.recursos, "seguridad_avanzada")  # -2 saltos más
        avanzada = aplicar_evento(self.rumor, self.arbol, self.recursos, self.mundo, self.rng)
        self.assertEqual(avanzada.regiones, ["sudamerica"])

    def test_un_evento_positivo_tambien_se_propaga_y_suma_por_region(self):
        viral = next(e for e in CATALOGO if e.id == "publicacion_viral")
        conquistar(self.mundo, "centroamerica")
        usuarios = self.recursos.usuarios
        resultado = aplicar_evento(viral, self.arbol, self.recursos, self.mundo, self.rng)
        self.assertEqual(len(resultado.regiones), 2)
        self.assertEqual(self.recursos.usuarios, usuarios + 240)

    def test_el_origen_se_elige_entre_las_regiones_conquistadas(self):
        conquistar(self.mundo, "centroamerica", "africa")
        origenes = set()
        gestor = GestorEventos(catalogo=[self.rumor], rng=random.Random(5))
        for _ in range(60):
            origenes.add(gestor.disparar(self.arbol, Recursos(), self.mundo).origen)
        self.assertEqual(origenes, {"sudamerica", "centroamerica", "africa"})


if __name__ == "__main__":
    unittest.main()
