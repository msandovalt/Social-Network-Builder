"""Partículas simples (confeti / destellos) y textos flotantes para celebrar premios y cambios."""

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


class _TextoFlotante:
    __slots__ = ("x", "y", "vy", "texto", "color", "vida", "vida_max")

    def __init__(self, x, y, texto, color, duracion=1.25, vy=-38.0):
        self.x = float(x)
        self.y = float(y)
        self.vy = float(vy)
        self.texto = str(texto)
        self.color = color
        self.vida = self.vida_max = float(duracion)


class SistemaParticulas:
    GRAVEDAD = 520.0

    def __init__(self):
        self.particulas = []
        self.textos = []

    @property
    def hay_activas(self):
        return bool(self.particulas)

    @property
    def hay_textos_activos(self):
        return bool(self.textos)

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

    def emitir_texto(self, x, y, texto, color, duracion=1.25):
        """Lanza una etiqueta flotante (p. ej. '+$3.000' o '-8') que sube y se desvanece."""
        desplazamiento = (len(self.textos) % 3 - 1) * 8
        self.textos.append(_TextoFlotante(x + desplazamiento, y, texto, color, duracion))

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

        textos_vivos = []
        for t in self.textos:
            t.vida -= dt
            if t.vida <= 0:
                continue
            t.y += t.vy * dt
            t.vy *= max(0.0, 1.0 - 1.5 * dt)
            textos_vivos.append(t)
        self.textos = textos_vivos

    def dibujar(self, pantalla, fuente=None):
        for p in self.particulas:
            radio = max(1, int(p.radio * p.vida / p.vida_max))
            pygame.draw.circle(pantalla, p.color, (int(p.x), int(p.y)), radio)

        if not self.textos or fuente is None:
            return
        for t in self.textos:
            frac = max(0.0, min(1.0, t.vida / t.vida_max))
            alpha = int(255 * min(1.0, frac * 1.6))
            sombra = fuente.render(t.texto, True, (10, 12, 24))
            superficie = fuente.render(t.texto, True, t.color)
            sombra.set_alpha(alpha)
            superficie.set_alpha(alpha)
            rect = superficie.get_rect(center=(int(t.x), int(t.y)))
            pantalla.blit(sombra, (rect.x + 1, rect.y + 2))
            pantalla.blit(superficie, rect)
