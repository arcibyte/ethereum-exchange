# Red de transferencias de tokens Ethereum

Proyecto final de **Estructura de Datos** — Universidad Industrial de Santander.

**Profesor:** Jonnathan Alfredo Ramos Chaux
**Equipo:** Jhon Arciniegas, Pablo Álvarez y Emerson Ballesteros (líder)

---

## ¿De qué trata el proyecto?

Construimos un **grafo** a partir de transferencias de un token ERC-20 en
Ethereum y lo analizamos con **4 algoritmos, uno por integrante**.

El grafo es:

- **V** = las direcciones (wallets, exchanges, contratos).
- **E** = las transferencias de una dirección a otra (aristas dirigidas).
- **w(e)** = la cantidad transferida.

## División de tareas

| Tarea | Pregunta que responde | Algoritmo | Responsable |
|-------|-----------------------|-----------|-------------|
| 1 | ¿Cuál es el camino más barato entre dos direcciones? | Bellman-Ford | Pablo Álvarez |
| 2 | ¿Qué nodos son los más importantes? | Centralidad de grado + PageRank | Jhon Arciniegas |
| 3 | ¿Qué grupos de nodos interactúan más entre sí? | Louvain (comunidades) | Emerson Ballesteros |
| 4 | ¿Cuál es la red mínima que conecta a todos? | Kruskal + Union-Find | Grupal |

**Emerson** es el líder: coordina las entregas y la comunicación con el
profesor, además de aportar su tarea (T3).

## Reglas del proyecto

- **No** se puede usar el algoritmo de Dijkstra.
- Todo se implementa **desde cero** en Python (diccionarios y listas).
- Las librerías externas solo se usan para graficar (matplotlib).

## Estructura del proyecto

```
proyecto/
├── data/sample/            <- dataset de ejemplo (pequeño, corre al instante)
│   ├── transferencias.csv  <- transferencias (from_address, to_address, value)
│   └── etiquetas.csv       <- nombre legible de cada dirección
├── src/                    <- nuestros algoritmos (Python puro)
│   ├── grafo.py            <- carga del dataset y construcción del grafo
│   ├── bellman_ford.py     <- tarea 1: caminos de costo mínimo
│   ├── centralidad.py      <- tarea 2: centralidad y PageRank
│   ├── comunidades.py      <- tarea 3: detección de comunidades
│   └── arbol_expansion.py  <- tarea 4: árbol de expansión mínima
├── notebooks/
│   └── Proyecto_Teoria_Grafos.ipynb   <- entregable principal (notebook)
├── tests/
│   └── test_algorithms.py  <- pruebas de cada algoritmo
├── docs/
│   ├── guion_video.md      <- plan del video (9 min)
│   └── poster.md           <- contenido del póster
└── README.md
```

## Cómo ejecutar

**Google Colab (recomendado):** sube el repositorio a GitHub y abre el
notebook desde Colab.

**Local:**

```bash
git clone https://github.com/arcibyte/ethereum-exchange
cd ethereum-exchange

# (opcional) entorno virtual
python3 -m venv .venv && source .venv/bin/activate

pip install matplotlib jupyter
jupyter notebook notebooks/Proyecto_Teoria_Grafos.ipynb
```

Para correr las pruebas:

```bash
pip install pytest
python -m pytest tests/ -v
```

## Sobre el dataset

Para este proyecto usamos una **muestra pequeña** (12 direcciones y 24
transferencias) para que todo se entienda y corra rápido. La misma idea se
aplica al dataset completo (~38 millones de transferencias), que se comparte
por Drive y **no** se sube al repositorio por su tamaño.

## Entregables y evaluación

| Producto | Peso |
|----------|------|
| Notebook (descripción del dataset 10% + 4 tareas 60%) | 70% |
| Video (máximo 9 minutos) | 15% |
| Póster | 15% |
