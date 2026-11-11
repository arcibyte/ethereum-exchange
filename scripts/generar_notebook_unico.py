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


seccion1_md = "## 3. Sección 1 — Descripción y preparación del dataset\n\n**Responsable:** Pablo Álvarez\n\nEl dataset es **Ethereum Exchanges (AlphaCore)** de Stanford SNAP:\n\n| Dato | Valor |\n|---|---|\n| Contenido | 28 redes de tokens ERC-20 (una por token) |\n| Transferencias | ~38,9 millones |\n| Tamaño CSV | ~8,3 GB |\n| Periodo | 16-oct-2018 a 04-may-2020 |\n| Etiquetas | 296 exchanges: 247 `cex` y 49 `dex` |\n\nCada fila es un evento `Transfer(from, to, value)` de un contrato ERC-20.\n`value` está en la **unidad mínima de cada token**, así que no se pueden sumar\nmontos de tokens distintos.\n\n### Decisiones de modelado\n\n1. **Un grafo por token.** Mezclar USDC (6 decimales) con DAI (18) no tiene\n   sentido.\n2. **Limpieza igual a la del paper AlphaCore:**\n   - quitar valores ≤ 0;\n   - quitar “polvo”: valor < valor máximo del token / \\(10^{10}\\);\n   - quitar autolazos;\n   - conservar la dirección cero (mint/burn) y reportarla aparte.\n3. **Agregar transferencias repetidas** del mismo par en una sola arista:\n   `value` = suma, `n_transferencias` = cuántas fueron.\n\nEsta sección lee los archivos reales:\n\n```\nMi unidad/ED2/real/softchaincoin.csv\nMi unidad/ED2/real/exchange_labels.csv\n```\n\nSi no existen, la celda se detiene con un mensaje claro. SoftChainCoin es una\nred real pequeña; las tareas 1–4 usan la muestra de USDC.\n"
seccion1_code = "# ============ SECCIÓN 1: DESCRIPCIÓN Y LIMPIEZA DEL DATASET ============\nimport csv\nimport math\nfrom collections import defaultdict, deque\n\nimport matplotlib.pyplot as plt\n\nif not RUTA_SOFTCHAIN or not RUTA_LABELS:\n    print(\"Sección 1 omitida: faltan real/softchaincoin.csv y real/exchange_labels.csv.\")\n    grafo_s1 = None\nelse:\n    # Etiquetas reales de exchanges\n    exchanges = {}\n    with open(RUTA_LABELS, newline=\"\", encoding=\"latin-1\") as fh:\n        for fila in csv.DictReader(fh):\n            exchanges[fila[\"address\"].strip().lower()] = {\n                \"nombre\": fila[\"name\"].strip(),\n                \"tipo\": fila[\"type\"].strip(),\n            }\n\n    # Transferencias crudas de SoftChainCoin\n    filas = []\n    with open(RUTA_SOFTCHAIN, newline=\"\", encoding=\"utf-8\") as fh:\n        for fila in csv.DictReader(fh):\n            filas.append((\n                fila[\"from_address\"].strip().lower(),\n                fila[\"to_address\"].strip().lower(),\n                float(fila[\"value\"]),\n                int(fila[\"block_number\"]),\n            ))\n\n    # Reglas de limpieza del paper AlphaCore\n    CERO = \"0x0000000000000000000000000000000000000000\"\n    vmax = max(v for _, _, v, _ in filas)\n    umbral = vmax / 1e10\n    aristas = {}\n    reporte = {\n        \"leidas\": len(filas),\n        \"valor_cero\": 0,\n        \"polvo\": 0,\n        \"autolazos\": 0,\n        \"direccion_cero\": 0,\n        \"conservadas\": 0,\n    }\n    for origen, destino, valor, bloque in filas:\n        if valor <= 0:\n            reporte[\"valor_cero\"] += 1\n            continue\n        if valor < umbral:\n            reporte[\"polvo\"] += 1\n            continue\n        if origen == destino:\n            reporte[\"autolazos\"] += 1\n            continue\n        if origen == CERO or destino == CERO:\n            reporte[\"direccion_cero\"] += 1\n        clave = (origen, destino)\n        if clave not in aristas:\n            aristas[clave] = [0.0, 0]\n        aristas[clave][0] += valor\n        aristas[clave][1] += 1\n    reporte[\"conservadas\"] = len(aristas)\n\n    # Construir el grafo limpio de la sección 1\n    grafo_s1 = Grafo()\n    for (origen, destino), (valor, n) in aristas.items():\n        grafo_s1._agregar_arista(origen, destino, valor, limpiar=False)\n    grafo_s1.etiquetas = exchanges\n\n    print(\"SoftChainCoin — transferencias crudas:\", reporte[\"leidas\"])\n    for clave in [\"valor_cero\", \"polvo\", \"autolazos\", \"direccion_cero\"]:\n        print(f\"  {clave:<15}: {reporte[clave]:,}\")\n    print(f\"  aristas únicas : {reporte['conservadas']:,}\")\n    print(f\"  grafo          : {len(grafo_s1.nodos):,} nodos, {len(grafo_s1.aristas):,} aristas\")\n\n\n    def perfil(g):\n        \"\"\"Resumen estructural de un grafo dirigido.\"\"\"\n        n = len(g.nodos)\n        m = len(g.aristas)\n        densidad = m / (n * (n - 1)) if n > 1 else 0.0\n        pares = {(a, b) for a, b, _ in g.aristas}\n        reciprocidad = (\n            sum(1 for a, b in pares if (b, a) in pares) / len(pares) if pares else 0.0\n        )\n        ady = defaultdict(set)\n        for a, b, _ in g.aristas:\n            ady[a].add(b)\n            ady[b].add(a)\n        vistos = set()\n        componentes = 0\n        mayor = 0\n        for inicio in ady:\n            if inicio in vistos:\n                continue\n            componentes += 1\n            cola = deque([inicio])\n            vistos.add(inicio)\n            tam = 0\n            while cola:\n                u = cola.popleft()\n                tam += 1\n                for v in ady[u]:\n                    if v not in vistos:\n                        vistos.add(v)\n                        cola.append(v)\n            mayor = max(mayor, tam)\n        origenes = {a for a, _, _ in g.aristas}\n        destinos = {b for _, b, _ in g.aristas}\n        return {\n            \"nodos\": n,\n            \"aristas\": m,\n            \"densidad\": densidad,\n            \"reciprocidad\": reciprocidad,\n            \"componentes\": componentes,\n            \"componente_mayor\": mayor,\n            \"fuentes\": sum(1 for v in g.nodos if v not in destinos),\n            \"sumideros\": sum(1 for v in g.nodos if v not in origenes),\n        }\n\n\n    def grados(aristas):\n        entrada = defaultdict(int)\n        salida = defaultdict(int)\n        for a, b, _ in aristas:\n            salida[a] += 1\n            entrada[b] += 1\n        return dict(entrada), dict(salida)\n\n\n    p = perfil(grafo_s1)\n    for clave, valor in p.items():\n        texto = f\"{valor:.4f}\" if isinstance(valor, float) else f\"{valor:,}\"\n        print(f\"  {clave:<18} {texto}\")\n\n    entrada, salida = grados(grafo_s1.aristas)\n\n\n    def frecuencias(grado):\n        conteo = {}\n        for g in grado.values():\n            if g > 0:\n                conteo[g] = conteo.get(g, 0) + 1\n        return sorted(conteo.items())\n\n\n    fig, ejes = plt.subplots(1, 2, figsize=(12, 4))\n    for g, etiqueta, color in [(entrada, \"entrada\", \"steelblue\"), (salida, \"salida\", \"darkorange\")]:\n        xs, ys = zip(*frecuencias(g))\n        ejes[0].loglog(xs, ys, \"o\", label=f\"grado de {etiqueta}\", color=color, alpha=0.8)\n    ejes[0].set_xlabel(\"Grado\")\n    ejes[0].set_ylabel(\"Número de nodos\")\n    ejes[0].set_title(\"Distribución de grados (log-log)\")\n    ejes[0].legend()\n\n    montos = [v for _, _, v, _ in filas if v > 0]\n    ejes[1].hist([math.log10(v) for v in montos], bins=30, color=\"seagreen\", edgecolor=\"white\")\n    ejes[1].set_xlabel(\"log10(valor en unidad mínima del token)\")\n    ejes[1].set_ylabel(\"Frecuencia\")\n    ejes[1].set_title(\"Monto por transferencia\")\n    plt.tight_layout()\n    plt.show()\n\n    # Exchanges presentes y línea base por grado\n    presentes = {a: info for a, info in exchanges.items() if a in grafo_s1.nodos}\n    total = {v: entrada.get(v, 0) + salida.get(v, 0) for v in grafo_s1.nodos}\n\n    print()\n    print(f\"Exchanges etiquetados presentes: {len(presentes)} de {len(exchanges)}\")\n    print()\n    print(f\"{'nombre':<24}{'tipo':<6}{'entrada':>9}{'salida':>8}{'percentil':>11}\")\n    for addr in sorted(presentes, key=lambda a: -total[a]):\n        info = presentes[addr]\n        pct = 100 * sum(1 for x in total.values() if x < total[addr]) / max(1, len(total) - 1)\n        print(f\"{info['nombre'][:22]:<24}{info['tipo']:<6}{entrada.get(addr,0):>9}{salida.get(addr,0):>8}{pct:>10.1f}%\")\n\n\n    def ranking(puntajes, mayor_es_mejor=True):\n        signo = -1.0 if mayor_es_mejor else 1.0\n        return sorted(puntajes, key=lambda n: (signo * puntajes[n], n))\n\n\n    def evaluar(puntajes, relevantes, ks):\n        presentes_rel = {n for n in relevantes if n in puntajes}\n        orden = ranking(puntajes)\n        filas_eval = []\n        for k in ks:\n            enc = sum(1 for n in orden[:k] if n in presentes_rel)\n            filas_eval.append((\n                k,\n                enc,\n                enc / k if k else 0.0,\n                enc / len(presentes_rel) if presentes_rel else 0.0,\n            ))\n        return filas_eval\n\n\n    if presentes:\n        ks = [k for k in (10, 20, 50, 100) if k <= len(grafo_s1.nodos)]\n        print()\n        print(\"Línea base (precisión@k / recall@k) ordenando por grado:\")\n        print(f\"{'puntaje':<16}\" + \"\".join(f\"{'k=' + str(k):>14}\" for k in ks))\n        for nombre, puntaje in [(\"grado total\", total), (\"grado entrada\", entrada), (\"grado salida\", salida)]:\n            filas_eval = evaluar(puntaje, presentes, ks)\n            print(f\"{nombre:<16}\" + \"\".join(f\"{f[2]:>7.2f} / {f[3]:<4.2f}\" for f in filas_eval))\n    else:\n        print(\"SoftChainCoin no tiene exchanges etiquetados en esta muestra.\")\n"

carga_md = "## 2. Carga de datos\n\nEl profesor debe subir el paquete de datos a:\n\n```\nMi unidad/ED2/\n├── transferencias.parquet\n├── muestra/\n│   ├── transferencias_2k.csv\n│   └── etiquetas.csv\n└── real/\n    ├── softchaincoin.csv\n    └── exchange_labels.csv\n```\n\nLa celda busca primero esas rutas de Drive y luego `data/` en local.\n\n- Si existe `muestra/transferencias_2k.csv`, carga esa muestra.\n- Si no existe, genera la muestra de USDC desde el Parquet.\n- Si no existe el Parquet, las tareas 1–4 no pueden correr.\n- La Sección 1 necesita `real/softchaincoin.csv` y `real/exchange_labels.csv`.\n"
carga_datos = "# ============ RUTAS Y CARGA DE DATOS ============\nimport os\nfrom collections import defaultdict, deque\n\n# Carpeta del dataset en Drive y en local.\nCARPETA_DRIVE = \"/content/drive/MyDrive/ED2\"\nCARPETA_LOCAL = \"data\"\n\nUSDC = \"0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48\"\nCERO = \"0x0000000000000000000000000000000000000000\"\n\n\ndef buscar_archivo(*rutas):\n    \"\"\"Devuelve la primera ruta que exista, o None si no existe ninguna.\"\"\"\n    for ruta in rutas:\n        if ruta and os.path.isfile(ruta):\n            return ruta\n    return None\n\n\nRUTA_PARQUET = buscar_archivo(\n    f\"{CARPETA_DRIVE}/transferencias.parquet\",\n    f\"{CARPETA_DRIVE}/procesado/transferencias.parquet\",\n    f\"{CARPETA_LOCAL}/procesado/transferencias.parquet\",\n)\nRUTA_MUESTRA = buscar_archivo(\n    f\"{CARPETA_DRIVE}/muestra/transferencias_2k.csv\",\n    f\"{CARPETA_LOCAL}/muestra/transferencias_2k.csv\",\n)\nRUTA_ETIQUETAS_MUESTRA = buscar_archivo(\n    f\"{CARPETA_DRIVE}/muestra/etiquetas.csv\",\n    f\"{CARPETA_LOCAL}/muestra/etiquetas.csv\",\n)\nRUTA_SOFTCHAIN = buscar_archivo(\n    f\"{CARPETA_DRIVE}/real/softchaincoin.csv\",\n    f\"{CARPETA_LOCAL}/real/softchaincoin.csv\",\n)\nRUTA_LABELS = buscar_archivo(\n    f\"{CARPETA_DRIVE}/real/exchange_labels.csv\",\n    f\"{CARPETA_LOCAL}/real/exchange_labels.csv\",\n)\n\nprint(\"Rutas encontradas:\")\nprint(\"  Parquet          :\", RUTA_PARQUET)\nprint(\"  Muestra          :\", RUTA_MUESTRA)\nprint(\"  Etiquetas muestra:\", RUTA_ETIQUETAS_MUESTRA)\nprint(\"  SoftChainCoin    :\", RUTA_SOFTCHAIN)\nprint(\"  Etiquetas reales :\", RUTA_LABELS)\n\n\ndef componente_mayor(aristas):\n    \"\"\"Conserva solo las aristas de la componente conexa más grande.\"\"\"\n    adyacencia = defaultdict(set)\n    for origen, destino, _ in aristas:\n        adyacencia[origen].add(destino)\n        adyacencia[destino].add(origen)\n\n    visitados = set()\n    mejor = set()\n\n    for inicio in adyacencia:\n        if inicio in visitados:\n            continue\n\n        componente = set()\n        cola = deque([inicio])\n        visitados.add(inicio)\n\n        while cola:\n            nodo = cola.popleft()\n            componente.add(nodo)\n            for vecino in adyacencia[nodo]:\n                if vecino not in visitados:\n                    visitados.add(vecino)\n                    cola.append(vecino)\n\n        if len(componente) > len(mejor):\n            mejor = componente\n\n    return [\n        (origen, destino, peso)\n        for origen, destino, peso in aristas\n        if origen in mejor and destino in mejor\n    ]\n\n\ndef muestra_desde_parquet(ruta):\n    \"\"\"Genera la muestra de USDC desde el Parquet si no existe el CSV.\"\"\"\n    try:\n        import duckdb\n    except ImportError:\n        import subprocess\n        import sys\n        subprocess.run(\n            [sys.executable, \"-m\", \"pip\", \"install\", \"-q\", \"duckdb\", \"pyarrow\"],\n            check=True,\n        )\n        import duckdb\n\n    con = duckdb.connect()\n    con.execute(\"SET memory_limit='2GB'\")\n    con.execute(\"SET threads=2\")\n\n    filas = con.execute(\n        \"\"\"\n        SELECT from_address, to_address, value\n        FROM read_parquet(?)\n        WHERE token_address = ?\n        USING SAMPLE reservoir(65000 ROWS) REPEATABLE (42)\n        \"\"\",\n        [ruta, USDC],\n    ).fetchall()\n\n    aristas = []\n    for origen, destino, valor in filas:\n        origen = str(origen).lower()\n        destino = str(destino).lower()\n        valor = float(valor) / 1e6\n\n        if not origen or not destino or origen == destino:\n            continue\n        if origen == CERO or destino == CERO:\n            continue\n        if valor <= 0:\n            continue\n\n        aristas.append((origen, destino, valor))\n\n    return componente_mayor(aristas)\n\n\n# Construir el grafo de trabajo de las tareas 1-4.\nif RUTA_MUESTRA is not None:\n    grafo = cargar_grafo(RUTA_MUESTRA, etiquetas=RUTA_ETIQUETAS_MUESTRA)\n    print()\n    print(\"Grafo de trabajo: muestra preparada\")\nelif RUTA_PARQUET is not None:\n    aristas = muestra_desde_parquet(RUTA_PARQUET)\n    grafo = Grafo()\n    for origen, destino, peso in aristas:\n        grafo._agregar_arista(origen, destino, peso, limpiar=False)\n\n    if RUTA_ETIQUETAS_MUESTRA is not None:\n        grafo.cargar_etiquetas(RUTA_ETIQUETAS_MUESTRA)\n    elif RUTA_LABELS is not None:\n        grafo.cargar_etiquetas(RUTA_LABELS)\n\n    print()\n    print(\"Grafo de trabajo: muestra generada desde el Parquet\")\nelse:\n    raise FileNotFoundError(\n        \"No encontré la muestra ni el Parquet. Sube el dataset a \"\n        \"Mi unidad/ED2 o revisa las rutas.\"\n    )\n\nprint(\"  nodos    :\", len(grafo.nodos))\nprint(\"  aristas  :\", len(grafo.aristas))\nprint(\"  etiquetas:\", len(grafo.etiquetas))\nprint(\"  resumen  :\", grafo.resumen())\n"

drive_md = "## 1. Conectar con Google Drive\n\nEsta celda monta Google Drive para poder leer el dataset desde\n`Mi unidad/ED2/`. En local se salta sola.\n"
drive_code = "# ============ MONTAR GOOGLE DRIVE (COLAB) ============\ntry:\n    from google.colab import drive\n    drive.mount(\"/content/drive\")\nexcept Exception as exc:\n    print(\"Drive no disponible (normal si estás en local):\", exc)\n"

portada = """
# Proyecto final — Red de transferencias de Ethereum

**Estructura de Datos — Universidad Industrial de Santander**

**Equipo:** Jhon Arciniegas, Pablo Álvarez y Emerson Ballesteros

---

Este notebook **carga los datos desde Google Drive o desde la carpeta local
`data/`**. El profesor debe subir el paquete de datos a `Mi unidad/ED2/`.

| Tarea | Pregunta | Algoritmo | Responsable |
|---|---|---|---|
| 1 | ¿Cuál es el camino más barato? | Bellman-Ford | Pablo Álvarez |
| 2 | ¿Qué nodos son más importantes? | Grado + PageRank | Jhon Arciniegas |
| 3 | ¿Qué grupos de nodos hay? | Louvain | Emerson Ballesteros |
| 4 | ¿Cuál es la red mínima? | Kruskal + Union-Find | Grupal |

> **Cómo ejecutar:** en Colab, ejecuta las celdas en orden. Primero se monta
> Drive, después se cargan los datos. La última sección analiza el Parquet
> completo de 38,9 millones de transferencias.
"""

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
## 4. Análisis del dataset completo (opcional)

Si el Parquet completo está en Drive o en local, esta sección calcula
estadísticas sobre las **38.901.039 transferencias** con DuckDB, sin cargarlas
enteras en RAM.

Si no está, la celda se omite y el resto del notebook sigue funcionando.
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
    md(capa_datos_md),
    code(leer_modulo("grafo.py")),
    md(drive_md),
    code(drive_code),
    md(carga_md),
    code(carga_datos),
    md(seccion1_md),
    code(seccion1_code),
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
