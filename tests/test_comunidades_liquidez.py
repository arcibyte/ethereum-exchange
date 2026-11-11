"""
Pruebas de la Tarea 3 — Comunidades de liquidez (Louvain).

Responsable: Juan Pablo Álvarez.

Ejecutar solo esta tarea:
    python -m pytest tests/test_comunidades_liquidez.py -v
"""

import random

import pytest

from src.comunidades_liquidez import (
    barrido_resolucion,
    estabilidad_reinicios,
    grafo_no_dirigido,
    label_propagation,
    louvain,
    modularidad_definicion,
    modularity,
    nmi,
)

# Club de karate de Zachary (34 nodos, 78 aristas): referencia clásica.
# La mejor modularidad conocida para este grafo es Q = 0.4198.
KARATE = [
    (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8),
    (0, 10), (0, 11), (0, 12), (0, 13), (0, 17), (0, 19), (0, 21), (0, 31),
    (1, 2), (1, 3), (1, 7), (1, 13), (1, 17), (1, 19), (1, 21), (1, 30),
    (2, 3), (2, 7), (2, 8), (2, 9), (2, 13), (2, 27), (2, 28), (2, 32),
    (3, 7), (3, 12), (3, 13), (4, 6), (4, 10), (5, 6), (5, 10), (5, 16),
    (6, 16), (8, 30), (8, 32), (8, 33), (9, 33), (13, 33), (14, 32), (14, 33),
    (15, 32), (15, 33), (18, 32), (18, 33), (19, 33), (20, 32), (20, 33), (22, 32),
    (22, 33), (23, 25), (23, 27), (23, 29), (23, 32), (23, 33), (24, 25), (24, 27),
    (24, 31), (25, 31), (26, 29), (26, 33), (27, 33), (28, 31), (28, 33), (29, 32),
    (29, 33), (30, 32), (30, 33), (31, 32), (31, 33), (32, 33),
]


def _karate():
    adj = grafo_no_dirigido([(str(u), str(v), 1) for u, v in KARATE])
    return sorted(adj), adj


def _sin_lazos(nodos):
    return {u: 0.0 for u in nodos}


def _dos_cliques():
    """Dos cliques de 6 nodos unidas por una sola arista."""
    a = [f"a{i}" for i in range(6)]
    b = [f"b{i}" for i in range(6)]
    aristas = [(x, y, 5) for g in (a, b) for i, x in enumerate(g) for y in g[i + 1:]]
    aristas.append(("a0", "b0", 1))
    adj = grafo_no_dirigido(aristas)
    return sorted(adj), adj


# ---------------------------------------------------------------- grafo

def test_grafo_no_dirigido_suma_sentidos_e_ignora_lazos():
    adj = grafo_no_dirigido([("x", "y", 3), ("y", "x", 2), ("x", "x", 9), ("y", "z", 1)])
    assert adj["x"] == {"y": 5.0}
    assert adj["y"] == {"x": 5.0, "z": 1.0}
    assert "x" not in adj["x"]


# ---------------------------------------------------------------- modularidad

def test_modularidad_igual_a_la_definicion():
    nodos, adj = _karate()
    rng = random.Random(0)
    for _ in range(5):
        particion = {u: rng.randrange(4) for u in nodos}
        assert modularity(adj, _sin_lazos(nodos), particion) == pytest.approx(
            modularidad_definicion(adj, particion))


def test_particiones_triviales():
    nodos, adj = _karate()
    assert modularity(adj, _sin_lazos(nodos), {u: 0 for u in nodos}) == pytest.approx(0.0)
    assert modularity(adj, _sin_lazos(nodos), {u: u for u in nodos}) < 0


# ---------------------------------------------------------------- louvain

def test_louvain_karate_alcanza_el_optimo_conocido():
    nodos, adj = _karate()
    mem, q, niveles, _ = louvain(nodos, adj, n_restarts=10)
    assert q == pytest.approx(0.4198, abs=5e-4)
    assert q == pytest.approx(modularidad_definicion(adj, mem))
    assert 3 <= len(set(mem.values())) <= 5
    assert len(niveles) >= 1


def test_louvain_igual_a_networkx_en_karate():
    nx = pytest.importorskip("networkx")
    nodos, adj = _karate()
    mem, q, _, _ = louvain(nodos, adj, n_restarts=10)
    grupos = {}
    for u, c in mem.items():
        grupos.setdefault(c, set()).add(int(u))
    g = nx.Graph(KARATE)
    assert nx.community.modularity(g, grupos.values(), weight=None) == pytest.approx(q)


def test_louvain_y_label_propagation_separan_dos_cliques():
    nodos, adj = _dos_cliques()
    esperado = {u: u[0] for u in nodos}
    mem, q, _, _ = louvain(nodos, adj, n_restarts=3)
    assert nmi(mem, esperado) == pytest.approx(1.0)
    assert q > 0.4
    assert nmi(label_propagation(nodos, adj), esperado) == pytest.approx(1.0)


def test_louvain_es_reproducible_con_la_misma_semilla():
    nodos, adj = _karate()
    assert louvain(nodos, adj, n_restarts=3, base_seed=7)[0] == louvain(nodos, adj, n_restarts=3, base_seed=7)[0]


# ---------------------------------------------------------------- nmi

def test_nmi_propiedades():
    a = {"p": 1, "q": 1, "r": 2, "s": 2}
    assert nmi(a, {"p": "x", "q": "x", "r": "y", "s": "y"}) == pytest.approx(1.0)   # solo cambia el nombre
    assert nmi(a, {"p": 1, "q": 2, "r": 1, "s": 2}) == pytest.approx(0.0)           # independientes
    assert 0.0 <= nmi(a, {"p": 1, "q": 1, "r": 1, "s": 2}) <= 1.0


# ---------------------------------------------------------------- estabilidad y resolución

def test_estabilidad_reinicios():
    nodos, adj = _karate()
    filas = estabilidad_reinicios(nodos, adj, n_restarts=6)
    assert len(filas) == 6
    mejor = max(filas, key=lambda f: f["Q"])
    assert mejor["NMI_vs_mejor"] == pytest.approx(1.0)
    assert all(0.0 <= f["NMI_vs_mejor"] <= 1.0 + 1e-12 for f in filas)


def test_barrido_resolucion_mas_gamma_mas_comunidades():
    nodos, adj = _karate()
    filas = barrido_resolucion(nodos, adj, gammas=(0.5, 1.0, 3.0))
    comunidades = [f["comunidades"] for f in filas]
    assert comunidades[0] <= comunidades[1] <= comunidades[2]
    assert max(filas, key=lambda f: f["Q_gamma_1"])["gamma"] == 1.0
