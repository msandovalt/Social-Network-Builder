"""
Eventos aleatorios: sucesos que le pasan a tu red social cada cierto tiempo
(una reseña en prensa, una filtración de datos, un rumor que se riega...).

Cómo se conectan con el resto del juego:
- Lo que construyes en el ÁRBOL los cambia: ciertos nodos MITIGAN los eventos
  malos (reducen a la mitad sus pérdidas) o CONTIENEN su propagación, y algunos
  eventos solo aparecen si tomaste ciertas decisiones de diseño (por ejemplo,
  el "scroll infinito" puede engancharte a tus usuarios).
- Los eventos de PROPAGACIÓN viajan por el GRAFO del mapa: nacen en una región
  tuya al azar y se riegan (BFS) por las regiones conquistadas vecinas.

Unidades: igual que en los nodos del árbol, el engagement se escribe como
fracción (0.04 = +4 puntos) y se convierte al aplicarlo.
"""

from collections import namedtuple

POSITIVO = "positivo"
NEGATIVO = "negativo"

# efectos: lo que quedó aplicado (ya con mitigación), en las mismas unidades del catálogo
# origen / regiones: solo en eventos de propagación
# mitigado: se redujeron las pérdidas por tener nodos de seguridad
# contenido: la propagación llegó menos lejos por tener nodos de seguridad
ResultadoEvento = namedtuple("ResultadoEvento", "evento efectos origen regiones mitigado contenido")


class Evento:
    def __init__(self, id_evento, titulo, descripcion, tono, efectos=None, por_region=None,
                 saltos=0, mitigadores=(), contencion=None, requiere_nodos=()):
        self.id = id_evento
        self.titulo = titulo
        self.descripcion = descripcion
        self.tono = tono
        self.efectos = efectos or {}            # efectos globales, una sola vez
        self.por_region = por_region or {}      # efectos por cada región alcanzada (propagación)
        self.saltos = saltos                    # hasta dónde se propaga, en saltos
        self.mitigadores = tuple(mitigadores)   # nodos que reducen a la mitad las pérdidas
        self.contencion = contencion or {}      # nodo -> saltos que le quita a la propagación
        self.requiere_nodos = tuple(requiere_nodos)  # solo ocurre si están desbloqueados

    @property
    def se_propaga(self):
        return bool(self.por_region)

    def es_elegible(self, arbol):
        return all(arbol.nodo_por_id(id_nodo).desbloqueado for id_nodo in self.requiere_nodos)


CATALOGO = (
    # --- Buenas noticias ---
    Evento("resena_prensa", "Reseña en la prensa",
           "Un medio destaca tu red por promover un uso sano de la tecnología.",
           POSITIVO, efectos={"reputacion": 8, "usuarios": 150}),
    Evento("influencer", "Un creador te recomienda",
           "Un creador de contenido invita a sus seguidores a probar tu red.",
           POSITIVO, efectos={"usuarios": 300, "engagement": 0.04}),
    Evento("desconexion_digital", "Campaña de desconexión digital",
           "Tus usuarios se animan a pasar un rato lejos de la pantalla.",
           POSITIVO, efectos={"bienestar": 8, "engagement": -0.03}),
    Evento("inversion", "Inversión inesperada",
           "Un fondo apuesta por tu proyecto y te transfiere capital.",
           POSITIVO, efectos={"dinero": 1500}),
    Evento("publicacion_viral", "Publicación viral",
           "Una publicación positiva se comparte de región en región.",
           POSITIVO, por_region={"usuarios": 120}, saltos=2),

    # --- Problemas ---
    Evento("ciberacoso", "Ola de ciberacoso",
           "Crecen los comentarios hirientes y tus usuarios se sienten mal.",
           NEGATIVO, efectos={"bienestar": -8, "reputacion": -4},
           mitigadores=("comunidad_verificacion", "seguridad_avanzada")),
    Evento("filtracion_datos", "Filtración de datos",
           "Una brecha de seguridad expone información de tus usuarios.",
           NEGATIVO, efectos={"reputacion": -12, "dinero": -800},
           mitigadores=("seguridad_basica", "seguridad_avanzada")),
    Evento("reto_peligroso", "Reto viral peligroso",
           "Un reto riesgoso se difunde y presiona a los más jóvenes.",
           NEGATIVO, efectos={"bienestar": -10, "engagement": 0.06},
           mitigadores=("comunidad_verificacion",)),
    Evento("desinformacion", "Ola de desinformación",
           "Un rumor falso se riega de región en región.",
           NEGATIVO, por_region={"reputacion": -3}, saltos=3,
           contencion={"seguridad_basica": 1, "seguridad_avanzada": 2}),
    Evento("caida_servidor", "Caída del servidor",
           "Un fallo técnico deja a tus usuarios sin servicio por unas horas.",
           NEGATIVO, efectos={"dinero": -600, "bienestar": -2}),
    Evento("adiccion_scroll", "Atrapados en el scroll",
           "Tus usuarios pasan horas desplazándose sin parar y se sienten agotados.",
           NEGATIVO, efectos={"bienestar": -6, "engagement": 0.08},
           requiere_nodos=("feed_scroll",)),
)


# Aviso que el juego muestra (una vez) cuando el bienestar cae por debajo del
# umbral de fuga. No está en el catálogo: no sale al azar, lo dispara el juego.
ALERTA_BIENESTAR = Evento(
    "alerta_bienestar", "¡Tus usuarios se están yendo!",
    "Con el bienestar tan bajo abandonan la red en cada ronda. Apaga funciones "
    "adictivas o mejora la moderación para recuperarlo.",
    NEGATIVO,
)
