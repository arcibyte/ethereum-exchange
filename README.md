# Red de transferencias de tokens Ethereum

Proyecto final de **Estructura de Datos** — Universidad Industrial de Santander.

**Profesor:** Jonnathan Alfredo Ramos Chaux
**Equipo:** Jhon Arciniegas, Pablo Álvarez y Emerson Ballesteros (líder)

[![Abrir en Google Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/arcibyte/ethereum-exchange/blob/main/notebooks/Proyecto_Teoria_Grafos.ipynb)

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
│   └── muestra/            <- muestra conectada real de USDC (~2.000 aristas)
│       ├── transferencias_2k.csv
│       └── etiquetas.csv
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
│   ├── Proyecto_Teoria_Grafos.ipynb      <- entregable principal (Colab)
│   └── Preparar_Dataset_Colab.ipynb      <- herramienta para procesar el CSV grande
├── scripts/
│   ├── preparar_dataset.py <- 8,3 GB -> Parquet (~0,8 GB)
│   └── generar_muestra.py  <- Parquet -> muestra conectada + etiquetas
├── docs/
│   ├── ARQUITECTURA.md     <- contrato y reglas de división
│   ├── DATASET.md          <- cómo procesar el dataset grande
│   ├── PROCESAMIENTO_DATOS.md <- qué se hizo con los datos y por qué
│   ├── guias/              <- guías de lectura por tarea
│   ├── emerson/            <- reporte y guion de la T3
│   ├── guion_video.md      <- plan del video (9 min)
│   └── poster.md           <- contenido del póster
├── requirements.txt
├── requirements-datos.txt  <- duckdb + pyarrow (solo preprocesamiento)
└── README.md
```

La división del código y las reglas para modificarlo sin romper las demás
tareas están en [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md).

## Cómo ejecutar

### Google Colab (recomendado)

1. Abre `notebooks/Proyecto_Teoria_Grafos.ipynb` en Colab.
2. Ejecuta la **celda de configuración**: clona el repositorio público y se
   ubica en su raíz.
3. Ejecuta la **celda de carga única** (Sección 1): construye una sola vez el
   grafo que usan las cuatro tareas. Por defecto usa la muestra conectada de
   ~2.000 aristas; también acepta el Parquet real.
4. Ejecuta las demás celdas en orden.

Las cuatro tareas reciben el mismo objeto `grafo`; ninguna vuelve a leer el
archivo. El análisis del dataset completo se hace aparte con DuckDB en la
Sección 2.

No hay que subir archivos ni cambiar rutas: la celda de configuración lo hace
todo.

### Local

```bash
git clone https://github.com/arcibyte/ethereum-exchange
cd ethereum-exchange

# (opcional) entorno virtual
python3 -m venv .venv && source .venv/bin/activate

pip install matplotlib jupyter
jupyter notebook notebooks/Proyecto_Teoria_Grafos.ipynb
```

La misma celda de configuración detecta la raíz del repositorio en local.

### Pruebas

```bash
pip install pytest

python -m pytest tests/ -v                    # toda la suite
python -m pytest tests/test_bellman_ford.py -v    # solo T1 (Pablo)
python -m pytest tests/test_centralidad.py -v     # solo T2 (Jhon)
python -m pytest tests/test_comunidades.py -v     # solo T3 (Emerson)
python -m pytest tests/test_arbol_expansion.py -v # solo T4 (grupo)
```

## Sobre el dataset

El dataset completo (~38,9 millones de transferencias, ~8 GB) se comparte por
Drive y **no** se sube al repositorio por su tamaño. Para trabajar con él sin
quedarnos sin memoria, lo "precargamos" en **Parquet comprimido** (~0,8 GB) y
generamos una muestra conectada para los algoritmos:

> La explicación completa del pipeline —qué se hizo con los datos, por qué,
> cómo verificarlo y dónde va cada archivo— está en
> [`docs/PROCESAMIENTO_DATOS.md`](docs/PROCESAMIENTO_DATOS.md).

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
    --etiquetas data/labels/exchange_labels.csv \
    --salida-etiquetas data/muestra/etiquetas.csv \
    --objetivo 2000 --filas 65000 --semilla 42 \
    --token 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48 --decimales 6
```

- `data/procesado/transferencias.parquet` (~0,8 GB): dataset completo, va a
  **Drive**.
- `data/muestra/transferencias_2k.csv` (~195 KB): muestra de USDC para los
  algoritmos, va a **GitHub**.
- `data/sample/`: 12 nodos para tests, va a **GitHub**.

El detalle (por qué baja de tamaño, qué tamaño usar para cada algoritmo y cómo
filtrar por token o fecha) está en [`docs/DATASET.md`](docs/DATASET.md).

El notebook incluye además una sección de **análisis extenso** con su propia
celda de configuración: estadísticas del dataset completo (38,9 M) y un
**benchmark de escalabilidad** que mide, sobre subgrafos reales de tamaño
creciente, por qué Bellman-Ford y Louvain se ejecutan sobre una muestra y
Kruskal/PageRank aguantan más. Todo sale del dataset real; no se inventan
grafos.

Para el desarrollo diario y los tests usamos una **muestra mínima** (12
direcciones y 20 transferencias) que corre al instante.

## Entregables y evaluación

| Producto | Peso |
|----------|------|
| Notebook (descripción del dataset 10% + 4 tareas 60%) | 70% |
| Video (máximo 9 minutos) | 15% |
| Póster | 15% |
