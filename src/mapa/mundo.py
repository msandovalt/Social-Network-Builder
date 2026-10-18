"""
El planeta: un grafo de regiones a las que tu red social puede expandirse.

Reglas de expansión (todas deben cumplirse):
1. La región debe ser VECINA de una que ya conquistaste (está a un salto, BFS).
2. Debes tener desbloqueados los nodos del árbol que la región exige: así lo
   que construyes en el árbol decide hasta dónde puedes llegar.
3. Debes alcanzar los usuarios, la reputación y el bienestar mínimos: una red
   que maltrata a sus usuarios no se recomienda y no puede crecer a otro lado.
4. Debes pagar la ruta: el costo es el de la arista más barata que te conecta
   con la región.

Dijkstra se usa para planear: dice cuál es la ruta más barata hacia una región
lejana (qué regiones conquistar en el camino y cuánto costará en total).

Cada región conquistada aporta su `ingreso` en cada ronda y su `capacidad`:
el máximo de usuarios que tu red puede tener es la suma de la capacidad de tus
regiones. Para seguir creciendo tienes que expandirte.

Los valores de requisitos, costos e ingresos son provisionales: se calibran
jugando.
"""

import math
from collections import namedtuple

from mapa.grafo import Grafo

CONQUISTADA = "conquistada"
DISPONIBLE = "disponible"   # vecina y con todos los requisitos cumplidos
BLOQUEADA = "bloqueada"     # vecina, pero todavía faltan requisitos
LEJANA = "lejana"           # no es vecina de ninguna región tuya

# tipo: "vecina" | "nodo" | "usuarios" | "reputacion" | "bienestar" | "dinero"
# etiqueta: nombre del nodo del árbol (solo para tipo "nodo")
Requisito = namedtuple("Requisito", "tipo etiqueta necesario actual cumplido")


# Bienestar mínimo para expandirte a cada región (se ajusta jugando)
BIEN_NORTE, BIEN_AFRICA, BIEN_EUROPA, BIEN_MEDIO, BIEN_ASIA, BIEN_OCEANIA = 40, 40, 50, 45, 50, 55


# Capacidad de usuarios que aporta cada región (se ajusta jugando)
CAP_SUDAMERICA, CAP_CENTROAMERICA, CAP_NORTEAMERICA, CAP_AFRICA = 1500, 1000, 4000, 3000
CAP_EUROPA, CAP_MEDIO, CAP_ASIA, CAP_OCEANIA = 3500, 2000, 8000, 1000


class Region:
    def __init__(self, id_region, nombre, descripcion, ingreso,
                 nodos=(), usuarios=0, reputacion=0, bienestar=0, capacidad=0):
        self.id = id_region
        self.nombre = nombre
        self.descripcion = descripcion
        self.ingreso = ingreso          # efectos por ronda mientras esté conquistada
        self.capacidad = capacidad      # usuarios máximos que aporta al estar conquistada
        self.nodos = tuple(nodos)       # ids de nodos del árbol que exige
        self.usuarios = usuarios        # usuarios mínimos
        self.reputacion = reputacion    # reputación mínima
        self.bienestar = bienestar      # bienestar mínimo
        self.conquistada = False


class Mundo:
    def __init__(self):
        self.grafo = Grafo()
        self.regiones = {}

    def agregar_region(self, region):
        self.regiones[region.id] = region
        self.grafo.agregar_nodo(region.id)

    def conectar(self, a, b, costo):
        self.grafo.agregar_arista(a, b, costo)

    # --- consulta -----------------------------------------------------------------
    def conquistadas(self):
        return [id_region for id_region, region in self.regiones.items() if region.conquistada]

    def saltos(self):
        """Saltos (BFS) desde tus regiones hasta cada una: {id: saltos}."""
        return self.grafo.bfs_niveles(self.conquistadas())

    def frontera(self):
        """Regiones sin conquistar que son vecinas de alguna conquistada."""
        return [id_region for id_region, saltos in self.saltos().items() if saltos == 1]

    def capacidad_total(self):
        """Tope de usuarios de tu red: suma de la capacidad de las regiones conquistadas."""
        return sum(region.capacidad for region in self.regiones.values() if region.conquistada)

    def todas_conquistadas(self):
        """Condición de victoria: el planeta entero es tuyo."""
        return all(region.conquistada for region in self.regiones.values())

    def regiones_alcanzadas(self, origen, saltos):
        """Regiones por las que se propaga algo que nace en `origen` y avanza
        hasta `saltos` saltos, pasando SOLO por regiones conquistadas (BFS
        limitado). Devuelve ids en orden de alcance; el origen va primero."""
        niveles = self.grafo.bfs_niveles(
            [origen],
            permitido=lambda id_region: self.regiones[id_region].conquistada,
            max_saltos=saltos,
        )
        return sorted(niveles, key=niveles.get)

    def costo_expansion(self, id_region):
        """Costo de expandirte a una región vecina: la arista más barata desde
        una región tuya. None si ya es tuya o no es vecina."""
        if self.regiones[id_region].conquistada:
            return None
        costos = [peso for vecino, peso in self.grafo.vecinos(id_region).items()
                  if self.regiones[vecino].conquistada]
        return min(costos) if costos else None

    def ruta_mas_barata(self, id_region):
        """(costo total, [ids]) del camino más barato (Dijkstra) desde tus
        regiones hasta `id_region`; el camino empieza en la región tuya."""
        return self.grafo.camino_minimo(self.conquistadas(), id_region)

    def requisitos(self, id_region, arbol, recursos):
        """Lista de Requisito con su estado actual (vacía si ya es tuya)."""
        region = self.regiones[id_region]
        if region.conquistada:
            return []
        costo = self.costo_expansion(id_region)
        vecina = costo is not None

        lista = [Requisito("vecina", "", 1, 1 if vecina else 0, vecina)]
        for id_nodo in region.nodos:
            nodo = arbol.nodo_por_id(id_nodo)
            lista.append(Requisito("nodo", nodo.nombre, 1, 1 if nodo.desbloqueado else 0,
                                   nodo.desbloqueado))
        if region.usuarios:
            lista.append(Requisito("usuarios", "", region.usuarios, recursos.usuarios,
                                   recursos.usuarios >= region.usuarios))
        if region.reputacion:
            lista.append(Requisito("reputacion", "", region.reputacion, recursos.reputacion,
                                   recursos.reputacion >= region.reputacion))
        if region.bienestar:
            lista.append(Requisito("bienestar", "", region.bienestar, recursos.bienestar,
                                   recursos.bienestar >= region.bienestar))
        if vecina:
            lista.append(Requisito("dinero", "", costo, recursos.dinero, recursos.dinero >= costo))
        return lista

    def estado_region(self, id_region, arbol, recursos):
        if self.regiones[id_region].conquistada:
            return CONQUISTADA
        if self.costo_expansion(id_region) is None:
            return LEJANA
        if all(r.cumplido for r in self.requisitos(id_region, arbol, recursos)):
            return DISPONIBLE
        return BLOQUEADA

    def puede_expandirse(self, id_region, arbol, recursos):
        return self.estado_region(id_region, arbol, recursos) == DISPONIBLE

    # --- acciones -----------------------------------------------------------------
    def expandir(self, id_region, arbol, recursos):
        """Conquista la región y cobra la ruta. False (sin cambios) si no cumple."""
        if not self.puede_expandirse(id_region, arbol, recursos):
            return False
        costo = self.costo_expansion(id_region)
        recursos.aplicar_efectos({"dinero": -costo})
        self.regiones[id_region].conquistada = True
        recursos.actualizar_limite_usuarios(self.capacidad_total())
        return True

    def efectos_totales_de_la_ronda(self):
        """Suma del ingreso por ronda de todas las regiones conquistadas."""
        totales = {}
        for region in self.regiones.values():
            if region.conquistada:
                for clave, valor in region.ingreso.items():
                    totales[clave] = totales.get(clave, 0) + valor
        return totales

    # --- planeta inicial ------------------------------------------------------------
    @staticmethod
    def construir_mundo_inicial():
        mundo = Mundo()
        regiones = (
            Region("sudamerica", "Sudamérica",
                   "Tu punto de partida. Comunidad joven y muy conectada.",
                   {"usuarios": 25, "dinero": 120}, capacidad=CAP_SUDAMERICA),
            Region("centroamerica", "Centroamérica",
                   "Puente entre dos continentes. Un feed básico basta para empezar.",
                   {"usuarios": 30, "dinero": 100},
                   nodos=("feed_basico",), usuarios=600, capacidad=CAP_CENTROAMERICA),
            Region("norteamerica", "Norteamérica",
                   "Mercado grande y rico, pero exige comunidades activas y buena reputación.",
                   {"usuarios": 45, "dinero": 450},
                   nodos=("comunidad_grupos",), usuarios=1200, reputacion=50, bienestar=BIEN_NORTE, capacidad=CAP_NORTEAMERICA),
            Region("africa", "África",
                   "Población joven en pleno crecimiento. Necesitas seguridad básica para operar.",
                   {"usuarios": 90, "dinero": 60},
                   nodos=("seguridad_basica",), usuarios=1000, bienestar=BIEN_AFRICA, capacidad=CAP_AFRICA),
            Region("europa", "Europa",
                   "Leyes estrictas de privacidad: sin seguridad avanzada no puedes entrar.",
                   {"usuarios": 50, "dinero": 350, "reputacion": 0.5},
                   nodos=("seguridad_avanzada",), usuarios=1500, reputacion=60, bienestar=BIEN_EUROPA, capacidad=CAP_EUROPA),
            Region("medio_oriente", "Medio Oriente",
                   "Encrucijada entre tres continentes. La confianza entre usuarios es clave.",
                   {"usuarios": 70, "dinero": 300},
                   nodos=("comunidad_verificacion",), usuarios=2000, bienestar=BIEN_MEDIO, capacidad=CAP_MEDIO),
            Region("asia", "Asia",
                   "El mayor mercado del planeta. Exige un feed inteligente y cuentas verificadas.",
                   {"usuarios": 160, "dinero": 250},
                   nodos=("feed_algoritmo", "comunidad_verificacion"), usuarios=3000, bienestar=BIEN_ASIA, capacidad=CAP_ASIA),
            Region("oceania", "Oceanía",
                   "Islas lejanas y exigentes: comunidades sólidas y una reputación impecable.",
                   {"usuarios": 60, "dinero": 280},
                   nodos=("seguridad_basica", "comunidad_grupos"), usuarios=2500, reputacion=65, bienestar=BIEN_OCEANIA, capacidad=CAP_OCEANIA),
        )
        for region in regiones:
            mundo.agregar_region(region)

        # Rutas entre regiones y su costo de expansión (en dinero)
        rutas = (
            ("sudamerica", "centroamerica", 1500),
            ("centroamerica", "norteamerica", 1500),
            ("norteamerica", "europa", 3000),
            ("sudamerica", "africa", 4500),
            ("europa", "africa", 2000),
            ("europa", "medio_oriente", 2500),
            ("africa", "medio_oriente", 2500),
            ("medio_oriente", "asia", 2000),
            ("europa", "asia", 4000),
            ("asia", "oceania", 3000),
        )
        for a, b, costo in rutas:
            mundo.conectar(a, b, costo)

        mundo.regiones["sudamerica"].conquistada = True
        return mundo
