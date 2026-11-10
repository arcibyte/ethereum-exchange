"""
Pruebas unitarias de los algoritmos del proyecto.

Ejecutar con:
    python -m pytest tests/ -v
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.bellman_ford import bellman_ford, reconstruir_camino
from src.centralidad import centralidad_grado, pagerank
from src.comunidades import louvain, modularidad
from src.arbol_expansion import UnionFind, aristas_no_dirigidas, kruskal


# ---------- Bellman-Ford (Tarea 1) ----------

def test_bellman_ford_camino_simple():
    adj = {"A": [("B", 2.0), ("C", 5.0)], "B": [("C", 1.0)], "C": []}
    dist, _ = bellman_ford(adj, "A")
    assert dist["A"] == 0.0
    assert dist["B"] == 2.0
    assert dist["C"] == 3.0   # A -> B -> C cuesta 2 + 1


def test_bellman_ford_nodo_inalcanzable():
    adj = {"A": [("B", 1.0)], "B": [], "C": []}
    dist, _ = bellman_ford(adj, "A")
    assert dist["C"] == float("inf")


def test_reconstruir_camino():
    adj = {"A": [("B", 1.0)], "B": [("C", 1.0)], "C": []}
    _, prev = bellman_ford(adj, "A")
    assert reconstruir_camino(prev, "A", "C") == ["A", "B", "C"]


# ---------- Centralidad (Tarea 2) ----------

def test_centralidad_grado():
    adj = {"A": [("B", 1.0)], "B": []}
    nodos = {"A", "B"}
    cent = centralidad_grado(adj, nodos)
    # A tiene grado 1 (salida), B tiene grado 1 (entrada): 1 / (2 - 1)
    assert cent["A"] == 1.0
    assert cent["B"] == 1.0


def test_pagerank_suma_uno():
    adj = {"A": [("B", 1.0), ("C", 1.0)], "B": [("C", 1.0)], "C": [("A", 1.0)]}
    nodos = {"A", "B", "C"}
    pr = pagerank(adj, nodos)
    assert abs(sum(pr.values()) - 1.0) < 0.01


# ---------- Comunidades (Tarea 3) ----------

def test_modularidad_particion_buena():
    # Dos triángulos separados: Q debe ser alta y positiva.
    adj = {
        "A": [("B", 1.0), ("C", 1.0)],
        "B": [("A", 1.0), ("C", 1.0)],
        "C": [("A", 1.0), ("B", 1.0)],
        "D": [("E", 1.0), ("F", 1.0)],
        "E": [("D", 1.0), ("F", 1.0)],
        "F": [("D", 1.0), ("E", 1.0)],
    }
    comunidades = {"A": 0, "B": 0, "C": 0, "D": 1, "E": 1, "F": 1}
    assert modularidad(adj, comunidades) > 0.3


def test_louvain_separa_comunidades():
    # Dos cliques unidas por una arista muy débil.
    adj = {}

    def enlazar(u, v, w=1.0):
        adj.setdefault(u, []).append((v, w))
        adj.setdefault(v, []).append((u, w))

    for a, b in [("A", "B"), ("A", "C"), ("B", "C")]:
        enlazar(a, b)
    for a, b in [("D", "E"), ("D", "F"), ("E", "F")]:
        enlazar(a, b)
    enlazar("C", "D", 0.1)

    comunidades = louvain(adj, semilla=1)
    assert comunidades["A"] == comunidades["B"] == comunidades["C"]
    assert comunidades["D"] == comunidades["E"] == comunidades["F"]
    assert comunidades["A"] != comunidades["D"]


# ---------- Árbol de expansión mínima (Tarea 4) ----------

def test_union_find():
    uf = UnionFind({"A", "B", "C"})
    assert uf.unir("A", "B") is True
    assert uf.unir("A", "B") is False   # ya estaban unidos
    assert uf.unir("B", "C") is True


def test_aristas_no_dirigidas():
    aristas = [("A", "B", 3.0), ("B", "A", 2.0), ("B", "C", 1.0)]
    resultado = aristas_no_dirigidas(aristas)
    assert len(resultado) == 2
    pesos = {tuple(sorted((a, b))): w for a, b, w in resultado}
    assert pesos[("A", "B")] == 5.0   # 3 + 2
    assert pesos[("B", "C")] == 1.0


def test_kruskal_mst():
    nodos = {"A", "B", "C"}
    aristas = [("A", "B", 1.0), ("B", "C", 2.0), ("A", "C", 3.0)]
    mst, costo = kruskal(nodos, aristas)
    assert len(mst) == 2          # |V| - 1
    assert costo == 3.0           # 1 + 2
