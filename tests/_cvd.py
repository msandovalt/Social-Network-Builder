"""Simulación de daltonismo (Machado et al. 2009, severidad 1.0) y distancia de color CIE76."""
import math

MATRICES = {
    "protanopia": ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216), (-0.003882, -0.048116, 1.051998)),
    "deuteranopia": ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881)),
    "tritanopia": ((1.255528, -0.076749, -0.178779), (-0.078411, 0.930809, 0.147602), (0.004733, 0.691367, 0.303900)),
}

def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def _enc(c):
    c = max(0.0, min(1.0, c))
    return 255 * (12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055)

def simular(rgb, tipo):
    """Color (R,G,B 0-255) tal como lo vería alguien con `tipo` (acromatopsia = gris por luminancia)."""
    lin = [_lin(c) for c in rgb[:3]]
    if tipo == "acromatopsia":
        y = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
        v = _enc(y)
        return (v, v, v)
    if tipo in (None, "normal"):
        return tuple(float(c) for c in rgb[:3])
    m = MATRICES[tipo]
    return tuple(_enc(sum(m[i][j] * lin[j] for j in range(3))) for i in range(3))

def a_lab(rgb):
    r, g, b = (_lin(c) for c in rgb[:3])
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = (0.2126 * r + 0.7152 * g + 0.0722 * b)
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116
    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))

def delta_e(c1, c2, tipo=None):
    l1, l2 = a_lab(simular(c1, tipo)), a_lab(simular(c2, tipo))
    return math.dist(l1, l2)

def luminancia(rgb):
    r, g, b = (_lin(c) for c in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contraste(c1, c2):
    a, b = sorted((luminancia(c1), luminancia(c2)), reverse=True)
    return (a + 0.05) / (b + 0.05)
