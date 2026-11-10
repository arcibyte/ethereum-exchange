"""
Pruebas de la Tarea 1 — Caminos de costo mínimo (Bellman-Ford).

Responsable: Pablo Álvarez.

Ejecutar solo esta tarea:
    python -m pytest tests/test_bellman_ford.py -v
"""

from src.bellman_ford import bellman_ford, reconstruir_camino


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
