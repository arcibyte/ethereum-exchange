"""
comunidades.py
==============
Tarea 3 — Detección de comunidades con Louvain (versión didáctica).

Responsable: Emerson Ballesteros.

¿Qué es una comunidad?
----------------------
Una comunidad es un grupo de nodos que interactúa mucho entre sí y poco con
el resto de la red. Por ejemplo, los exchanges centralizados y sus usuarios
suelen formar un grupo, y los DEX con sus usuarios otro.

¿Cómo se mide si una partición es buena?
----------------------------------------
Con la **modularidad Q**. La idea es comparar las aristas que quedan *dentro*
de los grupos con las que aparecerían si las conexiones fueran al azar:

    Q = (1 / 2m) * suma_{i,j} [ A_ij - k_i*k_j/(2m) ] * delta(c_i, c_j)

    - A_ij: peso de la arista entre i y j.
    - k_i: grado (suma de pesos) del nodo i.
    - m: peso total del grafo.
    - delta(c_i, c_j): 1 si i y j están en la misma comunidad, 0 si no.

Para no recorrer todos los pares de nodos, el código usa una fórmula
equivalente que se calcula por comunidad:

    Q = suma_c [ L_c / m - (K_c / (2m))^2 ]

    - L_c: peso de las aristas internas de la comunidad c.
    - K_c: suma de grados de los nodos de la comunidad c.

Valores de Q por encima de ~0.3 sugieren una buena estructura de comunidades.

Algoritmo (fase principal de Louvain)
-------------------------------------
1. Cada nodo empieza en su propia comunidad.
2. Se repite hasta que nada cambie:
   - Se recorren los nodos en orden aleatorio.
   - Para cada nodo, se prueba moverlo a la comunidad de cada vecino.
   - Se queda con el movimiento que más aumente Q.
3. Se devuelve la comunidad final de cada nodo.

Esta es una versión **sencilla y fácil de leer**: recalcula Q completo en cada
prueba. La versión de producción usa una fórmula incremental (ΔQ) y una fase
de agregación. Al final del archivo hay una lista de posibles mejoras.
"""

import random
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

# Tipos con nombres claros para que el código se lea mejor.
Adyacencia = Dict[str, List[Tuple[str, float]]]
Comunidades = Dict[str, int]


def simetrizar(adj: Adyacencia) -> Adyacencia:
    """Convierte un grafo dirigido en un grafo NO dirigido.

    Si existe la arista u -> v con peso w, se crea la arista no dirigida
    {u, v} con peso w. Si existen u -> v y v -> u, los pesos se suman.

    Para Louvain trabajamos con el grafo no dirigido porque una comunidad no
    tiene dirección: interesa si dos nodos están conectados, no en qué sentido.
    """
    # Paso 1: juntar los pesos de cada par no ordenado {a, b}.
    pesos_por_par: Dict[Tuple[str, str], float] = defaultdict(float)

    for origen, vecinos in adj.items():
        for destino, peso in vecinos:
            # sorted((origen, destino)) hace que (A, B) y (B, A) sean el
            # mismo par. Así no contamos dos veces la misma conexión.
            a, b = sorted((origen, destino))
            pesos_por_par[(a, b)] += peso

    # Paso 2: construir la lista de adyacencia no dirigida.
    adj_no_dirigida: Adyacencia = defaultdict(list)

    for (a, b), peso in pesos_por_par.items():
        # La arista existe en los dos sentidos.
        adj_no_dirigida[a].append((b, peso))
        adj_no_dirigida[b].append((a, peso))

    return dict(adj_no_dirigida)


def calcular_grados(adj_no_dirigida: Adyacencia) -> Dict[str, float]:
    """Calcula el grado ponderado de cada nodo.

    El grado de un nodo es la suma de los pesos de todas sus aristas.
    En un grafo no dirigido, cada arista aporta su peso a los dos extremos.
    """
    grados: Dict[str, float] = {}

    for nodo, vecinos in adj_no_dirigida.items():
        suma_de_pesos = 0.0
        for _, peso in vecinos:
            suma_de_pesos += peso
        grados[nodo] = suma_de_pesos

    return grados


def modularidad(
    adj_no_dirigida: Adyacencia,
    comunidades: Comunidades,
) -> float:
    """Calcula la modularidad Q de una partición.

    Se usa la fórmula por comunidad:

        Q = suma_c [ L_c / m - (K_c / (2m))^2 ]

    Parámetros:
        adj_no_dirigida: lista de adyacencia del grafo no dirigido.
        comunidades: diccionario {nodo: id_de_comunidad}.

    Retorna:
        Q, un número entre -0.5 y 1.0.
    """
    # Paso 1: grado de cada nodo.
    grados = calcular_grados(adj_no_dirigida)

    # Paso 2: m = peso total del grafo.
    # La suma de todos los grados cuenta cada arista dos veces, por eso / 2.
    suma_de_grados = 0.0
    for grado in grados.values():
        suma_de_grados += grado
    peso_total = suma_de_grados / 2.0

    if peso_total == 0.0:
        return 0.0

    # Paso 3: K_c = suma de grados de los nodos de cada comunidad.
    grado_por_comunidad: Dict[int, float] = defaultdict(float)
    for nodo, grado in grados.items():
        comunidad = comunidades[nodo]
        grado_por_comunidad[comunidad] += grado

    # Paso 4: L_c = peso de las aristas internas de cada comunidad.
    # Cada arista no dirigida se cuenta una sola vez. Para lograrlo, solo se
    # suma cuando nodo < vecino (o una vez si es un auto-loop).
    interno_por_comunidad: Dict[int, float] = defaultdict(float)

    for nodo, vecinos in adj_no_dirigida.items():
        for vecino, peso in vecinos:
            if comunidades[nodo] != comunidades[vecino]:
                continue  # la arista sale de la comunidad: no es interna

            if nodo < vecino:
                interno_por_comunidad[comunidades[nodo]] += peso
            elif nodo == vecino:
                # Un auto-loop suma dos veces al grado; para la parte interna
                # se cuenta una sola vez.
                interno_por_comunidad[comunidades[nodo]] += peso / 2.0

    # Paso 5: aplicar la fórmula para cada comunidad.
    q = 0.0
    for comunidad, grado_total in grado_por_comunidad.items():
        interno = interno_por_comunidad.get(comunidad, 0.0)
        parte_interna = interno / peso_total
        parte_esperada = (grado_total / (2.0 * peso_total)) ** 2
        q += parte_interna - parte_esperada

    return q


def louvain(
    adj_no_dirigida: Adyacencia,
    semilla: int = 42,
    max_pasadas: int = 20,
) -> Comunidades:
    """Detecta comunidades maximizando la modularidad.

    Es la fase principal de Louvain:

    - Cada nodo empieza solo en su comunidad.
    - En cada pasada, se prueba mover cada nodo a la comunidad de sus vecinos.
    - Se acepta el movimiento solo si Q aumenta.
    - Se termina cuando una pasada completa no cambia nada.

    Parámetros:
        adj_no_dirigida: grafo no dirigido.
        semilla: semilla para que el resultado sea reproducible.
        max_pasadas: máximo de pasadas completas.

    Retorna:
        {nodo: id_de_comunidad}.
    """
    # random.Random(semilla) crea un generador propio. Así no cambiamos el
    # generador global de Python y el resultado es reproducible.
    generador = random.Random(semilla)

    nodos = list(adj_no_dirigida.keys())

    # Al inicio, cada nodo está en su propia comunidad.
    comunidades: Comunidades = {}
    for identificador, nodo in enumerate(nodos):
        comunidades[nodo] = identificador

    for numero_pasada in range(max_pasadas):
        hubo_cambio = False

        # Orden aleatorio para no favorecer siempre a los mismos nodos.
        generador.shuffle(nodos)

        for nodo in nodos:
            comunidad_actual = comunidades[nodo]
            mejor_comunidad = comunidad_actual
            mejor_q = modularidad(adj_no_dirigida, comunidades)

            # Comunidades de los vecinos. Usamos un set para no probar dos
            # veces la misma comunidad.
            comunidades_vecinas: Set[int] = set()
            for vecino, _ in adj_no_dirigida.get(nodo, []):
                comunidades_vecinas.add(comunidades[vecino])

            # Probamos cada comunidad vecina (en orden fijo para que sea
            # reproducible).
            for comunidad_vecina in sorted(comunidades_vecinas):
                if comunidad_vecina == comunidad_actual:
                    continue

                # Mover temporalmente el nodo.
                comunidades[nodo] = comunidad_vecina
                q_con_movimiento = modularidad(adj_no_dirigida, comunidades)

                if q_con_movimiento > mejor_q:
                    mejor_q = q_con_movimiento
                    mejor_comunidad = comunidad_vecina

                # Deshacer el movimiento antes de probar el siguiente.
                comunidades[nodo] = comunidad_actual

            # Si encontramos una comunidad mejor, dejamos el nodo allí.
            if mejor_comunidad != comunidad_actual:
                comunidades[nodo] = mejor_comunidad
                hubo_cambio = True

        # Si nadie se movió, ya no tiene sentido seguir.
        if not hubo_cambio:
            break

    return comunidades


def resumen_comunidades(
    comunidades: Comunidades,
    etiquetas: Optional[Dict[str, Dict[str, str]]] = None,
) -> Dict[int, List[str]]:
    """Agrupa los nodos por comunidad y devuelve nombres legibles.

    Parámetros:
        comunidades: {nodo: id_de_comunidad}.
        etiquetas: opcional, {dirección: {"nombre": ...}}.

    Retorna:
        {id_de_comunidad: [nombres de sus nodos]}.
    """
    grupos: Dict[int, List[str]] = defaultdict(list)

    for nodo, comunidad in comunidades.items():
        nombre = nodo
        if etiquetas is not None and nodo in etiquetas:
            nombre = etiquetas[nodo].get("nombre", nodo)
        grupos[comunidad].append(nombre)

    return dict(grupos)


def renumerar_comunidades(comunidades: Comunidades) -> Comunidades:
    """Cambia los IDs de comunidad por 0, 1, 2, ... en orden de aparición.

    Louvain devuelve IDs que son el índice original de un nodo (por ejemplo,
    300 o 692). Eso es correcto, pero para leer los resultados es más cómodo
    que las comunidades se llamen 0, 1, 2, ...

    No cambia la partición: solo cambia el nombre de cada grupo.
    """
    mapa_de_ids: Dict[int, int] = {}
    comunidades_nuevas: Comunidades = {}

    for nodo, id_viejo in comunidades.items():
        if id_viejo not in mapa_de_ids:
            mapa_de_ids[id_viejo] = len(mapa_de_ids)
        comunidades_nuevas[nodo] = mapa_de_ids[id_viejo]

    return comunidades_nuevas


def desde_aristas(aristas: List[Tuple[str, str, float]]) -> Adyacencia:
    """Construye el grafo no dirigido a partir de la lista compartida de aristas.

    La lista `grafo.aristas` viene de la carga única del dataset. Cada módulo
    recibe esa lista y construye su propia estructura; así no depende de la
    estructura de otro módulo.

    Si hay transferencias en ambos sentidos, sus pesos se suman.
    """
    # Primero construimos el grafo dirigido tal como viene en las aristas.
    adj_dirigida: Adyacencia = {}

    for origen, destino, peso in aristas:
        if origen not in adj_dirigida:
            adj_dirigida[origen] = []
        adj_dirigida[origen].append((destino, float(peso)))

    # Después lo convertimos a no dirigido.
    return simetrizar(adj_dirigida)


def louvain_desde_aristas(
    aristas: List[Tuple[str, str, float]],
    semilla: int = 42,
    max_pasadas: int = 20,
) -> Comunidades:
    """Atajo: construye el grafo no dirigido y ejecuta Louvain.

    Es la función que usa el notebook. Recibe directamente `grafo.aristas`.
    """
    adj_no_dirigida = desde_aristas(aristas)
    return louvain(
        adj_no_dirigida,
        semilla=semilla,
        max_pasadas=max_pasadas,
    )


# ----------------------------------------------------------------------
# Posibles mejoras (para cuando el proyecto crezca)
# ----------------------------------------------------------------------
# 1. Calcular el cambio de modularidad ΔQ con una fórmula incremental, en
#    vez de recalcular Q completo en cada prueba. Eso hace el algoritmo mucho
#    más rápido en grafos grandes.
# 2. Agregar la segunda fase de Louvain: convertir cada comunidad en un
#    super-nodo y repetir el proceso. Es la versión completa del paper.
# 3. Agregar el parámetro de resolución γ, que permite encontrar comunidades
#    más grandes o más pequeñas.
# 4. Probar varias semillas y quedarse con la partición de mayor Q.
# 5. Comparar con Label Propagation y con `python-louvain` usando la misma
#    muestra y las mismas etiquetas de exchanges.
# 6. Para grafos de millones de aristas, usar arreglos/CSR en vez de
#    diccionarios de Python.
