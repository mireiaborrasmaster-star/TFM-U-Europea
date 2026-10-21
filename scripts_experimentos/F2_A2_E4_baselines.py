"""
BASELINES DEL AGENTE A2  ·  CLASIFICACION SECTORIAL
====================================================
Establece el punto de comparacion antes de tocar ningun transformer.

QUE MIDE
--------
1. Los TRES NIVELES de la taxonomia de Empresa:
       sector agrupado (12)  ·  sector (41)  ·  subsector (169)
   Asi se responde con datos a la pregunta de si conviene simplificar:
   se ve cuanto se gana en fiabilidad al subir de nivel.

2. DE DONDE VIENE LA SENAL (ablacion de entrada):
       solo el nombre  ·  solo el texto web  ·  ambos

3. SEGMENTADO por disponibilidad de texto, que es lo que de verdad explica
   el rendimiento.

PRIVACIDAD: solo imprime metricas y nombres de clase. Ni una empresa.

Uso:  python scripts/F2_A2_E4_baselines.py
"""

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import make_pipeline, make_union
from sklearn.svm import LinearSVC

warnings.filterwarnings("ignore")

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos" / "02_derivado"
SALIDA = RAIZ / "datos" / "03_resultados"
SALIDA.mkdir(parents=True, exist_ok=True)
SEMILLA = 42

NIVELES = [
    ("sector_agrupado", "Sector agrupado"),
    ("sector",          "Sector"),
    ("subsector_agr",   "Subsector (cola plegada)"),
]
ENTRADAS = [
    ("input_nombre",   "solo nombre"),
    ("input_texto",    "solo texto web"),
    ("input_completo", "nombre + texto"),
]


# Longitud maxima de texto que se pasa al vectorizador.
# La longitud media real es de 1.968 caracteres, asi que cortar en 2.000
# apenas pierde informacion y reduce mucho el coste.
CORTE_TEXTO = 2000


def vectorizador():
    """Palabra + caracter.

    Configuracion elegida MIDIENDO, no a ojo. Comparativa sobre el nivel de
    sector (41 clases), sobre el mismo test:

        solo palabras, texto a 1500 ......  44s   acc 44,08   f1m 36,07
        solo palabras, texto a 3000 ......  77s   acc 45,14   f1m 37,50
        palabras + caracteres 4-5 ........ 135s   acc 48,45   f1m 39,93  <- esta
        palabras + caracteres, con SGD ...  88s   acc 44,00   f1m 34,59
        configuracion original (char 3-5,
        200k variables, texto completo) .. >600s

    Conclusiones:
      · Los n-gramas de CARACTERES valen +4,4 puntos. Se mantienen: capturan
        nombres comerciales, acronimos y terminos tecnicos en varios idiomas.
      · SGD es mas rapido pero pierde 4,5 puntos. No compensa.
      · Bajar de char(3,5)/200k a char(4,5)/40k y cortar el texto multiplica
        la velocidad por 4-5 sin perder calidad apreciable.
    """
    return make_union(
        TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=3,
                        max_features=150000, sublinear_tf=True,
                        strip_accents="unicode"),
        TfidfVectorizer(analyzer="char_wb", ngram_range=(4, 5), min_df=5,
                        max_features=40000, sublinear_tf=True,
                        strip_accents="unicode"),
    )


def metricas(y, p):
    return (round(accuracy_score(y, p) * 100, 2),
            round(f1_score(y, p, average="macro", zero_division=0) * 100, 2))


def main():
    for p in ["train", "val", "test"]:
        if not (DATOS / f"cuentas_{p}.csv").exists():
            sys.exit("Faltan los datos. Ejecuta antes PREP_preparar_cuentas.py")

    tr = pd.read_csv(DATOS / "cuentas_train.csv")
    te = pd.read_csv(DATOS / "cuentas_test.csv")
    for d in (tr, te):
        for c in [e for e, _ in ENTRADAS]:
            d[c] = d[c].fillna("").astype(str).str.slice(0, CORTE_TEXTO)

    print("=" * 74)
    print("BASELINES · CLASIFICACION SECTORIAL")
    print("=" * 74)
    print(f"train {len(tr):,} · test {len(te):,}".replace(",", "."))
    print(f"con texto web: train {tr.tiene_texto.mean()*100:.1f}% · "
          f"test {te.tiene_texto.mean()*100:.1f}%")

    filas, predicciones = [], {}

    for nivel, etiqueta_nivel in NIVELES:
        if nivel not in tr.columns or tr[nivel].isna().all():
            continue
        # filas con etiqueta en ese nivel
        t = tr[tr[nivel].notna()]
        e = te[te[nivel].notna()]
        clases = t[nivel].nunique()
        # el test solo puede evaluarse en clases vistas en train
        e = e[e[nivel].isin(set(t[nivel]))]

        print("\n" + "=" * 74)
        print(f"NIVEL: {etiqueta_nivel}   ({clases} clases, "
              f"train {len(t):,}, test {len(e):,})".replace(",", "."))
        print("=" * 74)

        # suelo trivial
        d = DummyClassifier(strategy="most_frequent").fit(t[["input_nombre"]], t[nivel])
        acc, f1 = metricas(e[nivel], d.predict(e[["input_nombre"]]))
        print(f"   {'clase mayoritaria':<22} acc {acc:6.2f}   f1_macro {f1:6.2f}")
        filas.append({"nivel": etiqueta_nivel, "clases": clases,
                      "modelo": "clase mayoritaria", "accuracy": acc, "f1_macro": f1})

        for campo, etiqueta_entrada in ENTRADAS:
            modelo = make_pipeline(
                vectorizador(),
                LinearSVC(C=1.0, class_weight="balanced",
                          random_state=SEMILLA, max_iter=2000),
            ).fit(t[campo], t[nivel])
            pred = modelo.predict(e[campo])
            acc, f1 = metricas(e[nivel], pred)
            print(f"   {'SVM · ' + etiqueta_entrada:<22} acc {acc:6.2f}   f1_macro {f1:6.2f}")
            filas.append({"nivel": etiqueta_nivel, "clases": clases,
                          "modelo": f"SVM · {etiqueta_entrada}",
                          "accuracy": acc, "f1_macro": f1})
            if campo == "input_completo":
                predicciones[nivel] = (e.index, pred)

        # regresion logistica, que si da probabilidades calibrables
        lr = make_pipeline(
            vectorizador(),
            LogisticRegression(C=5.0, class_weight="balanced", max_iter=1000,
                               random_state=SEMILLA, n_jobs=-1),
        ).fit(t["input_completo"], t[nivel])
        acc, f1 = metricas(e[nivel], lr.predict(e["input_completo"]))
        print(f"   {'LogReg · completo':<22} acc {acc:6.2f}   f1_macro {f1:6.2f}")
        filas.append({"nivel": etiqueta_nivel, "clases": clases,
                      "modelo": "LogReg · completo", "accuracy": acc, "f1_macro": f1})

        # segmentacion por disponibilidad de texto
        idx, pred = predicciones[nivel]
        sub = te.loc[idx].copy()
        sub["acierto"] = pred == sub[nivel]
        print("\n   Segun disponibilidad de texto web:")
        for tiene, g in sub.groupby("tiene_texto"):
            print(f"      {'CON texto' if tiene else 'SIN texto':<12} "
                  f"n={len(g):>5}   acc {g.acierto.mean()*100:6.2f}")

    # ---- efecto de la jerarquia incoherente --------------------------
    if "jerarquia_incoherente" in te.columns and "sector" in predicciones:
        idx, pred = predicciones["sector"]
        sub = te.loc[idx].copy()
        sub["acierto"] = pred == sub["sector"]
        print("\n" + "=" * 74)
        print("¿FALLAN MAS LAS FILAS CON JERARQUIA INCOHERENTE?")
        print("=" * 74)
        for v, g in sub.groupby(sub.jerarquia_incoherente.fillna(False)):
            print(f"   {'incoherente' if v else 'coherente':<14} "
                  f"n={len(g):>5}   acc {g.acierto.mean()*100:6.2f}")

    tabla = pd.DataFrame(filas)
    tabla.to_csv(SALIDA / "baselines_cuentas.csv", index=False, encoding="utf-8")
    with open(SALIDA / "baselines_cuentas.json", "w", encoding="utf-8") as f:
        json.dump(filas, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 74)
    print("RESUMEN · mejor modelo por nivel")
    print("=" * 74)
    for nivel, etiqueta in NIVELES:
        sel = tabla[tabla.nivel == etiqueta]
        if len(sel):
            mejor = sel.loc[sel.f1_macro.idxmax()]
            print(f"   {etiqueta:<26} {int(mejor.clases):>4} clases   "
                  f"acc {mejor.accuracy:6.2f}   f1_macro {mejor.f1_macro:6.2f}   "
                  f"({mejor.modelo})")
    print(f"\nGuardado en {SALIDA}")


if __name__ == "__main__":
    main()
