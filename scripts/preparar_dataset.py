"""
preparar_dataset.py
===================
Preprocesa el dataset grande de transferencias (~8 GB) para poder usarlo en el
proyecto sin reventar la memoria de Colab.

La idea es la misma que ya habías usado antes: "precargar" el CSV en un formato
binario comprimido. El CSV pesa ~8 GB porque es texto; en Parquet con
compresión ZSTD baja a ~2.3 GB y se puede consultar sin cargarlo todo en RAM.

Comandos
--------
1) Convertir el CSV completo a Parquet (la "precarga"):

    python scripts/preparar_dataset.py convertir \
        --entrada /ruta/transferencias.csv \
        --salida data/procesado/transferencias.parquet

2) Generar una muestra manejable para el notebook:

    python scripts/preparar_dataset.py muestra \
        --entrada data/procesado/transferencias.parquet \
        --salida data/muestra/transferencias_100k.csv \
        --filas 100000 --componente

3) Ver estadísticas del archivo procesado:

    python scripts/preparar_dataset.py info \
        --entrada data/procesado/transferencias.parquet

Requisitos:
    pip install -r requirements-datos.txt

Nota: esto es solo preprocesamiento de datos. Los algoritmos del proyecto
(Bellman-Ford, PageRank, Louvain, Kruskal) siguen siendo Python puro.
"""

from __future__ import annotations

import argparse
import csv
import os
from collections import defaultdict, deque
from pathlib import Path

# Nombres de columna que aceptamos para cada dato. Se comparan sin distinguir
# mayúsculas/minúsculas, así funciona con distintos exports.
CANDIDATOS = {
    "from": ["from_address", "from", "sender", "from_addr", "fromaddress"],
    "to": ["to_address", "to", "receiver", "to_addr", "toaddress"],
    "value": ["value", "amount", "token_amount", "quantity", "val"],
    "token": ["token_address", "contract_address", "token", "tokenaddress"],
    "time": ["block_timestamp", "timestamp", "block_time", "date", "time"],
}


def _sql_texto(ruta: str) -> str:
    """Escapa una ruta para usarla dentro de una consulta SQL."""
    return "'" + str(ruta).replace("'", "''") + "'"


def _fuente(ruta: str) -> str:
    """Devuelve la función de lectura de DuckDB según la extensión."""
    if str(ruta).lower().endswith(".parquet"):
        return f"read_parquet({_sql_texto(ruta)})"
    return f"read_csv_auto({_sql_texto(ruta)}, header=true)"


def _conectar():
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "Falta duckdb. Instálalo con:\n"
            "    pip install -r requirements-datos.txt"
        ) from exc
    return duckdb.connect()


def _columnas(con, ruta: str) -> list[str]:
    rel = con.read_parquet(ruta) if str(ruta).lower().endswith(".parquet") else con.read_csv(ruta, header=True)
    return list(rel.columns)


def _mapear(columnas: list[str]) -> dict[str, str | None]:
    """Encuentra, para cada dato, el nombre real de la columna en el archivo."""
    por_nombre = {c.lower(): c for c in columnas}
    resultado: dict[str, str | None] = {}
    for clave, opciones in CANDIDATOS.items():
        elegida = None
        for opcion in opciones:
            if opcion in por_nombre:
                elegida = por_nombre[opcion]
                break
        resultado[clave] = elegida
    return resultado


def _exigir_columnas(mapa: dict[str, str | None], columnas: list[str]) -> None:
    faltan = [k for k in ("from", "to", "value") if not mapa[k]]
    if faltan:
        raise SystemExit(
            "No encontré las columnas necesarias: "
            + ", ".join(faltan)
            + ".\nColumnas disponibles: "
            + ", ".join(columnas)
        )


def convertir(args: argparse.Namespace) -> None:
    """Convierte el CSV grande a Parquet comprimido (~8 GB -> ~2.3 GB)."""
    con = _conectar()
    columnas = _columnas(con, args.entrada)
    mapa = _mapear(columnas)
    _exigir_columnas(mapa, columnas)

    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)

    columnas_select = [
        f'CAST("{mapa["from"]}" AS VARCHAR) AS from_address',
        f'CAST("{mapa["to"]}" AS VARCHAR) AS to_address',
        f'CAST("{mapa["value"]}" AS DOUBLE) AS value',
    ]
    # Conservamos token y fecha (si existen) para poder filtrar después por
    # token o por ventana de tiempo sin volver a leer el CSV de 8 GB.
    if mapa["token"] and mapa["token"] not in (mapa["from"], mapa["to"], mapa["value"]):
        columnas_select.append(f'CAST("{mapa["token"]}" AS VARCHAR) AS token_address')
    if mapa["time"] and mapa["time"] not in (mapa["from"], mapa["to"], mapa["value"]):
        columnas_select.append(f'CAST("{mapa["time"]}" AS VARCHAR) AS block_timestamp')

    select = ", ".join(columnas_select)
    consulta = (
        f"COPY (SELECT {select} FROM {_fuente(args.entrada)}) "
        f"TO {_sql_texto(salida)} "
        f"(FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 1000000)"
    )

    print("Convirtiendo a Parquet...")
    con.execute(consulta)

    entrada_mb = os.path.getsize(args.entrada) / (1024 ** 2)
    salida_mb = salida.stat().st_size / (1024 ** 2)
    print(f"Listo: {salida}")
    print(f"  entrada: {entrada_mb:,.0f} MB")
    print(f"  salida : {salida_mb:,.0f} MB")


def _componente_mas_grande(ruta: str) -> tuple[int, int]:
    """Conserva solo la componente conexa (no dirigida) más grande del CSV.

    Un muestreo aleatorio deja muchos nodos aislados. Quedarnos con la
    componente más grande hace que los algoritmos trabajen sobre una red
    conectada y los resultados sean interpretables.

    Retorna (filas_antes, filas_despues).
    """
    with open(ruta, newline="", encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))

    ady: dict[str, set[str]] = defaultdict(set)
    for fila in filas:
        a, b = fila["from_address"], fila["to_address"]
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

    conservadas = [f for f in filas if f["from_address"] in mejor and f["to_address"] in mejor]
    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=["from_address", "to_address", "value"])
        escritor.writeheader()
        escritor.writerows(conservadas)

    return len(filas), len(conservadas)


def muestra(args: argparse.Namespace) -> None:
    """Genera una muestra (CSV) a partir del Parquet o del CSV grande."""
    con = _conectar()
    columnas = _columnas(con, args.entrada)
    mapa = _mapear(columnas)
    _exigir_columnas(mapa, columnas)

    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)

    select = (
        f'CAST("{mapa["from"]}" AS VARCHAR) AS from_address, '
        f'CAST("{mapa["to"]}" AS VARCHAR) AS to_address, '
        f'CAST("{mapa["value"]}" AS DOUBLE) AS value'
    )

    filtros: list[str] = []
    if args.token:
        if not mapa["token"]:
            raise SystemExit("Pediste --token pero el archivo no tiene columna de token.")
        filtros.append(f'CAST("{mapa["token"]}" AS VARCHAR) = {_sql_texto(args.token)}')
    if args.desde:
        if not mapa["time"]:
            raise SystemExit("Pediste --desde pero el archivo no tiene columna de tiempo.")
        filtros.append(f'CAST("{mapa["time"]}" AS VARCHAR) >= {_sql_texto(args.desde)}')
    if args.hasta:
        if not mapa["time"]:
            raise SystemExit("Pediste --hasta pero el archivo no tiene columna de tiempo.")
        filtros.append(f'CAST("{mapa["time"]}" AS VARCHAR) <= {_sql_texto(args.hasta)}')

    where = ("WHERE " + " AND ".join(filtros)) if filtros else ""
    # El muestreo va DESPUÉS del filtro: así `--filas` cuenta las filas que
    # realmente cumplen las condiciones.
    consulta = (
        f"COPY (SELECT * FROM (SELECT {select} FROM {_fuente(args.entrada)} {where}) "
        f"USING SAMPLE {args.filas} ROWS) "
        f"TO {_sql_texto(salida)} (FORMAT CSV, HEADER)"
    )

    print("Generando muestra...")
    con.execute(consulta)

    antes = despues = 0
    if args.componente:
        print("Conservando la componente conexa más grande...")
        antes, despues = _componente_mas_grande(str(salida))
        print(f"  filas antes: {antes:,}")
        print(f"  filas después: {despues:,}")

    print(f"Listo: {salida}")


def info(args: argparse.Namespace) -> None:
    """Imprime estadísticas básicas del archivo procesado."""
    con = _conectar()
    fuente = _fuente(args.entrada)

    total = con.execute(f"SELECT count(*) FROM {fuente}").fetchone()[0]
    distintos = con.execute(
        f"SELECT count(DISTINCT from_address), count(DISTINCT to_address) FROM {fuente}"
    ).fetchone()
    tamano = os.path.getsize(args.entrada) / (1024 ** 2)

    print(f"Archivo: {args.entrada}")
    print(f"  tamaño: {tamano:,.0f} MB")
    print(f"  transferencias: {total:,}")
    print(f"  direcciones origen distintas: {distintos[0]:,}")
    print(f"  direcciones destino distintas: {distintos[1]:,}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="comando", required=True)

    p_conv = sub.add_parser("convertir", help="CSV grande -> Parquet comprimido")
    p_conv.add_argument("--entrada", required=True)
    p_conv.add_argument("--salida", required=True)
    p_conv.set_defaults(func=convertir)

    p_mues = sub.add_parser("muestra", help="Generar una muestra manejable")
    p_mues.add_argument("--entrada", required=True)
    p_mues.add_argument("--salida", required=True)
    p_mues.add_argument("--filas", type=int, default=100_000)
    p_mues.add_argument("--token", default=None, help="Filtrar por dirección de token")
    p_mues.add_argument("--desde", default=None, help="Fecha/hora mínima (texto)")
    p_mues.add_argument("--hasta", default=None, help="Fecha/hora máxima (texto)")
    p_mues.add_argument("--componente", action="store_true",
                        help="Conservar solo la componente conexa más grande")
    p_mues.set_defaults(func=muestra)

    p_info = sub.add_parser("info", help="Estadísticas del archivo")
    p_info.add_argument("--entrada", required=True)
    p_info.set_defaults(func=info)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
