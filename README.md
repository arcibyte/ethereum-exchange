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
│   ├── real/               <- datos REALES pequeños (ver data/real/FUENTE.md)
│   │   ├── exchange_labels.csv <- 296 exchanges (247 cex, 49 dex)
│   │   └── softchaincoin.csv   <- red real de SoftChainCoin
│   ├── labels/             <- etiquetas completas de exchanges
│   ├── resumen/            <- resumen de los 28 tokens (lo genera la sección 1)
│   └── tokens/             <- aristas limpias por token: entrada de T1-T4
├── src/                    <- nuestros algoritmos (Python puro)
│   ├── grafo.py            <- COMPARTIDO: carga única (CSV/Parquet)
│   ├── dataset.py          <- sección 1 (Pablo): lectura, limpieza, perfil
│   ├── evaluacion.py       <- COMPARTIDO: precisión@k contra etiquetas
│   ├── bellman_ford.py     <- tarea 1 (Pablo)
│   ├── centralidad.py      <- tarea 2 (Jhon)
│   ├── comunidades.py      <- tarea 3 (Emerson)
│   └── arbol_expansion.py  <- tarea 4 (grupo)
├── tests/                  <- un archivo de pruebas por dueño
│   ├── conftest.py
│   ├── test_dataset.py
│   ├── test_evaluacion.py
│   ├── test_bellman_ford.py
│   ├── test_centralidad.py
│   ├── test_comunidades.py
│   ├── test_arbol_expansion.py
│   ├── test_grafo.py
│   └── test_datos.py
├── notebooks/
│   ├── Proyecto_Final_Colab.ipynb     <- ENTREGABLE único (autocontenido)
│   ├── Proyecto_Teoria_Grafos.ipynb   <- versión modular para desarrollo
│   └── Preparar_Dataset_Colab.ipynb   <- herramienta para procesar el CSV grande
├── scripts/
│   ├── preparar_dataset.py <- 8,3 GB -> Parquet (~0,8 GB)
│   ├── generar_muestra.py  <- Parquet -> muestra conectada + etiquetas
│   └── preparar_seccion1.py <- resumen por token y aristas limpias (stdlib)
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

### Google Colab — entregable

El entregable es **un solo notebook**:

```
notebooks/Proyecto_Final_Colab.ipynb
```

Es **autocontenido**: incluye la muestra de datos y el código de los cuatro
algoritmos en sus propias celdas. No necesita clonar el repositorio ni
instalar módulos del proyecto.

1. Abre `notebooks/Proyecto_Final_Colab.ipynb` en Colab.
2. Ejecuta las celdas en orden.
3. La sección final usa el Parquet completo si está en Drive
   (`Mi unidad/ED2/transferencias.parquet`); si no está, se omite.

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
python -m pytest tests/test_dataset.py -v         # solo sección 1 (Pablo)
python -m pytest tests/test_bellman_ford.py -v    # solo T1 (Pablo)
python -m pytest tests/test_centralidad.py -v     # solo T2 (Jhon)
python -m pytest tests/test_comunidades.py -v     # solo T3 (Emerson)
python -m pytest tests/test_arbol_expansion.py -v # solo T4 (grupo)
```

## Sección 1: preparar los datos reales

La sección 1 del notebook corre sin descargar nada: usa las etiquetas reales y
la red real de SoftChainCoin que vienen en `data/real/`. Para describir los 28
tokens del dataset y analizar uno de ellos, se generan **una sola vez** dos
archivos pequeños a partir del CSV completo y se suben al repositorio:

```bash
# 1) Resumen de los 28 tokens (una pasada, ~4 min y 2-3 GB de RAM; --sin-distintos usa poca RAM)
python scripts/preparar_seccion1.py resumen --entrada /ruta/token_transfers_full.csv

# 2) Aristas limpias del token elegido (entrada de las tareas 1-4)
python scripts/preparar_seccion1.py exportar --entrada /ruta/token_transfers_full.csv \
    --token 0x... --resumen data/resumen/tokens.csv --salida data/tokens/<nombre>.csv
```

Solo usa la librería estándar. Las reglas de limpieza son las mismas de los
autores del dataset; están explicadas en la sección 1.2 del notebook.

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
