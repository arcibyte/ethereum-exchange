"""
Pruebas de la capa compartida de datos (`src/grafo.py`).

Cubren la carga desde CSV, la carga desde Parquet (si DuckDB está instalado),
la limpieza de transferencias inválidas y la componente conexa mayor.

Ejecutar:
    python -m pytest tests/test_grafo.py -v
"""

import csv

import pytest

from src.grafo import DIRECCION_CERO, Grafo


# ---------- CSV ----------

def test_cargar_csv_arma_grafo(tmp_path):
    ruta = tmp_path / "transferencias.csv"
    with ruta.open("w", newline="", encoding="utf-8") as fh:
        escritor = csv.writer(fh)
        escritor.writerow(["from_address", "to_address", "value"])
        escritor.writerow(["0xaaa", "0xbbb", "10"])
        escritor.writerow(["0xbbb", "0xccc", "20"])

    grafo = Grafo().cargar_transferencias(str(ruta))

    assert grafo.nodos == {"0xaaa", "0xbbb", "0xccc"}
    assert len(grafo.aristas) == 2
    assert grafo.adj["0xaaa"] == [("0xbbb", 10.0)]
    assert grafo.resumen()["peso_total"] == 30.0


def test_cargar_csv_limpia_invalidas(tmp_path):
    ruta = tmp_path / "transferencias.csv"
    with ruta.open("w", newline="", encoding="utf-8") as fh:
        escritor = csv.writer(fh)
        escritor.writerow(["from_address", "to_address", "value"])
        escritor.writerow(["0xaaa", "0xbbb", "10"])
        escritor.writerow(["0xaaa", "0xaaa", "5"])          # auto-loop
        escritor.writerow([DIRECCION_CERO, "0xbbb", "7"])   # dirección cero
        escritor.writerow(["0xbbb", "0xccc", "-3"])         # valor negativo

    grafo = Grafo().cargar_transferencias(str(ruta))

    assert len(grafo.aristas) == 1
    assert grafo.nodos == {"0xaaa", "0xbbb"}


def test_cargar_detecta_csv(tmp_path):
    ruta = tmp_path / "transferencias.csv"
    with ruta.open("w", newline="", encoding="utf-8") as fh:
        fh.write("from,to,value\nA,B,1\n")

    grafo = Grafo().cargar(str(ruta))
    assert grafo.nodos == {"a", "b"}


def test_conservar_componente_mayor():
    grafo = Grafo()
    grafo._agregar_arista("A", "B", 1.0)
    grafo._agregar_arista("B", "C", 1.0)
    grafo._agregar_arista("D", "E", 1.0)

    grafo.conservar_componente_mayor()

    assert grafo.nodos == {"A".lower(), "B".lower(), "C".lower()}
    assert len(grafo.aristas) == 2


def test_cargar_etiquetas_en_latin1(tmp_path):
    ruta = tmp_path / "etiquetas.csv"
    ruta.write_bytes(
        "address,name,type\n0xaaa,Café Central,dex\n".encode("latin-1")
    )

    grafo = Grafo().cargar_etiquetas(str(ruta))

    assert grafo.nombre("0xaaa") == "Café Central"


# ---------- Parquet (opcional) ----------

@pytest.fixture()
def parquet(tmp_path):
    duckdb = pytest.importorskip("duckdb")
    ruta = tmp_path / "transferencias.parquet"
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE t ("
        "from_address VARCHAR, to_address VARCHAR, value DOUBLE, "
        "token_address VARCHAR, block_timestamp VARCHAR)"
    )
    con.executemany(
        "INSERT INTO t VALUES (?, ?, ?, ?, ?)",
        [
            ("0xaaa", "0xbbb", 10.0, "0xtoken", "2024-01-01 00:00:00"),
            ("0xbbb", "0xccc", 20.0, "0xtoken", "2024-01-02 00:00:00"),
            ("0xccc", "0xaaa", 30.0, "0xtoken", "2024-01-03 00:00:00"),
            ("0xddd", "0xeee", 40.0, "0xotro", "2024-01-03 00:00:00"),
        ],
    )
    con.execute(f"COPY t TO '{ruta}' (FORMAT PARQUET)")
    con.close()
    return str(ruta)


def test_cargar_parquet(parquet):
    grafo = Grafo().cargar(parquet)

    assert len(grafo.aristas) == 4
    assert grafo.nodos == {"0xaaa", "0xbbb", "0xccc", "0xddd", "0xeee"}


def test_cargar_parquet_filtra_token(parquet):
    grafo = Grafo().cargar(parquet, token="0xotro")

    assert len(grafo.aristas) == 1
    assert grafo.nodos == {"0xddd", "0xeee"}


def test_cargar_parquet_muestra(parquet):
    grafo = Grafo().cargar(parquet, muestra=2, semilla=7)

    assert len(grafo.aristas) == 2


def test_cargar_parquet_ventana_de_tiempo(parquet):
    grafo = Grafo().cargar(parquet, desde="2024-01-02", hasta="2024-01-02 23:59:59")

    assert len(grafo.aristas) == 1
    assert grafo.aristas[0][0] == "0xbbb"
