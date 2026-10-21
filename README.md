# TFM — Sistema multi-agente para la automatización comercial B2B

Código del Trabajo Fin de Máster (Universidad Europea).

Este repositorio contiene los scripts del sistema multi-agente y de los
experimentos que sostienen las cifras de la memoria.

## Estructura

- **`scripts/`** — los 14 scripts del sistema: los dos circuitos (salida y
  recepción) y cada uno de los agentes.
- **`scripts_experimentos/`** — las pruebas que respaldan los resultados de la
  memoria (baselines, contrastes estadísticos, figuras, verificaciones, etc.).
- **`requirements.txt`** — librerías y versiones utilizadas.
- **`LEEME.txt`** — explicación detallada de qué hace cada script y cómo se
  organiza el conjunto.

## Nota sobre los datos

Los datos del CRM están seudonimizados y **no se incluyen** por
confidencialidad. Cada script indica, al ejecutarse sin los datos completos,
qué necesita y dónde está el resultado ya calculado.

## Correspondencia de numeración de los ficheros

Algunos nombres de fichero conservan el número de agente antiguo:

| En la memoria | En los ficheros |
|---------------|-----------------|
| A6            | `F6_A6_...`     |
| A7            | `F8_A8_...`     |
| A8            | `F9_A9_...`     |

Se renumeraron los agentes y no los ficheros, para no romper lo ya ejecutado.
