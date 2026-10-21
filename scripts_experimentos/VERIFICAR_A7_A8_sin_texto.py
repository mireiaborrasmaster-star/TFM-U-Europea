# -*- coding: utf-8 -*-
"""
VERIFICAR_A7_A8_sin_texto.py · entrena A7 y A8 sin ver el texto original
=========================================================================

PARA QUIEN LEA ESTO DESDE FUERA

    Los agentes A7 y A8 se entrenan con un campo de texto del sistema de
    gestion de Empresa que contiene informacion comercial de la empresa, y que
    por eso no se entrega.

    Para que el sistema pueda comprobarse igualmente, ese texto viaja ya
    convertido a una matriz mediante una funcion de troceo
    (`HashingVectorizer`): cada palabra se transforma en una posicion sin
    que se guarde la correspondencia. No hay diccionario que deshacer.

    Este script entrena los dos clasificadores con esa matriz y comprueba
    que salen las mismas cifras que figuran en la memoria.

    NO HACE FALTA TARJETA GRAFICA. Tarda unos segundos.

LO QUE ESTO PROTEGE Y LO QUE NO
    Protege de LEER el texto: no viaja ningun termino.
    NO es cifrado: quien sospeche que una palabra concreta esta en el corpus
    puede trocearla y mirar si esa posicion tiene peso. Queda dicho.

DE DONDE SALE LA IDEA
    Del experimento E26 del propio trabajo, que midio que la representacion
    por troceo rinde igual que TF-IDF y no almacena vocabulario.

COMO SE EJECUTA
    python scripts/VERIFICAR_A7_A8_sin_texto.py
"""

import sys
import warnings
from pathlib import Path

import numpy as np
from scipy import sparse
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.svm import LinearSVC

warnings.filterwarnings("ignore")

VERSION_SCRIPT = "v1 · 06-10-2026"
SEMILLA = 42

RAIZ = Path(__file__).resolve().parent.parent
PAQUETE = RAIZ / "datos" / "02_derivado" / "a8_hashed.npz"

# Lo que la memoria publica, para cotejar
PUBLICADO_A8 = 80.51      # apartado 4.6.4
PUBLICADO_A7 = 66.20      # apartado 4.6.7
SUELO_A8 = 27.12
SUELO_A7 = 56.90


def main():
    print()
    print("#" * 76)
    print("# VERIFICACION · A7 y A8 entrenados sin el texto original")
    print(f"# {VERSION_SCRIPT}")
    print("#" * 76)
    print()

    if not PAQUETE.exists():
        raise SystemExit(
            f"   No encuentro {PAQUETE.name}.\n"
            f"   Deberia estar en datos/02_derivado/. Si no esta, es que la\n"
            f"   copia se entrego sin el, y entonces A7 y A8 no se pueden\n"
            f"   comprobar: sus cifras figuran medidas en la memoria.")

    z = np.load(PAQUETE, allow_pickle=True)
    X = sparse.csr_matrix((z["data"], z["indices"], z["indptr"]),
                          shape=tuple(z["shape"]))
    area, gana, trim = z["area"], z["gana"], z["trim"]

    print(f"   Matriz troceada : {X.shape[0]} casos x {X.shape[1]} posiciones")
    print(f"   Etiquetas       : area (A8) · ganada/perdida (A7) · trimestre")
    print()
    print("   Comprobacion de que no viaja texto:")
    largos = [v for v in list(area[:500]) + list(trim[:500]) if len(str(v)) > 8]
    print(f"   [{'ok' if not largos else 'NO'}]  ninguna etiqueta pasa de 8 "
          "caracteres: son codigos, no texto")

    fallos = 0

    # ------------------------------------------------------------------ A8
    print()
    print("=" * 76)
    print("A8 · ¿a que area tecnica corresponde la solicitud?")
    print("=" * 76)
    import collections
    frec = collections.Counter(area)
    m = np.array([a != "" and frec[a] >= 10 for a in area])
    X8, y8 = X[m], area[m]
    print(f"   Casos: {X8.shape[0]}  ·  areas distintas: {len(set(y8))}")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMILLA)
    acs = []
    for itr, ite in cv.split(X8, y8):
        mod = LinearSVC(C=1.0, class_weight="balanced").fit(X8[itr], y8[itr])
        acs.append(100 * (mod.predict(X8[ite]) == y8[ite]).mean())
    a8 = float(np.mean(acs))

    print()
    print(f"   {'':<28}{'acierto':>10}")
    print("   " + "-" * 40)
    print(f"   {'Suelo: la clase mas comun':<28}{SUELO_A8:>9.2f} %")
    print(f"   {'Aqui, con la matriz':<28}{a8:>9.2f} %  (±{np.std(acs):.2f})")
    print(f"   {'Publicado en la memoria':<28}{PUBLICADO_A8:>9.2f} %")
    d8 = a8 - PUBLICADO_A8
    print(f"   {'Diferencia':<28}{d8:>+9.2f} puntos")
    ok8 = abs(d8) < 3
    print(f"   [{'ok' if ok8 else 'NO'}]  reproduce lo publicado")
    fallos += 0 if ok8 else 1

    # ------------------------------------------------------------------ A7
    print()
    print("=" * 76)
    print("A7 · ¿se va a convertir esta solicitud?")
    print("=" * 76)
    m = (gana >= 0) & (trim != "")
    X7, y7, t7 = X[m], gana[m], trim[m]
    tr, te = t7 <= "2026Q1", t7 == "2026Q2"
    print(f"   Particion TEMPORAL, no aleatoria: se entrena con lo anterior")
    print(f"   a 2026Q2 y se prueba con ese trimestre.")
    print(f"   Entrena {tr.sum()}  ·  prueba {te.sum()}")

    mod = LogisticRegression(max_iter=3000, class_weight="balanced")
    mod.fit(X7[tr], y7[tr])
    a7 = 100 * (mod.predict(X7[te]) == y7[te]).mean()
    suelo = 100 * max(y7[te].mean(), 1 - y7[te].mean())

    print()
    print(f"   {'':<28}{'acierto':>10}")
    print("   " + "-" * 40)
    print(f"   {'Suelo: la clase mas comun':<28}{suelo:>9.2f} %")
    print(f"   {'Aqui, con la matriz':<28}{a7:>9.2f} %")
    print(f"   {'Publicado en la memoria':<28}{PUBLICADO_A7:>9.2f} %")
    d7 = a7 - PUBLICADO_A7
    print(f"   {'Diferencia':<28}{d7:>+9.2f} puntos")
    ok7 = abs(d7) < 4
    print(f"   [{'ok' if ok7 else 'NO'}]  reproduce lo publicado")
    fallos += 0 if ok7 else 1
    print()
    print("   NOTA: el original de A7 usa TF-IDF y aqui va troceado, asi que")
    print("   una diferencia de uno o dos puntos es esperable. La de A8 no,")
    print("   porque alli el modelo final YA usaba troceo.")

    # ------------------------------------------------------------------
    print()
    print("=" * 76)
    if fallos:
        print(f"   {fallos} de 2 NO reproducen. Habria que mirar por que.")
        print()
        sys.exit(1)
    print("   LOS DOS REPRODUCEN LO PUBLICADO.")
    print()
    print("   Y se ha hecho sin que el texto original saliera de Empresa, que")
    print("   es el procedimiento que el apartado 4.2.4 describe y que el")
    print("   experimento E26 justifica: la representacion por troceo rinde")
    print("   igual y no almacena vocabulario.")
    print()


if __name__ == "__main__":
    main()
