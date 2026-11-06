# proyecto teoria de grafos - red ethereum defi
## universidad industrial de santander | estructura de datos
**profesor:** Jonnathan Alfredo Ramos Chaux

---

## equipo y division de responsabilidades

lider del proyecto: Emerson Ballesteros
rol: coordinar entregas, comunicacion con el profesor

### tareas por integrante (esfuerzo aprox 33% cada uno)

| componente | jhon arciniegas | pablo alvarez | emerson ballesteros (lider) |
|------------|----------------|---------------|---------------------|
| tarea individual | T2: pagerank + betweenness | T1: bellman-ford (caminos minimos) | T3: louvain (comunidades) |
| tarea grupal | T4: kruskal mst (1/3) | T4: kruskal mst (1/3) | T4: kruskal mst (1/3) |
| exploracion dataset (S1) | — | principal | — |
| modulo src/ | centrality.py | graph_loader.py, bellman_ford.py | community_detection.py |
| modulo grupal | spanning_tree.py (kruskal) | spanning_tree.py (unionfind) | spanning_tree.py (analytics) |
| notebook colab | T2 + integracion | estructura + S1 + T1 | T3 + conclusiones |
| video youtube (9 min) | T2 + T4 (3-6 min) | intro + dataset (0-3 min) | T3 + conclusiones (6-9 min) |
| poster academico | diseno y maquetacion | revision final | contenido tecnico |
| README + git | creacion del repo + gestion github | documentacion tecnica | coordinacion general |

nota de equidad:
- emerson se encarga de la gestion (lider, coordinacion), menos en diseno de poster
- jhon creo el repositorio y maneja github entonces menos carga en video
- pablo se encarga de la documentacion tecnica y el dataset entonces puede reducir el trabajo en git

---

## estructura de directorios

```
proyecto/
|
|-- notebooks/
|   └── Proyecto_Teoria_Grafos.ipynb    <- notebook principal (entregable 70%)
|
|-- src/
|   |-- __init__.py
|   |-- graph_loader.py                 <- carga y construccion del grafo (pablo)
|   |-- bellman_ford.py                 <- tarea 1: caminos minimos (pablo)
|   |-- centrality.py                   <- tarea 2: centralidad (jhon)
|   |-- community_detection.py          <- tarea 3: comunidades (emerson)
|   └── spanning_tree.py                <- tarea 4: mst grupal (todos)
|
|-- data/
|   |-- raw/                            <- dataset original (no subir a git)
|   |-- processed/                      <- datos preprocesados (generados)
|   └── samples/                        <- muestras pequeñas para desarrollo
|
|-- docs/
|   └── (vacio)
|
|-- tests/
|   └── test_algorithms.py              <- tests unitarios
|
└── assets/                             <- graficas generadas por el notebook
```

---

## reglas importantes

- dijkstra esta **prohibido** en las 4 tareas. si se detecta el uso la tarea queda en 0.0
- todos los algoritmos deben implementarse desde cero en python puro (listas, diccionarios)
- networkx, igraph y scipy solo se pueden usar para visualizaciones o comparacion, no para la logica principal

---

## como correr el proyecto

**opcion A - google colab (recomendado)**

1. subir el repo a github
2. abrir el notebook desde colab
3. ejecutar la celda 0 que hace el git clone
4. ejecutar todas las celdas en orden

**opcion B - local**

```bash
git clone https://github.com/arcibyte/ethereum-exchange
cd ethereum-exchange

python3 -m venv .venv
source .venv/bin/activate

pip install jupyter networkx matplotlib pandas tqdm

jupyter notebook notebooks/Proyecto_Teoria_Grafos.ipynb
```

---

## flujo de trabajo git

ramas del proyecto:
```
main                   <- rama principal (solo el lider hace merge)
|-- feature/seccion1   <- pablo: exploracion del dataset
|-- feature/tarea1     <- pablo: bellman-ford
|-- feature/tarea2     <- jhon: centralidad + pagerank
|-- feature/tarea3     <- emerson: deteccion de comunidades
|-- feature/tarea4     <- todos: kruskal mst
└── feature/docs       <- poster + guion de video
```

como contribuir:
```bash
git checkout feature/tarea2

git add src/centrality.py
git commit -m "feat(T2): implementar pagerank con iteracion de potencias"

git push origin feature/tarea2
# luego crear PR en github y jhon hace merge
```

convencion de commits:
```
feat(T1): nueva funcionalidad en tarea 1
fix(T3): corregir bug en deteccion de comunidades
docs: actualizar readme
test: agregar tests para bellman_ford
refactor: mejorar eficiencia en graph_loader
```

---

## criterios de evaluacion

| componente | peso | responsable |
|------------|------|-------------|
| notebook google colab | 70% | grupal |
| -- seccion 1: dataset | 10% | pablo |
| -- tarea 1: bellman-ford | 15% | pablo |
| -- tarea 2: centralidad | 15% | jhon |
| -- tarea 3: comunidades | 15% | emerson |
| -- tarea 4: mst grupal | 15% | grupal |
| video youtube (max 9 min) | 15% | grupal |
| poster academico | 15% | grupal |

---

## dataset

ethereum token transfers (ERC-20)

- archivo: token_transfers_full.csv (~38.9M filas, 8.3 GB) - no esta en el repo, se comparte por drive
- columnas: token_address, from_address, to_address, value, transaction_hash, log_index, block_number
- se modela como grafo dirigido ponderado G = (V, E, w)
  - V = wallets unicas
  - E = transferencias agregadas (from -> to)
  - w(e) = volumen total transferido entre el par


