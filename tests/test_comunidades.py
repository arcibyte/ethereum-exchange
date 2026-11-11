"""
Pruebas unitarias de la Tarea 3 — Detección de comunidades (Louvain).

Responsable: Emerson Ballesteros.

Ejecutar solo esta tarea:
    python -m pytest tests/test_comunidades.py -v
"""

from src.comunidades import louvain, modularidad, resumen_comunidades, simetrizar


# ---------- Simetrización del grafo ----------

def test_simetrizar_suma_pesos():
    adj = {"A": [("B", 3.0)], "B": [("A", 2.0), ("C", 1.0)], "C": []}
    sim = simetrizar(adj)

    # Reconstruimos un diccionario {par_ordenado: peso} para revisar fácil.
    pesos = {}
    for u, vecinos in sim.items():
        for v, w in vecinos:
            pesos[tuple(sorted((u, v)))] = w

    assert pesos[("A", "B")] == 5.0   # 3 + 2
    assert pesos[("B", "C")] == 1.0


def test_simetrizar_es_no_dirigido():
    # La arista {A,B} debe aparecer tanto desde A como desde B.
    adj = {"A": [("B", 1.0)], "B": []}
    sim = simetrizar(adj)
    assert ("B", 1.0) in sim["A"]
    assert ("A", 1.0) in sim["B"]


# ---------- Modularidad ----------

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


def test_modularidad_grafo_sin_aristas():
    # Sin aristas no hay estructura que medir: Q = 0.
    assert modularidad({"A": []}, {"A": 0}) == 0.0


def test_modularidad_una_sola_comunidad_es_cero():
    # Si todos los nodos están en la misma comunidad, Q debe ser 0.
    adj = {
        "A": [("B", 3.0)],
        "B": [("A", 3.0), ("C", 1.0)],
        "C": [("B", 1.0)],
    }
    comunidades = {"A": 0, "B": 0, "C": 0}
    assert abs(modularidad(adj, comunidades)) < 1e-12


def test_modularidad_coincide_con_la_formula_clasica():
    # Comparamos la versión por comunidad con la suma directa sobre pares.
    adj = {
        "A": [("B", 3.0), ("C", 1.0)],
        "B": [("A", 3.0)],
        "C": [("A", 1.0), ("D", 2.0)],
        "D": [("C", 2.0)],
    }
    comunidades = {"A": 0, "B": 0, "C": 1, "D": 1}

    grados = {v: sum(w for _, w in adj.get(v, [])) for v in adj}
    m = sum(grados.values()) / 2.0
    esperado = 0.0
    for i in adj:
        for j in adj:
            a_ij = sum(w for v, w in adj.get(i, []) if v == j)
            if comunidades[i] == comunidades[j]:
                esperado += a_ij - grados[i] * grados[j] / (2.0 * m)
    esperado /= 2.0 * m

    assert abs(modularidad(adj, comunidades) - esperado) < 1e-12


# ---------- Louvain ----------

def test_louvain_separa_dos_cliques():
    # Dos cliques unidas por una arista muy débil: deben quedar separadas.
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


def test_louvain_es_reproducible():
    # Con la misma semilla, el resultado debe ser idéntico.
    adj = {}

    def enlazar(u, v):
        adj.setdefault(u, []).append((v, 1.0))
        adj.setdefault(v, []).append((u, 1.0))

    for a, b in [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")]:
        enlazar(a, b)

    assert louvain(adj, semilla=7) == louvain(adj, semilla=7)


# ---------- Resumen de comunidades ----------

def test_resumen_comunidades():
    comunidades = {"A": 0, "B": 0, "C": 1}
    etiquetas = {
        "A": {"nombre": "Uniswap"},
        "B": {"nombre": "Curve"},
        "C": {"nombre": "Binance"},
    }
    resumen = resumen_comunidades(comunidades, etiquetas)
    assert sorted(resumen[0]) == ["Curve", "Uniswap"]
    assert resumen[1] == ["Binance"]
