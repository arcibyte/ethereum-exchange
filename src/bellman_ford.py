"""
bellman_ford.py – Tarea 1: Caminos mínimos sin Dijkstra.

Responsable: Pablo Álvarez

Problema real:
    En la red de transferencias de tokens Ethereum, un actor malicioso puede
    intentar mover fondos a través de la menor cantidad de intermediarios
    posibles (lavado de dinero, arbitraje encubierto). Encontrar el camino
    de costo mínimo (medido en número de saltos o en inverso del volumen
    transferido) entre dos wallets permite al análisis forense identificar
    rutas de flujo financiero.

Equivalencia matemática:
    G = (V, E, w)  grafo DIRIGIDO y PONDERADO
    Problema: Dado s ∈ V, encontrar d(s, v) = min-weight path de s a todo v ∈ V
    Se usa Bellman-Ford en lugar de Dijkstra porque:
      1) Dijkstra está PROHIBIDO por las reglas del proyecto.
      2) Bellman-Ford detecta ciclos de peso negativo (relevante si w(e) = -log(ratio),
         técnica estándar en detección de arbitraje).
      3) Bellman-Ford es O(|V|·|E|) vs O((|V|+|E|) log|V|) de Dijkstra,
         lo cual es tolerable para subgrafos de tamaño moderado.

Alternativas algorítmicas descartadas:
    - Dijkstra: PROHIBIDO explícitamente.
    - Floyd-Warshall: O(|V|³) – inviable para |V| >> 10³.
    - BFS: solo válido para grafos no ponderados (w ≡ 1).
    ✓ Bellman-Ford: seleccionado por detectar pesos negativos y cumplir restricciones.
"""

from __future__ import annotations

from math import inf
from typing import Dict, List, Optional, Tuple

from src.graph_loader import AdjList


def bellman_ford(
    adj: AdjList,
    source: str,
) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
    """Implementa el algoritmo de Bellman-Ford desde cero.

    Calcula distancias mínimas desde `source` a todos los nodos alcanzables
    del grafo dirigido y ponderado representado por `adj`.

    Args:
        adj: Lista de adyacencia {src: [(dst, weight), ...]} del grafo G.
        source: Nodo origen s ∈ V desde el cual se calculan las distancias.

    Returns:
        Tupla (dist, prev) donde:
            dist (Dict[str, float]): dist[v] = costo mínimo de s a v.
                                     inf si v no es alcanzable desde s.
            prev (Dict[str, Optional[str]]): prev[v] = predecesor de v en el
                                             camino mínimo (None si v == source).

    Raises:
        ValueError: Si se detecta un ciclo de peso negativo alcanzable desde source.

    Complexity:
        Tiempo: O(|V| · |E|)
        Espacio: O(|V|)

    Example:
        >>> adj = {"A": [("B", 2.0), ("C", 5.0)], "B": [("C", 1.0)], "C": []}
        >>> dist, prev = bellman_ford(adj, "A")
        >>> dist["C"]
        3.0
    """
    # Recolectar todos los nodos del grafo (incluye nodos sin aristas salientes)
    nodes: set = set(adj.keys())
    for neighbors in adj.values():
        for dst, _ in neighbors:
            nodes.add(dst)

    # dist[v] = estimación actual del costo mínimo s → v
    dist: Dict[str, float] = {v: inf for v in nodes}
    dist[source] = 0.0

    # prev[v] = predecesor de v en el árbol de caminos mínimos
    prev: Dict[str, Optional[str]] = {v: None for v in nodes}

    # Invariante de ciclo (iteración k):
    #   Al inicio de la iteración k, dist[v] contiene el costo mínimo de todo
    #   camino s → v que usa EXACTAMENTE k-1 aristas o menos.
    #   Al finalizar la iteración k, dist[v] es el mínimo para k aristas o menos.
    # Tras |V|-1 iteraciones, dist[v] es el costo mínimo global (si no hay
    # ciclos negativos alcanzables desde s).
    num_vertices = len(nodes)
    for _iteration in range(num_vertices - 1):
        # TODO (Pablo): implementar el bucle de relajación de aristas
        # Para cada arista (u → v, w):
        #     si dist[u] + w < dist[v]:
        #         dist[v] = dist[u] + w
        #         prev[v] = u
        updated = False  # optimización: parar si no hubo cambios
        for src, neighbors in adj.items():
            for dst, w in neighbors:
                if dist[src] + w < dist[dst]:
                    dist[dst] = dist[src] + w
                    prev[dst] = src
                    updated = True
        if not updated:
            break  # Convergencia prematura: grafo sin más relajaciones posibles

    #Detección de ciclos negativos
    # Si después de |V|-1 iteraciones aún es posible relajar alguna arista,
    # existe un ciclo de peso negativo alcanzable desde source.
    for src, neighbors in adj.items():
        for dst, w in neighbors:
            if dist[src] + w < dist[dst]:
                raise ValueError(
                    f"Ciclo de peso negativo detectado. "
                    f"Nodo involucrado: {dst}"
                )

    return dist, prev


def reconstruct_path(
    prev: Dict[str, Optional[str]],
    source: str,
    target: str,
) -> List[str]:
    """Reconstruye el camino mínimo de source a target usando el árbol prev.

    Args:
        prev: Diccionario de predecesores obtenido de bellman_ford().
        source: Nodo origen.
        target: Nodo destino.

    Returns:
        Lista de nodos [source, ..., target] formando el camino mínimo.
        Lista vacía si target no es alcanzable desde source.

    Example:
        >>> path = reconstruct_path(prev, "A", "C")
        >>> path
        ['A', 'B', 'C']
    """
    path: List[str] = []
    current: Optional[str] = target

    # Traza hacia atrás desde target hasta source usando prev
    # Invariante: en cada iteración, `current` es el nodo anterior en el camino
    while current is not None:
        path.append(current)
        current = prev.get(current)
        # Guardia contra ciclos (no debería ocurrir si bellman_ford es correcto)
        if current == target:
            break

    path.reverse()

    # Verificar que el camino efectivamente empieza en source
    if path and path[0] == source:
        return path
    return []  # target no alcanzable desde source
