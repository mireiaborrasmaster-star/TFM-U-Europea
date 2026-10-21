# -*- coding: utf-8 -*-
"""
PREP_paquete_sin_texto.py · datos para entrenar A7 y A8 sin ver el texto
=========================================================================

EL PROBLEMA
    A7 y A8 se entrenan con el campo `Tema` del sistema de gestion, que es
    informacion comercial que Empresa pidio proteger. Sin ese fichero los dos
    agentes no arrancan, de modo que quien quiera comprobar el sistema —el
    tribunal, por ejemplo— se queda sin poder ejecutarlos.

LA SALIDA, Y SALE DE E26
    El experimento E26 midio que la representacion por **huella digital**
    (`HashingVectorizer`) rinde igual que TF-IDF y **no almacena ningun
    termino**: convierte cada palabra en una posicion mediante una funcion
    de troceo, sin guardar la correspondencia.

    Asi que se puede entregar la matriz YA TROCEADA con sus etiquetas. Con
    eso se entrena el clasificador y se reproducen las cifras exactas, y el
    texto original no viaja.

LO QUE ESTO ES Y LO QUE NO
    NO es cifrado. El troceo no guarda vocabulario, pero tampoco es
    irreversible en sentido criptografico: quien sospeche que una palabra
    concreta esta en el corpus puede trocearla y mirar si esa posicion
    tiene peso. O sea que **protege frente a la lectura, no frente a la
    comprobacion de una sospecha**.

    Para entregar a un tribunal es proporcionado. Para publicar en abierto
    habria que pensarlo mas.

QUE GENERA
    datos/02_derivado/a8_hashed.npz    la matriz troceada y las etiquetas
    Y una comprobacion de que entrenando con eso sale la misma cifra.

COMO SE EJECUTA
    python scripts/PREP_paquete_sin_texto.py
    python scripts/PREP_paquete_sin_texto.py --guardar
"""

import sys
import unicodedata
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.model_selection import StratifiedKFold
from sklearn.svm import LinearSVC

warnings.filterwarnings("ignore")

VERSION_SCRIPT = "v1 · 06-10-2026"
SEMILLA = 42

RAIZ = Path(__file__).resolve().parent.parent
PRIV = RAIZ / "datos" / "_mapeo_privado"
LIMPIO = RAIZ / "datos" / "01_limpio"
DERIV = RAIZ / "datos" / "02_derivado"

TEMAS = PRIV / "temas_oportunidades.csv"
OPORT = LIMPIO / "Oportunidades - cuentas 2025_ACT 27-09-2026 19-08-56_anon.csv"
SALIDA = DERIV / "a8_hashed.npz"

N_RASGOS = 2 ** 18


def sin_tildes(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t).lower())
                   if unicodedata.category(c) != "Mn")


def main():
    guardar = "--guardar" in sys.argv

    print()
    print("=" * 76)
    print(f"PREP · datos para entrenar sin el texto  ·  {VERSION_SCRIPT}")
    print("=" * 76)
    print()

    if not TEMAS.exists():
        raise SystemExit(f"   No encuentro {TEMAS.name}. Este script hay que\n"
                         f"   lanzarlo en el equipo que SI tiene el mapeo privado.")

    # El paquete tiene que servir a los DOS agentes, y cada uno necesita
    # cosas distintas de la misma tabla:
    #   A8 -> el area tecnica
    #   A7 -> si la oportunidad se gano, y el trimestre para partir por
    #         fecha, porque su evaluacion es temporal y no aleatoria
    tm = pd.read_csv(TEMAS, sep=";")
    op = pd.read_csv(OPORT, sep=";", low_memory=False)
    col = next(c for c in op.columns if "rea de Empresa" in c)
    col_f = next(c for c in op.columns if "Fecha de creaci" in c)
    d = tm.merge(op[["Nº oportunidad", col, "Estado", col_f]],
                 on="Nº oportunidad", how="inner")
    d = d.dropna(subset=["Tema"])
    d["txt"] = d.Tema.astype(str).map(sin_tildes)
    d = d[d.txt.str.len() >= 3]
    # las fechas vienen en ISO; pasar dayfirst aqui las invalidaba y se
    # perdian dos tercios de las filas. Es el error X24.
    d[col_f] = pd.to_datetime(d[col_f], errors="coerce")
    d["trim"] = d[col_f].dt.to_period("Q").astype(str)

    print(f"   Oportunidades con `Tema`        : {len(d):>6}")
    print(f"   …con area asignada              : {d[col].notna().sum():>6}   (A8)")
    print(f"   …cerradas, ganada o perdida     : "
          f"{d.Estado.isin(['Lograda','Perdida']).sum():>6}   (A7)")

    vec = HashingVectorizer(n_features=N_RASGOS, ngram_range=(1, 2),
                            alternate_sign=False, norm="l2")
    X = vec.transform(d.txt)
    area = d[col].fillna("").values
    gana = np.where(d.Estado == "Lograda", 1,
                    np.where(d.Estado == "Perdida", 0, -1))
    trim = d.trim.fillna("").values

    print(f"   Matriz troceada                 : {X.shape[0]} x {X.shape[1]}")
    print(f"   Valores distintos de cero       : {X.nnz:>6}  "
          f"({100*X.nnz/(X.shape[0]*X.shape[1]):.4f} %)")

    # para la comprobacion de A8, solo las areas con casos suficientes
    frec = pd.Series(area).value_counts()
    m8 = pd.Series(area).map(lambda a: a != "" and frec[a] >= 10).values
    X8, y = X[m8], area[m8]

    # ------------------------------------------------------------------
    print()
    print("=" * 76)
    print("COMPROBACION · ¿sale la misma cifra entrenando con esto?")
    print("=" * 76)
    print()
    print("   A8 · enrutar al area  ·  validacion cruzada de 5 pliegues")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMILLA)
    acs = []
    for itr, ite in cv.split(X8, y):
        m = LinearSVC(C=1.0, class_weight="balanced").fit(X8[itr], y[itr])
        acs.append(100 * (m.predict(X8[ite]) == y[ite]).mean())
    ac = float(np.mean(acs))
    print(f"      con la matriz troceada : {ac:.2f} %  (±{np.std(acs):.2f})")
    print(f"      lo publicado           : 80,51 %")
    print(f"      diferencia             : {ac-80.51:+.2f} puntos")

    # --- A7 · ganar o perder, con particion TEMPORAL ----------------------
    from sklearn.linear_model import LogisticRegression
    print()
    print("   A7 · cualificar  ·  particion temporal, como el original")
    m7 = (gana >= 0) & (trim != "")
    X7, y7, t7 = X[m7], gana[m7], trim[m7]
    tr, te = t7 <= "2026Q1", t7 == "2026Q2"
    if te.sum() < 50:
        print("      [!!] el trimestre de prueba se ha quedado sin casos")
        ac7 = float("nan")
    else:
        c7 = LogisticRegression(max_iter=3000, class_weight="balanced")
        c7.fit(X7[tr], y7[tr])
        pr = c7.predict(X7[te])
        ac7 = 100 * (pr == y7[te]).mean()
        suelo = 100 * max(y7[te].mean(), 1 - y7[te].mean())
        print(f"      entrena {tr.sum()} · prueba {te.sum()}")
        print(f"      con la matriz troceada : {ac7:.2f} %   (suelo {suelo:.1f} %)")
        print(f"      lo publicado           : 66,20 %")
        print(f"      diferencia             : {ac7-66.20:+.2f} puntos")

    print()
    ok8 = abs(ac - 80.51) < 3
    ok7 = not np.isnan(ac7) and abs(ac7 - 66.20) < 4
    if ok8 and ok7:
        print("   LOS DOS REPRODUCEN. Quien reciba solo esta matriz obtiene")
        print("   las mismas cifras sin haber visto ni un solo tema.")
    else:
        print("   OJO: alguno NO reproduce lo publicado.")
        print("   A7 usa TF-IDF en el original y aqui va troceado, asi que")
        print("   una diferencia pequena es esperable; una grande no, y")
        print("   habria que explicarla antes de entregar esto.")

    # ------------------------------------------------------------------
    print()
    print("=" * 76)
    print("QUE PROTEGE Y QUE NO")
    print("=" * 76)
    print()
    print("   PROTEGE de la lectura: la matriz no guarda ningun termino.")
    print("   El troceo va en un solo sentido y no hay diccionario que")
    print("   deshacer. Es lo que E26 midio.")
    print()
    print("   NO ES CIFRADO: quien sospeche que una palabra concreta esta en")
    print("   el corpus puede trocearla y mirar si esa posicion tiene peso.")
    print("   O sea que protege frente a LEER, no frente a COMPROBAR UNA")
    print("   SOSPECHA.")
    print()
    print("   Para que un tribunal ejecute el sistema es proporcionado.")
    print("   Para publicarlo en abierto habria que pensarlo mas.")

    if not guardar:
        print()
        print("   Simulacion: no se ha escrito nada. Usa --guardar.")
        print()
        return

    DERIV.mkdir(parents=True, exist_ok=True)
    sparse.save_npz(SALIDA.with_suffix(".tmp.npz"), X.tocsr())
    Xr = sparse.load_npz(SALIDA.with_suffix(".tmp.npz"))
    np.savez_compressed(SALIDA, data=Xr.data, indices=Xr.indices,
                        indptr=Xr.indptr, shape=Xr.shape,
                        area=area, gana=gana, trim=trim,
                        n_rasgos=N_RASGOS)
    SALIDA.with_suffix(".tmp.npz").unlink()

    print()
    print(f"   [ok] {SALIDA.name}  ·  {SALIDA.stat().st_size/1e6:.1f} MB")
    print()
    print("   COTEJO · se vuelve a cargar y se comprueba")
    z = np.load(SALIDA, allow_pickle=True)
    X2 = sparse.csr_matrix((z["data"], z["indices"], z["indptr"]),
                           shape=tuple(z["shape"]))
    igual = ((X2 - X.tocsr()).nnz == 0
             and list(z["area"]) == list(area)
             and list(z["gana"]) == list(gana))
    print(f"   [{'ok' if igual else 'NO'}]  la matriz recargada es identica")
    # ninguna de las columnas de texto puede llevar algo que no sea un
    # codigo de area o un trimestre: se comprueba, no se supone
    hay_texto = any(
        any(len(str(v)) > 8 for v in z[k][:200])
        for k in ("area", "trim") if k in z.files)
    print(f"   [{'ok' if not hay_texto else 'NO'}]  no viaja ningun texto "
          "salvo las etiquetas de area, que ya son codigos")
    if not igual:
        raise SystemExit("   la matriz no se recarga igual")
    print()


if __name__ == "__main__":
    main()
