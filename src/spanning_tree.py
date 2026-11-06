"""
spanning_tree.py – Tarea 4 (Grupal): Árbol de Expansión Mínima en la Red DeFi.

Responsables: Jhon Arciniegas, Pablo Álvarez y Emerson Ballesteros (Tarea Grupal)

Problema real:
    En la red de transferencias DeFi, encontrar el Árbol de Expansión Mínima
    (MST) del grafo subyacente permite identificar la infraestructura MÍNIMA
    de conectividad que sustenta el ecosistema de intercambio de tokens.
    El MST responde: ¿cuál es el conjunto de rutas de menor costo que mantiene
    la red completamente conectada?

    Aplicaciones:
        - Diseño de protocolos de routing óptimo entre exchanges.
        - Identificación de cuellos de botella en la liquidez (cut-edges del MST).
        - Clustering jerárquico por similitud de flujos de transferencia.

Equivalencia matemática:
    G = (V, E, w)   grafo NO DIRIGIDO y PONDERADO (simetrizamos el dirigido)
    
    MST T* = argmin_{T ∈ span(G)} Σ_{e ∈ T} w(e)
    
    Propiedades del MST:
        - |V(T*)| = |V(G)|
        - |E(T*)| = |V(G)| - 1
        - T* es un árbol (conexo y acíclico)
        - Corte Fundamental: para toda arista (u,v) ∉ T*, es la arista de mayor
          peso en el camino único u→v dentro de T*.

Alternativas algorítmicas descartadas:
    - Dijkstra: PROHIBIDO explícitamente.
    - Prim con cola de prioridad (heap): técnicamente no prohíbe Prim, pero
      Kruskal es más directo de implementar con Union-Find puro.
    - Borůvka: más complejo de implementar; ventaja solo en grafos densos.
    ✓ Kruskal + Union-Find (DSU): seleccionado por claridad algorítmica,
      O(|E| log |E|) con ordenamiento, y verificación formal con invariante
      de ciclo clara (cada arista agregada NO cierra un ciclo).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

from src.graph_loader import AdjList


# Estructura Union-Find (Disjoint Set Union – DSU)

class UnionFind:
    """Estructura Union-Find con compresión de caminos y unión por rango.

    Permite verificar eficientemente si dos nodos están en el mismo componente
    conexo y unir componentes, garantizando que agregar una arista no crea ciclos.

    Attributes:
        parent (Dict[str, str]): Padre de cada nodo en el árbol DSU.
        rank (Dict[str, int]): Rango (profundidad aproximada) del árbol.
    """

    def __init__(self, nodes: Set[str]) -> None:
        """Inicializa DSU con cada nodo en su propio componente.

        Args:
            nodes: Conjunto de todos los vértices V.
        """
        self.parent: Dict[str, str] = {v: v for v in nodes}
        self.rank: Dict[str, int] = {v: 0 for v in nodes}
        self.num_components: int = len(nodes)

    def find(self, x: str) -> str:
        """Encuentra la raíz del componente de x con compresión de caminos.

        Args:
            x: Nodo a consultar.

        Returns:
            Raíz canónica del componente de x.

        Note:
            Compresión de caminos: hace que todos los nodos en el camino
            apunten directamente a la raíz (amortización).
        """
        # TODO (Grupal): implementar compresión de caminos iterativa o recursiva
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # compresión
        return self.parent[x]

    def union(self, x: str, y: str) -> bool:
        """Une los componentes de x e y.

        Args:
            x: Primer nodo.
            y: Segundo nodo.

        Returns:
            True si se realizó la unión (x e y estaban en componentes distintos).
            False si ya estaban en el mismo componente (agregar la arista crearía ciclo).
        """
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False  # mismo componente → ciclo

        # Unión por rango: árbol más profundo absorbe al menos profundo
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1

        self.num_components -= 1
        return True

    def connected(self, x: str, y: str) -> bool:
        """Verifica si x e y están en el mismo componente conexo.

        Args:
            x: Primer nodo.
            y: Segundo nodo.

        Returns:
            True si find(x) == find(y).
        """
        return self.find(x) == self.find(y)


# Algoritmo de Kruskal

def kruskal_mst(
    nodes: Set[str],
    edges: List[Tuple[str, str, float]],
    maximize: bool = False,
) -> Tuple[List[Tuple[str, str, float]], float]:
    """Implementa el algoritmo de Kruskal para MST/MaxST desde cero.

    Construye el Árbol de Expansión Mínima (o Máxima si maximize=True)
    usando la estructura Union-Find para detección eficiente de ciclos.

    Args:
        nodes: Conjunto de vértices V del grafo.
        edges: Lista de aristas [(src, dst, weight), ...] del grafo NO DIRIGIDO.
               Cada arista aparece UNA SOLA VEZ (no duplicar src↔dst).
        maximize: Si True, construye el Árbol de Expansión MÁXIMA.
                  Útil para identificar flujos de mayor volumen.

    Returns:
        Tupla (mst_edges, total_weight) donde:
            mst_edges: Aristas del MST como [(src, dst, weight), ...].
            total_weight: Suma total de pesos del MST.

    Raises:
        ValueError: Si el grafo es desconectado (el MST no puede abarcar V).

    Complexity:
        Tiempo: O(|E| log |E|)   (dominado por el ordenamiento)
        Espacio: O(|V| + |E|)

    Example:
        >>> mst, cost = kruskal_mst(nodes, edges)
        >>> print(f"MST con {len(mst)} aristas, costo total = {cost:.2f}")

    Algorithm:
        1. Ordenar todas las aristas por peso (ascendente para MST).
        2. Inicializar DSU con cada nodo en su componente.
        3. Para cada arista (u, v, w) en orden:
           - Si u y v están en componentes distintos (no cierra ciclo):
             * Agregar (u, v, w) al MST.
             * Unir componentes de u y v en DSU.
           - Parar cuando |MST| = |V| - 1.
    """
    if not nodes:
        return [], 0.0

    # Paso 1: Ordenar aristas
    # Para MST: orden ascendente; para MaxST: orden descendente
    sorted_edges = sorted(edges, key=lambda e: e[2], reverse=maximize)

    # Paso 2: Inicializar DSU
    dsu = UnionFind(nodes)

    mst_edges: List[Tuple[str, str, float]] = []
    total_weight: float = 0.0
    target_edges = len(nodes) - 1  # un árbol de |V| nodos tiene |V|-1 aristas

    # Paso 3: Procesar aristas en orden
    # Invariante de ciclo (arista k):
    #   Al inicio, mst_edges contiene un bosque de expansión con k aristas
    #   y sin ciclos. Al agregar la arista k+1 (si no cierra ciclo), el bosque
    #   sigue siendo acíclico y conecta un componente más.
    # Terminación: cuando |mst_edges| = |V| - 1 → árbol de expansión completo.
    for src, dst, w in sorted_edges:
        if len(mst_edges) == target_edges:
            break  # MST completo

        # Agregar arista solo si no crea ciclo
        if dsu.union(src, dst):
            mst_edges.append((src, dst, w))
            total_weight += w

    # Verificar si el grafo es conexo
    if len(mst_edges) < target_edges and len(nodes) > 1:
        # Grafo desconectado: retornar el bosque de expansión mínima (MSF)
        # En lugar de lanzar excepción, retornamos lo que se pudo construir
        pass  # TODO (Grupal): decidir si lanzar error o retornar MSF parcial

    return mst_edges, total_weight


def mst_analytics(
    mst_edges: List[Tuple[str, str, float]],
    node_meta: Dict,
) -> Dict:
    """Analiza el MST resultante para extraer insights de la red DeFi.

    Args:
        mst_edges: Aristas del MST [(src, dst, weight), ...].
        node_meta: Metadatos de nodos (tipo, nombre de protocolo).

    Returns:
        Dict con estadísticas del MST:
            - num_edges: número de aristas en el MST.
            - total_weight: peso total del MST.
            - avg_weight: peso promedio por arista.
            - bridge_edges: aristas del MST que son puentes críticos de la red.
            - top_weight_edges: las 10 aristas de mayor peso (flujos clave).
    """
    if not mst_edges:
        return {}

    weights = [w for _, _, w in mst_edges]
    total = sum(weights)
    avg = total / len(weights)

    # Top 10 aristas de mayor peso en el MST
    top_edges = sorted(mst_edges, key=lambda e: e[2], reverse=True)[:10]
    top_labeled = []
    for src, dst, w in top_edges:
        src_name = node_meta.get(src, {}).get("name", src[:10] + "...")
        dst_name = node_meta.get(dst, {}).get("name", dst[:10] + "...")
        top_labeled.append({"from": src_name, "to": dst_name, "weight": w})

    return {
        "num_edges": len(mst_edges),
        "total_weight": total,
        "avg_weight": avg,
        "max_weight": max(weights),
        "min_weight": min(weights),
        "top_weight_edges": top_labeled,
    }


def symmetrize_edges(
    directed_edges: List[Tuple[str, str, float]]
) -> List[Tuple[str, str, float]]:
    """Convierte una lista de aristas dirigidas en aristas no dirigidas únicas.

    Para Kruskal necesitamos el grafo no dirigido. Se suma el peso de aristas
    paralelas (u→v y v→u) en una sola arista (u, v, w1+w2).

    Args:
        directed_edges: Lista de aristas dirigidas [(src, dst, w), ...].

    Returns:
        Lista de aristas no dirigidas sin duplicados [(u, v, w), ...].
    """
    edge_map: Dict[Tuple[str, str], float] = {}

    for src, dst, w in directed_edges:
        # Normalizar el orden del par para evitar (a,b) y (b,a) como distintos
        key = (min(src, dst), max(src, dst))
        edge_map[key] = edge_map.get(key, 0.0) + w

    return [(u, v, w) for (u, v), w in edge_map.items()]
