"""
comunidades.py
==============
Tarea 3 — Detección de comunidades.

Queremos agrupar los nodos en "comunidades": grupos de nodos que interactúan
mucho entre sí y poco con el resto de la red.

Medida de calidad: la modularidad Q (Newman-Girvan).

    Q = (1/2m) * suma_{i,j} [ A_ij - k_i*k_j/(2m) ] * delta(c_i, c_j)

    - A_ij: peso de la arista entre i y j.
    - k_i: grado (suma de pesos) del nodo i.
    - m: suma total de pesos del grafo.
    - delta(c_i, c_j): 1 si i y j están en la misma comunidad, 0 si no.

    Valores de Q por encima de ~0.3 indican una buena estructura de comunidades.

Algoritmo: usamos una versión sencilla de Louvain (su fase principal).

    - Cada nodo empieza en su propia comunidad.
    - Repetimos: para cada nodo, probamos moverlo a la comunidad de cada
      vecino y nos quedamos con el movimiento que más aumente Q.
    - Paramos cuando ningún movimiento mejore Q.

    (La versión "de producción" de Louvain usa una fórmula incremental para
    calcular el cambio de Q sin recalcularla toda; aquí la recalculamos cada
    vez para que el código sea fácil de leer. El grafo de ejemplo es pequeño.)
"""

import random
from collections import defaultdict
from typing import Dict, List, Set, Tuple


def simetrizar(adj: Dict[str, List[Tuple[str, float]]]) -> Dict[str, List[Tuple[str, float]]]:
    """Convierte el grafo dirigido en no dirigido.

    Si existe la arista u -> v con peso w, creamos la arista no dirigida
    {u, v} con peso w. Si existen en ambos sentidos, sumamos los pesos.

    Para comunidades trabajamos con el grafo no dirigido subyacente.
    """
    pesos = defaultdict(float)
    for u, vecinos in adj.items():
        for v, w in vecinos:
            a, b = sorted((u, v))   # ordenamos para no duplicar (u, v) y (v, u)
            pesos[(a, b)] += w

    sim = defaultdict(list)
    for (a, b), w in pesos.items():
        sim[a].append((b, w))
        sim[b].append((a, w))
    return dict(sim)


def modularidad(
    adj_nd: Dict[str, List[Tuple[str, float]]],
    comunidades: Dict[str, int],
) -> float:
    """Calcula la modularidad Q de la partición actual.

    Parámetros:
        adj_nd: lista de adyacencia del grafo NO dirigido.
        comunidades: {nodo: id_comunidad}.

    Retorna:
        Q, un número entre -0.5 y 1.0.
    """
    grados = {v: sum(w for _, w in adj_nd.get(v, [])) for v in adj_nd}
    m = sum(grados.values()) / 2.0
    if m == 0:
        return 0.0

    q = 0.0
    for u, vecinos in adj_nd.items():
        for v, w in vecinos:
            if comunidades[u] == comunidades[v]:
                # Arista dentro de la misma comunidad.
                q += w - grados[u] * grados[v] / (2 * m)
    return q / (2 * m)


def louvain(
    adj_nd: Dict[str, List[Tuple[str, float]]],
    semilla: int = 42,
    max_pasadas: int = 20,
) -> Dict[str, int]:
    """Detecta comunidades maximizando la modularidad (Louvain, fase principal).

    Parámetros:
        adj_nd: lista de adyacencia del grafo NO dirigido.
        semilla: semilla para que el resultado sea reproducible.
        max_pasadas: máximo número de pasadas completas.

    Retorna:
        {nodo: id_comunidad}.
    """
    random.seed(semilla)
    nodos = list(adj_nd.keys())
    comunidades = {v: i for i, v in enumerate(nodos)}  # cada nodo en su comunidad

    for _ in range(max_pasadas):
        cambio = False
        random.shuffle(nodos)   # orden aleatorio para no sesgar el resultado

        for v in nodos:
            actual = comunidades[v]
            mejor = actual
            mejor_q = modularidad(adj_nd, comunidades)

            # Probamos mover v a la comunidad de cada vecino.
            for u, _ in adj_nd.get(v, []):
                c = comunidades[u]
                if c == actual:
                    continue

                comunidades[v] = c
                q = modularidad(adj_nd, comunidades)
                if q > mejor_q:
                    mejor_q = q
                    mejor = c
                comunidades[v] = actual   # deshacemos el cambio

            if mejor != actual:
                comunidades[v] = mejor
                cambio = True

        if not cambio:
            break   # ya nadie se mueve: convergió

    return comunidades


def resumen_comunidades(
    comunidades: Dict[str, int],
    etiquetas: Dict[str, Dict[str, str]] | None = None,
) -> Dict[int, List[str]]:
    """Agrupa los nodos por comunidad y devuelve sus nombres legibles.

    Parámetros:
        comunidades: {nodo: id_comunidad}.
        etiquetas: (opcional) {dirección: {"nombre": ...}}.

    Retorna:
        {id_comunidad: [nombres...]}.
    """
    grupos = defaultdict(list)
    for nodo, c in comunidades.items():
        nombre = nodo
        if etiquetas and nodo in etiquetas:
            nombre = etiquetas[nodo].get("nombre", nodo)
        grupos[c].append(nombre)
    return dict(grupos)
