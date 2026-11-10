"""
preparar_seccion1.py
====================
Sección 1 (Pablo Álvarez): genera, a partir del CSV completo del dataset, los
archivos pequeños que usa el notebook. Solo usa la librería estándar.

Comandos
--------
1) Resumen de los 28 tokens (una sola pasada sobre el CSV de ~8 GB):

    python scripts/preparar_seccion1.py resumen \
        --entrada /ruta/token_transfers_full.csv \
        --salida data/resumen/tokens.csv

2) Aristas limpias y agregadas de un token (la entrada de las tareas 1-4):

    python scripts/preparar_seccion1.py exportar \
        --entrada /ruta/token_transfers_full.csv \
        --token 0xdirecciondeltoken \
        --resumen data/resumen/tokens.csv \
        --salida data/tokens/<nombre>.csv

   Con --resumen se reutiliza el valor máximo del token (para el umbral de
   polvo) y se lee el CSV una sola vez. Sin --resumen se lee dos veces.

Ambos archivos de salida pesan poco y se suben al repositorio, así el profesor
ejecuta el notebook sin descargar el dataset.
"""

import argparse
import os
import sys
import time

# Permite ejecutar el script desde la raíz del repositorio.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.dataset import (  # noqa: E402
    cargar_exchanges,
    guardar_aristas,
    guardar_resumen,
    leer_resumen,
    leer_transferencias,
    limpiar_y_agregar,
    resumir_por_token,
    valor_maximo,
)

RUTA_ETIQUETAS = "data/real/exchange_labels.csv"


def _con_progreso(filas, cada=1_000_000):
    """Reenvía las filas e imprime el avance cada `cada` filas."""
    inicio = time.perf_counter()
    n = 0
    for n, fila in enumerate(filas, 1):
        if n % cada == 0:
            seg = time.perf_counter() - inicio
            print(f"  {n:>12,} filas  ({seg:,.0f} s, {n / seg:,.0f} filas/s)", flush=True)
        yield fila
    print(f"  {n:>12,} filas en total ({time.perf_counter() - inicio:,.1f} s)")


def _crear_carpeta(ruta):
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)


def comando_resumen(args):
    exchanges = cargar_exchanges(args.etiquetas)
    print(f"Leyendo {args.entrada} ...")
    resumen = resumir_por_token(
        _con_progreso(leer_transferencias(args.entrada, token_por_defecto=args.token_por_defecto)),
        exchanges,
        contar_distintos=not args.sin_distintos,
    )
    _crear_carpeta(args.salida)
    guardar_resumen(resumen, args.salida)
    total = sum(d["transferencias"] for d in resumen.values())
    print(f"Listo: {args.salida} ({len(resumen)} tokens, {total:,} transferencias)")


def comando_exportar(args):
    token = args.token.strip().lower()
    if args.resumen:
        resumen = leer_resumen(args.resumen)
        if token not in resumen:
            raise SystemExit(f"El token {token} no está en {args.resumen}.")
        vmax = resumen[token]["valor_max"]
    else:
        print("Primera pasada: valor máximo del token ...")
        vmax = valor_maximo(_con_progreso(leer_transferencias(
            args.entrada, token=token, token_por_defecto=args.token_por_defecto)))

    print(f"Limpiando y agregando {token} (valor máximo = {vmax:.4g}) ...")
    aristas, reporte = limpiar_y_agregar(
        _con_progreso(leer_transferencias(args.entrada, token=token,
                                          token_por_defecto=args.token_por_defecto)),
        vmax,
        quitar_direccion_cero=args.quitar_cero,
    )
    _crear_carpeta(args.salida)
    guardar_aristas(aristas, args.salida)

    print("Reporte de limpieza:")
    for clave, valor in reporte.items():
        print(f"  {clave:<15} {valor:>12,}")
    peso_mb = os.path.getsize(args.salida) / 2**20
    print(f"Listo: {args.salida} ({len(aristas):,} aristas, {peso_mb:,.1f} MB)")
    if peso_mb > 50:
        print("Aviso: más de 50 MB. GitHub rechaza archivos de más de 100 MB; "
              "considera un token más pequeño para la versión del repositorio.")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="comando", required=True)

    p_res = sub.add_parser("resumen", help="Estadísticas por token del CSV completo")
    p_res.add_argument("--entrada", required=True)
    p_res.add_argument("--salida", default="data/resumen/tokens.csv")
    p_res.add_argument("--etiquetas", default=RUTA_ETIQUETAS)
    p_res.add_argument("--token-por-defecto", default="sin_token",
                       help="Token asignado si el CSV no tiene columna token_address")
    p_res.add_argument("--sin-distintos", action="store_true",
                       help="No contar direcciones ni pares distintos (usa poca RAM)")
    p_res.set_defaults(func=comando_resumen)

    p_exp = sub.add_parser("exportar", help="Aristas limpias y agregadas de un token")
    p_exp.add_argument("--entrada", required=True)
    p_exp.add_argument("--token", required=True)
    p_exp.add_argument("--salida", required=True)
    p_exp.add_argument("--resumen", default=None,
                       help="tokens.csv generado con 'resumen' (evita una pasada)")
    p_exp.add_argument("--quitar-cero", action="store_true",
                       help="Descartar también mint/burn (dirección 0x000...000)")
    p_exp.add_argument("--token-por-defecto", default="sin_token")
    p_exp.set_defaults(func=comando_exportar)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
