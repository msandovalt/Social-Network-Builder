"""
Ajustes del jugador que se recuerdan entre partidas (por ahora, la paleta de
daltonismo). Se guardan en un archivo JSON en la carpeta personal del usuario.

Pensado para no romper nunca el juego: si el archivo no existe, está dañado o
tiene un valor inválido, se usan los valores por defecto; y si no se puede
guardar (carpeta de solo lectura, por ejemplo), simplemente no se guarda.
"""

import json
import os

from ui.paletas import PALETA_POR_DEFECTO, es_paleta_valida

RUTA_POR_DEFECTO = os.path.join(os.path.expanduser("~"), ".social_network_builder.json")


class Ajustes:
    def __init__(self, ruta=RUTA_POR_DEFECTO):
        self.ruta = ruta
        self.daltonismo = PALETA_POR_DEFECTO
        self.mute = False
        self.volumen_sfx = 0.7
        self.volumen_musica = 0.5
        self.cargar()

    def cargar(self):
        try:
            with open(self.ruta, encoding="utf-8") as archivo:
                datos = json.load(archivo)
        except (OSError, ValueError):
            return  # sin archivo o con basura: se quedan los valores por defecto
        if not isinstance(datos, dict):
            return
        if es_paleta_valida(datos.get("daltonismo")):
            self.daltonismo = datos["daltonismo"]
        if isinstance(datos.get("mute"), bool):
            self.mute = datos["mute"]
        if isinstance(datos.get("volumen_sfx"), (int, float)) and not isinstance(datos.get("volumen_sfx"), bool):
            self.volumen_sfx = max(0.0, min(1.0, float(datos["volumen_sfx"])))
        if isinstance(datos.get("volumen_musica"), (int, float)) and not isinstance(datos.get("volumen_musica"), bool):
            self.volumen_musica = max(0.0, min(1.0, float(datos["volumen_musica"])))

    def guardar(self):
        """Devuelve True si se pudo guardar."""
        try:
            with open(self.ruta, "w", encoding="utf-8") as archivo:
                json.dump(
                    {
                        "daltonismo": self.daltonismo,
                        "mute": self.mute,
                        "volumen_sfx": self.volumen_sfx,
                        "volumen_musica": self.volumen_musica,
                    },
                    archivo,
                )
            return True
        except OSError:
            return False

