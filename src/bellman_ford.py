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

Complejidad: O(|V| * |E|) en el peor caso. Con la parada temprana (si una
pasada completa no cambia nada, ya terminó) el número real de pasadas es, como
máximo, el número de aristas del camino mínimo más largo + 1, que en redes
de transferencias suele ser pequeño. `bellman_ford_con_pasadas` lo reporta.

Costo de una arista. Sumar montos no mide un "costo" real, así que también
ofrecemos `adyacencia_probabilidad`: si u envió en total S y le mandó w a v,
la fracción p = w / S es la probabilidad de que una unidad que sale de u vaya
a v. Con costo(u, v) = -log(p):

    -log(p1) - log(p2) - ... = -log(p1 * p2 * ...)

el camino de costo mínimo es el camino MÁS PROBABLE que sigue el dinero.
Todos los costos son >= 0, así que no hay ciclos negativos.
"""

import math
from typing import Dict, List, Optional, Tuple

INF = float("inf")


def construir_adyacencia(aristas: List[Tuple[str, str, float]]) -> Dict[str, List[Tuple[str, float]]]:
    """Convierte la lista compartida de aristas en una lista de adyacencia.

    La lista de aristas viene de la carga única del dataset. Cada módulo
    construye su propia estructura, así no depende de la de otro.
    """
    from collections import defaultdict

    adj: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
    for origen, destino, peso in aristas:
        adj[origen].append((destino, float(peso)))
    return dict(adj)


def bellman_ford_con_pasadas(
    adj: Dict[str, List[Tuple[str, float]]],
    origen: str,
) -> Tuple[Dict[str, float], Dict[str, Optional[str]], int]:
    """Igual que `bellman_ford`, pero también retorna cuántas pasadas hizo.

    Una pasada = recorrer todas las aristas una vez relajándolas. El peor caso
    son |V|-1 pasadas; la parada temprana suele terminar mucho antes.

    Retorna (distancias, predecesores, pasadas).
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
    pasadas = 0
    for _ in range(len(nodos) - 1):
        pasadas += 1
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

    return dist, prev, pasadas


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

    Lanza ValueError si hay un ciclo de peso negativo alcanzable.
    """
    dist, prev, _ = bellman_ford_con_pasadas(adj, origen)
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


def bellman_ford_desde_aristas(
    aristas: List[Tuple[str, str, float]],
    origen: str,
) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
    """Igual que `bellman_ford`, pero recibe la lista compartida de aristas."""
    return bellman_ford(construir_adyacencia(aristas), origen)


def adyacencia_probabilidad(
    aristas: List[Tuple[str, str, float]],
) -> Dict[str, List[Tuple[str, float]]]:
    """Lista de adyacencia con costo = -log(fracción del flujo saliente).

    1. Se suman los montos de cada par (u, v) (puede haber varias
       transferencias entre el mismo par).
    2. S(u) = total que envió u.
    3. costo(u, v) = -log(monto(u, v) / S(u)), que es >= 0.

    Con este costo, el camino mínimo de Bellman-Ford es el camino más
    probable del dinero, y exp(-distancia) es su probabilidad.
    Se ignoran autolazos y montos <= 0.
    """
    montos: Dict[Tuple[str, str], float] = {}
    for origen, destino, peso in aristas:
        peso = float(peso)
        if origen == destino or peso <= 0:
            continue
        montos[(origen, destino)] = montos.get((origen, destino), 0.0) + peso

    total_salida: Dict[str, float] = {}
    for (origen, _), monto in montos.items():
        total_salida[origen] = total_salida.get(origen, 0.0) + monto

    adj: Dict[str, List[Tuple[str, float]]] = {}
    for (origen, destino), monto in montos.items():
        costo = -math.log(monto / total_salida[origen])
        adj.setdefault(origen, []).append((destino, max(0.0, costo)))
    return adj

