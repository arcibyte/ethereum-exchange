# Red de transferencias de tokens Ethereum

Proyecto final de **Estructura de Datos** — Universidad Industrial de Santander.

**Profesor:** Jonnathan Alfredo Ramos Chaux
**Equipo:** Jhon Arciniegas, Pablo Álvarez y Emerson Ballesteros (líder)

[![Abrir en Google Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/arcibyte/ethereum-exchange/blob/main/notebooks/Proyecto_Final_Colab.ipynb)

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
├── data/
│   ├── sample/             <- muestra mínima para tests (12 nodos)
│   │   ├── transferencias.csv
│   │   └── etiquetas.csv
│   ├── muestra/            <- muestra conectada real de USDC (~2.000 aristas)
│   │   ├── transferencias_2k.csv
│   │   └── etiquetas.csv
│   └── real/               <- etiquetas reales (ver data/real/FUENTE.md)
│       └── exchange_labels.csv <- 296 exchanges (247 cex, 49 dex)
├── src/                    <- nuestros algoritmos (Python puro)
│   ├── grafo.py            <- COMPARTIDO: carga única (CSV/Parquet)
│   ├── bellman_ford.py     <- tarea 1 (Pablo)
│   ├── centralidad.py      <- tarea 2 (Jhon)
│   ├── comunidades.py      <- tarea 3 (Emerson)
│   └── arbol_expansion.py  <- tarea 4 (grupo)
├── tests/                  <- un archivo de pruebas por dueño
│   ├── conftest.py
│   ├── test_bellman_ford.py
│   ├── test_centralidad.py
│   ├── test_comunidades.py
│   ├── test_arbol_expansion.py
│   ├── test_grafo.py
│   └── test_datos.py
├── notebooks/
│   ├── Proyecto_Final_Colab.ipynb     <- ENTREGABLE único (carga datos de Drive/local)
│   ├── Proyecto_Teoria_Grafos.ipynb   <- versión modular para desarrollo
│   └── Preparar_Dataset_Colab.ipynb   <- herramienta para procesar el CSV grande
├── scripts/
│   ├── preparar_dataset.py <- 8,3 GB -> Parquet (~0,8 GB)
│   └── generar_muestra.py  <- Parquet -> muestra conectada + etiquetas
├── requirements.txt
├── requirements-datos.txt  <- duckdb + pyarrow (solo preprocesamiento)
└── README.md
```

El código está dividido por tareas en `src/`, y cada módulo tiene sus
pruebas en `tests/`.

## Cómo ejecutar

### Google Colab — entregable

El entregable es **un solo notebook**:

```
notebooks/Proyecto_Final_Colab.ipynb
```

Incluye el código de los cuatro algoritmos en sus propias celdas y **carga
los datos desde un solo archivo**:

```
transferencias.parquet   (~807 MB)
```

El profesor puede dejarlo en:

```
/content/transferencias.parquet
Mi unidad/ED2/transferencias.parquet
data/procesado/transferencias.parquet
```

1. Sube `transferencias.parquet`.
2. Abre `notebooks/Proyecto_Final_Colab.ipynb` en Colab.
3. Ejecuta la celda **“Montar Google Drive”** (si lo subiste a Drive).
4. Ejecuta las celdas en orden.

El notebook genera una muestra de USDC desde el Parquet, ejecuta las cuatro
tareas y calcula las estadísticas del dataset completo con DuckDB.

### Google Colab — versión modular (desarrollo)

`notebooks/Proyecto_Teoria_Grafos.ipynb` es la versión para el equipo:
clona el repositorio, importa los módulos de `src/` y permite trabajar tarea
por tarea con tests. No es el archivo que se entrega.

### Local

```bash
git clone https://github.com/arcibyte/ethereum-exchange
cd ethereum-exchange

# (opcional) entorno virtual
python3 -m venv .venv && source .venv/bin/activate

pip install matplotlib jupyter
jupyter notebook notebooks/Proyecto_Final_Colab.ipynb
```

Para desarrollo y tests:

```bash
pip install pytest
python -m pytest tests/ -q
jupyter notebook notebooks/Proyecto_Teoria_Grafos.ipynb
```

### Pruebas

```bash
pip install pytest

python -m pytest tests/ -v                    # toda la suite
python -m pytest tests/test_bellman_ford.py -v    # solo T1 (Pablo)
python -m pytest tests/test_centralidad.py -v     # solo T2 (Jhon)
python -m pytest tests/test_comunidades.py -v     # solo T3 (Emerson)
python -m pytest tests/test_arbol_expansion.py -v # solo T4 (grupo)
```

## Scripts de desarrollo (opcional)

El entregable **no necesita estos scripts**: solo usa `transferencias.parquet`.
Se mantienen para regenerar el dataset o una muestra de referencia.

```bash
# CSV de 8,3 GB -> Parquet de ~0,8 GB
python scripts/preparar_dataset.py convertir \
    --entrada /ruta/token_transfers_full.csv \
    --salida data/procesado/transferencias.parquet \
    --memoria 2GB --temporal data/procesado/tmp

# Parquet -> muestra de USDC (referencia; el notebook también la genera)
python scripts/generar_muestra.py \
    --entrada data/procesado/transferencias.parquet \
    --salida data/muestra/transferencias_2k.csv \
    --objetivo 2000 --filas 65000 --semilla 42 \
    --token 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48 --decimales 6
```

## Sobre el dataset

El entregable usa **un solo archivo**: `transferencias.parquet` (~0,8 GB,
38.901.039 filas). El profesor lo sube a Colab o a Drive. El notebook genera
la muestra de USDC que necesitan los algoritmos. El CSV original de 8,3 GB
**no** se sube al repositorio.

El pipeline se ejecuta con `scripts/preparar_dataset.py` y
`scripts/generar_muestra.py`.

```bash
pip install -r requirements-datos.txt

# 1) CSV de 8,3 GB -> Parquet de ~0,8 GB
python scripts/preparar_dataset.py convertir \
    --entrada /ruta/transferencias.csv \
    --salida data/procesado/transferencias.parquet \
    --memoria 2GB --temporal data/procesado/tmp

# 2) Parquet -> muestra conectada de USDC (~2.000 aristas) + etiquetas
python scripts/generar_muestra.py \
    --entrada data/procesado/transferencias.parquet \
    --salida data/muestra/transferencias_2k.csv \
    --etiquetas data/real/exchange_labels.csv \
    --salida-etiquetas data/muestra/etiquetas.csv \
    --objetivo 2000 --filas 65000 --semilla 42 \
    --token 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48 --decimales 6
```

- `transferencias.parquet` (~0,8 GB): **único archivo** que se sube a Drive/Colab.
- `data/muestra/transferencias_2k.csv` (~195 KB): muestra de referencia;
  el notebook también puede generarla desde el Parquet.
- `data/sample/`: 12 nodos para tests.

El notebook incluye las **estadísticas del dataset completo (38,9 M)** con
DuckDB. Los cuatro algoritmos se ejecutan sobre la muestra de USDC porque su
complejidad no permite ejecutarlos sobre 38,9 M en Colab.

Para el desarrollo diario y los tests usamos una **muestra mínima** (12
direcciones y 20 transferencias) que corre al instante.

## Entregables y evaluación

| Producto | Peso |
|----------|------|
| Notebook (descripción del dataset 10% + 4 tareas 60%) | 70% |
| Video (máximo 9 minutos) | 15% |
| Póster | 15% |
