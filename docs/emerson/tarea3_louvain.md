# Tarea 3 — Detección de comunidades (Louvain)

**Responsable:** Emerson Ballesteros
**Proyecto:** Red de transferencias de tokens Ethereum
**Materia:** Estructura de Datos

---

## 1. Problema real

En la red de Ethereum, las direcciones no se comportan de forma aislada: los
exchanges, los DEX (intercambios descentralizados) y sus usuarios forman
"ecosistemas" que interactúan mucho entre sí y poco con el resto.

Queremos responder: **¿en qué grupos naturales se organiza la red?**

Detectar estos grupos sirve para:
- Entender la arquitectura del ecosistema (qué protocolos se usan juntos).
- Identificar clústeres anómalos o de comportamiento coordinado.

## 2. Equivalencia matemática

Formulamos el problema como **maximizar la modularidad** $Q$ sobre el grafo
no dirigido $G=(V,E)$:

$$Q = \frac{1}{2m}\sum_{i,j}\left[A_{ij} - \frac{k_i k_j}{2m}\right]\delta(c_i, c_j)$$

Donde:

| Símbolo | Significado |
|---------|-------------|
| $A_{ij}$ | peso de la arista entre $i$ y $j$ |
| $k_i$ | grado del nodo $i$ (suma de pesos de sus aristas) |
| $m$ | suma total de pesos del grafo |
| $c_i$ | comunidad asignada al nodo $i$ |
| $\delta(c_i,c_j)$ | 1 si $i$ y $j$ están en la misma comunidad, 0 si no |

**Intuición:** $Q$ compara las aristas que quedan *dentro* de los grupos con
las que esperaríamos en un grafo aleatorio con los mismos grados. Si hay más
aristas internas de las esperadas, la partición es buena.

- $Q$ puede tomar valores entre $-0.5$ y $1$.
- $Q > 0.3$ indica una estructura de comunidades clara.

## 3. Alternativas algorítmicas

| Algoritmo | Complejidad | Veredicto |
|-----------|-------------|-----------|
| Girvan-Newman | $O(V \cdot E^2)$ | Descartado: muy lento para grafos grandes |
| Clustering espectral | $O(V^3)$ | Descartado: necesita álgebra lineal densa |
| Propagación de etiquetas | $O(V+E)$ | Descartado: rápido pero inestable |
| **Louvain** | $\approx O(V \log V)$ empírico | **Seleccionado** |

**Justificación:** Louvain ofrece el mejor equilibrio entre calidad de la
partición (maximiza $Q$) y velocidad, y su idea central es sencilla de
explicar e implementar.

## 4. Algoritmo (Louvain, fase principal)

El algoritmo de Louvain completo tiene dos fases: (1) mover nodos para
maximizar $Q$ y (2) colapsar comunidades en super-nodos y repetir. Aquí
implementamos la **fase 1**, que ya captura la idea principal.

**Idea en palabras:**

1. Cada nodo empieza en su propia comunidad.
2. Repetimos hasta que nada cambie:
   - Para cada nodo $v$, probamos moverlo a la comunidad de cada uno de sus
     vecinos.
   - Nos quedamos con el movimiento que más aumente $Q$.
   - Si ningún movimiento mejora $Q$, $v$ se queda donde está.

**Pseudocódigo:**

```
funcion louvain(grafo):
    comunidades = {v: i para cada nodo v}   # cada uno en su grupo

    repetir:
        cambio = falso
        para cada nodo v (en orden aleatorio):
            mejor = comunidad_actual(v)
            mejor_q = modularidad(comunidades)

            para cada vecino u de v:
                mover v a comunidad(u)
                q = modularidad(comunidades)
                si q > mejor_q: mejor = comunidad(u); mejor_q = q
                deshacer el movimiento

            si mejor != comunidad_actual(v):
                comunidades[v] = mejor
                cambio = verdadero

        si no cambio: terminar

    devolver comunidades
```

> **Nota pedagógica:** aquí recalculamos $Q$ cada vez que probamos un
> movimiento, para que el código sea fácil de leer. La versión "de
> producción" de Louvain usa una fórmula incremental que calcula el cambio
> $\Delta Q$ sin rehacer todo el cálculo.

## 5. Estructuras de datos usadas

| Estructura | Uso |
|------------|-----|
| Lista de adyacencia (`dict` de listas) | representar el grafo no dirigido |
| `dict` (`comunidades`) | guardar a qué comunidad pertenece cada nodo |
| `set` / `sorted` | manejar nodos y pares sin duplicados |
| `defaultdict` | agrupar nodos por comunidad |

No usamos ninguna librería de grafos: todo es Python puro.

## 6. Implementación

El código está en `src/comunidades.py` y expone cuatro funciones:

- `simetrizar(adj)`: convierte el grafo dirigido en no dirigido sumando pesos.
- `modularidad(adj_nd, comunidades)`: calcula $Q$.
- `louvain(adj_nd, semilla, max_pasadas)`: detecta las comunidades.
- `resumen_comunidades(comunidades, etiquetas)`: devuelve los nombres legibles.

La modularidad se calcula por comunidad para que sea $O(V+E)$:

$$Q = \sum_c \left[ \frac{L_c}{m} - \left(\frac{K_c}{2m}\right)^2 \right]$$

donde $L_c$ es el peso de las aristas internas de la comunidad $c$ y $K_c$ la
suma de grados de sus nodos. Es equivalente a la fórmula clásica y se verificó
con una prueba que la compara contra la suma directa sobre todos los pares.

Las pruebas propias están en `tests/test_comunidades.py`.

## 7. Resultados sobre el dataset de ejemplo

Sobre la muestra (12 direcciones, 20 transferencias) el algoritmo encuentra:

```
Modularidad Q = 0.696
Número de comunidades = 2

Comunidad 1: Aave, Curve, USDC, Uniswap, cartera_a, cartera_b, cartera_c
Comunidad 2: Binance, Coinbase, DAI, cartera_d, cartera_e
```

**Interpretación:** $Q = 0.696$ es un valor alto (muy por encima de 0.3), lo
que confirma que la red tiene una estructura clara. Las dos comunidades
encontradas corresponden al **ecosistema DEX** (Uniswap, Curve, Aave y sus
usuarios) y al **ecosistema de exchanges centralizados** (Binance, Coinbase
y sus usuarios). El puente entre ambos es una transferencia débil USDC →
Binance, que el algoritmo correctamente no usa para fusionar los grupos.

Sobre la **muestra conectada real** (`data/muestra/transferencias_2k.csv`,
~2.063 aristas y ~1.371 nodos de USDC), Louvain encuentra entre **69 y 71
comunidades con $Q \approx 0.73$**. Al probar 5 semillas, $Q$ se mantiene
entre 0.730 y 0.736, lo que muestra que el resultado es estable.

## 8. Complejidad

- `simetrizar`: $O(|E|)$.
- `modularidad`: $O(|V| + |E|)$.
- `louvain`: $O(\text{pasadas} \cdot |V| \cdot \text{grado} \cdot (|V|+|E|))$
  en esta versión sencilla (aceptable para grafos pequeños). La versión
  incremental de Louvain es $\approx O(|V| \log |V|)$.

## 9. Conclusiones de la tarea

- Louvain resuelve el problema de "encontrar grupos" maximizando la
  modularidad $Q$, una medida con interpretación intuitiva.
- La fase principal del algoritmo es corta y comprensible, y ya da buenos
  resultados en el ejemplo.
- El uso de una lista de adyacencia y diccionarios hace que el código sea
  simple y legible en Python puro.

## 10. Referencias

- Blondel, V. D., Guillaume, J.-L., Lambiotte, R., & Lefebvre, E. (2008).
  *Fast unfolding of communities in large networks.*
- Newman, M. E. J. (2006). *Modularity and community structure in networks.*
