# -*- coding: utf-8 -*-
"""
A5 · CONTROL POR PERMUTACION DE LA FUNDAMENTACION
==================================================
Responde a una pregunta que la metrica sola no puede responder: un 34,8% de
fundamentacion, ¿es mucho o es poco?

EL PROBLEMA
-----------
La fundamentacion mide que proporcion del vocabulario del correo aparece en la
evidencia (web + ficha del servicio). Pero cualquier correo en castellano
contiene palabras que ninguna web contiene: "ayudar", "durante", "garantizar",
"interesaria". Se cuentan como no respaldadas sin ser afirmaciones sobre nada.

La metrica no tiene suelo conocido. Y un porcentaje sin punto de comparacion no
significa nada.

EL CONTROL
----------
Se evalua cada correo contra la web de OTRA empresa elegida al azar. Si la
puntuacion no baja, la metrica no mide fundamentacion sino solape de castellano
corriente. Repetido 2.000 veces, da la distribucion nula y un p-valor exacto.

Este procedimiento vale para cualquier metrica de fundamentacion y deberia
acompanarla siempre. Ver X9 en la bitacora: el error fue fijar umbrales de
calidad antes de conocer el suelo.

Uso (no necesita GPU):
    python scripts/F5_A5_E19_control_fundamentacion.py
    python scripts/F5_A5_E19_control_fundamentacion.py --permutaciones 5000
"""

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DERIVADO = RAIZ / "datos" / "02_derivado"
RESULTADOS = RAIZ / "datos" / "03_resultados"
sys.path.insert(0, str(Path(__file__).parent))
from F5_A5_E17_emparejar_lexico import leer_catalogo, sin_acentos  # noqa: E402
from F5_A5_E18_emparejar_semantico import texto_servicio  # noqa: E402

VACIAS = {"que", "de", "la", "el", "los", "las", "una", "uno", "para", "con",
          "por", "del", "sus", "este", "esta", "como", "mas", "sobre", "entre",
          "desde", "hasta", "pero", "todo", "cada", "muy", "ser", "son", "han",
          "hay", "les", "nos", "vuestro", "vuestra", "empresa", "empresa",
          "correo", "asunto", "cuerpo", "saludo", "hola", "gracias"}


def raiz(palabra):
    """Misma funcion que en F5_A5_E19_generar_correos.py: recorta a la raiz aproximada para que
    las formas conjugadas cuenten como la misma palabra."""
    p = palabra
    for suf in ("mientos", "aciones", "amiento", "ciones", "mente", "ando",
                "endo", "imos", "amos", "eis", "ais", "ado", "ido", "ar",
                "er", "ir", "es", "as", "os", "a", "o", "s"):
        if len(p) - len(suf) >= 5 and p.endswith(suf):
            return p[:-len(suf)]
    return p


def terminos(texto, minimo=5):
    return {raiz(w) for w in re.findall(r"[a-z]{%d,}" % minimo, sin_acentos(texto))
            if w not in VACIAS}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fichero", default="a5_correos.csv",
                    help="CSV de correos a evaluar")
    ap.add_argument("--permutaciones", type=int, default=2000)
    ap.add_argument("--semilla", type=int, default=42)
    a = ap.parse_args()
    rng = np.random.default_rng(a.semilla)

    print("=" * 68)
    print("A5 · CONTROL POR PERMUTACION DE LA FUNDAMENTACION")
    print(f"     fichero: {a.fichero}")
    print("=" * 68)

    catalogo = {s["codigo"]: s for s in leer_catalogo()}
    d = pd.concat([pd.read_csv(DERIVADO / f"cuentas_{p}.csv")
                   for p in ["train", "val", "test"]], ignore_index=True)
    d = d[d.tiene_texto.fillna(False)]
    e = pd.read_csv(RESULTADOS / a.fichero)
    print(f"Correos: {len(e)}   ·   webs disponibles para el control: {len(d):,}"
          .replace(",", "."))

    # se precomputan los conjuntos de terminos: la permutacion se reduce
    # entonces a operaciones de conjuntos, y 2.000 repeticiones son segundos
    t_web = {k: terminos(v) for k, v in zip(d.empresa_clave, d.web_text.fillna(""))}
    t_serv = {c: terminos(texto_servicio(s)) for c, s in catalogo.items()}
    t_cor = [terminos(r.correo) for r in e.itertuples()]
    servicios = list(e.servicio)
    claves = np.array(list(t_web.keys()))

    def media(webs):
        v = [1 - len(tc - (t_web[w] | t_serv[s])) / max(len(tc), 1)
             for tc, s, w in zip(t_cor, servicios, webs)]
        return float(np.mean(v))

    real = media(list(e.empresa_clave))
    nulas = np.array([media(rng.choice(claves, len(e), replace=False))
                      for _ in range(a.permutaciones)])

    z = (real - nulas.mean()) / nulas.std()
    p = (nulas >= real).mean()

    print("\n" + "-" * 68)
    print(f"   correo contra SU web         : {real*100:6.2f}%")
    print(f"   correo contra OTRA web       : {nulas.mean()*100:6.2f}%  "
          f"(suelo de la metrica, n={a.permutaciones})")
    print(f"   desviacion de la nula        : {nulas.std()*100:6.2f} puntos")
    print(f"   diferencia                   : {(real-nulas.mean())*100:+6.2f} puntos")
    print(f"   z                            : {z:6.2f}")
    print(f"   p (una cola)                 : {p:.4f}   "
          f"[{int((nulas >= real).sum())}/{a.permutaciones}]")
    print("-" * 68)

    if p < 0.05:
        print("\n   Los correos se anclan en la evidencia por encima del azar.")
        print(f"   El margen real es de {(real-nulas.mean())*100:.1f} puntos, no del "
              f"{real*100:.0f}% que sugiere la cifra bruta.")
    else:
        print("\n   No se distingue del azar: la metrica no esta midiendo anclaje.")


if __name__ == "__main__":
    main()
