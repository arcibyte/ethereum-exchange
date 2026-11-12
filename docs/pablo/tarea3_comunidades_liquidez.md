# Tarea 3 — Comunidades de liquidez (Louvain)

**Responsable:** Juan Pablo Álvarez

Esta carpeta documenta la parte de Pablo en el notebook entregable
`proyecto_grafos_ethereum.ipynb` (Colab del equipo) y lo que se agregó al
repositorio para respaldarla. No modifica archivos de otros integrantes.

## Qué hay en el repositorio

| Archivo | Qué es |
|---|---|
| `src/comunidades_liquidez.py` | El código de la Tarea 3 del notebook (`modularity`, `louvain_once`, `louvain`, `label_propagation`, sin cambios de lógica) más funciones nuevas de validación: `modularidad_definicion`, `nmi`, `estabilidad_reinicios`, `barrido_resolucion`. Solo librería estándar. |
| `tests/test_comunidades_liquidez.py` | 10 pruebas: la modularidad coincide con la definición; Louvain alcanza Q = 0,4198 en el club de karate (igual que NetworkX); separa dos cliques; es reproducible con semilla; propiedades de la NMI; estabilidad y resolución. |
| `docs/pablo/celdas_colab_tarea3.md` | Las celdas nuevas para pegar en el Colab y el texto actualizado de los resultados. |

```bash
python -m pytest tests/test_comunidades_liquidez.py -v
```

## Qué se agregó al notebook (sección 4.5)

1. **Corrección:** `modularity` frente a la doble suma de la definición, y
   Louvain en el club de karate de Zachary (óptimo conocido Q = 0,4198).
2. **Estabilidad:** Q y NMI de cada uno de los 10 reinicios.
3. **Sensibilidad al peso:** Louvain con volumen en USD en lugar de
   frecuencia (lo prometía 4.2 y no estaba hecho).
4. **Resolución:** barrido de γ entre 0,5 y 3.

Esto deja la Tarea 3 al nivel de validación de las demás: T1 compara DSU con
BFS y Tarjan con fuerza bruta, y T4 compara Dinic con Edmonds-Karp.

## Qué explicar en el video

- **Problema:** ¿qué ecosistemas de liquidez existen entre exchanges y
  contrapartes? Grafo no dirigido, peso = número de transferencias.
- **Modularidad:** compara las aristas dentro de cada comunidad con las que
  habría por azar; Q = 0 si todo está en una sola comunidad.
- **Louvain en dos fases:** mover cada nodo a la comunidad vecina que más
  aumenta Q y luego juntar cada comunidad en un supernodo; repetir.
- **Resultado:** 13 comunidades, Q ≈ 0,614, organizadas alrededor de
  Binance, 1inch, OasisDEX, Poloniex y otros.
- **Por qué confiar:** el karate da el óptimo conocido, los reinicios dan la
  misma partición (NMI) y el resultado se compara con Label Propagation.
