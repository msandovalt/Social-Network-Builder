# Social Network Builder

Simulador/estrategia donde el jugador es el creador de su propia red social y
debe hacerla crecer tomando decisiones sobre funcionalidades, monetización y
seguridad, equilibrando crecimiento e ingresos con el bienestar de sus
usuarios.

Proyecto para Estructura de Datos II — Universidad del Norte.

## Integrantes

- (agregar nombres del equipo)

## Requisitos

- Python 3.10 o superior
- Pygame

## Instalación

```bash
# Clonar el repositorio
git clone <url-del-repo>
cd social-network-builder

# Crear entorno virtual (opcional pero recomendado)
python3 -m venv venv
source venv/bin/activate   # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## Ejecutar el juego

```bash
cd src
python3 main.py
```

## Ejecutar las pruebas

```bash
python3 -m unittest discover -s tests -v
```

Ningún test abre una ventana. Los de lógica no usan Pygame; `test_juego.py`
y `test_layout.py` solo usan sus constantes, `Rect` y `Event` (simulan clics y
verifican que nada se superponga ni se salga de la pantalla).

## Cómo se juega

1. En **Principal** ves tus recursos (dinero, usuarios, bienestar, reputación
   y engagement) y juegas a la **tragamonedas**: los carretes giran en vertical; detén cada uno
   con clic o con las teclas `1`, `2` y `3` (queda el símbolo que estaba al
   centro). Si alineas tres símbolos iguales ganas
   la recompensa. Entre más bajo el bienestar, más rápido giran.
2. En **Árbol** haz clic en un nodo para ver su detalle y comprarlo. Los
   nodos interactivos dejan el panel abierto al comprarlos para configurarlos:
   - **Interruptor**: encendelo o apagalo; mientras esté encendido aplica su
     efecto cada ronda.
   - **Dial**: ajusta su intensidad de 0 a 100 con `-` / `+`.
   - **Bifurcación**: elige una de las dos variantes.
3. En **Mapa** ves el planeta como un grafo de 8 regiones. Empiezas en
   Sudamérica y solo puedes expandirte a regiones **vecinas** de las que ya
   tienes, si cumples lo que pide cada una: nodos del árbol (por ejemplo,
   Europa exige "Seguridad avanzada"), usuarios, reputación y **bienestar**
   mínimos, y pagar la ruta. Al elegir una región lejana se resalta la **ruta más barata**
   hasta ella. Cada región conquistada aporta usuarios y dinero en cada ronda y
   **sube el máximo de usuarios** de tu red: sin expandirte, tu red deja de crecer.
4. Cada **ronda** (10 segundos en tiempo real) se aplican los efectos del árbol, el ingreso de tus
   regiones y los
   usuarios crecen según la tasa de crecimiento. El tiempo no corre en el
   menú, en la pausa ni en la pantalla de fin.
   **Cuida el bienestar:** si baja de 40, en cada ronda se va una parte de tus
   usuarios (hasta el 12 % con bienestar 0), el indicador se pone rojo y recibes
   un aviso. Puedes recuperarlo apagando funciones adictivas (como el scroll
   infinito) o eligiendo variantes que cuidan a la comunidad (mensajes
   cifrados, moderación humana).
5. Cada **30 segundos** ocurre un **evento aleatorio** (reseñas, filtraciones de
   datos, ciberacoso, rumores...) y aparece un aviso que puedes cerrar con un
   clic. Lo que construiste en el árbol cambia sus efectos: la seguridad
   reduce a la mitad las pérdidas de los eventos malos y contiene los que se
   propagan, y algunos eventos solo ocurren por decisiones tuyas (por ejemplo,
   el scroll infinito puede dejar a tus usuarios agotados). Los eventos de
   propagación nacen en una de tus regiones y se riegan por el grafo, solo a
   través de regiones conquistadas.
6. **Ganas** si conquistas las 8 regiones del planeta; al terminar ves un
   resumen y un mensaje según el bienestar que lograste mantener.
7. Pierdes si te quedas **en deuda** (dinero negativo) o si **no quedan
   usuarios**. Quedarte en $0 exacto no cuenta como quiebra.

`Esc` pausa el juego (o cierra el panel de detalle si está abierto).

**Ayuda y accesibilidad**

- **Ayuda:** el botón `?` de la esquina superior (o "Ayuda" en el menú y en la
  pausa) abre las instrucciones en 8 páginas. Se navega con las pestañas, los
  botones Anterior / Siguiente o las flechas del teclado. El tiempo no corre
  mientras la ayuda está abierta.
- **Accesibilidad:** desde el menú, la pausa o la última página de la ayuda
  puedes elegir una paleta de colores para **protanopía**, **deuteranopía**,
  **tritanopía** o **acromatopsia**. El cambio es instantáneo y se recuerda la
  próxima vez que abras el juego.

## Estructura del proyecto

```
social-network-builder/
├── src/
│   ├── main.py                  # Punto de entrada: ventana 1280x720 y loop principal
│   ├── ajustes.py               # Ajustes que se recuerdan entre partidas (paleta de daltonismo)
│   ├── juego.py                 # Clase Juego: estado, pantallas, clics y dibujo
│   ├── tree/
│   │   ├── nodo.py              # Clase Nodo (fijo / interruptor / dial / bifurcación)
│   │   ├── arbol.py             # Clase Arbol (BFS, efectos por ronda, árbol inicial)
│   │   ├── recursos.py          # Recursos (dinero, usuarios, bienestar...) con límites
│   │   └── ronda.py             # Sistema de rondas y condiciones de derrota
│   ├── eventos/
│   │   ├── evento.py            # Evento, ResultadoEvento y catálogo de eventos
│   │   └── gestor.py            # Temporizador (30 s), elección al azar y aplicación
│   ├── mapa/
│   │   ├── grafo.py             # Grafo ponderado: BFS, Dijkstra, conexidad
│   │   └── mundo.py             # Regiones, requisitos, expansión e ingresos
│   ├── minijuego/
│   │   └── tragamonedas.py      # Lógica de la tragamonedas (sin Pygame)
│   └── ui/
│       ├── tema.py              # Colores (intercambiables), fuentes, fondo animado, paneles y botones
│       ├── paletas.py           # Paleta normal y las de daltonismo (solo datos)
│       ├── ayuda_contenido.py   # Texto de la ayuda, generado desde las constantes del juego
│       ├── ayuda_view.py        # Pantalla de ayuda por páginas
│       ├── accesibilidad_view.py # Elección de paleta para daltonismo
│       ├── animacion.py         # Easing, pulso y contadores animados (sin Pygame)
│       ├── particulas.py        # Partículas de celebración
│       ├── formato.py           # Formato de números y efectos para mostrar
│       ├── menu_view.py         # Menú, pausa y pantalla de fin
│       ├── hub_view.py          # Pantalla principal y encabezado con recursos y ronda
│       ├── eventos_view.py      # Aviso (toast) de los eventos aleatorios
│       ├── mapa_view.py         # Dibujo del planeta, rutas y panel de la región
│       ├── tree_view.py         # Dibujo del árbol y detección de clic sobre nodos
│       ├── nodo_detalle_view.py # Panel de detalle: compra y controles del nodo
│       └── tragamonedas_view.py # Dibujo de la tragamonedas
├── assets/
│   └── fuentes/                 # Opcional: principal.ttf para usar tu propia tipografía
├── tests/
│   ├── test_arbol.py            # Árbol y nodos
│   ├── test_paletas.py          # Paletas: contraste y distinguibilidad simulando cada daltonismo
│   ├── test_tema.py             # Cambio de paleta en vivo y contraste del texto
│   ├── test_ajustes.py          # Ajustes guardados, incluso con archivos dañados
│   ├── test_ayuda.py            # Contenido de la ayuda
│   ├── _cvd.py                  # Simulador de daltonismo usado por los tests
│   ├── test_eventos.py          # Temporizador, selección, mitigación y propagación
│   ├── test_grafo.py            # BFS, Dijkstra y casos borde
│   ├── test_mundo.py            # Regiones, requisitos, expansión y rutas
│   ├── test_recursos.py         # Límites y condiciones de derrota
│   ├── test_rondas.py           # Sistema de rondas
│   ├── test_tragamonedas.py     # Minijuego (incluye el giro suave)
│   ├── test_formato.py          # Formato de números y efectos
│   ├── test_animacion.py        # Easing, contadores animados y partículas
│   ├── test_layout.py           # Nada se superpone ni se sale de la pantalla
│   └── test_juego.py            # Flujo de pantallas, clics y animaciones
├── requirements.txt
└── README.md
```

## Estado actual

- [x] Árbol de funcionalidades con 4 tipos de control: fijo, interruptor,
      dial y bifurcación, todos con efecto real en el juego.
- [x] Sistema de rondas: efectos por ronda del árbol y crecimiento de usuarios.
- [x] Recursos con límites (escalas 0-100, valores enteros) y condiciones de
      derrota (quiebra / éxodo de usuarios) con pantalla de fin.
- [x] Interfaz (1280x720, escalable): tema visual coherente con fondo
      animado, tarjetas de recursos con contadores que suben y bajan, árbol
      con estados visibles y panel de compra con controles, pausa y fin.
- [x] Tragamonedas animada: carretes con giro fluido, frenado suave, brillo y
      partículas al ganar, y transiciones con fundido entre pantallas.
- [x] Pruebas unitarias de árbol, grafo, mapa, eventos, recursos, rondas, tragamonedas, formato, animación, layout y flujo del juego.
- [x] Eventos aleatorios cada 30 s, ligados al árbol (mitigación y contención)
      y al grafo (propagación por regiones conquistadas).
- [x] Tope de usuarios: cada región suma capacidad y el máximo es la suma de las
      regiones conquistadas.
- [x] Pantalla de ayuda con instrucciones y botón `?` durante la partida.
- [x] Modo daltonismo con 4 paletas (protanopía, deuteranopía, tritanopía y
      acromatopsia), íconos y formas que refuerzan el color, y ajuste recordado.
- [x] Objetivo del juego: conquistar todo el planeta (pantalla de victoria con
      resumen y confeti).
- [x] Grafo de expansión por regiones: BFS para saber qué regiones son vecinas
      y Dijkstra para planear la ruta más barata; la expansión depende de los
      nodos del árbol, los recursos y el costo de la ruta.
- [ ] Minijuego de habilidad ligado al bienestar: la tragamonedas ya existe;
      falta definir si es el definitivo (segunda/tercera entrega).
- [ ] Componente inclusivo (pendiente de definir).
- [ ] Modo multijugador local cliente-servidor (entrega final).

## Accesibilidad (daltonismo)

El color nunca es la única señal: el juego también usa **íconos y formas** (✓ y
✗, +, ! y candado en las regiones, flechas que suben o bajan en los recursos, un
ícono por tipo de nodo, símbolos distintos en la tragamonedas y signos + / - en
los efectos).

Las paletas de daltonismo se diseñaron con datos, no a ojo: `tests/_cvd.py`
simula cómo ve cada tipo (matrices de Machado et al., 2009) y
`tests/test_paletas.py` comprueba que, con esa simulación, los colores que
importan (éxito y peligro, botones, estados de nodos y de regiones, recursos)
siguen siendo claramente distintos, y que el texto mantiene buen contraste.

| Paleta | Idea |
|---|---|
| Protanopía y deuteranopía | Azul para lo bueno y naranja para lo malo, en vez de verde y rojo. |
| Tritanopía | Se evita depender de azules y amarillos; rojo y verde sí se distinguen. |
| Acromatopsia | Solo grises, con niveles de claridad muy distintos para cada significado. |

Limitaciones: es una simulación y no reemplaza probarlo con personas daltónicas
(conviene hacerlo antes de la Feria). El daltonismo parcial (anomalías) tiene
grados intermedios; las paletas están pensadas para el caso más exigente.

## Interfaz

- La ventana es de 1280x720 con `pygame.SCALED | pygame.RESIZABLE`: si tu
  pantalla es más chica, Pygame la escala solo y el código sigue trabajando
  en 1280x720.
- Todos los colores, fuentes y el tamaño de ventana están en `ui/tema.py`.
- Para usar tu propia tipografía copia un `.ttf` como
  `assets/fuentes/principal.ttf`.

## Valores provisionales a calibrar

- Bienestar bajo: umbral de fuga 40 y fuga máxima 12 % por ronda
  (`tree/ronda.py`); bienestar mínimo para expandirte a cada región
  (`mapa/mundo.py`: 40 a 55). Con una simulación de 300 partidas por tipo de
  jugador, quien ignora el bienestar no logra ganar, quien lo mantiene sobre 45
  gana siempre, y quien lo cuida bien gana en unos 8 minutos.
- Capacidad de usuarios por región (`mapa/mundo.py`, constantes `CAP_*`): entre
  1.000 y 8.000, 24.000 en total.

- Duración de la ronda: 10 s (`tree/ronda.py`).
- `crecimiento` es una tasa por ronda (0.02 = +2% de usuarios); el
  `engagement` de los nodos está en fracción (0.08) y se aplica como +8 puntos
  en la escala 0-100.
- Costos, efectos y recompensas de la tragamonedas se ajustan jugando.

Ver el documento de diseño completo del equipo para más detalle sobre las
decisiones tomadas y las ideas pendientes de evaluar.
