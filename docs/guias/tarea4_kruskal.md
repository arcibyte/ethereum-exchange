# Guía de lectura — Tarea 4: MST (Kruskal + Union-Find)

**Responsable:** grupo
**Código:** `src/arbol_expansion.py`
**Pruebas:** `tests/test_arbol_expansion.py`

## 1. ¿Qué pregunta responde?

¿Cuál es la **red mínima** que conecta a todos los nodos con el menor costo
total posible?

Ese conjunto de aristas siempre forma un **árbol** (no tiene ciclos) y tiene
exactamente `|V| - 1` aristas.

## 2. Idea intuitiva (Kruskal)

1. Ordena todas las aristas de menor a mayor peso.
2. Recórrelas en ese orden.
3. Agrega una arista **solo si no forma un ciclo**.
4. Para cuando tengas `|V| - 1` aristas.

## 3. Union-Find

Es la estructura que detecta ciclos de forma rápida:

- `encontrar(x)`: devuelve el representante del conjunto de `x`.
- `unir(x, y)`: une los conjuntos y devuelve `False` si ya estaban unidos
  (es decir, agregar esa arista formaría un ciclo).

Usa **compresión de caminos** y **unión por rango** para ser casi constante
por operación.

## 4. Ejemplo a mano

```
A - B (1)
B - C (2)
A - C (3)
```

- Orden: `A-B(1)`, `B-C(2)`, `A-C(3)`.
- Agrego `A-B`: no hay ciclo.
- Agrego `B-C`: no hay ciclo.
- `A-C` formaría ciclo: se descarta.

MST = `{A-B, B-C}`, costo `3`.

## 5. Complejidad

Ordenar las aristas: `O(|E| log |E|)`. Las operaciones de Union-Find son casi
`O(1)` amortizado (con compresión y rango).

## 6. ¿Por qué Kruskal y no Prim?

- Kruskal se apoya en Union-Find, que es una estructura de datos clásica de la
  materia.
- Es más fácil de leer cuando el grafo se representa como lista de aristas.

## 7. Qué debes poder explicar en el video

- Qué es un árbol de expansión mínima.
- Por qué el MST tiene `|V| - 1` aristas.
- Cómo Union-Find detecta ciclos.
- Qué hacen la compresión de caminos y la unión por rango.
- Cómo convertimos las aristas dirigidas en no dirigidas.
