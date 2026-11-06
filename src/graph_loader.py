"""
graph_loader.py – Módulo de ingesta y construcción del grafo.

Responsable: Pablo Álvarez

Este módulo lee los archivos CSV del dataset Ethereum Token Transfers y
construye una representación de grafo dirigido y ponderado usando
exclusivamente estructuras nativas de Python (diccionarios y listas).

Restricciones del proyecto:
    - NO usar NetworkX, igraph ni scipy para la lógica central.
    - NetworkX solo se permite para visualizaciones o benchmarking.
    - Restricción TOTAL: No implementar Dijkstra en ninguna tarea.
"""

from __future__ import annotations

import csv
import os
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Tipos canónicos del grafo
# ---------------------------------------------------------------------------

# Grafo como lista de adyacencia:
#   AdjList[nodo_origen] = [(nodo_destino, peso), ...]
AdjList = Dict[str, List[Tuple[str, float]]]

# Mapa de propiedades de nodos (etiquetas, tipos, etc.)
NodeMeta = Dict[str, Dict[str, str]]


# ---------------------------------------------------------------------------
# Clase principal
# ---------------------------------------------------------------------------

class EthereumGraphLoader:
    """Carga y construye el grafo de transferencias de tokens Ethereum.

    El grafo es:
        G = (V, E)  donde
        V = conjunto de direcciones Ethereum únicas (from_address ∪ to_address)
        E = conjunto de transferencias (from_address → to_address)
            con peso w(e) = valor total transferido (en unidades ERC-20 mínimas)

    Attributes:
        adj (AdjList): Lista de adyacencia {src: [(dst, weight), ...]}.
        nodes (Set[str]): Conjunto de todos los nodos (vértices) del grafo.
        edges (List[Tuple[str, str, float]]): Lista de aristas (src, dst, weight).
        node_meta (NodeMeta): Metadatos de nodos (tipo: dex/exchange/stablecoin).
        num_nodes (int): Cardinalidad de V.
        num_edges (int): Cardinalidad de E.
    """

    def __init__(self) -> None:
        """Inicializa un grafo vacío."""
        self.adj: AdjList = defaultdict(list)
        self.nodes: Set[str] = set()
        self.edges: List[Tuple[str, str, float]] = []
        self.node_meta: NodeMeta = {}
        self.num_nodes: int = 0
        self.num_edges: int = 0

    # ------------------------------------------------------------------
    # Métodos de carga
    # ------------------------------------------------------------------

    def load_transfers(
        self,
        csv_path: str,
        max_rows: Optional[int] = None,
        aggregate: bool = True,
    ) -> "EthereumGraphLoader":
        """Lee el CSV de transferencias y construye la lista de adyacencia.

        Para cada fila del CSV, se crea una arista dirigida:
            from_address  →  to_address   con peso = value

        Si `aggregate=True`, aristas paralelas entre el mismo par (src, dst)
        se consolidan sumando sus pesos (multigraph → weighted digraph).

        Args:
            csv_path: Ruta absoluta al archivo token_transfers_full.csv.
            max_rows: Límite de filas a leer (None = leer todo el archivo).
            aggregate: Si True, agrega aristas paralelas sumando pesos.

        Returns:
            self (para encadenamiento fluido).

        Raises:
            FileNotFoundError: Si csv_path no existe.

        Example:
            >>> loader = EthereumGraphLoader()
            >>> loader.load_transfers('data/samples/token_transfers_sample_500k.csv', max_rows=100_000)
            >>> print(loader.num_nodes, loader.num_edges)
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Dataset no encontrado: {csv_path}")

        # Acumulador temporal para agregación de pesos
        # edge_weights[(src, dst)] = peso_acumulado
        edge_weights: Dict[Tuple[str, str], float] = defaultdict(float)

        with open(csv_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            # Invariante: row_count ≤ max_rows (si max_rows no es None)
            for row_count, row in enumerate(reader):
                if max_rows is not None and row_count >= max_rows:
                    break

                src: str = row["from_address"].strip().lower()
                dst: str = row["to_address"].strip().lower()
                # Valor en unidades mínimas del token (uint256); se trata como float
                try:
                    weight: float = float(row["value"])
                except (ValueError, KeyError):
                    weight = 1.0  # peso unitario si el valor es inválido

                # Agregar nodos al conjunto V
                self.nodes.add(src)
                self.nodes.add(dst)

                if aggregate:
                    edge_weights[(src, dst)] += weight
                else:
                    self.adj[src].append((dst, weight))
                    self.edges.append((src, dst, weight))

        # Construir lista de adyacencia a partir del diccionario agregado
        if aggregate:
            for (src, dst), w in edge_weights.items():
                self.adj[src].append((dst, w))
                self.edges.append((src, dst, w))

        self.num_nodes = len(self.nodes)
        self.num_edges = len(self.edges)
        return self

    def load_node_labels(
        self,
        exchange_labels_path: str,
        stablecoin_labels_path: str,
    ) -> "EthereumGraphLoader":
        """Enriquece los nodos con etiquetas semánticas (exchange, DEX, stablecoin).

        Args:
            exchange_labels_path: Ruta a exchangeLabels.csv (columnas: type,address,name).
            stablecoin_labels_path: Ruta a alphacore_labels_stablecoin.csv
                                    (columnas: label,address,name,asset).

        Returns:
            self (para encadenamiento fluido).
        """
        # Cargar etiquetas de exchanges/DEX
        if os.path.exists(exchange_labels_path):
            with open(exchange_labels_path, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    addr = row.get("address", "").strip().lower()
                    if addr:
                        self.node_meta[addr] = {
                            "type": row.get("type", "exchange").strip(),
                            "name": row.get("name", "").strip(),
                        }

        # Cargar etiquetas de stablecoins/liquidity pools
        if os.path.exists(stablecoin_labels_path):
            with open(stablecoin_labels_path, newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    addr = row.get("address", "").strip().lower()
                    if addr:
                        self.node_meta[addr] = {
                            "type": row.get("label", "stablecoin").strip(),
                            "name": row.get("name", "").strip(),
                            "asset": row.get("asset", "").strip(),
                        }
        return self

    # ------------------------------------------------------------------
    # Métricas exploratorias (Sección 1 del Notebook – 10%)
    # ------------------------------------------------------------------

    def degree_sequence(self) -> Dict[str, Dict[str, int]]:
        """Calcula grado de entrada y salida para cada nodo.

        Returns:
            Dict con estructura:
                {nodo: {"in_degree": int, "out_degree": int, "total_degree": int}}

        Note:
            Complejidad: O(|V| + |E|)
        """
        in_deg: Dict[str, int] = defaultdict(int)
        out_deg: Dict[str, int] = defaultdict(int)

        # TODO (Jhon): completar el recorrido sobre self.adj
        # Invariante de ciclo: al finalizar cada iteración (src, neighbors),
        # out_deg[src] contiene el grado de salida completo de src,
        # e in_deg[dst] se ha incrementado por cada arista src→dst procesada.
        for src, neighbors in self.adj.items():
            out_deg[src] += len(neighbors)
            for dst, _ in neighbors:
                in_deg[dst] += 1

        result: Dict[str, Dict[str, int]] = {}
        for node in self.nodes:
            result[node] = {
                "in_degree": in_deg.get(node, 0),
                "out_degree": out_deg.get(node, 0),
                "total_degree": in_deg.get(node, 0) + out_deg.get(node, 0),
            }
        return result

    def density(self) -> float:
        """Calcula la densidad del grafo dirigido.

        Fórmula:
            δ(G) = |E| / (|V| · (|V| - 1))

        Returns:
            Densidad como float ∈ [0, 1].
        """
        v = self.num_nodes
        if v < 2:
            return 0.0
        return self.num_edges / (v * (v - 1))

    def summary(self) -> Dict[str, object]:
        """Retorna un resumen estadístico del grafo cargado.

        Returns:
            Diccionario con métricas básicas del grafo.
        """
        degrees = self.degree_sequence()
        all_total = [d["total_degree"] for d in degrees.values()]
        avg_deg = sum(all_total) / len(all_total) if all_total else 0.0
        max_deg_node = max(degrees, key=lambda n: degrees[n]["total_degree"]) if degrees else None

        return {
            "num_nodes": self.num_nodes,
            "num_edges": self.num_edges,
            "density": self.density(),
            "avg_degree": round(avg_deg, 4),
            "max_degree_node": max_deg_node,
            "max_degree_value": degrees[max_deg_node]["total_degree"] if max_deg_node else 0,
            "labeled_nodes": len(self.node_meta),
        }
