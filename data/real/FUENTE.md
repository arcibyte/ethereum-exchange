# Datos reales incluidos en el repositorio

Estos archivos son **reales** y pequeños, así que el notebook corre sin
descargar el dataset completo.

| Archivo | Qué es | Origen |
|---------|--------|--------|
| `exchange_labels.csv` | 296 direcciones de exchanges (247 `cex`, 49 `dex`) con su nombre. Columnas: `type, address, name`. | `data/tokens/exchangeLabels.csv` de [friedhelmvictor/alphacore](https://github.com/friedhelmvictor/alphacore), las mismas etiquetas que publica [SNAP](https://snap.stanford.edu/data/ethereum-exchanges.html). |
| `softchaincoin.csv` | Red real del token SoftChainCoin: 278 transferencias entre 197 direcciones. Es el ejemplo pequeño que usan los autores del dataset. | `data/sccTransfers.csv` del mismo repositorio, con las columnas renombradas al formato del dataset (`token_address, from_address, to_address, value, block_number`). SoftChainCoin **no** es uno de los 28 tokens del dataset. |

Ambos archivos vienen de un repositorio con licencia MIT
(Copyright (c) 2021 Friedhelm Victor).

Cita del dataset:

> F. Victor, C. G. Akcora, Y. R. Gel, M. Kantarcioglu. *AlphaCore: Data Depth
> based Core Decomposition*. KDD 2021, pp. 1625–1633.
> https://doi.org/10.1145/3447548.3467322
