# -*- coding: utf-8 -*-
"""
F6_A6_distinguir_solicitud.py · E41 · ¿se puede distinguir de verdad una
solicitud de trabajo de lo que no lo es?
=========================================================================

DE DONDE SALE LA PREGUNTA
    La cuarta pieza de A6 tiene un AUC de 0,919 y, puesta a decidir en el
    circuito de recepcion (E40), no sirve: dos solicitudes reales puntuan
    por encima de los catorce correos no comerciales, y ahi es justo donde
    un umbral tiene que cortar.

    La conclusion de E40 fue «no se usa como puerta». Esto va un paso mas
    alla: ¿se puede hacer mejor, aunque sea dejando una ZONA DE DUDA?

QUE SE PRUEBA, Y POR QUE CADA COSA
    V1 · palabras                 lo que hay hoy: TF-IDF de 1 y 2 palabras
    V2 · palabras + caracteres    los trozos de palabra arreglaron el
                                  clasificador del tipo de servicio (E38),
                                  y aqui hay dos idiomas mezclados
    V3 · sobre el telegrama       el extracto que arreglo el cambio de
                                  poblacion en E38 y en E40
    V4 · representaciones densas  e5-small, el mismo modelo del
                                  emparejamiento de A5, ya descargado. Con
                                  CATORCE ejemplos negativos, un modelo que
                                  ya sabe espanol e ingles parte con
                                  ventaja sobre uno que aprende de cero
    V5 · parecido a descripciones SIN ENTRENAR NADA: se describe en una
                                  frase que es una solicitud y que no lo
                                  es, y se mide a cual se parece cada
                                  correo. No puede sobreajustar a catorce
                                  casos porque no los mira
    V6 · densas + palabras        la media de V2 y V4
    V7 · vecinos mas cercanos     con pocos datos suele aguantar mejor que
                                  un modelo lineal

LO QUE DE VERDAD SE MIDE, QUE NO ES EL AUC
    El AUC ya era bueno y no servia. Lo que decide si esto es utilizable
    son las dos BANDAS LIMPIAS:

      · cuantas SOLICITUDES se pueden certificar sin colar ni un correo
        no comercial  -> esas el sistema las puede tratar solo
      · cuantos NO COMERCIALES se cazan antes del primer falso positivo
        -> esos se pueden apartar solos

    Lo que queda en medio es la ZONA DE DUDA, y va a una persona. Esa es
    la respuesta honesta a «aunque sea con un porcentaje de duda».

UNA ADVERTENCIA QUE HAY QUE LEER ANTES DE LAS CIFRAS
    Hay CATORCE correos no comerciales. Con catorce casos cualquier cifra
    baila, asi que la validacion cruzada se repite cinco veces con
    semillas distintas y se da la desviacion. Y al comparar siete
    variantes, la mejor lo es en parte por suerte: por eso se mira que la
    ventaja aguante en las cinco repeticiones, y no solo en el promedio.

COMO SE EJECUTA
    python scripts/F6_A6_distinguir_solicitud.py
    python scripts/F6_A6_distinguir_solicitud.py --guardar
"""

import json
import sys
import unicodedata
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import FeatureUnion

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from F8_A8_briefing_traspaso import (TELEGRAMA_PALABRAS,  # noqa: E402
                                     TELEGRAMA_TOPE_IDF)
from F8_A8_tema_modelo import (cortesia_comun, entrena_tipo,  # noqa: E402
                               hacer_telegrama, idf_de)

VERSION_SCRIPT = "v1 · 07-10-2026"
SEMILLA = 42
REPETICIONES = 5
MODELO_DENSO = "intfloat/multilingual-e5-small"

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "datos" / "00_bruto"
LIMPIO = RAIZ / "datos" / "01_limpio"
RES = RAIZ / "datos" / "03_resultados"
CORPUS = LIMPIO / "entradas_inbound_50_anon.csv"
ETIQUETAS = LIMPIO / "etiquetas_comercial_A6.csv"
OPORT = BRUTO / "Oportunidades - cuentas 2025_ACT 27-09-2026 19-08-56.xlsx"

# Las descripciones de V5. No son una lista de palabras clave —eso ya se
# probo y fue el error X25— sino dos frases que describen cada clase, que
# es lo que un modelo de representaciones sabe comparar.
ES_SOLICITUD = [
    "query: Un cliente pide un presupuesto para hacer ensayos de laboratorio "
    "sobre un envase o un material.",
    "query: Una empresa solicita asesoramiento tecnico o un estudio sobre "
    "normativa de envases, reciclabilidad o seguridad alimentaria.",
    "query: Nos piden informacion y precio para un servicio tecnico concreto "
    "sobre un producto suyo.",
]
NO_ES_SOLICITUD = [
    "query: Invitacion a un evento, una jornada, un congreso o un webinar.",
    "query: Una empresa nos ofrece sus productos o servicios como proveedor, "
    "o nos pide colaborar en un proyecto.",
    "query: Mensaje administrativo, factura, oferta de empleo, encuesta o "
    "comunicacion que no pide ningun trabajo tecnico.",
]


def sin_tildes(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t).lower())
                   if unicodedata.category(c) != "Mn")


def auc(punt, pos):
    p, y = np.asarray(punt, float), np.asarray(pos, bool)
    n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0:
        return np.nan
    orden = np.argsort(p, kind="mergesort")
    r = np.empty(len(p), float)
    r[orden] = np.arange(1, len(p) + 1)
    for v in np.unique(p):
        ig = p == v
        if ig.sum() > 1:
            r[ig] = r[ig].mean()
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def bandas(punt, y):
    """Las dos bandas limpias, que es lo que decide si esto es utilizable.

    ABAJO: cuantas solicitudes quedan por debajo del no comercial de
    puntuacion mas baja. Esas se pueden certificar como solicitudes.
    ARRIBA: cuantos no comerciales quedan por encima de la solicitud mejor
    puntuada. Esos se pueden apartar sin tocar nada bueno.
    """
    p, y = np.asarray(punt, float), np.asarray(y, bool)
    limpio_abajo = int((p[~y] < p[y].min()).sum())
    limpio_arriba = int((p[y] > p[~y].max()).sum())
    return limpio_abajo, limpio_arriba


def titulo(n, t):
    print()
    print("=" * 76)
    print(f"PASO {n} · {t}")
    print("=" * 76)


def main():
    guardar = "--guardar" in sys.argv

    print()
    print("#" * 76)
    print("# F6 · E41 · ¿se puede distinguir una solicitud de lo que no lo es?")
    print(f"# {VERSION_SCRIPT}")
    print("#" * 76)

    # ------------------------------------------------------------------ 1
    titulo(1, "LOS DATOS, Y POR QUE SON POCOS")
    d = pd.read_csv(CORPUS, sep=";")
    d["cuerpo"] = d.cuerpo.fillna("").astype(str)
    d["norm"] = d.cuerpo.map(sin_tildes)
    et = pd.read_csv(ETIQUETAS, sep=";")
    et["no"] = et.categoria.astype(str).str.upper().str.contains("NO")
    d = d.merge(et[["id", "no"]], on="id", how="left")
    y = d["no"].astype(int).values
    print(f"   Correos            : {len(d)}")
    print(f"   NO comerciales     : {int(y.sum())}")
    print(f"   Solicitudes        : {int((1 - y).sum())}")
    print()
    print("   Son catorce negativos. Todo lo que sigue hay que leerlo con")
    print("   esa cifra delante: no da para afinar, da para ver si alguna")
    print("   via es claramente mejor que las demas.")

    # ------------------------------------------------------------------ 2
    titulo(2, "LAS ENTRADAS QUE SE PRUEBAN")
    op = pd.read_excel(OPORT)
    op.columns = [c.strip() for c in op.columns]
    vec_t, _, _, _ = entrena_tipo(op)
    idf_t = idf_de(vec_t, TELEGRAMA_TOPE_IDF)
    prohibidas = cortesia_comun(d.norm)
    d["telegrama"] = d.cuerpo.map(
        lambda x: hacer_telegrama(x, idf_t, TELEGRAMA_PALABRAS, prohibidas))
    print(f"   Correo entero y telegrama de {TELEGRAMA_PALABRAS} palabras, listos")

    print("   Calculando representaciones densas con e5-small (sin GPU)...")
    from sentence_transformers import SentenceTransformer
    emb = SentenceTransformer(MODELO_DENSO)
    V = emb.encode(["query: " + t for t in d.cuerpo], normalize_embeddings=True,
                   show_progress_bar=False)
    print(f"   {V.shape[0]} correos en {V.shape[1]} dimensiones")

    # V5 · parecido a las descripciones, sin entrenar
    Ps = emb.encode(ES_SOLICITUD, normalize_embeddings=True)
    Pn = emb.encode(NO_ES_SOLICITUD, normalize_embeddings=True)
    sin_entrenar = (V @ Pn.T).max(axis=1) - (V @ Ps.T).max(axis=1)

    # ------------------------------------------------------------------ 3
    titulo(3, "SIETE VIAS, CINCO REPETICIONES CADA UNA")

    def palabras():
        return TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), min_df=1,
                               max_features=20000)

    def pal_car():
        return FeatureUnion([
            ("pal", TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2),
                                    min_df=1, max_features=20000)),
            ("car", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5),
                                    sublinear_tf=True, min_df=2,
                                    max_features=60000))])

    def corre(fn, semilla):
        """Una pasada de validacion cruzada; devuelve la puntuacion de cada
        correo, sacada siempre de un modelo que no lo habia visto."""
        p = np.zeros(len(y), float)
        cv = StratifiedKFold(5, shuffle=True, random_state=semilla)
        for tr, te in cv.split(np.zeros(len(y)), y):
            p[te] = fn(tr, te)
        return p

    def texto_fn(getvec, col):
        def f(tr, te):
            v = getvec()
            X = d[col].values
            Xtr = v.fit_transform(X[tr])
            clf = LogisticRegression(max_iter=2000, class_weight="balanced")
            clf.fit(Xtr, y[tr])
            return clf.predict_proba(v.transform(X[te]))[:, 1]
        return f

    def denso_fn(tr, te):
        clf = LogisticRegression(max_iter=3000, class_weight="balanced", C=4.0)
        clf.fit(V[tr], y[tr])
        return clf.predict_proba(V[te])[:, 1]

    def vecinos_fn(tr, te):
        k = KNeighborsClassifier(n_neighbors=3, metric="cosine", weights="distance")
        k.fit(V[tr], y[tr])
        return k.predict_proba(V[te])[:, 1]

    VIAS = [
        ("V1 · palabras (lo de hoy)", texto_fn(palabras, "norm")),
        ("V2 · palabras + caracteres", texto_fn(pal_car, "norm")),
        ("V3 · sobre el telegrama", texto_fn(pal_car, "telegrama")),
        ("V4 · representaciones densas", denso_fn),
        ("V7 · vecinos mas cercanos", vecinos_fn),
    ]

    res = {}
    punt_media = {}
    for nombre, fn in VIAS:
        aucs, ab, ar = [], [], []
        acum = np.zeros(len(y), float)
        for i in range(REPETICIONES):
            p = corre(fn, SEMILLA + i)
            acum += p
            aucs.append(auc(p, y))
            a, b = bandas(p, y)
            ab.append(a)
            ar.append(b)
        punt_media[nombre] = acum / REPETICIONES
        res[nombre] = dict(auc=float(np.mean(aucs)), auc_sd=float(np.std(aucs)),
                           abajo=float(np.mean(ab)), arriba=float(np.mean(ar)),
                           aucs=[float(x) for x in aucs])

    # V5 no se entrena: una sola pasada
    a5, b5 = bandas(sin_entrenar, y)
    res["V5 · parecido a descripciones"] = dict(
        auc=auc(sin_entrenar, y), auc_sd=0.0, abajo=float(a5), arriba=float(b5),
        aucs=[auc(sin_entrenar, y)])
    punt_media["V5 · parecido a descripciones"] = sin_entrenar

    # V6 · la media de V2 y V4, cada una normalizada a su rango
    def norm01(x):
        return (x - x.min()) / (x.max() - x.min() + 1e-12)
    mezcla = (norm01(punt_media["V2 · palabras + caracteres"])
              + norm01(punt_media["V4 · representaciones densas"])) / 2
    a6, b6 = bandas(mezcla, y)
    res["V6 · densas + palabras"] = dict(auc=auc(mezcla, y), auc_sd=0.0,
                                         abajo=float(a6), arriba=float(b6),
                                         aucs=[auc(mezcla, y)])
    punt_media["V6 · densas + palabras"] = mezcla

    orden = ["V1 · palabras (lo de hoy)", "V2 · palabras + caracteres",
             "V3 · sobre el telegrama", "V4 · representaciones densas",
             "V5 · parecido a descripciones", "V6 · densas + palabras",
             "V7 · vecinos mas cercanos"]
    print()
    print(f"   {'via':<32}{'AUC':>8}{'±':>7}{'certifica':>11}{'aparta':>8}")
    print("   " + "-" * 74)
    for k in orden:
        r = res[k]
        print(f"   {k:<32}{r['auc']:>8.3f}{r['auc_sd']:>7.3f}"
              f"{r['abajo']:>10.0f} {r['arriba']:>8.0f}")
    print()
    print("   CERTIFICA · solicitudes que quedan por debajo del no comercial")
    print("               mas bajo: el sistema puede tratarlas solo")
    print("   APARTA    · no comerciales por encima de la solicitud mas alta")
    print(f"   De {int((1-y).sum())} solicitudes y {int(y.sum())} no comerciales.")

    # ------------------------------------------------------------------ 4
    titulo(4, "LA MEJOR VIA, Y SI LA VENTAJA AGUANTA")
    mejor = max(orden, key=lambda k: res[k]["auc"])
    base = "V1 · palabras (lo de hoy)"
    print(f"   Mejor AUC: {mejor} con {res[mejor]['auc']:.3f}")
    print(f"   Hoy      : {base} con {res[base]['auc']:.3f}")
    if len(res[mejor]["aucs"]) == REPETICIONES and len(res[base]["aucs"]) == REPETICIONES:
        gana = sum(1 for a, b in zip(res[mejor]["aucs"], res[base]["aucs"]) if a > b)
        print(f"   Gana en {gana} de las {REPETICIONES} repeticiones")
        if gana < REPETICIONES:
            print("   NO en todas: la ventaja no es firme con estos datos.")
    print()
    print("   Con siete vias y catorce negativos, la mejor lo es en parte por")
    print("   suerte. Lo que importa no es cual gana por tres milesimas, sino")
    print("   si ALGUNA consigue bandas limpias grandes, que es lo utilizable.")

    # ------------------------------------------------------------------ 5
    titulo(5, "LA ZONA DE DUDA, QUE ES LA RESPUESTA PRACTICA")
    p = punt_media[mejor]
    orden_p = np.argsort(p)
    ab, ar = bandas(p, y)
    print(f"   Con {mejor}:")
    print()
    print(f"   {'zona':<34}{'correos':>9}{'contenido':>26}")
    print("   " + "-" * 74)
    print(f"   {'ES SOLICITUD, sin duda':<34}{ab:>9}"
          f"{'0 no comerciales':>26}")
    print(f"   {'DUDA · la mira una persona':<34}{len(y) - ab - ar:>9}"
          f"{f'{int(y.sum()) - ar} no comerciales dentro':>26}")
    print(f"   {'NO ES SOLICITUD, sin duda':<34}{ar:>9}"
          f"{'0 solicitudes':>26}")
    print()
    if ab + ar == 0:
        print("   NO HAY NINGUNA BANDA LIMPIA. El sistema no puede certificar")
        print("   nada por su cuenta, ni en un sentido ni en el otro.")
    else:
        print(f"   El sistema decide solo en {ab + ar} de {len(y)} correos "
              f"({100*(ab+ar)/len(y):.0f} %)")
        print(f"   y pide ayuda en {len(y) - ab - ar}. Esa es la «zona de duda»:")
        print(f"   no es un fallo, es el alcance medido de la pieza.")

    # ---------------------------------------------------------------- 5b
    titulo(6, "LA BANDA CON TOLERANCIA · «UN PORCENTAJE LOGICO DE DUDA»")
    print("   Exigir CERO contaminacion es brutal con catorce negativos:")
    print("   basta un correo raro para vaciar la banda. La pregunta util es")
    print("   otra: si se miran los K peor puntuados, ¿cuantos son de verdad")
    print("   no comerciales y cuantas solicitudes se tocan?")
    print()
    print(f"   {'los K mas sospechosos':<24}{'no comerciales':>16}"
          f"{'solicitudes':>13}{'aciertos':>11}")
    print("   " + "-" * 70)
    orden_desc = np.argsort(-p)
    tabla_k = []
    for k in (5, 10, 14, 20, 25, 30):
        sel = orden_desc[:k]
        nn = int(y[sel].sum())
        tabla_k.append({"k": k, "no_comerciales": nn, "solicitudes": k - nn,
                        "precision": 100 * nn / k})
        print(f"   {f'los {k} primeros':<24}{nn:>16}{k - nn:>13}"
              f"{100 * nn / k:>10.0f} %")
    print()
    print(f"   De los {int(y.sum())} no comerciales que hay en total.")
    print()
    # la banda mas grande que no se come mas de una solicitud, y la de dos
    for tope in (1, 2, 3):
        mejor_k = 0
        for k in range(1, len(y) + 1):
            if int((1 - y[orden_desc[:k]]).sum()) <= tope:
                mejor_k = k
        caza = int(y[orden_desc[:mejor_k]].sum()) if mejor_k else 0
        print(f"   Tolerando {tope} solicitud{'es' if tope > 1 else ''} tocada"
              f"{'s' if tope > 1 else ''}: se apartan {mejor_k} correos y")
        print(f"      se cazan {caza} de los {int(y.sum())} no comerciales")
    print()
    print("   ASI ES COMO SE USA: no como puerta que tira correos, sino como")
    print("   una lista corta ordenada por sospecha. Quien la mira confirma")
    print("   de un vistazo, y el resto del circuito sigue su camino.")

    if not guardar:
        print()
        print("   Simulacion: no se ha escrito nada. Usa --guardar.")
        print()
        return

    salida = {
        "experimento": "E41", "agente": "A6",
        "pregunta": "¿se puede distinguir una solicitud de trabajo de lo que "
                    "no lo es, aunque sea dejando una zona de duda?",
        "version": VERSION_SCRIPT,
        "n": int(len(y)), "n_no_comerciales": int(y.sum()),
        "repeticiones": REPETICIONES,
        "vias": {k: res[k] for k in orden},
        "mejor": mejor,
        "banda_con_tolerancia": tabla_k,
        "zona_de_duda": {"certifica_solicitud": int(ab),
                         "aparta_no_comercial": int(ar),
                         "a_una_persona": int(len(y) - ab - ar)},
        "advertencia": "catorce negativos; las cifras bailan y la mejor via "
                       "lo es en parte por azar",
    }
    RES.mkdir(parents=True, exist_ok=True)
    f = RES / "a6_distinguir_solicitud.json"
    f.write_text(json.dumps(salida, ensure_ascii=False, indent=1, default=float),
                 encoding="utf-8")
    pd.DataFrame({"id": d.id, "no_comercial_real": y,
                  **{k: punt_media[k] for k in orden}}).to_csv(
        RES / "a6_distinguir_por_correo.csv", sep=";", index=False,
        encoding="utf-8")
    print()
    print(f"   [ok] {f.name}  ·  a6_distinguir_por_correo.csv")
    print()


if __name__ == "__main__":
    main()
