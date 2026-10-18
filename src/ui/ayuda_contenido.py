"""
Texto de la pantalla de ayuda. Sin Pygame: se puede probar y revisar aparte.

Los números (segundos por ronda, umbral de bienestar...) salen de las mismas
constantes que usa el juego, así la ayuda no se desactualiza al ajustar valores.

Cada página es un diccionario con `titulo` y `puntos`, una lista de
(cabecera, texto). Para que quepan en pantalla: como máximo 4 puntos por página
y textos de hasta ~150 caracteres.
"""

from eventos.gestor import INTERVALO_EVENTOS
from mapa.mundo import Mundo
from tree.ronda import DURACION_RONDA, UMBRAL_FUGA, FUGA_MAXIMA

MAX_PUNTOS_POR_PAGINA = 4
MAX_CARACTERES_POR_PUNTO = 160

_TOTAL_REGIONES = len(Mundo.construir_mundo_inicial().regiones)

PAGINAS = (
    {
        "titulo": "Objetivo",
        "puntos": (
            ("Conquista el planeta",
             f"Tu meta es llevar tu red social a las {_TOTAL_REGIONES} regiones del planeta. "
             "Cuando conquistes la última, ganas."),
            ("Cuida a tu comunidad",
             "Una red sana crece más y llega más lejos: si tus usuarios se sienten mal, se van "
             "y no puedes expandirte."),
            ("Cómo se pierde",
             "Pierdes si te quedas en deuda (dinero negativo) o si ya no queda ningún usuario."),
            ("Cómo empezar",
             "Compra nodos en el Árbol, juega a la tragamonedas para ganar premios y expándete "
             "desde el Mapa."),
        ),
    },
    {
        "titulo": "Recursos",
        "puntos": (
            ("Dinero",
             "Sirve para comprar nodos del árbol y pagar las rutas del mapa. Si queda negativo, pierdes."),
            ("Usuarios",
             "Crecen solos en cada ronda, pero nunca superan la capacidad de las regiones que "
             "conquistaste. Para seguir creciendo, expándete."),
            ("Bienestar",
             f"Mide cómo se sienten tus usuarios. Si baja de {UMBRAL_FUGA}, en cada ronda se va "
             f"hasta el {round(FUGA_MAXIMA * 100)} % de ellos."),
            ("Reputación y engagement",
             "La reputación abre las regiones exigentes y los eventos la afectan. El engagement "
             "mide cuánto tiempo pasan tus usuarios en la red."),
        ),
    },
    {
        "titulo": "Árbol",
        "puntos": (
            ("Cómo comprar",
             "Haz clic en un nodo para ver su detalle y confirma la compra. Un aro amarillo marca "
             "los que puedes comprar ahora."),
            ("Efecto fijo",
             "Se aplica una sola vez, en el momento de comprarlo."),
            ("Interruptor y dial",
             "Se aplican en cada ronda: el interruptor mientras esté encendido y el dial en "
             "proporción a su valor (de 0 a 100)."),
            ("Bifurcación",
             "Eliges una de dos variantes y puedes cambiar cuando quieras. Cada una tiene ventajas y costos."),
        ),
    },
    {
        "titulo": "Mapa",
        "puntos": (
            ("Expandirte",
             "Solo puedes expandirte a regiones vecinas de las que ya tienes. Elige una para ver "
             "qué necesita."),
            ("Requisitos",
             "Cada región pide nodos del árbol, usuarios, reputación y bienestar mínimos, y que "
             "pagues el costo de la ruta."),
            ("Ruta más barata",
             "Si eliges una región lejana, el mapa resalta en amarillo el camino más barato para "
             "llegar hasta ella."),
            ("Capacidad e ingresos",
             "Cada región conquistada te da ingresos en cada ronda y sube el máximo de usuarios "
             "de tu red."),
        ),
    },
    {
        "titulo": "Rondas y eventos",
        "puntos": (
            ("Rondas",
             f"Cada {round(DURACION_RONDA)} segundos pasa una ronda: se aplican los efectos de tus "
             "nodos y regiones, y tus usuarios crecen."),
            ("Eventos",
             f"Cada {round(INTERVALO_EVENTOS)} segundos ocurre un evento aleatorio, bueno o malo. "
             "Puedes cerrar el aviso con un clic."),
            ("Tu seguridad cuenta",
             "Los nodos de seguridad reducen a la mitad las pérdidas de los eventos malos y frenan "
             "los que se propagan entre regiones."),
            ("Pausa",
             "El tiempo no corre en el menú, en la pausa ni en la ayuda."),
        ),
    },
    {
        "titulo": "Tragamonedas",
        "puntos": (
            ("Cómo jugar",
             "Pulsa Jugar y detén cada carrete con un clic o con las teclas 1, 2 y 3. Queda el "
             "símbolo que estaba en el centro."),
            ("Premios",
             "Si alineas tres símbolos iguales ganas una recompensa en dinero, usuarios o "
             "reputación. Jugar tiene un costo."),
            ("Bienestar y velocidad",
             "Con menos bienestar los carretes giran más rápido y es más difícil acertar. Las "
             "probabilidades no cambian."),
        ),
    },
    {
        "titulo": "Controles",
        "puntos": (
            ("Mouse",
             "Haz clic en botones, nodos y regiones. Un clic sobre un aviso lo cierra."),
            ("Teclado",
             "Esc pausa el juego, cierra paneles y vuelve atrás. Las teclas 1, 2 y 3 detienen los "
             "carretes. Las flechas cambian de página en la ayuda."),
            ("Botones de arriba",
             "El botón con el signo de pregunta abre esta ayuda y el de las dos barras pausa el juego."),
        ),
    },
    {
        "titulo": "Accesibilidad",
        "puntos": (
            ("Modo daltonismo",
             "Puedes elegir una paleta de colores pensada para protanopía, deuteranopía, "
             "tritanopía o acromatopsia."),
            ("No solo color",
             "Además del color, el juego usa íconos y formas (marcas, flechas, candados) para que "
             "no dependas solo de él."),
            ("Dónde cambiarlo",
             "Desde el menú principal, desde la pausa o con el botón de esta página."),
        ),
    },
)

TOTAL_PAGINAS = len(PAGINAS)
INDICE_ACCESIBILIDAD = next(i for i, p in enumerate(PAGINAS) if p["titulo"] == "Accesibilidad")
