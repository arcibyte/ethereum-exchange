# Guía de lectura — Tarea 1: Bellman-Ford

**Responsable:** Pablo Álvarez
**Código:** `src/bellman_ford.py`
**Pruebas:** `tests/test_bellman_ford.py`

## 1. ¿Qué pregunta responde?

¿Cuál es el **camino más barato** entre dos direcciones de la red?

El costo de un camino es la **suma de los pesos** de sus aristas. En nuestro
grafo, el peso es la cantidad transferida, así que "más barato" significa
"menor cantidad acumulada".

## 2. Idea intuitiva

Imagina que quieres ir de tu casa a la universidad y tienes un mapa con el
costo de cada tramo. Bellman-Ford hace esto:

1. Supone que llegar a todo cuesta "infinito", menos al origen, que cuesta 0.
2. Repite varias veces: por cada tramo `u -> v` con costo `w`, si
   `distancia[u] + w` es menor que `distancia[v]`, actualiza `distancia[v]`.
3. Al terminar, `distancia[v]` es el costo mínimo real.

Ese paso de "si mejora, actualizo" se llama **relajar** la arista.

## 3. Ejemplo a mano

```
A -> B (2)
A -> C (5)
B -> C (1)
```

- Inicio: `A=0`, `B=inf`, `C=inf`.
- Relajo `A->B`: `B = 0 + 2 = 2`.
- Relajo `A->C`: `C = 0 + 5 = 5`.
- Relajo `B->C`: `C = min(5, 2 + 1) = 3`.

Resultado: `A=0`, `B=2`, `C=3`, con camino `A -> B -> C`.

## 4. ¿Por qué se repite |V|-1 veces?

Un camino mínimo simple no repite nodos, así que tiene como máximo `|V|-1`
aristas. En cada pasada se "descubre" al menos una arista más del camino, por
eso con `|V|-1` pasadas alcanza.

## 5. Complejidad

`O(|V| * |E|)`: se recorren todas las aristas en cada una de las `|V|-1`
pasadas.

## 6. ¿Por qué Bellman-Ford y no Dijkstra?

- El proyecto **prohíbe Dijkstra**.
- Bellman-Ford además detecta **ciclos de peso negativo** (Dijkstra no).
- Es más fácil de entender: solo compara y actualiza.

## 7. Qué debes poder explicar en el video

- Qué significa "relajar" una arista.
- Por qué se repite `|V|-1` veces.
- Qué pasa con un nodo **inalcanzable** (queda en `inf`).
- Cómo se reconstruye el camino con el diccionario de **predecesores**.
- Su complejidad y por qué no usamos Dijkstra.
