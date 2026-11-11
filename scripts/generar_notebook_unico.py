import base64
import gzip
import json
import textwrap
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "notebooks" / "Proyecto_Final_Colab.ipynb"


def leer_modulo(nombre):
    texto = (RAIZ / "src" / nombre).read_text(encoding="utf-8")
    # En una celda no hace falta el future import y puede molestar.
    texto = texto.replace("from __future__ import annotations\n\n", "")
    texto = texto.replace("from __future__ import annotations\n", "")
    return texto.strip("\n")


def md(texto):
    return {
        "cell_type": "markdown",
        "id": uuid.uuid4().hex[:8],
        "metadata": {},
        "source": texto.strip("\n").splitlines(keepends=True),
    }


def code(texto):
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": uuid.uuid4().hex[:8],
        "metadata": {},
        "outputs": [],
        "source": texto.strip("\n").splitlines(keepends=True),
    }


# ---------- datos embebidos ----------
csv_bytes = (RAIZ / "data/muestra/transferencias_2k.csv").read_bytes()
b64 = base64.b64encode(gzip.compress(csv_bytes, 9)).decode("ascii")
b64 = "\n".join(textwrap.wrap(b64, 100))
etiquetas_csv = (RAIZ / "data/muestra/etiquetas.csv").read_text(encoding="utf-8")

portada = """
# Proyecto final — Red de transferencias de Ethereum

**Estructura de Datos — Universidad Industrial de Santander**

**Equipo:** Jhon Arciniegas, Pablo Álvarez y Emerson Ballesteros

---

Este notebook es **autocontenido**: incluye los datos de la muestra y el
código de los cuatro algoritmos en sus propias celdas. No necesita clonar el
repositorio ni instalar módulos del proyecto.

| Tarea | Pregunta | Algoritmo | Responsable |
|---|---|---|---|
| 1 | ¿Cuál es el camino más barato? | Bellman-Ford | Pablo Álvarez |
| 2 | ¿Qué nodos son más importantes? | Grado + PageRank | Jhon Arciniegas |
| 3 | ¿Qué grupos de nodos hay? | Louvain | Emerson Ballesteros |
| 4 | ¿Cuál es la red mínima? | Kruskal + Union-Find | Grupal |

> **Cómo ejecutar:** en Colab, ejecuta las celdas en orden. La celda de datos
> ya trae una muestra real de USDC. La última sección usa el Parquet completo
> si está disponible en Drive.
"""

capa_datos_md = """
## 0. Capa de datos: el grafo

Esta celda define la estructura compartida: un grafo dirigido y ponderado.

- **Nodos**: direcciones Ethereum.
- **Aristas**: transferencias `(from_address, to_address, value)`.
- **Peso**: cantidad transferida.

El resto de celdas usan el mismo objeto `grafo`.
"""

carga_datos = '''
# ============ DATOS DE LA MUESTRA (embebidos) ============
# La muestra está comprimida dentro del notebook para que sea autocontenido.
import base64
import csv
import gzip
import io
import math
import random

SAMPLE_B64 = """
__SAMPLE_B64__
"""

ETIQUETAS_CSV = """
__ETIQUETAS_CSV__
"""

# Decodificar la muestra
texto_csv = gzip.decompress(base64.b64decode(SAMPLE_B64)).decode("utf-8")
aristas = []
for fila in csv.DictReader(io.StringIO(texto_csv)):
    aristas.append((
        fila["from_address"].strip().lower(),
        fila["to_address"].strip().lower(),
        float(fila["value"]),
    ))

# Etiquetas
etiquetas = {}
for fila in csv.DictReader(io.StringIO(ETIQUETAS_CSV.strip())):
    etiquetas[fila["address"].strip().lower()] = {
        "nombre": fila["name"].strip(),
        "tipo": fila["type"].strip(),
    }

# Construir el grafo compartido
grafo = Grafo()
for origen, destino, peso in aristas:
    grafo._agregar_arista(origen, destino, peso)
grafo.etiquetas = etiquetas

print("Muestra cargada:")
print("  nodos :", len(grafo.nodos))
print("  aristas:", len(grafo.aristas))
print("  etiquetas:", len(grafo.etiquetas))
print("  resumen:", grafo.resumen())
'''

# Reemplazar placeholders de forma segura
carga_datos = carga_datos.replace("__SAMPLE_B64__", b64)
carga_datos = carga_datos.replace("__ETIQUETAS_CSV__", etiquetas_csv.strip("\n"))

t1_md = """
## Tarea 1 — Bellman-Ford: camino de costo mínimo

**Responsable:** Pablo Álvarez

El costo de un camino es la suma de los pesos de sus aristas. Bellman-Ford
relaja todas las aristas `|V|-1` veces y detecta ciclos negativos.

La implementación está en la celda siguiente y se prueba con la muestra.
"""

t1_demo = '''
# ============ DEMO TAREA 1 ============
from collections import Counter

salidas = Counter(origen for origen, _, _ in grafo.aristas)
etiquetados = sorted(
    (n for n in salidas if n in grafo.etiquetas),
    key=salidas.get, reverse=True,
)
origen = etiquetados[0] if etiquetados else max(salidas, key=salidas.get)

distancias, previos = bellman_ford_desde_aristas(grafo.aristas, origen)
alcanzables = sorted(
    (d, nodo) for nodo, d in distancias.items()
    if d != float("inf") and nodo != origen
)
inalcanzables = sum(1 for d in distancias.values() if d == float("inf"))

print(f"Origen: {grafo.nombre(origen)}")
print(f"Nodos alcanzables: {len(alcanzables):,}")
print(f"Nodos inalcanzables: {inalcanzables:,}\\n")
print("Los 10 destinos más baratos:")
for d, destino in alcanzables[:10]:
    camino = reconstruir_camino(previos, origen, destino)
    nombres = " -> ".join(grafo.nombre(n) for n in camino)
    print(f"  {grafo.nombre(destino):<16} costo={d:>14,.2f}  ({nombres})")
'''

t2_md = """
## Tarea 2 — Centralidad y PageRank

**Responsable:** Jhon Arciniegas

- **Grado**: número de conexiones de un nodo.
- **PageRank**: importancia según quién apunta a quién.

PageRank se calcula con iteración de potencias y factor de amortiguación
`d = 0.85`.
"""

t2_demo = '''
# ============ DEMO TAREA 2 ============
import matplotlib.pyplot as plt

cent_grado = centralidad_grado_desde_aristas(grafo.aristas)
pr = pagerank_desde_aristas(grafo.aristas)

print("Top 10 por grado:")
for _, score, nombre in top_n(cent_grado, n=10, etiquetas=grafo.etiquetas):
    print(f"  {nombre:<18} {score:.4f}")

print("\\nTop 10 por PageRank:")
top = top_n(pr, n=10, etiquetas=grafo.etiquetas)
for _, score, nombre in top:
    print(f"  {nombre:<18} {score:.4f}")

nombres = [nombre[:18] for _, _, nombre in top]
valores = [score for _, score, _ in top]
plt.figure(figsize=(8, 4))
plt.barh(nombres[::-1], valores[::-1], color="mediumpurple")
plt.xlabel("PageRank")
plt.title("Top 10 nodos por PageRank")
plt.tight_layout()
plt.show()
'''

t3_md = """
## Tarea 3 — Louvain: detección de comunidades

**Responsable:** Emerson Ballesteros

Se maximiza la modularidad:

$$Q = \\sum_c \\left[\\frac{L_c}{m} - \\left(\\frac{K_c}{2m}\\right)^2\\right]$$

- `L_c`: peso interno de la comunidad.
- `K_c`: suma de grados de la comunidad.
- `m`: peso total del grafo.

`Q > 0.3` sugiere una estructura de comunidades clara.
"""

t3_demo = '''
# ============ DEMO TAREA 3 ============
adj_no_dirigido = desde_aristas(grafo.aristas)
comunidades = louvain_desde_aristas(grafo.aristas, semilla=42)
Q = modularidad(adj_no_dirigido, comunidades)

print(f"Modularidad Q = {Q:.3f}")
print(f"Número de comunidades = {len(set(comunidades.values()))}\\n")

grupos = resumen_comunidades(comunidades, grafo.etiquetas)
for i, (c, nombres) in enumerate(
    sorted(grupos.items(), key=lambda kv: -len(kv[1]))[:10], 1
):
    muestra = ", ".join(sorted(nombres)[:5])
    if len(nombres) > 5:
        muestra += ", ..."
    print(f"Comunidad {i}: {len(nombres):>4} nodos | {muestra}")

# Estabilidad con varias semillas
print("\\nEstabilidad con 5 semillas:")
valores_q = []
for s in [1, 7, 42, 123, 2024]:
    c = louvain(adj_no_dirigido, semilla=s)
    q = modularidad(adj_no_dirigido, c)
    valores_q.append(q)
    print(f"  semilla {s:>4}: Q={q:.3f}, comunidades={len(set(c.values()))}")

plt.figure(figsize=(6, 4))
plt.bar([str(s) for s in [1, 7, 42, 123, 2024]], valores_q, color="seagreen")
plt.xlabel("Semilla")
plt.ylabel("Modularidad Q")
plt.title("Sensibilidad de Louvain a la semilla")
plt.ylim(0, 1)
plt.show()
'''

t4_md = """
## Tarea 4 — Kruskal: árbol de expansión mínima

**Responsabilidad:** grupal

Se ordenan las aristas por peso y se agregan solo si no forman un ciclo,
usando **Union-Find**. El resultado tiene `|V|-1` aristas.
"""

t4_demo = '''
# ============ DEMO TAREA 4 ============
mst, costo = kruskal_desde_aristas(grafo.aristas)
print(f"MST: {len(mst)} aristas, costo total = {costo:,.2f}\\n")
print("Primeras 20 aristas del MST:")
for a, b, w in sorted(mst, key=lambda e: e[2])[:20]:
    print(f"  {grafo.nombre(a):<18} -- {grafo.nombre(b):<18} {w:,.2f}")
'''

analisis_md = """
## 3. Análisis del dataset completo (opcional)

Si el Parquet completo está en Drive o en local, esta sección calcula
estadísticas sobre las **38.901.039 transferencias** con DuckDB, sin cargarlas
enteras en RAM.

Si no está, la celda se omite y el resto del notebook sigue funcionando.
"""

analisis_code = '''
# ============ ANÁLISIS DEL DATASET COMPLETO ============
import os
import time

RUTA_PARQUET = "/content/transferencias.parquet"
RUTA_DRIVE = "/content/drive/MyDrive/ED2/transferencias.parquet"
RUTA_LOCAL = "data/procesado/transferencias.parquet"

# En Colab, descomenta si el Parquet está en Drive:
# from google.colab import drive
# drive.mount("/content/drive")

for _ruta in (RUTA_PARQUET, RUTA_DRIVE, RUTA_LOCAL):
    if os.path.isfile(_ruta):
        RUTA_PARQUET = _ruta
        break

if not os.path.isfile(RUTA_PARQUET):
    print("Sección omitida: no encontré el Parquet completo.")
    print("Súbelo a Drive como MyDrive/ED2/transferencias.parquet.")
else:
    try:
        import duckdb
    except ImportError:
        import subprocess, sys
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "duckdb", "pyarrow"], check=True)
        import duckdb

    con = duckdb.connect()
    con.execute("SET memory_limit='2GB'")
    con.execute("SET threads=2")
    con.execute("SET preserve_insertion_order=false")

    t0 = time.perf_counter()
    r = con.execute(f"""
        SELECT count(*) filas,
               count(DISTINCT token_address) tokens,
               min(block_number) bmin,
               max(block_number) bmax
        FROM read_parquet('{RUTA_PARQUET}')
    """).fetchone()
    print(f"Transferencias : {r[0]:,}")
    print(f"Tokens         : {r[1]}")
    print(f"Bloques        : {r[2]:,} .. {r[3]:,}")
    print(f"Tiempo         : {time.perf_counter()-t0:.1f} s")

    print("\\nTop 10 tokens por transferencias:")
    for tok, n in con.execute(f"""
        SELECT token_address, count(*) n
        FROM read_parquet('{RUTA_PARQUET}')
        GROUP BY 1 ORDER BY n DESC LIMIT 10
    """).fetchall():
        print(f"  {tok}  {n:>10,}")

    print("\\nActividad mensual aproximada:")
    for mes, n in con.execute(f"""
        SELECT strftime(to_timestamp(epoch(TIMESTAMP '2018-10-08') + (block_number-6525201)*13.5), '%Y-%m') mes,
               count(*) n
        FROM read_parquet('{RUTA_PARQUET}')
        GROUP BY mes ORDER BY mes
    """).fetchall():
        print(f"  {mes}: {n:>10,}")
'''


benchmark_md = """
### 3.1 Benchmark de escalabilidad

Extraemos subgrafos conectados reales del Parquet y medimos cuánto tarda cada
algoritmo. Si uno se pasa de 15 segundos, se marca como *timeout*.

Esto muestra, con datos reales, por qué Bellman-Ford y Louvain no pueden
ejecutarse sobre las 38,9 M de aristas en Python puro.
"""

benchmark_code = '''
# ============ BENCHMARK DE ESCALABILIDAD ============
if os.path.isfile(RUTA_PARQUET):
    import signal
    from collections import defaultdict, deque

    def subgrafo_conectado(aristas, max_aristas):
        ady = defaultdict(list)
        for i, (a, b, w) in enumerate(aristas):
            ady[a].append((b, w, i))
            ady[b].append((a, w, i))
        if not ady:
            return []
        inicio = max(ady, key=lambda n: len(ady[n]))
        visitados = {inicio}
        cola = deque([inicio])
        elegidas = set()
        while cola and len(elegidas) < max_aristas:
            u = cola.popleft()
            for v, w, i in ady[u]:
                if i in elegidas:
                    continue
                elegidas.add(i)
                if len(elegidas) >= max_aristas:
                    break
                if v not in visitados:
                    visitados.add(v)
                    cola.append(v)
        return [aristas[i] for i in sorted(elegidas)]

    def construir(aristas):
        adj = defaultdict(list)
        nodos = set()
        lista = []
        for a, b, w in aristas:
            adj[a].append((b, float(w)))
            nodos.add(a)
            nodos.add(b)
            lista.append((a, b, float(w)))
        return dict(adj), nodos, lista

    class _Timeout(Exception):
        pass

    def _handler(signum, frame):
        raise _Timeout()

    def medir(func, segundos):
        if not hasattr(signal, "SIGALRM"):
            t = time.perf_counter()
            func()
            return time.perf_counter() - t
        anterior = signal.signal(signal.SIGALRM, _handler)
        signal.setitimer(signal.ITIMER_REAL, segundos)
        try:
            t = time.perf_counter()
            func()
            return time.perf_counter() - t
        except _Timeout:
            return None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, anterior)

    base = con.execute(f"""
        SELECT from_address, to_address, value
        FROM read_parquet('{RUTA_PARQUET}')
        USING SAMPLE reservoir(100000 ROWS) REPEATABLE (42)
    """).fetchall()

    tamanos = [1000, 5000, 10000, 50000, 100000]
    print(f"{'Algoritmo':<14}{'Aristas':>10}{'Nodos':>10}{'Tiempo (s)':>14}")
    for tam in tamanos:
        sub = subgrafo_conectado(base, tam)
        adj, nodos, aristas = construir(sub)
        if not nodos:
            continue
        origen = max(adj, key=lambda u: len(adj[u]))
        tareas = {
            "Bellman-Ford": lambda: bellman_ford(adj, origen),
            "PageRank": lambda: pagerank(adj, nodos),
            "Louvain": lambda: louvain(simetrizar(adj)),
            "Kruskal": lambda: kruskal(nodos, aristas_no_dirigidas(aristas)),
        }
        for nombre, func in tareas.items():
            t = medir(func, 15)
            marca = "timeout" if t is None else f"{t:.4f}"
            print(f"{nombre:<14}{len(aristas):>10,}{len(nodos):>10,}{marca:>14}")
'''

conclusiones = """
## Conclusiones

1. **Un mismo dataset admite varias preguntas.** Bellman-Ford responde
   caminos, PageRank responde importancia, Louvain responde grupos y Kruskal
   responde conectividad mínima.

2. **Las estructuras de datos importan.** La lista de adyacencia, Union-Find y
   los diccionarios hacen que los algoritmos sean simples y legibles.

3. **La escala importa.** El análisis completo usa 38,9 M de transferencias con
   DuckDB; los algoritmos en Python puro se ejecutan sobre una muestra
   conectada de USDC.

4. **La muestra no reemplaza al dataset.** El Parquet conserva las 38.901.039
   filas; la muestra es solo para que los algoritmos terminen en Colab.

5. **Todo es reproducible.** La muestra tiene semilla 42 y el pipeline está
   documentado en el repositorio.
"""

celdas = [
    md(portada),
    md(capa_datos_md),
    code(leer_modulo("grafo.py")),
    code(carga_datos),
    md(t1_md),
    code(leer_modulo("bellman_ford.py") + "\n\n" + t1_demo),
    md(t2_md),
    code(leer_modulo("centralidad.py") + "\n\n" + t2_demo),
    md(t3_md),
    code(leer_modulo("comunidades.py") + "\n\n" + t3_demo),
    md(t4_md),
    code(leer_modulo("arbol_expansion.py") + "\n\n" + t4_demo),
    md(analisis_md),
    code(analisis_code),
    md(benchmark_md),
    code(benchmark_code),
    md(conclusiones),
]

nb = {
    "cells": celdas,
    "metadata": {
        "colab": {"provenance": []},
        "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

SALIDA.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("Notebook escrito:", SALIDA)
print("Celdas:", len(celdas))
print("Tamaño:", SALIDA.stat().st_size, "bytes")
