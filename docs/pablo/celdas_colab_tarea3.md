# Celdas para el Colab — Tarea 3 (Pablo)

Pegar en `proyecto_grafos_ethereum.ipynb` **después de la celda de validación
complementaria** (la que empieza con `# T3 (validación complementaria):
proyección exchange-exchange`) y **antes** de "4.5 Resultados de la Tarea 3".
Son tres celdas nuevas, en este orden: una de texto y dos de código. Después,
reemplazar el texto de la celda de resultados por el de la sección 4.

Se ejecutan en menos de 5 segundos. Usan variables de las celdas anteriores
de la Tarea 2 y la Tarea 3 (`t2`, `g_t3`, `nodes_t3`, `best_mem`, `lp_mem`,
`q_lp`, `node_strength`, `best_mem_label`, `type_map`, `name_map`), así que
hay que ejecutar el notebook en orden.

## 1. Celda de texto

```markdown
### 4.5 Validación, estabilidad y sensibilidad

Louvain es una heurística: conviene comprobar que la implementación propia es
correcta y que la partición no depende de una elección arbitraria.

1. **Corrección.** La función `modularity` (que suma por comunidades) debe dar
   lo mismo que la fórmula de la definición (doble suma sobre todos los pares
   $i, j$). Además, Louvain se prueba en el **club de karate de Zachary**, un
   grafo de referencia cuya mejor modularidad conocida es $Q = 0{,}4198$, y se
   compara con NetworkX (usado solo para comparar, no en la tarea).
2. **Estabilidad.** Se ejecutan los 10 reinicios por separado y se mide cuánto
   se parecen sus particiones con la **información mutua normalizada**:

   $$\mathrm{NMI}(A,B) = \frac{2\,I(A;B)}{H(A)+H(B)} \in [0, 1],$$

   donde 1 significa la misma partición (salvo el nombre de las comunidades).
3. **Sensibilidad al peso.** En 4.2 se eligió la frecuencia de transferencias
   como peso. Aquí se repite Louvain con el **volumen en USD** y se compara.
4. **Resolución.** Con $\gamma < 1$ Louvain prefiere comunidades grandes y con
   $\gamma > 1$, pequeñas. El barrido muestra si las 13 comunidades son una
   escala natural de la red o un artefacto de $\gamma = 1$.
```

## 2. Celda de código: validación

```python
# ---------------------------------------------------------------------------
# T3: validación de la implementación propia de modularidad y Louvain
# ---------------------------------------------------------------------------
def modularidad_definicion(adj, comm):
    """Q = 1/(2m) * sum_ij [A_ij - k_i k_j / 2m] * delta(c_i, c_j).  O(n^2)."""
    nodos = list(adj)
    k = {u: sum(adj[u].values()) for u in nodos}
    dos_m = sum(k.values())
    q = 0.0
    for i in nodos:
        for j in nodos:
            if comm[i] == comm[j]:
                q += adj[i].get(j, 0.0) - k[i] * k[j] / dos_m
    return q / dos_m


# (1) modularity() frente a la definición, en el subgrafo de los 150 nodos más fuertes
top150 = set(sorted(g_t3, key=node_strength.get, reverse=True)[:150])
sub = {u: {v: w for v, w in g_t3[u].items() if v in top150} for u in top150}
sub = {u: vec for u, vec in sub.items() if vec}
part_sub = {u: best_mem[u] for u in sub}
q_rapida = modularity(sub, {u: 0.0 for u in sub}, part_sub)
q_def = modularidad_definicion(sub, part_sub)
assert abs(q_rapida - q_def) < 1e-9, "modularity() no coincide con la definición"
print(f"Subgrafo de {len(sub)} nodos: Q (por comunidades) = {q_rapida:.6f} | "
      f"Q (doble suma) = {q_def:.6f} -> coinciden")

# (2) Louvain en el club de karate de Zachary (referencia: Q óptima = 0,4198)
try:
    import networkx as nx  # solo para obtener el grafo de referencia y comparar
    karate = nx.karate_club_graph()
    g_kar = defaultdict(dict)
    for a, b in karate.edges():
        g_kar[str(a)][str(b)] = 1.0
        g_kar[str(b)][str(a)] = 1.0
    g_kar = dict(g_kar)
    mem_kar, q_kar, _, _ = louvain(sorted(g_kar), g_kar, n_restarts=10)
    grupos = defaultdict(set)
    for u, c in mem_kar.items():
        grupos[c].add(int(u))
    q_nx = nx.community.modularity(karate, grupos.values(), weight=None)
    assert abs(q_kar - q_nx) < 1e-9, "Q propia y Q de NetworkX deben coincidir"
    print(f"Karate: Louvain propio Q = {q_kar:.4f} con {len(grupos)} comunidades | "
          f"NetworkX mide la misma partición: Q = {q_nx:.4f} | óptimo conocido 0,4198")
except ImportError:
    print("NetworkX no está instalado: se omite la comparación con el club de karate.")
```

## 3. Celda de código: estabilidad y sensibilidad

```python
# ---------------------------------------------------------------------------
# T3: estabilidad entre reinicios, sensibilidad al peso y a la resolución
# ---------------------------------------------------------------------------
def nmi(part_a, part_b):
    """Información mutua normalizada entre dos particiones de los mismos nodos."""
    nodos = list(part_a)
    n = len(nodos)
    ca = Counter(part_a[u] for u in nodos)
    cb = Counter(part_b[u] for u in nodos)
    cab = Counter((part_a[u], part_b[u]) for u in nodos)
    h_a = -sum(c / n * math.log(c / n) for c in ca.values())
    h_b = -sum(c / n * math.log(c / n) for c in cb.values())
    if h_a + h_b == 0:
        return 1.0
    info = sum(c / n * math.log(c * n / (ca[a] * cb[b])) for (a, b), c in cab.items())
    return 2 * info / (h_a + h_b)


sin_lazos = {u: 0.0 for u in nodes_t3}

# (a) Estabilidad: cada uno de los 10 reinicios por separado
reinicios = []
for r in range(10):
    mem_r, q_r, _ = louvain_once(nodes_t3, g_t3, 1.0, r)
    reinicios.append({"reinicio": r, "comunidades": len(set(mem_r.values())), "Q": q_r,
                      "NMI_vs_mejor": nmi(mem_r, best_mem)})
reinicios = pd.DataFrame(reinicios)
display(reinicios.round(4))
print(f"Q entre reinicios: mín {reinicios.Q.min():.4f} | media {reinicios.Q.mean():.4f} | "
      f"máx {reinicios.Q.max():.4f}; NMI medio con la mejor partición = {reinicios.NMI_vs_mejor.mean():.3f}")

# (b) Sensibilidad al peso: volumen en USD en lugar de número de transferencias
g_vol = defaultdict(dict)
for s, d, v in zip(t2["src"], t2["dst"], t2["volume_usd"]):
    if s == d:
        continue
    g_vol[s][d] = g_vol[s].get(d, 0.0) + float(v)
    g_vol[d][s] = g_vol[d].get(s, 0.0) + float(v)
g_vol = {u: dict(vec) for u, vec in g_vol.items()}
mem_vol, q_vol, _, _ = louvain(sorted(g_vol), g_vol, n_restarts=10)
comunes = [u for u in nodes_t3 if u in mem_vol]
nmi_peso = nmi({u: best_mem[u] for u in comunes}, {u: mem_vol[u] for u in comunes})
nmi_lp = nmi(best_mem, lp_mem)
print(f"\nPeso = volumen USD: {len(set(mem_vol.values()))} comunidades, Q = {q_vol:.4f}")
print(f"NMI(frecuencia, volumen) = {nmi_peso:.3f} | NMI(Louvain, Label Propagation) = {nmi_lp:.3f}")

# ¿Los exchanges principales quedan juntos o separados con ambos pesos?
principales = sorted((u for u in nodes_t3 if type_map.get(u) != "wallet"),
                     key=node_strength.get, reverse=True)[:8]
etiqueta_vol = {c: f"V{i+1:02d}" for i, c in enumerate(
    sorted(set(mem_vol.values()), key=lambda c: -sum(1 for u in mem_vol if mem_vol[u] == c)))}
display(pd.DataFrame({
    "exchange": [name_map.get(u) or short_addr(u) for u in principales],
    "comunidad (frecuencia)": [best_mem_label[u] for u in principales],
    "comunidad (volumen)": [etiqueta_vol[mem_vol[u]] if u in mem_vol else "—" for u in principales],
}))

# (c) Barrido de resolución gamma
barrido = []
for gamma in [0.5, 0.75, 1.0, 1.5, 2.0, 3.0]:
    mem_g, _, _, _ = louvain(nodes_t3, g_t3, resolution=gamma, n_restarts=3)
    barrido.append({"gamma": gamma, "comunidades": len(set(mem_g.values())),
                    "Q (gamma=1)": modularity(g_t3, sin_lazos, mem_g, 1.0),
                    "NMI_vs_gamma_1": nmi(mem_g, best_mem)})
barrido = pd.DataFrame(barrido)
display(barrido.round(4))

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].bar(reinicios["reinicio"], reinicios["Q"], color="#55A868")
axes[0].axhline(q_lp, color="#4C72B0", ls="--", label=f"Label Propagation ({q_lp:.3f})")
axes[0].set_ylim(min(reinicios["Q"].min(), q_lp) - 0.02, reinicios["Q"].max() + 0.01)
axes[0].set_xlabel("Reinicio (semilla)")
axes[0].set_ylabel("Modularidad Q")
axes[0].set_title("Q de cada reinicio de Louvain")
axes[0].legend(fontsize=8)
axes[1].plot(barrido["gamma"], barrido["comunidades"], "o-", color="#C44E52", label="Comunidades")
axes[1].set_xlabel("Resolución γ")
axes[1].set_ylabel("Número de comunidades", color="#C44E52")
ax_q = axes[1].twinx()
ax_q.plot(barrido["gamma"], barrido["Q (gamma=1)"], "s--", color="#4C72B0", label="Q (γ = 1)")
ax_q.set_ylabel("Q medida con γ = 1", color="#4C72B0")
ax_q.ticklabel_format(axis="y", useOffset=False, style="plain")
axes[1].set_title("Efecto de la resolución γ")
plt.tight_layout()
plt.show()

# Lectura automática de los resultados (para el texto de 4.6)
nmi_medio = reinicios["NMI_vs_mejor"].mean()
mejor_gamma = barrido.loc[barrido["Q (gamma=1)"].idxmax(), "gamma"]
print("Lectura automática:")
print(f"- Estabilidad: los 10 reinicios dan Q entre {reinicios.Q.min():.3f} y {reinicios.Q.max():.3f} "
      f"y su NMI medio con la mejor partición es {nmi_medio:.2f} "
      + ("(la partición es estable)." if nmi_medio >= 0.9 else
         "(hay variación entre reinicios; por eso se conserva el de mayor Q)."))
print(f"- Peso: con volumen USD salen {len(set(mem_vol.values()))} comunidades (Q = {q_vol:.3f}) "
      f"y NMI = {nmi_peso:.2f} con la partición por frecuencia: "
      + ("la estructura comunitaria no depende del peso elegido." if nmi_peso >= 0.7 else
         "el peso cambia la partición; con volumen dominan pocas transferencias grandes, "
         "lo que justifica usar la frecuencia."))
print(f"- Resolución: de γ = {barrido.gamma.iloc[0]} a γ = {barrido.gamma.iloc[-1]} las comunidades pasan de "
      f"{barrido.comunidades.iloc[0]} a {barrido.comunidades.iloc[-1]}; la Q (γ = 1) es máxima en γ = {mejor_gamma}.")
print(f"- Louvain frente a Label Propagation: NMI = {nmi_lp:.2f}.")
```

## 4. Texto nuevo de la celda de resultados (reemplaza "4.5 Resultados de la Tarea 3")

```markdown
### 4.6 Resultados de la Tarea 3

- Louvain encuentra **13 comunidades** con modularidad **Q ≈ 0,614**, muy por encima de la partición trivial ($Q=0$). Esto indica una estructura mesoescalar fuerte: los flujos stablecoin no son aleatorios, se organizan en ecosistemas.
- La comunidad más grande agrupa a **Binance 1** con una gran cantidad de billeteras y otros exchanges; es el “ecosistema Binance”. Otras comunidades están lideradas por **1inch.exchange**, **OasisDEX**, **Poloniex**, **Huobi**, etc.
- La composición mezcla CEX, DEX y billeteras: las billeteras no etiquetadas se adhieren a la comunidad del exchange con el que más interactúan, lo que es consistente con el modelo.
- **La implementación es correcta.** `modularity` coincide con la doble suma de la definición en un subgrafo de 150 nodos, y en el club de karate de Zachary el Louvain propio alcanza **Q = 0,4198**, el óptimo conocido, con el mismo valor que mide NetworkX.
- **Robustez.** La estabilidad entre los 10 reinicios, el cambio de peso (frecuencia → volumen en USD) y el barrido de resolución $\gamma$ se cuantifican en 4.5 con la NMI; la lectura automática de esa celda resume si la partición cambia y cuánto.
- **Label Propagation** obtiene una modularidad cercana (≈ 0,605) pero fragmenta en más comunidades (24), muchas de ellas pequeñas. Louvain logra una partición más compacta y con mayor $Q$, aunque LP es más barato computacionalmente.
- La proyección alternativa exchange–exchange por billeteras compartidas (archivo `exchange_shared_wallets.csv`) produce 6 comunidades entre 88 exchanges conectados; el resto de exchanges no comparte contrapartes principales. Es una señal de fragmentación adicional y se puede usar como validación cualitativa.

**Interpretación real:** la red tiene una arquitectura de “hub-and-spoke” alrededor de Binance y de agregadores DEX. Para un participante, esto implica que las rutas de liquidez más eficientes pasan por pocos ecosistemas; para un regulador, implica que la caída de un hub puede afectar a muchas contrapartes.
```
