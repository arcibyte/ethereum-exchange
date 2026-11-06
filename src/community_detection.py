"""
community_detection.py – Tarea 3: Detección de Comunidades / Clustering.

Responsable: Emerson Ballesteros

Problema real:
    En la red Ethereum DeFi, las comunidades de wallets representan grupos
    de actores que interactúan preferentemente entre sí: fondos de liquidez
    (liquidity pools), grupos de arbitrajistas coordinados, clusters de
    stablecoins (USDC, DAI, USDT). Detectar estas comunidades ayuda a
    comprender la arquitectura del ecosistema y a identificar comportamientos
    anómalos o carteles de manipulación.

Equivalencia matemática:
    G = (V, E)  grafo no dirigido (simetrizamos el grafo dirigido original)
    
    Modularidad (Newman-Girvan):
        Q = (1/2m) · Σ_{i,j} [A_{ij} - k_i·k_j/(2m)] · δ(c_i, c_j)
        donde:
            m = |E|, número de aristas
            A_{ij} = 1 si existe arista (i,j), 0 en caso contrario
            k_i = grado del nodo i
            c_i = comunidad asignada al nodo i
            δ = función delta de Kronecker

    Objetivo: maximizar Q ∈ [-0.5, 1.0]
    Q > 0.3 → estructura de comunidades significativa.

Alternativas algorítmicas descartadas:
    - Dijkstra: PROHIBIDO explícitamente.
    - Girvan-Newman (edge betweenness): O(|V|·|E|²) – computacionalmente
      inviable para |E| en el orden de millones.
    - Spectral Clustering (Laplaciano): requiere álgebra lineal densa, O(|V|³).
    ✓ Louvain (aproximación greedy de modularidad): seleccionado por ser
      O(|V| log |V|), escalable y producir resultados interpretables.
      Se implementa desde cero sin usar python-louvain ni NetworkX.communities.
"""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from src.graph_loader import AdjList


def symmetrize_graph(adj: AdjList) -> Dict[str, List[Tuple[str, float]]]:
    """Convierte el grafo dirigido en no dirigido sumando pesos de aristas paralelas.

    Para comunidades, trabajamos con el grafo no dirigido subyacente.
    Si existe (u→v, w1) y (v→u, w2), la arista no dirigida tendrá peso w1+w2.

    Args:
        adj: Lista de adyacencia del grafo DIRIGIDO original.

    Returns:
        Lista de adyacencia del grafo NO DIRIGIDO simétrico.
    """
    sym: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

    # Invariante: tras procesar cada arista (src→dst, w),
    # sym[src][dst] y sym[dst][src] reflejan el peso acumulado bidireccional.
    for src, neighbors in adj.items():
        for dst, w in neighbors:
            sym[src][dst] += w
            sym[dst][src] += w

    return {node: list(nbrs.items()) for node, nbrs in sym.items()}


def louvain_communities(
    adj_undirected: Dict[str, List[Tuple[str, float]]],
    resolution: float = 1.0,
    max_passes: int = 10,
    seed: int = 42,
) -> Dict[str, int]:
    """Implementa el algoritmo de Louvain para detección de comunidades.

    El algoritmo opera en dos fases que se repiten:
      Fase 1 (Local): Mover cada nodo a la comunidad vecina que maximice
                      el incremento de modularidad ΔQ.
      Fase 2 (Global): Colapsar cada comunidad en un super-nodo y repetir.

    Args:
        adj_undirected: Lista de adyacencia del grafo NO DIRIGIDO (simétrico).
        resolution: Parámetro γ de resolución. Mayor γ → más comunidades pequeñas.
        max_passes: Número máximo de pases globales.
        seed: Semilla para reproducibilidad del orden de visita.

    Returns:
        Dict {nodo: id_comunidad} con la asignación final de comunidades.

    Note:
        Esta implementación cubre la Fase 1 completa y un esquema simplificado
        de la Fase 2. El equipo debe completar el collapse completo.

    Complexity:
        Tiempo: O(|V| log |V|) por pase (empíricamente).
        Espacio: O(|V| + |E|)
    """
    random.seed(seed)
    nodes: List[str] = list(adj_undirected.keys())

    # Inicialización: cada nodo en su propia comunidad
    community: Dict[str, int] = {v: i for i, v in enumerate(nodes)}

    # Precalcular suma de pesos por nodo (k_i)
    k: Dict[str, float] = {
        v: sum(w for _, w in adj_undirected.get(v, []))
        for v in nodes
    }
    m: float = sum(k.values()) / 2.0  # peso total de aristas (m = Σk_i / 2)

    if m == 0:
        return community

    improved = True
    pass_num = 0

    # --- Fase 1: optimización local ---
    # Invariante de pase: al finalizar cada pase, ningún movimiento individual
    # de nodo incrementa Q. La modularidad es localmente óptima.
    while improved and pass_num < max_passes:
        improved = False
        pass_num += 1
        random.shuffle(nodes)  # orden aleatorio para evitar sesgos

        for v in nodes:
            current_comm = community[v]

            # Calcular el peso de conexión de v a cada comunidad vecina
            # comm_weights[c] = Σ w(v,u) para u en comunidad c
            comm_weights: Dict[int, float] = defaultdict(float)
            for u, w in adj_undirected.get(v, []):
                comm_weights[community[u]] += w

            # Calcular ΔQ para mover v a cada comunidad vecina
            # ΔQ(v → c) = [k_{v,c}/m - γ · Σ_c · k_v / (2m²)]
            # donde k_{v,c} = peso de aristas de v a comunidad c
            #       Σ_c = suma total de grados en comunidad c
            best_comm = current_comm
            best_dq = 0.0  # solo mover si ΔQ > 0

            # TODO (Emerson): completar el cálculo de ΔQ y la selección de la mejor comunidad
            # Fórmula ΔQ al remover v de current_comm y moverlo a c:
            # ΔQ = comm_weights[c]/m - resolution * k[v] * sum_k[c] / (2*m*m)
            #      (menos la contribución al remover de current_comm)

            # Suma de grados por comunidad (Σ_c)
            sum_k: Dict[int, float] = defaultdict(float)
            for u in nodes:
                sum_k[community[u]] += k.get(u, 0.0)

            for c, w_vc in comm_weights.items():
                if c == current_comm:
                    continue
                # ΔQ simplificado (Blondel et al. 2008)
                dq = w_vc / m - resolution * k.get(v, 0.0) * sum_k[c] / (2 * m * m)
                if dq > best_dq:
                    best_dq = dq
                    best_comm = c

            if best_comm != current_comm:
                community[v] = best_comm
                improved = True

    return community


def compute_modularity(
    adj_undirected: Dict[str, List[Tuple[str, float]]],
    community: Dict[str, int],
) -> float:
    """Calcula la modularidad Q de una partición de comunidades dada.

    Args:
        adj_undirected: Lista de adyacencia del grafo no dirigido.
        community: Asignación de comunidades {nodo: comunidad_id}.

    Returns:
        Modularidad Q ∈ [-0.5, 1.0]. Valores > 0.3 indican buena estructura.

    Example:
        >>> q = compute_modularity(adj_undirected, community)
        >>> print(f"Q = {q:.4f}")
    """
    # Precalcular grados y peso total
    k: Dict[str, float] = {
        v: sum(w for _, w in adj_undirected.get(v, []))
        for v in adj_undirected
    }
    m: float = sum(k.values()) / 2.0
    if m == 0:
        return 0.0

    q = 0.0
    # TODO (Emerson): implementar la suma de modularidad
    # Q = (1/2m) · Σ_{i,j} [A_ij - k_i·k_j/(2m)] · δ(c_i, c_j)
    for src, neighbors in adj_undirected.items():
        for dst, w_ij in neighbors:
            if community.get(src) == community.get(dst):
                q += w_ij - (k[src] * k.get(dst, 0.0)) / (2 * m)

    return q / (2 * m)


def community_summary(
    community: Dict[str, int],
    node_meta: Dict,
) -> Dict[int, Dict]:
    """Genera un resumen estadístico de cada comunidad detectada.

    Args:
        community: Asignación {nodo: comunidad_id}.
        node_meta: Metadatos de nodos (tipo, nombre).

    Returns:
        Dict {comunidad_id: {size, labeled_nodes, known_names}}
    """
    summary: Dict[int, Dict] = defaultdict(lambda: {"size": 0, "labeled": [], "names": []})

    for node, comm_id in community.items():
        summary[comm_id]["size"] += 1
        if node in node_meta:
            summary[comm_id]["labeled"].append(node)
            summary[comm_id]["names"].append(node_meta[node].get("name", "?"))

    return dict(sorted(summary.items(), key=lambda x: x[1]["size"], reverse=True))
