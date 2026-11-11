"""
comunidades_liquidez.py
=======================
Tarea 3 — Comunidades de liquidez mediante Louvain.

Responsable: Juan Pablo Álvarez.

Es el código de la Tarea 3 del notebook entregable
(`proyecto_grafos_ethereum.ipynb`), sacado a un módulo para poder probarlo
con pytest. Solo usa la librería estándar.

Grafo: no dirigido y ponderado. Nodos = exchanges + contrapartes principales;
peso de {u, v} = número de transferencias stablecoin entre u y v (en ambos
sentidos). Representación: diccionario de diccionarios {u: {v: peso}}.

Funciones del notebook (sin cambios de lógica):
    modularity, louvain_once, louvain, label_propagation

Funciones nuevas para validar y analizar sensibilidad:
    grafo_no_dirigido      construye {u: {v: peso}} desde (src, dst, peso)
    modularidad_definicion Q con la doble suma de la definición, O(n^2)
    nmi                    información mutua normalizada entre particiones
    estabilidad_reinicios  Q y NMI de cada reinicio de Louvain
    barrido_resolucion     comunidades y Q para varios valores de gamma
"""

import math
import random
from collections import Counter, defaultdict
from typing import Dict, Hashable, Iterable, List, Tuple

def modularity(adj, loops, comm, resolution=1.0):
    m = sum(sum(adj[u].values()) for u in adj) / 2 + sum(loops.values())
    if m == 0:
        return 0.0
    in_c = defaultdict(float)
    tot_c = defaultdict(float)
    for u in adj:
        cu = comm[u]
        tot_c[cu] += sum(adj[u].values()) + 2 * loops.get(u, 0.0)
        in_c[cu] += loops.get(u, 0.0)
        for v, w in adj[u].items():
            if v > u and comm[v] == cu:
                in_c[cu] += w
    return sum(in_c[c] / m - resolution * (tot_c[c] / (2 * m)) ** 2
               for c in set(comm.values()))


def louvain_once(orig_nodes, adj0, resolution=1.0, seed=0, max_levels=20):
    rng = random.Random(seed)
    adj = {u: dict(adj0[u]) for u in orig_nodes}
    loops = {u: 0.0 for u in orig_nodes}
    membership = {u: u for u in orig_nodes}
    levels = []

    for level in range(max_levels):
        m = sum(sum(adj[u].values()) for u in adj) / 2 + sum(loops.values())
        if m == 0:
            break
        k = {u: sum(adj[u].values()) + 2 * loops[u] for u in adj}
        tot = dict(k)
        comm = {u: u for u in adj}
        order = sorted(adj)
        moves_total = 0

        for _ in range(200):
            rng.shuffle(order)
            moved = 0
            for u in order:
                ci = comm[u]
                nc = defaultdict(float)
                for v, w in adj[u].items():
                    if v != u:
                        nc[comm[v]] += w
                tot[ci] -= k[u]
                best_c, best_gain = ci, 0.0
                for c, w in nc.items():
                    gain = w / m - resolution * tot.get(c, 0.0) * k[u] / (2 * m * m)
                    if gain > best_gain + 1e-12:
                        best_gain, best_c = gain, c
                if best_c != ci:
                    comm[u] = best_c
                    tot[best_c] += k[u]
                    moved += 1
                else:
                    tot[ci] += k[u]
            moves_total += moved
            if moved == 0:
                break

        membership = {o: comm[v] for o, v in membership.items()}
        levels.append({"level": level, "n_comms": len(set(comm.values())),
                       "modularity": modularity(adj, loops, comm, resolution),
                       "moves": moves_total})
        if moves_total == 0:
            break

        new_adj = defaultdict(dict)
        new_loops = defaultdict(float)
        for u in adj:
            cu = comm[u]
            new_adj.setdefault(cu, {})
            new_loops[cu] += loops[u]
            for v, w in adj[u].items():
                if v < u:
                    continue
                cv = comm[v]
                if cu == cv:
                    new_loops[cu] += w
                else:
                    new_adj[cu][cv] = new_adj[cu].get(cv, 0.0) + w
                    new_adj[cv][cu] = new_adj[cv].get(cu, 0.0) + w
        adj = {u: dict(new_adj[u]) for u in new_adj}
        loops = {u: new_loops.get(u, 0.0) for u in adj}
        if len(adj) >= len(orig_nodes):
            break

    adj_orig = {u: dict(adj0[u]) for u in orig_nodes}
    loops0 = {u: 0.0 for u in orig_nodes}
    return membership, modularity(adj_orig, loops0, membership, resolution), levels


def louvain(nodes, adj, resolution=1.0, n_restarts=10, base_seed=0):
    best = None
    for r in range(n_restarts):
        mem, q, levels = louvain_once(nodes, adj, resolution, base_seed + r)
        if best is None or q > best[1] + 1e-12:
            best = (mem, q, levels, r)
    return best


def label_propagation(nodes, adj, max_iter=100, seed=42):
    rng = random.Random(seed)
    labels = {u: u for u in nodes}
    order = sorted(nodes)
    for _ in range(max_iter):
        rng.shuffle(order)
        changed = 0
        for u in order:
            counts = defaultdict(float)
            for v, w in adj[u].items():
                counts[labels[v]] += w
            if not counts:
                continue
            best = max(counts.values())
            candidates = [c for c, w in counts.items() if abs(w - best) < 1e-12]
            new = labels[u] if labels[u] in candidates else min(candidates)
            if new != labels[u]:
                labels[u] = new
                changed += 1
        if changed == 0:
            break
    return labels


# ----------------------------------------------------------------------
# Construcción del grafo
# ----------------------------------------------------------------------

def grafo_no_dirigido(aristas: Iterable[Tuple[str, str, float]]) -> Dict[str, Dict[str, float]]:
    """Grafo no dirigido {u: {v: peso}} sumando ambos sentidos.

    Igual que la celda de construcción del notebook: se ignoran los autolazos
    y los pesos de u->v y v->u se suman en la arista {u, v}.
    """
    g: Dict[str, Dict[str, float]] = defaultdict(dict)
    for s, d, w in aristas:
        if s == d:
            continue
        w = float(w)
        g[s][d] = g[s].get(d, 0.0) + w
        g[d][s] = g[d].get(s, 0.0) + w
    return {u: dict(vecinos) for u, vecinos in g.items()}


# ----------------------------------------------------------------------
# Validación
# ----------------------------------------------------------------------

def modularidad_definicion(adj: Dict[str, Dict[str, float]], comm: Dict[str, Hashable]) -> float:
    """Modularidad con la fórmula de la definición (doble suma sobre i, j).

        Q = 1/(2m) * sum_ij [A_ij - k_i k_j / (2m)] * delta(c_i, c_j)

    Es O(n^2): solo sirve para comprobar `modularity` en grafos pequeños.
    """
    nodos = list(adj)
    k = {u: sum(adj[u].values()) for u in nodos}
    dos_m = sum(k.values())
    if dos_m == 0:
        return 0.0
    q = 0.0
    for i in nodos:
        for j in nodos:
            if comm[i] == comm[j]:
                q += adj[i].get(j, 0.0) - k[i] * k[j] / dos_m
    return q / dos_m


def nmi(particion_a: Dict[str, Hashable], particion_b: Dict[str, Hashable]) -> float:
    """Información mutua normalizada entre dos particiones de los mismos nodos.

    NMI = 2 I(A; B) / (H(A) + H(B)), en [0, 1]: 1 = particiones idénticas
    (salvo el nombre de las comunidades), 0 = independientes.
    """
    nodos = list(particion_a)
    n = len(nodos)
    if n == 0:
        return 1.0
    ca = Counter(particion_a[u] for u in nodos)
    cb = Counter(particion_b[u] for u in nodos)
    cab = Counter((particion_a[u], particion_b[u]) for u in nodos)
    h_a = -sum(c / n * math.log(c / n) for c in ca.values())
    h_b = -sum(c / n * math.log(c / n) for c in cb.values())
    if h_a + h_b == 0:
        return 1.0
    info = sum(c / n * math.log(c * n / (ca[a] * cb[b])) for (a, b), c in cab.items())
    return 2 * info / (h_a + h_b)


# ----------------------------------------------------------------------
# Estabilidad y sensibilidad
# ----------------------------------------------------------------------

def estabilidad_reinicios(nodes, adj, n_restarts=10, base_seed=0, resolution=1.0) -> List[Dict[str, float]]:
    """Ejecuta Louvain con varias semillas y compara cada resultado con el mejor.

    Retorna una fila por reinicio: semilla, comunidades, Q y NMI contra la
    partición de mayor Q.
    """
    corridas = []
    for r in range(n_restarts):
        mem, q, _ = louvain_once(nodes, adj, resolution, base_seed + r)
        corridas.append((base_seed + r, mem, q))
    mejor = max(corridas, key=lambda t: t[2])[1]
    return [
        {"semilla": s, "comunidades": len(set(m.values())), "Q": q, "NMI_vs_mejor": nmi(m, mejor)}
        for s, m, q in corridas
    ]


def barrido_resolucion(nodes, adj, gammas=(0.5, 1.0, 1.5, 2.0, 3.0), n_restarts=3) -> List[Dict[str, float]]:
    """Louvain para varios valores de resolución gamma.

    gamma < 1 favorece comunidades grandes; gamma > 1, comunidades pequeñas.
    Se reporta la Q con gamma = 1 para poder comparar las particiones.
    """
    loops = {u: 0.0 for u in nodes}
    filas = []
    for g in gammas:
        mem, _, _, _ = louvain(nodes, adj, resolution=g, n_restarts=n_restarts)
        filas.append({
            "gamma": g,
            "comunidades": len(set(mem.values())),
            "Q_gamma_1": modularity(adj, loops, mem, 1.0),
        })
    return filas
