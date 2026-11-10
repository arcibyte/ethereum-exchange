# Guía de lectura — Tarea 3: Comunidades (Louvain)

**Responsable:** Emerson Ballesteros
**Código:** `src/comunidades.py`
**Pruebas:** `tests/test_comunidades.py`
**Reporte completo:** `docs/emerson/tarea3_louvain.md`

## 1. ¿Qué pregunta responde?

¿Qué **grupos de nodos** interactúan mucho entre sí y poco con el resto?

En una red de transferencias, esos grupos suelen coincidir con ecosistemas:
por ejemplo, el conjunto de contratos DEX frente al de exchanges.

## 2. Idea intuitiva

Cada nodo empieza en su propia comunidad. Luego, para cada nodo, probamos
moverlo a la comunidad de cada vecino y nos quedamos con el movimiento que más
**aumente la modularidad Q**. Repetimos hasta que ningún movimiento mejore.

## 3. Modularidad Q

```
Q = (1/2m) * suma_{i,j} [ A_ij - k_i*k_j/(2m) ] * delta(c_i, c_j)
```

- `A_ij`: peso entre `i` y `j`.
- `k_i`: suma de pesos del nodo `i`.
- `m`: suma total de pesos.
- `delta`: 1 si están en la misma comunidad, 0 si no.

Valores de `Q` por encima de `0.3` indican una buena estructura de comunidades.

## 4. Ejemplo a mano

Dos triángulos unidos por una arista muy débil:

```
A - B       D - E
| X |       | X |
C - - - - - F      (peso 0.1)
```

Louvain deja `{A, B, C}` y `{D, E, F}` separados, porque unirlos bajaría `Q`.

## 5. Complejidad

Nuestra versión recalcula `Q` completa en cada intento para que sea fácil de
leer. Eso la hace más costosa que Louvain de producción, pero el grafo de
ejemplo es pequeño y el resultado es el mismo.

## 6. ¿Por qué Louvain y no Leiden?

- Louvain es más fácil de implementar y de explicar.
- Leiden es una mejora (garantiza comunidades bien conectadas) y se menciona
  como **trabajo futuro**.
- Para el tamaño de nuestro grafo, ambos dan resultados equivalentes.

## 7. Qué debes poder explicar en el video

- Qué es una comunidad y qué mide `Q`.
- Qué hace una "pasada" de Louvain.
- Por qué usamos el grafo **no dirigido** (simetrizado).
- Por qué el puente débil `USDC -> Binance` no une las comunidades.
- La diferencia conceptual con Leiden.
