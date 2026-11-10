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


def muestrear(entrada: str, filas: int, semilla: int) -> list[tuple[str, str, float]]:
    """Toma una muestra aleatoria reproducible de transferencias."""
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "Falta duckdb. Instálalo con:\n"
            "    pip install -r requirements-datos.txt"
        ) from exc

    con = duckdb.connect()
    try:
        consulta = (
            f"SELECT from_address, to_address, value FROM {_fuente(entrada)} "
            f"USING SAMPLE reservoir({int(filas)} ROWS) REPEATABLE ({int(semilla)})"
        )
        filas_leidas = con.execute(consulta).fetchall()
    finally:
        con.close()

    aristas: list[tuple[str, str, float]] = []
    for origen, destino, valor in filas_leidas:
        origen = str(origen).strip().lower()
        destino = str(destino).strip().lower()
        valor = float(valor)
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
        escritor = csv.writer(fh)
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
        escritor = csv.writer(fh)
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
    parser.add_argument("--semilla", type=int, default=42)
    args = parser.parse_args()

    # Se muestrean más filas de las necesarias porque al quedarnos con la
    # componente conexa más grande se descartan nodos aislados.
    filas = max(args.objetivo * 2, 1_000)
    aristas = componente_mayor(muestrear(args.entrada, filas, args.semilla))

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
