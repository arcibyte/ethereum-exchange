# Guía de lectura — Tarea 2: Centralidad y PageRank

**Responsable:** Jhon Arciniegas
**Código:** `src/centralidad.py`
**Pruebas:** `tests/test_centralidad.py`

## 1. ¿Qué pregunta responde?

¿Qué nodos son los **más importantes** dentro de la red?

No hay una sola respuesta: "importante" puede significar "tiene muchas
conexiones" o "lo apuntan nodos importantes". Por eso calculamos dos medidas.

## 2. Centralidad de grado

Cuenta las conexiones de cada nodo y las normaliza:

```
C(v) = grado(v) / (|V| - 1)
```

En un grafo dirigido sumamos grado de salida + grado de entrada. El nodo con
más conexiones tiene `C` cercano a 1.

**Limitación:** un nodo puede tener muchas conexiones y no ser realmente
influyente (por ejemplo, muchas transferencias pequeñas).

## 3. PageRank

La idea de Google: **un nodo es importante si lo apuntan nodos importantes**.

```
PR(v) = (1 - d)/N + d * suma_{u -> v} ( PR(u) / grado_salida(u) )
```

- `d` es el factor de amortiguación (`0.85`).
- Se calcula por **iteración de potencias**: se empieza con `1/N` para todos y
  se repite la fórmula hasta que los valores casi no cambian.

## 4. Ejemplo a mano

```
A -> B
A -> C
B -> C
C -> A
```

Al principio todos valen `1/3`. Como `A` recibe de `C` y `B`/`A` apuntan a `C`,
`C` empieza a ganar importancia. Tras varias iteraciones los valores se
estabilizan y suman 1.

## 5. Complejidad

Cada iteración recorre todas las aristas: `O(|E|)`. Con `k` iteraciones,
`O(k * |E|)`.

## 6. ¿Por qué estas medidas y no otras?

- **Grado** es la más simple y sirve de línea base.
- **PageRank** captura influencia indirecta (la importancia se propaga).
- Alternativas como *betweenness* miden "puentes", pero son más costosas y no
  eran necesarias para responder la pregunta.

## 7. Qué debes poder explicar en el video

- Diferencia entre grado y PageRank.
- Qué significa el factor de amortiguación `d`.
- Por qué PageRank suma aproximadamente 1.
- Qué es la iteración de potencias.
- Por qué un exchange puede salir con PageRank alto.
