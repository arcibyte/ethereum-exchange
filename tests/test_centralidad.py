"""
Pruebas de la Tarea 2 — Centralidad e influencia.

Responsable: Jhon Arciniegas.

Ejecutar solo esta tarea:
    python -m pytest tests/test_centralidad.py -v
"""

from src.centralidad import centralidad_grado, pagerank


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


def test_pagerank_con_sumidero_suma_uno():
    # B no tiene aristas de salida (sumidero). Su masa debe repartirse para
    # que los puntajes sigan sumando 1.
    adj = {"A": [("B", 1.0)], "B": []}
    pr = pagerank(adj, {"A", "B"})
    assert abs(sum(pr.values()) - 1.0) < 0.01
