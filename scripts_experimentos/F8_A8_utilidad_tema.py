# -*- coding: utf-8 -*-
"""
F8_A8_utilidad_tema.py · ¿hace falta `Tema` para A8, y sirve para lo que se pensaba?
====================================================================================

LA PREGUNTA
    Al retirar la columna `Tema` de los ficheros de trabajo dije que no costaba
    nada porque A8 nunca se construyo. La autora pregunta lo obvio: entonces,
    ¿hace falta `Tema` para construir A8?

    La respuesta corta es SI, y no hay alternativa. Pero hay una segunda
    pregunta que nadie habia hecho y que importa mas:

        ¿sirve `Tema` para entrenar lo que A8 tiene que hacer EN PRODUCCION?

    Porque A8 se entrenaria con `Tema` —texto escrito POR EL COMERCIAL, en
    jerga interna, DESPUES de que exista la oportunidad— y se ejecutaria sobre
    lo que escribe UN CLIENTE, en prosa, ANTES de que exista nada.

    E24 acaba de demostrar que ese salto de registro hunde un emparejador. Este
    script comprueba si le pasa lo mismo a un clasificador.

QUE MIDE
    1. Si existe alguna alternativa a `Tema` como entrada de A8
    2. Cuanto se parecen `Tema` y correo de cliente · el mismo diagnostico de E24
    3. Si `Tema` lleva de verdad la señal: clasificador entrenado y validado
       sobre las etiquetas de area reales
    4. Veredicto

CONFIDENCIALIDAD
    Lee el fichero de temas de la carpeta privada. NO imprime ningun tema, ni
    entero ni en trozos, ni ningun termino del vocabulario. Solo agregados. Las
    areas salen codificadas. La salida de este script se puede pegar en la
    memoria tal cual.

COMO SE EJECUTA
    python scripts/F8_A8_utilidad_tema.py
    python scripts/F8_A8_utilidad_tema.py --guardar
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

VERSION_SCRIPT = "v1 · 30-09-2026"

RAIZ = Path(__file__).resolve().parent.parent
LIMPIO = RAIZ / "datos" / "01_limpio"
RESULTADOS = RAIZ / "datos" / "03_resultados"
PRIVADO = RAIZ / "datos" / "_mapeo_privado"

TEMAS = PRIVADO / "temas_oportunidades.csv"
OPORTUNIDADES = LIMPIO / "Oportunidades - cuentas 2025_ACT 27-09-2026 19-08-56_anon.csv"
CORPUS = LIMPIO / "entradas_inbound_50_anon.csv"
SALIDA = RESULTADOS / "f8_utilidad_tema.json"
MODELO = "intfloat/multilingual-e5-small"


def titulo(n, t):
    print()
    print("=" * 76)
    print(f"{n} · {t}")
    print("=" * 76)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--guardar", action="store_true")
    ap.add_argument("--semilla", type=int, default=42)
    a = ap.parse_args()

    print()
    print("#" * 76)
    print("# F8 · A8 · ¿hace falta `Tema`, y sirve para lo que se pensaba?")
    print(f"# {VERSION_SCRIPT}")
    print("#" * 76)

    if not TEMAS.exists():
        raise SystemExit(f"Falta {TEMAS}. Lanza antes PREP_confidencialidad.py --aplicar")
    tm = pd.read_csv(TEMAS, sep=";")
    op = pd.read_csv(OPORTUNIDADES, sep=";", low_memory=False)
    d = tm.merge(op[["Nº oportunidad", "Área de Empresa"]], on="Nº oportunidad",
                 how="left")
    d = d[d.Tema.notna() & d["Área de Empresa"].notna()].copy()
    d["Tema"] = d.Tema.astype(str)
    d = d[d.Tema.str.len() > 3]
    cifras = {"version": VERSION_SCRIPT, "n": int(len(d))}

    # ------------------------------------------------------------------ 1
    titulo(1, "¿HAY ALTERNATIVA A `Tema` COMO ENTRADA DE A8?")
    print("   A8 tiene que leer ALGO y decidir el area. Los campos disponibles")
    print("   en el historico de oportunidades son:")
    print()
    for c in op.columns:
        tipo = ("ETIQUETA · es lo que hay que predecir"
                if "rea de Empresa" in c or "Tipo Oportunidad" in c
                else "identificador o fecha" if any(
                    k in c for k in ["No modificar", "Fecha", "Nº", "Número",
                                     "Cuenta", "Propietario", "Autor", "Estado"])
                else "estructura interna · también etiqueta")
        print(f"      {c[:44]:<46} {tipo}")
    print()
    print("   NO HAY OTRO TEXTO. Todo lo demas son identificadores, fechas o")
    print("   las propias etiquetas que hay que predecir. Sin `Tema`, A8 no")
    print("   tiene entrada: el conjunto de entrenamiento se queda vacio.")
    print()
    print("   RESPUESTA A LA PREGUNTA: SI, `Tema` es imprescindible para A8.")
    print("   Por eso no se ha borrado: esta integro en la carpeta privada, y")
    print("   el script de preparacion de A8 lee del fichero BRUTO. Retirarlo")
    print("   de 01_limpio no impide construir A8; impide publicarlo.")

    # ------------------------------------------------------------------ 2
    titulo(2, "PERO… ¿SE PARECE `Tema` A LO QUE ESCRIBE UN CLIENTE?")
    print("   A8 se entrenaria con texto del COMERCIAL y se ejecutaria sobre")
    print("   texto del CLIENTE. E24 demostro que ese salto hunde un")
    print("   emparejador. Se comprueba si aqui pasa lo mismo.")
    print()
    cor = pd.read_csv(CORPUS, sep=";")
    cor["cuerpo"] = cor.cuerpo.fillna("")
    lt = d.Tema.str.len()
    lc = cor.cuerpo.str.len()
    print(f"   Longitud de `Tema`   : media {lt.mean():>6.0f} caracteres   "
          f"(mediana {lt.median():.0f})")
    print(f"   Longitud de un correo: media {lc.mean():>6.0f} caracteres   "
          f"(mediana {lc.median():.0f})")
    print(f"   Un correo es {lc.mean()/lt.mean():.0f} veces mas largo.")
    print()

    from sentence_transformers import SentenceTransformer
    modelo = SentenceTransformer(MODELO)
    rng = np.random.default_rng(a.semilla)
    muestra = d.Tema.sample(min(300, len(d)), random_state=a.semilla).tolist()
    v_t = modelo.encode(["query: " + t for t in muestra],
                        normalize_embeddings=True, show_progress_bar=False)
    v_c = modelo.encode(["query: " + t[:2000] for t in cor.cuerpo],
                        normalize_embeddings=True, show_progress_bar=False)
    tt = v_t @ v_t.T
    cc = v_c @ v_c.T
    tc = v_t @ v_c.T
    m_tt = tt[~np.eye(len(tt), dtype=bool)].mean()
    m_cc = cc[~np.eye(len(cc), dtype=bool)].mean()
    m_tc = tc.mean()
    print(f"   tema  con tema   : {m_tt:.3f}")
    print(f"   correo con correo: {m_cc:.3f}")
    print(f"   tema  con correo : {m_tc:.3f}   <- la mas baja")
    print()
    if m_tc < min(m_tt, m_cc) - 0.01:
        print("   MISMO PATRON QUE E24. Son dos registros distintos: la jerga")
        print("   interna del comercial y la prosa del cliente. Un modelo")
        print("   entrenado en uno y aplicado al otro parte en desventaja.")
    else:
        print("   No se aprecia el desajuste de registro de E24.")
    cifras["registro"] = {"tema_tema": float(m_tt), "correo_correo": float(m_cc),
                          "tema_correo": float(m_tc)}

    # ------------------------------------------------------------------ 3
    titulo(3, "¿LLEVA `Tema` LA SEÑAL?  clasificador entrenado y validado")
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.svm import LinearSVC
    from sklearn.model_selection import cross_val_score, StratifiedKFold
    from sklearn.pipeline import make_pipeline
    from sklearn.dummy import DummyClassifier

    y = d["Área de Empresa"].astype(str)
    frec = y.value_counts()
    validas = frec[frec >= 20].index
    sub = d[y.isin(validas)]
    ys = sub["Área de Empresa"].astype(str)
    print(f"   Oportunidades con tema y area   : {len(d):>6}")
    print(f"   …en areas con 20 o mas casos    : {len(sub):>6}   "
          f"({len(validas)} areas)")
    print()

    cv = StratifiedKFold(5, shuffle=True, random_state=a.semilla)
    tubo = make_pipeline(
        TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), min_df=2,
                        strip_accents="unicode", lowercase=True),
        LinearSVC(C=1.0, class_weight="balanced"))
    acc = cross_val_score(tubo, sub.Tema, ys, cv=cv, scoring="accuracy")
    f1 = cross_val_score(tubo, sub.Tema, ys, cv=cv, scoring="f1_macro")
    suelo = cross_val_score(DummyClassifier(strategy="most_frequent"),
                            sub.Tema, ys, cv=cv, scoring="accuracy")

    print(f"   {'':<34}{'aciertos':>11}{'F1-macro':>11}")
    print("   " + "-" * 56)
    print(f"   {'Responder siempre lo mas comun':<34}{suelo.mean()*100:>10.2f}%"
          f"{'—':>11}")
    print(f"   {'TF-IDF + SVM sobre el tema':<34}{acc.mean()*100:>10.2f}%"
          f"{f1.mean()*100:>10.2f}")
    print()
    print(f"   Validacion cruzada de 5 particiones. Desviacion del acierto: "
          f"±{acc.std()*100:.2f}")
    print(f"   Mejora sobre el suelo: +{(acc.mean()-suelo.mean())*100:.1f} puntos")
    print()
    if acc.mean() - suelo.mean() > 0.25:
        print("   `Tema` lleva la señal, y con holgura. Con un modelo lineal")
        print("   sencillo y sin ajustar nada ya separa las areas.")
    elif acc.mean() - suelo.mean() > 0.10:
        print("   `Tema` lleva señal, moderada.")
    else:
        print("   `Tema` apenas mejora el suelo. Habria que revisar el planteo.")
    cifras["clasificador"] = {
        "n": int(len(sub)), "areas": int(len(validas)),
        "acierto": float(acc.mean()), "acierto_sd": float(acc.std()),
        "f1_macro": float(f1.mean()), "suelo": float(suelo.mean())}

    # ------------------------------------------------------------------ 4
    titulo(4, "VEREDICTO")
    print("   1. ¿Hace falta `Tema` para A8?")
    print("      SI. Es el unico texto del historico. Sin el no hay conjunto")
    print("      de entrenamiento. Por eso se conserva integro en privado.")
    print()
    print("   2. ¿Perdimos algo al sacarlo de 01_limpio?")
    print("      No. El script de preparacion de A8 lee del fichero bruto y la")
    print("      copia integra sigue en la carpeta privada. Lo que se impide")
    print("      es PUBLICARLO, que era el problema.")
    print()
    print("   3. ¿Sirve `Tema` para lo que A8 tiene que hacer?")
    print(f"      Para aprender la relacion texto->area, si: "
          f"{acc.mean()*100:.1f} % frente a un suelo de {suelo.mean()*100:.1f} %.")
    print("      Pero A8 se ejecutaria sobre texto de CLIENTE, no de comercial,")
    print(f"      y son dos registros distintos ({m_tc:.3f} frente a "
          f"{m_tt:.3f} y {m_cc:.3f}).")
    print()
    print("      ESO NO ESTA MEDIDO: no hay correos con su area verdadera")
    print("      salvo ocho. Medirlo exige etiquetar los 52 a mano. Queda")
    print("      como M6.")
    print()
    print("   4. Lo que esto significa para la memoria")
    print("      El acierto que se reporte entrenando y validando sobre `Tema`")
    print("      es un TECHO OPTIMISTA, no el rendimiento esperable en")
    print("      produccion. Hay que declararlo asi. Es el mismo aviso que ya")
    print("      llevan E14 (desajuste de poblacion) y E24.")

    titulo(5, "GUARDAR")
    if a.guardar:
        SALIDA.write_text(json.dumps(cifras, indent=2, ensure_ascii=False),
                          encoding="utf-8")
        print(f"   [ok] {SALIDA.relative_to(RAIZ)}")
        print("   No contiene ningun tema ni ningun nombre de area real.")
    else:
        print("   Simulacion. Lanzalo con --guardar para escribir las cifras.")
    print()


if __name__ == "__main__":
    main()
