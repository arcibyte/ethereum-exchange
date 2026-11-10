"""
Pruebas de la Tarea 4 — Árbol de expansión mínima (Kruskal + Union-Find).

Responsable: grupo.

Ejecutar solo esta tarea:
    python -m pytest tests/test_arbol_expansion.py -v
"""

from src.arbol_expansion import UnionFind, aristas_no_dirigidas, kruskal


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
