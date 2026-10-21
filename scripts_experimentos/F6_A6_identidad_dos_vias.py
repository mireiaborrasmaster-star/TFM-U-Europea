# -*- coding: utf-8 -*-
"""
F6_A6_identidad_dos_vias.py · ¿resuelve mejor el dominio del correo?
=====================================================================

LA PREGUNTA
    La primera pieza de A6 decide si quien escribe ya esta en el sistema de
    gestion. Hasta ahora solo podia hacerlo de una forma: comparar el
    `@dominio` del remitente con el dominio que se extrae del campo
    `Sitio web` de la cuenta. Eso resolvia 32 de 98 correos, un 32,7 %.

    Esa via tiene un techo estructural conocido: solo el 67,7 % de las
    cuentas tiene sitio web. Y ademas compara dos cosas que no son la misma
    —el dominio de una pagina web y el de un correo—, que es la confusion
    que costo el error X19.

    La autora ha anadido al CRM una columna `Dominio` con la parte de
    detras de la arroba del correo asociado a la cuenta. Eso SI es lo mismo
    que se compara. La pregunta es si funciona mejor.

QUE SE COMPARA
    Tres formas de resolver la identidad, sobre los MISMOS correos:
       1. VIA WEB      · el @dominio contra el dominio del `Sitio web`
       2. VIA DOMINIO  · el @dominio contra la columna `Dominio`
       3. LAS DOS      · vale con que resuelva cualquiera de las dos

    Y para cada una: cuantas cuentas son candidatas (el techo estructural),
    cuantos correos resuelve, y con que intervalo.

POR QUE IMPORTA QUE SEAN COMPLEMENTARIAS
    4.909 cuentas tienen `Dominio` y NO tienen sitio web. Si las dos vias
    taparan los mismos huecos, sumarlas no aportaria nada. Como no lo hacen,
    la pregunta no es cual gana sino cuanto suman juntas.

CONFIDENCIALIDAD
    No imprime ningun dominio concreto, ningun nombre de empresa ni ninguna
    direccion. Solo recuentos.

COMO SE EJECUTA
    python scripts/F6_A6_identidad_dos_vias.py
    python scripts/F6_A6_identidad_dos_vias.py --guardar
"""

import json
import re
import sys
import unicodedata
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

VERSION_SCRIPT = "v1 · 05-10-2026"

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "datos" / "00_bruto"
LIMPIO = RAIZ / "datos" / "01_limpio"
RES = RAIZ / "datos" / "03_resultados"

CUENTAS = BRUTO / "Cuentas activas 25-09-2026 20-36-50.xlsx"
CORPUS = LIMPIO / "entradas_inbound_50_anon.csv"

Z95 = 1.959963984540054

# Dominios de correo que no identifican a ninguna empresa
GENERICOS = {
    "gmail.com", "hotmail.com", "outlook.com", "yahoo.com", "yahoo.es",
    "live.com", "icloud.com", "aol.com", "protonmail.com", "gmx.com",
    "msn.com", "terra.es", "telefonica.net", "hotmail.es", "outlook.es",
}


def limpia_dominio(x):
    """Deja un dominio desnudo: sin protocolo, sin www, sin ruta, sin arroba.

    Sirve para las tres fuentes —el remitente, el `Sitio web` y la columna
    `Dominio`— precisamente para que la comparacion sea entre iguales. Es
    la leccion del error X19: antes se comparaban cosas distintas.
    """
    u = str(x).lower().strip()
    if not u or u == "nan":
        return ""
    u = u.split("@")[-1]
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    u = u.split("/")[0].split("?")[0].split(":")[0]
    return u.strip(" .")


def wilson(exitos, n):
    if n == 0:
        return (np.nan, np.nan)
    p = exitos / n
    c = (p + Z95 * Z95 / (2 * n)) / (1 + Z95 * Z95 / n)
    m = Z95 * np.sqrt(p * (1 - p) / n + Z95 * Z95 / (4 * n * n)) / (1 + Z95 * Z95 / n)
    return (100 * max(0.0, c - m), 100 * min(1.0, c + m))


def mcnemar_exacto(solo_a, solo_b):
    """p de dos colas para dos metodos sobre los MISMOS casos.

    Solo cuentan los casos en que discrepan: los que ambos aciertan o ambos
    fallan no informan de cual es mejor. Con pocos casos se calcula exacto
    con la binomial, no con la aproximacion de ji-cuadrado.
    """
    n = solo_a + solo_b
    if n == 0:
        return 1.0
    k = min(solo_a, solo_b)
    # suma de la binomial(n, 0.5) en las dos colas
    from math import comb
    cola = sum(comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return float(min(1.0, 2 * cola))


def titulo(n, t):
    print()
    print("=" * 76)
    print(f"PASO {n} · {t}")
    print("=" * 76)


def main():
    guardar = "--guardar" in sys.argv

    print()
    print("#" * 76)
    print("# F6 · A6 · ¿resuelve mejor la identidad el dominio del correo?")
    print(f"# {VERSION_SCRIPT}")
    print("#" * 76)

    # ------------------------------------------------------------------ 1
    titulo(1, "LAS DOS FUENTES DEL CRM")
    cu = pd.read_excel(CUENTAS)
    cu.columns = [c.strip() for c in cu.columns]
    col_web = next(c for c in cu.columns if "Sitio web" in c)
    col_dom = next((c for c in cu.columns if c.strip().lower() == "dominio"), None)
    if col_dom is None:
        raise SystemExit("   No encuentro la columna «Dominio» en el export de cuentas")

    cu["d_web"] = cu[col_web].map(limpia_dominio)
    cu["d_cor"] = cu[col_dom].map(limpia_dominio)
    # un dominio generico en la ficha de una cuenta no identifica nada
    cu.loc[cu.d_cor.isin(GENERICOS), "d_cor"] = ""
    cu.loc[cu.d_web.isin(GENERICOS), "d_web"] = ""

    n_cu = len(cu)
    con_web = int((cu.d_web != "").sum())
    con_cor = int((cu.d_cor != "").sum())
    con_alg = int(((cu.d_web != "") | (cu.d_cor != "")).sum())
    solo_cor = int(((cu.d_cor != "") & (cu.d_web == "")).sum())

    print(f"   Cuentas en el sistema de gestión : {n_cu:>7}")
    print()
    print(f"   {'fuente':<34}{'cuentas':>9}{'% del total':>13}")
    print("   " + "-" * 56)
    print(f"   {'con Sitio web utilizable':<34}{con_web:>9}{100*con_web/n_cu:>12.1f} %")
    print(f"   {'con la columna Dominio':<34}{con_cor:>9}{100*con_cor/n_cu:>12.1f} %")
    print(f"   {'con alguna de las dos':<34}{con_alg:>9}{100*con_alg/n_cu:>12.1f} %")
    print()
    print(f"   LAS DOS SON COMPLEMENTARIAS: {solo_cor} cuentas tienen Dominio")
    print("   y NO tienen sitio web. Por eso sumarlas sube el techo.")
    print()
    print(f"   EL TECHO ESTRUCTURAL PASA DEL {100*con_web/n_cu:.1f} % "
          f"AL {100*con_alg/n_cu:.1f} %.")
    print("   Ese techo no es el acierto: es el maximo al que se puede")
    print("   aspirar, porque una cuenta sin ninguno de los dos campos no")
    print("   se puede encontrar por esta via haga lo que haga el sistema.")

    dom_web = {d for d in cu.d_web if d}
    dom_cor = {d for d in cu.d_cor if d}

    # ------------------------------------------------------------------ 2
    titulo(2, "LOS CORREOS SOBRE LOS QUE SE MIDE")
    co = pd.read_csv(CORPUS, sep=";")
    co["dom"] = co.dominio.map(limpia_dominio)
    co["generico"] = co.dom.isin(GENERICOS) | (co.dom == "")
    pr = co[~co.generico].copy()
    print(f"   Correos del buzón                : {len(co):>5}")
    print(f"   …con dominio de empresa          : {len(pr):>5}   "
          "<-- sobre estos se mide")
    print(f"   …con dominio genérico (gmail…)   : {len(co)-len(pr):>5}   "
          "no identifican a nadie")

    # ------------------------------------------------------------------ 3
    titulo(3, "LAS TRES VÍAS, SOBRE LOS MISMOS CORREOS")
    pr["por_web"] = pr.dom.isin(dom_web)
    pr["por_cor"] = pr.dom.isin(dom_cor)
    pr["por_alg"] = pr.por_web | pr.por_cor

    n = len(pr)
    filas = []
    for etiqueta, col in (("1 · vía web (la publicada)", "por_web"),
                          ("2 · vía Dominio (nueva)", "por_cor"),
                          ("3 · las dos juntas", "por_alg")):
        a = int(pr[col].sum())
        lo, hi = wilson(a, n)
        filas.append({"via": etiqueta, "resueltos": a, "de": n,
                      "pct": 100 * a / n, "ic": [lo, hi]})

    print(f"   {'vía':<30}{'resuelve':>10}{'%':>8}{'IC 95 %':>20}")
    print("   " + "-" * 68)
    for f in filas:
        ic = f"[{f['ic'][0]:.1f}, {f['ic'][1]:.1f}]"
        print(f"   {f['via']:<30}{f['resueltos']:>5} de {f['de']:<2}"
              f"{f['pct']:>7.1f} %{ic:>20}")

    # ------------------------------------------------------------------ 4
    titulo(4, "¿MEJOR O PEOR?  ·  comparación emparejada")
    solo_w = int((pr.por_web & ~pr.por_cor).sum())
    solo_c = int((pr.por_cor & ~pr.por_web).sum())
    ambas = int((pr.por_web & pr.por_cor).sum())
    ninguna = int((~pr.por_web & ~pr.por_cor).sum())

    print(f"   {'':<28}{'vía Dominio sí':>16}{'vía Dominio no':>16}")
    print("   " + "-" * 60)
    print(f"   {'vía web sí':<28}{ambas:>16}{solo_w:>16}")
    print(f"   {'vía web no':<28}{solo_c:>16}{ninguna:>16}")
    print()
    print("   Solo informan las casillas en que discrepan: los que resuelven")
    print("   las dos, o ninguna, no dicen cuál es mejor.")
    print()
    print(f"   Resuelve SOLO la vía web     : {solo_w}")
    print(f"   Resuelve SOLO la vía Dominio : {solo_c}")
    p = mcnemar_exacto(solo_w, solo_c)
    print(f"   p exacto (binomial de dos colas): {p:.4f}")
    print()
    if solo_c > solo_w and p < 0.05:
        v = "LA VÍA DOMINIO ES MEJOR, y la diferencia no se explica por azar"
    elif solo_w > solo_c and p < 0.05:
        v = "LA VÍA WEB ES MEJOR, y la diferencia no se explica por azar"
    elif solo_c > solo_w:
        v = ("La vía Dominio resuelve más, pero con estos casos la diferencia "
             "NO alcanza significación")
    elif solo_w > solo_c:
        v = ("La vía web resuelve más, pero con estos casos la diferencia "
             "NO alcanza significación")
    else:
        v = "Empatan exactamente"
    print(f"   {v}")

    # ------------------------------------------------------------------ 5
    titulo(5, "LO QUE ESTO CAMBIA PARA EL AGENTE")
    pub = filas[0]
    nue = filas[2]
    print(f"   Lo publicado hasta ahora  : {pub['resueltos']} de {pub['de']}  "
          f"{pub['pct']:.1f} %")
    print(f"   Con las dos vías          : {nue['resueltos']} de {nue['de']}  "
          f"{nue['pct']:.1f} %")
    print(f"   Gana {nue['resueltos']-pub['resueltos']} correos  "
          f"({nue['pct']-pub['pct']:+.1f} puntos)")
    print()
    print("   Y RECUÉRDESE POR QUÉ IMPORTA: por la decisión D19 el sistema no")
    print("   da de alta cuentas por su cuenta. Cada correo que se resuelve")
    print("   es uno que NO necesita que una persona decida el alta, así que")
    print("   esta pieza es la que limita la automatización completa de A6.")
    print()
    print("   SALVEDADES")
    print(f"   · Son {n} correos. Los intervalos son anchos y se publican.")
    print("   · El techo estructural sigue existiendo, solo que más alto:")
    print(f"     el {100-100*con_alg/n_cu:.1f} % de las cuentas no tiene ninguno")
    print("     de los dos campos y por esta vía no se puede encontrar.")
    print("   · Las vías 1 y 2 de la decisión D18 —buscar en los contactos—")
    print("     siguen sin medirse: exigen datos personales que no se")
    print("     exportaron.")

    if not guardar:
        print()
        print("   Simulación: no se ha escrito nada. Usa --guardar.")
        print()
        return

    salida = {
        "experimento": "E35", "agente": "A6", "pieza": "1 · identidad",
        "version": VERSION_SCRIPT,
        "cuentas": {"total": n_cu, "con_sitio_web": con_web,
                    "con_dominio": con_cor, "con_alguna": con_alg,
                    "solo_dominio": solo_cor,
                    "techo_web_pct": 100 * con_web / n_cu,
                    "techo_ambas_pct": 100 * con_alg / n_cu},
        "correos": {"total": int(len(co)), "con_dominio_empresa": n},
        "vias": filas,
        "emparejado": {"ambas": ambas, "solo_web": solo_w,
                       "solo_dominio": solo_c, "ninguna": ninguna,
                       "p_exacto": p, "veredicto": v},
        "limitaciones": [
            f"{n} correos: intervalos anchos",
            "las vias 1 y 2 de D18 siguen sin medir: datos personales",
            "el techo estructural sigue, solo que mas alto",
        ],
    }
    RES.mkdir(parents=True, exist_ok=True)
    f = RES / "a6_identidad_dos_vias.json"
    f.write_text(json.dumps(salida, ensure_ascii=False, indent=1, default=float),
                 encoding="utf-8")
    print()
    print(f"   [ok] {f.name}")
    print()


if __name__ == "__main__":
    main()
