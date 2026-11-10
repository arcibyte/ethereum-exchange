"""
Pruebas del módulo de análisis (dataset completo + benchmark).

Se saltan automáticamente si `duckdb` no está instalado, porque es una
dependencia opcional de preprocesamiento.

Ejecutar:
    python -m pytest tests/test_analisis.py -v
"""

import pytest

duckdb = pytest.importorskip("duckdb")

from src.analisis import (  # noqa: E402
    abrir,
    benchmark,
    componente_mas_grande,
    estadisticas,
    extraer_base,
)


@pytest.fixture()
def parquet(tmp_path):
    """Crea un Parquet pequeño con datos realistas de prueba."""
    ruta = tmp_path / "transferencias.parquet"
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE t ("
        "from_address VARCHAR, to_address VARCHAR, value DOUBLE, "
        "token_address VARCHAR, block_timestamp VARCHAR)"
    )
    filas = [
        ("A", "B", 10.0, "0xtoken", "2024-01-01 00:00:00"),
        ("B", "C", 20.0, "0xtoken", "2024-01-01 00:01:00"),
        ("C", "A", 30.0, "0xtoken", "2024-01-02 00:00:00"),
        ("D", "E", 40.0, "0xtoken", "2024-01-02 00:01:00"),
        ("A", "D", 50.0, "0xtoken", "2024-01-03 00:00:00"),
    ]
    con.executemany("INSERT INTO t VALUES (?, ?, ?, ?, ?)", filas)
    con.execute(f"COPY t TO '{ruta}' (FORMAT PARQUET)")
    con.close()
    return str(ruta)


def test_estadisticas_resumen(parquet):
    con = abrir()
    datos = estadisticas(con, parquet)
    assert datos["resumen"]["transferencias"] == 5
    assert datos["resumen"]["origenes"] == 4   # A, B, C, D
    assert datos["resumen"]["destinos"] == 5   # B, C, A, E, D
    assert datos["actividad"] is not None
    assert datos["tokens"] == [("0xtoken", 5)]


def test_extraer_base(parquet):
    con = abrir()
    aristas = extraer_base(con, parquet, 3)
    assert len(aristas) == 3
    assert all(len(a) == 3 for a in aristas)


def test_componente_mas_grande():
    aristas = [
        ("A", "B", 1.0), ("B", "C", 1.0),      # componente de 3
        ("D", "E", 1.0),                        # componente de 2
        ("F", "G", 1.0),                        # componente de 2
    ]
    filtradas = componente_mas_grande(aristas)
    assert len(filtradas) == 2
    assert {a for a, _, _ in filtradas} == {"A", "B"}
    assert {b for _, b, _ in filtradas} == {"B", "C"}


def test_benchmark_devuelve_tiempos(parquet):
    con = abrir()
    base = extraer_base(con, parquet, 10)
    filas = benchmark(base, [5, 10], repeticiones=1, timeout=5, verbose=False)

    # 4 algoritmos x 2 tamaños
    assert len(filas) == 8
    assert {f["algoritmo"] for f in filas} == {
        "Bellman-Ford", "PageRank", "Louvain", "Kruskal"
    }
    for f in filas:
        assert f["tiempo"] is None or f["tiempo"] >= 0
