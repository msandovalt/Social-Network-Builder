"""
Recursos del jugador: el estado numérico que el árbol, la tragamonedas y,
más adelante, los eventos aleatorios van a modificar.

Unidades:
- dinero, usuarios: enteros. El dinero puede quedar negativo (deuda); eso es
  lo que se considera quiebra.
- usuarios nunca superan `limite_usuarios` (el mercado que tus regiones
  conquistadas pueden alcanzar); None significa sin tope.
- bienestar, reputacion, engagement: escala 0-100, siempre acotados.
- crecimiento: tasa de crecimiento pasivo de usuarios por ronda (0.02 = +2%).
"""

LIMITE_MIN_ESCALA = 0
LIMITE_MAX_ESCALA = 100
RECURSOS_ESCALA = ("bienestar", "reputacion", "engagement")


def efectos_en_puntos(efectos):
    """Copia de `efectos` con el engagement convertido de fracción (0.08) a
    puntos de la escala 0-100 (8), como lo aplican las rondas y los eventos."""
    convertidos = dict(efectos)
    if "engagement" in convertidos:
        convertidos["engagement"] *= 100
    return convertidos


class Recursos:
    def __init__(self, dinero=10000, usuarios=500, bienestar=70,
                 reputacion=70, engagement=30, crecimiento=0.0):
        self.dinero = dinero
        self.usuarios = usuarios
        self.bienestar = bienestar
        self.reputacion = reputacion
        self.engagement = engagement
        self.crecimiento = crecimiento
        self.limite_usuarios = None  # lo fija el mapa: suma de la capacidad de tus regiones
        self.dinero_generado_total = 0
        self.usuarios_pico = max(0, int(round(usuarios)))
        self._normalizar()

    def aplicar_efectos(self, efectos):
        """Aplica un diccionario de efectos (ej. {"bienestar": -5, "dinero": 200})
        sumándolos a los recursos actuales y luego normaliza los valores
        (enteros, límites 0-100). Las condiciones de derrota no se revisan
        aquí: las revisa el sistema de rondas."""
        delta_dinero = efectos.get("dinero", 0)
        if delta_dinero > 0:
            self.dinero_generado_total += int(round(delta_dinero))

        for clave, valor in efectos.items():
            if hasattr(self, clave):
                setattr(self, clave, getattr(self, clave) + valor)
        self._normalizar()

    def _normalizar(self):
        """Deja los recursos en un estado válido: dinero y usuarios enteros,
        usuarios nunca negativos, y las escalas dentro de 0-100."""
        self.dinero = int(round(self.dinero))
        self.usuarios = max(0, int(round(self.usuarios)))
        if self.limite_usuarios is not None:
            self.usuarios = min(self.usuarios, self.limite_usuarios)
        if self.usuarios > self.usuarios_pico:
            self.usuarios_pico = self.usuarios
        for clave in RECURSOS_ESCALA:
            valor = getattr(self, clave)
            valor = max(LIMITE_MIN_ESCALA, min(LIMITE_MAX_ESCALA, valor))
            setattr(self, clave, round(valor, 2))

    def actualizar_limite_usuarios(self, limite):
        """Cambia el tope de usuarios y recorta de inmediato si quedaron por encima."""
        self.limite_usuarios = limite
        self._normalizar()

    def esta_en_quiebra(self):
        """Quiebra = deuda. Quedarse exactamente en 0 (por ejemplo, tras
        comprar un nodo con todo el dinero) todavía no cuenta."""
        return self.dinero < 0

    def sufre_exodo(self):
        return self.usuarios <= 0
