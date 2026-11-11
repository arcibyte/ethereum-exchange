# Arquitectura del proyecto

Este documento explica **cómo está dividido** el código para que cada
integrante pueda trabajar en su parte sin romper la de los demás.

## Idea general

El proyecto tiene **una capa compartida** (datos y grafo) y **cuatro módulos
independientes** (uno por tarea). Cada módulo recibe el grafo como parámetro y
no sabe nada de los otros.

```
                 +---------------------------+
                 |   src/grafo.py (COMPARTIDO) |
                 |   carga el CSV y arma el    |
                 |   grafo dirigido ponderado  |
                 +-------------+-------------+
                               |
        +--------------+-------+-------+--------------+
        |              |               |              |
  src/bellman_ford  src/centralidad  src/comunidades  src/arbol_expansion
     (Pablo)          (Jhon)          (Emerson)         (grupo)
        |              |               |              |
  tests/test_       tests/test_     tests/test_     tests/test_
  bellman_ford.py   centralidad.py  comunidades.py  arbol_expansion.py
```

## Dueños de cada archivo

| Archivo | Dueño | Tarea |
|---------|-------|-------|
| `src/grafo.py` | Grupo | Capa compartida (datos y grafo) |
| `src/analisis.py` | Grupo | Análisis del dataset completo con DuckDB |
| `src/evaluacion.py` | Grupo | Capa compartida (precisión@k contra las etiquetas) |
| `src/dataset.py` | Pablo Álvarez | Sección 1 — lectura, limpieza y perfil del dataset |
| `scripts/preparar_seccion1.py` | Pablo Álvarez | Sección 1 — genera `data/resumen/` y `data/tokens/` |
| `src/bellman_ford.py` | Pablo Álvarez | T1 — caminos de costo mínimo |
| `src/centralidad.py` | Jhon Arciniegas | T2 — centralidad y PageRank |
| `src/comunidades.py` | Emerson Ballesteros | T3 — comunidades (Louvain) |
| `src/arbol_expansion.py` | Grupo | T4 — MST (Kruskal + Union-Find) |
| `tests/test_dataset.py` | Pablo Álvarez | Pruebas de la sección 1 |
| `tests/test_evaluacion.py` | Grupo | Pruebas de la evaluación |
| `tests/test_bellman_ford.py` | Pablo Álvarez | Pruebas de T1 |
| `tests/test_centralidad.py` | Jhon Arciniegas | Pruebas de T2 |
| `tests/test_comunidades.py` | Emerson Ballesteros | Pruebas de T3 |
| `tests/test_arbol_expansion.py` | Grupo | Pruebas de T4 |

## El contrato de la capa compartida

`src/grafo.py` es lo único que todos usan. **Nadie carga el CSV por su cuenta.**

```python
from src.grafo import Grafo

grafo = Grafo()
grafo.cargar_transferencias("data/sample/transferencias.csv")
grafo.cargar_etiquetas("data/sample/etiquetas.csv")
```

Después de eso, todos los módulos reciben:

| Dato | Tipo | Qué es |
|------|------|--------|
| `grafo.adj` | `dict[str, list[tuple[str, float]]]` | lista de adyacencia `{nodo: [(vecino, peso), ...]}` |
| `grafo.nodos` | `set[str]` | todos los vértices |
| `grafo.aristas` | `list[tuple[str, str, float]]` | aristas `(origen, destino, peso)` |
| `grafo.etiquetas` | `dict[str, dict]` | nombre legible de cada dirección |
| `grafo.nombre(addr)` | `str` | nombre legible de un nodo |

### Carga única y formatos

La carga se hace **una sola vez** en la celda de la Sección 1 del notebook.
Después, las cuatro tareas reutilizan el mismo objeto `grafo`; ninguna vuelve
a abrir el CSV ni el Parquet.

`cargar()` detecta el formato por la extensión:

```python
from src.grafo import Grafo

# CSV pequeño (muestra del repo)
grafo = Grafo().cargar("data/sample/transferencias.csv")

# Parquet real: se trae una muestra a memoria, no las 38 M de filas
grafo = Grafo().cargar(
    "data/procesado/transferencias.parquet",
    muestra=2_000,
    semilla=42,
)
```

Para Parquet, DuckDB solo se usa para leer, filtrar y muestrear. Los
algoritmos siguen siendo Python puro y reciben el grafo ya construido. Si la
muestra deja nodos aislados, `grafo.conservar_componente_mayor()` se queda con
la componente conexa más grande sin volver a leer el archivo.

Cada módulo recibe `grafo.aristas` y construye **su propia estructura** con un
adaptador pequeño. Así ningún módulo depende de la estructura de otro:

```python
from src.comunidades import louvain_desde_aristas

comunidades = louvain_desde_aristas(grafo.aristas)   # arma su grafo no dirigido
```

| Módulo | Adaptador |
|--------|-----------|
| `bellman_ford.py` | `bellman_ford_desde_aristas` |
| `centralidad.py` | `pagerank_desde_aristas`, `centralidad_grado_desde_aristas` |
| `comunidades.py` | `louvain_desde_aristas`, `desde_aristas` |
| `arbol_expansion.py` | `kruskal_desde_aristas` |

> **Celda vs. módulo:** en Colab, cada cuadro de código es una **celda**; la
> implementación de cada algoritmo vive en un **módulo** `.py` dentro de
> `src/`. Las celdas solo importan y usan esos módulos.

### De dónde sale el CSV que carga `Grafo`

La sección 1 (`src/dataset.py`) produce, por token, un archivo
`data/tokens/<token>.csv` con las columnas
`from_address, to_address, value, n_transferencias`:

- un solo token (no se mezclan unidades);
- limpio con las reglas de los autores del dataset (valor > 0, sin polvo,
  sin autolazos);
- una arista por par (`value` = suma, `n_transferencias` = cuántas fueron).

`Grafo.cargar_transferencias` lo lee **sin cambios** (ignora la columna
extra). Para usar datos reales en una tarea basta con apuntar la ruta a ese
archivo; `grafo.py` no se modifica.

### Evaluar contra las etiquetas

`src/evaluacion.py` es la segunda pieza compartida: cualquier tarea que
produzca un puntaje por nodo lo evalúa con

```python
from src.evaluacion import evaluar_ranking
evaluar_ranking(puntajes, exchanges_presentes, ks=(10, 20, 50, 100))
```

Es la misma medida (precisión@k y recall@k) del artículo de los autores, así
que los resultados se pueden comparar con los publicados. Solo usa la
librería estándar y no importa ningún otro módulo de `src/`.

## Reglas de aislamiento

1. **Sin importaciones cruzadas.** `bellman_ford.py` no importa
   `centralidad.py`, ni al revés. Cada módulo solo importa la librería estándar
   (y, si hace falta, las capas compartidas `grafo` y `evaluacion`).
2. **Datos por parámetro.** Ningún módulo lee el CSV; recibe el grafo ya
   construido.
3. **Un archivo de tests por dueño.** Si modificas tu algoritmo, corres
   `pytest tests/test_<tu_modulo>.py`. No puedes romper los tests de otro
   porque no los tocas.
4. **La capa compartida se congela.** Si necesitas cambiar `src/grafo.py`,
   lo hablas con el grupo. Es el único punto de contacto entre tareas.
5. **Una sección del notebook por tarea.** Cada sección importa solo su módulo.

Con esto, si alguien reescribe su módulo entero, lo peor que puede pasar es que
**falle su propia sección**, no el proyecto completo.

## Cómo correr solo tu parte

```bash
# Toda la suite
python -m pytest tests/ -v

# Solo tu tarea (ejemplo: Pablo)
python -m pytest tests/test_dataset.py tests/test_bellman_ford.py -v

# Solo tu tarea (ejemplo: Jhon)
python -m pytest tests/test_centralidad.py -v

# Solo tu tarea (ejemplo: Emerson)
python -m pytest tests/test_comunidades.py -v

# Solo la tarea grupal
python -m pytest tests/test_arbol_expansion.py -v
```

## Cómo correr en Google Colab

1. Abre `notebooks/Proyecto_Teoria_Grafos.ipynb` en Colab.
2. Ejecuta la **celda de configuración**: clona el repositorio público y se
   ubica en su raíz.
3. Ejecuta las demás celdas en orden.

La celda de configuración también funciona en local: detecta la raíz del
repositorio automáticamente.

## Flujo de trabajo con ramas

Cada integrante trabaja en su rama y el líder integra en `main`:

```
main
├── feature/seccion1 (Pablo)
├── feature/tarea1   (Pablo)
├── feature/tarea2   (Jhon)
├── feature/tarea3   (Emerson)
└── feature/tarea4   (grupo)
```

Antes de pedir un merge, cada uno verifica que **sus** tests pasen.
