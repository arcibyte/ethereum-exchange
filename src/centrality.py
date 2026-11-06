"""
centrality.py – Tarea 2: Métricas de Centralidad e Influencia en la Red.

Responsable: Jhon Arciniegas

Problema real:
    En el ecosistema DeFi (Finanzas Descentralizadas), ciertos contratos
    inteligentes o wallets actúan como 'hubs' que concentran el flujo de
    liquidez (Uniswap, Aave, Curve). Identificar estos nodos de alta
    centralidad permite detectar puntos de falla única, actores sistémicamente
    importantes y posibles vectores de manipulación de mercado.

Equivalencia matemática:
    G = (V, E)  grafo dirigido
    
    Centralidad de Grado (Degree Centrality):
        C_D(v) = deg(v) / (|V| - 1)

    Centralidad de Intermediación (Betweenness Centrality):
        C_B(v) = Σ_{s≠v≠t} [σ(s,t|v) / σ(s,t)]
        donde σ(s,t) = número de caminos mínimos entre s y t,
              σ(s,t|v) = número de esos caminos que pasan por v.

    PageRank (Centralidad de Eigenvector simplificada):
        PR(v) = (1-d)/|V| + d · Σ_{u∈in(v)} [PR(u) / out_deg(u)]
        donde d = factor de amortiguación (típicamente 0.85).

Alternativas algorítmicas descartadas:
    - Dijkstra: PROHIBIDO explícitamente.
    - Centralidad de Cercanía vía Dijkstra: descartada por la misma razón.
    - HITS (Hyperlink-Induced Topic Search): análisis de hubs/autoridades,
      mayor complejidad para el contexto financiero sin ventaja interpretativa.
    ✓ PageRank + Degree Centrality + Betweenness aproximada (Brandes):
      equilibrio entre costo computacional e interpretabilidad financiera.
"""

from __future__ import annotations

import math
from collections import deque
from typing import Dict, List, Set, Tuple

from src.graph_loader import AdjList


def degree_centrality(
    adj: AdjList,
    nodes: Set[str],
    mode: str = "out",
) -> Dict[str, float]:
    """Calcula la centralidad de grado para todos los nodos del grafo.

    Args:
        adj: Lista de adyacencia del grafo dirigido G.
        nodes: Conjunto completo de vértices V.
        mode: Tipo de grado a usar:
              'out' → grado de salida (emisores de transferencias),
              'in'  → grado de entrada (receptores de transferencias),
              'total' → suma de ambos.

    Returns:
        Dict {nodo: centralidad_normalizada ∈ [0, 1]}

    Complexity:
        Tiempo: O(|V| + |E|)
        Espacio: O(|V|)
    """
    n = len(nodes)
    if n <= 1:
        return {v: 0.0 for v in nodes}

    # Calcular grados brutos
    out_deg: Dict[str, int] = {v: 0 for v in nodes}
    in_deg: Dict[str, int] = {v: 0 for v in nodes}

    # Invariante de ciclo: al finalizar el bucle, out_deg y in_deg
    # contienen los grados correctos para todos los nodos procesados.
    for src, neighbors in adj.items():
        out_deg[src] = len(neighbors)
        for dst, _ in neighbors:
            in_deg[dst] = in_deg.get(dst, 0) + 1

    centrality: Dict[str, float] = {}
    normalizer = n - 1  # máximo posible de grado en grafo simple

    for v in nodes:
        if mode == "out":
            raw = out_deg.get(v, 0)
        elif mode == "in":
            raw = in_deg.get(v, 0)
        else:  # total
            raw = out_deg.get(v, 0) + in_deg.get(v, 0)
        centrality[v] = raw / normalizer

    return centrality


def pagerank(
    adj: AdjList,
    nodes: Set[str],
    damping: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-6,
) -> Dict[str, float]:
    """Implementa el algoritmo PageRank desde cero con iteración de potencias.

    Modela la probabilidad de que un 'surfer' aleatorio (que sigue transacciones
    en la red Ethereum) esté en un nodo determinado en el largo plazo.

    Args:
        adj: Lista de adyacencia del grafo dirigido G.
        nodes: Conjunto completo de vértices V.
        damping: Factor de amortiguación d ∈ (0, 1). Por defecto 0.85.
        max_iter: Número máximo de iteraciones de convergencia.
        tol: Tolerancia de convergencia (norma L1 del vector de diferencias).

    Returns:
        Dict {nodo: pagerank_score} con scores normalizados (suman ≈ 1.0).

    Complexity:
        Tiempo: O(max_iter · |E|)
        Espacio: O(|V|)

    Example:
        >>> pr = pagerank(adj, nodes, damping=0.85)
        >>> top_nodes = sorted(pr, key=pr.get, reverse=True)[:10]
    """
    n = len(nodes)
    if n == 0:
        return {}

    node_list: List[str] = list(nodes)
    # Inicialización uniforme: PR(v) = 1/|V| para todo v ∈ V
    pr: Dict[str, float] = {v: 1.0 / n for v in node_list}

    # Pre-calcular grado de salida para cada nodo
    out_deg: Dict[str, int] = {v: len(adj.get(v, [])) for v in node_list}

    # --- Iteración de potencias ---
    # Invariante de ciclo (iteración k):
    #   pr contiene el vector PageRank de la iteración k.
    #   Al converger, pr[v] ≈ probabilidad estacionaria de estar en v.
    for _k in range(max_iter):
        new_pr: Dict[str, float] = {}
        base = (1.0 - damping) / n  # término de teletransportación

        for v in node_list:
            # TODO (Jhon): completar la suma de contribuciones de predecesores
            # Σ_{u: u→v ∈ E} PR(u) / out_deg(u)
            incoming_sum = 0.0
            # NOTA: en un grafo grande es más eficiente mantener in_adj inverso.
            # Para el esqueleto usamos el enfoque directo (correcto pero lento):
            for src, neighbors in adj.items():
                for dst, _ in neighbors:
                    if dst == v and out_deg.get(src, 0) > 0:
                        incoming_sum += pr[src] / out_deg[src]

            new_pr[v] = base + damping * incoming_sum

        # Verificar convergencia (norma L1)
        delta = sum(abs(new_pr[v] - pr[v]) for v in node_list)
        pr = new_pr
        if delta < tol:
            break

    return pr


def betweenness_centrality_approx(
    adj: AdjList,
    nodes: Set[str],
    sample_size: int = 200,
    seed: int = 42,
) -> Dict[str, float]:
    """Calcula la centralidad de intermediación por muestreo de nodos fuente.

    Usa el algoritmo de Brandes (BFS-based) sobre un subconjunto de nodos
    fuente para aproximar la betweenness real sin usar Dijkstra.

    Args:
        adj: Lista de adyacencia del grafo G (no ponderado a efectos de BFS).
        nodes: Conjunto completo de vértices V.
        sample_size: Número de nodos fuente a muestrear aleatoriamente.
        seed: Semilla aleatoria para reproducibilidad.

    Returns:
        Dict {nodo: betweenness_aproximada_normalizada}

    Note:
        Este algoritmo usa BFS (válido para grafos no ponderados, equivalente
        a contar saltos). Para grafos ponderados usaría Bellman-Ford como base.
        Dijkstra está PROHIBIDO.

    Complexity:
        Tiempo: O(sample_size · (|V| + |E|))
        Espacio: O(|V|)
    """
    import random
    random.seed(seed)

    node_list: List[str] = list(nodes)
    n = len(node_list)
    betweenness: Dict[str, float] = {v: 0.0 for v in node_list}

    # Muestra de nodos fuente
    sources = random.sample(node_list, min(sample_size, n))

    for s in sources:
        # Algoritmo de Brandes para un nodo fuente s
        # stack: nodos en orden inverso de descubrimiento (BFS)
        stack: List[str] = []
        # pred[v]: predecesores de v en el árbol BFS
        pred: Dict[str, List[str]] = {v: [] for v in node_list}
        # sigma[v]: número de caminos mínimos de s a v
        sigma: Dict[str, float] = {v: 0.0 for v in node_list}
        sigma[s] = 1.0
        # dist[v]: distancia BFS de s a v (-1 = no visitado)
        dist: Dict[str, int] = {v: -1 for v in node_list}
        dist[s] = 0

        # --- BFS desde s ---
        queue: deque = deque([s])
        # Invariante: queue contiene nodos a explorar en la capa BFS actual.
        while queue:
            u = queue.popleft()
            stack.append(u)
            for v, _ in adj.get(u, []):
                # Primer descubrimiento de v
                if dist[v] < 0:
                    queue.append(v)
                    dist[v] = dist[u] + 1
                # Camino mínimo encontrado
                if dist[v] == dist[u] + 1:
                    sigma[v] += sigma[u]
                    pred[v].append(u)

        # --- Acumulación de dependencias (fase inversa) ---
        delta: Dict[str, float] = {v: 0.0 for v in node_list}
        # TODO (Jhon): completar la acumulación de Brandes
        # Recorrer stack en orden inverso:
        #   δ(s, u | w) += σ(s,u)/σ(s,w) · (1 + δ(s,w))
        while stack:
            w = stack.pop()
            for u in pred[w]:
                if sigma[w] > 0:
                    delta[u] += (sigma[u] / sigma[w]) * (1.0 + delta[w])
            if w != s:
                betweenness[w] += delta[w]

    # Normalizar: dividir por número de pares (n-1)(n-2) y escalar por muestra
    normalizer = (n - 1) * (n - 2) if n > 2 else 1
    scale = n / max(len(sources), 1)  # corrección por muestreo
    for v in node_list:
        betweenness[v] = betweenness[v] * scale / normalizer

    return betweenness


def top_k_nodes(
    scores: Dict[str, float],
    k: int = 10,
    label_map: Dict | None = None,
) -> List[Tuple[str, float, str]]:
    """Retorna los k nodos con mayor puntuación de centralidad.

    Args:
        scores: Diccionario {nodo: score}.
        k: Número de nodos top a retornar.
        label_map: Mapa opcional {dirección: nombre} para enriquecer resultados.

    Returns:
        Lista de tuplas (nodo, score, nombre_etiqueta) ordenada de mayor a menor.
    """
    sorted_nodes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    result = []
    for addr, score in sorted_nodes[:k]:
        name = label_map.get(addr, {}).get("name", "unknown") if label_map else "unknown"
        result.append((addr, round(score, 8), name))
    return result
