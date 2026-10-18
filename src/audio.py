"""
Gestor centralizado de audio y efectos sonoros (pygame.mixer).

Ofrece:
- Control de volumen independiente para SFX y Música (0.0 a 1.0).
- Opción de 'mute' toggleable (ej. con la tecla M).
- Síntesis procedural de tonos básicos (ondas senoidales/cuadradas con envolvente
  mediante `array` y `pygame.mixer.Sound(buffer=...)`) cuando no existen archivos
  .wav/.ogg en disco.
- Manejo de excepciones silencioso para funcionar en entornos sin dispositivo
  de audio (ej. tests unitarios o servidores CI).
"""

import array
import math
import os

import pygame

FRECUENCIA_MUESTREO = 22050

# Definición procedural de cada efecto: lista de (frecuencia_hz, duracion_s, forma, volumen_rel)
# forma: "seno" | "cuadrada"
RECETAS_SFX = {
    "clic_ui": [
        (680, 0.045, "seno", 0.5),
    ],
    "click_ui": [
        (680, 0.045, "seno", 0.5),
    ],
    "compra_nodo": [
        (523.25, 0.07, "seno", 0.6),   # Do5
        (659.25, 0.07, "seno", 0.65),  # Mi5
        (783.99, 0.11, "seno", 0.7),   # Sol5
    ],
    "comprar_nodo": [
        (523.25, 0.07, "seno", 0.6),
        (659.25, 0.07, "seno", 0.65),
        (783.99, 0.11, "seno", 0.7),
    ],
    "expansion_region": [
        (440.00, 0.08, "seno", 0.65),  # La4
        (554.37, 0.08, "seno", 0.65),  # Do#5
        (659.25, 0.09, "seno", 0.7),   # Mi5
        (880.00, 0.16, "seno", 0.75),  # La5
    ],
    "expandir_region": [
        (440.00, 0.08, "seno", 0.65),
        (554.37, 0.08, "seno", 0.65),
        (659.25, 0.09, "seno", 0.7),
        (880.00, 0.16, "seno", 0.75),
    ],
    "giro_tragamonedas": [
        (360, 0.05, "cuadrada", 0.4),
        (480, 0.05, "cuadrada", 0.4),
    ],
    "frenar_carrete": [
        (420, 0.04, "seno", 0.5),
    ],
    "premio_triple": [
        (587.33, 0.08, "seno", 0.7),   # Re5
        (739.99, 0.08, "seno", 0.7),   # Fa#5
        (880.00, 0.08, "seno", 0.75),  # La5
        (1174.66, 0.18, "seno", 0.8),  # Re6
    ],
    "premio_tragamonedas": [
        (587.33, 0.08, "seno", 0.7),
        (739.99, 0.08, "seno", 0.7),
        (880.00, 0.14, "seno", 0.75),
    ],
    "sin_premio": [
        (310.0, 0.08, "seno", 0.4),
        (260.0, 0.10, "seno", 0.4),
    ],
    "alerta_evento": [
        (311.13, 0.11, "cuadrada", 0.55),  # Re#4
        (277.18, 0.16, "cuadrada", 0.55),  # Do#4
    ],
    "evento_positivo": [
        (523.25, 0.08, "seno", 0.6),
        (659.25, 0.12, "seno", 0.65),
    ],
    "fin_victoria": [
        (523.25, 0.10, "seno", 0.7),
        (659.25, 0.10, "seno", 0.7),
        (783.99, 0.10, "seno", 0.75),
        (1046.50, 0.25, "seno", 0.8),
    ],
    "fin_derrota": [
        (392.00, 0.14, "seno", 0.65),
        (349.23, 0.14, "seno", 0.65),
        (311.13, 0.14, "seno", 0.65),
        (261.63, 0.28, "seno", 0.7),
    ],
}

RUTA_SONIDOS = os.path.join(os.path.dirname(__file__), "..", "assets", "sonidos")


def sintetizar_pcm(segmentos, frecuencia_muestreo=FRECUENCIA_MUESTREO, canales=2):
    """Genera un buffer de enteros de 16 bits con signo (mono o estéreo) a partir de
    una lista de tuplas (frecuencia_hz, duracion_s_o_ms, forma, volumen)."""
    muestras = array.array("h")
    for freq, duracion, forma, vol in segmentos:
        # Si duracion > 5, se interpreta en milisegundos para conveniencia
        dur_s = duracion / 1000.0 if duracion > 5 else float(duracion)
        total = max(1, int(frecuencia_muestreo * dur_s))
        ataque = max(1, int(total * 0.08))
        caida = max(1, int(total * 0.25))
        for i in range(total):
            if forma == "silencio" or freq <= 0 or vol <= 0:
                valor = 0
            else:
                if i < ataque:
                    env = i / ataque
                elif i > total - caida:
                    env = (total - i) / caida
                else:
                    env = 1.0

                t = i / frecuencia_muestreo
                angulo = 2.0 * math.pi * freq * t
                if forma == "cuadrada":
                    onda = 1.0 if math.sin(angulo) >= 0 else -1.0
                elif forma == "triangulo":
                    onda = (2.0 / math.pi) * math.asin(math.sin(angulo))
                elif forma == "ruido":
                    onda = math.sin(angulo * 13.7 + math.cos(angulo * 7.3) * 5.0)
                else:
                    onda = 0.8 * math.sin(angulo) + 0.2 * math.sin(2.0 * angulo)

                valor = int(max(-32767, min(32767, onda * env * vol * 16000)))
            muestras.append(valor)
            if canales >= 2:
                muestras.append(valor)
    return muestras.tobytes()


class GestorAudio:
    """Gestor de SFX y música con síntesis procedural de respaldo y control de mute."""

    def __init__(self, volumen_sfx=0.7, volumen_musica=0.5, mute=False, habilitar_mixer=True):
        self._volumen_sfx = max(0.0, min(1.0, float(volumen_sfx)))
        self._volumen_musica = max(0.0, min(1.0, float(volumen_musica)))
        self.mute = bool(mute)
        self.disponible = False
        self._sonidos = {}
        self._canal_musica = None
        self._loop_musica = None
        self.historial = []  # Registro de los últimos SFX disparados (útil para tests y debug)
        self.ultimo_evento = None

        if habilitar_mixer:
            self._inicializar_mixer()

    def _inicializar_mixer(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=FRECUENCIA_MUESTREO, size=-16, channels=2, buffer=512)
            self.disponible = pygame.mixer.get_init() is not None
        except Exception:
            self.disponible = False

        if not self.disponible:
            return

        for nombre, receta in RECETAS_SFX.items():
            sonido = self._cargar_o_sintetizar(nombre, receta)
            if sonido is not None:
                self._sonidos[nombre] = sonido

        self._actualizar_volumenes()

    def _cargar_o_sintetizar(self, nombre, receta):
        for ext in (".wav", ".ogg"):
            ruta = os.path.join(RUTA_SONIDOS, nombre + ext)
            if os.path.isfile(ruta):
                try:
                    return pygame.mixer.Sound(ruta)
                except Exception:
                    pass

        try:
            pcm = sintetizar_pcm(receta)
            return pygame.mixer.Sound(buffer=pcm)
        except Exception:
            return None

    # --- Propiedades de volumen y mute -------------------------------------------

    @property
    def volumen_sfx(self):
        return self._volumen_sfx

    @volumen_sfx.setter
    def volumen_sfx(self, valor):
        self._volumen_sfx = max(0.0, min(1.0, float(valor)))
        self._actualizar_volumenes()

    @property
    def volumen_musica(self):
        return self._volumen_musica

    @volumen_musica.setter
    def volumen_musica(self, valor):
        self._volumen_musica = max(0.0, min(1.0, float(valor)))
        self._actualizar_volumenes()

    def ajustar_volumen_sfx(self, valor):
        self.volumen_sfx = valor

    def ajustar_volumen_musica(self, valor):
        self.volumen_musica = valor

    def establecer_mute(self, valor):
        self.mute = bool(valor)
        self._actualizar_volumenes()
        return self.mute

    def alternar_mute(self):
        """Activa o desactiva el silencio general y devuelve el nuevo estado."""
        self.mute = not self.mute
        self._actualizar_volumenes()
        return self.mute

    def volumen_efectivo_sfx(self):
        return 0.0 if self.mute else self._volumen_sfx

    def volumen_efectivo_musica(self):
        return 0.0 if self.mute else self._volumen_musica

    def _actualizar_volumenes(self):
        if not self.disponible:
            return
        vol_sfx = self.volumen_efectivo_sfx()
        for sonido in self._sonidos.values():
            try:
                sonido.set_volume(vol_sfx)
            except Exception:
                pass
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.set_volume(self.volumen_efectivo_musica())
        except Exception:
            pass
        if self._canal_musica is not None:
            try:
                self._canal_musica.set_volume(self.volumen_efectivo_musica())
            except Exception:
                pass

    # --- Reproducción de efectos y hooks limpios ---------------------------------

    def reproducir(self, nombre):
        """Reproduce un efecto por nombre. Nunca lanza excepción."""
        if self.mute or self._volumen_sfx <= 0.0:
            return False

        self.ultimo_evento = nombre
        self.historial.append(nombre)
        if len(self.historial) > 100:
            self.historial.pop(0)

        if not self.disponible:
            return True

        sonido = self._sonidos.get(nombre)
        if sonido is None:
            return False
        try:
            sonido.set_volume(self.volumen_efectivo_sfx())
            sonido.play()
            return True
        except Exception:
            return False

    def iniciar_musica(self, ruta_archivo=None):
        """Inicia música desde `ruta_archivo` o delega a `iniciar_musica_ambiente`."""
        if not self.disponible:
            return False
        if ruta_archivo is not None:
            if not os.path.isfile(ruta_archivo):
                return False
            try:
                pygame.mixer.music.load(ruta_archivo)
                pygame.mixer.music.set_volume(self.volumen_efectivo_musica())
                pygame.mixer.music.play(-1)
                return True
            except Exception:
                return False
        return self.iniciar_musica_ambiente()

    def iniciar_musica_ambiente(self):
        """Inicia música de fondo desde archivo o un pad ambiental sintetizado."""
        if not self.disponible:
            return False
        for ext in (".ogg", ".wav", ".mp3"):
            ruta = os.path.join(RUTA_SONIDOS, "musica" + ext)
            if os.path.isfile(ruta):
                try:
                    pygame.mixer.music.load(ruta)
                    pygame.mixer.music.set_volume(self.volumen_efectivo_musica())
                    pygame.mixer.music.play(-1)
                    return True
                except Exception:
                    pass
        try:
            if self._loop_musica is None:
                acorde = [
                    (220.00, 0.8, "seno", 0.12),
                    (277.18, 0.8, "seno", 0.10),
                    (329.63, 0.8, "seno", 0.12),
                    (246.94, 0.8, "seno", 0.10),
                ]
                self._loop_musica = pygame.mixer.Sound(buffer=sintetizar_pcm(acorde))
            self._loop_musica.set_volume(self.volumen_efectivo_musica())
            self._canal_musica = self._loop_musica.play(loops=-1)
            return True
        except Exception:
            return False

    def detener_musica(self):
        if not self.disponible:
            return
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        if self._canal_musica is not None:
            try:
                self._canal_musica.stop()
            except Exception:
                pass

    # Hooks semánticos para los eventos del juego
    def clic_ui(self):
        return self.reproducir("clic_ui")

    def click_ui(self):
        return self.reproducir("clic_ui")

    def compra_nodo(self):
        return self.reproducir("compra_nodo")

    def expansion_region(self):
        return self.reproducir("expansion_region")

    def giro_tragamonedas(self):
        return self.reproducir("giro_tragamonedas")

    def frenar_carrete(self):
        return self.reproducir("frenar_carrete")

    def premio_tragamonedas(self, es_triple=False, hay_premio=True):
        if not hay_premio:
            return self.reproducir("sin_premio")
        return self.reproducir("premio_triple" if es_triple else "premio_tragamonedas")

    def alerta_evento(self, critico=True, es_critico=None):
        usar_critico = critico if es_critico is None else es_critico
        return self.reproducir("alerta_evento" if usar_critico else "evento_positivo")

    def fin_partida(self, victoria=False):
        return self.reproducir("fin_victoria" if victoria else "fin_derrota")
