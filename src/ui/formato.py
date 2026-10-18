"""Utilidades de formato para mostrar números y efectos en la interfaz."""

ETIQUETAS_EFECTO = {
    "dinero": "dinero",
    "usuarios": "usuarios",
    "bienestar": "bienestar",
    "reputacion": "reputación",
    "engagement": "engagement",
    "crecimiento": "crecimiento",
}


def formato_numero(valor):
    """Entero con separador de miles estilo es-CO: 10000 -> '10.000'."""
    return f"{int(round(valor)):,}".replace(",", ".")


def formatear_efecto(clave, valor):
    """Texto legible de un efecto: ('crecimiento', 0.02) -> '+2% crecimiento'.
    El crecimiento es una tasa y el engagement viene como fracción (0.08 = 8
    puntos), igual que en tree/ronda.py."""
    etiqueta = ETIQUETAS_EFECTO.get(clave, clave)
    if clave == "crecimiento":
        cantidad = f"{valor * 100:+.0f}%"
    elif clave == "engagement":
        cantidad = f"{valor * 100:+.0f}"
    else:
        signo = "+" if valor >= 0 else "-"
        prefijo = "$" if clave == "dinero" else ""
        if float(valor).is_integer():
            numero = formato_numero(abs(valor))
        else:  # valores fraccionarios (ej. +0,5 de reputación por ronda)
            numero = f"{abs(valor):.1f}".replace(".", ",")
        cantidad = f"{signo}{prefijo}{numero}"
    return f"{cantidad} {etiqueta}"


def formatear_efectos(efectos):
    return ", ".join(formatear_efecto(clave, valor) for clave, valor in efectos.items())
