"""
Árbol de funcionalidades: agrupa los nodos y expone un recorrido (BFS)
para saber qué nodos existen y cuáles están disponibles para
desbloquear en un momento dado.
"""

from collections import deque

from tree.nodo import Nodo


class Arbol:
    def __init__(self, raiz):
        self.raiz = raiz

    def recorrido_bfs(self):
        """Recorre el árbol por niveles (padres antes que hijos).
        Se usa tanto para dibujar la interfaz como para calcular efectos."""
        visitados = []
        cola = deque([self.raiz])
        while cola:
            nodo = cola.popleft()
            visitados.append(nodo)
            cola.extend(nodo.hijos)
        return visitados

    def nodos_disponibles(self, recursos):
        """Nodos que el jugador podría desbloquear ahora mismo."""
        return [n for n in self.recorrido_bfs() if n.puede_desbloquearse(recursos)]

    def efectos_totales_de_la_ronda(self):
        """Suma los efectos por ronda de todos los nodos activos
        (interruptores encendidos, diales, bifurcaciones ya elegidas)."""
        totales = {}
        for nodo in self.recorrido_bfs():
            for clave, valor in nodo.efecto_por_ronda().items():
                totales[clave] = totales.get(clave, 0) + valor
        return totales

    @staticmethod
    def construir_arbol_inicial():
        """Construye el árbol tal como quedó definido en el documento de diseño:
        Red social -> Feed / Comunidad / Seguridad, cada rama con sus nodos
        fijos e interactivos. Los costos y efectos numéricos son un punto de
        partida provisional, se calibran jugando."""
        raiz = Nodo("red_social", "Red social", "fijo", costo=0)

        # --- Feed ---
        feed = Nodo("feed", "Feed", "fijo", costo=0)
        basico = Nodo("feed_basico", "Básico", "fijo", costo=2000,
                       efectos={"crecimiento": 0.02})
        scroll_infinito = Nodo("feed_scroll", "Scroll infinito", "interruptor", costo=3000,
                                efectos={"crecimiento": 0.05, "engagement": 0.08, "bienestar": -4})
        algoritmo = Nodo("feed_algoritmo", "Algoritmo", "dial", costo=5000,
                          efectos={"usuarios": 300, "engagement": 0.1, "bienestar": -6})
        feed.agregar_hijo(basico)
        feed.agregar_hijo(scroll_infinito)
        feed.agregar_hijo(algoritmo)

        # --- Comunidad ---
        comunidad = Nodo("comunidad", "Comunidad", "fijo", costo=0)
        grupos = Nodo("comunidad_grupos", "Grupos", "fijo", costo=3000,
                       efectos={"bienestar": 2})
        mensajes = Nodo("comunidad_mensajes", "Mensajes", "bifurcacion", costo=4000, variantes={
            "cifrado": {"efectos": {"reputacion": 5, "bienestar": 3, "crecimiento": -0.01}},
            "abierta": {"efectos": {"crecimiento": 0.03, "bienestar": -2}},
        })
        verificacion_paga = Nodo("comunidad_verificacion", "Verificación paga", "interruptor", costo=4000,
                                  efectos={"dinero": 500, "bienestar": -3, "reputacion": -2})
        comunidad.agregar_hijo(grupos)
        comunidad.agregar_hijo(mensajes)
        comunidad.agregar_hijo(verificacion_paga)

        # --- Seguridad ---
        seguridad = Nodo("seguridad", "Seguridad", "fijo", costo=0)
        basica = Nodo("seguridad_basica", "Básica", "fijo", costo=2500,
                       efectos={"reputacion": 3, "bienestar": 2})
        avanzada = Nodo("seguridad_avanzada", "Avanzada", "bifurcacion", costo=4500, variantes={
            "humana": {"efectos": {"bienestar": 5, "reputacion": 4, "dinero": -300}},
            "automatica": {"efectos": {"bienestar": 1, "reputacion": 1}},
        })
        seguridad.agregar_hijo(basica)
        seguridad.agregar_hijo(avanzada)

        raiz.agregar_hijo(feed)
        raiz.agregar_hijo(comunidad)
        raiz.agregar_hijo(seguridad)

        return Arbol(raiz)
