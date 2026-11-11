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


# ---------------------------------------------------------------- pasadas

from math import exp, isclose, log  # noqa: E402

import pytest  # noqa: E402

from src.bellman_ford import adyacencia_probabilidad, bellman_ford_con_pasadas  # noqa: E402


def test_pasadas_con_parada_temprana():
    # Cadena de 50 nodos: el peor caso serían 49 pasadas.
    nodos = [f"n{i}" for i in range(50)]
    adj = {u: [(v, 1.0)] for u, v in zip(nodos, nodos[1:])}
    dist, _, pasadas = bellman_ford_con_pasadas(adj, "n0")
    assert dist["n49"] == 49.0
    assert pasadas == 2          # 1 pasada que relaja todo en orden + 1 que confirma
    assert pasadas < len(nodos) - 1


def test_pasadas_no_superan_saltos_mas_uno():
    # Aristas en orden inverso: cada pasada solo avanza un salto.
    nodos = [f"n{i}" for i in range(6)]
    adj = {u: [(v, 1.0)] for u, v in reversed(list(zip(nodos, nodos[1:])))}
    _, _, pasadas = bellman_ford_con_pasadas(adj, "n0")
    assert pasadas <= 5 + 1


def test_ciclo_negativo():
    adj = {"A": [("B", 1.0)], "B": [("C", -2.0)], "C": [("A", -2.0)]}
    with pytest.raises(ValueError, match="ciclo de peso negativo"):
        bellman_ford(adj, "A")


# ---------------------------------------------------------------- probabilidad

def test_adyacencia_probabilidad_costos():
    aristas = [("A", "B", 30.0), ("A", "B", 10.0), ("A", "C", 60.0),
               ("B", "C", 5.0), ("C", "C", 9.0), ("C", "A", 0.0)]
    adj = adyacencia_probabilidad(aristas)
    costos = {(u, v): c for u, vecinos in adj.items() for v, c in vecinos}
    assert isclose(costos[("A", "B")], -log(0.4))      # 40 de 100
    assert isclose(costos[("A", "C")], -log(0.6))
    assert costos[("B", "C")] == 0.0                   # B solo envía a C
    assert "C" not in adj                              # autolazo y monto 0 ignorados


def test_camino_mas_probable():
    # A reparte 50/50 entre B y C; B manda todo a D; C manda 10% a D.
    aristas = [("A", "B", 1.0), ("A", "C", 1.0), ("B", "D", 7.0),
               ("C", "D", 1.0), ("C", "E", 9.0)]
    dist, prev = bellman_ford(adyacencia_probabilidad(aristas), "A")
    assert reconstruir_camino(prev, "A", "D") == ["A", "B", "D"]
    assert isclose(exp(-dist["D"]), 0.5)
    assert isclose(exp(-dist["E"]), 0.5 * 0.9)
