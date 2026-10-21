# -*- coding: utf-8 -*-
"""
PREP_paquete_biblioteca.py · arma el .zip del experimento E31
=============================================================

QUE HACE
    Prepara `paquete_biblioteca.zip` para subirlo a Google Colab y lanzar el
    experimento de la biblioteca de sectores (E31).

POR QUE HAY QUE RECORTAR LOS DATOS
    Los tres ficheros de cuentas ocupan 132 MB, y subir eso a Colab es lento
    y se corta a menudo. Pero la mayor parte es texto repetido: `web_text`,
    `input_texto` e `input_completo` contienen practicamente lo mismo.

    Ademas el modelo solo lee los primeros 256 tokens de cada empresa, que
    son unos 1.200 caracteres. Todo lo que venga despues se descarta ANTES de
    entrar al modelo, tanto aqui como en el entrenamiento original.

    Asi que el paquete lleva:
      · una sola columna de texto, no cuatro
      · recortada a 2.500 caracteres, con margen sobre lo que el modelo usa

    NO SE PIERDE INFORMACION que el modelo fuera a utilizar. Queda declarado
    aqui para que conste.

COMO SE EJECUTA
    python scripts/PREP_paquete_biblioteca.py
"""

import json
import shutil
import tempfile
import zipfile
from pathlib import Path

import pandas as pd

VERSION_SCRIPT = "v1 · 01-10-2026"

RAIZ = Path(__file__).resolve().parent.parent
DERIVADO = RAIZ / "datos" / "02_derivado"
ZIP = RAIZ / "paquete_biblioteca.zip"

MAX_CARACTERES = 2500          # el modelo usa ~1.200; se deja margen
COLUMNAS = ["empresa", "sector", "input_completo"]

LEEME = """PAQUETE BIBLIOTECA · experimento E31
generado por PREP_paquete_biblioteca.py {version}

QUE ES ESTO
   El experimento que comprueba si el clasificador de sectores mejora cuando
   ve las descripciones de cada sector, en vez de deducirlas solo de los
   ejemplos.

COMO SE USA
   1. Abre A2_biblioteca_colab.ipynb en Google Colab
   2. Activa la GPU: Entorno de ejecucion -> Cambiar tipo -> GPU
   3. Sube ESTE fichero cuando el cuaderno te lo pida
   4. Sigue las celdas en orden

   Primero hay una prueba corta de diez minutos. Si sale bien, lanzas la
   tanda completa, que son unas dos horas.

QUE LLEVA DENTRO
{contenido}

SOBRE LOS DATOS
   Los ficheros de cuentas van RECORTADOS: una sola columna de texto en vez
   de cuatro, y cortada a {maxc} caracteres por empresa.

   El modelo solo lee los primeros 256 tokens, que son unos 1.200 caracteres,
   asi que no se pierde nada de lo que fuera a utilizar. Se recorta porque
   los ficheros completos ocupan 132 MB y subirlos a Colab es un suplicio.

QUE DEVUELVE
   a2_biblioteca.json con las cifras de las tres variantes. Descargalo al
   terminar: con eso se decide que hacer con A2.
"""


def main():
    print()
    print("=" * 74)
    print(f"PREP · paquete de la biblioteca  ·  {VERSION_SCRIPT}")
    print("=" * 74)
    print()

    tax = next((f for f in [RAIZ / "datos" / "taxonomia_completa (1).json",
                            RAIZ / "datos" / "taxonomia_completa.json"]
                if f.exists()), None)
    if tax is None:
        raise SystemExit("   No encuentro la taxonomía con descripciones en datos/")

    script = RAIZ / "scripts" / "F2_A2_E31_biblioteca_entrenamiento.py"
    if not script.exists():
        raise SystemExit(f"   Falta {script.name}")

    tmp = Path(tempfile.mkdtemp())
    incluidos = []

    # --- los datos, recortados ---------------------------------------------
    print("   Recortando los datos:")
    for p in ("train", "val", "test"):
        f = DERIVADO / f"cuentas_{p}.csv"
        d = pd.read_csv(f)
        antes = f.stat().st_size / 1e6
        cols = [c for c in COLUMNAS if c in d.columns]
        if "input_completo" not in cols:
            d["input_completo"] = ("Empresa: " + d.empresa.fillna("").astype(str)
                                   + " | Web: " + d.web_text.fillna("").astype(str))
            cols = ["empresa", "sector", "input_completo"]
        s = d[cols].copy()
        s["input_completo"] = s.input_completo.fillna("").astype(str).str[:MAX_CARACTERES]
        destino = tmp / f"cuentas_{p}.csv"
        s.to_csv(destino, index=False, encoding="utf-8")
        despues = destino.stat().st_size / 1e6
        print(f"      cuentas_{p:<6} {antes:>7.1f} MB  ->  {despues:>6.1f} MB"
              f"   ({len(s)} filas)")
        incluidos.append(f"cuentas_{p}.csv")

    # --- el script y la taxonomía ------------------------------------------
    shutil.copy2(script, tmp / script.name)
    incluidos.append(script.name)
    shutil.copy2(tax, tmp / "taxonomia_completa (1).json")
    incluidos.append("taxonomia_completa (1).json")

    tx = json.loads(tax.read_text(encoding="utf-8"))
    con_desc = sum(1 for v in tx.values()
                   if isinstance(v, dict) and v.get("descripcion"))
    print()
    print(f"   Biblioteca: {len(tx)} sectores, {con_desc} con descripción propia")

    # --- el léeme ------------------------------------------------------------
    (tmp / "LEEME.txt").write_text(
        LEEME.format(version=VERSION_SCRIPT, maxc=MAX_CARACTERES,
                     contenido="\n".join(f"   · {x}" for x in sorted(incluidos))),
        encoding="utf-8")
    incluidos.append("LEEME.txt")

    # --- el zip --------------------------------------------------------------
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for x in sorted(incluidos):
            z.write(tmp / x, x)
    shutil.rmtree(tmp, ignore_errors=True)

    print()
    print(f"   [ok] {ZIP.name}   {ZIP.stat().st_size/1e6:.1f} MB")
    print(f"   [ok] A2_biblioteca_colab.ipynb   el cuaderno")
    print()
    print("   Sube los dos a Colab: el cuaderno se abre y el zip se sube")
    print("   cuando la celda 2 te lo pida.")
    print()


if __name__ == "__main__":
    main()
