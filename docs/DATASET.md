# Dataset: cómo pasar de 8 GB a una muestra usable

> **Sección 1 del notebook.** Para el resumen de los 28 tokens y las aristas
> limpias de un token (la entrada de las tareas 1-4) se usa
> `scripts/preparar_seccion1.py`, que solo necesita la librería estándar y
> aplica las reglas de limpieza de los autores del dataset. Los comandos están
> en el README (sección "Sección 1: preparar los datos reales"). Este documento
> describe la herramienta de Parquet/DuckDB, que sigue disponible para el
> análisis extenso.

El dataset completo de transferencias pesa **~8 GB** y no cabe cómodamente en
memoria (Colab da ~12 GB y esta máquina tiene 11 GB). Además, los algoritmos
del proyecto son de Python puro y no están pensados para millones de aristas.

La solución tiene dos partes:

1. **Precargar** el CSV en **Parquet comprimido** (~2.3 GB).
2. **Muestrear** un subgrafo manejable para ejecutar los algoritmos.

El preprocesamiento usa `duckdb` (solo para datos). **Los algoritmos siguen
siendo Python puro** y no dependen de ninguna librería externa.

## ¿Por qué baja de 8 GB a 2.3 GB?

El CSV guarda todo como texto. Parquet guarda columnas en binario y las
comprime con ZSTD. Las direcciones hexadecimales se repiten mucho, así que
comprimen muy bien. Una reducción de 3 a 4 veces es lo normal: **8 GB → ~2.3 GB**.

## Instalar las dependencias de datos

```bash
pip install -r requirements-datos.txt
```

## 1. Convertir el CSV completo a Parquet

```bash
python scripts/preparar_dataset.py convertir \
    --entrada /ruta/al/transferencias.csv \
    --salida data/procesado/transferencias.parquet
```

El script **detecta solo** las columnas. Acepta nombres como
`from_address`/`from`/`sender`, `to_address`/`to`/`receiver` y
`value`/`amount`. Si existen `token_address` y `block_timestamp`, los conserva
para poder filtrar después sin volver a leer el CSV.

## 2. Generar una muestra para el notebook

```bash
python scripts/preparar_dataset.py muestra \
    --entrada data/procesado/transferencias.parquet \
    --salida data/muestra/transferencias_100k.csv \
    --filas 100000 --componente
```

Opciones útiles:

| Opción | Para qué sirve |
|--------|----------------|
| `--filas N` | cuántas transferencias conservar (después de filtrar) |
| `--token 0x...` | analizar un solo token ERC-20 |
| `--desde` / `--hasta` | ventana de tiempo (texto ISO, ej. `2024-01-01`) |
| `--componente` | conservar solo la componente conexa más grande |

`--componente` es importante: un muestreo aleatorio deja muchos nodos
aislados. Quedarse con la componente más grande produce una red conectada y
resultados interpretables.

## 3. Ver estadísticas

```bash
python scripts/preparar_dataset.py info \
    --entrada data/procesado/transferencias.parquet
```

## ¿Qué tamaño usar?

| Uso | Tamaño recomendado | Por qué |
|-----|--------------------|---------|
| Tests y demo rápida | 12 nodos / 20 aristas (`data/sample/`) | corre al instante |
| Notebook (algoritmos) | **V ≤ 2 000, E ≤ 5 000** | Bellman-Ford es `O(V·E)`; Louvain recalcula `Q` |
| Estadísticas del dataset | 100 000–1 000 000 de filas | solo se consultan con DuckDB, no se corren algoritmos |

Regla práctica: Bellman-Ford hace `V · E` operaciones. Con `V = 2 000` y
`E = 5 000` son ~10 millones, aceptable. Con `V = 50 000` y `E = 200 000` son
~10 000 millones: no termina.

Por eso el notebook usa una muestra para los algoritmos y, si se quiere,
DuckDB para describir el dataset completo.

## En Colab con Drive (recomendado)

Si el CSV está en Google Drive, abre
[`notebooks/Preparar_Dataset_Colab.ipynb`](../notebooks/Preparar_Dataset_Colab.ipynb).
Ese notebook:

1. monta Drive,
2. clona el repositorio e instala `requirements-datos.txt`,
3. convierte el CSV a Parquet,
4. muestra estadísticas,
5. genera la muestra en `data/muestra/`.

Solo hay que cambiar `RUTA_CSV` por la ruta real del archivo en Drive.

## Análisis extenso (benchmark de escalabilidad)

El notebook principal trae una sección **"Análisis extenso del dataset
completo"** con su celda de configuración:

```python
RUTA_PARQUET = "/content/transferencias.parquet"
FILAS_ANALISIS = None          # None = todo el Parquet
TAMANOS = [1_000, 5_000, 10_000, 25_000, 50_000, 100_000]
REPETICIONES = 3
TIMEOUT_SEG = 30
TOKEN = None
```

| Parámetro | Qué controla |
|-----------|--------------|
| `FILAS_ANALISIS` | cuántas filas usar para las estadísticas |
| `TAMANOS` | cuántas aristas reales extraer en cada medición |
| `REPETICIONES` | repeticiones por medición (se usa la mediana) |
| `TIMEOUT_SEG` | si un algoritmo tarda más, se marca como *timeout* |
| `TOKEN` | analizar un solo token |

Todo sale del **Parquet real**: el benchmark extrae una muestra de
transferencias y toma prefijos de tamaño creciente. **No se generan grafos
sintéticos.**

Para un análisis más largo, sube `TAMANOS` (por ejemplo, hasta 500 000) y
`TIMEOUT_SEG`. Si Colab va lento, bájalos.

La sección produce:
- resumen del dataset (transferencias, direcciones, volumen);
- distribución de montos (log10);
- distribución de grados (log-log);
- actividad por día (si hay `block_timestamp`);
- top 10 direcciones por volumen;
- tabla y gráfica log-log del tiempo vs. tamaño de cada algoritmo.

## Usarlo en el notebook

En la celda de imports, cambia la ruta:

```python
# RUTA_TRANSFERENCIAS = "data/sample/transferencias.csv"      # muestra mínima
RUTA_TRANSFERENCIAS = "data/muestra/transferencias_100k.csv"  # muestra mediana
```

En **Colab**, si el Parquet está en Drive:

```python
from google.colab import drive
drive.mount("/content/drive")
```

y apunta `--entrada` / `--salida` a `/content/drive/MyDrive/...`.

## Archivos que no se suben a Git

`.gitignore` excluye `data/procesado/` y `*.parquet` porque pesan demasiado.
La muestra mediana (`data/muestra/`) sí se puede versionar si pesa poco
(alrededor de 10–20 MB).
