"""
Gestor de eventos aleatorios: cada `INTERVALO_EVENTOS` segundos elige un
evento al azar y lo aplica. Al igual que las rondas, el tiempo solo corre en
las pantallas de juego (no en el menú, la pausa ni el fin de partida).

El generador aleatorio (`rng`) se puede inyectar para que las pruebas sean
reproducibles.
"""

import random

from eventos.evento import CATALOGO, ResultadoEvento
from tree.recursos import efectos_en_puntos

INTERVALO_EVENTOS = 30.0  # segundos reales entre eventos


def aplicar_evento(evento, arbol, recursos, mundo, rng):
    """Aplica el evento a los recursos y devuelve su ResultadoEvento."""
    efectos = dict(evento.efectos)
    origen, regiones, contenido = None, [], False

    if evento.se_propaga and mundo.conquistadas():
        origen = rng.choice(mundo.conquistadas())
        reduccion = sum(saltos for id_nodo, saltos in evento.contencion.items()
                        if arbol.nodo_por_id(id_nodo).desbloqueado)
        saltos = max(0, evento.saltos - reduccion)
        contenido = saltos < evento.saltos
        regiones = mundo.regiones_alcanzadas(origen, saltos)
        for clave, valor in evento.por_region.items():
            efectos[clave] = efectos.get(clave, 0) + valor * len(regiones)

    mitigado = False
    if any(arbol.nodo_por_id(id_nodo).desbloqueado for id_nodo in evento.mitigadores):
        perdidas = [clave for clave, valor in efectos.items() if valor < 0]
        if perdidas:
            mitigado = True
            efectos = {clave: (valor / 2 if valor < 0 else valor) for clave, valor in efectos.items()}

    recursos.aplicar_efectos(efectos_en_puntos(efectos))
    return ResultadoEvento(evento, efectos, origen, regiones, mitigado, contenido)


class GestorEventos:
    def __init__(self, intervalo=INTERVALO_EVENTOS, catalogo=None, rng=None):
        self.intervalo = intervalo
        self.catalogo = tuple(catalogo) if catalogo is not None else CATALOGO
        self.rng = rng if rng is not None else random.Random()
        self.acumulado = 0.0
        self.historial = []

    @property
    def ultimo(self):
        return self.historial[-1] if self.historial else None

    def segundos_restantes(self):
        return max(0.0, self.intervalo - self.acumulado)

    def elegir_evento(self, arbol):
        """Evento al azar entre los que pueden ocurrir ahora. Evita repetir el
        anterior si hay otra opción. None si no hay ninguno disponible."""
        elegibles = [e for e in self.catalogo if e.es_elegible(arbol)]
        if len(elegibles) > 1 and self.ultimo is not None:
            elegibles = [e for e in elegibles if e.id != self.ultimo.evento.id]
        return self.rng.choice(elegibles) if elegibles else None

    def disparar(self, arbol, recursos, mundo, evento=None):
        """Aplica un evento ya (el indicado, o uno al azar)."""
        evento = evento or self.elegir_evento(arbol)
        if evento is None:
            return None
        resultado = aplicar_evento(evento, arbol, recursos, mundo, self.rng)
        self.historial.append(resultado)
        return resultado

    def actualizar(self, dt, arbol, recursos, mundo):
        """Suma tiempo; al completar el intervalo dispara un evento y lo devuelve."""
        self.acumulado += dt
        if self.acumulado < self.intervalo:
            return None
        self.acumulado %= self.intervalo
        return self.disparar(arbol, recursos, mundo)
