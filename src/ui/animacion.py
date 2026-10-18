"""Utilidades de animación sin dependencias de Pygame (fáciles de probar)."""

import math


def _limitar(t):
    return max(0.0, min(1.0, t))


def ease_out_cubic(t):
    """Arranca rápido y frena suave. t en [0, 1]."""
    t = _limitar(t)
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = _limitar(t)
    return t * t * (3 - 2 * t)


def pulso(t, periodo=1.5):
    """Oscila suavemente entre 0 y 1 con el tiempo `t` (en segundos)."""
    return 0.5 + 0.5 * math.sin(2 * math.pi * t / periodo)


class NumeroAnimado:
    """Valor que se acerca suavemente a su objetivo, para que los contadores
    suban y bajen en vez de cambiar de golpe."""

    UMBRAL = 0.5

    def __init__(self, valor=0.0, velocidad=8.0):
        self.valor = float(valor)
        self.objetivo = float(valor)
        self.velocidad = velocidad

    @property
    def direccion(self):
        """1 si está subiendo, -1 si está bajando, 0 si ya llegó."""
        if self.objetivo > self.valor:
            return 1
        if self.objetivo < self.valor:
            return -1
        return 0

    def actualizar(self, dt, objetivo=None):
        if objetivo is not None:
            self.objetivo = float(objetivo)
        diferencia = self.objetivo - self.valor
        if abs(diferencia) < self.UMBRAL:
            self.valor = self.objetivo
        else:
            self.valor += diferencia * min(1.0, dt * self.velocidad)
