"""
Sistema de rondas: cada cierto tiempo el juego avanza una ronda, aplica los
efectos por ronda del árbol (interruptores encendidos, diales, bifurcaciones
elegidas) y revisa las condiciones de derrota.

Decisiones de unidades (provisionales, se calibran jugando):
- "crecimiento" no se suma a los recursos: es una tasa. Cada ronda los
  usuarios crecen en `usuarios * (crecimiento pasivo + crecimiento de nodos)`.
- "engagement" en los nodos está expresado como fracción (0.08); se traduce
  a puntos de la escala 0-100 (0.08 -> +8) al aplicarlo.
- El resto (dinero, usuarios, bienestar, reputacion) se suma tal cual.
- Los usuarios nunca superan la capacidad de tus regiones conquistadas (ver
  mapa/mundo.py): sin expandirte, tu red deja de crecer.
- Con el bienestar por debajo de UMBRAL_FUGA, cada ronda se van usuarios: la
  fuga crece mientras más bajo esté (hasta FUGA_MAXIMA con bienestar 0). Así
  descuidar a tu comunidad tiene un costo real y no solo un número que baja.
"""

from tree.recursos import efectos_en_puntos

DURACION_RONDA = 10.0  # segundos reales por ronda

UMBRAL_FUGA = 40      # con menos bienestar que esto, los usuarios empiezan a irse
FUGA_MAXIMA = 0.12    # fracción de usuarios que se va por ronda con bienestar 0

QUIEBRA = "quiebra"
EXODO = "exodo"
SATURACION = "saturacion"
VICTORIA = "victoria"  # conquistaste todo el planeta


def tasa_fuga(bienestar):
    """Fracción de usuarios que abandona la red en una ronda según el bienestar.
    0 desde UMBRAL_FUGA hacia arriba; crece linealmente hasta FUGA_MAXIMA."""
    if bienestar >= UMBRAL_FUGA:
        return 0.0
    return FUGA_MAXIMA * (UMBRAL_FUGA - bienestar) / UMBRAL_FUGA


def avanzar_ronda(arbol, recursos, mundo=None):
    """Aplica una ronda completa. Devuelve QUIEBRA, EXODO o None.
    Si hay `mundo`, se suman también los ingresos de sus regiones conquistadas."""
    if mundo is not None:
        recursos.actualizar_limite_usuarios(mundo.capacidad_total())
    efectos = dict(arbol.efectos_totales_de_la_ronda())
    if mundo is not None:
        for clave, valor in mundo.efectos_totales_de_la_ronda().items():
            efectos[clave] = efectos.get(clave, 0) + valor

    tasa = recursos.crecimiento + efectos.pop("crecimiento", 0.0)
    nuevos_usuarios = recursos.usuarios * (tasa - tasa_fuga(recursos.bienestar))

    efectos["usuarios"] = efectos.get("usuarios", 0) + nuevos_usuarios
    recursos.aplicar_efectos(efectos_en_puntos(efectos))

    if recursos.esta_en_quiebra():
        return QUIEBRA
    if recursos.sufre_exodo():
        return EXODO
    return None


class Rondas:
    """Lleva la cuenta del tiempo, del número de ronda y del historial de métricas."""

    def __init__(self, duracion=DURACION_RONDA):
        self.duracion = duracion
        self.numero = 1
        self.acumulado = 0.0
        self.resultado = None  # None mientras la partida sigue; QUIEBRA, EXODO, SATURACION o VICTORIA
        self.historial = []    # list[dict] con métricas por ronda (ronda, usuarios, bienestar, reputacion, dinero)

    @property
    def terminada(self):
        return self.resultado is not None

    def registrar_muestra(self, recursos, numero_ronda=None):
        """Guarda una instantánea de las métricas actuales para el gráfico post-mortem."""
        r = self.numero if numero_ronda is None else numero_ronda
        muestra = {
            "ronda": r,
            "usuarios": recursos.usuarios,
            "bienestar": recursos.bienestar,
            "reputacion": recursos.reputacion,
            "dinero": recursos.dinero,
        }
        if self.historial and self.historial[-1]["ronda"] == r:
            self.historial[-1] = muestra
        else:
            self.historial.append(muestra)

    def finalizar(self, resultado):
        """Termina la partida con `resultado` (por ejemplo VICTORIA). Si ya
        había terminado, no cambia el resultado original."""
        if not self.terminada:
            self.resultado = resultado

    def segundos_restantes(self):
        return max(0.0, self.duracion - self.acumulado)

    def actualizar(self, dt, arbol, recursos, mundo=None):
        """Suma tiempo; si se completó una ronda la aplica.
        Devuelve True si en esta llamada se jugó una ronda."""
        if self.terminada:
            return False
        if not self.historial:
            self.registrar_muestra(recursos, 0)
        self.acumulado += dt
        if self.acumulado < self.duracion:
            return False
        self.acumulado -= self.duracion
        self.resultado = avanzar_ronda(arbol, recursos, mundo)
        self.registrar_muestra(recursos, self.numero)
        self.numero += 1
        return True

