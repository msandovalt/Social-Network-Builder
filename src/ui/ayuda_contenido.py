"""
Texto de la pantalla de ayuda. Sin Pygame: se puede probar y revisar aparte.

Los números (segundos por ronda, umbral de bienestar...) salen de las mismas
constantes que usa el juego, así la ayuda no se desactualiza al ajustar valores.

Cada página es un diccionario con `titulo` y `puntos`, una lista de
(cabecera, texto). Para que quepan en pantalla: como máximo 4 puntos por página
y textos de hasta ~150 caracteres.
"""

from eventos.gestor import INTERVALO_EVENTOS, INTERVALO_MIN, INTERVALO_MAX
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
             f"Conquista las {_TOTAL_REGIONES} regiones y llena toda la capacidad de usuarios para ganar."),
            ("Cuida a tu comunidad",
             "Una red sana crece más y llega más lejos; si tus usuarios se sienten mal, no podrás "
             "expandirte."),
            ("Cómo se pierde",
             "Pierdes si quedas en deuda (dinero negativo) o si no te queda ningún usuario."),
            ("Cómo empezar",
             "Compra nodos, gana premios en la tragamonedas y expándete desde el Mapa."),
        ),
    },
    {
        "titulo": "Recursos",
        "puntos": (
            ("Dinero",
             "Sirve para comprar nodos y pagar rutas. Cada ronda pagas costos de operación según tus regiones y usuarios; si queda negativo, pierdes."),
            ("Usuarios",
             "Crecen cada ronda hasta la capacidad de tus regiones; para crecer más, expándete."),
            ("Bienestar",
             f"Mide cómo se sienten tus usuarios. Si baja de {UMBRAL_FUGA}, cada ronda se va "
             f"hasta el {round(FUGA_MAXIMA * 100)} % de ellos. Compra una campaña en el panel para recuperar 10 puntos."),
            ("Reputación y engagement",
             "La reputación abre las regiones exigentes y los eventos la afectan; el engagement mide "
             "el tiempo que pasan tus usuarios."),
        ),
    },
    {
        "titulo": "Árbol",
        "puntos": (
            ("Cómo comprar",
             "Haz clic en un nodo, revisa su detalle y confirma la compra; el aro amarillo marca "
             "los disponibles."),
            ("Efecto fijo",
             "Se aplica una vez, en el momento de la compra."),
            ("Interruptor y dial",
             "Se aplican cada ronda: el interruptor mientras esté encendido y el dial según su "
             "valor (0 a 100). Cada cambio muestra su precio y pide confirmación."),
            ("Bifurcación",
             "Eliges una variante; cambiar a otra tiene un costo que se muestra antes de confirmar."),
        ),
    },
    {
        "titulo": "Mapa",
        "puntos": (
            ("Expandirte",
             "Solo puedes llegar a regiones vecinas de las que ya tienes. Elige una para ver qué "
             "necesita."),
            ("Requisitos",
             "Cada región pide nodos del árbol, mínimos de usuarios, reputación y bienestar, y "
             "pagar la ruta."),
            ("Ruta más barata",
             "Al elegir una región lejana, el mapa resalta en amarillo el camino más barato hasta ella."),
            ("Capacidad e ingresos",
             "Cada región da ingresos y capacidad, pero también aumenta los costos de operación. "
             "Para ganar, conquista todas las regiones y llena la capacidad de usuarios."),
        ),
    },
    {
        "titulo": "Rondas y eventos",
        "puntos": (
            ("Rondas",
             f"Cada {round(DURACION_RONDA)} segundos activos se aplican los efectos de tus nodos y "
             "regiones. El tiempo se pausa al abrir el árbol o el mapa."),
            ("Eventos",
             f"Ocurren al azar (cada {round(INTERVALO_MIN)}–{round(INTERVALO_MAX)}s, prom. {round(INTERVALO_EVENTOS)} segundos). "
             "Con bienestar alto abundan los positivos; si baja, las crisis."),
            ("Tu seguridad cuenta",
             "Los nodos de seguridad reducen a la mitad las pérdidas de los eventos malos y frenan "
             "su propagación."),
            ("Pausa",
             "El tiempo no corre en el menú, la pausa, la ayuda, el árbol ni el mapa."),
        ),
    },
    {
        "titulo": "Tragamonedas",
        "puntos": (
            ("Cómo jugar",
             "Pulsa Jugar y detén cada carrete con un clic o con 1, 2 y 3. Queda el símbolo del centro."),
            ("Premios",
             "Tres símbolos iguales dan una recompensa en dinero, usuarios o reputación. Jugar cuesta."),
            ("Bienestar y velocidad",
             "Con menos bienestar los carretes giran más rápido y cuesta más acertar; las "
             "probabilidades no cambian."),
        ),
    },
    {
        "titulo": "Controles",
        "puntos": (
            ("Mouse",
             "Haz clic en botones, nodos y regiones; un clic sobre un aviso lo cierra."),
            ("Teclado",
             "Esc pausa, cierra paneles y vuelve atrás; 1, 2 y 3 detienen los carretes; M silencia "
             "el audio; las flechas cambian de página."),
            ("Botones de arriba",
             "El botón ? abre esta ayuda y el de las barras pausa el juego."),
        ),
    },
    {
        "titulo": "Accesibilidad",
        "puntos": (
            ("Modo daltonismo",
             "Elige una paleta para protanopía, deuteranopía, tritanopía o acromatopsia."),
            ("No solo color",
             "El juego también usa íconos y formas (marcas, flechas, candados), no solo color."),
            ("Dónde cambiarlo",
             "Desde el menú principal, la pausa o el botón de esta página."),
        ),
    },
)

TOTAL_PAGINAS = len(PAGINAS)
INDICE_ACCESIBILIDAD = next(i for i, p in enumerate(PAGINAS) if p["titulo"] == "Accesibilidad")
