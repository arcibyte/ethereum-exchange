# Muestra conectada para los algoritmos

Esta carpeta contiene la muestra que usa el notebook en la Sección 1:

| Archivo | Descripción |
|---|---|
| `transferencias_2k.csv` | ~2.258 transferencias reales de USDC entre ~1.554 direcciones |
| `etiquetas.csv` | Nombres de los 23 exchanges que aparecen en la muestra |

## Cómo se generó

Se tomó una muestra aleatoria reproducible (`semilla=42`) del dataset de
transferencias, se descartaron direcciones inválidas y se conservó la
**componente conexa más grande**. El resultado pesa ~200 KB y corre en Colab
en pocos segundos.

La muestra actual son transferencias de **USDC** (token real de Ethereum).
El campo `value` está en unidades mínimas del token: `1 USDC = 1.000.000`.
Cuando esté disponible el Parquet completo de los 28 tokens, se puede
regenerar con el mismo script.

## Cómo regenerarla

Cuando esté disponible el Parquet completo:

```bash
python scripts/generar_muestra.py \
    --entrada data/procesado/transferencias.parquet \
    --salida data/muestra/transferencias_2k.csv \
    --etiquetas data/labels/exchange_labels.csv \
    --salida-etiquetas data/muestra/etiquetas.csv \
    --objetivo 2000 --semilla 42
```

El detalle del pipeline está en [`docs/DATASET.md`](../../docs/DATASET.md).
