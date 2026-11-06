"""
test_algorithms.py – Tests unitarios para validar las implementaciones propias

ejecutar con: python -m pytest tests/ -v
"""
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

import pytest
from src.bellman_ford import bellman_ford, reconstruct_path
from src.spanning_tree import UnionFind, kruskal_mst, symmetrize_edges
from src.centrality import degree_centrality, pagerank


# Tests Bellman-Ford

class TestBellmanFord:
    def test_simple_graph(self):
        """Grafo simple con camino único."""
        adj = {"A": [("B", 2.0), ("C", 5.0)], "B": [("C", 1.0)], "C": []}
        dist, prev = bellman_ford(adj, "A")
        assert dist["A"] == 0.0
        assert dist["B"] == 2.0
        assert dist["C"] == 3.0  # A→B→C = 2+1

    def test_unreachable_node(self):
        """Nodo no alcanzable desde la fuente."""
        adj = {"A": [("B", 1.0)], "B": [], "C": [("A", 1.0)]}
        dist, _ = bellman_ford(adj, "A")
        assert dist["C"] == float('inf')

    def test_negative_cycle_detection(self):
        """Ciclo de peso negativo debe lanzar ValueError."""
        adj = {
            "A": [("B", 1.0)],
            "B": [("C", -2.0)],
            "C": [("A", -2.0)]  # ciclo A→B→C→A con peso -3 < 0
        }
        with pytest.raises(ValueError, match="Ciclo de peso negativo"):
            bellman_ford(adj, "A")

    def test_path_reconstruction(self):
        """Reconstrucción correcta del camino mínimo."""
        adj = {"A": [("B", 1.0)], "B": [("C", 1.0)], "C": []}
        dist, prev = bellman_ford(adj, "A")
        path = reconstruct_path(prev, "A", "C")
        assert path == ["A", "B", "C"]

    def test_single_node(self):
        """Grafo de un solo nodo."""
        adj = {"A": []}
        dist, _ = bellman_ford(adj, "A")
        assert dist["A"] == 0.0


# Tests Union-Find

class TestUnionFind:
    def test_initial_state(self):
        """Cada nodo inicia en su propio componente."""
        dsu = UnionFind({"A", "B", "C"})
        assert not dsu.connected("A", "B")
        assert not dsu.connected("B", "C")
        assert dsu.num_components == 3

    def test_union_reduces_components(self):
        """Unir dos nodos reduce el número de componentes."""
        dsu = UnionFind({"A", "B", "C"})
        result = dsu.union("A", "B")
        assert result is True
        assert dsu.connected("A", "B")
        assert dsu.num_components == 2

    def test_union_same_component(self):
        """Unir nodos del mismo componente no hace nada."""
        dsu = UnionFind({"A", "B"})
        dsu.union("A", "B")
        result = dsu.union("A", "B")  # segunda unión
        assert result is False

    def test_path_compression(self):
        """Find con compresión retorna el mismo representante."""
        dsu = UnionFind({"A", "B", "C", "D"})
        dsu.union("A", "B")
        dsu.union("B", "C")
        dsu.union("C", "D")
        assert dsu.find("A") == dsu.find("D")


# Tests Kruskal MST

class TestKruskalMST:
    def test_simple_mst(self):
        """MST de un grafo triangular simple."""
        nodes = {"A", "B", "C"}
        edges = [("A", "B", 1.0), ("B", "C", 2.0), ("A", "C", 3.0)]
        mst, weight = kruskal_mst(nodes, edges)
        assert len(mst) == 2        # |V| - 1 = 2
        assert weight == 3.0        # 1 + 2

    def test_mst_no_cycles(self):
        """El MST no contiene ciclos."""
        nodes = {"A", "B", "C", "D"}
        edges = [
            ("A", "B", 1.0), ("B", "C", 2.0),
            ("C", "D", 3.0), ("A", "D", 10.0),
            ("B", "D", 5.0)
        ]
        mst, _ = kruskal_mst(nodes, edges)
        assert len(mst) == 3  # árbol con 4 nodos tiene 3 aristas

    def test_maxst_selects_heavy_edges(self):
        """MaxST selecciona las aristas más pesadas."""
        nodes = {"A", "B", "C"}
        edges = [("A", "B", 10.0), ("B", "C", 1.0), ("A", "C", 5.0)]
        maxst, weight = kruskal_mst(nodes, edges, maximize=True)
        assert weight == 15.0  # 10 + 5 (las dos más pesadas)

    def test_symmetrize_edges(self):
        """Aristas (A,B) y (B,A) se consolidan."""
        directed = [("A", "B", 3.0), ("B", "A", 2.0), ("B", "C", 1.0)]
        undirected = symmetrize_edges(directed)
        # Debe haber 2 aristas únicas: {A,B} y {B,C}
        assert len(undirected) == 2
        edge_set = {(min(s, d), max(s, d)) for s, d, _ in undirected}
        assert ("A", "B") in edge_set
        assert ("B", "C") in edge_set


# Tests PageRank

class TestPageRank:
    def test_sum_to_one(self):
        """Los scores de PageRank deben sumar aproximadamente 1."""
        adj = {
            "A": [("B", 1.0), ("C", 1.0)],
            "B": [("C", 1.0)],
            "C": [("A", 1.0)]
        }
        nodes = {"A", "B", "C"}
        pr = pagerank(adj, nodes, damping=0.85)
        total = sum(pr.values())
        assert abs(total - 1.0) < 0.01

    def test_sink_node_handling(self):
        """Nodo sin aristas salientes no produce división por cero."""
        adj = {"A": [("B", 1.0)], "B": []}  # B es sink
        nodes = {"A", "B"}
        pr = pagerank(adj, nodes)
        assert all(v >= 0 for v in pr.values())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
