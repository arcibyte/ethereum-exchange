"""
arbol_expansion.py
==================
Tarea 4 — Árbol de expansión mínima (MST).

Problema: dado un grafo ponderado, encontrar el conjunto de aristas que
conecta TODOS los nodos con el MENOR costo total posible. Ese conjunto
siempre forma un árbol (no tiene ciclos) y tiene exactamente |V|-1 aristas.

Algoritmo elegido: Kruskal.

    1. Ordenar las aristas por peso de menor a mayor.
    2. Recorrerlas en orden y agregar cada arista SOLO si no forma un ciclo.
    3. Para detectar ciclos usamos Union-Find (conjuntos disjuntos).

Union-Find es una estructura de datos clásica que permite saber rápido si
dos nodos ya están conectados (están en el mismo conjunto) y unirlos.
"""

from typing import Dict, List, Set, Tuple


class UnionFind:
    """Conjuntos disjuntos con compresión de caminos y unión por rango."""

    def __init__(self, nodos: Set[str]) -> None:
        # Cada nodo apunta a su "padre". Al inicio, cada uno es su propio padre.
        self.padre: Dict[str, str] = {v: v for v in nodos}
        # El "rango" es una cota de la altura del árbol de cada conjunto.
        self.rango: Dict[str, int] = {v: 0 for v in nodos}

    def encontrar(self, x: str) -> str:
        """Devuelve el representante (raíz) del conjunto al que pertenece x."""
        # Compresión de caminos: hacemos que cada nodo apunte directo a la raíz,
        # así las siguientes búsquedas son más rápidas.
        if self.padre[x] != x:
            self.padre[x] = self.encontrar(self.padre[x])
        return self.padre[x]

    def unir(self, x: str, y: str) -> bool:
        """Une los conjuntos de x e y.

        Retorna:
            True si estaban en conjuntos distintos (y los unió),
            False si ya estaban conectados (agregar la arista crearía un ciclo).
        """
        rx = self.encontrar(x)
        ry = self.encontrar(y)
        if rx == ry:
            return False   # ya conectados: esta arista formaría un ciclo

        # Unión por rango: el árbol más "bajo" cuelga del más "alto".
        if self.rango[rx] < self.rango[ry]:
            rx, ry = ry, rx
        self.padre[ry] = rx
        if self.rango[rx] == self.rango[ry]:
            self.rango[rx] += 1
        return True


def aristas_no_dirigidas(aristas: List[Tuple[str, str, float]]) -> List[Tuple[str, str, float]]:
    """Convierte aristas dirigidas en no dirigidas.

    Si aparecen (a, b, w1) y (b, a, w2), las juntamos en una sola arista
    {a, b} con peso w1 + w2.
    """
    pesos: Dict[Tuple[str, str], float] = {}
    for a, b, w in aristas:
        clave = tuple(sorted((a, b)))
        pesos[clave] = pesos.get(clave, 0.0) + w
    return [(a, b, w) for (a, b), w in pesos.items()]


def kruskal(
    nodos: Set[str],
    aristas: List[Tuple[str, str, float]],
) -> Tuple[List[Tuple[str, str, float]], float]:
    """Construye el árbol de expansión mínima con el algoritmo de Kruskal.

    Parámetros:
        nodos: conjunto de todos los vértices.
        aristas: lista de aristas NO dirigidas (a, b, peso).

    Retorna:
        (mst, costo_total) donde mst es la lista de aristas del árbol.
    """
    # 1. Ordenar las aristas por peso, de menor a mayor.
    ordenadas = sorted(aristas, key=lambda e: e[2])

    # 2. Estructura Union-Find para detectar ciclos.
    uf = UnionFind(nodos)

    mst: List[Tuple[str, str, float]] = []
    costo = 0.0
    objetivo = len(nodos) - 1   # un árbol con |V| nodos tiene |V|-1 aristas

    # 3. Recorrer las aristas en orden.
    for a, b, w in ordenadas:
        if len(mst) == objetivo:
            break   # ya tenemos el árbol completo

        if uf.unir(a, b):
            mst.append((a, b, w))
            costo += w

    return mst, costo


def resumen_mst(mst: List[Tuple[str, str, float]]) -> Dict[str, float]:
    """Resumen simple del MST: número de aristas y costo total."""
    return {
        "aristas": len(mst),
        "costo_total": sum(w for _, _, w in mst),
    }


def kruskal_desde_aristas(
    aristas: List[Tuple[str, str, float]],
) -> Tuple[List[Tuple[str, str, float]], float]:
    """Kruskal a partir de la lista compartida de aristas.

    Convierte las aristas dirigidas en no dirigidas (sumando pesos si hay
    transferencias en ambos sentidos) y calcula el MST.
    """
    no_dirigidas = aristas_no_dirigidas(
        [(origen, destino, float(peso)) for origen, destino, peso in aristas]
    )
    nodos: Set[str] = set()
    for origen, destino, _ in no_dirigidas:
        nodos.add(origen)
        nodos.add(destino)
    return kruskal(nodos, no_dirigidas)
