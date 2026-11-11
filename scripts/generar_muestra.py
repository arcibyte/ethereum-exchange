"""
generar_muestra.py
==================
Genera una muestra conectada del dataset para ejecutar los algoritmos en
Colab sin cargar millones de aristas.

La muestra se saca del dataset real (CSV o Parquet) y se guarda como CSV
pequeño, junto con las etiquetas de los exchanges que aparecen en ella.

Uso:
    python scripts/generar_muestra.py \
        --entrada data/procesado/transferencias.parquet \
        --salida data/muestra/transferencias_2k.csv \
        --etiquetas data/raw/exchange_labels.csv \
        --salida-etiquetas data/muestra/etiquetas.csv \
        --objetivo 2000

La muestra es reproducible: usa la misma semilla y el mismo archivo de entrada.
"""

from __future__ import annotations

import argparse
import csv
import os
from collections import defaultdict, deque
from pathlib import Path


def _fuente(ruta: str) -> str:
    """Devuelve la función de lectura de DuckDB según la extensión."""
    texto = str(ruta).replace("'", "''")
    if str(ruta).lower().endswith((".parquet", ".pq")):
        return f"read_parquet('{texto}')"
    return f"read_csv_auto('{texto}', header=true)"


def muestrear(
    entrada: str,
    filas: int,
    semilla: int,
    token: str | None = None,
    decimales: int = 0,
) -> list[tuple[str, str, float]]:
    """Toma una muestra aleatoria reproducible de transferencias.

    Si se indica `token`, filtra por ese contrato. `decimales` normaliza el
    valor (por ejemplo, USDC tiene 6 decimales).
    """
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "Falta duckdb. Instálalo con:\n"
            "    pip install -r requirements-datos.txt"
        ) from exc

    con = duckdb.connect()
    try:
        where = ""
        if token:
            where = f"WHERE CAST(token_address AS VARCHAR) = '{token}'"
        consulta = (
            f"SELECT from_address, to_address, value FROM {_fuente(entrada)} "
            f"{where} "
            f"USING SAMPLE reservoir({int(filas)} ROWS) REPEATABLE ({int(semilla)})"
        )
        filas_leidas = con.execute(consulta).fetchall()
    finally:
        con.close()

    factor = 10.0 ** int(decimales)
    aristas: list[tuple[str, str, float]] = []
    for origen, destino, valor in filas_leidas:
        origen = str(origen).strip().lower()
        destino = str(destino).strip().lower()
        valor = float(valor) / factor
        if not origen or not destino or origen == destino:
            continue
        if origen == "0x0000000000000000000000000000000000000000":
            continue
        if destino == "0x0000000000000000000000000000000000000000":
            continue
        if valor <= 0:
            continue
        aristas.append((origen, destino, valor))
    return aristas


def componente_mayor(aristas: list[tuple[str, str, float]]) -> list[tuple[str, str, float]]:
    """Conserva solo las aristas de la componente conexa más grande."""
    ady: dict[str, set[str]] = defaultdict(set)
    for origen, destino, _ in aristas:
        ady[origen].add(destino)
        ady[destino].add(origen)

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

    return [(a, b, w) for a, b, w in aristas if a in mejor and b in mejor]


def guardar(aristas: list[tuple[str, str, float]], salida: Path) -> None:
    salida.parent.mkdir(parents=True, exist_ok=True)
    with salida.open("w", newline="", encoding="utf-8") as fh:
        escritor = csv.writer(fh, lineterminator="\n")
        escritor.writerow(["from_address", "to_address", "value"])
        for origen, destino, valor in aristas:
            escritor.writerow([origen, destino, valor])


def guardar_etiquetas(
    direcciones: set[str],
    entrada: Path,
    salida: Path,
) -> int:
    """Guarda solo las etiquetas de las direcciones que aparecen en la muestra."""
    if not entrada.is_file():
        return 0

    filas = []
    with entrada.open(newline="", encoding="latin-1") as fh:
        lector = csv.DictReader(fh)
        campos = {c.lower(): c for c in (lector.fieldnames or [])}
        col_address = campos.get("address")
        col_name = campos.get("name")
        col_type = campos.get("type")
        if not col_address or not col_name:
            return 0
        for fila in lector:
            addr = fila[col_address].strip().lower()
            if addr in direcciones:
                filas.append((
                    addr,
                    fila[col_name].strip(),
                    fila[col_type].strip() if col_type else "",
                ))

    salida.parent.mkdir(parents=True, exist_ok=True)
    with salida.open("w", newline="", encoding="utf-8") as fh:
        escritor = csv.writer(fh, lineterminator="\n")
        escritor.writerow(["address", "name", "type"])
        escritor.writerows(sorted(filas))
    return len(filas)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", required=True, help="CSV o Parquet de transferencias")
    parser.add_argument("--salida", required=True, help="CSV pequeño de salida")
    parser.add_argument("--etiquetas", default=None, help="CSV de etiquetas de exchanges")
    parser.add_argument("--salida-etiquetas", default=None, help="CSV de etiquetas filtradas")
    parser.add_argument("--objetivo", type=int, default=2_000,
                        help="Aristas objetivo de la muestra (aproximado)")
    parser.add_argument("--filas", type=int, default=None,
                        help="filas a muestrear antes de la componente (por defecto 3*objetivo)")
    parser.add_argument("--token", default=None,
                        help="contrato del token a analizar (ej. USDC)")
    parser.add_argument("--decimales", type=int, default=0,
                        help="decimales del token para normalizar value (USDC=6, DAI=18)")
    parser.add_argument("--semilla", type=int, default=42)
    args = parser.parse_args()

    # Se muestrean más filas de las necesarias porque al quedarnos con la
    # componente conexa más grande se descartan nodos aislados.
    filas = args.filas if args.filas else max(args.objetivo * 3, 1_000)
    aristas = componente_mayor(
        muestrear(args.entrada, filas, args.semilla, args.token, args.decimales)
    )

    # Si la componente quedó pequeña, se amplía la muestra (hasta un límite).
    while (
        not args.filas
        and len(aristas) < args.objetivo
        and filas < args.objetivo * 20
    ):
        filas *= 2
        aristas = componente_mayor(
            muestrear(args.entrada, filas, args.semilla, args.token, args.decimales)
        )

    if not aristas:
        raise SystemExit("La muestra quedó vacía. Revisa el archivo de entrada.")

    guardar(aristas, Path(args.salida))

    direcciones = set()
    for origen, destino, _ in aristas:
        direcciones.add(origen)
        direcciones.add(destino)
    n_etiquetas = 0
    if args.etiquetas and args.salida_etiquetas:
        n_etiquetas = guardar_etiquetas(
            direcciones, Path(args.etiquetas), Path(args.salida_etiquetas)
        )

    print(f"Muestra escrita en: {args.salida}")
    print(f"  aristas: {len(aristas):,}")
    print(f"  nodos  : {len(direcciones):,}")
    print(f"  etiquetas: {n_etiquetas:,}")
    print(f"  tamaño : {os.path.getsize(args.salida) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
