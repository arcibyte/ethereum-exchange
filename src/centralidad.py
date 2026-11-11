from typing import Dict, List, Optional, Set, Tuple


def centralidad_grado(adj, nodos):
    """Centralidad de grado: C(v) = (vecinos distintos de v) / (|V| - 1).

    Cuenta direcciones DISTINTAS con las que v se conecta (envia o recibe),
    sin importar cuántas transferencias haya entre ellas. Va de 0 a 1
    """
    n = len(nodos)
    if n <= 1:
        return {v: 0.0 for v in nodos}
    vecinos = {v: set() for v in nodos}
    for u, destinos in adj.items():
        for v, _ in destinos:
            if u != v and u in vecinos and v in vecinos:
                vecinos[u].add(v)
                vecinos[v].add(u)
    return {v: len(vecinos[v]) / (n - 1) for v in nodos}


def pagerank(
    adj: Dict[str, List[Tuple[str, float]]],
    nodos: Set[str],
    amortiguacion: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-6,
) -> Dict[str, float]:
    """Calcula PageRank con el método de iteración de potencias.

    parametros:
        adj: lista de adyacencia
        nodos: conjunto de todos los vertices
        amortiguacion: factor de amortiguación d (0.85 por defecto)
        max_iter: máximo número de iteraciones
        tol: tolerancia de convergencia

    Retorna:
        {nodo: score} con scores que suman aproximadamente 1
    """
    n = len(nodos)
    if n == 0:
        return {}

    lista = list(nodos)

    # Puntaje inicial: todos los nodos igual de importantes (1/N).
    pr = {v: 1.0 / n for v in lista}

    # Grado de salida de cada nodo.
    grado_salida = {v: len(adj.get(v, [])) for v in lista}

    # Lista de adyacencia INVERSA: quién apunta a cada nodo.
    # Esto hace el cálculo más directo y eficiente.
    entrantes = {v: [] for v in lista}
    for u, vecinos in adj.items():
        for v, _ in vecinos:
            if v in entrantes:
                entrantes[v].append(u)

    for _ in range(max_iter):
        base = (1.0 - amortiguacion) / n

        # Los nodos "sumidero" (sin aristas de salida) no reparten su
        # importancia a nadie. Para que los puntajes sigan sumando 1, su masa
        # se reparte por igual entre todos los nodos.
        masa_sumidero = sum(pr[v] for v in lista if grado_salida[v] == 0)

        nuevo = {}
        for v in lista:
            suma = 0.0
            for u in entrantes[v]:
                if grado_salida[u] > 0:
                    suma += pr[u] / grado_salida[u]
            nuevo[v] = base + amortiguacion * (suma + masa_sumidero / n)

        # Medimos cuánto cambió el vector para saber si ya convergió.
        delta = sum(abs(nuevo[v] - pr[v]) for v in lista)
        pr = nuevo
        if delta < tol:
            break

    return pr


def top_n(
    puntajes: Dict[str, float],
    n: int = 10,
    etiquetas: Optional[Dict[str, Dict[str, str]]] = None,
) -> List[Tuple[str, float, str]]:
    """devuelve los `n` nodos con mayor puntaje, ordenados de mayor a menor

    retorna:
        lista de tuplas (direccion, puntaje, nombre) para mayor orden
    """
    etiquetas = etiquetas or {}

    # Orden: mayor puntaje primero; si empatan, por direccion (alfabetico)
    ordenados = sorted(puntajes.items(), key=lambda par: (-par[1], par[0]))[:n]

    resultado = []
    for addr, score in ordenados:
        # Si la etiqueta no existe o su nombre esta vacio, usamos la direccion
        nombre = etiquetas.get(addr, {}).get("nombre") or addr
        resultado.append((addr, score, nombre))
    return resultado


def construir_adyacencia(aristas: List[Tuple[str, str, float]]) -> Dict[str, List[Tuple[str, float]]]:
    """Convierte la lista compartida de aristas en lista de adyacencia."""
    adj: Dict[str, List[Tuple[str, float]]] = {}
    for origen, destino, peso in aristas:
        adj.setdefault(origen, []).append((destino, float(peso)))
    return adj


def nodos_de_aristas(aristas: List[Tuple[str, str, float]]) -> Set[str]:
    """Devuelve todos los nodos que aparecen en la lista de aristas."""
    nodos: Set[str] = set()
    for origen, destino, _ in aristas:
        nodos.add(origen)
        nodos.add(destino)
    return nodos


def centralidad_grado_desde_aristas(
    aristas: List[Tuple[str, str, float]],
) -> Dict[str, float]:
    """Centralidad de grado a partir de la lista compartida de aristas."""
    return centralidad_grado(construir_adyacencia(aristas), nodos_de_aristas(aristas))


def pagerank_desde_aristas(
    aristas: List[Tuple[str, str, float]],
    **opciones,
) -> Dict[str, float]:
    """PageRank a partir de la lista compartida de aristas."""
    return pagerank(
        construir_adyacencia(aristas),
        nodos_de_aristas(aristas),
        **opciones,
    )
