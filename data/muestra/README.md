# Muestra conectada para los algoritmos

Esta carpeta contiene la muestra que usan las Tareas 1–4:

| Archivo | Descripción |
|---|---|
| `transferencias_2k.csv` | ~2.063 transferencias reales de USDC entre ~1.371 direcciones |
| `etiquetas.csv` | Nombres de los 20 exchanges que aparecen en la muestra |

## Cómo se generó

Se filtró **USDC** (`0xa0b8...eb48`) del Parquet completo, se tomó una muestra
aleatoria reproducible (`semilla=42`), se descartaron direcciones inválidas y
se conservó la **componente conexa más grande**.

- `value` está normalizado a **USDC** (6 decimales): `1000.30` son 1.000,30
  USDC.
- El resultado pesa ~195 KB y corre en Colab en pocos segundos.
- Analizar un solo token evita mezclar unidades de tokens distintos.

El resto del dataset (28 tokens, 38,9 M de transferencias) se analiza en la
sección final del notebook con DuckDB.

## Cómo regenerarla

```bash
python scripts/generar_muestra.py \
    --entrada data/procesado/transferencias.parquet \
    --salida data/muestra/transferencias_2k.csv \
    --etiquetas data/real/exchange_labels.csv \
    --salida-etiquetas data/muestra/etiquetas.csv \
    --objetivo 2000 --filas 65000 --semilla 42 \
    --token 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48 --decimales 6
```

El detalle del pipeline está en [`docs/DATASET.md`](../../docs/DATASET.md).
