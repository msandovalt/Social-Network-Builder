"""Pruebas unitarias para el sistema de audio y síntesis procedural (src/audio.py)."""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pygame
from audio import GestorAudio, RECETAS_SFX, sintetizar_pcm
from ajustes import Ajustes
from juego import Juego, PRINCIPAL
from ui.audio_view import DURACION_INDICADOR_AUDIO, dibujar_indicador_audio
from ui.menu_view import RECT_BOTON_START
from ui.hub_view import RECT_BOTON_ARBOL
from ui.tema import ALTO, ANCHO, crear_fuentes


class TestSintesisProcedural(unittest.TestCase):
    def test_sintetizar_pcm_genera_bytes_para_todas_las_recetas(self):
        for nombre, receta in RECETAS_SFX.items():
            datos = sintetizar_pcm(receta, frecuencia_muestreo=22050, canales=2)
            self.assertIsInstance(datos, bytes, nombre)
            self.assertGreater(len(datos), 0, nombre)
            # 16-bit estéreo: múltiplo de 4 bytes
            self.assertEqual(len(datos) % 4, 0, nombre)

    def test_sintetizar_pcm_soporta_mono_y_distintas_ondas(self):
        receta = [
            (440, 60, "seno", 0.3),
            (550, 60, "cuadrada", 0.3),
            (660, 60, "triangulo", 0.3),
            (220, 60, "ruido", 0.2),
            (0, 40, "silencio", 0.0),
        ]
        datos_mono = sintetizar_pcm(receta, frecuencia_muestreo=22050, canales=1)
        datos_estereo = sintetizar_pcm(receta, frecuencia_muestreo=22050, canales=2)
        self.assertEqual(len(datos_estereo), len(datos_mono) * 2)


class TestGestorAudio(unittest.TestCase):
    def test_controles_de_volumen_se_acotan_entre_0_y_1(self):
        audio = GestorAudio(volumen_sfx=1.5, volumen_musica=-0.4, habilitar_mixer=False)
        self.assertEqual(audio.volumen_sfx, 1.0)
        self.assertEqual(audio.volumen_musica, 0.0)

        audio.ajustar_volumen_sfx(0.35)
        audio.ajustar_volumen_musica(0.8)
        self.assertAlmostEqual(audio.volumen_sfx, 0.35)
        self.assertAlmostEqual(audio.volumen_musica, 0.8)

    def test_alternar_mute_cambia_estado_y_silencia_reproduccion(self):
        audio = GestorAudio(habilitar_mixer=False)
        self.assertFalse(audio.mute)
        self.assertTrue(audio.reproducir("clic_ui"))
        self.assertEqual(audio.ultimo_evento, "clic_ui")

        nuevo_estado = audio.alternar_mute()
        self.assertTrue(nuevo_estado)
        self.assertTrue(audio.mute)
        self.assertFalse(audio.reproducir("compra_nodo"))
        # El historial no registra sonidos bloqueados por mute
        self.assertEqual(audio.historial, ["clic_ui"])

        audio.establecer_mute(False)
        self.assertFalse(audio.mute)
        self.assertTrue(audio.reproducir("compra_nodo"))
        self.assertEqual(audio.ultimo_evento, "compra_nodo")

    def test_hooks_semanticos_registran_los_eventos_correctos(self):
        audio = GestorAudio(habilitar_mixer=False)
        audio.clic_ui()
        audio.compra_nodo()
        audio.expansion_region()
        audio.giro_tragamonedas()
        audio.frenar_carrete()
        audio.premio_tragamonedas(es_triple=True, hay_premio=True)
        audio.premio_tragamonedas(es_triple=False, hay_premio=True)
        audio.premio_tragamonedas(es_triple=False, hay_premio=False)
        audio.alerta_evento(critico=True)
        audio.alerta_evento(critico=False)
        audio.fin_partida(victoria=True)
        audio.fin_partida(victoria=False)

        self.assertEqual(
            audio.historial,
            [
                "clic_ui",
                "compra_nodo",
                "expansion_region",
                "giro_tragamonedas",
                "frenar_carrete",
                "premio_triple",
                "premio_tragamonedas",
                "sin_premio",
                "alerta_evento",
                "evento_positivo",
                "fin_victoria",
                "fin_derrota",
            ],
        )

    def test_fallback_seguro_cuando_mixer_falla_al_inicializar(self):
        with patch("pygame.mixer.get_init", side_effect=pygame.error("Sin dispositivo de audio")):
            audio = GestorAudio(habilitar_mixer=True)
            self.assertFalse(audio.disponible)
            # Ninguna llamada debe lanzar excepción
            self.assertTrue(audio.clic_ui())
            self.assertFalse(audio.iniciar_musica("inexistente.ogg"))
            audio.detener_musica()


class TestIntegracionAudioEnJuego(unittest.TestCase):
    def test_tecla_m_alterna_mute_y_persiste_en_ajustes(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = os.path.join(tmp, "ajustes.json")
            ajustes = Ajustes(ruta)
            audio = GestorAudio(habilitar_mixer=False)
            juego = Juego(ajustes=ajustes, audio=audio)

            self.assertFalse(juego.audio.mute)
            juego.manejar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m))
            self.assertTrue(juego.audio.mute)
            self.assertTrue(ajustes.mute)

            # Al recargar ajustes desde disco se conserva el mute
            reabierto = Ajustes(ruta)
            self.assertTrue(reabierto.mute)

    def test_mostrar_indicador_de_audio(self):
        audio = GestorAudio(habilitar_mixer=False)
        juego = Juego(audio=audio)
        self.assertIsNone(juego.tiempo_indicador_audio)

        juego.manejar_evento(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m))
        self.assertEqual(juego.tiempo_indicador_audio, 0.0)
        self.assertTrue(juego.audio.mute)

        juego.actualizar(DURACION_INDICADOR_AUDIO / 2)
        self.assertIsNotNone(juego.tiempo_indicador_audio)

        juego.actualizar(DURACION_INDICADOR_AUDIO)
        self.assertIsNone(juego.tiempo_indicador_audio)

    def test_clics_de_navegacion_disparan_clic_ui(self):
        audio = GestorAudio(habilitar_mixer=False)
        juego = Juego(audio=audio)
        juego.manejar_evento(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=RECT_BOTON_START.center, button=1)
        )
        self.assertEqual(juego.estado, PRINCIPAL)
        self.assertIn("clic_ui", audio.historial)

        juego.manejar_evento(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=RECT_BOTON_ARBOL.center, button=1)
        )
        self.assertEqual(audio.historial.count("clic_ui"), 2)


class TestIndicadorAudioVisual(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()
        cls.fuentes = crear_fuentes()

    def _capturar(self, silenciado, tiempo=0.5):
        pantalla = pygame.Surface((ANCHO, ALTO))
        pantalla.fill((0, 0, 0))
        dibujar_indicador_audio(pantalla, self.fuentes, silenciado, tiempo)
        return pantalla

    def test_dibujar_estados_distintos(self):
        activo = pygame.image.tobytes(self._capturar(False), "RGB")
        silenciado = pygame.image.tobytes(self._capturar(True), "RGB")
        self.assertNotEqual(activo, silenciado)

    def test_aparece_y_desaparecer(self):
        visible = self._capturar(False)
        self.assertNotEqual(visible.get_at((ANCHO // 2, 45))[:3], (0, 0, 0))

        desvanecido = self._capturar(False, tiempo=DURACION_INDICADOR_AUDIO)
        self.assertEqual(desvanecido.get_at((ANCHO // 2, 45))[:3], (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
