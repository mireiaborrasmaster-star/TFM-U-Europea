"""
A3 · ARBOLES FRENTE A REDES NEURONALES EN DATOS TABULARES  (RQ2b · M4)
======================================================================
Compara familias de modelos sobre las MISMAS variables tabulares de A3 para
responder empiricamente a una pregunta que hasta ahora solo estaba respaldada
por la literatura:

    ¿Conviene una red neuronal para puntuar cuentas, o los modelos de arboles
    siguen siendo preferibles en este tipo de dato?

POR QUE HACE FALTA MEDIRLO
--------------------------
El documento 06_MODELOS_POR_AGENTE.md razona que en datos tabulares los modelos
de arboles superan a las redes por motivos estructurales —variables
heterogeneas, ausencia de vecindad u orden entre columnas, relaciones
escalonadas, robustez a variables inutiles— y cita literatura que lo respalda
(Grinsztajn et al., 2022; Shwartz-Ziv y Armon, 2022).

Pero un argumento teorico se rebate con otro argumento teorico. Una medicion, no.
La diferencia entre escribir en la memoria "la literatura sostiene que" y "se
probaron ambas familias sobre los mismos datos y el resultado fue" es la
diferencia entre una justificacion discutible y un dato.

Estaba anotado como medicion pendiente M4 desde el 27-09-2026. Este script la
cierra.

QUE SE COMPARA
--------------
Todas las familias reciben EXACTAMENTE las mismas variables y la misma
particion, de modo que la unica diferencia es el modelo:

  Clase mayoritaria       el suelo: responder siempre lo mas frecuente
  Regresion logistica     lineal, el clasico
  Random Forest           arboles en paralelo
  Gradient Boosting       arboles en secuencia
  Red neuronal densa      2 capas ocultas
  Red neuronal profunda   3 capas ocultas, mas ancha

Se reporta rendimiento, tiempo de entrenamiento y numero de parametros o
reglas, porque la decision de ingenieria no depende solo del acierto.

UN RESULTADO NEGATIVO TAMBIEN VALE
----------------------------------
Si la red gana, hay que decirlo y cambiar el modelo de A3. Si pierde, es una
ablacion que respalda la eleccion. En ambos casos el experimento informa; la
unica opcion mala es no hacerlo y afirmar de todos modos.

Uso (sin GPU, unos 2 minutos):
    python scripts/F3_A3_E21_arboles_vs_redes.py
    python scripts/F3_A3_E21_arboles_vs_redes.py --sin_texto
"""

import argparse
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

VERSION_SCRIPT = "v1 · 29-09-2026"

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "datos" / "03_resultados"
SALIDA.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(Path(__file__).parent))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--semilla", type=int, default=42)
    ap.add_argument("--sin_texto", action="store_true",
                    help="excluye el TF-IDF del texto web y deja solo tabulares")
    a = ap.parse_args()

    from sklearn.dummy import DummyClassifier
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, f1_score
    from sklearn.neural_network import MLPClassifier
    from sklearn.preprocessing import StandardScaler

    # se reutiliza la preparacion de datos de A3 para que la comparacion sea
    # exactamente sobre las mismas variables que usa el modelo en produccion
    from F3_A3_E14_fase1_encaje import cargar, construir_variables

    print("=" * 74)
    print("A3 · ARBOLES FRENTE A REDES NEURONALES EN DATOS TABULARES")
    print(f"     {VERSION_SCRIPT}  ·  cierra M4 / RQ2b")
    print(f"     texto web: {'NO (solo tabulares)' if a.sin_texto else 'SI'}")
    print("=" * 74)

    print("\nCargando datos...")
    d = cargar()
    val = d[d.nota.notna()].copy()
    print(f"   cuentas valoradas: {len(val):,}".replace(",", "."))
    print("   reparto de notas: " + " · ".join(
        f"{k}:{v}" for k, v in val.nota.value_counts().items()))

    # misma particion que A3: estratificada, semilla fija
    from sklearn.model_selection import train_test_split
    tr, te = train_test_split(val, test_size=0.25, random_state=a.semilla,
                              stratify=val.nota)
    X_tr, X_te = construir_variables(tr, te, usar_texto=not a.sin_texto)

    # Las etiquetas se codifican a entero. No es cosmetico: MLPClassifier con
    # parada temprana falla con etiquetas de texto, porque comprueba si las
    # predicciones son NaN y esa comprobacion no admite cadenas. Se codifican
    # para TODOS los modelos por igual, de modo que la comparacion siga siendo
    # sobre las mismas condiciones.
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder().fit(tr.nota.values)
    y_tr, y_te = le.transform(tr.nota.values), le.transform(te.nota.values)
    print(f"   train {len(tr):,} · test {len(te):,} · variables {X_tr.shape[1]:,}"
          .replace(",", "."))

    # Las redes neuronales EXIGEN escalado; los arboles son indiferentes.
    # Se escala solo para las redes, que es el trato justo: darle a cada
    # familia lo que necesita para rendir al maximo.
    esc = StandardScaler()
    X_tr_esc = esc.fit_transform(X_tr)
    X_te_esc = esc.transform(X_te)

    modelos = [
        ("Clase mayoritaria", DummyClassifier(strategy="most_frequent"), False),
        ("Regresion logistica", LogisticRegression(max_iter=2000, class_weight="balanced"), True),
        ("Random Forest", RandomForestClassifier(
            n_estimators=400, min_samples_leaf=3, class_weight="balanced",
            random_state=a.semilla, n_jobs=-1), False),
        ("Gradient Boosting", GradientBoostingClassifier(
            n_estimators=200, max_depth=3, random_state=a.semilla), False),
        ("Red neuronal densa (2 capas)", MLPClassifier(
            hidden_layer_sizes=(128, 64), max_iter=600, early_stopping=True,
            random_state=a.semilla), True),
        ("Red neuronal profunda (3 capas)", MLPClassifier(
            hidden_layer_sizes=(256, 128, 64), max_iter=600, early_stopping=True,
            random_state=a.semilla), True),
    ]

    # Nota de comparabilidad: esta ejecucion incluye la nota T (administraciones
    # y centros tecnologicos), que E14 excluyo. Son 6 clases frente a 5, de modo
    # que las cifras absolutas NO son comparables con las de E14. La comparacion
    # ENTRE familias, que es el objeto del experimento, si lo es: todas ven
    # exactamente los mismos datos.
    print(f"\n   clases en juego: {len(set(y_tr))}  "
          f"({', '.join(sorted(set(tr.nota)))})")
    print("   AVISO: incluye la nota T, que E14 excluyo. Las cifras absolutas no")
    print("   son comparables con E14; la comparacion entre familias si lo es.")

    print("\n" + "-" * 78)
    print(f"   {'modelo':<32}{'acc':>8}{'F1-macro':>10}{'seg':>8}{'tamano':>18}")
    print("   " + "-" * 74)

    filas = []
    for nombre, m, escalar in modelos:
        Xa, Xb = (X_tr_esc, X_te_esc) if escalar else (X_tr, X_te)
        t0 = time.perf_counter()
        m.fit(Xa, y_tr)
        seg = time.perf_counter() - t0
        p = m.predict(Xb)
        acc = accuracy_score(y_te, p) * 100
        f1 = f1_score(y_te, p, average="macro", zero_division=0) * 100

        # tamano del modelo, para la comparacion de coste
        if hasattr(m, "coefs_"):
            tam = sum(c.size for c in m.coefs_)
            tam_txt = f"{tam:,} pesos".replace(",", ".")
        elif hasattr(m, "estimators_"):
            tam_txt = f"{len(np.ravel(m.estimators_))} arboles"
        elif hasattr(m, "coef_"):
            tam_txt = f"{m.coef_.size:,} coefs".replace(",", ".")
        else:
            tam_txt = "-"

        print(f"   {nombre:<32}{acc:>7.2f}%{f1:>9.2f}%{seg:>8.1f}{tam_txt:>18}")
        filas.append({"modelo": nombre, "accuracy": round(acc, 2),
                      "f1_macro": round(f1, 2), "segundos": round(seg, 1),
                      "tamano": tam_txt})

    e = pd.DataFrame(filas)

    # ------------------------------------------------------------------
    print("\n" + "=" * 74)
    print("CONCLUSION")
    print("=" * 74)
    arboles = e[e.modelo.isin(["Random Forest", "Gradient Boosting"])]
    redes = e[e.modelo.str.startswith("Red neuronal")]
    mejor_arbol = arboles.loc[arboles.f1_macro.idxmax()]
    mejor_red = redes.loc[redes.f1_macro.idxmax()]

    print(f"   mejor arbol : {mejor_arbol.modelo:<32} "
          f"F1 {mejor_arbol.f1_macro:.2f}%  en {mejor_arbol.segundos}s")
    print(f"   mejor red   : {mejor_red.modelo:<32} "
          f"F1 {mejor_red.f1_macro:.2f}%  en {mejor_red.segundos}s")
    dif = mejor_arbol.f1_macro - mejor_red.f1_macro
    print(f"   diferencia  : {dif:+.2f} puntos de F1-macro a favor del "
          f"{'arbol' if dif > 0 else 'RED'}")
    if mejor_red.segundos > 0 and mejor_arbol.segundos > 0:
        print(f"   coste       : la red tarda "
              f"{mejor_red.segundos/mejor_arbol.segundos:.1f}x lo que el arbol")

    print()
    if dif > 0:
        print("   El resultado respalda la eleccion de modelos de arboles para A3:")
        print("   mejor rendimiento, menor coste y decisiones inspeccionables.")
        print("   Es una ablacion que confirma la decision, no que la cuestiona.")
    else:
        print("   OJO: la red neuronal supera al arbol. Hay que revisar la")
        print("   eleccion de modelo de A3 y corregir 06_MODELOS_POR_AGENTE.md.")

    print()
    print("   Conviene no sobreinterpretar: el resultado vale para ESTE conjunto")
    print("   de variables y ESTE volumen (unos 3.000 casos). No demuestra que")
    print("   las redes sean peores en datos tabulares en general, solo que aqui")
    print("   no compensan.")

    ruta = SALIDA / ("a3_arboles_vs_redes" + ("_sin_texto" if a.sin_texto else "") + ".csv")
    e.to_csv(ruta, index=False, encoding="utf-8")
    print(f"\n   Guardado: {ruta.name}")


if __name__ == "__main__":
    main()
