"""
Nodo del árbol de funcionalidades de la red social.

Cada nodo representa una funcionalidad que el jugador puede desbloquear.
El campo `tipo_control` determina cómo se comporta una vez desbloqueado:

- "fijo": aplica su efecto una sola vez, al desbloquearse.
- "interruptor": el jugador puede encenderlo/apagarlo en cualquier momento;
  el efecto se aplica cada ronda mientras esté encendido.
- "dial": expone un valor ajustable de 0 a 100; el efecto escala
  proporcionalmente a ese valor.
- "bifurcacion": el jugador elige una de dos variantes; puede cambiar de
  variante más adelante (normalmente con un costo, aún por definir).
"""

TIPOS_CONTROL = ("fijo", "interruptor", "dial", "bifurcacion")


class Nodo:
    def __init__(self, id_nodo, nombre, tipo_control, costo, efectos=None, variantes=None, descripcion=""):
        if tipo_control not in TIPOS_CONTROL:
            raise ValueError(f"tipo_control inválido: {tipo_control}")

        self.id = id_nodo
        self.nombre = nombre
        self.tipo_control = tipo_control
        self.costo = costo
        self.descripcion = descripcion

        # Estado de progresión
        self.desbloqueado = False

        # Estado específico según tipo_control
        self.activo = False            # usado por "interruptor"
        self.valor = 0                 # usado por "dial", rango 0-100
        self.variante_actual = None    # usado por "bifurcacion"
        self.variantes = variantes or {}   # ej. {"cifrado": {"efectos": {...}}, ...}

        # Efectos base (usados directamente por nodos "fijo", "interruptor" y "dial")
        self.efectos = efectos or {}

        # Relaciones en el árbol
        self.padre = None
        self.hijos = []

    def agregar_hijo(self, hijo):
        hijo.padre = self
        self.hijos.append(hijo)

    def puede_desbloquearse(self, recursos):
        """Un nodo puede desbloquearse si su padre ya está desbloqueado
        (o no tiene padre, es la raíz) y hay dinero suficiente."""
        if self.desbloqueado:
            return False
        if self.padre is not None and not self.padre.desbloqueado:
            return False
        return recursos.dinero >= self.costo

    def desbloquear(self, recursos):
        if not self.puede_desbloquearse(recursos):
            return False
        recursos.dinero -= self.costo
        self.desbloqueado = True
        if self.tipo_control == "fijo":
            recursos.aplicar_efectos(self.efectos)
        return True

    def alternar_interruptor(self):
        if self.tipo_control != "interruptor" or not self.desbloqueado:
            return
        self.activo = not self.activo

    def ajustar_dial(self, nuevo_valor):
        if self.tipo_control != "dial" or not self.desbloqueado:
            return
        self.valor = max(0, min(100, nuevo_valor))

    def elegir_variante(self, nombre_variante):
        if self.tipo_control != "bifurcacion" or not self.desbloqueado:
            return
        if nombre_variante in self.variantes:
            self.variante_actual = nombre_variante

    def efecto_por_ronda(self):
        """Calcula el efecto que este nodo aporta en la ronda actual.
        Se llama una vez por ronda desde el loop principal del juego.
        Los nodos "fijo" no devuelven nada aquí: su efecto ya se aplicó
        una sola vez al desbloquearse."""
        if not self.desbloqueado:
            return {}

        if self.tipo_control == "interruptor":
            return self.efectos if self.activo else {}

        if self.tipo_control == "dial":
            factor = self.valor / 100
            return {clave: valor * factor for clave, valor in self.efectos.items()}

        if self.tipo_control == "bifurcacion" and self.variante_actual:
            return self.variantes[self.variante_actual].get("efectos", {})

        return {}
