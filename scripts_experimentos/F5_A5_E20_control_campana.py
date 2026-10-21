"""
A5 · CONTROLES DE LA CAMPANA  ·  reproduce E20
===============================================
Recalcula las dos metricas que responden a la pregunta del experimento:

    ¿Personalizar automaticamente aporta algo frente a mandar el mismo
    correo a todo el mundo?

POR QUE EXISTE ESTE FICHERO
---------------------------
F5_A5_E20_campana.py genera los correos e imprime sus metricas, pero los CONTROLES
—el suelo de la personalizacion y la prueba de permutacion— se calcularon
aparte, de forma exploratoria, y no quedaron en ningun script. Sin ellos las
cifras de E20 no son recomprobables.

LAS DOS METRICAS, Y POR QUE HACEN FALTA LAS DOS
-----------------------------------------------
PERSONALIZACION
  Que parte del correo procede de la web de ESA empresa y no del brief, que es
  comun a todos. Se compara con dos referencias distintas:

    a) el correo GENERICO real que Empresa envia hoy, evaluado contra esas mismas
       webs. Dice CUANTO HAY QUE SUPERAR. No es cero: cualquier texto comparte
       lexico con cualquier web por azar.

    b) una PERMUTACION: el mismo correo evaluado contra la web de otra empresa.
       Dice si lo especifico es de esa empresa o simplemente vocabulario que
       encajaria con cualquiera.

  Son preguntas distintas. Superar (a) sin superar (b) significaria que el
  modelo escribe cosas concretas pero no las correctas.

REDUNDANCIA
  Cuanto se parecen los correos entre si. El generico tiene 1,000 por
  definicion: es literalmente el mismo para todas las empresas. Es la
  referencia natural y no hay que estimarla.

  Se calcula con Jaccard sobre terminos de contenido en lugar de embeddings
  para que el script corra sin GPU ni descargas. Mide solape de vocabulario,
  no de significado, lo cual es suficiente aqui: si dos correos comparten el
  80% de sus terminos, son el mismo correo.

SOBRE LOS UMBRALES
------------------
Este script no fija ninguno. Fue el error X9: poner un listo/no listo antes de
conocer el suelo de la metrica. Aqui se mide el suelo y se informa la distancia.

Uso (sin GPU):
    python scripts/F5_A5_E20_control_campana.py
    python scripts/F5_A5_E20_control_campana.py --fichero a5_campana_C01_sin_ejemplo.csv
"""

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

VERSION_SCRIPT = "v1 · 29-09-2026"

RAIZ = Path(__file__).resolve().parent.parent
DERIVADO = RAIZ / "datos" / "02_derivado"
RESULTADOS = RAIZ / "datos" / "03_resultados"
BRUTO = RAIZ / "datos" / "00_bruto"
sys.path.insert(0, str(Path(__file__).parent))
from F5_A5_E20_campana import leer_campana  # noqa: E402
from F5_A5_E19_generar_correos import terminos  # noqa: E402

# Lo registrado en E20, para detectar divergencias.
BITACORA = {
    "personalizacion": 5.06,
    "suelo_generico": 1.29,
    "nula_permutacion": 3.04,
    "z": 3.50,
    "redundancia": 0.486,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--campana", default="C01")
    ap.add_argument("--fichero", default="a5_campana_C01.csv")
    ap.add_argument("--permutaciones", type=int, default=2000)
    ap.add_argument("--semilla", type=int, default=42)
    a = ap.parse_args()
    rng = np.random.default_rng(a.semilla)

    print("=" * 74)
    print("A5 · CONTROLES DE LA CAMPANA")
    print(f"     {VERSION_SCRIPT}  ·  reproduce E20")
    print(f"     campana {a.campana}  ·  {a.fichero}")
    print("=" * 74)

    campana = leer_campana(a.campana)
    t_brief = terminos(campana["texto"])

    e = pd.read_csv(RESULTADOS / a.fichero)
    escritos = e[~e.se_abstiene].reset_index(drop=True)
    print(f"\nentradas          : {len(e)}")
    print(f"se abstiene       : {e.se_abstiene.sum()} ({e.se_abstiene.mean()*100:.1f}%)")
    print(f"correos escritos  : {len(escritos)}")

    d = pd.concat([pd.read_csv(DERIVADO / f"cuentas_{p}.csv")
                   for p in ["train", "val", "test"]], ignore_index=True)
    d = d[d.tiene_texto.fillna(False)]
    # se precomputan los conjuntos de terminos: la permutacion se reduce
    # entonces a operaciones de conjuntos y 2.000 repeticiones son segundos
    t_web = {k: terminos(v) for k, v in zip(d.empresa_clave, d.web_text.fillna(""))}
    t_cor = [terminos(c) for c in escritos.correo]
    claves = np.array(list(t_web.keys()))

    # ------------------------------------------------------------------
    print()
    print("-" * 74)
    print("1 · PERSONALIZACION")
    print("-" * 74)

    def personalizacion(conjuntos, webs):
        return float(np.mean([len((tc & t_web[w]) - t_brief) / max(len(tc), 1)
                              for tc, w in zip(conjuntos, webs)]))

    real = personalizacion(t_cor, escritos.empresa_clave)
    print(f"   correos generados            : {real*100:6.2f}%")

    # referencia (a): el correo generico real de Empresa
    generico = BRUTO / f"correo_generico_{a.campana}.txt"
    suelo = None
    if generico.exists():
        txt = re.sub(r"\{\{[^}]*\}\}", "", generico.read_text(encoding="utf-8"))
        t_gen = terminos(txt)
        suelo = float(np.mean([len((t_gen & t_web[k]) - t_brief) / max(len(t_gen), 1)
                               for k in escritos.empresa_clave]))
        print(f"   correo generico de Empresa     : {suelo*100:6.2f}%   <- suelo real")
        print(f"   diferencia                   : {(real-suelo)*100:+6.2f} puntos"
              f"  (x{real/suelo:.1f})")
        print()
        print("   El generico no es cero porque cualquier texto comparte lexico")
        print("   con cualquier web por azar. Ese azar es lo que hay que descontar.")
    else:
        print(f"   (falta {generico.name}: sin el no hay suelo que superar)")

    # referencia (b): permutacion
    nula = np.array([personalizacion(t_cor, rng.choice(claves, len(t_cor), replace=False))
                     for _ in range(a.permutaciones)])
    z = (real - nula.mean()) / nula.std()
    p = (nula >= real).mean()
    print()
    print(f"   control por permutacion (n={a.permutaciones:,})".replace(",", "."))
    print(f"      correo contra OTRA web    : {nula.mean()*100:6.2f}% "
          f"± {nula.std()*100:.2f}")
    print(f"      z                         : {z:6.2f}")
    print(f"      p (una cola)              : {p:.4f}  "
          f"[{int((nula >= real).sum())}/{a.permutaciones}]")

    # ------------------------------------------------------------------
    print()
    print("-" * 74)
    print("2 · REDUNDANCIA ENTRE CORREOS")
    print("-" * 74)
    n = len(t_cor)
    pares = []
    for i in range(n):
        for j in range(i + 1, n):
            u = len(t_cor[i] | t_cor[j])
            pares.append(len(t_cor[i] & t_cor[j]) / u if u else 0.0)
    pares = np.array(pares)
    print(f"   parecido medio entre pares   : {pares.mean():.3f}")
    print(f"   maximo entre dos correos     : {pares.max():.3f}")
    print(f"   correo generico actual       : 1.000  <- el mismo para todas")
    print(f"   -> varia {(1-pares.mean())*100:.0f} puntos sobre el generico")

    # ------------------------------------------------------------------
    print()
    print("-" * 74)
    print("3 · DISTRIBUCION  (lo que esconde la media)")
    print("-" * 74)
    pers = escritos.personalizacion.values
    print(f"   mediana                      : {np.median(pers)*100:6.2f}%")
    print(f"   minimo / maximo              : {pers.min()*100:.2f}% / {pers.max()*100:.2f}%")
    if suelo is not None:
        bajo = (pers < suelo).mean()
        print(f"   por debajo del generico      : {bajo*100:6.1f}%  "
              f"<- no aportan nada sobre lo que ya se manda")

    # ------------------------------------------------------------------
    if a.fichero == "a5_campana_C01.csv":
        print()
        print("-" * 74)
        print("4 · COTEJO CON LA BITACORA (E20)")
        print("-" * 74)
        obtenido = {
            "personalizacion": real * 100,
            "suelo_generico": suelo * 100 if suelo is not None else float("nan"),
            "nula_permutacion": nula.mean() * 100,
            "z": z,
            "redundancia": pares.mean(),
        }
        print(f"   {'cifra':<24}{'bitacora':>11}{'ahora':>11}   estado")
        print("   " + "-" * 58)
        for k, v in BITACORA.items():
            o = obtenido[k]
            tol = 0.15 if k != "redundancia" else 0.01
            print(f"   {k:<24}{v:>11.3f}{o:>11.3f}   "
                  f"{'coincide' if abs(o - v) <= tol else '<-- REVISAR'}")


if __name__ == "__main__":
    main()
