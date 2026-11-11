import json
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


seccion1_md = ""
seccion1_code = ""

carga_md = "## Cargar el dataset\n\nSube **un solo archivo**:\n\n```\ntransferencias.parquet\n```\n\nPuedes dejarlo en cualquiera de estas rutas:\n\n```\n/content/transferencias.parquet\nMi unidad/ED2/transferencias.parquet\ndata/procesado/transferencias.parquet\n```\n\nLa celda busca el archivo, genera una muestra de USDC y construye el grafo\nque usan las Tareas 1–4.\n\n> Si estás en Colab, también puedes subirlo con **Archivo → Subir** o con:\n>\n> ```python\n> # from google.colab import files\n> # files.upload()\n> ```"
carga_datos = "# ============ RUTAS Y CARGA DEL DATASET ============\nimport os\nfrom collections import defaultdict, deque\n\nCARPETA_DRIVE = \"/content/drive/MyDrive/ED2\"\nCARPETA_LOCAL = \"data\"\n\nUSDC = \"0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48\"\nCERO = \"0x0000000000000000000000000000000000000000\"\n\n\ndef buscar_archivo(*rutas):\n    \"\"\"Devuelve la primera ruta que exista, o None si no existe ninguna.\"\"\"\n    for ruta in rutas:\n        if ruta and os.path.isfile(ruta):\n            return ruta\n    return None\n\n\nRUTA_PARQUET = buscar_archivo(\n    \"/content/transferencias.parquet\",\n    f\"{CARPETA_DRIVE}/transferencias.parquet\",\n    f\"{CARPETA_LOCAL}/procesado/transferencias.parquet\",\n)\n\nprint(\"Parquet encontrado:\", RUTA_PARQUET)\n\nif RUTA_PARQUET is None:\n    raise FileNotFoundError(\n        \"No encontré transferencias.parquet. Súbelo a /content/ o a \"\n        \"Mi unidad/ED2/transferencias.parquet.\"\n    )\n\n\ndef componente_mayor(aristas):\n    \"\"\"Conserva solo las aristas de la componente conexa más grande.\"\"\"\n    adyacencia = defaultdict(set)\n    for origen, destino, _ in aristas:\n        adyacencia[origen].add(destino)\n        adyacencia[destino].add(origen)\n\n    visitados = set()\n    mejor = set()\n\n    for inicio in adyacencia:\n        if inicio in visitados:\n            continue\n\n        componente = set()\n        cola = deque([inicio])\n        visitados.add(inicio)\n\n        while cola:\n            nodo = cola.popleft()\n            componente.add(nodo)\n            for vecino in adyacencia[nodo]:\n                if vecino not in visitados:\n                    visitados.add(vecino)\n                    cola.append(vecino)\n\n        if len(componente) > len(mejor):\n            mejor = componente\n\n    return [\n        (origen, destino, peso)\n        for origen, destino, peso in aristas\n        if origen in mejor and destino in mejor\n    ]\n\n\ndef muestra_desde_parquet(ruta):\n    \"\"\"Genera una muestra de USDC desde el Parquet.\"\"\"\n    try:\n        import duckdb\n    except ImportError:\n        import subprocess\n        import sys\n        subprocess.run(\n            [sys.executable, \"-m\", \"pip\", \"install\", \"-q\", \"duckdb\", \"pyarrow\"],\n            check=True,\n        )\n        import duckdb\n\n    con = duckdb.connect()\n    con.execute(\"SET memory_limit='2GB'\")\n    con.execute(\"SET threads=2\")\n\n    filas = con.execute(\n        \"\"\"\n        SELECT from_address, to_address, value\n        FROM read_parquet(?)\n        WHERE token_address = ?\n        USING SAMPLE reservoir(65000 ROWS) REPEATABLE (42)\n        \"\"\",\n        [ruta, USDC],\n    ).fetchall()\n\n    aristas = []\n    for origen, destino, valor in filas:\n        origen = str(origen).lower()\n        destino = str(destino).lower()\n        valor = float(valor) / 1e6\n\n        if not origen or not destino or origen == destino:\n            continue\n        if origen == CERO or destino == CERO:\n            continue\n        if valor <= 0:\n            continue\n\n        aristas.append((origen, destino, valor))\n\n    return componente_mayor(aristas)\n\n\naristas = muestra_desde_parquet(RUTA_PARQUET)\n\ngrafo = Grafo()\nfor origen, destino, peso in aristas:\n    grafo._agregar_arista(origen, destino, peso, limpiar=False)\n\nprint(\"Muestra generada desde el Parquet:\")\nprint(\"  nodos   :\", len(grafo.nodos))\nprint(\"  aristas :\", len(grafo.aristas))\nprint(\"  resumen :\", grafo.resumen())"

drive_md = "## 1. Conectar con Google Drive\n\nEsta celda monta Google Drive para poder leer el dataset desde\n`Mi unidad/ED2/`. En local se salta sola.\n"
drive_code = "# ============ MONTAR GOOGLE DRIVE (COLAB) ============\ntry:\n    from google.colab import drive\n    drive.mount(\"/content/drive\")\nexcept Exception as exc:\n    print(\"Drive no disponible (normal si estás en local):\", exc)\n"

portada = """
# Proyecto final — Red de transferencias de Ethereum

**Estructura de Datos — Universidad Industrial de Santander**

**Equipo:** Jhon Arciniegas, Pablo Álvarez y Emerson Ballesteros

---

Este notebook usa **un solo dataset**:

```
transferencias.parquet
```

El profesor lo sube y el notebook hace todo lo demás:

1. Analiza las 38,9 M de transferencias con DuckDB.
2. Genera una muestra conectada de USDC.
3. Ejecuta las cuatro tareas con estructuras de datos básicas.
4. Explica la teoría y la complejidad de cada algoritmo.

| Tarea | Pregunta | Algoritmo | Responsable |
|---|---|---|---|
| 1 | ¿Cuál es el camino más barato? | Bellman-Ford | Pablo Álvarez |
| 2 | ¿Qué nodos son más importantes? | Grado + PageRank | Jhon Arciniegas |
| 3 | ¿Qué grupos de nodos hay? | Louvain | Emerson Ballesteros |
| 4 | ¿Cuál es la red mínima? | Kruskal + Union-Find | Grupal |

> **Cómo ejecutar:** sube `transferencias.parquet`, ejecuta las celdas en
> orden y listo. No necesitas clonar el repositorio ni instalar módulos.
"""

teoria_md = "## Teoría: grafos y estructuras de datos\n\nUn **grafo** tiene nodos y aristas. En este proyecto:\n\n- **Nodo**: una dirección de Ethereum.\n- **Arista**: una transferencia de una dirección a otra.\n- **Peso**: la cantidad transferida.\n\nEl grafo es **dirigido** (A → B no es lo mismo que B → A) y **ponderado**.\n\n### Estructuras de datos que usamos\n\n| Estructura | Dónde se usa | Para qué |\n|---|---|---|\n| **Lista de adyacencia** (`dict` de listas) | T1, T2, T3 | recorrer los vecinos de un nodo |\n| **Diccionario** | T1, T2, T3 | guardar distancias, puntajes y comunidades |\n| **Conjunto** (`set`) | T2, T3 | nodos visitados y comunidades vecinas |\n| **Cola** (`deque`) | T1, T3 | recorrer por niveles y encontrar componentes |\n| **Lista de aristas** | T4 | ordenar las aristas por peso |\n| **Union-Find** | T4 | detectar ciclos en Kruskal |\n\nLa idea es simple: **cada algoritmo usa la estructura que le permite hacer su trabajo sin recorrer el grafo de más**."

capa_datos_md = """
## 0. Capa de datos: el grafo

Esta celda define la estructura compartida: un grafo dirigido y ponderado.

- **Nodos**: direcciones Ethereum.
- **Aristas**: transferencias `(from_address, to_address, value)`.
- **Peso**: cantidad transferida.

El resto de celdas usan el mismo objeto `grafo`.
"""

t1_md = """
## Tarea 1 — Bellman-Ford: camino de costo mínimo

**Responsable:** Pablo Álvarez

**Estructura de datos:** lista de adyacencia + diccionario de distancias.

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

**Estructura de datos:** lista de adyacencia + diccionario de puntajes.

- **Grado**: número de conexiones de un nodo.
- **PageRank**: importancia según quién apunta a quién.

PageRank se calcula con iteración de potencias y factor de amortiguación
`d = 0.85`.

La gráfica del top 5 y las validaciones de esta sección fueron aportadas por
Jhon Arciniegas (T2).
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
for _, score, nombre in top_n(pr, n=10, etiquetas=grafo.etiquetas):
    print(f"  {nombre:<18} {score:.4f}")

# Gráfica y validaciones aportadas por Jhon Arciniegas (T2).
top_pr = top_n(pr, n=5, etiquetas=grafo.etiquetas)
nombres_pr = [nombre for _, _, nombre in top_pr]
scores_pr = [score for _, score, _ in top_pr]

plt.figure(figsize=(7, 4))
plt.barh(nombres_pr[::-1], scores_pr[::-1], color="steelblue")
plt.xlabel("PageRank")
plt.title("Top 5 direcciones por PageRank")
plt.tight_layout()
plt.show()

# Validaciones de centralidad (mismas que tests/test_centralidad.py).
assert centralidad_grado({"A": []}, {"A"})["A"] == 0.0
assert pagerank({}, set()) == {}
assert top_n({"A": 0.5, "B": 0.3}, n=2)[0][0] == "A"
print("Validaciones de centralidad: OK")
'''

t3_md = r"""
## Tarea 3 — Louvain: detección de comunidades

**Responsable:** Emerson Ballesteros

### Antes del código: ¿qué es una comunidad?

Imagina cuatro direcciones:

```
Ana   <--> Beto     (se transfieren mucho)
Carla <--> Dani     (se transfieren mucho)
Beto  -->  Carla    (se transfieren poquito)
```

Hay dos grupos naturales: `{Ana, Beto}` y `{Carla, Dani}`. Louvain intenta
encontrar esos grupos automáticamente, sin que le digamos cuántos hay.

### ¿Qué mide la modularidad Q?

Q compara las aristas que quedan **dentro** de los grupos con las que
aparecerían si las conexiones fueran al azar. Si hay más conexiones internas
de las esperadas, Q sube.

$$Q = \sum_c \left[\frac{L_c}{m} - \left(\frac{K_c}{2m}\right)^2\right]$$

- `L_c`: peso de las aristas internas de la comunidad `c`.
- `K_c`: suma de grados de los nodos de `c`.
- `m`: peso total del grafo.
- `Q > 0.3` sugiere una estructura de comunidades clara.
- `Q = 0` significa que la partición no es mejor que el azar.

### Paso a paso del algoritmo

1. Cada nodo empieza en su propia comunidad.
2. Se recorre la lista de nodos en orden aleatorio.
3. Para cada nodo, se prueba moverlo a la comunidad de cada vecino.
4. Se acepta el movimiento solo si Q aumenta.
5. Cuando una pasada completa no cambia nada, el algoritmo termina.

### Cómo leer el código

| Función | Qué hace |
|---|---|
| `simetrizar` | convierte el grafo dirigido en no dirigido |
| `calcular_grados` | suma los pesos de las aristas de cada nodo |
| `modularidad` | calcula Q de una partición |
| `louvain` | hace las pasadas y mueve los nodos |
| `desde_aristas` | construye el grafo no dirigido desde `grafo.aristas` |
| `louvain_desde_aristas` | atajo: construye el grafo y ejecuta Louvain |
| `renumerar_comunidades` | cambia los IDs por 0, 1, 2, ... para leerlos mejor |

### Qué mirar en los resultados

- Los **IDs de comunidad son arbitrarios**: la comunidad 0 no es mejor que la 5.
- Lo importante es **Q**, el **tamaño** de las comunidades y **qué exchanges**
  quedan juntos.
- Louvain es **heurístico**: dos semillas pueden dar particiones parecidas
  pero no idénticas.

### Limitaciones y posibles mejoras

- Esta versión recalcula Q completo en cada prueba: es fácil de leer, pero lenta.
- No incluye la fase de agregación de Louvain.
- Puede sufrir el límite de resolución: comunidades muy pequeñas pueden pasar
  desapercibidas.
- Mejoras: calcular ΔQ incremental, agregar la fase de agregación, probar
  varias semillas y comparar con Label Propagation o `python-louvain`.
"""

t3_demo = '''
# ============ TAREA 3: LOUVAIN ============
# Paso 1: construir el grafo no dirigido.
adj_no_dirigido = desde_aristas(grafo.aristas)

cantidad_nodos = len(adj_no_dirigido)
cantidad_aristas = 0
for vecinos in adj_no_dirigido.values():
    cantidad_aristas += len(vecinos)
cantidad_aristas = cantidad_aristas // 2

print("Grafo no dirigido:")
print(f"  nodos   : {cantidad_nodos:,}")
print(f"  aristas : {cantidad_aristas:,}")

# Paso 2: ejecutar Louvain con una semilla fija.
comunidades = louvain(adj_no_dirigido, semilla=42)

# Renumerar 0, 1, 2, ... para que sea más fácil leer los resultados.
comunidades = renumerar_comunidades(comunidades)

# Paso 3: medir la calidad de la partición.
Q = modularidad(adj_no_dirigido, comunidades)

print()
print(f"Modularidad Q = {Q:.3f}")
print(f"Número de comunidades = {len(set(comunidades.values())):,}")

# Paso 4: mostrar las comunidades más grandes.
grupos = resumen_comunidades(comunidades, grafo.etiquetas)

print()
print("Comunidades más grandes:")
for posicion, (id_comunidad, nombres) in enumerate(
    sorted(grupos.items(), key=lambda par: -len(par[1]))[:10],
    start=1,
):
    primeros = ", ".join(sorted(nombres)[:5])
    if len(nombres) > 5:
        primeros += ", ..."
    print(f"  Comunidad {posicion:>2}: {len(nombres):>4} nodos | {primeros}")

# Paso 5: ver en qué comunidad cae cada exchange etiquetado.
print()
print("Comunidad de cada exchange etiquetado:")
for direccion, info in sorted(
    grafo.etiquetas.items(), key=lambda par: par[1]["nombre"]
):
    if direccion not in comunidades:
        continue
    id_comunidad = comunidades[direccion]
    tamano = len(grupos[id_comunidad])
    print(f"  {info['nombre']:<18} comunidad {id_comunidad:>3} ({tamano} nodos)")
'''

t3_exp_md = """
### Experimento: ¿qué pasa si cambiamos la semilla?

Louvain es un algoritmo **heurístico**: el orden en que prueba los nodos
puede cambiar el resultado. Por eso se repite con varias semillas y se mira
si Q se mantiene estable.
"""

t3_exp_code = '''
# ============ EXPERIMENTO: ESTABILIDAD CON SEMILLAS ============
import matplotlib.pyplot as plt

semillas = [1, 7, 42, 123, 2024]
resultados = []

for semilla in semillas:
    comunidades_semilla = louvain(adj_no_dirigido, semilla=semilla)
    q = modularidad(adj_no_dirigido, comunidades_semilla)
    cuantas = len(set(comunidades_semilla.values()))
    resultados.append((semilla, q, cuantas))

print(f"{'Semilla':>8} {'Q':>8} {'Comunidades':>12}")
print("-" * 32)
for semilla, q, cuantas in resultados:
    print(f"{semilla:>8} {q:>8.3f} {cuantas:>12}")

mejor = max(resultados, key=lambda fila: fila[1])
print()
print(f"Mejor semilla: {mejor[0]} con Q = {mejor[1]:.3f}")

plt.figure(figsize=(6, 4))
plt.bar(
    [str(fila[0]) for fila in resultados],
    [fila[1] for fila in resultados],
    color="seagreen",
)
plt.xlabel("Semilla")
plt.ylabel("Modularidad Q")
plt.title("Sensibilidad de Louvain a la semilla")
plt.ylim(0, 1)
plt.show()
'''

t4_md = """
## Tarea 4 — Kruskal: árbol de expansión mínima

**Responsabilidad:** grupal

**Estructura de datos:** lista de aristas + Union-Find.

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
## Estadísticas del dataset completo

Esta sección sí usa las **38.901.039 transferencias**. DuckDB lee el Parquet
por columnas y calcula los totales sin cargar todo en RAM.
"""

analisis_code = '''
# ============ ANÁLISIS DEL DATASET COMPLETO ============
import os
import time

if not RUTA_PARQUET:
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
### 4.1 Benchmark de escalabilidad

Extraemos subgrafos conectados reales del Parquet y medimos cuánto tarda cada
algoritmo. Si uno se pasa de 15 segundos, se marca como *timeout*.

Esto muestra, con datos reales, por qué Bellman-Ford y Louvain no pueden
ejecutarse sobre las 38,9 M de aristas en Python puro.

> Requiere haber ejecutado antes las celdas de las tareas 1–4: allí se definen
> las funciones de los cuatro algoritmos.
"""

benchmark_code = '''
# ============ BENCHMARK DE ESCALABILIDAD ============
if RUTA_PARQUET and os.path.isfile(RUTA_PARQUET):
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
    md(teoria_md),
    md(capa_datos_md),
    code(leer_modulo("grafo.py")),
    md(drive_md),
    code(drive_code),
    md(carga_md),
    code(carga_datos),
    md(t1_md),
    code(leer_modulo("bellman_ford.py") + "\n\n" + t1_demo),
    md(t2_md),
    code(leer_modulo("centralidad.py") + "\n\n" + t2_demo),
    md(t3_md),
    code(leer_modulo("comunidades.py") + "\n\n" + t3_demo),
    md(t3_exp_md),
    code(t3_exp_code),
    md(t4_md),
    code(leer_modulo("arbol_expansion.py") + "\n\n" + t4_demo),
    md(analisis_md),
    code(analisis_code),
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
