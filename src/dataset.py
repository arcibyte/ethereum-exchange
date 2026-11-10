"""
dataset.py
==========
Sección 1 — Descripción y preparación del dataset.

Responsable: Pablo Álvarez.

Dataset: "Ethereum Exchanges (AlphaCore)" de Stanford SNAP
(https://snap.stanford.edu/data/ethereum-exchanges.html).

    - 28 redes de tokens ERC-20 (una por token), extraídas de Ethereum
      entre el 16-oct-2018 y el 04-may-2020.
    - Cada fila es una transferencia: token_address, from_address,
      to_address, value, block_number (y otras columnas que se ignoran).
    - Etiquetas: 296 direcciones de exchanges (CEX y DEX), obtenidas de
      Etherscan en mayo de 2020.

Decisiones de modelado que este módulo fija para TODAS las tareas:

    1. Un grafo POR TOKEN. `value` está en la unidad mínima de cada token
       (cada token tiene sus propios decimales y su propio precio), así que
       sumar valores de tokens distintos no tiene sentido.
    2. Limpieza igual a la de los autores del dataset (función `getGraph` del
       repositorio github.com/friedhelmvictor/alphacore):
         - se descartan transferencias con valor <= 0;
         - se descartan las de "polvo": valor < valor_max_del_token / 1e10.
       Además quitamos los autolazos (origen == destino), que no aportan a
       ningún algoritmo de la materia.
    3. Las transferencias repetidas entre el mismo par se AGREGAN en una sola
       arista: value = suma de valores, n_transferencias = cuántas fueron.
    4. La dirección 0x000...000 se conserva por defecto (los autores también
       la conservan) pero se reporta aparte: desde ella se crean tokens
       (mint) y hacia ella se destruyen (burn); no es un exchange.

El archivo de aristas limpias que produce `guardar_aristas` tiene las
columnas `from_address, to_address, value, n_transferencias`, así que
`Grafo.cargar_transferencias` lo lee sin cambios: es el punto de contacto
entre esta sección y las tareas 1-4.

Solo se usa la librería estándar de Python.
"""

import csv
import math
import re
from collections import defaultdict, deque
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple

# ----------------------------------------------------------------------
# Constantes del dataset
# ----------------------------------------------------------------------

DIRECCION_CERO = "0x0000000000000000000000000000000000000000"

# Umbral de "polvo" de los autores: valor < valor_max / FACTOR_POLVO.
FACTOR_POLVO = 1e10

# Nombres de columna aceptados (en minúsculas). El primero es el oficial del
# dataset; los demás permiten leer otros exports, como el de SoftChainCoin del
# repositorio de AlphaCore (source, target, amount, blockNumber).
ALIAS_COLUMNAS = {
    "token": ("token_address", "contract_address", "token"),
    "origen": ("from_address", "source", "from", "sender"),
    "destino": ("to_address", "target", "to", "receiver"),
    "valor": ("value", "amount"),
    "bloque": ("block_number", "blocknumber", "block"),
}

# Una transferencia normalizada:
#   (token, origen, destino, valor, bloque)
# valor es None si el texto no se pudo convertir a número.
# bloque es None si el archivo no trae esa columna.
Transferencia = Tuple[str, str, str, Optional[float], Optional[int]]

# Aristas agregadas: {(origen, destino): [suma_valor, n_transferencias]}
Aristas = Dict[Tuple[str, str], List[float]]

# Columnas del resumen por token, en el orden en que se guardan.
COLUMNAS_RESUMEN = [
    "token_address", "transferencias", "valor_invalido", "valor_cero",
    "autolazos", "mint", "burn", "valor_max", "bloque_min", "bloque_max",
    "direcciones", "pares", "exchanges_presentes", "cex_presentes",
    "dex_presentes",
]


# ----------------------------------------------------------------------
# Lectura
# ----------------------------------------------------------------------

def _indices(encabezado: List[str]) -> Dict[str, Optional[int]]:
    """Ubica cada dato en el encabezado usando los alias aceptados."""
    normal = [c.strip().lower() for c in encabezado]
    indices: Dict[str, Optional[int]] = {}
    for dato, alias in ALIAS_COLUMNAS.items():
        indices[dato] = next((normal.index(a) for a in alias if a in normal), None)
    faltan = [d for d in ("origen", "destino", "valor") if indices[d] is None]
    if faltan:
        raise ValueError(
            f"Al CSV le faltan columnas para: {', '.join(faltan)}. "
            f"Encabezado leído: {encabezado}"
        )
    return indices


def _a_numero(texto: str) -> Optional[float]:
    """Convierte el valor (uint256 en texto) a float. None si no es número.

    Un uint256 puede tener hasta 78 dígitos; float conserva ~15 cifras
    significativas, suficiente para comparar y sumar montos de un mismo token.
    """
    try:
        valor = float(texto)
    except (TypeError, ValueError):
        return None
    return valor if math.isfinite(valor) else None


def leer_transferencias(
    ruta_csv: str,
    token: Optional[str] = None,
    token_por_defecto: str = "sin_token",
) -> Iterator[Transferencia]:
    """Recorre un CSV de transferencias fila por fila, sin cargarlo en memoria.

    Parámetros:
        ruta_csv: archivo con las transferencias (sirve para el CSV completo
            de ~8 GB porque se lee en streaming).
        token: si se indica, solo devuelve las filas de ese token.
        token_por_defecto: token que se asigna si el archivo no trae la
            columna `token_address` (por ejemplo, un archivo de un solo token).

    Produce tuplas (token, origen, destino, valor, bloque), con las
    direcciones en minúsculas.
    """
    filtro = token.strip().lower() if token else None
    with open(ruta_csv, newline="", encoding="utf-8") as archivo:
        lector = csv.reader(archivo)
        encabezado = next(lector, None)
        if encabezado is None:
            return
        idx = _indices(encabezado)
        i_tok, i_ori, i_des = idx["token"], idx["origen"], idx["destino"]
        i_val, i_blo = idx["valor"], idx["bloque"]

        for fila in lector:
            if not fila:
                continue
            tok = fila[i_tok].strip().lower() if i_tok is not None else token_por_defecto
            if filtro is not None and tok != filtro:
                continue
            bloque = None
            if i_blo is not None:
                try:
                    bloque = int(float(fila[i_blo]))
                except ValueError:
                    bloque = None
            yield (
                tok,
                fila[i_ori].strip().lower(),
                fila[i_des].strip().lower(),
                _a_numero(fila[i_val]),
                bloque,
            )


def cargar_exchanges(ruta_csv: str) -> Dict[str, Dict[str, str]]:
    """Lee las etiquetas reales de exchanges (exchangeLabels.csv).

    Columnas: type (cex/dex), address, name.

    Retorna {dirección: {"nombre", "tipo", "entidad"}}. `entidad` agrupa las
    varias direcciones de un mismo exchange: se quita lo que va después de ":"
    y el número final ("Binance 14" -> "Binance", "Poloniex: BAT" ->
    "Poloniex", "DDEX 1.0" -> "DDEX"). Con esta regla salen 150 entidades;
    SNAP reporta 149 exchanges.
    """
    exchanges: Dict[str, Dict[str, str]] = {}
    with open(ruta_csv, newline="", encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            addr = fila["address"].strip().lower()
            nombre = fila.get("name", "").strip()
            exchanges[addr] = {
                "nombre": nombre,
                "tipo": fila.get("type", "").strip().lower(),
                "entidad": re.sub(r"\s+\d+(\.\d+)?$", "", nombre.split(":")[0].strip()),
            }
    return exchanges


# ----------------------------------------------------------------------
# Resumen por token (una sola pasada sobre el CSV completo)
# ----------------------------------------------------------------------

def resumir_por_token(
    transferencias: Iterable[Transferencia],
    exchanges: Optional[Dict[str, Dict[str, str]]] = None,
    contar_distintos: bool = True,
) -> Dict[str, Dict[str, float]]:
    """Calcula, en una sola pasada, las estadísticas crudas de cada token.

    Para contar direcciones y pares distintos sin guardar millones de textos
    de 42 caracteres, se guarda el `hash` de cada uno (un entero). La
    probabilidad de que dos direcciones distintas choquen es despreciable
    (hash de 64 bits), y la memoria baja a menos de la mitad.

    Con `contar_distintos=False` no se cuentan direcciones ni pares (quedan
    vacíos) y la memoria casi no crece: útil en un computador con poca RAM.

    Retorna {token: {columna: valor}} con las columnas de COLUMNAS_RESUMEN.
    """
    exchanges = exchanges or {}
    datos: Dict[str, Dict[str, float]] = {}
    direcciones: Dict[str, Set[int]] = defaultdict(set)
    pares: Dict[str, Set[int]] = defaultdict(set)
    presentes: Dict[str, Set[str]] = defaultdict(set)

    for tok, ori, des, valor, bloque in transferencias:
        d = datos.get(tok)
        if d is None:
            d = datos[tok] = {
                "transferencias": 0, "valor_invalido": 0, "valor_cero": 0,
                "autolazos": 0, "mint": 0, "burn": 0, "valor_max": 0.0,
                "bloque_min": None, "bloque_max": None,
            }
        d["transferencias"] += 1
        if valor is None:
            d["valor_invalido"] += 1
        elif valor <= 0:
            d["valor_cero"] += 1
        elif valor > d["valor_max"]:
            d["valor_max"] = valor
        if ori == des:
            d["autolazos"] += 1
        if ori == DIRECCION_CERO:
            d["mint"] += 1
        if des == DIRECCION_CERO:
            d["burn"] += 1
        if bloque is not None:
            if d["bloque_min"] is None or bloque < d["bloque_min"]:
                d["bloque_min"] = bloque
            if d["bloque_max"] is None or bloque > d["bloque_max"]:
                d["bloque_max"] = bloque

        if contar_distintos:
            direcciones[tok].add(hash(ori))
            direcciones[tok].add(hash(des))
            pares[tok].add(hash((ori, des)))
        if ori in exchanges:
            presentes[tok].add(ori)
        if des in exchanges:
            presentes[tok].add(des)

    for tok, d in datos.items():
        d["direcciones"] = len(direcciones[tok]) if contar_distintos else None
        d["pares"] = len(pares[tok]) if contar_distintos else None
        vistos = presentes[tok]
        d["exchanges_presentes"] = len(vistos)
        d["cex_presentes"] = sum(1 for a in vistos if exchanges[a]["tipo"] == "cex")
        d["dex_presentes"] = sum(1 for a in vistos if exchanges[a]["tipo"] == "dex")
    return datos


def guardar_resumen(resumen: Dict[str, Dict[str, float]], ruta_csv: str) -> None:
    """Guarda el resumen por token, ordenado de más a menos transferencias."""
    with open(ruta_csv, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo, lineterminator="\n")
        escritor.writerow(COLUMNAS_RESUMEN)
        orden = sorted(resumen.items(), key=lambda t: (-t[1]["transferencias"], t[0]))
        for tok, d in orden:
            fila = [tok] + [d[c] if d[c] is not None else "" for c in COLUMNAS_RESUMEN[1:]]
            escritor.writerow([repr(x) if isinstance(x, float) else x for x in fila])


def leer_resumen(ruta_csv: str) -> Dict[str, Dict[str, float]]:
    """Lee un resumen guardado con `guardar_resumen`."""
    resumen: Dict[str, Dict[str, float]] = {}
    with open(ruta_csv, newline="", encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            tok = fila.pop("token_address")
            datos: Dict[str, float] = {}
            for clave, texto in fila.items():
                if texto == "":
                    datos[clave] = None
                elif clave == "valor_max":
                    datos[clave] = float(texto)
                else:
                    datos[clave] = int(float(texto))
            resumen[tok] = datos
    return resumen


# ----------------------------------------------------------------------
# Limpieza y agregación de un token
# ----------------------------------------------------------------------

def valor_maximo(transferencias: Iterable[Transferencia]) -> float:
    """Mayor valor positivo de un conjunto de transferencias (0.0 si no hay)."""
    maximo = 0.0
    for _, _, _, valor, _ in transferencias:
        if valor is not None and valor > maximo:
            maximo = valor
    return maximo


def limpiar_y_agregar(
    transferencias: Iterable[Transferencia],
    valor_max: float,
    quitar_direccion_cero: bool = False,
) -> Tuple[Aristas, Dict[str, int]]:
    """Aplica las reglas de limpieza y agrega las transferencias por par.

    Parámetros:
        transferencias: filas de UN token (usar `leer_transferencias(..., token=...)`).
        valor_max: mayor valor positivo del token (del resumen o de `valor_maximo`).
        quitar_direccion_cero: si True, también descarta mint y burn.

    Reglas, en orden (cada fila descartada cuenta solo en la primera regla
    que la descarta):
        1. valor inválido;
        2. valor <= 0;
        3. polvo: valor < valor_max / FACTOR_POLVO;
        4. autolazo (origen == destino);
        5. dirección cero (solo si quitar_direccion_cero).

    Retorna (aristas, reporte):
        aristas = {(origen, destino): [suma_valor, n_transferencias]}
        reporte = conteo de filas leídas, descartadas por regla y conservadas.
    """
    umbral = valor_max / FACTOR_POLVO
    reporte = {
        "leidas": 0, "valor_invalido": 0, "valor_cero": 0, "polvo": 0,
        "autolazos": 0, "direccion_cero": 0, "conservadas": 0,
    }
    aristas: Aristas = {}

    for _, ori, des, valor, _ in transferencias:
        reporte["leidas"] += 1
        if valor is None:
            reporte["valor_invalido"] += 1
            continue
        if valor <= 0:
            reporte["valor_cero"] += 1
            continue
        if valor < umbral:
            reporte["polvo"] += 1
            continue
        if ori == des:
            reporte["autolazos"] += 1
            continue
        if quitar_direccion_cero and DIRECCION_CERO in (ori, des):
            reporte["direccion_cero"] += 1
            continue

        reporte["conservadas"] += 1
        acumulado = aristas.get((ori, des))
        if acumulado is None:
            aristas[(ori, des)] = [valor, 1]
        else:
            acumulado[0] += valor
            acumulado[1] += 1

    return aristas, reporte


def guardar_aristas(aristas: Aristas, ruta_csv: str) -> None:
    """Guarda las aristas limpias en el formato que lee `Grafo`.

    Columnas: from_address, to_address, value, n_transferencias.
    Las filas se ordenan para que el archivo sea idéntico en cada ejecución.
    """
    with open(ruta_csv, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo, lineterminator="\n")
        escritor.writerow(["from_address", "to_address", "value", "n_transferencias"])
        for (ori, des), (suma, n) in sorted(aristas.items()):
            escritor.writerow([ori, des, repr(float(suma)), int(n)])


# ----------------------------------------------------------------------
# Perfil del grafo de un token (opera sobre un objeto Grafo)
# ----------------------------------------------------------------------

def grados(adj: Dict[str, List[Tuple[str, float]]], nodos: Set[str]) -> Tuple[Dict[str, int], Dict[str, int]]:
    """Grado de entrada y de salida de cada nodo."""
    entrada = {v: 0 for v in nodos}
    salida = {v: 0 for v in nodos}
    for u, vecinos in adj.items():
        salida[u] = salida.get(u, 0) + len(vecinos)
        for v, _ in vecinos:
            entrada[v] = entrada.get(v, 0) + 1
    return entrada, salida


def componentes_debiles(adj: Dict[str, List[Tuple[str, float]]], nodos: Set[str]) -> List[int]:
    """Tamaños de las componentes débilmente conexas, de mayor a menor (BFS)."""
    vecinos: Dict[str, List[str]] = defaultdict(list)
    for u, salientes in adj.items():
        for v, _ in salientes:
            vecinos[u].append(v)
            vecinos[v].append(u)

    visitado: Set[str] = set()
    tamanos: List[int] = []
    for inicio in nodos:
        if inicio in visitado:
            continue
        visitado.add(inicio)
        cola = deque([inicio])
        tamano = 0
        while cola:
            nodo = cola.popleft()
            tamano += 1
            for otro in vecinos[nodo]:
                if otro not in visitado:
                    visitado.add(otro)
                    cola.append(otro)
        tamanos.append(tamano)
    return sorted(tamanos, reverse=True)


def perfil(grafo) -> Dict[str, float]:
    """Estadísticas estructurales de un `Grafo` ya cargado.

    Retorna: nodos, aristas, densidad, reciprocidad (fracción de aristas u->v
    que tienen su inversa v->u), fuentes (sin entradas), sumideros (sin
    salidas), autolazos, número de componentes débiles y tamaño de la mayor.
    """
    nodos = grafo.nodos
    n, m = len(nodos), len(grafo.aristas)
    pares = {(u, v) for u, v, _ in grafo.aristas}
    reciprocas = sum(1 for u, v in pares if u != v and (v, u) in pares)
    entrada, salida = grados(grafo.adj, nodos)
    comps = componentes_debiles(grafo.adj, nodos)
    return {
        "nodos": n,
        "aristas": m,
        "densidad": m / (n * (n - 1)) if n > 1 else 0.0,
        "reciprocidad": reciprocas / len(pares) if pares else 0.0,
        "fuentes": sum(1 for v in nodos if entrada[v] == 0),
        "sumideros": sum(1 for v in nodos if salida[v] == 0),
        "autolazos": sum(1 for u, v in pares if u == v),
        "componentes": len(comps),
        "componente_mayor": comps[0] if comps else 0,
    }


def exchanges_en_grafo(
    nodos: Set[str],
    exchanges: Dict[str, Dict[str, str]],
) -> Dict[str, Dict[str, str]]:
    """Subconjunto de etiquetas de exchanges cuyas direcciones están en el grafo."""
    return {a: info for a, info in exchanges.items() if a in nodos}


def percentil_de_grado(
    grado_total: Dict[str, int],
    direcciones: Iterable[str],
) -> Dict[str, float]:
    """Percentil (0-100) del grado de cada dirección dentro del grafo.

    100 = el nodo de mayor grado. Sirve para ver qué tan "arriba" están los
    exchanges solo por su número de conexiones.
    """
    valores = sorted(grado_total.values())
    n = len(valores)
    resultado: Dict[str, float] = {}
    for addr in direcciones:
        g = grado_total[addr]
        # cuántos nodos tienen grado estrictamente menor (búsqueda binaria)
        lo, hi = 0, n
        while lo < hi:
            mid = (lo + hi) // 2
            if valores[mid] < g:
                lo = mid + 1
            else:
                hi = mid
        resultado[addr] = 100.0 * lo / (n - 1) if n > 1 else 100.0
    return resultado
