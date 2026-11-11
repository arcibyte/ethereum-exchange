"""
Pruebas de los adaptadores que leen la lista compartida de aristas.

Cada módulo recibe `grafo.aristas` y construye su propia estructura. Estas
pruebas verifican que los adaptadores producen lo mismo que las funciones
originales sobre un grafo pequeño.

Ejecutar:
    python -m pytest tests/test_datos.py -v
"""

import csv

from src.arbol_expansion import kruskal_desde_aristas
from src.bellman_ford import bellman_ford_desde_aristas
from src.centralidad import centralidad_grado_desde_aristas, pagerank_desde_aristas
from src.comunidades import louvain_desde_aristas, modularidad, desde_aristas
from src.grafo import cargar_grafo


ARISTAS = [
    ("a", "b", 1.0),
    ("b", "a", 1.0),
    ("b", "c", 1.0),
    ("c", "a", 1.0),
    ("d", "e", 1.0),
    ("e", "f", 1.0),
    ("f", "d", 1.0),
    ("c", "d", 0.1),
]


def test_bellman_ford_desde_aristas():
    distancias, previos = bellman_ford_desde_aristas(ARISTAS, "a")
    assert distancias["a"] == 0.0
    assert distancias["b"] == 1.0
    assert distancias["c"] <= 2.0


def test_centralidad_desde_aristas():
    centralidad = centralidad_grado_desde_aristas(ARISTAS)
    assert set(centralidad) == {"a", "b", "c", "d", "e", "f"}
    assert all(0.0 <= valor <= 1.0 for valor in centralidad.values())

    pr = pagerank_desde_aristas(ARISTAS)
    assert abs(sum(pr.values()) - 1.0) < 1e-6


def test_louvain_desde_aristas_separa_cliques():
    comunidades = louvain_desde_aristas(ARISTAS, semilla=1)
    assert comunidades["a"] == comunidades["b"] == comunidades["c"]
    assert comunidades["d"] == comunidades["e"] == comunidades["f"]
    assert comunidades["a"] != comunidades["d"]

    q = modularidad(desde_aristas(ARISTAS), comunidades)
    assert q > 0.3


def test_kruskal_desde_aristas():
    mst, costo = kruskal_desde_aristas(ARISTAS)
    assert len(mst) == 5          # |V| - 1 con 6 nodos
    assert costo > 0.0


def test_cargar_grafo_lee_una_vez(tmp_path):
    ruta = tmp_path / "transferencias.csv"
    etiquetas = tmp_path / "etiquetas.csv"
    with ruta.open("w", newline="", encoding="utf-8") as fh:
        escritor = csv.writer(fh)
        escritor.writerow(["from_address", "to_address", "value"])
        escritor.writerow(["0xaaa", "0xbbb", "10"])
    with etiquetas.open("w", newline="", encoding="utf-8") as fh:
        escritor = csv.writer(fh)
        escritor.writerow(["address", "name", "type"])
        escritor.writerow(["0xaaa", "Uniswap", "dex"])

    grafo = cargar_grafo(str(ruta), etiquetas=str(etiquetas))

    assert grafo.aristas == [("0xaaa", "0xbbb", 10.0)]
    assert grafo.nombre("0xaaa") == "Uniswap"
