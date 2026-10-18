"""
Grafo no dirigido y ponderado, con lista de adyacencia.

Se usa para el mapa del planeta (cada región es un nodo y cada ruta entre
regiones es una arista con un costo), pero es genérico: no sabe nada del juego.

Dos recorridos, con propósitos distintos:
- BFS (`bfs`, `bfs_niveles`): cuenta SALTOS, ignora los pesos. Sirve para saber
  qué está a un salto (la frontera) y qué tan lejos queda cada nodo.
- Dijkstra (`dijkstra`, `camino_minimo`): minimiza el COSTO total. El camino
  más barato no siempre es el de menos saltos.

Ambos aceptan varios nodos de origen a la vez ("multi-fuente"): en el juego
los orígenes son todas las regiones que ya conquistaste.
"""

import heapq
import math
from collections import deque


class Grafo:
    def __init__(self):
        self._ady = {}  # nodo -> {vecino: peso}

    # --- construcción -----------------------------------------------------------
    def agregar_nodo(self, nodo):
        self._ady.setdefault(nodo, {})

    def agregar_arista(self, a, b, peso=1):
        """Conecta a y b en ambos sentidos. Los pesos no pueden ser negativos
        (Dijkstra no lo soporta)."""
        if peso < 0:
            raise ValueError("el peso de una arista no puede ser negativo")
        self.agregar_nodo(a)
        self.agregar_nodo(b)
        self._ady[a][b] = peso
        self._ady[b][a] = peso

    # --- consulta -----------------------------------------------------------------
    def nodos(self):
        return list(self._ady)

    def vecinos(self, nodo):
        """Diccionario {vecino: peso}. Es una copia: modificarla no altera el grafo."""
        return dict(self._ady[nodo])

    def peso(self, a, b):
        return self._ady[a][b]

    def aristas(self):
        """Lista de (a, b, peso), cada arista una sola vez."""
        vistas = set()
        resultado = []
        for a, vecinos in self._ady.items():
            for b, peso in vecinos.items():
                if (b, a) not in vistas:
                    vistas.add((a, b))
                    resultado.append((a, b, peso))
        return resultado

    # --- BFS --------------------------------------------------------------------
    def bfs(self, inicio):
        """Orden en que BFS visita los nodos alcanzables desde `inicio`."""
        if inicio not in self._ady:
            raise KeyError(inicio)
        visitados = {inicio}
        orden = []
        cola = deque([inicio])
        while cola:
            actual = cola.popleft()
            orden.append(actual)
            for vecino in self._ady[actual]:
                if vecino not in visitados:
                    visitados.add(vecino)
                    cola.append(vecino)
        return orden

    def bfs_niveles(self, origenes, permitido=None, max_saltos=None):
        """Saltos mínimos desde el conjunto de orígenes: {nodo: saltos}. Los
        orígenes quedan en 0; los nodos inalcanzables no aparecen.

        `permitido(nodo)` (opcional) decide por cuáles nodos se puede pasar, y
        `max_saltos` (opcional) limita la distancia. Con ambos se modela cómo
        algo SE PROPAGA: por ejemplo, un rumor que solo avanza por las regiones
        que ya conquistaste y hasta cierto número de saltos."""
        niveles = {}
        cola = deque()
        for origen in origenes:
            if origen not in self._ady:
                raise KeyError(origen)
            niveles[origen] = 0
            cola.append(origen)
        while cola:
            actual = cola.popleft()
            if max_saltos is not None and niveles[actual] >= max_saltos:
                continue
            for vecino in self._ady[actual]:
                if vecino in niveles:
                    continue
                if permitido is not None and not permitido(vecino):
                    continue
                niveles[vecino] = niveles[actual] + 1
                cola.append(vecino)
        return niveles

    def es_conexo(self):
        """True si desde cualquier nodo se llega a todos los demás."""
        if not self._ady:
            return True
        primero = next(iter(self._ady))
        return len(self.bfs(primero)) == len(self._ady)

    # --- Dijkstra -----------------------------------------------------------------
    def dijkstra(self, origenes):
        """Costo mínimo desde el conjunto de orígenes hasta cada nodo.
        Devuelve (distancias, previos): `previos[n]` es el nodo anterior en el
        camino más barato (None para los orígenes). Nodos inalcanzables: inf."""
        distancias = {nodo: math.inf for nodo in self._ady}
        previos = {nodo: None for nodo in self._ady}
        cola = []
        for origen in origenes:
            if origen not in self._ady:
                raise KeyError(origen)
            distancias[origen] = 0
            heapq.heappush(cola, (0, origen))

        while cola:
            distancia, actual = heapq.heappop(cola)
            if distancia > distancias[actual]:
                continue  # entrada vieja: ya se encontró un camino mejor
            for vecino, peso in self._ady[actual].items():
                nueva = distancia + peso
                if nueva < distancias[vecino]:
                    distancias[vecino] = nueva
                    previos[vecino] = actual
                    heapq.heappush(cola, (nueva, vecino))
        return distancias, previos

    def camino_minimo(self, origenes, destino):
        """(costo, camino) del camino más barato desde el origen más conveniente
        hasta `destino`. El camino empieza en el origen e incluye el destino.
        Si no hay camino: (inf, [])."""
        if destino not in self._ady:
            raise KeyError(destino)
        distancias, previos = self.dijkstra(origenes)
        if distancias[destino] == math.inf:
            return math.inf, []
        camino = []
        nodo = destino
        while nodo is not None:
            camino.append(nodo)
            nodo = previos[nodo]
        camino.reverse()
        return distancias[destino], camino
