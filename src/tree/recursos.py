"""
Recursos del jugador: el estado numérico que el árbol y, más adelante,
los eventos aleatorios van a modificar.
"""


class Recursos:
    def __init__(self, dinero=10000, usuarios=500, bienestar=70,
                 reputacion=70, engagement=30, crecimiento=0.0):
        self.dinero = dinero
        self.usuarios = usuarios
        self.bienestar = bienestar
        self.reputacion = reputacion
        self.engagement = engagement
        self.crecimiento = crecimiento

    def aplicar_efectos(self, efectos):
        """Aplica un diccionario de efectos (ej. {"bienestar": -5, "dinero": 200})
        sumándolos a los recursos actuales. No revisa condiciones de derrota aquí;
        eso se hace en el loop principal después de sumar los efectos de la ronda."""
        for clave, valor in efectos.items():
            if hasattr(self, clave):
                setattr(self, clave, getattr(self, clave) + valor)

    def esta_en_quiebra(self):
        return self.dinero <= 0

    def sufre_exodo(self):
        return self.usuarios <= 0
