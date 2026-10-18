"""Partículas simples (confeti / destellos) para celebrar premios."""

import math
import random

import pygame


class _Particula:
    __slots__ = ("x", "y", "vx", "vy", "vida", "vida_max", "color", "radio")

    def __init__(self, x, y, vx, vy, vida, color, radio):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.vida = self.vida_max = vida
        self.color = color
        self.radio = radio


class SistemaParticulas:
    GRAVEDAD = 520.0

    def __init__(self):
        self.particulas = []

    @property
    def hay_activas(self):
        return bool(self.particulas)

    def emitir(self, x, y, color, cantidad=24):
        """Lanza una ráfaga de partículas en todas direcciones."""
        for _ in range(cantidad):
            angulo = random.uniform(0, 2 * math.pi)
            velocidad = random.uniform(120, 420)
            self.particulas.append(_Particula(
                x, y,
                math.cos(angulo) * velocidad,
                math.sin(angulo) * velocidad - 160,
                random.uniform(0.6, 1.3),
                color,
                random.uniform(3, 7),
            ))

    def actualizar(self, dt):
        vivas = []
        for p in self.particulas:
            p.vida -= dt
            if p.vida <= 0:
                continue
            p.vy += self.GRAVEDAD * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            vivas.append(p)
        self.particulas = vivas

    def dibujar(self, pantalla):
        for p in self.particulas:
            radio = max(1, int(p.radio * p.vida / p.vida_max))
            pygame.draw.circle(pantalla, p.color, (int(p.x), int(p.y)), radio)
