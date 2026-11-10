"""
Pruebas de la capa compartida de evaluación (precisión@k y recall@k).

Ejecutar:
    python -m pytest tests/test_evaluacion.py -v
"""

import random

from src.evaluacion import encontrados_en_k, evaluar_ranking, ranking


def test_ranking_rompe_empates_por_direccion():
    assert ranking({"b": 1.0, "a": 1.0, "c": 5.0}) == ["c", "a", "b"]
    assert ranking({"b": 1.0, "a": 2.0}, mayor_es_mejor=False) == ["b", "a"]


def test_precision_y_recall():
    puntajes = {"ex1": 9, "x": 8, "ex2": 7, "y": 1, "z": 0}
    filas = evaluar_ranking(puntajes, {"ex1", "ex2", "no_esta"}, ks=(1, 2, 3))
    assert [f["encontrados"] for f in filas] == [1, 1, 2]
    assert filas[2]["precision"] == 2 / 3
    assert filas[2]["recall"] == 1.0   # "no_esta" no cuenta: no está en el grafo


def test_igual_a_conteo_directo():
    random.seed(1)
    puntajes = {f"n{i}": random.random() for i in range(500)}
    relevantes = set(random.sample(sorted(puntajes), 40))
    orden = sorted(puntajes, key=puntajes.get, reverse=True)
    for k in (10, 50, 100):
        esperado = len(set(orden[:k]) & relevantes)
        assert encontrados_en_k(ranking(puntajes), relevantes, k) == esperado
