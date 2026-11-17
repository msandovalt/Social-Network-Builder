"""
Gestor de eventos aleatorios: en intervalos impredecibles elige un evento y lo
aplica. La probabilidad depende del bienestar y de las afinidades de cada
evento con la reputación, el engagement, los usuarios y las regiones.

Al igual que las rondas, el tiempo solo corre en las pantallas de juego
(no en el menú, la pausa ni el fin de partida).

El generador aleatorio (`rng`) se puede inyectar para que las pruebas sean
reproducibles.
"""

import random

from eventos.evento import CATALOGO, ResultadoEvento, NEGATIVO, POSITIVO
from tree.recursos import efectos_en_puntos

INTERVALO_MIN = 20.0     # Mínimo de segundos entre eventos
INTERVALO_MAX = 40.0     # Máximo de segundos entre eventos
INTERVALO_EVENTOS = 30.0  # Promedio de referencia / compatibilidad


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
    def __init__(self, intervalo=None, intervalo_min=INTERVALO_MIN,
                 intervalo_max=INTERVALO_MAX, catalogo=None, rng=None):
        self.rng = rng if rng is not None else random.Random()
        self.catalogo = tuple(catalogo) if catalogo is not None else CATALOGO
        self.intervalo_min = float(intervalo_min)
        self.intervalo_max = float(intervalo_max)
        if intervalo is not None:
            if isinstance(intervalo, (tuple, list)):
                self.intervalo_min = float(intervalo[0])
                self.intervalo_max = float(intervalo[1])
                self.intervalo = self._nuevo_intervalo()
            else:
                self.intervalo_min = self.intervalo_max = float(intervalo)
                self.intervalo = float(intervalo)
        else:
            self.intervalo = self._nuevo_intervalo()
        self.acumulado = 0.0
        self.historial = []

    def _nuevo_intervalo(self):
        """Genera un nuevo intervalo aleatorio entre intervalo_min e intervalo_max."""
        if self.intervalo_min >= self.intervalo_max:
            return self.intervalo_min
        return round(self.rng.uniform(self.intervalo_min, self.intervalo_max), 1)

    @property
    def ultimo(self):
        return self.historial[-1] if self.historial else None

    def segundos_restantes(self):
        return max(0.0, self.intervalo - self.acumulado)

    def elegir_evento(self, arbol, bienestar=None, metricas=None):
        """Evento al azar entre los que pueden ocurrir ahora. Evita repetir el
        anterior si hay otra opción.

        Si se indica `bienestar` (0 a 100), pondera las probabilidades:
        - Bienestar alto: los eventos positivos son mucho más probables.
        - Bienestar bajo: los eventos negativos (ciberacoso, desinformación,
          filtraciones) son mucho más probables.
        - Bienestar neutro (~50): probabilidades equilibradas.
        """
        elegibles = [e for e in self.catalogo if e.es_elegible(arbol)]
        if not elegibles:
            return None
        if len(elegibles) > 1 and self.ultimo is not None:
            elegibles = [e for e in elegibles if e.id != self.ultimo.evento.id]

        if bienestar is None:
            return self.rng.choice(elegibles)

        # El bienestar inclina el balance general entre eventos positivos y
        # negativos. Las afinidades agregan contexto propio de cada evento.
        b = max(0.0, min(100.0, float(bienestar)))
        pesos = []
        for e in elegibles:
            if getattr(e, "tono", None) == NEGATIVO:
                # Más probable cuanto menor sea el bienestar
                peso = (100.0 - b) + 10.0
            else:
                # Más probable cuanto mayor sea el bienestar
                peso = b + 10.0
            for metrica, direccion in getattr(e, "afinidades", {}).items():
                valor = max(0.0, min(1.0, float((metricas or {}).get(metrica, 0.5))))
                # Cada afinidad multiplica el peso entre 0.5x y 1.5x.
                peso *= 0.5 + valor if direccion > 0 else 1.5 - valor
            pesos.append(peso)

        return self.rng.choices(elegibles, weights=pesos, k=1)[0]

    def disparar(self, arbol, recursos, mundo, evento=None, metricas=None):
        """Aplica un evento ya (el indicado, o uno al azar ponderado por bienestar)."""
        bienestar = getattr(recursos, "bienestar", None) if recursos is not None else None
        evento = evento or self.elegir_evento(
            arbol, bienestar=bienestar, metricas=metricas,
        )
        if evento is None:
            return None
        resultado = aplicar_evento(evento, arbol, recursos, mundo, self.rng)
        self.historial.append(resultado)
        return resultado

    def actualizar(self, dt, arbol, recursos, mundo):
        """Suma tiempo; al completar el intervalo dispara un evento y lo devuelve.
        Al dispararse, calcula un nuevo intervalo aleatorio para el próximo evento."""
        self.acumulado += dt
        if self.acumulado < self.intervalo:
            return None
        sobrante = self.acumulado % self.intervalo
        limite_usuarios = max(1, getattr(recursos, "limite_usuarios", 1))
        total_regiones = max(1, len(getattr(mundo, "regiones", {})))
        conquistadas = len(mundo.conquistadas()) if mundo is not None else 0
        metricas = {
            "bienestar": max(0.0, min(1.0, recursos.bienestar / 100)),
            "reputacion": max(0.0, min(1.0, recursos.reputacion / 100)),
            "engagement": max(0.0, min(1.0, recursos.engagement / 100)),
            "usuarios": max(0.0, min(1.0, recursos.usuarios / limite_usuarios)),
            "regiones": max(0.0, min(1.0, conquistadas / total_regiones)),
        }
        resultado = self.disparar(arbol, recursos, mundo, metricas=metricas)
        self.intervalo = self._nuevo_intervalo()
        self.acumulado = min(sobrante, max(0.0, self.intervalo - 0.001))
        return resultado
