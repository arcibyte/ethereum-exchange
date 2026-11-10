# Conclusiones del proyecto

**Responsable:** Emerson Ballesteros

---

A partir del análisis de la red de transferencias de tokens Ethereum,
llegamos a las siguientes conclusiones:

## 1. Un mismo dataset admite varias preguntas

No existe un único algoritmo "correcto" para una red. Cada tarea respondió
una pregunta distinta sobre el mismo grafo:

- **Bellman-Ford** → ¿cuál es el camino más barato?
- **PageRank** → ¿qué nodos son los más importantes?
- **Louvain** → ¿en qué grupos se organiza la red?
- **Kruskal** → ¿cuál es la red mínima que conecta a todos?

## 2. Las estructuras de datos importan

- La **lista de adyacencia** permite recorrer el grafo con diccionarios y
  listas, sin librerías externas.
- **Union-Find** (conjuntos disjuntos) es la clave para detectar ciclos en
  Kruskal.
- Los **diccionarios y conjuntos** de Python hacen que el código sea corto y
  legible.

Entender qué estructura usa cada algoritmo es más valioso que memorizar el
algoritmo.

## 3. La red no es un solo bloque

Louvain encontró dos comunidades claras (ecosistema DEX y ecosistema de
exchanges) separadas por un puente débil, con una modularidad $Q = 0.696$.
Esto confirma que los actores de Ethereum se agrupan en ecosistemas, no
interactúan de forma uniforme.

## 4. Sin Dijkstra también se puede

Cumplimos la restricción del curso usando **Bellman-Ford** (caminos) y
**Kruskal** (árbol de expansión), ambos con estructuras de datos accesibles
para tercer semestre.

## 5. Qué queda por explorar

- Correr los algoritmos sobre el dataset completo (~38 millones de
  transferencias).
- Comparar Louvain con otros métodos (Girvan-Newman, propagación de
  etiquetas).
- Aplicar Louvain en varias escalas para encontrar sub-comunidades.

---

**En una frase:** lo importante no fue el tamaño del dataset ni la cantidad
de algoritmos, sino entender qué estructura de datos usa cada uno y por qué
funciona.
