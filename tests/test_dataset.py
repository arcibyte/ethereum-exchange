"""
Pruebas de la Sección 1 — Descripción y preparación del dataset.

Responsable: Pablo Álvarez.

Ejecutar solo esta sección:
    python -m pytest tests/test_dataset.py -v
"""

import csv
import os
import random

import pytest

from src.dataset import (
    DIRECCION_CERO,
    cargar_exchanges,
    componentes_debiles,
    exchanges_en_grafo,
    guardar_aristas,
    guardar_resumen,
    leer_resumen,
    leer_transferencias,
    limpiar_y_agregar,
    percentil_de_grado,
    perfil,
    resumir_por_token,
    valor_maximo,
)
from src.grafo import Grafo

CERO = DIRECCION_CERO
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_A = "0xaaa0000000000000000000000000000000000000"
TOKEN_B = "0xbbb0000000000000000000000000000000000000"


def _escribir(ruta, encabezado, filas):
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(encabezado)
        w.writerows(filas)
    return str(ruta)


@pytest.fixture()
def crudo(tmp_path):
    """Transferencias con todos los casos que la limpieza debe tratar."""
    filas = [
        # token A
        (TOKEN_A, CERO, "0xU1", "1e12", 100),      # mint
        (TOKEN_A, "0xU1", "0xEX", "4e11", 101),    # a un exchange
        (TOKEN_A, "0xU1", "0xEX", "1e11", 102),    # mismo par: se agrega
        (TOKEN_A, "0xEX", "0xU2", "2e11", 103),
        (TOKEN_A, "0xU2", "0xU2", "5e10", 104),    # autolazo
        (TOKEN_A, "0xU2", "0xU1", "0", 105),       # valor cero
        (TOKEN_A, "0xU2", "0xU1", "50", 106),      # polvo: 50 < 1e12 / 1e10
        (TOKEN_A, "0xU2", "0xU1", "abc", 107),     # valor inválido
        (TOKEN_A, "0xU2", CERO, "3e11", 108),      # burn
        # token B (otra unidad: no se mezcla con A)
        (TOKEN_B, "0xU1", "0xDX", "7", 200),
        (TOKEN_B, "0xDX", "0xU1", "7", 201),
    ]
    return _escribir(tmp_path / "crudo.csv",
                     ["token_address", "from_address", "to_address", "value", "block_number"],
                     filas)


@pytest.fixture()
def etiquetas(tmp_path):
    return _escribir(tmp_path / "etiquetas.csv", ["type", "address", "name"], [
        ("cex", "0xEX", "Binance 14"),
        ("dex", "0xDX", "Uniswap"),
        ("cex", "0xNOESTA", "Kraken 3"),
        ("cex", "0xPOLO", "Poloniex: BAT"),
    ])


# ---------------------------------------------------------------- lectura

def test_leer_normaliza_y_filtra_por_token(crudo):
    filas = list(leer_transferencias(crudo))
    assert len(filas) == 11
    assert filas[1] == (TOKEN_A, "0xu1", "0xex", 4e11, 101)   # minúsculas
    assert filas[7][3] is None                                 # "abc" -> None
    solo_b = list(leer_transferencias(crudo, token=TOKEN_B.upper()))
    assert [f[0] for f in solo_b] == [TOKEN_B, TOKEN_B]


def test_leer_formato_alphacore_sin_columna_token(tmp_path):
    ruta = _escribir(tmp_path / "scc.csv", ["source", "target", "amount", "blockNumber"],
                     [("0xA", "0xB", "3e+08", "6227591")])
    filas = list(leer_transferencias(ruta, token_por_defecto="scc"))
    assert filas == [("scc", "0xa", "0xb", 3e8, 6227591)]


def test_leer_sin_columnas_obligatorias(tmp_path):
    ruta = _escribir(tmp_path / "malo.csv", ["from_address", "value"], [("0xA", "1")])
    with pytest.raises(ValueError, match="destino"):
        list(leer_transferencias(ruta))


def test_cargar_exchanges(etiquetas):
    ex = cargar_exchanges(etiquetas)
    assert ex["0xex"] == {"nombre": "Binance 14", "tipo": "cex", "entidad": "Binance"}
    assert ex["0xdx"]["tipo"] == "dex"
    assert ex["0xpolo"]["entidad"] == "Poloniex"


# ---------------------------------------------------------------- resumen

def test_resumen_por_token(crudo, etiquetas):
    res = resumir_por_token(leer_transferencias(crudo), cargar_exchanges(etiquetas))
    a, b = res[TOKEN_A], res[TOKEN_B]
    assert a["transferencias"] == 9
    assert a["valor_invalido"] == 1 and a["valor_cero"] == 1
    assert a["autolazos"] == 1 and a["mint"] == 1 and a["burn"] == 1
    assert a["valor_max"] == 1e12
    assert (a["bloque_min"], a["bloque_max"]) == (100, 108)
    assert a["direcciones"] == 4          # cero, u1, ex, u2
    assert a["pares"] == 6                # (0,u1) (u1,ex) (ex,u2) (u2,u2) (u2,u1) (u2,0)
    assert (a["exchanges_presentes"], a["cex_presentes"], a["dex_presentes"]) == (1, 1, 0)
    assert b["transferencias"] == 2 and b["valor_max"] == 7
    assert (b["exchanges_presentes"], b["dex_presentes"]) == (1, 1)


def test_resumen_sin_distintos(crudo):
    res = resumir_por_token(leer_transferencias(crudo), contar_distintos=False)
    assert res[TOKEN_A]["direcciones"] is None and res[TOKEN_A]["pares"] is None
    assert res[TOKEN_A]["transferencias"] == 9


def test_resumen_ida_y_vuelta(crudo, tmp_path):
    res = resumir_por_token(leer_transferencias(crudo))
    ruta = str(tmp_path / "tokens.csv")
    guardar_resumen(res, ruta)
    assert leer_resumen(ruta) == res
    with open(ruta, encoding="utf-8") as f:
        primera = list(csv.DictReader(f))[0]
    assert primera["token_address"] == TOKEN_A   # ordenado por transferencias


# ---------------------------------------------------------------- limpieza

def test_limpiar_y_agregar_reglas(crudo):
    filas = list(leer_transferencias(crudo, token=TOKEN_A))
    aristas, rep = limpiar_y_agregar(filas, valor_maximo(filas))
    assert rep == {"leidas": 9, "valor_invalido": 1, "valor_cero": 1, "polvo": 1,
                   "autolazos": 1, "direccion_cero": 0, "conservadas": 5}
    assert aristas[("0xu1", "0xex")] == [5e11, 2]       # 4e11 + 1e11, 2 transferencias
    assert (CERO, "0xu1") in aristas and ("0xu2", CERO) in aristas
    assert ("0xu2", "0xu2") not in aristas


def test_limpiar_quitando_direccion_cero(crudo):
    filas = list(leer_transferencias(crudo, token=TOKEN_A))
    aristas, rep = limpiar_y_agregar(filas, valor_maximo(filas), quitar_direccion_cero=True)
    assert rep["direccion_cero"] == 2
    assert all(CERO not in par for par in aristas)


def test_archivo_limpio_lo_lee_grafo(crudo, tmp_path):
    """Contrato con las tareas 1-4: Grafo carga el archivo sin cambios."""
    filas = list(leer_transferencias(crudo, token=TOKEN_A))
    aristas, _ = limpiar_y_agregar(filas, valor_maximo(filas))
    ruta = str(tmp_path / "token_a.csv")
    guardar_aristas(aristas, ruta)

    grafo = Grafo().cargar_transferencias(ruta)
    assert len(grafo.aristas) == len(aristas) == 4
    assert grafo.nodos == {CERO, "0xu1", "0xex", "0xu2"}
    assert ("0xex", 5e11) in grafo.adj["0xu1"]


def test_guardar_aristas_es_determinista(crudo, tmp_path):
    filas = list(leer_transferencias(crudo, token=TOKEN_A))
    aristas, _ = limpiar_y_agregar(filas, valor_maximo(filas))
    r1, r2 = str(tmp_path / "1.csv"), str(tmp_path / "2.csv")
    guardar_aristas(aristas, r1)
    guardar_aristas(dict(reversed(list(aristas.items()))), r2)
    assert open(r1, encoding="utf-8").read() == open(r2, encoding="utf-8").read()


# ---------------------------------------------------------------- perfil

def _grafo(tmp_path, pares):
    ruta = _escribir(tmp_path / "g.csv", ["from_address", "to_address", "value"],
                     [(a, b, 1) for a, b in pares])
    return Grafo().cargar_transferencias(ruta)


def test_perfil_basico(tmp_path):
    g = _grafo(tmp_path, [("a", "b"), ("b", "a"), ("b", "c"), ("d", "e")])
    p = perfil(g)
    assert (p["nodos"], p["aristas"]) == (5, 4)
    assert p["reciprocidad"] == 0.5             # a->b y b->a de 4 aristas
    assert (p["componentes"], p["componente_mayor"]) == (2, 3)
    assert p["fuentes"] == 1                    # d
    assert p["sumideros"] == 2                  # c, e
    assert p["densidad"] == 4 / (5 * 4)


def test_perfil_igual_a_networkx(tmp_path):
    nx = pytest.importorskip("networkx")
    random.seed(0)
    pares = {(f"n{random.randrange(60)}", f"n{random.randrange(60)}") for _ in range(150)}
    pares = [(a, b) for a, b in pares if a != b]
    g = _grafo(tmp_path, pares)
    ref = nx.DiGraph(pares)
    p = perfil(g)
    assert p["reciprocidad"] == pytest.approx(nx.reciprocity(ref))
    tam_ref = sorted((len(c) for c in nx.weakly_connected_components(ref)), reverse=True)
    assert componentes_debiles(g.adj, g.nodos) == tam_ref


def test_percentil_y_exchanges_en_grafo(etiquetas):
    grado = {"a": 1, "b": 2, "c": 2, "d": 10}
    pct = percentil_de_grado(grado, ["a", "b", "d"])
    assert pct == {"a": 0.0, "b": pytest.approx(100 / 3), "d": 100.0}
    ex = exchanges_en_grafo({"0xex", "0xu1"}, cargar_exchanges(etiquetas))
    assert list(ex) == ["0xex"]


# ---------------------------------------------------------------- datos reales

def test_etiquetas_reales():
    ex = cargar_exchanges(os.path.join(RAIZ, "data/real/exchange_labels.csv"))
    assert len(ex) == 296
    tipos = [v["tipo"] for v in ex.values()]
    assert tipos.count("cex") == 247 and tipos.count("dex") == 49
    assert len({v["entidad"].lower() for v in ex.values()}) == 150


def test_softchaincoin_real_reproduce_archivo_versionado(tmp_path):
    filas = list(leer_transferencias(os.path.join(RAIZ, "data/real/softchaincoin.csv")))
    aristas, rep = limpiar_y_agregar(filas, valor_maximo(filas))
    assert rep["leidas"] == 278 and rep["conservadas"] == 278
    ruta = str(tmp_path / "scc.csv")
    guardar_aristas(aristas, ruta)
    with open(ruta, encoding="utf-8") as nuevo, \
            open(os.path.join(RAIZ, "data/tokens/softchaincoin.csv"), encoding="utf-8") as versionado:
        assert nuevo.read() == versionado.read()
    p = perfil(Grafo().cargar_transferencias(ruta))
    assert (p["nodos"], p["aristas"], p["componentes"]) == (197, 252, 1)
