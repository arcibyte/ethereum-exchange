# Guion del video — segmento de Emerson Ballesteros

Dos bloques:
1. **Tarea 3 (comunidades):** minuto 5:00 – 6:30 (1 minuto y medio).
2. **Conclusiones:** minuto 8:00 – 9:00 (1 minuto).

Escribí el texto como se va a decir, en primera persona y con frases cortas.

---

## Bloque 1 — Tarea 3: comunidades (5:00 – 6:30)

**Apertura (15 s):**

> Hola, yo soy Emerson y me encargué de la tercera tarea: encontrar
> comunidades en la red.

**El problema (20 s):**

> La pregunta es: ¿qué direcciones interactúan mucho entre sí? Porque en
> Ethereum los exchanges y los DEX no trabajan solos: forman ecosistemas.
> Uniswap, Curve y Aave, por ejemplo, se usan mucho entre ellos, y lo mismo
> pasa con Binance y Coinbase.

**La matemática (20 s):**

> Para medir qué tan bueno es un agrupamiento usamos la modularidad Q. En
> palabras simples: Q compara cuántas aristas quedan *dentro* de los grupos
> contra las que esperaríamos si el grafo fuera aleatorio. Si Q es mayor a
> 0.3, la estructura es clara.

**El algoritmo (20 s):**

> Implementamos Louvain. La idea es sencilla: cada nodo empieza solo, y vamos
> moviendo cada nodo al grupo del vecino que más aumente Q, hasta que ya no
> se pueda mejorar. Lo programamos en Python puro, sin librerías de grafos.

**Resultado (15 s):**

> En nuestro ejemplo, Louvain encontró dos comunidades con una Q de 0.69:
> por un lado el ecosistema de los DEX y por el otro el de los exchanges.
> Justo lo que esperábamos.

---

## Bloque 2 — Conclusiones (8:00 – 9:00)

**Resumen (30 s):**

> Para cerrar, ¿qué aprendimos? Que un mismo dataset se puede atacar con
> varios algoritmos de grafos, y cada uno responde una pregunta distinta.

> Bellman-Ford encuentra el camino más barato sin usar Dijkstra. PageRank
> muestra qué nodos son los más importantes. Louvain separa la red en
> comunidades. Y Kruskal, con Union-Find, encuentra la red mínima que
> conecta a todos.

**Mensaje final (30 s):**

> Lo más valioso no fue memorizar los algoritmos, sino entender qué
> estructura de datos usa cada uno y por qué funciona. Eso es lo que nos
> llevamos del proyecto. Muchas gracias.

---

## Consejos para grabar

- Hablar despacio: el texto de cada bloque cabe en el tiempo indicado.
- Apoyarse en la gráfica de comunidades (la barra de tamaños del notebook).
- Tener a mano la tabla de la Tarea 3 para señalar el resultado.
