"""
Tragamonedas: el minijuego de habilidad que genera dinero, usuarios o
reputación. Ver el documento de diseño para la justificación completa.

Regla de oro: el bienestar NUNCA toca la probabilidad de fondo. Lo único
que cambia con el bienestar es la velocidad de giro (más bajo = más rápido
= más difícil de ejecutar bien el timing), nunca las probabilidades.
"""

SIMBOLOS = ("dinero", "usuarios", "reputacion")

COLORES = {
    "dinero": (60, 150, 90),
    "usuarios": (60, 110, 190),
    "reputacion": (170, 120, 200),
}

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


class Tragamonedas:
    def __init__(self):
        self.estado = INACTIVO
        self.indices = [0, 0, 0]
        self.girando = [False, False, False]
        self.tiempos = [0.0, 0.0, 0.0]
        self.intervalo = 0.30
        self.mensaje_resultado = ""

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
        self.tiempos = [0.0, 0.0, 0.0]
        self.girando = [True, True, True]
        self.intervalo = self._calcular_intervalo(recursos.bienestar)
        self.mensaje_resultado = ""
        self.estado = GIRANDO
        return True

    def _calcular_intervalo(self, bienestar):
        """Bienestar 100 -> 0.45s por símbolo (lento, cómodo).
        Bienestar 0 -> 0.15s por símbolo (rápido, estresante).
        Cambia la dificultad de ejecución, no la probabilidad."""
        bienestar = max(0, min(100, bienestar))
        return 0.15 + (bienestar / 100) * 0.30

    def actualizar(self, dt):
        if self.estado != GIRANDO:
            return
        for i in range(3):
            if not self.girando[i]:
                continue
            self.tiempos[i] += dt
            if self.tiempos[i] >= self.intervalo:
                self.tiempos[i] = 0.0
                self.indices[i] = (self.indices[i] + 1) % len(SIMBOLOS)

    def detener(self, indice):
        if self.estado != GIRANDO or not self.girando[indice]:
            return
        self.girando[indice] = False
        if not any(self.girando):
            self.estado = POR_RESOLVER

    def resolver(self, recursos):
        if self.estado != POR_RESOLVER:
            return
        resultado = [SIMBOLOS[i] for i in self.indices]
        if resultado[0] == resultado[1] == resultado[2]:
            tipo = resultado[0]
            recursos.aplicar_efectos(RECOMPENSAS[tipo])
            self.mensaje_resultado = f"¡Alineaste {tipo}! Ganaste la recompensa."
        else:
            self.mensaje_resultado = "No alinearon. Sin recompensa esta vez."
        self.estado = RESUELTO

    def reiniciar(self):
        self.estado = INACTIVO
        self.mensaje_resultado = ""
