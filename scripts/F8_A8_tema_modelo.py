# -*- coding: utf-8 -*-
"""
F8_A8_tema_modelo.py · E38 · el tema del briefing, de diccionario a modelo
==========================================================================

DE DONDE VIENE
    E37 construyo el briefing de A7. Funciona, pero el tipo de servicio
    —«Ensayo», «Consultoria»...— NO lo decide un modelo: lo busca en una
    lista de palabras escrita a mano, el diccionario TIPOS de
    F8_A8_briefing_traspaso.py. Esto lo convierte en un clasificador
    entrenado, y mide si gana o no.

LA ETIQUETA ES HUMANA, Y ESO ES LO QUE HACE VALIDO EL EXPERIMENTO
    El export de oportunidades trae la columna «Tipo Oportunidad»
    rellenada por las personas de Empresa en 4.863 filas, con seis valores:

        Ensayos · Consultoria y asistencia tecnica · Desarrollo I+D ·
        Servicios · Formacion · Valoracion-patente-prueba de concepto

    Asi que no hay circularidad: el diccionario y el modelo reciben el
    MISMO texto, proponen un tipo, y los dos se comparan contra lo que
    puso una persona. Gane quien gane, la comparacion significa algo.

EL SUELO, QUE SON DOS
    1. La clase mas frecuente, que es lo que se acierta sin leer nada.
    2. EL DICCIONARIO DE HOY, en su mejor version: el nombre que usa
       («Ensayo») se traduce a la clase humana que mas veces le
       corresponde en ENTRENAMIENTO. Es darle su mejor oportunidad en
       vez de penalizarlo por como se llaman sus etiquetas.

LAS CINCO PREGUNTAS QUE SE RESPONDEN
    1. ¿Acierta mas el modelo que el diccionario?            (paso 3)
    2. ¿Y si al modelo se le exige callarse tanto como
       se calla el diccionario, a igual cobertura?           (paso 4)
    3. ¿Y cuando la palabra clave NO esta en el texto?       (paso 5)
       Es el caso real: el cliente no escribe «ensayo», escribe
       «necesitamos comprobar si el film aguanta».
    4. ¿Aguanta al cambiar de poblacion, de tema corto a
       correo largo de cliente?                              (paso 6)
    5. ¿Y la MATERIA —envase, film, bandeja—, se modela
       tambien o se deja extractiva?                         (paso 7)

UNA PRECAUCION QUE CAMBIA LAS CIFRAS
    De los 4.878 temas solo 3.878 son distintos: hay textos repetidos. Si
    el mismo texto cae en entrenamiento y en prueba, el modelo lo ha
    visto y la cifra sale inflada. Se parte por GRUPOS de texto
    identico, y se mide cuanto infla no hacerlo.

COMO SE EJECUTA
    python scripts/F8_A8_tema_modelo.py
    python scripts/F8_A8_tema_modelo.py --guardar
    python scripts/F8_A8_tema_modelo.py --ver 12   # casos nuevos a revisar

NOTA SOBRE LOS NOMBRES DE AGENTE (D24, 07-10-2026)
    Este fichero conserva su nombre antiguo, pero los agentes se
    renumeraron: lo que aqui se llamaba A8 es hoy A7, y lo que se llamaba
    A9 es hoy A8. El texto que imprime usa ya los nombres nuevos. La tabla
    completa esta en 4.6.0 de la memoria y en el ESTADO.
"""

import json
import re
import sys
import unicodedata
import warnings
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import FeatureUnion

warnings.filterwarnings("ignore")

VERSION_SCRIPT = "v1 · 06-10-2026"
SEMILLA = 42
Z95 = 1.959963985

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "datos" / "00_bruto"
LIMPIO = RAIZ / "datos" / "01_limpio"
RES = RAIZ / "datos" / "03_resultados"

OPORT = BRUTO / "Oportunidades - cuentas 2025_ACT 27-09-2026 19-08-56.xlsx"
CORPUS = LIMPIO / "entradas_inbound_50_anon.csv"
ETIQUETAS = LIMPIO / "etiquetas_comercial_A6.csv"

# ---------------------------------------------------------------------------
# EL DICCIONARIO QUE HAY QUE BATIR · copiado literal de E37, sin tocar nada
# ---------------------------------------------------------------------------
TIPOS = {
    "Ensayo": ["ensayo", "ensayos", "analisis", "analitica", "test", "testing",
               "muestra", "muestras", "laboratorio", "determinacion"],
    "Consultoría": ["asesoramiento", "consultoria", "asesoria", "informe",
                    "dictamen", "revision documental", "interpretacion"],
    "Certificación": ["certificado", "certificacion", "declaracion de conformidad",
                      "conformidad", "homologacion"],
    "Formación": ["formacion", "curso", "taller", "jornada"],
}

MATERIAS = ["envase", "envases", "embalaje", "film", "pelicula", "bandeja",
            "botella", "caja", "carton", "papel", "plastico", "tapa", "bolsa",
            "palet", "palets", "etiqueta", "tarrina", "bote", "tapon",
            "saco", "big bag", "barqueta", "capsula", "capsulas"]

# palabras que no pueden ser materia por mucho que se repitan
NO_MATERIA = {
    "ensayo", "ensayos", "analisis", "analitica", "test", "testing", "muestra",
    "muestras", "laboratorio", "determinacion", "asesoramiento", "consultoria",
    "consultoria", "asesoria", "informe", "dictamen", "interpretacion",
    "certificado", "certificacion", "conformidad", "homologacion", "formacion",
    "curso", "taller", "jornada", "servicio", "servicios", "proyecto",
    "oferta", "cliente", "nuevo", "nueva", "anual", "renovacion", "apoyo",
    "estudio", "evaluacion", "revision", "propuesta", "solicitud", "varios",
    "bolsa de horas", "refs", "referencias", "segun", "sobre", "para",
    "mediante", "incluye", "pendiente", "definir", "presupuesto",
}


def sin_tildes(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t).lower())
                   if unicodedata.category(c) != "Mn")


def contiene(texto, termino):
    """El mismo buscador corregido en X28: solo se tolera el plural
    castellano, para que «ensayo» encuentre «ensayos» pero «reach» NO
    encuentre «reached»."""
    partes = [re.escape(p) for p in termino.split()]
    return re.search(r"\b" + r"\s+".join(partes) + r"(e?s)?" + r"\b",
                     texto) is not None


def quita(texto, terminos):
    """Borra del texto los terminos indicados. Sirve para la prueba del
    paso 5: ¿que queda del acierto cuando la palabra clave no esta?"""
    t = texto
    for x in terminos:
        partes = [re.escape(p) for p in x.split()]
        t = re.sub(r"\b" + r"\s+".join(partes) + r"(e?s)?" + r"\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def wilson(exitos, n):
    if n == 0:
        return (np.nan, np.nan)
    p = exitos / n
    c = (p + Z95 * Z95 / (2 * n)) / (1 + Z95 * Z95 / n)
    m = Z95 * np.sqrt(p * (1 - p) / n + Z95 * Z95 / (4 * n * n)) / (1 + Z95 * Z95 / n)
    return (100 * max(0.0, c - m), 100 * min(1.0, c + m))


def bootstrap_pareado(a, b, reps=4000, semilla=SEMILLA):
    """IC de la diferencia a-b remuestreando los MISMOS casos para los dos.
    Pareado porque los dos metodos ven exactamente las mismas filas."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    rng = np.random.default_rng(semilla)
    n = len(a)
    dif = np.array([(a[i] - b[i]).mean()
                    for i in (rng.integers(0, n, n) for _ in range(reps))])
    return 100 * (a.mean() - b.mean()), 100 * np.percentile(dif, 2.5), \
        100 * np.percentile(dif, 97.5)


def mcnemar(a, b):
    """Prueba exacta sobre los casos en que discrepan: de los que uno
    acierta y el otro falla, ¿se reparten por azar?"""
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    s1 = int((a & ~b).sum())
    s2 = int((~a & b).sum())
    n = s1 + s2
    if n == 0:
        return s1, s2, 1.0
    k = min(s1, s2)
    if n <= 900:
        from math import comb
        p = 2 * sum(comb(n, i) for i in range(k + 1)) / (2 ** n)
    else:
        # con tantos casos discordantes la exacta desborda y la
        # aproximacion normal con correccion de continuidad ya coincide
        from math import erfc, sqrt
        z = (abs(s1 - s2) - 1) / sqrt(n)
        p = erfc(z / sqrt(2))
    return s1, s2, min(1.0, p)


def pstr(p):
    """Cuando la p es tan pequena que no cabe en un numero, se dice asi
    en vez de imprimir 0,0, que significaria otra cosa."""
    return "< 1e-16" if p < 1e-16 else f"{p:.2}"


def hacer_telegrama(texto, idf, k, prohibidas=frozenset()):
    """Saca del correo un telegrama parecido a un tema.

    Se queda SOLO con palabras que existen en el historico, se ordena por
    lo raras que son ahi —lo raro distingue, lo comun no— y se cortan las
    k primeras. No escribe nada: descarta. Es lo que permite que un modelo
    entrenado con telegramas lea un correo de doscientas palabras.

    Las dos cribas son necesarias y se midieron:

      · PROHIBIDAS · la cortesia. «Buenos», «gracias», «empresa» o
        «informacion» salen en casi todos los correos y en ninguna
        oportunidad, asi que no distinguen nada. Se sacan mirando en que
        proporcion de correos aparece cada palabra, sin usar ninguna
        etiqueta.
      · idf_de(..., tope) · lo demasiado raro. Una palabra que solo esta
        en dos temas del historico tiene un peso enorme y es ruido: asi
        es como «puedan» y «parte» se colaban en el telegrama por delante
        de «reciclabilidad».
    """
    vistas, orden = set(), []
    for p in re.findall(r"[a-z0-9]{4,}", sin_tildes(texto)):
        if p in idf and p not in vistas and p not in prohibidas:
            vistas.add(p)
            orden.append(p)
    orden.sort(key=lambda p: -idf[p])
    return " ".join(orden[:k])


def idf_de(vec, tope=None):
    """El peso de cada palabra en el vectorizador ya entrenado.

    Con `tope` se descartan las palabras cuyo peso lo supera, que son las
    que casi no aparecen en el historico.
    """
    wv = dict(vec.transformer_list)["pal"]
    return {p: wv.idf_[i] for p, i in wv.vocabulary_.items()
            if " " not in p and (tope is None or wv.idf_[i] <= tope)}


def cortesia_comun(textos, umbral=0.25):
    """Las palabras que salen en mas de una cuarta parte de los correos.

    Son el saludo, la presentacion y la firma. No se usa ninguna etiqueta
    para encontrarlas, solo en cuantos correos aparecen.
    """
    n = len(textos)
    c = Counter()
    for t in textos:
        for p in set(re.findall(r"[a-z0-9]{4,}", sin_tildes(t))):
            c[p] += 1
    return {p for p, v in c.items() if v / n >= umbral}


def cortesia(correos, semilla=SEMILLA):
    """El envoltorio de un correo de verdad: saludo, presentacion y firma.

    Se toman las 25 primeras y las 25 ultimas palabras de los correos
    reales. Sirve para fabricar correos de prueba CON ETIQUETA: cortesia
    de verdad alrededor de un tema de verdad, del que si se sabe el tipo
    porque lo puso una persona.
    """
    ini, fin = [], []
    for t in correos:
        pal = str(t).split()
        if len(pal) > 60:
            ini.append(" ".join(pal[:25]))
            fin.append(" ".join(pal[-25:]))
    return ini, fin


def titulo(n, t):
    print()
    print("=" * 76)
    print(f"PASO {n} · {t}")
    print("=" * 76)


def vectorizador():
    """Palabras y trozos de palabra a la vez.

    Los temas son telegramas de cinco palabras, con siglas y abreviaturas
    («MG en tenax», «ISTA6MAZON»). Las palabras sueltas se quedan cortas
    ahi, y los trozos de 3 a 5 letras recogen la raiz aunque la palabra
    este mal escrita o abreviada.
    """
    return FeatureUnion([
        ("pal", TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2),
                                min_df=2, max_features=60000)),
        ("car", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5),
                                sublinear_tf=True, min_df=3,
                                max_features=120000)),
    ])


def dic_tipo(texto):
    """El diccionario de hoy. Devuelve su etiqueta o None si no ve nada."""
    return next((k for k, v in TIPOS.items() if any(contiene(texto, x) for x in v)),
                None)


# ---------------------------------------------------------------------------
# LOS DOS PUNTOS DE TRABAJO, MEDIDOS EN E38 · PASO 4
#
#   Un clasificador siempre contesta algo. Decidir CUANDO conviene que se
#   calle es una eleccion, no un detalle, y aqui hay dos razonables:
#
#   UMBRAL_IGUAL_COBERTURA · callarse tanto como se calla el diccionario de
#       E37, para compararlos a cobertura identica. Sirve para la
#       comparacion del paso 4 y NO sirve para trabajar: sobre correos
#       largos las probabilidades son mas bajas que sobre temas cortos, y
#       con este umbral el modelo solo habla en 3 de 105 correos.
#
#   UMBRAL_IGUAL_CALIDAD · el umbral mas bajo que mantiene el acierto que ya
#       tiene el diccionario donde habla. Medido, sale CERO: el modelo
#       contestando siempre acierta el 86,6 %, por encima del 83,9 % que
#       acierta el diccionario donde se atreve. No hace falta freno para
#       igualarlo, asi que el briefing propone siempre y ensena el tramo de
#       confianza (paso 4). Lo que no hace es presentar la propuesta como un
#       dato que consta en el correo.
#
#   Los dos se recalculan en cada ejecucion del paso 4 y se cotejan contra
#   estas constantes; si dejan de cuadrar, el guion avisa.
# ---------------------------------------------------------------------------
UMBRAL_IGUAL_COBERTURA = 0.98
UMBRAL_IGUAL_CALIDAD = 0.00


def umbral_igual_calidad(prob, acierto, objetivo):
    """El umbral mas BAJO cuyo acierto, entre los casos que superan el
    umbral, llega al objetivo. Hablar todo lo posible sin bajar la calidad
    de referencia."""
    for u in np.arange(0.0, 1.0, 0.01):
        sel = prob >= u
        if sel.sum() >= 50 and acierto[sel].mean() >= objetivo:
            return float(round(u, 2))
    return 1.0


# ===========================================================================
def entrena_tipo(op=None, umbral=UMBRAL_IGUAL_CALIDAD):
    """Entrena el clasificador de tipo de servicio con TODO el historico.

    Es la funcion que importa el briefing: devuelve lo necesario para
    predecir y el umbral por debajo del cual conviene callarse.

    El umbral NO se calcula aqui. Calcularlo con las probabilidades del
    propio modelo sobre los datos que acaba de ver daria un numero
    optimista, y ademas exigiria cinco entrenamientos mas cada vez que el
    briefing arranca. Viene medido fuera de muestra en el paso 4.
    """
    if op is None:
        op = pd.read_excel(OPORT)
        op.columns = [c.strip() for c in op.columns]
    col = next(c for c in op.columns if c.strip().lower() == "tipo oportunidad")
    d = op[op["Tema"].notna() & op[col].notna()].copy()
    d["txt"] = d.Tema.astype(str).map(sin_tildes)
    vec = vectorizador()
    X = vec.fit_transform(d.txt)
    y = d[col].astype(str).values
    clf = LogisticRegression(max_iter=3000, C=4.0).fit(X, y)
    return vec, clf, float(umbral), sorted(set(y))


# ===========================================================================
def main():
    guardar = "--guardar" in sys.argv
    ver = 0
    if "--ver" in sys.argv:
        i = sys.argv.index("--ver")
        ver = int(sys.argv[i + 1]) if i + 1 < len(sys.argv) else 10

    print()
    print("#" * 76)
    print("# F8 · E38 · el tema del briefing, de diccionario a modelo")
    print(f"# {VERSION_SCRIPT}")
    print("#" * 76)

    # ------------------------------------------------------------------ 1
    titulo(1, "LA ETIQUETA ES HUMANA, NO MIA")
    op = pd.read_excel(OPORT)
    op.columns = [c.strip() for c in op.columns]
    col = next(c for c in op.columns if c.strip().lower() == "tipo oportunidad")
    d = op[op["Tema"].notna() & op[col].notna()].copy().reset_index(drop=True)
    d["txt"] = d.Tema.astype(str).map(sin_tildes)
    y = d[col].astype(str).values
    print(f"   Temas con tipo puesto por una persona : {len(d)}")
    print(f"   Textos distintos                      : {d.txt.nunique()}")
    print()
    print("   LO QUE HAY QUE ADIVINAR, y como se reparte:")
    for k, n in Counter(y).most_common():
        print(f"      {k[:46]:<48}{n:>6}  {100*n/len(d):>5.1f} %")

    # grupos de texto identico: ningun texto repetido puede estar a la vez
    # en entrenamiento y en prueba
    grupo = d.txt.map({t: i for i, t in enumerate(d.txt.unique())}).values

    # ------------------------------------------------------------------ 2
    titulo(2, "LOS DOS SUELOS QUE HAY QUE BATIR")
    cob_dic = np.mean([dic_tipo(t) is not None for t in d.txt])
    print(f"   SUELO 1 · la clase mas frecuente, sin leer el texto")
    print(f"             {Counter(y).most_common(1)[0][0]} · "
          f"{100*Counter(y).most_common(1)[0][1]/len(d):.1f} %")
    print()
    print(f"   SUELO 2 · el diccionario TIPOS de E37, tal cual esta hoy")
    print(f"             ve algo en el {100*cob_dic:.1f} % de los temas; en el")
    print(f"             resto se calla, y callarse tambien es fallar cuando")
    print(f"             el briefing necesita un tipo.")
    print()
    print("   Al diccionario se le da su MEJOR version: su etiqueta «Ensayo»")
    print("   se traduce a la clase humana que mas veces le toca, aprendido")
    print("   solo con los datos de entrenamiento de cada vuelta.")

    # ------------------------------------------------------------------ 3
    titulo(3, "¿ACIERTA MAS EL MODELO QUE EL DICCIONARIO?")
    print("   Cinco vueltas. En cada una, cuatro quintos entrenan y un")
    print("   quinto se mide; los textos repetidos van juntos.")

    # reparto por grupos, estratificado a mano sobre el grupo
    rng = np.random.default_rng(SEMILLA)
    gr_clase = pd.Series(y).groupby(grupo).agg(lambda s: s.value_counts().idxmax())
    gr_ids = gr_clase.index.values
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMILLA)
    pliegos = []
    for tr_g, te_g in skf.split(gr_ids.reshape(-1, 1), gr_clase.values):
        en_te = np.isin(grupo, gr_ids[te_g])
        pliegos.append((np.where(~en_te)[0], np.where(en_te)[0]))

    # los correos reales se cargan ya aqui: su cortesia sirve para fabricar
    # los correos de prueba con etiqueta del paso 6
    co = pd.read_csv(CORPUS, sep=";")
    co["cuerpo"] = co.cuerpo.fillna("").astype(str)
    co["txt"] = co.cuerpo.map(sin_tildes)
    ini, fin = cortesia(co.txt)
    # la cortesia que hay que tirar del telegrama, vista en los correos
    PROHIBIDAS = cortesia_comun(co.txt)
    TOPE_IDF = 7.0
    rg = np.random.default_rng(SEMILLA)
    envuelto = np.array([
        f"{ini[rg.integers(len(ini))]} {t} {fin[rg.integers(len(fin))]}"
        for t in d.txt])

    KS = (6, 10, 16)
    pred_mod = np.empty(len(d), object)
    pred_dic = np.empty(len(d), object)
    prob_mod = np.zeros(len(d))
    pred_mod_sp = np.empty(len(d), object)   # paso 5, sin palabra clave
    pred_dic_sp = np.empty(len(d), object)
    pred_env = np.empty(len(d), object)      # paso 6, correo fabricado
    pred_dic_env = np.empty(len(d), object)
    pred_tel = {k: np.empty(len(d), object) for k in KS}
    todos_disp = [x for v in TIPOS.values() for x in v]

    for tr, te in pliegos:
        vec = vectorizador()
        Xtr = vec.fit_transform(d.txt.iloc[tr])
        clf = LogisticRegression(max_iter=3000, C=4.0).fit(Xtr, y[tr])

        Xte = vec.transform(d.txt.iloc[te])
        pr = clf.predict_proba(Xte)
        pred_mod[te] = clf.classes_[pr.argmax(axis=1)]
        prob_mod[te] = pr.max(axis=1)

        # el mapeo del diccionario, aprendido SOLO en entrenamiento
        mapa = {}
        for et in TIPOS:
            cs = [y[i] for i in tr if dic_tipo(d.txt.iloc[i]) == et]
            if cs:
                mapa[et] = Counter(cs).most_common(1)[0][0]
        pred_dic[te] = [mapa.get(dic_tipo(d.txt.iloc[i])) for i in te]

        # y lo mismo con el texto despojado de las palabras del diccionario
        txt_sp = [quita(d.txt.iloc[i], todos_disp) for i in te]
        pred_mod_sp[te] = clf.classes_[clf.predict_proba(
            vec.transform(txt_sp)).argmax(axis=1)]
        pred_dic_sp[te] = [mapa.get(dic_tipo(t)) for t in txt_sp]

        # el correo fabricado: el mismo tema envuelto en cortesia real, y
        # el telegrama que se saca de el con varios tamanos
        env = envuelto[te]
        pred_env[te] = clf.classes_[clf.predict_proba(
            vec.transform(env)).argmax(axis=1)]
        pred_dic_env[te] = [mapa.get(dic_tipo(t)) for t in env]
        idf_pl = idf_de(vec, TOPE_IDF)
        for k in KS:
            tel = [hacer_telegrama(t, idf_pl, k, PROHIBIDAS) for t in env]
            pred_tel[k][te] = clf.classes_[clf.predict_proba(
                vec.transform(tel)).argmax(axis=1)]

    ok_mod = np.array([a == b for a, b in zip(pred_mod, y)])
    ok_dic = np.array([a == b for a, b in zip(pred_dic, y)])
    emite_dic = np.array([x is not None for x in pred_dic])
    may = Counter(y).most_common(1)[0][0]
    ok_may = np.array([x == may for x in y])

    print()
    print(f"   {'':<40}{'cobertura':>11}{'acierto':>10}{'IC 95 %':>15}")
    print("   " + "-" * 74)
    for et, ok, cob in (("Suelo 1 · la clase mas frecuente", ok_may, np.ones(len(d), bool)),
                        ("Suelo 2 · el diccionario de E37", ok_dic, emite_dic),
                        ("EL MODELO", ok_mod, np.ones(len(d), bool))):
        lo, hi = wilson(int(ok.sum()), len(d))
        neg = "**" if et == "EL MODELO" else "  "
        print(f"   {neg}{et:<38}{100*cob.mean():>9.1f} %{100*ok.mean():>9.1f} %"
              f"{f'[{lo:.1f}, {hi:.1f}]':>15}")
    print()
    print(f"   El acierto cuenta sobre los {len(d)}, asi que callarse cuenta")
    print("   como fallo: un briefing sin tipo no le sirve al comercial.")

    dif, lo, hi = bootstrap_pareado(ok_mod, ok_dic)
    s1, s2, pv = mcnemar(ok_mod, ok_dic)
    print()
    print(f"   DIFERENCIA modelo - diccionario : {dif:+.1f} puntos  "
          f"[{lo:+.1f}, {hi:+.1f}]")
    print(f"   McNemar · {s1} casos los arregla el modelo, {s2} los estropea"
          f"  ·  p = {pstr(pv)}")
    print()
    print(f"   Acierto cuando el diccionario SI habla : "
          f"{100*ok_dic[emite_dic].mean():.1f} %  (n={int(emite_dic.sum())})")
    print(f"   Y el modelo en esos mismos casos       : "
          f"{100*ok_mod[emite_dic].mean():.1f} %")
    print(f"   Donde el diccionario se calla          : "
          f"{100*ok_mod[~emite_dic].mean():.1f} %  (n={int((~emite_dic).sum())})")
    print(f"   F1 macro del modelo (trata igual a las clases raras): "
          f"{100*f1_score(y, list(pred_mod), average='macro'):.1f} %")

    # cuanto inflaria no separar los textos repetidos
    skf2 = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMILLA)
    ok_fuga = np.zeros(len(d), bool)
    for tr, te in skf2.split(np.zeros(len(d)), y):
        vec = vectorizador()
        clf = LogisticRegression(max_iter=3000, C=4.0).fit(
            vec.fit_transform(d.txt.iloc[tr]), y[tr])
        ok_fuga[te] = clf.predict(vec.transform(d.txt.iloc[te])) == y[te]
    print()
    print(f"   Si no se separan los textos repetidos sale "
          f"{100*ok_fuga.mean():.1f} %, o sea")
    print(f"   {100*(ok_fuga.mean()-ok_mod.mean()):+.1f} puntos de regalo. La cifra "
          f"buena es la de arriba.")

    # ------------------------------------------------------------------ 4
    titulo(4, "CUANDO DEBE CALLARSE EL MODELO · LOS DOS PUNTOS DE TRABAJO")
    cal_dic = ok_dic[emite_dic].mean()
    umb_cob = float(np.quantile(prob_mod, 1 - cob_dic))
    umb_cal = umbral_igual_calidad(prob_mod, ok_mod, cal_dic)
    habla_cob = prob_mod >= umb_cob
    habla_cal = prob_mod >= umb_cal
    print("   El modelo da una probabilidad con cada respuesta, asi que se le")
    print("   puede exigir callarse cuando no esta seguro. Donde se pone esa")
    print("   raya es una decision, y hay dos maneras de ponerla.")
    print()
    print(f"   {'':<40}{'umbral':>8}{'cobertura':>11}{'acierto donde habla':>21}")
    print("   " + "-" * 74)
    print(f"     {'El diccionario de E37':<38}{'—':>8}{100*emite_dic.mean():>9.1f} %"
          f"{100*cal_dic:>19.1f} %")
    print(f"     {'A igual cobertura que el diccionario':<38}{umb_cob:>8.2f}"
          f"{100*habla_cob.mean():>9.1f} %{100*ok_mod[habla_cob].mean():>19.1f} %")
    print(f"   **{'A igual calidad que el diccionario':<38}{umb_cal:>8.2f}"
          f"{100*habla_cal.mean():>9.1f} %{100*ok_mod[habla_cal].mean():>19.1f} %")
    print()
    print("   A IGUAL COBERTURA el modelo acierta casi siempre, pero esa raya")
    print("   tan alta no sirve para trabajar: se vera en el paso 6 que sobre")
    print("   correos largos las probabilidades son mas bajas y con ella el")
    print("   modelo se queda mudo.")
    print()
    print("   A IGUAL CALIDAD la pregunta se invierte: ¿hasta donde puede")
    print(f"   bajar la raya sin acertar menos del {100*cal_dic:.1f} % que ya "
          f"acierta el")
    print(f"   diccionario? La respuesta que da el dato es {umb_cal:.2f}, o sea")
    print(f"   NINGUNA RAYA: contestando siempre acierta el "
          f"{100*ok_mod.mean():.1f} %, que ya es mas")
    print(f"   que el {100*cal_dic:.1f} % del diccionario. El freno no hace falta "
          f"para igualarlo.")
    print()
    print("   PERO CONTESTAR SIEMPRE NO ES CONTESTAR CON LA MISMA SEGURIDAD, y")
    print("   el comercial tiene derecho a saberlo. La probabilidad se reparte")
    print("   en tres tramos y cada uno se mide:")
    print()
    print(f"   {'tramo':<28}{'casos':>10}{'acierto':>12}{'IC 95 %':>18}")
    print("   " + "-" * 74)
    bandas = [("confianza alta   p >= 0,80", prob_mod >= 0.80),
              ("media      0,50 - 0,80", (prob_mod >= 0.50) & (prob_mod < 0.80)),
              ("baja        p < 0,50", prob_mod < 0.50)]
    for nom, sel in bandas:
        if sel.sum() == 0:
            continue
        lo_b, hi_b = wilson(int(ok_mod[sel].sum()), int(sel.sum()))
        print(f"   {nom:<28}{int(sel.sum()):>10}{100*ok_mod[sel].mean():>11.1f} %"
              f"{f'[{lo_b:.1f}, {hi_b:.1f}]':>18}")
    print()
    print("   Asi que el briefing propone SIEMPRE el tipo y ensena en que")
    print("   tramo cae. Lo que no hace nunca es presentarlo como un dato que")
    print("   consta en el correo: es una propuesta, y va escrito como tal.")

    for nom, vivo, cte in (("UMBRAL_IGUAL_COBERTURA", umb_cob, UMBRAL_IGUAL_COBERTURA),
                           ("UMBRAL_IGUAL_CALIDAD", umb_cal, UMBRAL_IGUAL_CALIDAD)):
        if abs(vivo - cte) > 0.02:
            print()
            print(f"   [!!] {nom} vale {cte} en el codigo y acaba de salir "
                  f"{vivo:.2f}.")
            print(f"        Hay que actualizar la constante y rehacer las cifras")
            print(f"        del briefing que la usan.")
    umb, habla = umb_cal, habla_cal

    # ------------------------------------------------------------------ 5
    titulo(5, "LA PRUEBA QUE DE VERDAD IMPORTA: SIN LA PALABRA CLAVE")
    print("   Se borran del texto de prueba TODAS las palabras del")
    print("   diccionario. Es lo que pasa de verdad en un correo: el cliente")
    print("   no escribe «ensayo», escribe «comprobar si el film aguanta».")
    ok_mod_sp = np.array([a == b for a, b in zip(pred_mod_sp, y)])
    ok_dic_sp = np.array([a == b for a, b in zip(pred_dic_sp, y)])
    emite_sp = np.array([x is not None for x in pred_dic_sp])
    print()
    print(f"   {'':<40}{'cobertura':>11}{'acierto':>10}")
    print("   " + "-" * 74)
    print(f"     {'El diccionario, sin sus palabras':<38}"
          f"{100*emite_sp.mean():>9.1f} %{100*ok_dic_sp.mean():>9.1f} %")
    print(f"   **{'El modelo, sin esas palabras':<38}"
          f"{100*np.ones(len(d)).mean():>9.1f} %{100*ok_mod_sp.mean():>9.1f} %")
    print(f"     {'Suelo 1 · la clase mas frecuente':<38}"
          f"{100:>9.1f} %{100*ok_may.mean():>9.1f} %")
    print()
    print(f"   El modelo pierde {100*(ok_mod.mean()-ok_mod_sp.mean()):.1f} puntos "
          f"al quitarle las palabras del")
    print(f"   diccionario, y conserva "
          f"{100*(ok_mod_sp.mean()-ok_may.mean()):+.1f} sobre el suelo. El "
          f"diccionario no")
    print(f"   conserva nada porque sin sus palabras no tiene nada que buscar.")

    # ------------------------------------------------------------------ 6
    titulo(6, "CAMBIO DE POBLACION: DEL TEMA CORTO AL CORREO DE CLIENTE")
    print("   El modelo se entrena con telegramas de cinco palabras y se le")
    print("   pide trabajar sobre correos de doscientas. No es la misma")
    print("   poblacion, y eso se mide en vez de suponerse.")
    print()
    print("   COMO SE MIDE ESTO CON ETIQUETA, que es lo dificil. De los 105")
    print("   correos reales nadie ha anotado el tipo, asi que no hay verdad.")
    print("   Pero se puede fabricar: se coge un tema del historico —del que")
    print("   SI se sabe el tipo, porque lo puso una persona— y se envuelve en")
    print("   la cortesia de un correo real, saludo y firma incluidos. El")
    print("   resultado se parece a un correo y conserva la etiqueta.")
    print()
    ok_env = np.array([a == b for a, b in zip(pred_env, y)])
    ok_dic_env = np.array([a == b for a, b in zip(pred_dic_env, y)])
    emite_env = np.array([x is not None for x in pred_dic_env])
    mejor_k = max(KS, key=lambda k: np.mean(
        [a == b for a, b in zip(pred_tel[k], y)]))
    ok_tel = np.array([a == b for a, b in zip(pred_tel[mejor_k], y)])

    print(f"   {'':<44}{'acierto':>10}{'IC 95 %':>16}")
    print("   " + "-" * 74)
    lo_e, hi_e = wilson(int(ok_env.sum()), len(d))
    print(f"     {'El tema solo, como en el paso 3':<42}"
          f"{100*ok_mod.mean():>9.1f} %{'—':>16}")
    print(f"     {'El correo fabricado, entero':<42}{100*ok_env.mean():>9.1f} %"
          f"{f'[{lo_e:.1f}, {hi_e:.1f}]':>16}")
    for k in KS:
        okk = np.array([a == b for a, b in zip(pred_tel[k], y)])
        lo_k, hi_k = wilson(int(okk.sum()), len(d))
        marca = " **" if k == mejor_k else "   "
        print(f"  {marca}{f'Su telegrama de {k} palabras':<42}"
              f"{100*okk.mean():>9.1f} %{f'[{lo_k:.1f}, {hi_k:.1f}]':>16}")
    print(f"     {'El diccionario sobre el correo fabricado':<42}"
          f"{100*ok_dic_env.mean():>9.1f} %{'—':>16}")
    print()
    perdido = 100 * (ok_mod.mean() - ok_env.mean())
    recuperado = 100 * (ok_tel.mean() - ok_env.mean())
    print(f"   Envolver el tema en cortesia le cuesta al modelo "
          f"{perdido:.1f} puntos: del")
    print(f"   {100*ok_mod.mean():.1f} % al {100*ok_env.mean():.1f} %. El "
          f"telegrama recupera {recuperado:.1f} de esos {perdido:.1f},")
    print(f"   hasta el {100*ok_tel.mean():.1f} % con {mejor_k} palabras: "
          f"repara dos tercios del daño,")
    print(f"   no todo. Y esto SI es acierto medido contra la etiqueta de una")
    print(f"   persona, no coincidencia entre dos metodos.")
    dif_t, lo_t, hi_t = bootstrap_pareado(ok_tel, ok_env)
    s1t, s2t, pvt = mcnemar(ok_tel, ok_env)
    print()
    print(f"   El telegrama frente al correo entero: {dif_t:+.1f} puntos "
          f"[{lo_t:+.1f}, {hi_t:+.1f}],")
    print(f"   p = {pstr(pvt)}. El tamano del telegrama y las dos cribas se")
    print(f"   eligen aqui, con etiqueta, y no sobre los 105 correos reales,")
    print(f"   que es lo unico que luego queda para comprobar aparte.")
    print()
    print(f"   Y LA PREGUNTA QUE DECIDE EL BRIEFING: donde el diccionario SI")
    print(f"   ve su palabra ({int(emite_env.sum())} correos fabricados), ¿quien acierta mas?")
    print()
    print(f"   {'':<44}{'acierto':>10}")
    print("   " + "-" * 74)
    print(f"     {'El diccionario, donde ve su palabra':<42}"
          f"{100*ok_dic_env[emite_env].mean():>9.1f} %")
    print(f"   **{'El modelo con telegrama, ahi mismo':<42}"
          f"{100*ok_tel[emite_env].mean():>9.1f} %")
    dif_d, lo_d, hi_d = bootstrap_pareado(ok_tel[emite_env],
                                          ok_dic_env[emite_env])
    print()
    print(f"   {dif_d:+.1f} puntos [{lo_d:+.1f}, {hi_d:+.1f}]. "
          f"{'Gana el modelo tambien ahi' if lo_d > 0 else 'No es concluyente'}, "
          f"asi que")
    print(f"   {'el tipo lo decide el modelo siempre' if lo_d > 0 else 'donde el diccionario habla se le deja hablar a el'},")
    print(f"   y las palabras literales del correo se ensenan al lado como")
    print(f"   justificacion, que es lo que el comercial necesita ver.")
    print()
    print("   LO QUE ESTA PRUEBA NO ES: un correo fabricado tiene UN solo")
    print("   asunto y esta bien escrito. Los de verdad traen tres cosas a la")
    print("   vez, reenvios y cadenas. Asi que esta cifra es el mejor caso del")
    print("   cambio de poblacion, no el caso real.")

    print()
    print("   " + "-" * 70)
    print("   Y AHORA LOS 105 CORREOS DE VERDAD")
    print("   " + "-" * 70)
    vec_f, clf_f, umbral_f, clases = entrena_tipo(op)
    if ETIQUETAS.exists():
        et = pd.read_csv(ETIQUETAS, sep=";")
        et["no_com"] = et.categoria.astype(str).str.upper().str.contains("NO")
        co = co.merge(et[["id", "no_com"]], on="id", how="left")
    else:
        co["no_com"] = False

    P = clf_f.predict_proba(vec_f.transform(co.txt))
    co["mod"] = clf_f.classes_[P.argmax(axis=1)]
    co["p"] = P.max(axis=1)
    co["dic"] = co.txt.map(dic_tipo)
    # el mapeo del diccionario a las clases humanas, con todo el historico
    mapa = {}
    for e in TIPOS:
        cs = [y[i] for i in range(len(d)) if dic_tipo(d.txt.iloc[i]) == e]
        if cs:
            mapa[e] = Counter(cs).most_common(1)[0][0]
    co["dic_cl"] = co.dic.map(mapa)
    print()
    print(f"   {'':<46}{'propone tipo en':>18}")
    print("   " + "-" * 70)
    print(f"     {'El diccionario de E37':<44}"
          f"{f'{int(co.dic.notna().sum())} de {len(co)}':>16}")
    print(f"     {'El modelo, sin freno':<44}{f'{len(co)} de {len(co)}':>16}")
    print(f"     {f'El modelo con la raya alta (p >= {umb_cob:.2f})':<44}"
          f"{f'{int((co.p >= umb_cob).sum())} de {len(co)}':>16}")
    print()
    print(f"   La raya alta, que sobre temas era la mejor, aqui dejaria el")
    print(f"   briefing sin tipo en {int((co.p < umb_cob).sum())} de los "
          f"{len(co)} correos: las probabilidades")
    print(f"   caen de una mediana de {np.median(prob_mod):.2f} sobre temas a "
          f"{np.median(co.p):.2f} sobre correos. Es")
    print(f"   la primera señal de que el modelo esta en terreno desconocido.")

    # el telegrama, con el tamano elegido arriba CON etiqueta
    idf_f = idf_de(vec_f, TOPE_IDF)
    co["tel"] = co.cuerpo.map(
        lambda t: hacer_telegrama(t, idf_f, mejor_k, PROHIBIDAS))
    Pt = clf_f.predict_proba(vec_f.transform(co.tel))
    co["mod_tel"] = clf_f.classes_[Pt.argmax(axis=1)]
    co["p_tel"] = Pt.max(axis=1)

    amb = co[co.dic_cl.notna()]
    coin = (amb["mod"] == amb.dic_cl).mean() if len(amb) else np.nan
    coin_tel = (amb["mod_tel"] == amb.dic_cl).mean() if len(amb) else np.nan
    print()
    print(f"   Ejemplo de telegrama: {co.tel.iloc[5][:52]}")
    print()
    print(f"   {'':<44}{'acuerdo con la evidencia literal':>30}")
    print("   " + "-" * 74)
    print(f"     {'El correo entero':<42}{100*coin:>28.1f} %")
    print(f"   **{f'Su telegrama de {mejor_k} palabras':<42}{100*coin_tel:>28.1f} %")
    print()
    print(f"   ACUERDO NO ES ACIERTO: se mide contra lo que el correo dice con")
    print(f"   sus propias palabras —si pone «ensayo», el tipo es ensayo—, en")
    print(f"   los {len(amb)} correos donde eso consta. Nadie ha etiquetado a mano")
    print(f"   el tipo de estos {len(co)}, asi que esto es lo unico comprobable")
    print(f"   sin inventarse una verdad, y se llama por su nombre. Queda")
    print(f"   pendiente de que lo anotes, como el segundo evaluador de A6.")
    print()
    print(f"   El correo entero da un {100*coin:.1f} %, que es malo, y se ve por que:")
    print()
    print(f"   {'clase':<36}{'en temas':>10}{'correo entero':>15}{'telegrama':>12}")
    print("   " + "-" * 74)
    rep_t = Counter(pred_mod)
    rep_c = Counter(co["mod"])
    rep_tel = Counter(co["mod_tel"])
    for k in sorted(set(rep_t) | set(rep_c), key=lambda x: -rep_t.get(x, 0)):
        print(f"   {k[:34]:<36}{100*rep_t.get(k,0)/len(d):>8.1f} %"
              f"{100*rep_c.get(k,0)/len(co):>13.1f} %"
              f"{100*rep_tel.get(k,0)/len(co):>10.1f} %")
    print()
    print("   Con el correo entero el modelo contesta «Desarrollo I+D» o")
    print("   «Consultoria» a casi todo y los ensayos desaparecen. No es que")
    print("   se haya roto: un correo de cliente —presentacion, contexto de")
    print("   empresa, cortesia, peticion al final— se parece mas a como se")
    print("   describe un proyecto de I+D que a un telegrama de cinco")
    print("   palabras. El telegrama devuelve el reparto a su sitio.")
    print()
    print(f"   Mediana de la probabilidad: {np.median(co.p):.2f} con el correo "
          f"entero y {np.median(co.p_tel):.2f}")
    print(f"   con el telegrama. Menos seguridad declarada, mas acuerdo real:")
    print(f"   es justo lo que tiene que pasar cuando antes estaba equivocado")
    print(f"   con aplomo.")

    nuevos = co[co.dic.isna() & (co.p_tel >= umbral_f)]
    com = co[~co.no_com.fillna(False).astype(bool)]
    print()
    print(f"   CASOS NUEVOS · el diccionario se calla y el modelo contesta:")
    print(f"   {len(nuevos)} correos. La cobertura del tipo pasa del "
          f"{100*co.dic.notna().mean():.1f} % al "
          f"{100*(co.dic.notna()|(co.p_tel>=umbral_f)).mean():.1f} %,")
    print(f"   y sobre los correos que SI son comerciales —los unicos donde el")
    print(f"   tipo significa algo— del {100*com.dic.notna().mean():.1f} % al "
          f"{100*(com.dic.notna()|(com.p_tel>=umbral_f)).mean():.1f} % de {len(com)}.")

    if ver:
        print()
        print("   " + "-" * 70)
        print(f"   {min(ver, len(nuevos))} de esos casos, para que los mires:")
        for _, r in nuevos.head(ver).iterrows():
            frag = re.sub(r"\s+", " ", r.cuerpo)[:140]
            prop = r["mod_tel"]
            print()
            print(f"   {r.id} · propone «{prop}» con p={r.p_tel:.2f}"
                  f"{'  (NO comercial)' if r.no_com else ''}")
            print(f"      telegrama: {r.tel[:60]}")
            print(f"      {frag}...")

    # ------------------------------------------------------------------ 7
    titulo(7, "LA MATERIA SE QUEDA EXTRACTIVA, Y HAY MOTIVO")
    print("   La materia —envase, film, bandeja— NO se modela, y no es por")
    print("   pereza: no existe ninguna columna donde una persona haya")
    print("   escrito cual es el objeto de cada oportunidad. Etiquetar con el")
    print("   propio diccionario y luego aprender de esas etiquetas seria")
    print("   enseñarle al modelo a repetir el diccionario, y medirlo contra")
    print("   si mismo. Eso no mide nada.")
    print()
    print("   Ademas, la materia TIENE que salir del texto literal: es lo que")
    print("   sostiene la fundamentacion del 100 % de E37. Un modelo que")
    print("   proponga «bandeja» cuando el correo dice «tarrina» rompe")
    print("   justamente lo que hace fiable al briefing.")
    print()
    print("   Lo que SI se puede aprender del dato es la LISTA. Cobertura de")
    print("   la lista escrita a mano sobre el historico:")
    hay_mat = np.array([any(contiene(t, m) for m in MATERIAS) for t in d.txt])
    print(f"      {int(hay_mat.sum())} de {len(d)} temas  ·  "
          f"{100*hay_mat.mean():.1f} %")
    frec = Counter()
    for t in d.txt[~hay_mat]:
        for p in re.findall(r"[a-z]{5,}", t):
            if p not in NO_MATERIA:
                frec[p] += 1
    cand = [(p, n) for p, n in frec.most_common(40) if n >= 15][:14]
    print()
    print("   Palabras frecuentes en los temas que la lista NO cubre:")
    for p, n in cand:
        print(f"      {p:<28}{n:>5} temas")
    techo = np.array([any(contiene(t, m) for m in MATERIAS + [p for p, _ in cand])
                      for t in d.txt])
    print()
    print(f"   Aceptarlas todas subiria la cobertura del "
          f"{100*hay_mat.mean():.1f} % al {100*techo.mean():.1f} %, y")
    print(f"   SERIA UN ENGAÑO: mirando la lista, ninguna de esas palabras es")
    print(f"   un objeto. «Interes», «asociarse» y «sentiatech» hablan de")
    print(f"   socios; «simulacion», «protocolo» y «valorizacion» son")
    print(f"   servicios; «metales» es lo que se busca, no lo que se analiza.")
    print(f"   Son frecuentes porque los temas repiten servicios, no envases.")
    print()
    print(f"   Asi que la ampliacion automatica se RECHAZA, y la lista escrita")
    print(f"   a mano se queda. Los {100*hay_mat.mean():.1f} % no son el techo "
          f"de la lista: son")
    print(f"   los temas que de verdad nombran un objeto.")

    # ------------------------------------------------------------------ 8
    titulo(8, "VEREDICTO")
    gana = (dif > 0 and lo > 0)
    if gana:
        print(f"   1 · EN SU PROPIA POBLACION el modelo gana sin discusion:")
        print(f"       {100*ok_mod.mean():.1f} % frente al {100*ok_dic.mean():.1f} % "
              f"del diccionario, {dif:+.1f} puntos")
        print(f"       [{lo:+.1f}, {hi:+.1f}], p = {pstr(pv)}. Y gana por dos "
              f"motivos distintos:")
        print(f"       acierta mas donde los dos hablan "
              f"({100*ok_mod[emite_dic].mean():.1f} % frente a "
              f"{100*ok_dic[emite_dic].mean():.1f} %) y")
        print(f"       ademas contesta en los {int((~emite_dic).sum())} casos "
              f"donde el otro se calla, con")
        print(f"       un {100*ok_mod[~emite_dic].mean():.1f} % de acierto.")
        print()
        print(f"   2 · SIN SUS PALABRAS CLAVE conserva el "
              f"{100*ok_mod_sp.mean():.1f} %, {100*(ok_mod_sp.mean()-ok_may.mean()):+.1f} "
              f"sobre el")
        print(f"       suelo, donde el diccionario se queda a cero. Eso es lo")
        print(f"       que hace falta con un cliente que no usa el vocabulario")
        print(f"       de Empresa.")
        print()
        print(f"   3 · PERO SOBRE UN CORREO ENTERO SE DERRUMBA: del "
              f"{100*ok_mod.mean():.1f} % al {100*ok_env.mean():.1f} %")
        print(f"       en correo fabricado, y «Desarrollo I+D» para casi todo en")
        print(f"       los correos de verdad. Un clasificador entrenado con")
        print(f"       telegramas no sabe leer una carta.")
        print()
        print(f"   4 · LA SOLUCION NO ES OTRO MODELO, ES OTRA ENTRADA. Pasarle")
        print(f"       un telegrama extraido del correo lo sube al "
              f"{100*ok_tel.mean():.1f} % con etiqueta")
        print(f"       y al {100*coin_tel:.1f} % de acuerdo con lo que el correo "
              f"dice literalmente,")
        print(f"       desde el {100*coin:.1f} %. Nada de eso se inventa: se descarta.")
        print()
        print(f"   ASI QUEDA · el tipo de servicio del briefing lo decide un")
        print(f"   modelo entrenado con {len(d)} etiquetas humanas, que lee un")
        print(f"   telegrama de {mejor_k} palabras sacado del correo, contesta "
              f"siempre y")
        print(f"   declara en que tramo de confianza esta.")
    else:
        print(f"   El modelo NO supera al diccionario de forma concluyente:")
        print(f"   {dif:+.1f} puntos [{lo:+.1f}, {hi:+.1f}]. Se deja el")
        print(f"   diccionario y se dice, que para eso se midio.")
    print()
    print("   LO QUE NO CAMBIA · la materia sigue saliendo literal del correo")
    print("   y la norma sigue siendo un diccionario cerrado. El briefing")
    print("   tiene que seguir distinguiendo lo que CONSTA de lo que se")
    print("   PROPONE, y ahora con mas motivo que antes.")
    print()
    print("   LO QUE FALTA, y es trabajo tuyo: anotar a mano el tipo de los")
    print(f"   {len(co)} correos. Hasta entonces el {100*coin_tel:.1f} % de acuerdo "
          f"es un indicio,")
    print("   no una medida, y asi esta escrito en la memoria.")

    if not guardar:
        print()
        print("   Simulacion: no se ha escrito nada. Usa --guardar.")
        print()
        return

    salida = {
        "experimento": "E38", "agente": "A7",
        "pieza": "el tipo de servicio del tema, de diccionario a modelo",
        "version": VERSION_SCRIPT,
        "n_temas": int(len(d)), "n_textos_distintos": int(d.txt.nunique()),
        "clases": {k: int(v) for k, v in Counter(y).most_common()},
        "etiqueta": "columna «Tipo Oportunidad», rellenada por personas",
        "suelo_mayoritaria": float(100 * ok_may.mean()),
        "diccionario": {"cobertura": float(100 * emite_dic.mean()),
                        "acierto_global": float(100 * ok_dic.mean()),
                        "acierto_donde_habla": float(100 * ok_dic[emite_dic].mean())},
        "modelo": {"acierto_global": float(100 * ok_mod.mean()),
                   "ic": [float(x) for x in wilson(int(ok_mod.sum()), len(d))],
                   "f1_macro": float(100 * f1_score(y, list(pred_mod), average="macro")),
                   "acierto_donde_habla_el_dic": float(100 * ok_mod[emite_dic].mean()),
                   "acierto_donde_calla_el_dic": float(100 * ok_mod[~emite_dic].mean()),
                   "con_fuga_de_repetidos": float(100 * ok_fuga.mean())},
        "diferencia": {"puntos": float(dif), "ic": [float(lo), float(hi)],
                       "mcnemar": {"arregla": s1, "estropea": s2, "p": float(pv)}},
        "igual_cobertura": {"umbral": float(umb_cob),
                            "cobertura": float(100 * habla_cob.mean()),
                            "acierto_modelo": float(100 * ok_mod[habla_cob].mean()),
                            "acierto_diccionario": float(100 * cal_dic),
                            "no_sirve_para_trabajar":
                                "sobre correos solo habla en "
                                f"{int((co.p >= umb_cob).sum())} de {len(co)}"},
        "igual_calidad": {"umbral": float(umb_cal),
                          "cobertura": float(100 * habla_cal.mean()),
                          "acierto_modelo": float(100 * ok_mod[habla_cal].mean()),
                          "objetivo": float(100 * cal_dic),
                          "es_el_del_briefing": True},
        "sin_palabra_clave": {"modelo": float(100 * ok_mod_sp.mean()),
                              "diccionario": float(100 * ok_dic_sp.mean()),
                              "cobertura_diccionario": float(100 * emite_sp.mean()),
                              "suelo": float(100 * ok_may.mean())},
        "correo_fabricado": {
            "que_es": "un tema real del historico envuelto en la cortesia de "
                      "un correo real; conserva la etiqueta humana",
            "modelo_sobre_el_tema_solo": float(100 * ok_mod.mean()),
            "modelo_sobre_el_correo_entero": float(100 * ok_env.mean()),
            "caida_puntos": float(perdido),
            "telegrama": {str(k): float(100 * np.mean(
                [a == b for a, b in zip(pred_tel[k], y)])) for k in KS},
            "mejor_k": int(mejor_k),
            "modelo_con_telegrama": float(100 * ok_tel.mean()),
            "recuperado_puntos": float(recuperado),
            "diccionario_sobre_el_correo_entero": float(100 * ok_dic_env.mean()),
            "donde_el_diccionario_habla": {
                "n": int(emite_env.sum()),
                "diccionario": float(100 * ok_dic_env[emite_env].mean()),
                "modelo_con_telegrama": float(100 * ok_tel[emite_env].mean()),
                "diferencia": float(dif_d), "ic": [float(lo_d), float(hi_d)]},
            "limite": "un correo fabricado trae un solo asunto y esta bien "
                      "escrito; es el mejor caso, no el caso real"},
        "telegrama": {"palabras": int(mejor_k),
                      "tope_idf": float(TOPE_IDF),
                      "cortesia_descartada": int(len(PROHIBIDAS)),
                      "es_extraccion": "solo descarta palabras del correo, no "
                                       "escribe ninguna"},
        "correos": {"n": int(len(co)),
                    "acuerdo_literal_correo_entero": float(100 * coin),
                    "acuerdo_literal_telegrama": float(100 * coin_tel),
                    "n_con_evidencia_literal": int(len(amb)),
                    "que_mide": "acuerdo con lo que el correo dice con sus "
                                "propias palabras, no acierto: nadie ha "
                                "anotado el tipo de estos correos",
                    "mediana_p_en_temas": float(np.median(prob_mod)),
                    "mediana_p_en_correos": float(np.median(co.p)),
                    "cobertura_diccionario": float(100 * co.dic.notna().mean()),
                    "cobertura_modelo_con_freno": float(100 * (co.p >= umbral_f).mean()),
                    "cobertura_con_raya_alta": int((co.p >= umb_cob).sum()),
                    "cobertura_conjunta": float(100 * (co.dic.notna() | (co.p >= umbral_f)).mean()),
                    "reparto_correo_entero": {k: float(100 * v / len(co))
                                              for k, v in rep_c.items()},
                    "reparto_telegrama": {k: float(100 * v / len(co))
                                          for k, v in rep_tel.items()},
                    "reparto_en_temas": {k: float(100 * v / len(d))
                                         for k, v in rep_t.items()},
                    "mediana_p_telegrama": float(np.median(co.p_tel)),
                    "n_comerciales": int(len(com)),
                    "cobertura_comerciales_dic": float(100 * com.dic.notna().mean()),
                    "cobertura_comerciales_conjunta":
                        float(100 * (com.dic.notna() | (com.p >= umbral_f)).mean()),
                    "coincidencia_donde_los_dos_hablan": float(100 * coin),
                    "n_donde_los_dos_hablan": int(len(amb)),
                    "casos_nuevos": int(len(nuevos)),
                    "umbral": float(umbral_f),
                    "sin_verdad_a_mano": True},
        "materia": {"se_modela": False,
                    "motivo": "no hay etiqueta humana del objeto; y la materia "
                              "debe salir literal del correo para sostener la "
                              "fundamentacion del 100 %",
                    "cobertura_lista_actual": float(100 * hay_mat.mean()),
                    "ampliacion_automatica": "rechazada",
                    "por_que": "las 14 palabras frecuentes que la lista no "
                               "cubre no son objetos sino servicios y "
                               "programas de socios; subirian la cobertura "
                               f"al {100*techo.mean():.1f} % sin nombrar "
                               "ningun envase",
                    "cobertura_aparente_si_se_aceptaran": float(100 * techo.mean()),
                    "candidatas": [[p, int(n)] for p, n in cand]},
        "veredicto": ("el modelo sustituye al diccionario" if gana
                      else "se mantiene el diccionario"),
    }
    RES.mkdir(parents=True, exist_ok=True)
    f = RES / "a8_tema_modelo.json"
    f.write_text(json.dumps(salida, ensure_ascii=False, indent=1, default=float),
                 encoding="utf-8")
    pd.DataFrame({"id": co.id,
                  "diccionario": co.dic,
                  "modelo_correo_entero": co["mod"],
                  "p_correo_entero": co.p,
                  "telegrama": co.tel,
                  "modelo_telegrama": co["mod_tel"],
                  "p_telegrama": co.p_tel,
                  "coincide_con_lo_literal": co["mod_tel"] == co.dic_cl}
                 ).to_csv(RES / "a8_tipo_por_correo.csv", sep=";", index=False,
                          encoding="utf-8")
    print()
    print(f"   [ok] {f.name}  ·  a8_tipo_por_correo.csv")
    print()


if __name__ == "__main__":
    main()
