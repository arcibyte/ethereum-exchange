"""
bellman_ford.py
===============
Tarea 1 — Caminos de costo mínimo.

Problema: encontrar la ruta más "barata" entre dos direcciones del grafo,
donde el costo de una ruta es la suma de los pesos de sus aristas.

Regla del proyecto: NO se puede usar Dijkstra. Por eso usamos Bellman-Ford,
que además es capaz de detectar ciclos de peso negativo.

Idea del algoritmo:
    1. Empezamos con distancia 0 en el origen e "infinito" en el resto.
    2. Repetimos |V|-1 veces: por cada arista (u -> v, w), si
       dist[u] + w < dist[v], entonces actualizamos dist[v] = dist[u] + w.
       (a esto se le llama "relajar" una arista).
    3. Al terminar, dist[v] es la distancia mínima desde el origen a v.

Complejidad: O(|V| * |E|).
"""

from typing import Dict, List, Optional, Tuple

INF = float("inf")


def bellman_ford(
    adj: Dict[str, List[Tuple[str, float]]],
    origen: str,
) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
    """Calcula las distancias mínimas desde `origen` a todos los nodos.

    Parámetros:
        adj: lista de adyacencia {nodo: [(vecino, peso), ...]}.
        origen: nodo de partida.

    Retorna:
        (distancias, predecesores):
            - distancias[v] = costo mínimo desde `origen` hasta v
              (INF si v es inalcanzable).
            - predecesores[v] = nodo anterior a v en el camino mínimo
              (None para el origen).
    """
    # 1. Reunimos todos los nodos del grafo (incluye los que no tienen
    #    aristas salientes pero sí entrantes).
    nodos = set(adj.keys())
    for vecinos in adj.values():
        for dst, _ in vecinos:
            nodos.add(dst)

    # 2. Inicializamos distancias y predecesores.
    dist = {v: INF for v in nodos}
    dist[origen] = 0.0
    prev = {v: None for v in nodos}

    # 3. Relajamos todas las aristas |V|-1 veces.
    for _ in range(len(nodos) - 1):
        cambio = False
        for u in adj:
            for v, w in adj[u]:
                if dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
                    prev[v] = u
                    cambio = True
        if not cambio:
            # Ya no mejora nada: terminamos antes de tiempo.
            break

    # 4. (Opcional) Una pasada extra para detectar ciclos de peso negativo.
    #    Con pesos positivos nunca ocurre, pero es una ventaja de Bellman-Ford.
    for u in adj:
        for v, w in adj[u]:
            if dist[u] + w < dist[v]:
                raise ValueError("Se detectó un ciclo de peso negativo.")

    return dist, prev


def reconstruir_camino(
    prev: Dict[str, Optional[str]],
    origen: str,
    destino: str,
) -> List[str]:
    """Reconstruye el camino mínimo desde `origen` hasta `destino`.

    Usa el diccionario de predecesores que devuelve `bellman_ford`.

    Retorna:
        Lista de nodos [origen, ..., destino], o [] si no hay camino.
    """
    camino: List[str] = []
    actual: Optional[str] = destino

    # Retrocedemos desde el destino hasta el origen siguiendo `prev`.
    while actual is not None:
        camino.append(actual)
        actual = prev.get(actual)

    camino.reverse()
    return camino if camino and camino[0] == origen else []
