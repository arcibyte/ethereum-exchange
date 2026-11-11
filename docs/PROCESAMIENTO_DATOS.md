# Procesamiento del dataset — explicación para el profesor y el equipo

Este documento explica **qué se hizo con el dataset de Ethereum**, por qué se
transformó y cómo se usa en el proyecto. La idea es que cualquiera del equipo
(o el profesor) pueda entender el pipeline sin revisar el código.

---

## 1. Dataset original

El archivo original es `token_transfers_full.csv`:

| Dato | Valor |
|---|---|
| Tamaño | **8,3 GB** |
| Transferencias | **38.901.039** |
| Tokens ERC-20 distintos | **28** |
| Bloques | **6.525.201 → 10.000.000** |
| Periodo aproximado | octubre 2018 → abril 2020 |
| Columnas | `token_address, from_address, to_address, value, transaction_hash, log_index, block_number` |

Es el dataset completo de transferencias ERC-20. Un CSV de 8,3 GB no se puede
cargar cómodamente en Colab ni en un computador de 8 GB de RAM, y tampoco se
puede subir a GitHub.

Archivos auxiliares:

- `exchangeLabels.csv`: **296 exchanges** etiquetados (CEX y DEX).
- `alphacore_labels_stablecoin.csv`: **181 pools** de stablecoins.

---

## 2. Qué se hizo y por qué

### Paso 1 — Verificar el original

Antes de transformar nada se comprobó que el CSV tuviera:

- **38.901.039** filas de datos (más la cabecera).
- **28** tokens distintos.
- Bloques entre **6.525.201** y **10.000.000**.
- Las columnas esperadas.

### Paso 2 — Convertir el CSV a Parquet

Se usó **DuckDB** para leer el CSV una sola vez y escribir un Parquet
comprimido con ZSTD.

**¿Por qué Parquet?**

- Es un formato **columnar y comprimido**: ocupa mucho menos que el texto.
- Se puede consultar por columnas sin leer todo el archivo.
- DuckDB y pandas lo leen directamente.
- Es el formato estándar para análisis de datos grandes.

**¿Qué columnas se conservaron?**

| Columna | ¿Se conserva? | Por qué |
|---|---|---|
| `from_address` | Sí | Nodo origen del grafo |
| `to_address` | Sí | Nodo destino del grafo |
| `value` | Sí | Peso de la arista |
| `token_address` | Sí | Permite filtrar por token |
| `block_number` | Sí | Permite análisis temporal |
| `transaction_hash` | No | Identificador único; no se usa en los algoritmos |
| `log_index` | No | Índice interno; no se usa en los algoritmos |

**Resultado:**

| Dato | Valor |
|---|---|
| Archivo | `data/procesado/transferencias.parquet` |
| Tamaño | **807 MB** (antes 8,3 GB) |
| Filas | **38.901.039** (no se perdió ninguna) |
| Tokens | **28** |
| Columnas | `from_address, to_address, value, token_address, block_number` |

La reducción fue de **~10 veces**. No se muestreó ni se eliminaron
transferencias: solo se cambió el formato y se quitaron dos columnas que los
algoritmos no usan. El profesor había hablado de ~2 GB; el resultado fue aún
más liviano (~0,8 GB) sin perder filas.

### Paso 3 — Generar una muestra para los algoritmos

Los cuatro algoritmos están implementados en **Python puro**. Bellman-Ford es
$O(V \cdot E)$ y Louvain recalcula la modularidad; con 38,9 millones de aristas
no terminarían en Colab. Por eso se genera una muestra conectada.

**Cómo se generó:**

1. Se filtró **USDC** (`0xa0b8...eb48`) para no mezclar unidades de tokens
   distintos.
2. Se tomó una muestra aleatoria reproducible (`semilla=42`) de 65.000 filas.
3. Se descartaron dirección cero, auto-transferencias y valores ≤ 0.
4. Se conservó la **componente conexa más grande**.
5. Se normalizó `value` a USDC (6 decimales): `1000.30` significa 1.000,30
   USDC.

**Resultado:**

| Dato | Valor |
|---|---|
| Archivo | `data/muestra/transferencias_2k.csv` |
| Tamaño | **193 KB** |
| Aristas | **2.063** |
| Nodos | **1.371** |
| Exchanges etiquetados | **20** |
| Token | USDC |

Ventajas:

- Es una red **conectada**, no una lista de nodos aislados.
- Tiene exchanges reales (Binance, 1inch, etc.), así que los resultados son
  interpretables.
- Corre en Colab en segundos.
- Es reproducible: misma semilla y mismo Parquet → misma muestra.

### Paso 4 — Análisis del dataset completo

El dataset completo **no se descarta**. En la última sección del notebook se
consulta el Parquet de 807 MB directamente con DuckDB:

- 38.901.039 transferencias.
- Direcciones origen y destino distintas.
- Distribución de montos.
- Distribución de grados.
- Actividad por día (a partir de `block_number`).
- Top de direcciones por actividad.
- Conteo por token.
- **Benchmark de escalabilidad** con subgrafos conectados de tamaño creciente
  (1.000 → 500.000 aristas).

DuckDB lee el Parquet por partes y no lo carga entero en RAM. Por eso se puede
analizar el dataset completo sin que Colab colapse.

---

## 3. Dónde va cada archivo

| Archivo | Tamaño | ¿Dónde? | ¿Por qué? |
|---|---:|---|---|
| `token_transfers_full.csv` | 8,3 GB | Local / carpeta compartida | Es el original; no cabe en GitHub |
| `transferencias.parquet` | 807 MB | **Google Drive** | Dataset completo para el análisis |
| `transferencias_2k.csv` | 193 KB | **GitHub** | Muestra para los algoritmos |
| `etiquetas.csv` | 1,2 KB | **GitHub** | Nombres de exchanges de la muestra |
| `exchange_labels.csv` | 17 KB | **GitHub** | Etiquetas completas (296 exchanges) |

En Colab, el notebook busca el Parquet en:

```
/content/transferencias.parquet
/content/drive/MyDrive/ED2/transferencias.parquet
data/procesado/transferencias.parquet   (local)
```

---

## 4. Cómo reproducirlo

### Requisitos

```bash
pip install -r requirements-datos.txt   # duckdb + pyarrow
```

### 1) CSV → Parquet

```bash
python scripts/preparar_dataset.py convertir \
    --entrada data/raw/token_transfers_full.csv \
    --salida data/procesado/transferencias.parquet \
    --memoria 2GB \
    --temporal data/procesado/tmp
```

- `--memoria 2GB`: límite de DuckDB para no agotar la RAM.
- `--temporal`: directorio en disco para que DuckDB pueda derramar datos.

En una máquina con más RAM se puede subir el límite; en Colab también.

### 2) Parquet → muestra conectada

```bash
python scripts/generar_muestra.py \
    --entrada data/procesado/transferencias.parquet \
    --salida data/muestra/transferencias_2k.csv \
    --etiquetas data/labels/exchange_labels.csv \
    --salida-etiquetas data/muestra/etiquetas.csv \
    --objetivo 2000 \
    --filas 65000 \
    --semilla 42 \
    --token 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48 \
    --decimales 6
```

### 3) Notebook

En la Sección 1 del notebook:

```python
FUENTE = "muestra"   # usa data/muestra/transferencias_2k.csv
```

Para el análisis completo, la Sección 2 busca el Parquet automáticamente.

---

## 5. Verificación rápida

Para comprobar que el Parquet está completo:

```python
import duckdb

con = duckdb.connect()
print(con.execute("""
    SELECT count(*) AS filas,
           count(DISTINCT token_address) AS tokens,
           min(block_number) AS bloque_min,
           max(block_number) AS bloque_max
    FROM read_parquet('data/procesado/transferencias.parquet')
""").fetchone())
```

Resultado esperado:

```
(38901039, 28, 6525201, 10000000)
```

---

## 6. Decisiones y aclaraciones

- **No se muestreó el dataset completo.** El Parquet tiene las 38.901.039
  filas. La muestra de 2.063 aristas es solo para ejecutar los algoritmos en
  Python puro.
- **Se filtró USDC para los algoritmos.** Mezclar tokens con distintos
  decimales haría que los pesos no fueran comparables. El análisis completo sí
  usa los 28 tokens.
- **Los valores del Parquet están en unidades mínimas de cada token.** No se
  suman como USD entre tokens distintos. En la muestra de USDC sí están
  normalizados a USDC.
- **Hay 106.667 transferencias con `value = 0`.** Se conservan en el Parquet
  para no perder filas; los algoritmos las descartan porque un peso 0 no aporta
  al camino/MST.
- **La fecha se aproxima desde `block_number`.** Se usa el bloque 6.525.201
  como 2018-10-08 y ~13,5 segundos por bloque. Es una aproximación para la
  gráfica de actividad.
- **No se suben archivos grandes a GitHub.** GitHub tiene un límite de 100 MB
  por archivo. El Parquet de 807 MB va a Drive; el CSV original queda local.

---

## 7. Resultados que ya se pueden mostrar

Con la muestra de USDC:

- **Louvain:** $Q \approx 0,73$, entre **69 y 71 comunidades** con 5 semillas.
- **PageRank:** Binance 1 y los exchanges principales aparecen en el top.
- **Bellman-Ford:** caminos de costo mínimo desde Binance 1.
- **Kruskal:** árbol de expansión mínima con 1.370 aristas.

Con el dataset completo:

- **38.901.039** transferencias.
- **28** tokens.
- Actividad diaria entre 2018-10-07 y 2020-04-02.
- Benchmark de escalabilidad hasta **500.000 aristas**.

---

## 8. Resumen en una frase

> Convertimos el CSV de 8,3 GB en un Parquet de 807 MB con las 38,901,039
> transferencias completas, y generamos una muestra conectada de USDC de 2.063
> aristas para que los cuatro algoritmos en Python puro corran en Colab. El
> análisis descriptivo y el benchmark usan el dataset completo con DuckDB.
