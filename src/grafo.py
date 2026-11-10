"""
grafo.py
========
Carga del dataset y construcción del grafo.

En este proyecto modelamos las transferencias de un token ERC-20 de Ethereum
como un grafo DIRIGIDO y PONDERADO G = (V, E):

    - V (vértices): las direcciones (wallets, exchanges, contratos).
    - E (aristas): las transferencias de una dirección a otra.
    - w(e) (peso): la cantidad transferida.

Solo usamos estructuras nativas de Python: diccionarios y listas.
"""

from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

# Lista de adyacencia: cada nodo apunta a una lista de (vecino, peso).
AdjList = Dict[str, List[Tuple[str, float]]]


class Grafo:
    """Grafo dirigido y ponderado representado con una lista de adyacencia."""

    def __init__(self) -> None:
        # {origen: [(destino, peso), ...]}
        self.adj: AdjList = defaultdict(list)
        # Todos los vértices del grafo.
        self.nodos: Set[str] = set()
        # Lista de aristas como (origen, destino, peso).
        self.aristas: List[Tuple[str, str, float]] = []
        # {dirección: {"nombre": ..., "tipo": ...}} para mostrar resultados legibles.
        self.etiquetas: Dict[str, Dict[str, str]] = {}

    # ------------------------------------------------------------------
    # Carga de datos
    # ------------------------------------------------------------------

    def cargar_transferencias(self, ruta_csv: str, max_filas: Optional[int] = None) -> "Grafo":
        """Lee un CSV de transferencias y llena la lista de adyacencia.

        El CSV debe tener (al menos) las columnas:
            from_address, to_address, value
        (puede tener más columnas; se ignoran).

        Parámetros:
            ruta_csv: ruta al archivo CSV.
            max_filas: opcional. Leer solo las primeras `max_filas` filas
                       (útil para probar con una muestra).

        Retorna:
            self, para poder encadenar llamadas.
        """
        import csv

        with open(ruta_csv, newline="", encoding="utf-8") as archivo:
            lector = csv.DictReader(archivo)
            for i, fila in enumerate(lector):
                if max_filas is not None and i >= max_filas:
                    break

                origen = fila["from_address"].strip().lower()
                destino = fila["to_address"].strip().lower()
                peso = float(fila["value"])

                # Registramos los dos extremos como nodos.
                self.nodos.add(origen)
                self.nodos.add(destino)

                # Agregamos la arista dirigida origen -> destino.
                self.adj[origen].append((destino, peso))
                self.aristas.append((origen, destino, peso))

        return self

    def cargar_etiquetas(self, ruta_csv: str) -> "Grafo":
        """Lee un CSV con el nombre legible de cada dirección.

        El CSV debe tener las columnas: address, name, type.
        """
        import csv

        with open(ruta_csv, newline="", encoding="utf-8") as archivo:
            lector = csv.DictReader(archivo)
            for fila in lector:
                addr = fila["address"].strip().lower()
                self.etiquetas[addr] = {
                    "nombre": fila.get("name", "").strip(),
                    "tipo": fila.get("type", "").strip(),
                }
        return self

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def nombre(self, addr: str) -> str:
        """Nombre legible de un nodo, o la propia dirección si no está etiquetada."""
        return self.etiquetas.get(addr, {}).get("nombre", addr)

    def resumen(self) -> Dict[str, float]:
        """Estadísticas básicas: número de nodos, aristas y densidad."""
        n = len(self.nodos)
        m = len(self.aristas)
        # Densidad de un grafo dirigido: |E| / (|V| * (|V| - 1))
        densidad = m / (n * (n - 1)) if n > 1 else 0.0
        return {"nodos": n, "aristas": m, "densidad": round(densidad, 4)}
