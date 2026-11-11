"""
analisis.py
===========
Análisis del dataset completo y estudio de escalabilidad.

Todo se calcula a partir del **dataset real** (el Parquet que genera
`scripts/preparar_dataset.py`). No se inventan grafos: los subgrafos del
benchmark son muestras de transferencias reales.

Dos partes:

1. `estadisticas(...)`: resumen, distribuciones y tops sobre el dataset
   completo (o una cantidad configurable de filas), usando DuckDB.

2. `extraer_base(...)` + `benchmark(...)`: extrae una muestra real de aristas y
   mide cuánto tarda cada algoritmo a distintos tamaños. Sirve para mostrar,
   con datos reales, que Bellman-Ford y Louvain no escalan.

Los algoritmos siguen siendo los del proyecto (Python puro); DuckDB solo se
usa para leer y agregar los datos.
"""

from __future__ import annotations

import os
import signal
import statistics
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from typing import Callable

from src.arbol_expansion import aristas_no_dirigidas, kruskal
from src.bellman_ford import bellman_ford
from src.centralidad import pagerank
from src.comunidades import louvain, simetrizar


# ----------------------------------------------------------------------
# Utilidades de DuckDB
# ----------------------------------------------------------------------

def abrir(memoria: str | None = None, temporal: str | None = None, threads: int | None = None):
    """Abre una conexión DuckDB con ajustes para máquinas de poca RAM.

    Parámetros:
        memoria: límite de memoria, por ejemplo "2GB".
        temporal: directorio en disco para derramar datos.
        threads: número de hilos (menos hilos usan menos memoria).
    """
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "Falta duckdb. Instálalo con:\n"
            "    pip install -r requirements-datos.txt"
        ) from exc

    con = duckdb.connect()
    # No conservar el orden de inserción reduce mucho el uso de memoria.
    con.execute("SET preserve_insertion_order = false")
    if memoria:
        con.execute(f"SET memory_limit = {_texto(memoria)}")
    if threads:
        con.execute(f"SET threads = {int(threads)}")

    # DuckDB necesita un directorio temporal para poder derramar a disco.
    import tempfile
    ruta_temporal = temporal or os.path.join(tempfile.gettempdir(), "duckdb_tmp")
    os.makedirs(ruta_temporal, exist_ok=True)
    con.execute(f"SET temp_directory = {_texto(ruta_temporal)}")
    return con


def _texto(valor: str) -> str:
    """Escapa un texto para usarlo dentro de una consulta SQL."""
    return "'" + str(valor).replace("'", "''") + "'"


def _columnas(con, ruta: str) -> list[str]:
    return list(con.read_parquet(ruta).columns)


def _fuente(ruta: str, filas: int | None = None) -> str:
    base = f"read_parquet({_texto(ruta)})"
    if filas:
        return f"(SELECT * FROM {base} LIMIT {int(filas)})"
    return base


def _where(columnas: list[str], token: str | None) -> str:
    if token and "token_address" in columnas:
        return f"WHERE token_address = {_texto(token)}"
    return ""


# ----------------------------------------------------------------------
# 1. Estadísticas del dataset
# ----------------------------------------------------------------------

def estadisticas(
    con,
    ruta: str,
    filas: int | None = None,
    token: str | None = None,
) -> dict:
    """Calcula un resumen y las distribuciones principales del dataset.

    Parámetros:
        con: conexión DuckDB.
        ruta: ruta al Parquet.
        filas: si se indica, usa solo esas primeras filas (para pruebas).
        token: si se indica, filtra por `token_address`.

    Retorna un diccionario con:
        - resumen: totales y promedios.
        - valores: histograma de log10(valor).
        - grados: distribución de grados (entrada + salida).
        - top_volumen: direcciones que más volumen mueven (crudo, por token).
        - top_actividad: direcciones con más transferencias (comparable).
        - top_grado: direcciones con más conexiones.
        - tokens: conteo por token (si existe la columna).
        - actividad: transferencias por día (si existe la columna de tiempo).
    """
    columnas = _columnas(con, ruta)
    # `src` queda como una subconsulta para poder agregarle más filtros
    # (por ejemplo `WHERE value > 0`) sin repetir la cláusula WHERE.
    src = f"(SELECT * FROM {_fuente(ruta, filas)} {_where(columnas, token)})"

    total, volumen, promedio, maximo = con.execute(
        f"SELECT count(*), coalesce(sum(value), 0), "
        f"coalesce(avg(value), 0), coalesce(max(value), 0) "
        f"FROM {src}"
    ).fetchone()
    # Los distinct se hacen por separado para no mantener dos tablas hash
    # grandes al mismo tiempo en máquinas con poca RAM.
    origenes = con.execute(
        f"SELECT count(DISTINCT from_address) FROM {src}"
    ).fetchone()[0]
    destinos = con.execute(
        f"SELECT count(DISTINCT to_address) FROM {src}"
    ).fetchone()[0]

    valores = con.execute(
        f"SELECT floor(log10(value)) AS bin, count(*) AS n "
        f"FROM {src} WHERE value > 0 GROUP BY bin ORDER BY bin"
    ).fetchall()

    grados = con.execute(
        f"WITH base AS (SELECT * FROM {src}), "
        f"g AS (SELECT addr, count(*) AS grado FROM ("
        f"  SELECT from_address AS addr FROM base "
        f"  UNION ALL SELECT to_address AS addr FROM base"
        f") GROUP BY addr) "
        f"SELECT grado, count(*) AS n FROM g GROUP BY grado ORDER BY grado"
    ).fetchall()

    top_volumen = con.execute(
        f"SELECT from_address, sum(value) AS total FROM {src} "
        f"GROUP BY from_address ORDER BY total DESC LIMIT 20"
    ).fetchall()

    # Ranking por número de transferencias: es comparable entre tokens,
    # mientras que sumar `value` de tokens distintos mezcla unidades.
    top_actividad = con.execute(
        f"SELECT from_address, count(*) AS n FROM {src} "
        f"GROUP BY from_address ORDER BY n DESC LIMIT 20"
    ).fetchall()

    top_grado = con.execute(
        f"WITH base AS (SELECT * FROM {src}), "
        f"g AS (SELECT addr, count(*) AS grado FROM ("
        f"  SELECT from_address AS addr FROM base "
        f"  UNION ALL SELECT to_address AS addr FROM base"
        f") GROUP BY addr) "
        f"SELECT addr, grado FROM g ORDER BY grado DESC LIMIT 20"
    ).fetchall()

    tokens = None
    if "token_address" in columnas:
        tokens = con.execute(
            f"SELECT token_address, count(*) AS n FROM {src} "
            f"GROUP BY token_address ORDER BY n DESC LIMIT 20"
        ).fetchall()

    actividad = None
    if "block_timestamp" in columnas:
        actividad = con.execute(
            f"SELECT substr(block_timestamp, 1, 10) AS dia, count(*) AS n "
            f"FROM {src} GROUP BY dia ORDER BY dia"
        ).fetchall()
    elif "block_number" in columnas:
        # El dataset original trae número de bloque, no fecha. Convertimos a
        # una fecha aproximada usando el bloque génesis del extracto
        # (6.525.201 ≈ 2018-10-08) y ~13,5 s por bloque.
        actividad = con.execute(
            f"SELECT strftime("
            f"  to_timestamp("
            f"    epoch(TIMESTAMP '2018-10-08 00:00:00') "
            f"    + (CAST(block_number AS BIGINT) - 6525201) * 13.5"
            f"  ), '%Y-%m-%d'"
            f") AS dia, count(*) AS n "
            f"FROM {src} GROUP BY dia ORDER BY dia"
        ).fetchall()

    return {
        "resumen": {
            "transferencias": total,
            "origenes": origenes,
            "destinos": destinos,
            "volumen": float(volumen),
            "promedio": float(promedio),
            "maximo": float(maximo),
        },
        "valores": [(float(b), int(n)) for b, n in valores],
        "grados": [(int(g), int(n)) for g, n in grados],
        "top_volumen": [(a, float(v)) for a, v in top_volumen],
        "top_actividad": [(a, int(n)) for a, n in top_actividad],
        "top_grado": [(a, int(g)) for a, g in top_grado],
        "tokens": [(t, int(n)) for t, n in tokens] if tokens else None,
        "actividad": [(d, int(n)) for d, n in actividad] if actividad else None,
        "columnas": columnas,
    }


# ----------------------------------------------------------------------
# 2. Muestreo real y benchmark
# ----------------------------------------------------------------------

def extraer_base(
    con,
    ruta: str,
    max_aristas: int,
    token: str | None = None,
) -> list[tuple[str, str, float]]:
    """Extrae una muestra aleatoria real de aristas del Parquet.

    Devuelve una lista de (from_address, to_address, value). El benchmark usa
    prefijos de esta misma muestra, así todos los tamaños salen del dataset.
    """
    columnas = _columnas(con, ruta)
    where = _where(columnas, token)
    # Muestra reproducible: el benchmark debe dar los mismos tamaños en cada
    # ejecución. Si la versión de DuckDB no soporta REPEATABLE, se usa la
    # muestra aleatoria simple.
    consulta = (
        f"SELECT from_address, to_address, value "
        f"FROM (SELECT * FROM read_parquet({_texto(ruta)}) {where}) "
        f"USING SAMPLE reservoir({int(max_aristas)} ROWS) REPEATABLE (42)"
    )
    try:
        return con.execute(consulta).fetchall()
    except Exception as exc:
        if "parser" not in str(exc).lower() and "syntax" not in str(exc).lower():
            raise
        consulta = (
            f"SELECT from_address, to_address, value "
            f"FROM (SELECT * FROM read_parquet({_texto(ruta)}) {where}) "
            f"USING SAMPLE {int(max_aristas)} ROWS"
        )
        return con.execute(consulta).fetchall()


def componente_mas_grande(
    aristas: list[tuple[str, str, float]],
) -> list[tuple[str, str, float]]:
    """Conserva solo las aristas de la componente conexa (no dirigida) más grande.

    Un muestreo aleatorio deja nodos aislados. Quedarnos con la componente más
    grande hace que los algoritmos trabajen sobre una red conectada.
    """
    ady: dict[str, set[str]] = defaultdict(set)
    for a, b, _ in aristas:
        ady[a].add(b)
        ady[b].add(a)

    visitados: set[str] = set()
    mejor: set[str] = set()
    for inicio in ady:
        if inicio in visitados:
            continue
        componente: set[str] = set()
        cola = deque([inicio])
        visitados.add(inicio)
        while cola:
            nodo = cola.popleft()
            componente.add(nodo)
            for vecino in ady[nodo]:
                if vecino not in visitados:
                    visitados.add(vecino)
                    cola.append(vecino)
        if len(componente) > len(mejor):
            mejor = componente

    return [e for e in aristas if e[0] in mejor and e[1] in mejor]


def _adyacencia(aristas):
    """Construye {nodo: [(vecino, peso, indice_arista), ...]}."""
    ady = defaultdict(list)
    for indice, (a, b, w) in enumerate(aristas):
        ady[a].append((b, float(w), indice))
        ady[b].append((a, float(w), indice))
    return ady


def subgrafo_conectado(aristas, max_aristas, ady=None):
    """Extrae un subgrafo CONECTADO de hasta `max_aristas` aristas reales.

    Empieza por el nodo de mayor grado y hace un BFS, agregando las aristas
    que encuentra. Al procesar todas las aristas de cada nodo visitado, el
    subgrafo conserva ciclos (no es solo un árbol), lo que permite comparar
    Louvain y Kruskal de forma justa.

    Si se pasa `ady`, se reutiliza la adyacencia del conjunto base.
    """
    if ady is None:
        ady = _adyacencia(aristas)
    if not ady:
        return []

    inicio = max(ady, key=lambda nodo: len(ady[nodo]))
    visitados = {inicio}
    cola = deque([inicio])
    elegidas: set[int] = set()

    while cola and len(elegidas) < max_aristas:
        nodo = cola.popleft()
        for vecino, _, indice in ady[nodo]:
            if indice in elegidas:
                continue
            elegidas.add(indice)
            if len(elegidas) >= max_aristas:
                break
            if vecino not in visitados:
                visitados.add(vecino)
                cola.append(vecino)

    return [aristas[i] for i in sorted(elegidas)]


def _construir(aristas):
    adj: dict[str, list[tuple[str, float]]] = defaultdict(list)
    nodos: set[str] = set()
    for a, b, w in aristas:
        adj[a].append((b, float(w)))
        nodos.add(a)
        nodos.add(b)
    return dict(adj), nodos, [(a, b, float(w)) for a, b, w in aristas]


class _Timeout(Exception):
    pass


def _handler(signum, frame):  # pragma: no cover - depende de la señal
    raise _Timeout()


@contextmanager
def _limite(segundos: float):
    """Corta una función si tarda más de `segundos` (Linux/Colab)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return
    anterior = signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, segundos)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, anterior)


def _medir(func: Callable, timeout: float, repeticiones: int) -> float | None:
    """Devuelve la mediana de los tiempos, o None si se pasa del timeout."""
    tiempos = []
    for _ in range(repeticiones):
        try:
            with _limite(timeout):
                t0 = time.perf_counter()
                func()
                tiempos.append(time.perf_counter() - t0)
        except _Timeout:
            return None
    return statistics.median(tiempos)


def benchmark(
    aristas_base: list[tuple[str, str, float]],
    tamanos: list[int],
    repeticiones: int = 3,
    timeout: float = 30.0,
    verbose: bool = True,
) -> list[dict]:
    """Mide el tiempo de cada algoritmo a distintos tamaños reales.

    Para cada tamaño extrae un subgrafo CONECTADO del conjunto base (aristas
    reales) y corre los cuatro algoritmos.

    Si un algoritmo se pasa del timeout, se marca como `None` y **no se vuelve
    a probar en tamaños mayores** (su costo solo puede crecer). Esto evita
    repetir esperas inútiles.
    """
    resultados: list[dict] = []
    agotados: set[str] = set()
    ady_base = _adyacencia(aristas_base)

    for tamano in tamanos:
        sub = subgrafo_conectado(aristas_base, tamano, ady_base)
        adj, nodos, aristas = _construir(sub)
        n_nodos, n_aristas = len(nodos), len(aristas)
        if n_nodos == 0:
            continue

        if verbose:
            print(f"Tamaño pedido {tamano:,}: V={n_nodos:,}, E={n_aristas:,}")

        origen = max(adj, key=lambda u: len(adj[u])) if adj else next(iter(nodos))
        tareas = {
            "Bellman-Ford": lambda: bellman_ford(adj, origen),
            "PageRank": lambda: pagerank(adj, nodos),
            "Louvain": lambda: louvain(simetrizar(adj)),
            "Kruskal": lambda: kruskal(nodos, aristas_no_dirigidas(aristas)),
        }

        for nombre, func in tareas.items():
            if nombre in agotados:
                resultados.append({
                    "aristas": n_aristas, "nodos": n_nodos,
                    "algoritmo": nombre, "tiempo": None,
                })
                continue

            t = _medir(func, timeout, repeticiones)
            if t is None:
                agotados.add(nombre)
            resultados.append({
                "aristas": n_aristas, "nodos": n_nodos,
                "algoritmo": nombre, "tiempo": t,
            })
            if verbose:
                marca = "timeout" if t is None else f"{t:.3f} s"
                print(f"  {nombre:<14} {marca}")

    return resultados
