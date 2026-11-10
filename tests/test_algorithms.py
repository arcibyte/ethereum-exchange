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
