"""
evaluacion.py
=============
Capa COMPARTIDA: medir qué tan bien un ranking de nodos encuentra exchanges.

El dataset trae 296 direcciones de exchanges etiquetadas. Los autores del
dataset (paper AlphaCore, KDD 2021) evalúan cada algoritmo así: ordenan los
nodos por su puntaje y cuentan cuántos exchanges quedan entre los k primeros
(función `scoreResult` de github.com/friedhelmvictor/alphacore):

    precisión@k = encontrados / k
    recall@k    = encontrados / exchanges presentes en el grafo

Usar la misma medida permite comparar nuestros resultados con los del
artículo. Cualquier tarea que produzca un puntaje por nodo (grado, PageRank,
distancia de Bellman-Ford, k-core, ...) se evalúa con `evaluar_ranking`.

Nota: las etiquetas son parciales. Un nodo sin etiqueta puede ser un exchange
que nadie etiquetó, así que la precisión medida es una cota inferior.

Solo se usa la librería estándar de Python.
"""

from typing import Dict, Iterable, List, Sequence, Set

K_POR_DEFECTO = (10, 20, 50, 100)


def ranking(puntajes: Dict[str, float], mayor_es_mejor: bool = True) -> List[str]:
    """Ordena los nodos por puntaje.

    Los empates se rompen por la dirección, para que el resultado sea el mismo
    en cada ejecución. Con `mayor_es_mejor=False` (por ejemplo, una distancia)
    el menor puntaje queda primero.
    """
    signo = -1.0 if mayor_es_mejor else 1.0
    return sorted(puntajes, key=lambda nodo: (signo * puntajes[nodo], nodo))


def encontrados_en_k(orden: Sequence[str], relevantes: Set[str], k: int) -> int:
    """Cuántos nodos relevantes hay entre los k primeros del ranking."""
    return sum(1 for nodo in orden[:k] if nodo in relevantes)


def evaluar_ranking(
    puntajes: Dict[str, float],
    relevantes: Iterable[str],
    ks: Iterable[int] = K_POR_DEFECTO,
    mayor_es_mejor: bool = True,
) -> List[Dict[str, float]]:
    """Precisión@k y recall@k de un puntaje por nodo.

    Parámetros:
        puntajes: {nodo: puntaje}.
        relevantes: direcciones que se quieren encontrar (exchanges). Solo
            cuentan las que están en `puntajes`.
        ks: valores de k a evaluar.
        mayor_es_mejor: False si un puntaje menor es mejor.

    Retorna una fila por k: {"k", "encontrados", "precision", "recall"}.
    """
    presentes = {nodo for nodo in relevantes if nodo in puntajes}
    orden = ranking(puntajes, mayor_es_mejor)
    filas = []
    for k in ks:
        encontrados = encontrados_en_k(orden, presentes, k)
        filas.append({
            "k": k,
            "encontrados": encontrados,
            "precision": encontrados / k if k else 0.0,
            "recall": encontrados / len(presentes) if presentes else 0.0,
        })
    return filas
