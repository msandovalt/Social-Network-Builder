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

## Estructura del proyecto

```
social-network-builder/
├── src/
│   ├── main.py              # Punto de entrada, loop principal de Pygame
│   ├── tree/
│   │   ├── nodo.py          # Clase Nodo (fijo / interruptor / dial / bifurcación)
│   │   ├── arbol.py         # Clase Arbol (recorrido BFS, árbol inicial)
│   │   └── recursos.py      # Clase Recursos (dinero, usuarios, bienestar...)
│   └── ui/
│       └── tree_view.py     # Dibujo preliminar del árbol en pantalla
├── tests/
│   └── test_arbol.py        # Pruebas de la lógica del árbol
├── requirements.txt
└── README.md
```

## Estado actual (primera entrega)

- [x] Árbol de funcionalidades con 4 tipos de control: fijo, interruptor,
      dial y bifurcación.
- [x] Interfaz gráfica preliminar: muestra el árbol y permite desbloquear
      nodos con clic.
- [x] Pruebas unitarias de la lógica del árbol.
- [ ] Sistema de eventos aleatorios.
- [ ] Grafo de expansión por regiones (segunda entrega).
- [ ] Minijuego de habilidad ligado al bienestar (segunda/tercera entrega).
- [ ] Componente inclusivo (pendiente de definir).
- [ ] Modo multijugador local cliente-servidor (entrega final).

Ver el documento de diseño completo del equipo para más detalle sobre las
decisiones tomadas y las ideas pendientes de evaluar.
