"""
Tragamonedas: el minijuego de habilidad que genera dinero, usuarios o
reputación. Ver el documento de diseño para la justificación completa.

Regla de oro: el bienestar NUNCA toca la probabilidad de fondo. Lo único
que cambia con el bienestar es la velocidad de giro (más bajo = más rápido
= más difícil de ejecutar bien el timing), nunca las probabilidades.

Cada carrete tiene una posición continua (`posiciones`, en unidades de
símbolo) para poder animar el giro de forma fluida. El resultado sigue
siendo el de siempre: al detener un carrete queda el símbolo que estaba más
cerca del centro en ese instante, y el carrete frena suavemente hasta
alinearse con él (`DURACION_ASENTADO`).
"""

SIMBOLOS = ("dinero", "usuarios", "reputacion")

ETIQUETAS = {
    "dinero": "$",
    "usuarios": "U",
    "reputacion": "R",
}

RECOMPENSAS = {
    "dinero": {"dinero": 3000},
    "usuarios": {"usuarios": 1500},
    "reputacion": {"reputacion": 6},
}

INACTIVO = "inactivo"
GIRANDO = "girando"
POR_RESOLVER = "por_resolver"
RESUELTO = "resuelto"

DURACION_ASENTADO = 0.35  # segundos que tarda un carrete en frenar y alinearse


def _ease_out_cubic(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


class Tragamonedas:
    def __init__(self):
        self.estado = INACTIVO
        self.indices = [0, 0, 0]            # símbolo más cercano al centro de cada carrete
        self.posiciones = [0.0, 0.0, 0.0]   # posición continua, en símbolos (0 <= p < 3)
        self.girando = [False, False, False]
        self._asentado = [None, None, None]  # (desde, hasta, tiempo) mientras un carrete frena
        self.intervalo = 0.30                # segundos por símbolo
        self.mensaje_resultado = ""
        self.resultado_tipo = None           # símbolo ganador, o None si no alinearon
        self.tiempo_resultado = 0.0          # segundos desde que se resolvió (para animar)

    def costo(self, recursos):
        """Costo proporcional al dinero actual, con un piso mínimo.
        Mismo principio de escalado que las multas del sistema de
        'no derrota': barato al inicio, caro cuando ya eres grande."""
        return max(200, round(0.05 * recursos.dinero))

    def puede_jugar(self, recursos):
        return self.estado == INACTIVO and recursos.dinero >= self.costo(recursos)

    def iniciar(self, recursos):
        if not self.puede_jugar(recursos):
            return False
        recursos.dinero -= self.costo(recursos)
        self.indices = [0, 0, 0]
        self.posiciones = [0.0, 0.0, 0.0]
        self._asentado = [None, None, None]
        self.girando = [True, True, True]
        self.intervalo = self._calcular_intervalo(recursos.bienestar)
        self.mensaje_resultado = ""
        self.resultado_tipo = None
        self.tiempo_resultado = 0.0
        self.estado = GIRANDO
        return True

    def _calcular_intervalo(self, bienestar):
        """Bienestar 100 -> 0.45s por símbolo (lento, cómodo).
        Bienestar 0 -> 0.15s por símbolo (rápido, estresante).
        Cambia la dificultad de ejecución, no la probabilidad."""
        bienestar = max(0, min(100, bienestar))
        return 0.15 + (bienestar / 100) * 0.30

    def actualizar(self, dt):
        n = len(SIMBOLOS)

        if self.estado == GIRANDO:
            for i in range(3):
                if self.girando[i]:
                    self.posiciones[i] = (self.posiciones[i] + dt / self.intervalo) % n
                    self.indices[i] = int(round(self.posiciones[i])) % n

        # Los carretes ya detenidos siguen frenando aunque el estado ya sea POR_RESOLVER
        for i in range(3):
            ajuste = self._asentado[i]
            if ajuste is None:
                continue
            desde, hasta, tiempo = ajuste
            tiempo += dt
            if tiempo >= DURACION_ASENTADO:
                self.posiciones[i] = float(hasta % n)
                self._asentado[i] = None
            else:
                avance = _ease_out_cubic(tiempo / DURACION_ASENTADO)
                self.posiciones[i] = (desde + (hasta - desde) * avance) % n
                self._asentado[i] = (desde, hasta, tiempo)

        if self.estado == RESUELTO:
            self.tiempo_resultado += dt

    def detener(self, indice):
        if self.estado != GIRANDO or not self.girando[indice]:
            return
        self.girando[indice] = False
        hasta = int(round(self.posiciones[indice]))
        self.indices[indice] = hasta % len(SIMBOLOS)
        self._asentado[indice] = (self.posiciones[indice], float(hasta), 0.0)
        if not any(self.girando):
            self.estado = POR_RESOLVER

    def asentada(self):
        """True cuando ningún carrete sigue frenando (ya se puede resolver)."""
        return all(ajuste is None for ajuste in self._asentado)

    def resolver(self, recursos):
        if self.estado != POR_RESOLVER:
            return
        resultado = [SIMBOLOS[i] for i in self.indices]
        if resultado[0] == resultado[1] == resultado[2]:
            tipo = resultado[0]
            recursos.aplicar_efectos(RECOMPENSAS[tipo])
            self.resultado_tipo = tipo
            self.mensaje_resultado = f"¡Alineaste {tipo}! Ganaste la recompensa."
        else:
            self.resultado_tipo = None
            self.mensaje_resultado = "No alinearon. Sin recompensa esta vez."
        self.tiempo_resultado = 0.0
        self.estado = RESUELTO

    def reiniciar(self):
        self.estado = INACTIVO
        self.mensaje_resultado = ""
        self.resultado_tipo = None
        self.tiempo_resultado = 0.0
