"""
grafo.py
========
Carga del dataset y construcción del grafo.

En este proyecto modelamos las transferencias de un token ERC-20 de Ethereum
como un grafo DIRIGIDO y PONDERADO G = (V, E):

    - V (vértices): las direcciones (wallets, exchanges, contratos).
    - E (aristas): las transferencias de una dirección a otra.
    - w(e) (peso): la cantidad transferida.

La carga acepta **CSV** y **Parquet**. Para Parquet se usa DuckDB solo para
leer y muestrear el archivo; los algoritmos del proyecto siguen siendo Python
puro y reciben el grafo ya construido.

Solo usamos estructuras nativas de Python: diccionarios y listas.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple

# Lista de adyacencia: cada nodo apunta a una lista de (vecino, peso).
AdjList = Dict[str, List[Tuple[str, float]]]

# Nombres de columna que aceptamos para cada dato. Se comparan sin distinguir
# mayúsculas/minúsculas, así funciona con distintos exports del dataset.
COLUMNAS = {
    "from": ["from_address", "from", "sender", "from_addr", "fromaddress"],
    "to": ["to_address", "to", "receiver", "to_addr", "toaddress"],
    "value": ["value", "amount", "token_amount", "quantity", "val"],
    "token": ["token_address", "contract_address", "token", "tokenaddress"],
    "time": ["block_timestamp", "timestamp", "block_time", "date", "time"],
    "block": ["block_number", "block"],
}

DIRECCION_CERO = "0x0000000000000000000000000000000000000000"
DIRECCIONES_CERO = {DIRECCION_CERO, "0x0", "0x00"}


def _elegir_columnas(disponibles: list[str]) -> Dict[str, Optional[str]]:
    """Mapea cada dato lógico (from, to, value...) a su columna real.

    `disponibles` debe venir en minúsculas y en el orden del archivo; el
    resultado conserva el nombre real de la columna para poder citarlo en SQL.
    """
    return {
        clave: next((opcion for opcion in opciones if opcion in disponibles), None)
        for clave, opciones in COLUMNAS.items()
    }


def _sql_texto(valor: str) -> str:
    """Escapa un texto para usarlo dentro de una consulta SQL."""
    return "'" + str(valor).replace("'", "''") + "'"


def _sql_columna(columna: str) -> str:
    """Cita un identificador de columna para SQL."""
    return '"' + str(columna).replace('"', '""') + '"'


class Grafo:
    """Grafo dirigido y ponderado representado con una lista de adyacencia."""

    def __init__(self) -> None:
        # {origen: [(destino, peso), ...]}
        self.adj: AdjList = defaultdict(list)
        # Todos los vértices del grafo.
        self.nodos: Set[str] = set()
        # Lista de aristas como (origen, destino, peso).
        self.aristas: List[Tuple[str, str, float]] = []
        # {dirección: {"nombre": ..., "tipo": ...}} para mostrar resultados legibles.
        self.etiquetas: Dict[str, Dict[str, str]] = {}

    # ------------------------------------------------------------------
    # Carga de datos
    # ------------------------------------------------------------------

    def _agregar_arista(
        self,
        origen: str,
        destino: str,
        peso: float,
        limpiar: bool = True,
    ) -> bool:
        """Agrega una arista y devuelve si fue aceptada.

        Con `limpiar=True` se descartan transferencias inválidas para el
        análisis: dirección cero, auto-transferencias y valores no positivos.
        """
        origen = str(origen).strip().lower()
        destino = str(destino).strip().lower()
        peso = float(peso)

        if limpiar:
            if not origen or not destino:
                return False
            if origen == destino:
                return False
            if origen in DIRECCIONES_CERO or destino in DIRECCIONES_CERO:
                return False
            if peso <= 0:
                return False

        self.nodos.add(origen)
        self.nodos.add(destino)
        self.adj[origen].append((destino, peso))
        self.aristas.append((origen, destino, peso))
        return True

    def cargar_transferencias(
        self,
        ruta_csv: str,
        max_filas: Optional[int] = None,
        limpiar: bool = False,
    ) -> "Grafo":
        """Lee un CSV de transferencias y llena la lista de adyacencia.

        El CSV debe tener (al menos) columnas equivalentes a:
            from_address, to_address, value
        (se aceptan alias como `from`, `sender`, `to`, `receiver`, etc.).

        Parámetros:
            ruta_csv: ruta al archivo CSV.
            max_filas: opcional. Leer solo las primeras `max_filas` filas
                       (útil para probar con una muestra).
            limpiar: descartar dirección cero, auto-loops y valores <= 0.

        Retorna:
            self, para poder encadenar llamadas.
        """
        import csv

        with open(ruta_csv, newline="", encoding="utf-8") as archivo:
            lector = csv.DictReader(archivo)
            campos = lector.fieldnames or []
            disponibles = [c.lower() for c in campos]
            reales = {c.lower(): c for c in campos}
            mapa = _elegir_columnas(disponibles)

            faltan = [k for k in ("from", "to", "value") if not mapa[k]]
            if faltan:
                raise ValueError(
                    "No encontré las columnas necesarias: "
                    + ", ".join(faltan)
                    + ". Columnas disponibles: "
                    + ", ".join(campos)
                )

            col_from = reales[mapa["from"]]
            col_to = reales[mapa["to"]]
            col_value = reales[mapa["value"]]

            for i, fila in enumerate(lector):
                if max_filas is not None and i >= max_filas:
                    break
                self._agregar_arista(
                    fila[col_from],
                    fila[col_to],
                    fila[col_value],
                    limpiar=limpiar,
                )

        return self

    def cargar_parquet(
        self,
        ruta: str,
        max_filas: Optional[int] = None,
        muestra: Optional[int] = None,
        token: Optional[str] = None,
        desde: Optional[str] = None,
        hasta: Optional[str] = None,
        semilla: int = 42,
        limpiar: bool = False,
    ) -> "Grafo":
        """Lee un Parquet (o una muestra) usando DuckDB.

        DuckDB solo se encarga de leer, filtrar y muestrear; el grafo se
        construye igual que con el CSV, usando Python puro.

        Parámetros:
            ruta: ruta al archivo Parquet.
            max_filas: leer solo las primeras N filas.
            muestra: tomar una muestra aleatoria de N filas (recomendado para
                     el dataset completo).
            token: filtrar por `token_address`.
            desde / hasta: filtrar por `block_timestamp` (texto ISO) si existe.
            semilla: semilla de la muestra aleatoria.
            limpiar: descartar dirección cero, auto-loops y valores <= 0.

        Retorna:
            self, para poder encadenar llamadas.
        """
        try:
            import duckdb
        except ImportError as exc:  # pragma: no cover - depende del entorno
            raise SystemExit(
                "Falta duckdb para leer Parquet. Instálalo con:\n"
                "    pip install -r requirements-datos.txt"
            ) from exc

        con = duckdb.connect()
        try:
            campos = list(con.read_parquet(ruta).columns)
            disponibles = [c.lower() for c in campos]
            reales = {c.lower(): c for c in campos}
            mapa = _elegir_columnas(disponibles)

            faltan = [k for k in ("from", "to", "value") if not mapa[k]]
            if faltan:
                raise ValueError(
                    "No encontré las columnas necesarias: "
                    + ", ".join(faltan)
                    + ". Columnas disponibles: "
                    + ", ".join(campos)
                )

            select = (
                f"CAST({_sql_columna(reales[mapa['from']])} AS VARCHAR) AS from_address, "
                f"CAST({_sql_columna(reales[mapa['to']])} AS VARCHAR) AS to_address, "
                f"CAST({_sql_columna(reales[mapa['value']])} AS DOUBLE) AS value"
            )

            filtros: list[str] = []
            if token:
                if not mapa["token"]:
                    raise ValueError("Pediste `token` pero el Parquet no tiene columna de token.")
                filtros.append(
                    f"CAST({_sql_columna(reales[mapa['token']])} AS VARCHAR) = "
                    f"{_sql_texto(token)}"
                )
            if desde or hasta:
                if not mapa["time"]:
                    raise ValueError(
                        "Pediste una ventana de tiempo pero el Parquet no tiene "
                        "columna de tiempo (block_timestamp)."
                    )
                col_tiempo = _sql_columna(reales[mapa["time"]])
                if desde:
                    filtros.append(f"CAST({col_tiempo} AS VARCHAR) >= {_sql_texto(desde)}")
                if hasta:
                    filtros.append(f"CAST({col_tiempo} AS VARCHAR) <= {_sql_texto(hasta)}")

            consulta = f"SELECT {select} FROM read_parquet({_sql_texto(ruta)})"
            if filtros:
                consulta += " WHERE " + " AND ".join(filtros)

            if muestra is not None:
                n = int(muestra)
                consulta += f" USING SAMPLE reservoir({n} ROWS)"
                if semilla is not None:
                    consulta += f" REPEATABLE ({int(semilla)})"
            elif max_filas is not None:
                consulta += f" LIMIT {int(max_filas)}"

            try:
                filas = con.execute(consulta).fetchall()
            except Exception as exc:  # DuckDB antiguo sin REPEATABLE/reservoir
                mensaje = str(exc).lower()
                if muestra is not None and ("parser" in mensaje or "syntax" in mensaje):
                    base = consulta.split(" USING SAMPLE ")[0]
                    filas = con.execute(f"{base} LIMIT {int(muestra)}").fetchall()
                else:
                    raise
        finally:
            con.close()

        for origen, destino, peso in filas:
            self._agregar_arista(origen, destino, peso, limpiar=limpiar)

        return self

    def cargar(self, ruta: str, max_filas: Optional[int] = None, **opciones) -> "Grafo":
        """Carga transferencias detectando el formato por la extensión.

        - `.csv`  -> `cargar_transferencias`
        - `.parquet` / `.pq` -> `cargar_parquet`

        Las opciones específicas de Parquet (`muestra`, `token`, `desde`,
        `hasta`, `semilla`, `limpiar`) se pasan tal cual.
        """
        if str(ruta).lower().endswith((".parquet", ".pq")):
            return self.cargar_parquet(ruta, max_filas=max_filas, **opciones)

        sobrantes = set(opciones) - {"limpiar"}
        if sobrantes:
            raise ValueError(
                f"Las opciones {sorted(sobrantes)} solo aplican a archivos Parquet."
            )
        return self.cargar_transferencias(ruta, max_filas=max_filas, **opciones)

    def cargar_etiquetas(self, ruta_csv: str) -> "Grafo":
        """Lee un CSV con el nombre legible de cada dirección.

        El CSV debe tener las columnas: address, name, type.
        """
        import csv

        # Algunos exports de etiquetas vienen en latin-1 (nombres con tildes).
        filas = None
        for codificacion in ("utf-8", "latin-1"):
            try:
                with open(ruta_csv, newline="", encoding=codificacion) as archivo:
                    filas = list(csv.DictReader(archivo))
                break
            except UnicodeDecodeError:
                continue
        if filas is None:  # pragma: no cover - archivo binario inválido
            raise ValueError(f"No se pudo leer el CSV de etiquetas: {ruta_csv}")

        for fila in filas:
            addr = fila["address"].strip().lower()
            self.etiquetas[addr] = {
                "nombre": fila.get("name", "").strip(),
                "tipo": fila.get("type", "").strip(),
            }
        return self

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def conservar_componente_mayor(self) -> "Grafo":
        """Deja solo la componente conexa (no dirigida) más grande.

        Un muestreo aleatorio deja muchos nodos aislados. Quedarse con la
        componente más grande produce una red conectada y resultados
        interpretables, sin volver a leer el archivo.

        Retorna:
            self, para poder encadenar llamadas.
        """
        adyacencia: dict[str, set[str]] = defaultdict(set)
        for origen, destino, _ in self.aristas:
            adyacencia[origen].add(destino)
            adyacencia[destino].add(origen)

        visitados: Set[str] = set()
        mejor: Set[str] = set()
        for inicio in adyacencia:
            if inicio in visitados:
                continue
            componente: Set[str] = set()
            cola = deque([inicio])
            visitados.add(inicio)
            while cola:
                nodo = cola.popleft()
                componente.add(nodo)
                for vecino in adyacencia[nodo]:
                    if vecino not in visitados:
                        visitados.add(vecino)
                        cola.append(vecino)
            if len(componente) > len(mejor):
                mejor = componente

        if not mejor or len(mejor) == len(self.nodos):
            return self

        aristas = [
            (a, b, w) for a, b, w in self.aristas if a in mejor and b in mejor
        ]
        self.adj = defaultdict(list)
        self.nodos = set()
        self.aristas = []
        for origen, destino, peso in aristas:
            self._agregar_arista(origen, destino, peso, limpiar=False)
        return self

    def nombre(self, addr: str) -> str:
        """Nombre legible de un nodo, o la propia dirección si no está etiquetada."""
        return self.etiquetas.get(addr, {}).get("nombre", addr)

    def resumen(self) -> Dict[str, float]:
        """Estadísticas básicas: número de nodos, aristas, densidad y peso."""
        n = len(self.nodos)
        m = len(self.aristas)
        # Densidad de un grafo dirigido: |E| / (|V| * (|V| - 1))
        densidad = m / (n * (n - 1)) if n > 1 else 0.0
        peso_total = sum(w for _, _, w in self.aristas)
        return {
            "nodos": n,
            "aristas": m,
            "densidad": round(densidad, 4),
            "peso_total": round(peso_total, 2),
        }


def cargar_grafo(
    ruta: str,
    max_filas: Optional[int] = None,
    etiquetas: Optional[str] = None,
    limpiar: bool = True,
    **opciones,
) -> Grafo:
    """Carga el dataset UNA vez y devuelve el objeto compartido `Grafo`.

    Es la función que usa el notebook. Las cuatro tareas reciben
    `grafo.aristas` y construyen su propia estructura; no vuelven a leer el
    archivo.

    Por defecto limpia transferencias inválidas (dirección cero, autolazos y
    valores <= 0). Usa `limpiar=False` si quieres cargar el archivo tal cual.

    Ejemplo:
        grafo = cargar_grafo("data/sample/transferencias.csv")
    """
    opciones.setdefault("limpiar", limpiar)
    grafo = Grafo().cargar(ruta, max_filas=max_filas, **opciones)
    if etiquetas:
        grafo.cargar_etiquetas(etiquetas)
    return grafo
