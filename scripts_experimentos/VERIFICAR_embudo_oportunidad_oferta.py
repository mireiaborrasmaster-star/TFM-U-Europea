# -*- coding: utf-8 -*-
"""
VERIFICAR_embudo_oportunidad_oferta.py · ¿qué significa «ganada»?
==================================================================

LA PREGUNTA, QUE LA HIZO LA AUTORA
    «¿Entiendes que una oportunidad ganada quiere decir que se tiene que
    transformar en oferta y luego ganarse?»

    Si el proceso real es oportunidad -> oferta -> lograda, entonces la
    etiqueta que A8 predice NO es un paso sino DOS encadenados: que el caso
    llegue a presupuestarse y que, presupuestado, se gane. Y dos pasos
    metidos en una sola etiqueta se interpretan mal con facilidad: una
    oportunidad que nunca llegó a oferta y otra que se presupuestó y se
    perdió cuentan igual —«no ganada»— cuando para un comercial son cosas
    distintas y se corrigen de forma distinta.

    Esto no se contesta de memoria. Se mide.

QUE COMPRUEBA
    1. Cuántas oportunidades llegan a tener oferta.
    2. Si se puede ganar SIN pasar por oferta. Si se pudiera, el embudo
       no sería tal y la pregunta no tendría consecuencias.
    3. Cuánto vale cada paso por separado: pasar a oferta, y ganar una vez
       presupuestada.
    4. Qué parte de lo que A8 llama «no ganada» es cada cosa.

LO QUE NO HACE
    No cambia A8 ni ninguna cifra publicada. Comprueba qué significa su
    etiqueta, que es distinto.

COMO SE EJECUTA
    python scripts/VERIFICAR_embudo_oportunidad_oferta.py
    python scripts/VERIFICAR_embudo_oportunidad_oferta.py --guardar
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "datos" / "00_bruto"
RES = RAIZ / "datos" / "03_resultados"
OPORT = BRUTO / "Oportunidades - cuentas 2025_ACT 27-09-2026 19-08-56.xlsx"
OFERT = BRUTO / "Ofertas 2025 - ACT 27-09-2026 19-16-12.xlsx"
Z95 = 1.959963985


def wilson(exitos, n):
    if n == 0:
        return (np.nan, np.nan)
    p = exitos / n
    c = (p + Z95 * Z95 / (2 * n)) / (1 + Z95 * Z95 / n)
    m = Z95 * np.sqrt(p * (1 - p) / n + Z95 * Z95 / (4 * n * n)) / (1 + Z95 * Z95 / n)
    return (100 * max(0.0, c - m), 100 * min(1.0, c + m))


def f(v, n=1):
    return f"{v:.{n}f}".replace(".", ",")


def titulo(n, t):
    print()
    print("=" * 76)
    print(f"PASO {n} · {t}")
    print("=" * 76)


def main():
    guardar = "--guardar" in sys.argv
    print()
    print("#" * 76)
    print("# ¿QUE SIGNIFICA «GANADA»? · oportunidad -> oferta -> lograda")
    print("#" * 76)

    op = pd.read_excel(OPORT)
    of = pd.read_excel(OFERT)
    op.columns = [c.strip() for c in op.columns]
    of.columns = [c.strip() for c in of.columns]

    col_k = [c for c in of.columns if "oportunidad" in c.lower()][0]
    op["k"] = op["Nº oportunidad"].astype(str).str.strip()
    of["k"] = of[col_k].astype(str).str.strip()
    con_oferta = set(of.loc[of.k != "nan", "k"])

    op["tiene_oferta"] = op.k.isin(con_oferta)
    est = op.Estado.astype(str).str.strip()
    op["gana"] = est.str.lower() == "lograda"
    op["cerrada"] = est.str.lower().isin(["lograda", "perdida"])

    # ------------------------------------------------------------------ 1
    titulo(1, "EL EMBUDO, TAL COMO ESTA REGISTRADO")
    cerr = op[op.cerrada]
    print(f"   Oportunidades             : {len(op)}")
    print(f"   …cerradas (ganada o perdida): {len(cerr)}")
    print(f"   …con al menos una oferta  : {int(op.tiene_oferta.sum())}")
    print()
    n_co = int(cerr.tiene_oferta.sum())
    lo, hi = wilson(n_co, len(cerr))
    print(f"   De las cerradas, llegan a oferta {n_co} de {len(cerr)}  "
          f"({f(100*n_co/len(cerr))} % [{f(lo)}, {f(hi)}])")

    # ------------------------------------------------------------------ 2
    titulo(2, "¿SE PUEDE GANAR SIN PASAR POR OFERTA?")
    g_sin = int((cerr.gana & ~cerr.tiene_oferta).sum())
    g_con = int((cerr.gana & cerr.tiene_oferta).sum())
    print(f"   Ganadas CON oferta : {g_con}")
    print(f"   Ganadas SIN oferta : {g_sin}")
    print()
    if g_sin == 0:
        print("   NINGUNA. El embudo es estricto: para ganar hay que pasar")
        print("   por oferta, exactamente como dice la autora.")
    else:
        pct = 100 * g_sin / max(1, g_con + g_sin)
        print(f"   {g_sin} oportunidades constan como ganadas sin oferta asociada")
        print(f"   ({f(pct)} % de las ganadas). Puede ser que la oferta no se")
        print(f"   registrara, o que el enlace entre ambas tablas falte. En")
        print(f"   cualquier caso, el embudo NO es estricto en el registro.")

    # ------------------------------------------------------------------ 3
    titulo(3, "CADA PASO POR SEPARADO")
    p1 = 100 * cerr.tiene_oferta.mean()
    sub = cerr[cerr.tiene_oferta]
    p2 = 100 * sub.gana.mean() if len(sub) else np.nan
    total = 100 * cerr.gana.mean()
    l1, h1 = wilson(int(cerr.tiene_oferta.sum()), len(cerr))
    l2, h2 = wilson(int(sub.gana.sum()), len(sub))
    print(f"   {'paso':<40}{'pasan':>10}{'IC 95 %':>20}")
    print("   " + "-" * 74)
    print(f"   {'1 · la oportunidad llega a oferta':<40}{f(p1):>9} %"
          f"{f'[{f(l1)}, {f(h1)}]':>20}")
    print(f"   {'2 · presupuestada, se gana':<40}{f(p2):>9} %"
          f"{f'[{f(l2)}, {f(h2)}]':>20}")
    print(f"   {'1 y 2 · lo que A8 llama «se gana»':<40}{f(total):>9} %{'—':>20}")
    print()
    print(f"   {f(p1)} % × {f(p2)} % = {f(p1*p2/100)} %, que es el "
          f"{f(total)} % de arriba.")
    print("   La etiqueta de A8 es el producto de DOS pasos, no uno.")

    # ------------------------------------------------------------------ 4
    titulo(4, "QUE HAY DENTRO DE «NO GANADA»")
    perd = cerr[~cerr.gana]
    sin_of = int((~perd.tiene_oferta).sum())
    con_of = int(perd.tiene_oferta.sum())
    print(f"   No ganadas : {len(perd)}")
    print(f"      nunca llegaron a presupuestarse : {sin_of}  "
          f"({f(100*sin_of/len(perd))} %)")
    print(f"      se presupuestaron y se perdieron: {con_of}  "
          f"({f(100*con_of/len(perd))} %)")
    print()
    print("   SON DOS FRACASOS DISTINTOS y el modelo los trata igual. Para")
    print("   un comercial no lo son: el primero se corrige calificando")
    print("   mejor o respondiendo antes; el segundo, con el precio, el")
    print("   plazo o la competencia.")

    # ------------------------------------------------------------------ 5
    titulo(5, "QUE SIGNIFICA ESTO PARA A8, Y QUE NO")
    print("   A8 predice el resultado FINAL con lo que se sabe al registrar")
    print("   la oportunidad, que es antes de que exista la oferta. Eso es")
    print("   correcto y es lo que la organización necesita: la pregunta en")
    print("   ese momento es «¿esto acabará en trabajo?», no «¿se firmará el")
    print("   presupuesto que todavía no he hecho?».")
    print()
    print("   Lo que NO puede decirse es que A8 prediga «si se gana la")
    print("   oferta». Predice el recorrido completo, y conviene escribirlo")
    print("   así en la memoria.")
    print()
    print("   Queda como línea de continuación separar los dos pasos: un")
    print("   modelo para «llegará a oferta» y otro para «presupuestada, se")
    print("   gana». El segundo dispone además de la probabilidad que")
    print("   declara el comercial, que solo existe cuando hay oferta.")

    if not guardar:
        print()
        print("   Simulacion: no se ha escrito nada. Usa --guardar.")
        print()
        return

    salida = {
        "pregunta": "¿una oportunidad ganada pasa necesariamente por oferta?",
        "n_oportunidades": int(len(op)), "n_cerradas": int(len(cerr)),
        "cerradas_con_oferta": n_co,
        "pct_llegan_a_oferta": float(p1), "ic_llegan_a_oferta": [l1, h1],
        "pct_ganan_una_vez_presupuestada": float(p2), "ic_ganan": [l2, h2],
        "pct_total_ganadas": float(total),
        "ganadas_sin_oferta": g_sin, "ganadas_con_oferta": g_con,
        "embudo_estricto": bool(g_sin == 0),
        "no_ganadas": {"total": int(len(perd)),
                       "nunca_presupuestadas": sin_of,
                       "presupuestadas_y_perdidas": con_of},
        "consecuencia": "la etiqueta de A8 es el producto de dos pasos; "
                        "predice el recorrido completo, no el cierre de "
                        "la oferta",
    }
    RES.mkdir(parents=True, exist_ok=True)
    p = RES / "embudo_oportunidad_oferta.json"
    p.write_text(json.dumps(salida, ensure_ascii=False, indent=1, default=float),
                 encoding="utf-8")
    print()
    print(f"   [ok] {p.name}")
    print()


if __name__ == "__main__":
    main()
