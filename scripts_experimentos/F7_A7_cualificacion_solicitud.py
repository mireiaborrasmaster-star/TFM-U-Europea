# -*- coding: utf-8 -*-
"""
F7_A7_cualificacion_solicitud.py · A7 · ¿merece la pena esta solicitud?
========================================================================

QUE ES A7
    La fase 7: llega una solicitud y hay que cualificarla antes de dedicarle
    tiempo. El diseno original proponia siete criterios -necesidad, impacto,
    presupuesto, plazo, decisor, encaje y campeon- extraidos de la
    conversacion comercial.

POR QUE NO SE HABIA CONSTRUIDO, Y QUE CAMBIA AHORA
    No existia el dato de entrada: Empresa no graba las llamadas comerciales, y
    sin conversacion no hay de donde extraer los criterios. Eso sigue siendo
    cierto.

    Lo que cambia es que el **sustituto escrito** de esa conversacion si
    existe, y por duplicado:
       · 105 correos reales de clientes, para ver si el agente corre
       · 3.835 solicitudes historicas del CRM CON SU RESULTADO REAL

    Y eso ultimo permite responder la pregunta que de verdad importa y que
    nadie habia planteado:

        ¿PREDICE LA CONVERSION CONTAR CRITERIOS DE CUALIFICACION,
        O HAY QUE APRENDER DEL TEXTO?

    Porque el marco de siete criterios se da por bueno en la bibliografia
    comercial, pero aqui se puede contrastar contra lo que paso de verdad.

COMO SE EVALUA
    Particion TEMPORAL, igual que A9: se entrena con lo viejo y se prueba con
    lo nuevo. Y se compara contra tres referencias, no contra ninguna:
       1. el suelo: decir siempre la clase mayoritaria
       2. contar los SIETE criterios
       3. contar los TRES que de verdad aparecen en los correos
          (necesidad 74,3 %, encaje 69,5 %, presupuesto 43,8 %)

LO QUE HAY QUE VIGILAR, Y SE VIGILA
    El texto de la solicitud lo escribe el comercial en el CRM, a veces
    DESPUES de saber como acabo. Si dentro pone «anulado» o «no procede», el
    modelo no esta cualificando: esta leyendo el resultado. El paso 5
    busca esos terminos y mide cuanto cae el modelo al quitarlos. No se
    supone que no hay fuga: se comprueba.

CONFIDENCIALIDAD
    No se imprime ningun texto de solicitud, ningun nombre y ningun area sin
    codificar. De los terminos influyentes solo se dice CUANTOS son de
    resultado, nunca cuales, porque son vocabulario comercial de la casa.

COMO SE EJECUTA
    python scripts/F7_A7_cualificacion_solicitud.py
    python scripts/F7_A7_cualificacion_solicitud.py --guardar
"""

import json
import re
import sys
import unicodedata
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

warnings.filterwarnings("ignore")

VERSION_SCRIPT = "v1 · 04-10-2026"
SEMILLA = 42

RAIZ = Path(__file__).resolve().parent.parent
LIMPIO = RAIZ / "datos" / "01_limpio"
PRIV = RAIZ / "datos" / "_mapeo_privado"
RES = RAIZ / "datos" / "03_resultados"

TEMAS = PRIV / "temas_oportunidades.csv"
OPORT = LIMPIO / "Oportunidades - cuentas 2025_ACT 27-09-2026 19-08-56_anon.csv"
CORPUS = LIMPIO / "entradas_inbound_50_anon.csv"

TRIM_TRAIN_FIN = "2026Q1"
TRIM_TEST = "2026Q2"
TRIM_APARTE = "2026Q3"
Z95 = 1.959963984540054

# Los siete criterios. Las listas son las de F6_A7_A8_viabilidad_cadena.py.
NIPPDEC = {
    "N · Necesidad": [
        "solicitar", "solicitamos", "necesitamos", "necesitaria", "quisiera",
        "nos gustaria", "requerimos", "interesados", "consulta", "informacion",
        "analisis", "ensayo", "ensayos", "estudio", "asesoramiento",
        "would like", "we need", "we are looking", "request", "enquiry"],
    "I · Impacto": [
        "cumplimiento", "cumplir", "obligacion", "obligatorio", "exige",
        "exigencia", "nos piden", "nos solicitan", "cliente nos", "auditoria",
        "reclamacion", "rechazo", "incidencia", "problema", "sancion",
        "entrada en vigor", "compliance", "requirement"],
    "P · Presupuesto": [
        "presupuesto", "coste", "costes", "precio", "precios", "tarifa",
        "tarifas", "oferta economica", "importe", "cuanto costaria",
        "quotation", "quote", "cost", "budget", "pricing"],
    "P · Plazo": [
        "plazo", "plazos", "urgente", "urgencia", "cuanto tiempo", "cuando",
        "antes de", "fecha limite", "disponibilidad", "lo antes posible",
        "timeline", "lead time", "deadline", "how long", "when"],
    "D · Decisor": [
        "director", "directora", "responsable", "jefe", "jefa", "gerente",
        "manager", "head of", "coordinador", "coordinadora", "tecnico",
        "calidad", "i+d", "compras", "produccion", "developer", "engineer"],
    "E · Encaje": [
        "envase", "envases", "embalaje", "packaging", "film", "pelicula",
        "bandeja", "botella", "caja", "carton", "plastico", "papel",
        "material", "materiales", "producto", "producimos", "fabricamos",
        "comercializamos", "we produce", "we manufacture"],
    "C · Campeon": [
        "quedo a la espera", "quedamos a la espera", "no dude", "no duden",
        "podemos concertar", "reunion", "llamada", "contactar", "hablar",
        "ampliar informacion", "happy to", "look forward", "please advise",
        "get in touch", "further details"],
}

# Los tres que de verdad aparecen en los correos de cliente (medido sobre 105)
TRES = ["N · Necesidad", "E · Encaje", "P · Presupuesto"]

# Terminos que delatan el resultado en vez de cualificar la solicitud.
# Si el modelo se apoya en estos no esta prediciendo, esta leyendo.
FUGA = ["anulado", "anulada", "cancelado", "cancelada", "no procede",
        "desestimado", "desestimada", "rechazado", "rechazada", "perdida",
        "perdido", "ganado", "ganada", "adjudicado", "adjudicada",
        "facturado", "facturada", "no interesa", "descartado", "descartada",
        "duplicado", "duplicada", "error", "prueba"]


def sin_tildes(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t).lower())
                   if unicodedata.category(c) != "Mn")


def contiene(texto, termino):
    """Busca el termino como palabra, con una salvedad que costo un error.

    Para palabras largas en castellano se tolera un sufijo de hasta tres
    letras, para que «ensayo» encuentre «ensayos» y «caida» encuentre
    «caidas». Eso esta bien.

    Pero para SIGLAS y terminos cortos esa tolerancia es un desastre: con
    ella «reach» —el reglamento— encontraba «reached» y «reaching» en los
    correos en ingles, y el briefing proponia un tema sobre REACH para un
    correo que hablaba de biodegradacion. Tres falsos positivos de 105, dos
    de ellos cambiando el veredicto del correo. Es el error X28.

    Asi que los terminos de seis letras o menos, y los que llevan digitos
    —que son las normas: «en 13432», «2025/40»— se buscan EXACTOS.
    """
    partes = [re.escape(p) for p in termino.split()]
    # Solo se tolera el PLURAL castellano, nada mas. La regla por
    # longitud dejaba fuera «caidas» y la de tres letras cualquiera
    # cazaba «reached». El plural resuelve los dos casos.
    cola = r"(e?s)?"
    return re.search(r"\b" + r"\s+".join(partes) + cola + r"\b",
                     texto) is not None


def wilson(exitos, n):
    if n == 0:
        return (np.nan, np.nan)
    p = exitos / n
    c = (p + Z95 * Z95 / (2 * n)) / (1 + Z95 * Z95 / n)
    m = Z95 * np.sqrt(p * (1 - p) / n + Z95 * Z95 / (4 * n * n)) / (1 + Z95 * Z95 / n)
    return (100 * max(0.0, c - m), 100 * min(1.0, c + m))


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


def ic_auc(punt, y, n=1000, semilla=SEMILLA):
    punt, y = np.asarray(punt, float), np.asarray(y, bool)
    rng = np.random.default_rng(semilla)
    v = auc(punt, y)
    ms = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if y[i].all() or (~y[i]).all():
            continue
        ms.append(auc(punt[i], y[i]))
    return v, float(np.percentile(ms, 2.5)), float(np.percentile(ms, 97.5))


def criterios(texto, cuales=None):
    """Cuantos criterios aparecen, y cuales."""
    cs = cuales or list(NIPPDEC)
    hall = [c for c in cs if any(contiene(texto, x) for x in NIPPDEC[c])]
    return len(hall), hall


def titulo(n, t):
    print()
    print("=" * 76)
    print(f"PASO {n} · {t}")
    print("=" * 76)


# ===========================================================================
def main():
    guardar = "--guardar" in sys.argv

    print()
    print("#" * 76)
    print("# F7 · A7 · ¿merece la pena esta solicitud?")
    print(f"# {VERSION_SCRIPT}")
    print("#" * 76)

    # ------------------------------------------------------------------ 1
    titulo(1, "LOS DATOS: SOLICITUDES HISTORICAS CON SU RESULTADO")
    tm = pd.read_csv(TEMAS, sep=";")
    op = pd.read_csv(OPORT, sep=";", low_memory=False)
    col_fecha = next(c for c in op.columns if "Fecha de creaci" in c)
    d = tm.merge(op, on="Nº oportunidad", how="inner")
    d = d.dropna(subset=["Tema"])
    d["texto"] = d.Tema.astype(str).map(sin_tildes)
    d = d[d.texto.str.len() >= 10]
    # OJO: aqui las fechas vienen en ISO (2025-01-25 14:00:47). Pasar
    # dayfirst=True hacia que pandas leyera el 25 como MES, lo invalidaba y
    # devolvia NaT: se perdian dos tercios de las filas y el conjunto de
    # prueba se quedaba en 155 casos. Sin dayfirst se leen todas.
    d[col_fecha] = pd.to_datetime(d[col_fecha], errors="coerce")
    d = d.dropna(subset=[col_fecha])
    d["trim"] = d[col_fecha].dt.to_period("Q").astype(str)
    cerr = d[d.Estado.isin(["Lograda", "Perdida"])].copy()
    cerr["gana"] = (cerr.Estado == "Lograda").astype(int)

    print(f"   Solicitudes con texto      : {len(d)}")
    print(f"   …cerradas (resultado real) : {len(cerr)}")
    print(f"   …se ganaron                : {cerr.gana.sum()} "
          f"({100*cerr.gana.mean():.1f} %)")
    print(f"   Longitud del texto         : mediana "
          f"{int(cerr.texto.str.split().str.len().median())} palabras")
    print()
    print("   AVISO SOBRE ESTE TEXTO: lo escribe el comercial en el CRM, no el")
    print("   cliente. Es mucho mas corto y mas tecnico que un correo. El")
    print("   paso 6 mide que pasa al cruzar esa frontera.")

    tr = cerr[cerr.trim <= TRIM_TRAIN_FIN]
    te = cerr[cerr.trim == TRIM_TEST]
    print()
    print(f"   Entrenamiento (<= {TRIM_TRAIN_FIN}): {len(tr):>5}  "
          f"{100*tr.gana.mean():.1f} % ganadas")
    print(f"   Prueba ({TRIM_TEST})            : {len(te):>5}  "
          f"{100*te.gana.mean():.1f} % ganadas")
    suelo = 100 * max(te.gana.mean(), 1 - te.gana.mean())
    print(f"   SUELO en prueba: {suelo:.1f} %  (decir siempre la mas comun)")

    # ------------------------------------------------------------------ 2
    titulo(2, "¿CUANTOS CRITERIOS TRAE UNA SOLICITUD DEL CRM?")
    cuentas7, cuentas3 = [], []
    for t in cerr.texto:
        n7, _ = criterios(t)
        n3, _ = criterios(t, TRES)
        cuentas7.append(n7)
        cuentas3.append(n3)
    cerr["crit7"] = cuentas7
    cerr["crit3"] = cuentas3
    print(f"   Media de criterios por solicitud: {np.mean(cuentas7):.2f} de 7")
    print(f"   (en los correos de cliente era 3,1 de 7)")
    print()
    print(f"   {'criterio':<18}{'solicitudes':>13}{'%':>8}{'se ganan':>11}")
    print("   " + "-" * 51)
    por_crit = {}
    for c in NIPPDEC:
        tiene = cerr.texto.map(lambda t: any(contiene(t, x) for x in NIPPDEC[c]))
        n = int(tiene.sum())
        gana_si = 100 * cerr.gana[tiene].mean() if n else float("nan")
        por_crit[c] = {"n": n, "pct": 100 * n / len(cerr), "gana": gana_si}
        print(f"   {c:<18}{n:>13}{100*n/len(cerr):>7.1f} %{gana_si:>10.1f} %")
    print()
    print(f"   Media global de ganadas: {100*cerr.gana.mean():.1f} %")
    print("   Si un criterio sirviera para cualificar, su columna de la")
    print("   derecha se separaria de esa media. Miresela antes de seguir.")

    # ------------------------------------------------------------------ 3
    titulo(3, "LAS DOS REFERENCIAS: CONTAR SIETE CRITERIOS, Y CONTAR TRES")
    yte = te.gana.values
    p7 = cerr.loc[te.index, "crit7"].values.astype(float)
    p3 = cerr.loc[te.index, "crit3"].values.astype(float)
    a7, a7lo, a7hi = ic_auc(p7, yte)
    a3, a3lo, a3hi = ic_auc(p3, yte)
    print(f"   {'referencia':<34}{'AUC':>8}{'IC 95 %':>20}")
    print("   " + "-" * 62)
    print(f"   {'Azar':<34}{0.500:>8.3f}{'—':>20}")
    print(f"   {'Contar los SIETE criterios':<34}{a7:>8.3f}"
          f"{f'[{a7lo:.3f}, {a7hi:.3f}]':>20}")
    print(f"   {'Contar los TRES que si aparecen':<34}{a3:>8.3f}"
          f"{f'[{a3lo:.3f}, {a3hi:.3f}]':>20}")
    print()
    ordena = a7lo > 0.5 or a3lo > 0.5
    if not ordena:
        print("   NINGUNA DE LAS DOS ORDENA: los dos intervalos cruzan el 0,5.")
        print()
        print("   PERO CUIDADO CON LO QUE ESTO SIGNIFICA, Y CON LO QUE NO.")
        print(f"   En este texto los criterios apenas aparecen: "
              f"{np.mean(cuentas7):.2f} de 7 de media, y dos de los siete no")
        print("   salen practicamente nunca. Contar algo que no esta no puede")
        print("   ordenar nada, de modo que esto NO refuta el marco de los")
        print("   siete criterios: dice que **no es aplicable a este texto**,")
        print("   que son cuatro o cinco palabras escritas por el comercial.")
        print()
        print("   Para refutarlo o confirmarlo haria falta medirlo sobre")
        print("   correos de cliente -donde los criterios si aparecen, 3,1 de")
        print("   7- y esos correos NO traen resultado comercial asociado.")
        print("   Queda como pregunta abierta, no como resultado negativo.")
    else:
        print("   Alguna de las dos ordena por encima del azar. Ver cual y")
        print("   cuanto antes de dar por bueno el marco completo.")

    # ------------------------------------------------------------------ 4
    titulo(4, "EL MODELO: APRENDER DEL TEXTO EN VEZ DE CONTAR")
    vec = TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), min_df=3,
                          max_features=60000)
    Xtr = vec.fit_transform(tr.texto)
    Xte = vec.transform(te.texto)
    clf = LogisticRegression(max_iter=3000, class_weight="balanced")
    clf.fit(Xtr, tr.gana.values)
    pm = clf.predict_proba(Xte)[:, 1]
    am, amlo, amhi = ic_auc(pm, yte)
    acc = 100 * ((pm >= 0.5) == yte.astype(bool)).mean()
    alo, ahi = wilson(int(((pm >= 0.5) == yte.astype(bool)).sum()), len(yte))
    print(f"   Terminos del vocabulario: {Xtr.shape[1]}")
    print()
    print(f"   {'':<34}{'acierto':>10}{'AUC':>8}{'IC 95 %':>20}")
    print("   " + "-" * 72)
    print(f"   {'SUELO':<34}{suelo:>9.1f} %{0.500:>8.3f}{'—':>20}")
    print(f"   {'Contar los siete criterios':<34}{'—':>10}{a7:>8.3f}"
          f"{f'[{a7lo:.3f}, {a7hi:.3f}]':>20}")
    print(f"   {'A7 · aprender del texto':<34}{acc:>9.1f} %{am:>8.3f}"
          f"{f'[{amlo:.3f}, {amhi:.3f}]':>20}")
    print(f"   {'':<34}{f'[{alo:.1f}, {ahi:.1f}]':>10}")
    print()
    print(f"   Sobre el suelo: {acc - suelo:+.1f} puntos de acierto")
    print(f"   Sobre contar criterios: {am - a7:+.3f} de AUC")

    # ------------------------------------------------------------------ 5
    titulo(5, "¿ESTA LEYENDO EL RESULTADO EN VEZ DE PREDECIRLO?")
    print("   El texto lo escribe el comercial, a veces despues de saber como")
    print("   acabo. Se comprueba de dos formas.")
    print()
    con_fuga = cerr.texto.map(lambda t: any(contiene(t, x) for x in FUGA))
    print(f"   1 · Solicitudes con algun termino de resultado: "
          f"{int(con_fuga.sum())} de {len(cerr)} "
          f"({100*con_fuga.mean():.1f} %)")
    if con_fuga.any():
        print(f"       de esas, se ganan el {100*cerr.gana[con_fuga].mean():.1f} % "
              f"(media global {100*cerr.gana.mean():.1f} %)")

    # cuantos terminos influyentes son de resultado
    nombres = np.array(vec.get_feature_names_out())
    coef = clf.coef_[0]
    top = np.argsort(-np.abs(coef))[:200]
    delatores = [n for n in nombres[top]
                 if any(contiene(n, x) for x in FUGA)]
    print()
    print(f"   2 · De los 200 terminos mas influyentes, "
          f"{len(delatores)} son de resultado")
    print("       (no se imprimen: son vocabulario comercial de la casa)")

    # reentrenar sin los terminos de fuga
    quitar = {n for n in nombres if any(contiene(n, x) for x in FUGA)}
    vec2 = TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), min_df=3,
                           max_features=60000,
                           vocabulary=[n for n in nombres if n not in quitar])
    X2tr, X2te = vec2.fit_transform(tr.texto), vec2.transform(te.texto)
    clf2 = LogisticRegression(max_iter=3000, class_weight="balanced")
    clf2.fit(X2tr, tr.gana.values)
    pm2 = clf2.predict_proba(X2te)[:, 1]
    am2, am2lo, am2hi = ic_auc(pm2, yte)
    acc2 = 100 * ((pm2 >= 0.5) == yte.astype(bool)).mean()
    print()
    print(f"   {'':<34}{'acierto':>10}{'AUC':>8}")
    print("   " + "-" * 52)
    print(f"   {'A7 con todo el vocabulario':<34}{acc:>9.1f} %{am:>8.3f}")
    print(f"   {'A7 sin los terminos de resultado':<34}{acc2:>9.1f} %{am2:>8.3f}")
    print(f"   {'Diferencia':<34}{acc2-acc:>+9.1f} p{am2-am:>+8.3f}")
    print()
    if abs(am2 - am) < 0.02:
        print("   NO HAY FUGA APRECIABLE: quitar esos terminos apenas cambia")
        print("   nada, asi que el modelo no se apoyaba en ellos. La cifra")
        print("   buena es la de arriba.")
        limpio = False
    else:
        print("   SI HABIA FUGA. La cifra que vale es la de SIN los terminos de")
        print("   resultado, porque la otra incluye leer el desenlace.")
        limpio = True
    am_bueno, acc_bueno = (am2, acc2) if limpio else (am, acc)

    # ------------------------------------------------------------------ 6
    titulo(6, "A7 SOBRE LOS CORREOS DE CLIENTE REALES")
    cor = pd.read_csv(CORPUS, sep=";")
    cor["texto"] = cor.cuerpo.fillna("").astype(str).map(sin_tildes)
    pc = clf.predict_proba(vec.transform(cor.texto))[:, 1]
    cor["punt"] = pc
    n3c = cor.texto.map(lambda t: criterios(t, TRES)[0])
    print(f"   Correos          : {len(cor)}")
    print(f"   Criterios (de 3) : media {n3c.mean():.2f}")
    print()
    print("   Reparto de la puntuacion de A7:")
    print(f"   {'tramo':<16}{'correos':>9}{'%':>8}")
    print("   " + "-" * 33)
    tramos = {}
    for lo, hi, et in ((0, .25, "muy baja"), (.25, .5, "baja"),
                       (.5, .75, "alta"), (.75, 1.01, "muy alta")):
        n = int(((pc >= lo) & (pc < hi)).sum())
        tramos[et] = n
        print(f"   {et:<16}{n:>9}{100*n/len(cor):>7.1f} %")
    print()
    print("   EL AGENTE CORRE SOBRE TEXTO DE CLIENTE Y DEVUELVE UNA")
    print("   PUNTUACION PARA CADA UNO. Pero no hay con que comprobarla:")
    print("   ninguno de los 105 trae su resultado comercial asociado, asi")
    print("   que esta tabla describe el comportamiento del agente, NO su")
    print("   acierto. Es la limitacion que queda abierta.")

    # ------------------------------------------------------------------ 7
    titulo(7, "VEREDICTO")
    print(f"   A7 ESTA CONSTRUIDO y evaluado sobre {len(te)} solicitudes con")
    print("   resultado real, con particion temporal.")
    print()
    print(f"   · Acierto {acc_bueno:.1f} % frente a un suelo de {suelo:.1f} %  "
          f"({acc_bueno-suelo:+.1f})")
    print(f"   · AUC {am_bueno:.3f}  frente a contar criterios: {a7:.3f}")
    print()
    print("   LO QUE NO SOSTIENE:")
    print("   · Se entrena y se prueba con texto del comercial, no del")
    print("     cliente. Sobre correo real corre, pero su acierto ahi NO")
    print("     esta medido. Es el mismo limite que A8 tenia antes de A6.")
    print("   · Cualifica con tres criterios de los siete del diseno, porque")
    print("     los otros cuatro no aparecen ni en el 36 % de los correos.")
    print("   · No mide el efecto de cualificar: mide si ordena.")

    if not guardar:
        print()
        print("   Simulacion: no se ha escrito nada. Usa --guardar.")
        print()
        return

    salida = {
        "experimento": "E34", "agente": "A7", "version": VERSION_SCRIPT,
        "n": {"con_texto": int(len(d)), "cerradas": int(len(cerr)),
              "entrena": int(len(tr)), "prueba": int(len(te)),
              "correos_cliente": int(len(cor))},
        "particion": {"entrena_hasta": TRIM_TRAIN_FIN, "prueba": TRIM_TEST},
        "suelo": suelo,
        "criterios": {"media_de_7_en_crm": float(np.mean(cuentas7)),
                      "media_de_7_en_correos": 3.1,
                      "por_criterio": por_crit,
                      "tres_elegidos": TRES},
        "referencias": {"contar_siete": {"auc": a7, "ic": [a7lo, a7hi]},
                        "contar_tres": {"auc": a3, "ic": [a3lo, a3hi]},
                        "ordenan_por_encima_del_azar": bool(ordena),
                        "lectura": "los criterios apenas aparecen en este texto, asi que NO ordenar aqui no refuta el marco: lo deja sin probar"},
        "modelo": {"acierto": acc, "acierto_ic": [alo, ahi],
                   "auc": am, "auc_ic": [amlo, amhi]},
        "sin_terminos_de_resultado": {"acierto": acc2, "auc": am2,
                                      "hubo_fuga": bool(limpio),
                                      "influyentes_delatores": len(delatores),
                                      "solicitudes_con_fuga": int(con_fuga.sum())},
        "cifra_publicable": {"acierto": acc_bueno, "auc": am_bueno},
        "sobre_correos_reales": {"reparto": tramos,
                                 "criterios_media_de_3": float(n3c.mean()),
                                 "acierto": None,
                                 "por_que_no": "ningun correo trae su "
                                               "resultado comercial asociado"},
    }
    RES.mkdir(parents=True, exist_ok=True)
    f = RES / "a7_cualificacion_solicitud.json"
    f.write_text(json.dumps(salida, ensure_ascii=False, indent=1, default=float),
                 encoding="utf-8")
    print()
    print(f"   [ok] {f.name}")
    print()


if __name__ == "__main__":
    main()
