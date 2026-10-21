# -*- coding: utf-8 -*-
"""
F7_A7_aporta_algo.py · ¿se puede prescindir de A7?
===================================================

LA PREGUNTA, DE LA AUTORA
    «A7 tal y como está planteado no me sirve de nada: el tema de la
    oportunidad y el correo son muy diferentes, como se vio en A6. ¿Me lo
    puedo cargar y pasar de A6 directamente a A8?»

    Es una pregunta legitima y hay que contestarla con una medicion, no con
    una opinion.

LO QUE HAY QUE SEPARAR, PORQUE SON DOS COSAS
    1. ¿Sirve A7 DONDE ESTA, cualificando correos de cliente?
    2. ¿Sirve el texto PARA ALGO, aunque sea en otro sitio?

    La primera ya tiene respuesta y es desfavorable: A7 se entrena con el
    campo `Tema` —cuatro o cinco palabras del comercial— y se aplicaria
    sobre correos de cliente de 154 palabras de media. A6 midio esa misma
    frontera para el enrutado y costo 4,9 puntos; para A7 **no se puede
    medir**, porque ningun correo trae su resultado comercial.

    La segunda no se habia planteado, y es la que decide. A7 y A9 predicen
    LO MISMO —si la oportunidad se gana— con datos distintos: A7 desde el
    texto, A9 desde los campos. Si el texto aporta algo que los campos no
    tienen, A7 no sobra: cambia de sitio.

QUE HACE ESTE SCRIPT
    Entrena A9 con sus campos, y luego A9 mas la puntuacion de texto de A7,
    sobre las MISMAS oportunidades y con la MISMA particion temporal.
    Compara las dos con un contraste emparejado.

    Si la diferencia no se separa del cero, el texto no aporta y A7 se
    puede retirar. Si se separa, A7 vale pero como variable de A9, no como
    fase aparte.

COMO SE EJECUTA
    python scripts/F7_A7_aporta_algo.py
    python scripts/F7_A7_aporta_algo.py --guardar
"""

import json
import sys
import unicodedata
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

warnings.filterwarnings("ignore")

VERSION_SCRIPT = "v1 · 06-10-2026"
SEMILLA = 42

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "datos" / "00_bruto"
LIMPIO = RAIZ / "datos" / "01_limpio"
PRIV = RAIZ / "datos" / "_mapeo_privado"
RES = RAIZ / "datos" / "03_resultados"

F_OPORT = BRUTO / "Oportunidades - cuentas 2025_ACT 27-09-2026 19-08-56.xlsx"
TEMAS = PRIV / "temas_oportunidades.csv"

TRIM_TRAIN_FIN, TRIM_TEST = "2026Q1", "2026Q2"


def sin_tildes(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t).lower())
                   if unicodedata.category(c) != "Mn")


def auc(punt, pos):
    p, y = np.asarray(punt, float), np.asarray(pos, bool)
    n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0:
        return np.nan
    o = np.argsort(p, kind="mergesort")
    r = np.empty(len(p), float)
    r[o] = np.arange(1, len(p) + 1)
    for v in np.unique(p):
        ig = p == v
        if ig.sum() > 1:
            r[ig] = r[ig].mean()
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def compara(a, b, y, n=2000, semilla=SEMILLA):
    """Diferencia de AUC entre dos predictores sobre LOS MISMOS casos."""
    a, b, y = np.asarray(a, float), np.asarray(b, float), np.asarray(y, bool)
    rng = np.random.default_rng(semilla)
    dif = auc(a, y) - auc(b, y)
    ms = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if y[i].all() or (~y[i]).all():
            continue
        ms.append(auc(a[i], y[i]) - auc(b[i], y[i]))
    m = np.array(ms)
    lo, hi = np.percentile(m, [2.5, 97.5])
    p = 2 * min((m <= 0).mean(), (m >= 0).mean())
    return dif, float(lo), float(hi), float(min(1.0, p))


def matriz(d, variables):
    X = pd.DataFrame(index=d.index)
    for v in variables:
        s = d[v]
        if s.dtype.kind in "ifb":
            X[v] = s.astype(float)
            X[v + "__falta"] = s.isna().astype(float)
            X[v] = X[v].fillna(s.median() if s.notna().any() else 0.0)
        else:
            s = s.astype(str).fillna("(falta)").replace("nan", "(falta)")
            frec = s.value_counts()
            s = s.where(s.map(frec) >= 15, "(poco frecuente)")
            for val in sorted(s.unique()):
                X[f"{v}={val}"] = (s == val).astype(float)
    return X


# LAS MISMAS VARIABLES QUE A9, no un subconjunto.
#
# La primera version de este script uso solo siete y el texto aparecia
# aportando +0,044. Pero A9 usa diecisiete, incluidas el historial de la
# cuenta y sus datos: si esas ya capturan lo que el texto anade, la mejora
# se evapora. Comparar contra un A9 recortado habria dado una recomendacion
# equivocada.
VARIABLES = ["Tipo Oportunidad", "Tipología de proyecto", "Línea Tecnológica",
             "Sublínea Tecnológica", "Área de Empresa", "Propietario", "mes",
             "ops_previas", "cerradas_previas", "tasa_previa",
             "pais", "provincia", "tamano", "cliente", "asociado",
             "atractividad", "sector_agrupado"]


def titulo(n, t):
    print()
    print("=" * 76)
    print(f"PASO {n} · {t}")
    print("=" * 76)


def main():
    guardar = "--guardar" in sys.argv

    print()
    print("#" * 76)
    print("# F7 · A7 · ¿aporta algo el texto, o se puede prescindir?")
    print(f"# {VERSION_SCRIPT}")
    print("#" * 76)

    # ------------------------------------------------------------------ 1
    titulo(1, "LAS MISMAS OPORTUNIDADES, CON Y SIN TEXTO")
    # El export de oportunidades YA trae la columna `Tema`: no hace falta
    # cruzarlo con el fichero privado, y cruzarlo duplicaba la columna.
    op = pd.read_excel(F_OPORT)
    op.columns = [c.strip() for c in op.columns]
    d = op[op.Estado.isin(["Lograda", "Perdida"])].copy()
    d = d.dropna(subset=["Tema"])
    d["gana"] = (d.Estado == "Lograda").astype(int)
    d["trim"] = d["Fecha de creación"].dt.to_period("Q").astype(str)
    d["mes"] = d["Fecha de creación"].dt.month
    d["txt"] = d.Tema.astype(str).map(sin_tildes)
    d = d[d.txt.str.len() >= 3].reset_index(drop=True)

    # el historial de la cuenta, HACIA ATRAS: solo con las creadas antes
    d = d.sort_values("Fecha de creación").reset_index(drop=True)
    d["cta"] = d["Cuenta"].astype(str).str.strip().str.lower()
    g = d.groupby("cta")
    d["ops_previas"] = g.cumcount()
    ganadas = g["gana"].cumsum() - d["gana"]
    cerradas = g["gana"].cumcount()
    d["cerradas_previas"] = cerradas
    d["tasa_previa"] = np.where(cerradas > 0, ganadas / cerradas.replace(0, np.nan),
                                np.nan)

    # y lo que se sabe de la cuenta
    trozos = []
    for part in ("train", "val", "test"):
        f = RAIZ / "datos" / "02_derivado" / f"cuentas_{part}.csv"
        if f.exists():
            trozos.append(pd.read_csv(f, usecols=lambda c: c in (
                "empresa", "pais", "provincia", "tamano", "cliente",
                "asociado", "atractividad", "sector_agrupado")))
    if trozos:
        cu = pd.concat(trozos, ignore_index=True)
        cu["cta"] = cu.empresa.astype(str).str.strip().str.lower()
        cu = cu.drop_duplicates("cta").drop(columns=["empresa"])
        antes = len(d)
        d = d.merge(cu, on="cta", how="left")
        assert len(d) == antes, "el cruce con cuentas ha duplicado filas"
        print(f"   …cruzadas con su cuenta          : "
              f"{d.provincia.notna().sum():>6}")
    else:
        for c_ in ("pais", "provincia", "tamano", "cliente", "asociado",
                   "atractividad", "sector_agrupado"):
            d[c_] = np.nan

    tr = d.trim <= TRIM_TRAIN_FIN
    te = d.trim == TRIM_TEST
    y = d.gana.values
    print(f"   Oportunidades cerradas con texto : {len(d):>6}")
    print(f"   Entrenamiento (<= {TRIM_TRAIN_FIN})        : {tr.sum():>6}")
    print(f"   Prueba ({TRIM_TEST})                   : {te.sum():>6}")
    suelo = 100 * max(y[te].mean(), 1 - y[te].mean())
    print(f"   Suelo en prueba                  : {suelo:>6.1f} %")

    # ------------------------------------------------------------------ 2
    titulo(2, "TRES PREDICTORES SOBRE LOS MISMOS CASOS")
    X = matriz(d, VARIABLES)

    # a · solo los campos, como A9
    m_a = RandomForestClassifier(n_estimators=400, min_samples_leaf=5,
                                 random_state=SEMILLA, n_jobs=-1)
    m_a.fit(X[tr], y[tr])
    p_a = m_a.predict_proba(X[te])[:, 1]

    # b · solo el texto, como A7
    vec = TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), min_df=3,
                          max_features=60000)
    Xt_tr = vec.fit_transform(d.txt[tr])
    Xt_te = vec.transform(d.txt[te])
    m_b = LogisticRegression(max_iter=3000, class_weight="balanced")
    m_b.fit(Xt_tr, y[tr])
    p_b = m_b.predict_proba(Xt_te)[:, 1]

    # c · los campos MAS la puntuacion de texto
    #
    # La puntuacion de texto para el ENTRENAMIENTO se saca por validacion
    # cruzada, no del mismo modelo que ya vio esas filas: si no, el bosque
    # aprenderia de una variable que en entrenamiento es casi perfecta y en
    # prueba no, y la comparacion saldria falsa a favor del texto.
    from sklearn.model_selection import cross_val_predict
    p_txt_tr = cross_val_predict(
        LogisticRegression(max_iter=3000, class_weight="balanced"),
        Xt_tr, y[tr], cv=5, method="predict_proba")[:, 1]
    Xc_tr = X[tr].copy()
    Xc_tr["txt"] = p_txt_tr
    Xc_te = X[te].copy()
    Xc_te["txt"] = p_b
    m_c = RandomForestClassifier(n_estimators=400, min_samples_leaf=5,
                                 random_state=SEMILLA, n_jobs=-1)
    m_c.fit(Xc_tr, y[tr])
    p_c = m_c.predict_proba(Xc_te)[:, 1]

    print()
    print(f"   {'predictor':<36}{'AUC':>8}{'acierto':>10}")
    print("   " + "-" * 56)
    for et, p in (("A9 · solo los campos", p_a),
                  ("A7 · solo el texto", p_b),
                  ("Los campos MAS el texto", p_c)):
        ac = 100 * ((p >= 0.5) == y[te].astype(bool)).mean()
        print(f"   {et:<36}{auc(p, y[te]):>8.3f}{ac:>9.1f} %")

    # ------------------------------------------------------------------ 3
    titulo(3, "¿APORTA EL TEXTO ALGO QUE LOS CAMPOS NO TENGAN?")
    dif, lo, hi, pv = compara(p_c, p_a, y[te])
    print(f"   Campos + texto frente a solo campos")
    print(f"   Diferencia de AUC : {dif:+.3f}   IC 95 % [{lo:+.3f}, {hi:+.3f}]"
          f"   p ~ {pv:.3f}")
    print()
    aporta = lo > 0
    if aporta:
        v = ("EL TEXTO APORTA. El intervalo no toca el cero, asi que A7 no "
             "sobra: lo que sobra es su sitio.")
    else:
        v = ("EL TEXTO NO APORTA NADA MEDIBLE sobre los campos. El intervalo "
             "cruza el cero.")
    print(f"   {v}")

    # y al reves: ¿aportan los campos sobre el texto?
    dif2, lo2, hi2, pv2 = compara(p_c, p_b, y[te])
    print()
    print(f"   Campos + texto frente a solo texto")
    print(f"   Diferencia de AUC : {dif2:+.3f}   IC 95 % [{lo2:+.3f}, {hi2:+.3f}]"
          f"   p ~ {pv2:.3f}")

    # ------------------------------------------------------------------ 4
    titulo(4, "QUE SIGNIFICA ESTO PARA LA ARQUITECTURA")
    print("   LO QUE YA SE SABIA, Y JUEGA EN CONTRA DE A7 DONDE ESTA:")
    print("   · Se entrena con `Tema`, de 4-5 palabras escritas por el")
    print("     comercial, y se aplicaria sobre correos de 154 palabras")
    print("     escritos por el cliente.")
    print("   · A6 midio esa frontera para el enrutado: cuesta 4,9 puntos.")
    print("     Para A7 NO SE PUEDE MEDIR, porque ningun correo trae su")
    print("     resultado comercial. Es una limitacion que no se cierra.")
    print("   · Al pasarlo por los 105 correos, 104 de 105 caen en las dos")
    print("     bandas bajas. El modelo no distingue sobre ese texto.")
    print()
    if aporta:
        print("   LO QUE ESTA MEDICION ANADE:")
        print("   El texto SI tiene senal que los campos no capturan. Asi que")
        print("   la respuesta no es retirar A7 sino MOVERLO: deja de ser una")
        print("   fase que cualifica correos y pasa a ser una variable mas de")
        print("   A9, que es donde hay resultado real contra el que validar.")
    else:
        print("   LO QUE ESTA MEDICION ANADE:")
        print("   El texto no aporta nada sobre los campos. Sumado a lo")
        print("   anterior, A7 no sostiene su sitio en la arquitectura.")
        print()
        print("   PERO NO SE BORRA SIN MAS: su resultado negativo —que contar")
        print("   criterios de cualificacion no ordena— sigue siendo un")
        print("   hallazgo, y el marco de los siete criterios es parte del")
        print("   diseno. Lo que cambia es que pasa de agente construido a")
        print("   agente evaluado y descartado CON MOTIVO MEDIDO, que es")
        print("   mejor defensa que un agente que no se usa.")

    if not guardar:
        print()
        print("   Simulacion: no se ha escrito nada. Usa --guardar.")
        print()
        return

    salida = {
        "experimento": "E36", "pregunta": "¿aporta A7 algo que A9 no tenga?",
        "version": VERSION_SCRIPT,
        "n": {"total": int(len(d)), "entrena": int(tr.sum()),
              "prueba": int(te.sum())},
        "suelo": suelo,
        "auc": {"solo_campos": auc(p_a, y[te]), "solo_texto": auc(p_b, y[te]),
                "campos_mas_texto": auc(p_c, y[te])},
        "texto_sobre_campos": {"diferencia": dif, "ic": [lo, hi], "p": pv,
                               "aporta": bool(aporta)},
        "campos_sobre_texto": {"diferencia": dif2, "ic": [lo2, hi2], "p": pv2},
        "veredicto": v,
    }
    RES.mkdir(parents=True, exist_ok=True)
    f = RES / "a7_aporta_algo.json"
    f.write_text(json.dumps(salida, ensure_ascii=False, indent=1, default=float),
                 encoding="utf-8")
    print()
    print(f"   [ok] {f.name}")
    print()


if __name__ == "__main__":
    main()
