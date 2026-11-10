"""
centralidad.py
==============
Tarea 2 — Centralidad e influencia.

Queremos responder: ¿qué nodos son los más importantes en la red?

Calculamos dos medidas:

    1. Centralidad de grado: cuántas conexiones tiene un nodo.
       C(v) = grado(v) / (|V| - 1)

    2. PageRank: la importancia de un nodo depende de la importancia de
       quienes le apuntan (es la misma idea que usa el buscador de Google).
       PR(v) = (1-d)/N + d * suma_{u -> v} ( PR(u) / grado_salida(u) )

       donde d es el factor de amortiguación (0.85 por defecto).
"""

from typing import Dict, List, Optional, Set, Tuple


def centralidad_grado(
    adj: Dict[str, List[Tuple[str, float]]],
    nodos: Set[str],
) -> Dict[str, float]:
    """Centralidad de grado normalizada: C(v) = grado(v) / (|V| - 1).

    En un grafo dirigido contamos grado de salida + grado de entrada.

    Parámetros:
        adj: lista de adyacencia.
        nodos: conjunto de todos los vértices.

    Retorna:
        {nodo: centralidad} con valores entre 0 y 1.
    """
    n = len(nodos)
    if n <= 1:
        return {v: 0.0 for v in nodos}

    grados = {v: 0 for v in nodos}
    for u, vecinos in adj.items():
        grados[u] += len(vecinos)   # grado de salida
        for v, _ in vecinos:
            grados[v] += 1          # grado de entrada

    return {v: grados[v] / (n - 1) for v in nodos}


def pagerank(
    adj: Dict[str, List[Tuple[str, float]]],
    nodos: Set[str],
    amortiguacion: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-6,
) -> Dict[str, float]:
    """Calcula PageRank con el método de iteración de potencias.

    Parámetros:
        adj: lista de adyacencia.
        nodos: conjunto de todos los vértices.
        amortiguacion: factor de amortiguación d (0.85 por defecto).
        max_iter: máximo número de iteraciones.
        tol: tolerancia de convergencia.

    Retorna:
        {nodo: score} con scores que suman aproximadamente 1.
    """
    n = len(nodos)
    if n == 0:
        return {}

    lista = list(nodos)

    # Puntaje inicial: todos los nodos igual de importantes (1/N).
    pr = {v: 1.0 / n for v in lista}

    # Grado de salida de cada nodo.
    grado_salida = {v: len(adj.get(v, [])) for v in lista}

    # Lista de adyacencia INVERSA: quién apunta a cada nodo.
    # Esto hace el cálculo más directo y eficiente.
    entrantes = {v: [] for v in lista}
    for u, vecinos in adj.items():
        for v, _ in vecinos:
            if v in entrantes:
                entrantes[v].append(u)

    for _ in range(max_iter):
        base = (1.0 - amortiguacion) / n
        nuevo = {}
        for v in lista:
            suma = 0.0
            for u in entrantes[v]:
                if grado_salida[u] > 0:
                    suma += pr[u] / grado_salida[u]
            nuevo[v] = base + amortiguacion * suma

        # Medimos cuánto cambió el vector para saber si ya convergió.
        delta = sum(abs(nuevo[v] - pr[v]) for v in lista)
        pr = nuevo
        if delta < tol:
            break

    return pr


def top_n(
    puntajes: Dict[str, float],
    n: int = 10,
    etiquetas: Optional[Dict[str, Dict[str, str]]] = None,
) -> List[Tuple[str, float, str]]:
    """Devuelve los `n` nodos con mayor puntaje, ordenados de mayor a menor.

    Retorna:
        Lista de tuplas (dirección, puntaje, nombre) para mostrarlos bonito.
    """
    ordenados = sorted(puntajes.items(), key=lambda par: par[1], reverse=True)[:n]

    resultado = []
    for addr, score in ordenados:
        nombre = addr
        if etiquetas and addr in etiquetas:
            nombre = etiquetas[addr].get("nombre", addr)
        resultado.append((addr, round(score, 6), nombre))
    return resultado
