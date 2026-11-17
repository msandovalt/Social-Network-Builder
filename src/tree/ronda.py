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

DURACION_RONDA = 25.0  # segundos activos en el panel principal por ronda

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


def balance_por_ronda(arbol, recursos, mundo=None):
    """Calcula el cambio neto en puntos que producirá la próxima ronda para cada
    recurso visible, sin modificar `recursos`."""
    efectos = dict(arbol.efectos_totales_de_la_ronda())
    if mundo is not None:
        for clave, valor in mundo.efectos_totales_de_la_ronda().items():
            efectos[clave] = efectos.get(clave, 0) + valor
        efectos["dinero"] = efectos.get("dinero", 0) - mundo.costo_operativo(recursos.usuarios)

    tasa = recursos.crecimiento + efectos.pop("crecimiento", 0.0)
    usuarios_fijos = efectos.pop("usuarios", 0)
    resultado = efectos_en_puntos(efectos)

    bienestar_proyectado = max(0.0, min(100.0, recursos.bienestar + resultado.get("bienestar", 0.0)))
    apoyo_comunidad = min(1.0, max(0.0, bienestar_proyectado / UMBRAL_FUGA))
    tasa_efectiva = max(0.0, tasa) * apoyo_comunidad + min(0.0, tasa)
    crecimiento = recursos.usuarios * tasa_efectiva
    usuarios_fijos_ef = usuarios_fijos * apoyo_comunidad if usuarios_fijos > 0 else usuarios_fijos
    fuga = recursos.usuarios * tasa_fuga(bienestar_proyectado)
    resultado["usuarios"] = crecimiento + usuarios_fijos_ef - fuga
    return resultado


def avanzar_ronda(arbol, recursos, mundo=None):
    """Aplica una ronda completa. Devuelve QUIEBRA, EXODO o None.
    Si hay `mundo`, se suman también los ingresos de sus regiones conquistadas."""
    if mundo is not None:
        recursos.actualizar_limite_usuarios(mundo.capacidad_total())
    if recursos.esta_en_quiebra():
        return QUIEBRA
    if recursos.sufre_exodo():
        return EXODO

    efectos = dict(arbol.efectos_totales_de_la_ronda())
    if mundo is not None:
        for clave, valor in mundo.efectos_totales_de_la_ronda().items():
            efectos[clave] = efectos.get(clave, 0) + valor
        efectos["dinero"] = efectos.get("dinero", 0) - mundo.costo_operativo(recursos.usuarios)

    tasa = recursos.crecimiento + efectos.pop("crecimiento", 0.0)
    usuarios_fijos = efectos.pop("usuarios", 0)

    # Primero aplica efectos no demográficos para que el bienestar que dejan
    # las decisiones de esta ronda afecte la captación y la fuga de inmediato.
    recursos.aplicar_efectos(efectos_en_puntos(efectos))

    # El bienestar bajo reduce la capacidad de captar usuarios. A cero, tanto
    # las tasas como las bonificaciones recurrentes de usuarios dejan de sumar;
    # la fuga sigue calculándose sobre la comunidad existente.
    apoyo_comunidad = min(1.0, max(0.0, recursos.bienestar / UMBRAL_FUGA))
    tasa_efectiva = max(0.0, tasa) * apoyo_comunidad + min(0.0, tasa)
    crecimiento = recursos.usuarios * tasa_efectiva
    usuarios_fijos = (usuarios_fijos * apoyo_comunidad if usuarios_fijos > 0
                      else usuarios_fijos)
    fuga = recursos.usuarios * tasa_fuga(recursos.bienestar)
    recursos.aplicar_efectos({"usuarios": crecimiento + usuarios_fijos - fuga})

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

