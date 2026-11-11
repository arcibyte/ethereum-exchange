"""
Pruebas de la Tarea 2 — Centralidad e influencia.

Responsable: Jhon Arciniegas.

Ejecutar solo esta tarea:
    python -m pytest tests/test_centralidad.py -v
"""

from src.centralidad import centralidad_grado, pagerank, top_n


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


def test_centralidad_grado_nodo_unico():
    # Con un solo nodo el denominador es 0, debe devolver 0.0 sin errores.
    cent = centralidad_grado({"A": []}, {"A"})
    assert cent["A"] == 0.0


def test_centralidad_grado_nodo_aislado():
    # D no tiene ninguna arista (ni entrante ni saliente): centralidad = 0.
    adj = {"A": [("B", 1.0)], "B": [], "D": []}
    nodos = {"A", "B", "D"}
    cent = centralidad_grado(adj, nodos)
    assert cent["D"] == 0.0


def test_pagerank_grafo_vacio():
    # Sin nodos el resultado debe ser un diccionario vacío.
    assert pagerank({}, set()) == {}


def test_pagerank_nodo_mas_referenciado_tiene_mayor_score():
    # C recibe aristas de A y de B, así que debe tener el PageRank más alto.
    adj = {"A": [("C", 1.0)], "B": [("C", 1.0)], "C": []}
    nodos = {"A", "B", "C"}
    pr = pagerank(adj, nodos)
    assert pr["C"] > pr["A"]
    assert pr["C"] > pr["B"]


def test_top_n_sin_etiquetas():
    scores = {"A": 0.5, "B": 0.3, "C": 0.2}
    resultado = top_n(scores, n=2)
    assert len(resultado) == 2
    # El primero debe ser el de mayor score.
    assert resultado[0][0] == "A"
    assert resultado[0][1] == 0.5
    # Sin etiquetas, el nombre es la misma dirección.
    assert resultado[0][2] == "A"


def test_top_n_con_etiquetas():
    scores = {"0xabc": 0.9, "0xdef": 0.1}
    etiquetas = {"0xabc": {"nombre": "Uniswap"}}
    resultado = top_n(scores, n=1, etiquetas=etiquetas)
    assert resultado[0][0] == "0xabc"
    assert resultado[0][2] == "Uniswap"
