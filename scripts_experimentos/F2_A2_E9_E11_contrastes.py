"""
CONTRASTES ESTADISTICOS DE A2  ·  reproduce E9, E10 y E11
==========================================================
Recalcula todos los contrastes que sostienen las conclusiones de A2 a partir
de las predicciones guardadas en datos/03_resultados/pred_*.csv.

POR QUE EXISTE ESTE FICHERO
---------------------------
Los contrastes de E9 y E11 se calcularon en su momento de forma exploratoria y
sus resultados se escribieron en la bitacora, pero el codigo que los producia
no se guardo. Las conclusiones centrales de A2 —que el transformer supera al
modelo lineal en aciertos pero no en F1-macro— descansaban por tanto sobre
cifras que nadie podia recomprobar.

Este script las recalcula todas. Si alguna no coincide con la bitacora, lo dice.

QUE CONTRASTES, Y POR QUE ESOS
------------------------------
McNEMAR EXACTO
  Compara dos clasificadores sobre LAS MISMAS empresas. Al ser una comparacion
  pareada, solo informan los casos en que discrepan: aquellos donde uno acierta
  y el otro falla. Los casos en que ambos aciertan o ambos fallan no dicen nada
  sobre cual es mejor, y contarlos —como haria un test para muestras
  independientes— diluiria la senal y perderia potencia.

  Se usa la version EXACTA (binomial) en lugar de la aproximacion chi-cuadrado
  con correccion de continuidad, porque el numero de discordancias es moderado
  y la exacta no necesita supuestos asintoticos.

BOOTSTRAP SOBRE LA DIFERENCIA DE F1-MACRO
  El F1-macro no admite un test pareado directo: no se descompone en aciertos
  por observacion, porque promedia el rendimiento por clase y cada clase depende
  de todas las filas a la vez. Se remuestrean por tanto las empresas con
  reemplazo, se recalcula la diferencia en cada remuestreo y se mira si el
  intervalo cruza el cero.

  Distincion importante: que el transformer gane en aciertos NO implica que gane
  en F1-macro. Aciertos premia acertar las clases frecuentes; F1-macro pesa
  igual todas las clases, incluidas las de pocos casos. Son dos preguntas
  distintas y el trabajo llego a responderlas de forma opuesta.

UNA ADVERTENCIA METODOLOGICA
----------------------------
En dos ocasiones se afirmo en esta bitacora que una diferencia era o no
significativa ANTES de contrastarla, y se fallo en ambas direcciones (ver la
seccion de errores). Este script existe tambien para que eso no vuelva a pasar:
el contraste se ejecuta, no se estima a ojo.

CUIDADO CON EL NOMBRE DE LOS FICHEROS  (error X11)
--------------------------------------------------
El modelo final de A2 NO esta en pred_principal.csv sino en
pred_abl_sin_jerarquia.csv.

La razon es historica: el modelo "principal" se entreno con cabeza jerarquica y
quitarla se planteo como una ABLACION. Resulto que la ablacion era mejor
(51,73 frente a 50,98) y paso a ser el modelo final, pero los ficheros
conservaron el nombre con que nacieron.

La primera version de este script comparo pred_principal.csv con el lineal y
obtuvo p = 0,026 y una diferencia de F1-macro NEGATIVA, cuando la bitacora
registra p = 0,002 y una diferencia positiva. No era un error de la bitacora:
era que el script estaba comparando el modelo equivocado.

Por eso aqui los ficheros se declaran explicitamente en FINAL y JERARQUICO en
lugar de deducirse del nombre.

Uso (sin GPU, en segundos):
    python scripts/F2_A2_E9_E11_contrastes.py
    python scripts/F2_A2_E9_E11_contrastes.py --remuestreos 20000
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

VERSION_SCRIPT = "v1 · 29-09-2026"

RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS = RAIZ / "datos" / "03_resultados"

# Que fichero es cada modelo. Se declara aqui y no se deduce del nombre:
# ver la advertencia sobre X11 en la cabecera.
FINAL = "pred_abl_sin_jerarquia.csv"       # el MODELO FINAL de A2
JERARQUICO = "pred_principal.csv"          # variante con cabeza jerarquica
LINEAL = "pred_lineal.csv"

# Lo que dice la bitacora. Se compara al final para detectar divergencias.
BITACORA = {
    "transformer_vs_lineal_acc_p": 0.002,
    "transformer_acc": 51.73,
    "lineal_acc": 48.91,
    "transformer_f1": 43.38,
    "lineal_f1": 41.89,
    "f1_bootstrap_p": 0.241,
}


def f1_macro(y, p):
    """F1-macro sin sklearn, para que el script no dependa de nada pesado.

    Promedia el F1 de cada clase presente en las etiquetas reales. Las clases
    sin ninguna prediccion ni caso real quedan fuera; las que existen en y pero
    nunca se predicen cuentan como F1 = 0, que es lo correcto: no detectarlas
    es un fallo, no un caso a ignorar.
    """
    clases = pd.unique(y)
    f1s = []
    for c in clases:
        tp = int(((y == c) & (p == c)).sum())
        fp = int(((y != c) & (p == c)).sum())
        fn = int(((y == c) & (p != c)).sum())
        if tp == 0:
            f1s.append(0.0)
            continue
        prec = tp / (tp + fp)
        rec = tp / (tp + fn)
        f1s.append(2 * prec * rec / (prec + rec))
    return float(np.mean(f1s))


def mcnemar_exacto(a, b):
    """Test de McNemar exacto sobre dos vectores de aciertos (booleanos).

    Devuelve (n01, n10, p). n01 = solo B acierta; n10 = solo A acierta.
    Bajo la hipotesis nula de igual rendimiento, cada discordancia es una
    moneda equilibrada, de modo que n01 ~ Binomial(n01+n10, 0.5).
    """
    n01 = int((~a & b).sum())
    n10 = int((a & ~b).sum())
    n = n01 + n10
    if n == 0:
        return n01, n10, 1.0
    try:
        from scipy.stats import binomtest
        p = binomtest(min(n01, n10), n, 0.5).pvalue
    except ImportError:
        from math import comb
        k = min(n01, n10)
        p = min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)
    return n01, n10, p


def bootstrap_diferencia(y, pa, pb, metrica, remuestreos, semilla=42):
    """Intervalo de confianza de la diferencia metrica(B) - metrica(A).

    Se remuestrean las EMPRESAS, no las predicciones sueltas: la unidad de
    incertidumbre es la empresa de la muestra de prueba, y las dos predicciones
    de una misma empresa tienen que viajar juntas para que la comparacion siga
    siendo pareada.
    """
    rng = np.random.default_rng(semilla)
    n = len(y)
    difs = np.empty(remuestreos)
    for i in range(remuestreos):
        idx = rng.integers(0, n, n)
        difs[i] = metrica(y[idx], pb[idx]) - metrica(y[idx], pa[idx])
    obs = metrica(y, pb) - metrica(y, pa)
    # p de dos colas: proporcion de remuestreos al otro lado del cero
    p = 2 * min((difs <= 0).mean(), (difs >= 0).mean())
    return obs, np.percentile(difs, [2.5, 97.5]), min(p, 1.0)


def cargar(nombre, col_pred, col_acierto):
    ruta = RESULTADOS / nombre
    if not ruta.exists():
        return None
    d = pd.read_csv(ruta)
    return pd.DataFrame({
        "empresa": d.empresa_clave,
        "real": d.sector,
        "pred": d[col_pred],
        "acierto": d[col_acierto].astype(bool),
        "tiene_texto": d.tiene_texto.astype(bool),
    })


def sep(t):
    print()
    print("=" * 74)
    print(t)
    print("=" * 74)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--remuestreos", type=int, default=10000)
    a = ap.parse_args()

    print("=" * 74)
    print("CONTRASTES ESTADISTICOS DE A2")
    print(f"     {VERSION_SCRIPT}  ·  reproduce E9, E10 y E11")
    print("=" * 74)

    princ = cargar(FINAL, "pred_sector", "acierto")
    lin = cargar(LINEAL, "pred_lineal", "acierto_lineal")
    if princ is None or lin is None:
        sys.exit(f"Faltan {FINAL} o {LINEAL} en 03_resultados")
    print()
    print(f"MODELO FINAL   : {FINAL}")
    print(f"MODELO LINEAL  : {LINEAL}")
    if not princ.empresa.equals(lin.empresa):
        sys.exit("Los dos ficheros no estan en el mismo orden de empresas: "
                 "la comparacion pareada no seria valida")

    y = princ.real.values
    print(f"\nEmpresas de prueba : {len(princ):,}".replace(",", "."))
    print(f"Clases (sector)    : {princ.real.nunique()}")
    print(f"Con texto web      : {princ.tiene_texto.mean()*100:.1f}%")

    # ------------------------------------------------------------------
    sep("1 · RENDIMIENTO DE CADA MODELO")
    modelos = {
        "Transformer (FINAL)": princ,
        "Regresion logistica": lin,
    }
    for nombre, arch in {
        "Ablacion · con jerarquia": JERARQUICO,
        "Ablacion · sin pesos": "pred_abl_sin_pesos.csv",
        "Ablacion · solo nombre": "pred_abl_solo_nombre.csv",
    }.items():
        d = cargar(arch, "pred_sector", "acierto")
        if d is not None:
            modelos[nombre] = d

    print(f"   {'modelo':<28}{'aciertos':>10}{'F1-macro':>11}")
    print("   " + "-" * 49)
    tabla = {}
    for nombre, d in modelos.items():
        acc = d.acierto.mean() * 100
        f1 = f1_macro(d.real.values, d.pred.values) * 100
        tabla[nombre] = (acc, f1)
        print(f"   {nombre:<28}{acc:>9.2f}%{f1:>10.2f}%")

    # ------------------------------------------------------------------
    sep("2 · McNEMAR · transformer frente a regresion logistica (E9)")
    n01, n10, p = mcnemar_exacto(lin.acierto.values, princ.acierto.values)
    ambos = int((lin.acierto & princ.acierto).sum())
    ninguno = int((~lin.acierto & ~princ.acierto).sum())
    print(f"   aciertan los dos            : {ambos:>5}")
    print(f"   falla el lineal, acierta el transformer : {n01:>5}  <- informativo")
    print(f"   acierta el lineal, falla el transformer : {n10:>5}  <- informativo")
    print(f"   fallan los dos              : {ninguno:>5}")
    print(f"   discordancias totales       : {n01+n10:>5}  "
          f"({(n01+n10)/len(princ)*100:.1f}% de la muestra)")
    print(f"\n   p (McNemar exacto)          : {p:.4f}")
    print(f"   -> {'diferencia significativa' if p < 0.05 else 'NO significativa'}"
          f" en aciertos")
    print()
    print("   Notese que solo el "
          f"{(n01+n10)/len(princ)*100:.0f}% de las empresas aporta informacion.")
    print("   Es la razon de usar un test pareado: las "
          f"{ambos+ninguno} restantes")
    print("   diluirian la senal sin decir nada sobre cual modelo es mejor.")

    # ------------------------------------------------------------------
    sep("3 · BOOTSTRAP · diferencia de F1-macro (E11)")
    print(f"   remuestreos: {a.remuestreos:,}".replace(",", "."))
    obs, ic, pb = bootstrap_diferencia(
        y, lin.pred.values, princ.pred.values, f1_macro, a.remuestreos)
    print(f"   diferencia observada        : {obs*100:+.2f} puntos")
    print(f"   IC 95 %                     : [{ic[0]*100:+.2f}, {ic[1]*100:+.2f}]")
    print(f"   p (dos colas)               : {pb:.3f}")
    print(f"   -> {'significativa' if pb < 0.05 else 'NO significativa'}"
          f" en F1-macro")
    print()
    print("   Este es el contraste que corrigio una afirmacion previa: ganar en")
    print("   aciertos no implica ganar en F1-macro. Aciertos premia las clases")
    print("   frecuentes; F1-macro pesa igual todas, incluidas las raras.")

    # ------------------------------------------------------------------
    sep("4 · ABLACIONES · cada pieza frente al modelo final (E10)")
    print(f"   {'ablacion':<28}{'dif. acc':>10}{'n01':>6}{'n10':>6}{'p':>9}")
    print("   " + "-" * 59)
    for nombre, d in modelos.items():
        if not nombre.startswith("Ablacion"):
            continue
        n01, n10, p = mcnemar_exacto(d.acierto.values, princ.acierto.values)
        dif = (princ.acierto.mean() - d.acierto.mean()) * 100
        marca = " *" if p < 0.05 else ""
        print(f"   {nombre:<28}{dif:>+9.2f}%{n01:>6}{n10:>6}{p:>9.4f}{marca}")
    print("\n   (n01 = solo acierta el modelo final; n10 = solo la ablacion)")

    # ------------------------------------------------------------------
    sep("5 · SEGMENTADO POR DISPONIBILIDAD DE TEXTO WEB")
    for etiqueta, mask in [("con texto", princ.tiene_texto),
                           ("sin texto", ~princ.tiene_texto)]:
        pa = princ[mask]
        pl = lin[mask]
        n01, n10, p = mcnemar_exacto(pl.acierto.values, pa.acierto.values)
        print(f"   {etiqueta}  n={mask.sum():>5}   "
              f"transformer {pa.acierto.mean()*100:5.2f}%   "
              f"lineal {pl.acierto.mean()*100:5.2f}%   p={p:.4f}")

    # ------------------------------------------------------------------
    sep("6 · COTEJO CON LO ESCRITO EN LA BITACORA")
    obtenido = {
        "transformer_acc": tabla["Transformer (FINAL)"][0],
        "lineal_acc": tabla["Regresion logistica"][0],
        "transformer_f1": tabla["Transformer (FINAL)"][1],
        "lineal_f1": tabla["Regresion logistica"][1],
        "f1_bootstrap_p": pb,
    }
    n01, n10, p_acc = mcnemar_exacto(lin.acierto.values, princ.acierto.values)
    obtenido["transformer_vs_lineal_acc_p"] = p_acc

    print(f"   {'cifra':<30}{'bitacora':>11}{'ahora':>11}   estado")
    print("   " + "-" * 64)
    desvios = 0
    for k, v in BITACORA.items():
        o = obtenido[k]
        # tolerancia: 0,05 puntos en porcentajes, 0,03 en p-valores de remuestreo
        tol = 0.03 if k.endswith("_p") else 0.05
        ok = abs(o - v) <= tol
        desvios += 0 if ok else 1
        print(f"   {k:<30}{v:>11.3f}{o:>11.3f}   {'coincide' if ok else '<-- REVISAR'}")
    print()
    if desvios == 0:
        print("   Todas las cifras de la bitacora se reproducen.")
    else:
        print(f"   {desvios} cifra(s) no coinciden. El p-valor del bootstrap puede")
        print("   variar levemente con la semilla y el numero de remuestreos; una")
        print("   diferencia en los porcentajes, en cambio, hay que investigarla.")


if __name__ == "__main__":
    main()
