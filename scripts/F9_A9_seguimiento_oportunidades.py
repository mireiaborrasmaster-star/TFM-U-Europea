# -*- coding: utf-8 -*-
"""
F9_A9_seguimiento_oportunidades.py · A8 · ¿se va a ganar esta oportunidad?
===========================================================================

QUE ES A8
    El agente de la fase 9: una vez la oportunidad esta creada, estimar la
    probabilidad de que acabe ganandose y cuanto va a tardar, para que el
    comercial sepa a que dedicar el tiempo y cual esta atascada.

LA FORMA DEL EXPERIMENTO, Y POR QUE ESTA
    Es la misma que el proyecto de prevision de ventas de la autora, que no
    entrena modelo alguno: mide la CALIBRACION (Brier) y la DISCRIMINACION
    (AUC) de la columna `Probabilidad` que rellena la persona, con
    intervalos por bootstrap.

    Aqui se anade la pieza que faltaba: un modelo que compite contra esa
    persona con esas mismas dos metricas. El rival no es una referencia
    inventada, SALE MEDIDO DEL PROPIO CRM.

    Son dos preguntas distintas y conviene no confundirlas:
      · CALIBRACION  : cuando se dice 50 %, ¿se gana el 50 %?
      · DISCRIMINACION: ¿se ganan mas las que llevan mas %, ordenadas?
    Se puede ordenar bien y estar mal calibrado. Entonces el numero sirve,
    pero hay que traducirlo antes de usarlo.

DECISIONES QUE CONVIENE CONOCER
    1. SIN IMPORTES. Decision D13 del trabajo. No entra ninguna variable
       monetaria y no se imprime ninguna cifra de euros. Como medida de
       tamano se usan las HORAS presupuestadas, que no son dinero.

    2. PARTICION TEMPORAL, no aleatoria. Se entrena con lo viejo y se
       prueba con lo nuevo, que es como funcionaria de verdad. Una
       particion aleatoria dejaria ver el futuro.

    3. EL ULTIMO TRIMESTRE SE APARTA. En 2026Q3 hay 303 ganadas y solo 71
       perdidas, porque las recientes aun no se han resuelto. Meterlo
       inflaria el resultado. Se evalua aparte y con el sesgo declarado.

    4. LA PROBABILIDAD DEL COMERCIAL ESTA PARCIALMENTE CONTAMINADA: hay
       355 ofertas con exactamente 100 %, y 346 de ellas se ganaron, o sea
       que ese valor se escribe DESPUES de saber el resultado. Se usa la
       probabilidad de la PRIMERA oferta de cada oportunidad y se mide
       cuanto cambia la conclusion al quitar los extremos. No se ignora.

    5. EL HISTORICO DE LA CUENTA SE CALCULA HACIA ATRAS. «Cuantas
       oportunidades tuvo antes esta cuenta y cuantas gano» se computa solo
       con las creadas ANTES de la que se esta prediciendo. Hacerlo de otro
       modo es ver el futuro, y es el error mas facil de cometer aqui.

CONFIDENCIALIDAD
    Areas, lineas y sublineas salen codificadas (AR/LT/SL) con el mapeo de
    `datos/_mapeo_privado`. No se imprime ningun nombre de cuenta, ningun
    nombre de area real ni el campo `Tema`.

COMO SE EJECUTA
    python scripts/F9_A9_seguimiento_oportunidades.py
    python scripts/F9_A9_seguimiento_oportunidades.py --guardar

NOTA SOBRE LOS NOMBRES DE AGENTE (D24, 07-10-2026)
    Este fichero conserva su nombre antiguo, pero los agentes se
    renumeraron: lo que aqui se llamaba A8 es hoy A7, y lo que se llamaba
    A9 es hoy A8. El texto que imprime usa ya los nombres nuevos. La tabla
    completa esta en 4.6.0 de la memoria y en el ESTADO.
"""

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression

warnings.filterwarnings("ignore")

VERSION_SCRIPT = "v1 · 04-10-2026"
SEMILLA = 42

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "datos" / "00_bruto"
DERIV = RAIZ / "datos" / "02_derivado"
PRIV = RAIZ / "datos" / "_mapeo_privado"
RES = RAIZ / "datos" / "03_resultados"

F_OPORT = BRUTO / "Oportunidades - cuentas 2025_ACT 27-09-2026 19-08-56.xlsx"
F_OFERT = BRUTO / "Ofertas 2025 - ACT 27-09-2026 19-16-12.xlsx"

TRIM_TRAIN_FIN = "2026Q1"     # se entrena hasta aqui, inclusive
TRIM_TEST = "2026Q2"          # se prueba con este
TRIM_APARTE = "2026Q3"        # censurado: se mira aparte

Z95 = 1.959963984540054


# ===========================================================================
# Metricas · las mismas que el proyecto de prevision, reimplementadas aqui
# ===========================================================================
def auc(puntuacion, positivo):
    """Area bajo la curva ROC por rangos (equivale al estadistico de Mann-Whitney)."""
    p = np.asarray(puntuacion, dtype=float)
    y = np.asarray(positivo, dtype=bool)
    n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0:
        return np.nan
    orden = np.argsort(p, kind="mergesort")
    rangos = np.empty(len(p), dtype=float)
    rangos[orden] = np.arange(1, len(p) + 1)
    # empates: se promedian los rangos, si no el AUC sale sesgado
    _, inicio, cuenta = np.unique(p, return_index=True, return_counts=True)
    for i, c in zip(inicio, cuenta):
        if c > 1:
            iguales = np.where(p == p[orden[i]])[0]
            rangos[iguales] = rangos[iguales].mean()
    return float((rangos[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def brier(probabilidad, positivo):
    """Error cuadratico medio. 0 es perfecto; 0,25 es decir siempre 50 %."""
    return float(np.mean((np.asarray(probabilidad, float)
                          - np.asarray(positivo, float)) ** 2))


def wilson(exitos, n):
    if n == 0:
        return (np.nan, np.nan)
    p = exitos / n
    c = (p + Z95 * Z95 / (2 * n)) / (1 + Z95 * Z95 / n)
    m = Z95 * np.sqrt(p * (1 - p) / n + Z95 * Z95 / (4 * n * n)) / (1 + Z95 * Z95 / n)
    return (100 * max(0.0, c - m), 100 * min(1.0, c + m))


def intervalo_bootstrap(fn, prob, y, n=1000, semilla=SEMILLA):
    """Intervalo 95 % de una metrica, remuestreando los casos."""
    prob, y = np.asarray(prob, float), np.asarray(y, bool)
    rng = np.random.default_rng(semilla)
    val = fn(prob, y)
    muestras = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if y[i].all() or (~y[i]).all():
            continue
        muestras.append(fn(prob[i], y[i]))
    if not muestras:
        return val, np.nan, np.nan
    return val, float(np.percentile(muestras, 2.5)), float(np.percentile(muestras, 97.5))


def compara(metrica, prob_a, prob_b, y, n=1000, semilla=SEMILLA):
    """Diferencia de una metrica entre dos predictores sobre LOS MISMOS casos.

    Se remuestrean los CASOS, los mismos para los dos predictores: asi la
    comparacion es emparejada y el intervalo es el de la diferencia, que es
    lo que se quiere contrastar. Remuestrear cada uno por separado daria un
    intervalo mas ancho y la comparacion perderia potencia.
    """
    a, b, y = np.asarray(prob_a, float), np.asarray(prob_b, float), np.asarray(y, bool)
    rng = np.random.default_rng(semilla)
    dif = metrica(a, y) - metrica(b, y)
    muestras = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if y[i].all() or (~y[i]).all():
            continue
        muestras.append(metrica(a[i], y[i]) - metrica(b[i], y[i]))
    m = np.array(muestras)
    lo, hi = np.percentile(m, [2.5, 97.5])
    # p aproximado de dos colas: cuantos remuestreos caen del otro lado del 0
    p = 2 * min((m <= 0).mean(), (m >= 0).mean())
    return dif, float(lo), float(hi), float(min(1.0, p))


def compara_auc(prob_a, prob_b, y, n=1000, semilla=SEMILLA):
    return compara(auc, prob_a, prob_b, y, n, semilla)


def compara_brier(prob_a, prob_b, y, n=1000, semilla=SEMILLA):
    return compara(brier, prob_a, prob_b, y, n, semilla)


def titulo(n, t):
    print()
    print("=" * 76)
    print(f"PASO {n} · {t}")
    print("=" * 76)


# ===========================================================================
def codificadores():
    """Lee el mapeo privado: nombre real -> codigo AR/LT/SL."""
    m = json.loads((PRIV / "mapeo_areas.json").read_text(encoding="utf-8"))
    campos = m["campos"]
    # las claves del json traen los nombres tal cual vienen del CRM
    return {k: v for k, v in campos.items()}


def construir_datos():
    op = pd.read_excel(F_OPORT)
    of = pd.read_excel(F_OFERT)
    op.columns = [c.strip() for c in op.columns]
    of.columns = [c.strip() for c in of.columns]

    col_k = [c for c in of.columns if "oportunidad" in c.lower()][0]
    op["k"] = op["Nº oportunidad"].astype(str).str.strip()
    of["k"] = of[col_k].astype(str).str.strip()

    # --- la PRIMERA oferta de cada oportunidad -----------------------------
    # Importa cual se coge: la ultima lleva la probabilidad ya actualizada
    # con el resultado. La primera es lo mas parecido a una prevision.
    of = of.sort_values("Fecha de creación")
    primera = (of[of.k != "nan"]
               .groupby("k", as_index=False)
               .agg(prob_comercial=("Probabilidad", "first"),
                    horas=("Total horas presupuestadas", "first"),
                    fecha_oferta=("Fecha de creación", "first"),
                    n_ofertas=("Nº Oferta", "count")))

    d = op.merge(primera, on="k", how="left")
    d = d[d.Estado.isin(["Lograda", "Perdida", "Abierta"])].copy()
    d["gana"] = (d.Estado == "Lograda").astype(int)
    d["cerrada"] = d.Estado.isin(["Lograda", "Perdida"])
    d["trim"] = d["Fecha de creación"].dt.to_period("Q").astype(str)
    d["mes"] = d["Fecha de creación"].dt.month
    d["dias_hasta_oferta"] = (d.fecha_oferta - d["Fecha de creación"]).dt.days
    d["tiene_oferta"] = d.prob_comercial.notna().astype(int)
    d["dias_cierre"] = (d["Fecha de cierre real"] - d["Fecha de creación"]).dt.days

    # --- historico de la cuenta, calculado HACIA ATRAS ---------------------
    # Solo con las oportunidades creadas antes que la actual. Si se usara el
    # total, el modelo veria el futuro de su propia cuenta.
    d = d.sort_values("Fecha de creación").reset_index(drop=True)
    d["cta"] = d["Cuenta"].astype(str).str.strip().str.lower()
    g = d.groupby("cta")
    d["ops_previas"] = g.cumcount()
    ganadas_hasta = g["gana"].cumsum() - d["gana"]
    cerradas_hasta = g["cerrada"].cumsum() - d["cerrada"].astype(int)
    d["tasa_previa"] = np.where(cerradas_hasta > 0,
                                ganadas_hasta / cerradas_hasta.replace(0, np.nan),
                                np.nan)
    d["cerradas_previas"] = cerradas_hasta
    return d


def anadir_cuenta(d):
    """Pega lo que se sabe de la cuenta: sector, tamano, cliente, provincia."""
    trozos = []
    for p in ("train", "val", "test"):
        f = DERIV / f"cuentas_{p}.csv"
        if f.exists():
            trozos.append(pd.read_csv(f, usecols=lambda c: c in (
                "empresa", "pais", "provincia", "tamano", "cliente",
                "asociado", "atractividad", "sector_agrupado")))
    if not trozos:
        return d, 0
    c = pd.concat(trozos, ignore_index=True)
    c["cta"] = c.empresa.astype(str).str.strip().str.lower()
    c = c.drop_duplicates("cta").drop(columns=["empresa"])
    antes = len(d)
    d = d.merge(c, on="cta", how="left")
    assert len(d) == antes, "el cruce con cuentas ha duplicado filas"
    return d, d.provincia.notna().sum()


VARIABLES_CREACION = [
    "Tipo Oportunidad", "Tipología de proyecto", "Línea Tecnológica",
    "Sublínea Tecnológica", "Área de Empresa", "Propietario",
    "mes", "ops_previas", "cerradas_previas", "tasa_previa",
    "pais", "provincia", "tamano", "cliente", "asociado",
    "atractividad", "sector_agrupado",
]
VARIABLES_OFERTA = ["horas", "n_ofertas", "dias_hasta_oferta"]

# La puntuacion que el texto de la solicitud da por si solo.
#
# Viene de lo que era el agente A7. E36 midio que el texto aporta +0,024 de
# AUC sobre estas diecisiete variables, con intervalo [+0,010, +0,040] y
# p = 0,001: ve algo que los campos no ven. Por eso dejo de ser una fase
# aparte —donde no habia forma de validarlo, porque ningun correo trae su
# resultado— y pasa a ser una variable mas de A8, que si tiene resultado
# real contra el que medirse. Es la decision D23.
VARIABLE_TEXTO = "punt_texto"


def puntuacion_del_texto(textos, y, entrena, prueba, semilla=SEMILLA):
    """Convierte el texto de la solicitud en una puntuacion, sin hacer trampa.

    El detalle que importa: la puntuacion de las filas de ENTRENAMIENTO se
    saca por validacion cruzada, no del mismo modelo que ya las vio. Si se
    usara ese, la variable seria casi perfecta en entrenamiento y mediocre
    en prueba, el bosque se apoyaria en ella de mas y la comparacion saldria
    falsa a favor del texto.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_predict

    vec = TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), min_df=3,
                          max_features=60000)
    Xtr = vec.fit_transform(textos[entrena])
    Xte = vec.transform(textos[prueba])
    clf = LogisticRegression(max_iter=3000, class_weight="balanced")

    p_tr = cross_val_predict(clf, Xtr, y[entrena], cv=5,
                             method="predict_proba")[:, 1]
    clf.fit(Xtr, y[entrena])
    p_te = clf.predict_proba(Xte)[:, 1]
    return p_tr, p_te


def matriz(d, variables):
    """Convierte a numeros. Las categoricas, a indicadores; los nulos, a su
    propia categoria, que en estos datos es informativa."""
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
            # categorias con menos de 15 casos se agrupan: si no, el modelo
            # memoriza nombres que no volvera a ver
            s = s.where(s.map(frec) >= 15, "(poco frecuente)")
            for val in sorted(s.unique()):
                X[f"{v}={val}"] = (s == val).astype(float)
    return X


def entrena_y_evalua(Xtr, ytr, Xte, yte, nombre, modelos):
    out = {}
    for etiqueta, mod in modelos.items():
        mod.fit(Xtr, ytr)
        p = mod.predict_proba(Xte)[:, 1]
        a, alo, ahi = intervalo_bootstrap(auc, p, yte)
        b, blo, bhi = intervalo_bootstrap(brier, p, yte)
        acc = float(((p >= 0.5) == yte.astype(bool)).mean())
        out[etiqueta] = {"auc": a, "auc_lo": alo, "auc_hi": ahi,
                         "brier": b, "brier_lo": blo, "brier_hi": bhi,
                         "acierto": 100 * acc, "prob": p, "modelo": mod}
    return out


# ===========================================================================
def main():
    guardar = "--guardar" in sys.argv

    print()
    print("#" * 76)
    print("# F9 · A8 · ¿se va a ganar esta oportunidad?")
    print(f"# {VERSION_SCRIPT}   ·   SIN IMPORTES (decision D13)")
    print("#" * 76)

    # ------------------------------------------------------------------ 1
    titulo(1, "LOS DATOS")
    d = construir_datos()
    d, con_cuenta = anadir_cuenta(d)
    print(f"   Oportunidades              : {len(d):>6}")
    print(f"   …cerradas (ganada o perdida): {d.cerrada.sum():>6}")
    print(f"   …abiertas                   : {(~d.cerrada).sum():>6}")
    print(f"   …con al menos una oferta    : {d.tiene_oferta.sum():>6}")
    print(f"   …cruzadas con su cuenta     : {con_cuenta:>6}")
    print()
    print("   Variables al crear la oportunidad: "
          f"{len(VARIABLES_CREACION)}  (ninguna monetaria)")
    print(f"   Variables que anade la oferta   : {len(VARIABLES_OFERTA)}")

    # ------------------------------------------------------------------ 2
    titulo(2, "EL SUELO Y LA PARTICION TEMPORAL")
    cerr = d[d.cerrada].copy()
    suelo_global = 100 * cerr.gana.mean()
    print(f"   Cerradas            : {len(cerr)}")
    print(f"   Se ganan            : {cerr.gana.sum()}  "
          f"({suelo_global:.1f} %)   <-- EL SUELO: decir siempre «se gana»")

    tr = cerr[cerr.trim <= TRIM_TRAIN_FIN]
    te = cerr[cerr.trim == TRIM_TEST]
    ap = cerr[cerr.trim == TRIM_APARTE]
    print()
    print(f"   {'conjunto':<28}{'casos':>7}{'se ganan':>11}")
    print("   " + "-" * 46)
    for etiqueta, parte in (("entrenamiento (<= 2026Q1)", tr),
                            ("prueba (2026Q2)", te),
                            ("apartado (2026Q3)", ap)):
        print(f"   {etiqueta:<28}{len(parte):>7}{100*parte.gana.mean():>10.1f} %")
    suelo = 100 * te.gana.mean()
    print()
    print(f"   SUELO EN PRUEBA: {suelo:.1f} %")
    print()
    print("   El trimestre apartado tiene un "
          f"{100*ap.gana.mean():.1f} % de ganadas porque las")
    print("   recientes aun no se han resuelto. No se usa para concluir.")

    # ------------------------------------------------------------------ 3
    titulo(3, "EL RIVAL: LA PROBABILIDAD QUE PONE LA PERSONA")
    hum = te[te.prob_comercial.notna()].copy()
    hum["p"] = hum.prob_comercial.clip(0, 100) / 100.0
    print(f"   Casos de prueba con probabilidad declarada: {len(hum)} de {len(te)}")
    print()
    extremos = ((hum.prob_comercial >= 100) | (hum.prob_comercial <= 0)).sum()
    print(f"   CONTAMINACION · valores en 0 o en 100: {extremos} "
          f"({100*extremos/max(1,len(hum)):.1f} %)")
    g100 = hum[hum.prob_comercial >= 100]
    if len(g100):
        print(f"      de los que marcan 100, se ganan el "
              f"{100*g100.gana.mean():.1f} %  ({len(g100)} casos)")
        print("      ese valor se escribe DESPUES de saber el resultado")
    print()
    a_h, alo_h, ahi_h = intervalo_bootstrap(auc, hum.p, hum.gana)
    b_h, blo_h, bhi_h = intervalo_bootstrap(brier, hum.p, hum.gana)
    print(f"   AUC   de la persona : {a_h:.3f}  [{alo_h:.3f}, {ahi_h:.3f}]")
    print(f"   Brier de la persona : {b_h:.4f}  [{blo_h:.4f}, {bhi_h:.4f}]")
    print()
    print("   Calibracion: de lo que dice al resultado real")
    print(f"   {'dice':<12}{'casos':>7}{'se gana de verdad':>20}{'IC 95 %':>20}")
    print("   " + "-" * 59)
    cal = []
    for lo, hi in ((0, 24), (25, 49), (50, 69), (70, 89), (90, 100)):
        s = hum[(hum.prob_comercial >= lo) & (hum.prob_comercial <= hi)]
        if not len(s):
            continue
        real = 100 * s.gana.mean()
        wlo, whi = wilson(s.gana.sum(), len(s))
        cal.append({"rango": f"{lo}-{hi}", "n": len(s), "real": real,
                    "ic": [wlo, whi]})
        print(f"   {lo}-{hi} %{'':<5}{len(s):>7}{real:>18.1f} %"
              f"{f'[{wlo:.1f}, {whi:.1f}]':>20}")

    # ------------------------------------------------------------------ 4
    titulo(4, "EL MODELO, CON LO QUE SE SABE AL CREAR LA OPORTUNIDAD")
    Xall = matriz(cerr, VARIABLES_CREACION)
    itr, ite = tr.index, te.index
    Xtr, Xte = Xall.loc[itr], Xall.loc[ite]
    ytr, yte = tr.gana.values, te.gana.values

    # --- el texto de la solicitud, que era A7 ------------------------------
    con_texto = "Tema" in cerr.columns and cerr.Tema.notna().sum() > 100
    if con_texto:
        import unicodedata

        def st(t):
            return "".join(c for c in unicodedata.normalize("NFD", str(t).lower())
                           if unicodedata.category(c) != "Mn")
        txt = cerr.Tema.fillna("").astype(str).map(st)
        m_tr = cerr.index.isin(itr)
        m_te = cerr.index.isin(ite)
        p_tr, p_te = puntuacion_del_texto(txt.values, cerr.gana.values,
                                          m_tr, m_te)
        Xtr = Xtr.copy()
        Xte = Xte.copy()
        Xtr[VARIABLE_TEXTO] = p_tr
        Xte[VARIABLE_TEXTO] = p_te
        print("   Incluye la puntuación del texto de la solicitud (lo que era A7)")
    else:
        print("   [i] Sin el campo de texto: A8 corre solo con los campos.")

    print(f"   Columnas tras convertir a numeros: {Xtr.shape[1]}")
    print(f"   Entrenamiento {Xtr.shape[0]} · prueba {Xte.shape[0]}")

    modelos = {
        "Regresión logística": LogisticRegression(max_iter=2000, C=1.0),
        "Bosque aleatorio": RandomForestClassifier(
            n_estimators=400, min_samples_leaf=5, random_state=SEMILLA, n_jobs=-1),
        "Potenciación del gradiente": GradientBoostingClassifier(
            random_state=SEMILLA),
    }
    r = entrena_y_evalua(Xtr, ytr, Xte, yte, "creacion", modelos)

    print()
    print(f"   {'modelo':<28}{'acierto':>9}{'AUC':>8}{'IC 95 %':>18}{'Brier':>9}")
    print("   " + "-" * 72)
    print(f"   {'SUELO (decir siempre sí)':<28}{suelo:>8.1f} %{0.500:>8.3f}"
          f"{'—':>18}{brier(np.full(len(yte), yte.mean()), yte):>9.4f}")
    for k, v in r.items():
        ic = f"[{v['auc_lo']:.3f}, {v['auc_hi']:.3f}]"
        print(f"   {k:<28}{v['acierto']:>8.1f} %{v['auc']:>8.3f}"
              f"{ic:>18}{v['brier']:>9.4f}")

    mejor = max(r, key=lambda k: r[k]["auc"])
    print()
    print(f"   MEJOR: {mejor}  ·  AUC {r[mejor]['auc']:.3f}")

    # ------------------------------------------------------------------ 5
    titulo(5, "CARA A CARA CONTRA LA PERSONA, SOBRE LOS MISMOS CASOS")
    # el modelo que compite ve tambien lo que aporta la oferta, porque la
    # persona tambien necesita la oferta para poner su porcentaje
    Xall2 = matriz(cerr, VARIABLES_CREACION + VARIABLES_OFERTA)
    X2tr, X2te = Xall2.loc[itr].copy(), Xall2.loc[ite].copy()
    if con_texto:
        # el mismo texto que en el paso 4: si se compara contra la persona
        # hay que hacerlo con el modelo que de verdad se publica, no con
        # una version a la que se le ha quitado una variable
        X2tr[VARIABLE_TEXTO] = p_tr
        X2te[VARIABLE_TEXTO] = p_te
    r2 = entrena_y_evalua(X2tr, ytr, X2te, yte,
                          "con_oferta", {mejor: modelos[mejor]})
    p_mod_te = pd.Series(r2[mejor]["prob"], index=ite)
    p_mod = p_mod_te.loc[hum.index].values

    print(f"   Casos comparables: {len(hum)}")
    print()
    a_m, alo_m, ahi_m = intervalo_bootstrap(auc, p_mod, hum.gana)
    b_m, blo_m, bhi_m = intervalo_bootstrap(brier, p_mod, hum.gana)
    print(f"   {'quien':<22}{'AUC':>8}{'IC 95 %':>18}{'Brier':>9}{'IC 95 %':>20}")
    print("   " + "-" * 78)
    print(f"   {'La persona':<22}{a_h:>8.3f}{f'[{alo_h:.3f}, {ahi_h:.3f}]':>18}"
          f"{b_h:>9.4f}{f'[{blo_h:.4f}, {bhi_h:.4f}]':>20}")
    print(f"   {'A8':<22}{a_m:>8.3f}{f'[{alo_m:.3f}, {ahi_m:.3f}]':>18}"
          f"{b_m:>9.4f}{f'[{blo_m:.4f}, {bhi_m:.4f}]':>20}")

    dif, dlo, dhi, pval = compara_auc(p_mod, hum.p.values, hum.gana.values)
    # el Brier baja cuando mejora, asi que se invierte el signo para que
    # «positivo = A8 mejor» signifique lo mismo en las dos filas
    difb, dblo, dbhi, pb = compara_brier(hum.p.values, p_mod, hum.gana.values)
    print()
    print("   CONTRASTE EMPAREJADO  ·  positivo = A8 mejor")
    print(f"   {'':<26}{'diferencia':>12}{'IC 95 %':>20}{'p':>9}")
    print("   " + "-" * 67)
    print(f"   {'ORDENAR (AUC)':<26}{dif:>+12.3f}"
          f"{f'[{dlo:+.3f}, {dhi:+.3f}]':>20}{pval:>9.3f}")
    print(f"   {'CALIBRAR (Brier)':<26}{difb:>+12.4f}"
          f"{f'[{dblo:+.4f}, {dbhi:+.4f}]':>20}{pb:>9.3f}")
    print()
    if dlo > 0:
        v_auc = "A8 ordena mejor y el intervalo no toca el cero"
    elif dhi < 0:
        v_auc = "la persona ordena mejor y el intervalo no toca el cero"
    else:
        v_auc = "ORDENANDO NO SE DISTINGUEN: el intervalo cruza el cero"
    if dblo > 0:
        v_bri = "A8 esta MEJOR CALIBRADO, y el intervalo no toca el cero"
    elif dbhi < 0:
        v_bri = "la persona esta mejor calibrada, y el intervalo no toca el cero"
    else:
        v_bri = "calibrando tampoco se distinguen"
    print(f"   · {v_auc}")
    print(f"   · {v_bri}")
    veredicto = f"AUC: {v_auc} | Brier: {v_bri}"
    print()
    print("   LAS DOS COSAS NO SON LA MISMA, y aqui se separan: ordenar es")
    print("   poner delante las que se van a ganar, y calibrar es que el")
    print("   numero signifique lo que dice. Mirense las dos filas de arriba")
    print("   antes de concluir nada.")

    # sin los extremos contaminados
    limpio = hum[(hum.prob_comercial > 0) & (hum.prob_comercial < 100)]
    if len(limpio) > 50:
        pm = p_mod_te.loc[limpio.index].values
        dif2, dlo2, dhi2, p2 = compara_auc(pm, limpio.p.values, limpio.gana.values)
        print()
        print(f"   SIN los valores en 0 y en 100 ({len(limpio)} casos):")
        print(f"   diferencia {dif2:+.3f}  [{dlo2:+.3f}, {dhi2:+.3f}]   p ~ {p2:.3f}")
        print("   Es la comparacion que importa: quita el efecto de marcar el")
        print("   100 cuando ya se sabe el resultado.")
    else:
        dif2 = dlo2 = dhi2 = p2 = None

    # ------------------------------------------------------------------ 6
    titulo(6, "¿SE APOYA EL MODELO EN QUIEN LLEVA LA OPORTUNIDAD?")
    sin_prop = [v for v in VARIABLES_CREACION if v != "Propietario"]
    X3 = matriz(cerr, sin_prop)
    X3tr, X3te = X3.loc[itr].copy(), X3.loc[ite].copy()
    if con_texto:
        X3tr[VARIABLE_TEXTO] = p_tr
        X3te[VARIABLE_TEXTO] = p_te
    r3 = entrena_y_evalua(X3tr, ytr, X3te, yte, "sin_prop",
                          {mejor: modelos[mejor]})
    print(f"   Con el propietario : AUC {r[mejor]['auc']:.3f}")
    print(f"   Sin el propietario : AUC {r3[mejor]['auc']:.3f}")
    caida = r[mejor]["auc"] - r3[mejor]["auc"]
    print(f"   Aporta {caida:+.3f}")
    print()
    if abs(caida) < 0.02:
        print("   No se apoya en el: el agente no esta aprendiendo «quien»")
        print("   sino «que». Es lo que interesa, porque un modelo que")
        print("   predice por comercial no es transferible.")
    else:
        print("   SI se apoya. Hay que declararlo: parte del acierto viene de")
        print("   identificar al comercial, no las caracteristicas del caso.")

    # ------------------------------------------------------------------ 7
    # ---------------------------------------------------------------- 6b
    if con_texto:
        titulo("6b", "¿CUANTO APORTA EL TEXTO DE LA SOLICITUD?")
        print("   Es lo que era el agente A7. Dejo de ser una fase propia")
        print("   porque alli no habia resultado con el que validarlo; aqui si.")
        rs = entrena_y_evalua(Xall.loc[itr], ytr, Xall.loc[ite], yte,
                              "sin_texto", {mejor: modelos[mejor]})
        a_sin = rs[mejor]["auc"]
        a_con = r[mejor]["auc"]
        dif_t, lo_t, hi_t, p_t = compara_auc(r[mejor]["prob"],
                                             rs[mejor]["prob"], yte)
        print()
        print(f"   {'':<30}{'AUC':>8}{'acierto':>10}")
        print("   " + "-" * 50)
        print(f"   {'A8 sin el texto':<30}{a_sin:>8.3f}{rs[mejor]['acierto']:>9.1f} %")
        print(f"   {'A8 CON el texto':<30}{a_con:>8.3f}{r[mejor]['acierto']:>9.1f} %")
        print()
        print(f"   Diferencia: {dif_t:+.3f}  [{lo_t:+.3f}, {hi_t:+.3f}]  "
              f"p ~ {p_t:.3f}")
        if lo_t > 0:
            print("   APORTA, y el intervalo no toca el cero.")
        else:
            print("   NO se distingue del cero sobre este trimestre.")
        ablacion_texto = {"auc_sin": a_sin, "auc_con": a_con,
                          "diferencia": dif_t, "ic": [lo_t, hi_t], "p": p_t}
    else:
        ablacion_texto = None

    titulo(7, "CUANTO TARDA, Y QUE ESTA ATASCADO")
    dc = cerr[(cerr.dias_cierre.notna()) & (cerr.dias_cierre >= 0)]
    print(f"   Cerradas con fecha coherente: {len(dc)} de {len(cerr)}")
    neg = (cerr.dias_cierre < 0).sum()
    print(f"   Con cierre ANTERIOR a la creacion: {neg}  <-- defecto del CRM")
    print()
    print(f"   {'':<14}{'casos':>7}{'mediana':>10}{'media':>9}{'p90':>8}")
    print("   " + "-" * 48)
    for etiqueta, s in (("Ganadas", dc[dc.gana == 1].dias_cierre),
                        ("Perdidas", dc[dc.gana == 0].dias_cierre)):
        print(f"   {etiqueta:<14}{len(s):>7}{s.median():>10.0f}{s.mean():>9.0f}"
              f"{s.quantile(.9):>8.0f}")

    abiertas = d[~d.cerrada].copy()
    # el nombre de esa columna viene con el prefijo "(No modificar)"
    col_mod = next((c for c in d.columns if "modificaci" in c.lower()), None)
    hoy = d[col_mod].max() if col_mod else d["Fecha de creación"].max()
    abiertas["edad"] = (hoy - abiertas["Fecha de creación"]).dt.days
    p90 = dc.dias_cierre.quantile(.9)
    atascadas = (abiertas.edad > p90).sum()
    print()
    print(f"   Abiertas: {len(abiertas)}")
    print(f"   El 90 % de las que cierran lo hacen antes de {p90:.0f} dias.")
    print(f"   ABIERTAS QUE PASAN DE ESE PLAZO: {atascadas} "
          f"({100*atascadas/max(1,len(abiertas)):.1f} %)")
    print()
    print("   Eso es una lista de trabajo inmediata y no necesita modelo:")
    print("   son las que llevan mas tiempo del que tarda el 90 % en")
    print("   resolverse. El modelo sirve para lo otro, para ordenar.")

    # ------------------------------------------------------------------ 8
    titulo(8, "LO QUE ESTE EXPERIMENTO NO DICE")
    print("   · No dice que usar A8 aumente las ventas. Mide si ordena mejor")
    print("     que la persona, no el efecto de actuar en consecuencia.")
    print("   · La comparacion es sobre un trimestre (2026Q2). Un trimestre")
    print("     distinto podria dar otra cosa.")
    print(f"   · El rival declara su porcentaje {len(hum)} veces de {len(te)}:")
    print("     donde no lo declara, no hay con quien comparar.")
    print("   · Sin importes, por decision D13. Un modelo con el importe")
    print("     podria ordenar mejor; no se ha probado y no se sabe.")

    if not guardar:
        print()
        print("   Simulacion: no se ha escrito nada. Usa --guardar.")
        print()
        return

    salida = {
        "experimento": "E32", "agente": "A8", "version": VERSION_SCRIPT,
        "sin_importes": True,
        "particion": {"entrena_hasta": TRIM_TRAIN_FIN, "prueba": TRIM_TEST,
                      "apartado_por_censura": TRIM_APARTE},
        "n": {"total": int(len(d)), "cerradas": int(d.cerrada.sum()),
              "abiertas": int((~d.cerrada).sum()),
              "entrena": int(len(tr)), "prueba": int(len(te)),
              "comparables_con_persona": int(len(hum))},
        "suelo_prueba": suelo,
        "persona": {"auc": a_h, "auc_ic": [alo_h, ahi_h],
                    "brier": b_h, "brier_ic": [blo_h, bhi_h],
                    "extremos_contaminados": int(extremos),
                    "calibracion": cal},
        "modelos_creacion": {k: {kk: vv for kk, vv in v.items()
                                 if kk not in ("prob", "modelo")}
                             for k, v in r.items()},
        "cara_a_cara": {
            "modelo": mejor,
            "auc_modelo": a_m, "auc_modelo_ic": [alo_m, ahi_m],
            "brier_modelo": b_m, "brier_modelo_ic": [blo_m, bhi_m],
            "diferencia_auc": dif, "diferencia_ic": [dlo, dhi], "p": pval,
            "veredicto": veredicto,
            "sin_extremos": None if dif2 is None else {
                "n": int(len(limpio)), "diferencia_auc": dif2,
                "ic": [dlo2, dhi2], "p": p2},
        },
        "incluye_texto_de_la_solicitud": bool(con_texto),
        "ablacion_texto": ablacion_texto,
        "ablacion_propietario": {"con": r[mejor]["auc"],
                                 "sin": r3[mejor]["auc"], "aporta": caida},
        "tiempos": {"mediana_ganadas": float(dc[dc.gana == 1].dias_cierre.median()),
                    "mediana_perdidas": float(dc[dc.gana == 0].dias_cierre.median()),
                    "p90": float(p90),
                    "abiertas": int(len(abiertas)),
                    "atascadas": int(atascadas),
                    "cierre_antes_de_crear": int(neg)},
    }
    RES.mkdir(parents=True, exist_ok=True)
    f = RES / "a9_seguimiento_oportunidades.json"
    f.write_text(json.dumps(salida, ensure_ascii=False, indent=1, default=float),
                 encoding="utf-8")
    print()
    print(f"   [ok] {f.name}")
    print()


if __name__ == "__main__":
    main()
